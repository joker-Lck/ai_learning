"""
向量化服务模块 - 预训练中文嵌入模型
模型: shibing624/text2vec-base-chinese (768维, 语义检索专用)
回退: TF-IDF + SVD (模型不可用时)
"""

import os
import threading

import numpy as np
from dotenv import load_dotenv

from core.logger import error, info, warning

load_dotenv(override=True)

# HuggingFace 国内镜像 + 离线优先
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# 模型配置
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
MAX_SEQ_LENGTH = 512


class EmbeddingService:
    """向量化服务类 — 预训练模型 + TF-IDF 回退"""

    def __init__(self):
        self._dim = 768  # text2vec-base-chinese 输出维度
        self._lock = threading.Lock()
        self._model = None
        self._model_loaded = False
        self._model_name = DEFAULT_MODEL

        # TF-IDF 回退相关
        self._tfidf_fallback = False
        self._vocab = None
        self._idf = None
        self._svd = None
        self._fitted = False
        self._vocab_size = int(os.getenv('EMBEDDING_VOCAB_SIZE', '20000'))

    def _load_model(self):
        """懒加载预训练模型"""
        if self._model_loaded:
            return
        with self._lock:
            if self._model_loaded:
                return
            try:
                from sentence_transformers import SentenceTransformer
                info(f"加载嵌入模型: {self._model_name}")
                self._model = SentenceTransformer(self._model_name)
                self._dim = self._model.get_embedding_dimension()
                self._model_loaded = True
                info(f"嵌入模型加载完成 (dim={self._dim})")
            except Exception as e:
                warning(f"预训练模型加载失败，回退到 TF-IDF: {e}")
                self._tfidf_fallback = True
                self._dim = 256

    # ── 预训练模型路径 ──────────────────────

    def _encode(self, text: str) -> list[float]:
        """使用预训练模型编码"""
        self._load_model()
        if self._model_loaded and self._model:
            text = text[:MAX_SEQ_LENGTH]
            vec = self._model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        return self._hash_fallback(text)

    def _encode_batch(self, texts: list[str]) -> list[list[float]]:
        """批量编码"""
        self._load_model()
        if self._model_loaded and self._model:
            texts = [t[:MAX_SEQ_LENGTH] if t else "" for t in texts]
            vecs = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
            return [v.tolist() for v in vecs]
        return [self._hash_fallback(t) for t in texts]

    # ── TF-IDF 回退路径 ─────────────────────

    def fit(self, corpus):
        """
        训练 TF-IDF + SVD 回退模型
        预训练模型可用时此方法为空操作
        """
        if self._model_loaded:
            info("预训练模型已加载，跳过 TF-IDF 训练")
            return

        with self._lock:
            try:
                from sklearn.decomposition import TruncatedSVD
                from collections import Counter
                import jieba

                info(f"TF-IDF 回退: 开始训练，语料 {len(corpus)} 条")

                # 构建词表
                STOP_WORDS = frozenset({
                    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
                    '一', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
                })

                def tokenize(text):
                    words = jieba.cut(text)
                    return [w for w in words if len(w) > 1 and w.strip() and w not in STOP_WORDS]

                word_freq = Counter()
                doc_freq = Counter()
                for text in corpus:
                    words = set(tokenize(text))
                    word_freq.update(words)
                    doc_freq.update(words)

                common = word_freq.most_common(self._vocab_size)
                self._vocab = {w: i for i, (w, _) in enumerate(common)}

                n_docs = len(corpus)
                self._idf = np.zeros(len(self._vocab))
                for w, i in self._vocab.items():
                    df = doc_freq.get(w, 0)
                    self._idf[i] = np.log((n_docs + 1) / (df + 1)) + 1

                # TF-IDF 矩阵
                def text_to_tfidf(text):
                    words = tokenize(text)
                    vec = np.zeros(len(self._vocab), dtype=np.float32)
                    wc = {}
                    for w in words:
                        wc[w] = wc.get(w, 0) + 1
                    for w, c in wc.items():
                        if w in self._vocab:
                            idx = self._vocab[w]
                            tf = c / len(words) if words else 0
                            vec[idx] = tf * self._idf[idx]
                    return vec

                tfidf_matrix = np.array([text_to_tfidf(t) for t in corpus])
                n_components = min(self._dim, tfidf_matrix.shape[1] - 1, tfidf_matrix.shape[0] - 1)
                self._svd = TruncatedSVD(n_components=n_components, random_state=42)
                self._svd.fit(tfidf_matrix)
                self._fitted = True
                self._dim = n_components
                self._tfidf_fallback = True
                info(f"TF-IDF 回退训练完成 (dim={n_components})")
            except Exception as e:
                error(f"TF-IDF 训练失败: {e}")

    def _tfidf_encode(self, text: str) -> list[float]:
        """TF-IDF + SVD 编码"""
        import jieba
        STOP_WORDS = frozenset({'的', '了', '在', '是', '我', '有', '和', '就', '不'})

        words = [w for w in jieba.cut(text) if len(w) > 1 and w.strip() and w not in STOP_WORDS]
        vec = np.zeros(len(self._vocab), dtype=np.float32)
        wc = {}
        for w in words:
            wc[w] = wc.get(w, 0) + 1
        for w, c in wc.items():
            if w in self._vocab:
                idx = self._vocab[w]
                tf = c / len(words) if words else 0
                vec[idx] = tf * self._idf[idx]

        tfidf = vec.reshape(1, -1)
        result = self._svd.transform(tfidf)[0]
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result.tolist()

    def _hash_fallback(self, text: str) -> list[float]:
        """哈希回退（最后手段）"""
        import hashlib
        vec = np.zeros(self._dim, dtype=np.float32)

        import jieba
        words = list(jieba.cut(text))
        for w in words:
            if len(w) > 1 and w.strip():
                h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
                idx = h % self._dim
                sign = 1 if (h // self._dim) % 2 == 0 else -1
                vec[idx] += sign

        chars = [c for c in text if c.strip()]
        for i in range(len(chars) - 1):
            bg = chars[i] + chars[i + 1]
            h = int(hashlib.md5(bg.encode('utf-8')).hexdigest(), 16)
            idx = h % self._dim
            sign = 1 if (h // self._dim) % 2 == 0 else -1
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    # ── 公共 API（保持不变）──────────────────

    def get_embedding(self, text, model=None):
        """
        获取文本的向量表示

        参数：
        - text: 要向量化的文本

        返回：
        - list: 向量数组 (768维)
        """
        try:
            text = text[:8000]
            if not text.strip():
                return [0.0] * self._dim

            # 优先预训练模型
            if self._model_loaded or not self._tfidf_fallback:
                return self._encode(text)

            # TF-IDF 回退
            if self._fitted and self._vocab:
                return self._tfidf_encode(text)

            # 哈希回退
            return self._hash_fallback(text)
        except Exception as e:
            error(f"获取向量失败：{e!s}")
            return None

    def get_embeddings(self, texts):
        """
        批量获取文本的向量表示
        """
        try:
            if self._model_loaded or not self._tfidf_fallback:
                return self._encode_batch(texts)

            return [self.get_embedding(t) for t in texts]
        except Exception as e:
            error(f"批量获取向量失败：{e!s}")
            return None

    def cosine_similarity(self, vec1, vec2):
        """计算余弦相似度"""
        try:
            if vec1 is None or vec2 is None:
                return 0.0
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        except Exception as e:
            error(f"计算相似度失败：{e!s}")
            return 0.0


# 全局实例
embedding_service = EmbeddingService()
