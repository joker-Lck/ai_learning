"""
BM25 + Softmax 检索模块

BM25 (Best Matching 25) 经典词项排序算法，配合 Softmax 分数归一化：
- BM25 对候选文档打相关性分（IDF × 词频饱和 × 长度归一）
- Softmax 把分数映射为概率分布，便于跨查询校准、多路融合与阈值截断

支持中文（jieba 分词）与英文，索引可从 MySQL knowledge_documents 构建。
"""

from __future__ import annotations

import math
import re
import threading
from collections import Counter, defaultdict
from typing import Callable, Iterable

from core.logger import debug, info, warning

# ── 分词 ──────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_]+")

_STOP_WORDS = frozenset(
    """
    的 了 在 是 我 有 和 就 不 都 一 一个 也 很 及 与 或 及其 请 问 什么 怎么 如何
    the a an and or of to in is are for on with that this
    """.split()
)


class Tokenizer:
    """jieba 中文分词 + 英文/数字切词，失败时降级到正则。"""

    def __init__(self):
        self._jieba = None
        try:
            import jieba

            jieba.setLogLevel(60)
            self._jieba = jieba
            debug("BM25 分词器: jieba")
        except ImportError:
            debug("BM25 分词器: 正则回退（jieba 不可用）")

    def __call__(self, text: str) -> list[str]:
        if not text:
            return []
        if self._jieba is not None:
            raw = self._jieba.cut_for_search(text)
        else:
            raw = _TOKEN_RE.findall(text)
        tokens: list[str] = []
        for tok in raw:
            tok = tok.strip().lower()
            if len(tok) < 2 or tok in _STOP_WORDS:
                continue
            tokens.append(tok)
        return tokens


# ── Softmax ───────────────────────────────────────────────


def softmax(scores: Iterable[float], temperature: float = 1.0) -> list[float]:
    """
    数值稳定的 Softmax。

    参数:
        scores: 原始分数（越大越相关）
        temperature: 温度 T；T<1 分布更尖锐，T>1 更平缓，T→0 退化为 argmax

    返回:
        与输入等长的概率列表，和为 1
    """
    vals = [float(s) for s in scores]
    if not vals:
        return []
    if temperature <= 0:
        temperature = 1e-6
    scaled = [v / temperature for v in vals]
    mx = max(scaled)
    exps = [math.exp(v - mx) for v in scaled]
    total = sum(exps)
    if total <= 0:
        n = len(vals)
        return [1.0 / n] * n
    return [e / total for e in exps]


# ── BM25 索引 ─────────────────────────────────────────────


class BM25Index:
    """
    内存 BM25 索引。

    score(D, Q) = Σ_i IDF(q_i) · (tf · (k1+1)) / (tf + k1 · (1 - b + b · |D|/avgdl))

    - k1: 词频饱和系数（默认 1.5）
    - b:  文档长度归一化强度（默认 0.75）
    - IDF: Robertson/Sparck-Jones 平滑  ln((N - df + 0.5)/(df + 0.5) + 1)
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Callable[[str], list[str]] | None = None,
    ):
        self.k1 = float(k1)
        self.b = float(b)
        self._tokenize = tokenizer or Tokenizer()
        self._lock = threading.RLock()

        self._doc_ids: list[int] = []
        self._doc_len: list[int] = []          # 每篇文档的 token 数
        self._tf: list[Counter] = []           # 每篇文档的词频
        self._df: dict[str, int] = defaultdict(int)   # 文档频率
        self._postings: dict[str, set[int]] = defaultdict(set)  # 倒排：term → doc 下标集合
        self._id_to_pos: dict[int, int] = {}   # doc_id → 下标（O(1) 增删）
        self._avgdl: float = 0.0
        self._N: int = 0

    # ── 构建 / 更新 ──────────────────────────

    def build(self, docs: Iterable[dict]) -> None:
        """
        全量构建。

        docs: [{"id": int, "text": str}, ...]
        """
        with self._lock:
            self._doc_ids = []
            self._doc_len = []
            self._tf = []
            self._df = defaultdict(int)
            self._postings = defaultdict(set)
            self._id_to_pos = {}
            self._N = 0

            for doc in docs:
                self._add_one(doc.get("id"), doc.get("text") or "")

            self._recompute_avgdl()
            info(f"[BM25] 索引构建完成: docs={self._N}, vocab={len(self._df)}, avgdl={self._avgdl:.1f}")

    def upsert(self, doc_id: int, text: str) -> None:
        """插入或覆盖单篇文档（O(tokens)，增量倒排）"""
        with self._lock:
            self._remove_locked(doc_id)
            self._add_one(doc_id, text)
            self._recompute_avgdl()

    def remove(self, doc_id: int) -> None:
        with self._lock:
            if self._remove_locked(doc_id):
                self._recompute_avgdl()

    def clear(self) -> None:
        with self._lock:
            self._doc_ids.clear()
            self._doc_len.clear()
            self._tf.clear()
            self._df = defaultdict(int)
            self._postings = defaultdict(set)
            self._id_to_pos = {}
            self._N = 0
            self._avgdl = 0.0

    # ── 检索 ──────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[tuple[int, float]]:
        """
        返回按 BM25 分数降序的 [(doc_id, score), ...]
        走倒排索引，只遍历命中词项的文档（O(Σ postings) 而非 O(N)）。
        """
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        with self._lock:
            if self._N == 0:
                return []

            q_tf = Counter(q_tokens)
            scores: dict[int, float] = defaultdict(float)

            for term, _q_count in q_tf.items():
                df = self._df.get(term, 0)
                if df == 0:
                    continue
                idf = math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)

                # 倒排：只访问含该词的文档
                for pos in self._postings.get(term, ()):
                    if pos >= len(self._tf):
                        continue
                    tf = self._tf[pos].get(term, 0)
                    if tf == 0:
                        continue
                    dl = self._doc_len[pos] or 1
                    denom = tf + self.k1 * (1.0 - self.b + self.b * dl / (self._avgdl or 1.0))
                    doc_id = self._doc_ids[pos]
                    scores[doc_id] += idf * (tf * (self.k1 + 1.0)) / denom

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:limit] if limit > 0 else ranked

    def search_with_prob(
        self,
        query: str,
        limit: int = 10,
        temperature: float = 1.0,
        candidate_pool: int | None = None,
    ) -> list[tuple[int, float, float]]:
        """
        BM25 打分 + Softmax 归一化。

        返回 [(doc_id, bm25_score, probability), ...]
        probability 对最终返回列表求和为 1。
        """
        pool = candidate_pool or max(limit * 5, 20)
        hits = self.search(query, limit=pool)
        if not hits:
            return []

        # 先在候选池上 Softmax，截断后重归一化，保证返回概率分布和为 1
        pool_probs = softmax([s for _, s in hits], temperature=temperature)
        truncated = list(zip(hits, pool_probs, strict=False))[:limit] if limit > 0 else list(zip(hits, pool_probs, strict=False))
        final_scores = [s for (_, s), _ in truncated]
        final_probs = softmax(final_scores, temperature=temperature)

        return [
            (doc_id, score, prob)
            for ((doc_id, score), _), prob in zip(truncated, final_probs, strict=False)
        ]

    # ── 统计 ──────────────────────────────────

    @property
    def num_docs(self) -> int:
        return self._N

    @property
    def vocab_size(self) -> int:
        return len(self._df)

    @property
    def avgdl(self) -> float:
        return self._avgdl

    def stats(self) -> dict:
        with self._lock:
            return {
                "docs": self._N,
                "vocab": len(self._df),
                "avgdl": round(self._avgdl, 2),
                "k1": self.k1,
                "b": self.b,
            }

    # ── 内部 ──────────────────────────────────

    def _add_one(self, doc_id, text: str) -> None:
        if doc_id is None:
            return
        tokens = self._tokenize(text)
        pos = len(self._doc_ids)
        self._doc_ids.append(int(doc_id))
        self._id_to_pos[int(doc_id)] = pos
        tf = Counter(tokens)
        self._tf.append(tf)
        self._doc_len.append(len(tokens))
        for term in tf:
            self._df[term] += 1
            self._postings[term].add(pos)
        self._N += 1

    def _remove_locked(self, doc_id) -> bool:
        doc_id = int(doc_id)
        pos = self._id_to_pos.pop(doc_id, None)
        if pos is None:
            return False

        removed_tf = self._tf[pos]

        # 尾部元素交换到 pos，保证数组紧凑 + 映射正确
        last_pos = len(self._doc_ids) - 1
        if pos != last_pos:
            moved_id = self._doc_ids[last_pos]
            self._doc_ids[pos] = moved_id
            self._tf[pos] = self._tf[last_pos]
            self._doc_len[pos] = self._doc_len[last_pos]
            self._id_to_pos[moved_id] = pos
            # 更新被移动文档在倒排中的位置
            for term in self._tf[pos]:
                if term in self._postings:
                    self._postings[term].discard(last_pos)
                    self._postings[term].add(pos)
        self._doc_ids.pop()
        self._tf.pop()
        self._doc_len.pop()

        # 清理被删文档的倒排项
        for term in removed_tf:
            self._postings[term].discard(last_pos)
            if pos != last_pos:
                self._postings[term].discard(pos)
            # 若该词没有其它文档，丢弃 postings 集合
            if not self._postings[term]:
                del self._postings[term]
            self._df[term] -= 1
            if self._df[term] <= 0:
                del self._df[term]
        self._N -= 1
        return True

    def _recompute_avgdl(self) -> None:
        self._avgdl = (sum(self._doc_len) / self._N) if self._N else 0.0


# ── 端到端检索器 ─────────────────────────────────────────


class BM25SoftmaxRetriever:
    """
    BM25 + Softmax 检索器。

    流程:
        查询 → jieba 分词 → BM25 打分 → Softmax 概率化 → Top-K
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        temperature: float = 1.0,
    ):
        self.temperature = float(temperature)
        self.index = BM25Index(k1=k1, b=b)
        self._built = False

    def build_from_rows(self, rows: Iterable[dict]) -> int:
        """
        从行数据构建索引。

        rows: [{"id": ..., "title": ..., "subject": ..., "text": ...}, ...]
        """
        docs = []
        for row in rows:
            doc_id = row.get("id")
            if doc_id is None:
                continue
            text = " ".join(
                filter(
                    None,
                    [
                        row.get("title") or "",
                        row.get("subject") or "",
                        row.get("text") or "",
                    ],
                )
            )
            docs.append({"id": int(doc_id), "text": text})
        self.index.build(docs)
        self._built = True
        return len(docs)

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        temperature: float | None = None,
    ) -> list[dict]:
        """
        检索并返回统一文档格式（与 fulltext/vector 路径对齐）。

        返回: [{"id", "score", "probability", "retrieval_method"}, ...]
        """
        t = self.temperature if temperature is None else temperature
        hits = self.index.search_with_prob(query, limit=limit, temperature=t)
        return [
            {
                "id": doc_id,
                "score": score,
                "similarity": score,
                "probability": prob,
                "retrieval_method": "bm25_softmax",
            }
            for doc_id, score, prob in hits
        ]

    @property
    def is_ready(self) -> bool:
        return self._built and self.index.num_docs > 0

    def stats(self) -> dict:
        return {"temperature": self.temperature, "ready": self.is_ready, **self.index.stats()}


def fuse_probabilities(
    score_lists: list[list[tuple[int, float]]],
    weights: list[float] | None = None,
    temperature: float = 1.0,
) -> list[tuple[int, float]]:
    """
    多路分数融合：各自 Softmax 成概率后加权平均。

    参数:
        score_lists: 多路 [(doc_id, raw_score), ...]
        weights:     各路权重（默认等权）
        temperature: Softmax 温度

    返回:
        [(doc_id, fused_prob), ...] 按融合概率降序
    """
    if not score_lists:
        return []

    if weights is None:
        weights = [1.0] * len(score_lists)
    wsum = sum(weights) or 1.0
    weights = [w / wsum for w in weights]

    fused: dict[int, float] = defaultdict(float)
    for scores, w in zip(score_lists, weights, strict=False):
        if not scores:
            continue
        probs = softmax([s for _, s in scores], temperature=temperature)
        for (doc_id, _), p in zip(scores, probs, strict=False):
            fused[doc_id] += w * p

    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


# 全局单例（惰性构建）
bm25_retriever = BM25SoftmaxRetriever()
