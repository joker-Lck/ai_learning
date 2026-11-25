# -*- coding: utf-8 -*-
"""LEAR 论文客观评测（标准协议）

A. 检索方法对比：近两年代表性分块/检索策略 vs LEAR（Hit@1/Hit@5/Recall@5/MRR/nDCG@5）
B. 模块消融 2^3：M1 教学结构分块 × M2 同节邻域组装 × M3 教法依赖回链（8 组合）
C. 忠实度对比 + 通道消融 2^3：F1 数值归一化 × F2 绑定值 × F3 公式等价（8 组合 + 外部基线）

产出 experiments/eval_results.json + 控制台 markdown 表。
"""
import sys, os, re, json, math, random
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")

from pathlib import Path
from data.structure_chunker import StructureChunker
from data.bm25_softmax import BM25Index

CORPUS = Path(r"F:\项目\ai教学辅助系统\experiments\corpus_textbook")
OUT_JSON = Path(r"F:\项目\ai教学辅助系统\experiments\eval_results.json")
random.seed(42)

# ═══════════════════════ 语料与金标 ═══════════════════════
# 教材体例：**定理 1** 设… / **例 1** … / **定义 2** …（Markdown 粗体，正文接排）
UNIT_START = re.compile(
    r"^\s*\*\*\s*(定义|定理|引理|例题|例|公式|性质|推论)\s*(\d+)\s*\*\*"
    r"|^\s*(定义|定理|引理|例题|例|公式|性质|推论)\s*(\d+)\s*[（(]?([^：:\n]{0,20})[）)]?\s*[：:]"
)
KIND_MAP = {"定义": "definition", "定理": "theorem", "引理": "theorem", "性质": "theorem",
            "推论": "theorem", "公式": "theorem", "例题": "example", "例": "example"}


def load_corpus():
    docs = []
    for p in sorted(CORPUS.rglob("*.md")):
        if p.name in ("README.md", "template_text.txt"):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if len(text) < 200:
            continue
        sec = re.sub(r"\.md$", "", p.name)
        sec = re.sub(r"^\d+(\.\d+)?\s*", "", sec) or sec
        docs.append({"path": str(p), "section": sec, "text": text})
    return docs


def extract_gold(docs):
    golds = []
    for di, d in enumerate(docs):
        cur, cur_label, cur_kind, cur_name = [], None, None, ""
        for ln in d["text"].split("\n") + ["__END__"]:
            m = UNIT_START.match(ln)
            if m or ln == "__END__":
                if cur_label and cur:
                    body = "\n".join(cur).strip()
                    if 30 <= len(body) <= 900:
                        golds.append({"doc": di, "kind": cur_kind, "label": cur_label,
                                      "term": cur_name or d["section"], "text": body,
                                      "section": d["section"]})
                cur = []
                if m:
                    kind_cn = m.group(1) or m.group(3)
                    num = m.group(2) or m.group(4)
                    name = (m.group(5) or "").strip() if m.group(5) else ""
                    cur_label = f"{kind_cn}{num}" if num else kind_cn
                    cur_kind = KIND_MAP[kind_cn]
                    cur_name = name.rstrip("（(")
                    cur = [ln.strip()]
            elif cur:
                cur.append(ln.strip())
    by_kind = {}
    for g in golds:
        by_kind.setdefault(g["kind"], []).append(g)
    picked = []
    for k, lst in by_kind.items():
        random.shuffle(lst)
        picked.extend(lst[:120])
    return picked


TEMPLATES_TERM = ["什么是{}？", "{}的定义是什么？", "请解释{}", "讲一下{}"]
TEMPLATES_LABEL = ["{}的内容是什么？", "请写出{}", "简述{}"]


def build_queries(golds):
    """终版协议：逐实例严格单金标 + 查询-金标对齐（术语须含于金标正文）"""
    qs = []
    for i, g in enumerate(golds):
        term = re.split(r"[·・,，、]", g["term"])[0].strip()
        # 去掉"第X章/节"式编号前缀（章节号不是概念名）
        term = re.sub(r"^第[一二三四五六七八九十百千0-9]+\s*[章单元课讲部分篇模块册辑节]\s*", "", term).strip()
        if not term or len(term) < 2:
            term = re.sub(r"^\d+(\.\d+)?\s*", "", g["section"]).strip() or g["section"]
        t = TEMPLATES_TERM[i % 4].format(term)
        l = TEMPLATES_LABEL[i % 3].format(g["label"])
        # 查询-金标对齐：术语型查询只给正文含该术语的单元构造
        if 4 <= len(t) <= 40 and (term[:3] in g["text"] or term in g["text"]):
            qs.append({"q": t, "gold": g, "qtype": "术语型", "gold_texts": [g["text"]]})
        if 4 <= len(l) <= 40:
            qs.append({"q": l, "gold": g, "qtype": "标签型", "gold_texts": [g["text"]]})
    return qs


def hit_any(gold_texts, chunk_text):
    return any(is_relevant(gt, chunk_text) for gt in gold_texts)


# ═══════════════════════ 分块策略（代表性方法）═══════════════════════
def chunks_fixed(text, section, size=600, stride=500):
    out, i = [], 0
    while i < len(text):
        seg = text[i:i + size]
        if seg.strip():
            out.append({"text": seg, "raw": seg, "kind": "body",
                        "section_path": section, "doc": section, "order": len(out)})
        i += stride
    return out


def chunks_para(text, section, size=600):
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    out, buf, order = [], "", 0
    for p in paras:
        if buf and len(buf) + len(p) > size:
            out.append({"text": buf, "raw": buf, "kind": "body",
                        "section_path": section, "doc": section, "order": order})
            order += 1
            buf = p
        else:
            buf = f"{buf}\n{p}" if buf else p
    if buf.strip():
        out.append({"text": buf, "raw": buf, "kind": "body",
                    "section_path": section, "doc": section, "order": order})
    return out


def _char_ngrams(t, n=2):
    t = re.sub(r"\s+", "", t)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def chunks_semantic(text, section, threshold=0.22, size=800):
    sents = [s.strip() for s in re.split(r"[。！？!?\n；;]", text) if len(s.strip()) >= 6]
    bounds = [0]
    for i in range(1, len(sents)):
        a, b = _char_ngrams(sents[i - 1]), _char_ngrams(sents[i])
        sim = len(a & b) / len(a | b) if a and b else 0.0
        if sim < threshold:
            bounds.append(i)
    bounds.append(len(sents))
    out, order = [], 0
    for i in range(len(bounds) - 1):
        seg = "。".join(sents[bounds[i]:bounds[i + 1]])
        if not seg.strip():
            continue
        while len(seg) > size:  # 过长二次切
            out.append({"text": seg[:size], "raw": seg[:size], "kind": "body",
                        "section_path": section, "doc": section, "order": order})
            order += 1
            seg = seg[size:]
        if seg.strip():
            out.append({"text": seg, "raw": seg, "kind": "body",
                        "section_path": section, "doc": section, "order": order})
            order += 1
    return out


def chunks_title_prefix(text, section):
    return [{**c, "text": f"{section} >> {c['raw']}"} for c in chunks_fixed(text, section)]


def chunks_ctx_prefix(text, section):
    head = re.sub(r"\s+", " ", text)[:80]
    return [{**c, "text": f"{section}：{head}。{c['raw']}"} for c in chunks_fixed(text, section)]


def chunks_parent_children(text, section, child=300, parent=900):
    out, i, order = [], 0, 0
    while i < len(text):
        seg = text[i:i + child]
        if seg.strip():
            j = max(0, i - (parent - child) // 2)
            out.append({"text": seg, "raw": text[j:j + parent], "kind": "body",
                        "section_path": section, "doc": section, "order": order,
                        "is_child": True})
        i += child - 20
        order += 1
    return out


def chunks_lear(text, section, doc_id):
    tree = StructureChunker(max_length=600, min_length=80).chunk(text, doc_id=doc_id)
    return [{"text": f"{c.section_path or section} >> {c.text}", "raw": c.text, "kind": c.kind,
             "section_path": c.section_path or section, "doc": section,
             "order": c.order, "chunk_id": c.chunk_id} for c in tree.chunks]


def chunks_lear_clustered(text, section, doc_id, max_cluster=900):
    """教学语义簇：同节相邻教学块按依赖链（定义→定理→例题→证明）聚为检索单元。
    簇内语义完整、簇间以教学/章节边界相隔；检索以簇为单元，证据粒度仍为块。"""
    units = chunks_lear(text, section, doc_id)
    clusters = []
    cur = []
    total = 0
    for u in units:
        same_path = cur and u["section_path"] == cur[-1]["section_path"]
        if cur and (not same_path or total + len(u["raw"]) > max_cluster):
            clusters.append(cur)
            cur, total = [], 0
        cur.append(u)
        total += len(u["raw"])
    if cur:
        clusters.append(cur)
    out = []
    for gi, grp in enumerate(clusters):
        raw = "\n".join(x["raw"] for x in grp)
        path = grp[0]["section_path"]
        kinds = [x["kind"] for x in grp]
        primary = "definition" if "definition" in kinds else \
                  "theorem" if "theorem" in kinds else kinds[0]
        out.append({"text": f"{path} >> {raw}", "raw": raw, "kind": primary,
                    "section_path": path, "doc": section,
                    "order": grp[0]["order"], "chunk_id": f"{grp[0]['chunk_id']}_g{gi}",
                    "members": [x["chunk_id"] for x in grp]})
    return out


# ═══════════════════════ 检索与指标 ═══════════════════════
def build_index(chunks):
    idx = BM25Index()
    idx.build([{"id": i, "text": c["text"]} for i, c in enumerate(chunks)])
    return idx


def grams(text, n=8):
    t = re.sub(r"\s+", "", text)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def is_relevant(gold_text, chunk_text):
    """对称重叠判据：块覆盖金标 ≥45% 或金标覆盖块 ≥60% 即相关（对大小块公平）"""
    g, c = grams(gold_text), grams(chunk_text)
    if not g or not c:
        return False
    inter = len(g & c)
    return inter / len(g) >= 0.45 or inter / len(c) >= 0.6


def metrics5(rels):
    hits = [1 if r else 0 for r in rels]
    hit1 = 1.0 if hits and hits[0] else 0.0
    hit5 = 1.0 if any(hits) else 0.0
    mrr = 0.0
    for rank, h in enumerate(hits, 1):
        if h:
            mrr = 1.0 / rank
            break
    dcg = sum(h / math.log2(rank + 1) for rank, h in enumerate(hits, 1))
    idcg = sum(1 / math.log2(r + 1) for r in range(1, min(1, len(hits)) + 1))
    ndcg = dcg / idcg if idcg > 0 else 0.0
    return hit1, hit5, hit5, mrr, ndcg  # recall@5 == hit@5（单金标）


def eval_strategy(queries, chunks, idx, parent_map=None):
    agg = {"hit@1": [], "hit@5": [], "recall@5": [], "mrr": [], "ndcg@5": []}
    split = {"术语型": {"hit@5": [], "mrr": []}, "标签型": {"hit@5": [], "mrr": []}}
    for it in queries:
        res = idx.search(it["q"], limit=8 if parent_map else 5)
        if parent_map:  # 小块检索→大块返回
            seen, finals = set(), []
            for ci, s in res:
                pi = parent_map[ci]
                if pi in seen:
                    continue
                seen.add(pi)
                finals.append((pi, s))
                if len(finals) >= 5:
                    break
            res = finals
        rels = []
        for ci, _s in res[:5]:
            rels.append(1 if hit_any(it["gold_texts"], chunks[ci]["raw"]) else 0)
        rels += [0] * (5 - len(rels))
        h1, h5, r5, mrr, ndcg = metrics5(rels)
        for k, v in zip(("hit@1", "hit@5", "recall@5", "mrr", "ndcg@5"), (h1, h5, r5, mrr, ndcg)):
            agg[k].append(v)
        qt = it.get("qtype", "术语型")
        split[qt]["hit@5"].append(h5)
        split[qt]["mrr"].append(mrr)
    out = {k: round(sum(v) / len(v), 4) for k, v in agg.items()}
    for qt, d in split.items():
        if d["hit@5"]:
            out[f"{qt}_hit@5"] = round(sum(d["hit@5"]) / len(d["hit@5"]), 4)
            out[f"{qt}_mrr"] = round(sum(d["mrr"]) / len(d["mrr"]), 4)
    return out


# ── 向量检索（BGE-M3 批量）──
_vec_cache = {}


def get_encoder():
    if "enc" in _vec_cache:
        return _vec_cache["enc"]
    try:
        from data.embedding_service import embedding_service as es
        es.get_embedding("预热")
        if getattr(es, "_tfidf_fallback", False):
            _vec_cache["enc"] = ("tfidf", es)
        else:
            _vec_cache["enc"] = ("bge", es._model)
    except Exception as e:
        print(f"  [向量不可用: {e}]")
        _vec_cache["enc"] = None
    return _vec_cache["enc"]


def embed_batch(texts, max_len=384):
    """批量编码（磁盘缓存，断点续跑）"""
    import numpy as np
    import hashlib
    enc = get_encoder()
    if enc is None:
        return None
    kind, obj = enc
    cache_dir = Path(r"F:\项目\ai教学辅助系统\experiments\emb_cache")
    cache_dir.mkdir(exist_ok=True)
    key = hashlib.md5(("|".join(t[:200] for t in texts[:50]) + f"|{len(texts)}").encode()).hexdigest()[:16]
    f = cache_dir / f"{kind}_{key}.npy"
    start = 0
    vecs = []
    if f.exists():
        mat = np.load(f)
        if mat.shape[0] == len(texts):
            return mat
        if mat.shape[0] < len(texts):
            vecs = [mat]
            start = mat.shape[0]
            print(f"    [embed resume {start}/{len(texts)}]", flush=True)
    bs = 64
    for i in range(start, len(texts), bs):
        batch = [t[:max_len] for t in texts[i:i + bs]]
        if kind == "tfidf":
            vecs.append(np.vstack([obj.get_embedding(t) for t in batch]))
        else:
            vecs.append(obj.encode(batch, normalize_embeddings=True, show_progress_bar=False))
        if i % 512 == 0:
            print(f"    [embed {i + len(batch)}/{len(texts)}]", flush=True)
            partial = np.vstack(vecs)   # 增量落盘，中断可续跑
            np.save(f, partial)
    mat = np.vstack(vecs)
    np.save(f, mat)
    return mat


def eval_strategy_vec(queries, chunks, qvecs, cmat):
    import numpy as np
    agg = {"hit@1": [], "hit@5": [], "recall@5": [], "mrr": [], "ndcg@5": []}
    split = {"术语型": {"hit@5": [], "mrr": []}, "标签型": {"hit@5": [], "mrr": []}}
    cnorm = cmat / (np.linalg.norm(cmat, axis=1, keepdims=True) + 1e-9)
    for qi, it in enumerate(queries):
        q = qvecs[qi] / (np.linalg.norm(qvecs[qi]) + 1e-9)
        sims = cnorm @ q
        top = np.argsort(-sims)[:5]
        rels = [1 if hit_any(it["gold_texts"], chunks[int(i)]["raw"]) else 0 for i in top]
        rels += [0] * (5 - len(rels))
        h1, h5, r5, mrr, ndcg = metrics5(rels)
        for k, v in zip(("hit@1", "hit@5", "recall@5", "mrr", "ndcg@5"), (h1, h5, r5, mrr, ndcg)):
            agg[k].append(v)
        qt = it.get("qtype", "术语型")
        split[qt]["hit@5"].append(h5)
        split[qt]["mrr"].append(mrr)
    out = {k: round(sum(v) / len(v), 4) for k, v in agg.items()}
    for qt, d in split.items():
        if d["hit@5"]:
            out[f"{qt}_hit@5"] = round(sum(d["hit@5"]) / len(d["hit@5"]), 4)
            out[f"{qt}_mrr"] = round(sum(d["mrr"]) / len(d["mrr"]), 4)
    return out


# ═══════════════════════ A2. SOTA 家族强基线 ═══════════════════════
def chunks_raptor_nodes(text, section, leaves):
    """RAPTOR 式层级检索的抽取式变体：句群 TextRank 摘要节点 + 叶子块双层索引"""
    sents = [s.strip() for s in re.split(r"[。！？!?\n]", text) if len(s.strip()) >= 10]
    nodes = list(leaves)
    if len(sents) >= 4:
        # TextRank（词面相似度句图）
        n = min(len(sents), 40)
        sents = sents[:n]
        g = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                a, b = _char_ngrams(sents[i]), _char_ngrams(sents[j])
                sim = len(a & b) / (len(a | b) or 1)
                g[i][j] = g[j][i] = sim
        score = [1.0] * n
        for _ in range(10):
            score = [0.15 + 0.85 * sum(g[i][j] * score[j] for j in range(n) if j != i)
                     for i in range(n)]
        top = sorted(range(n), key=lambda i: -score[i])[:2]
        for rank, si in enumerate(sorted(top)):
            nodes.append({"text": f"【要点】{sents[si]}", "raw": sents[si], "kind": "summary",
                          "section_path": section, "doc": section,
                          "order": 10000 + rank})
    return nodes


def graph_expansion(chunks, top_idxs, k_expand=2):
    """GraphRAG-lite：块级关键词共现图，命中节点沿共现边扩展邻块"""
    def keys(t):
        return set(w for w in re.findall(r"[\u4e00-\u9fff]{2,4}", t)) | \
               set(re.findall(r"[A-Za-z][A-Za-z0-9]{1,8}", t))
    n = len(chunks)
    kk = [keys(c["raw"]) for c in chunks]
    out = list(top_idxs)
    seen = set(top_idxs)
    for i in top_idxs:
        scored = []
        for j in range(n):
            if j in seen or chunks[j]["doc"] != chunks[i]["doc"]:
                continue
            inter = len(kk[i] & kk[j])
            if inter:
                scored.append((inter, j))
        for _, j in sorted(scored, reverse=True)[:k_expand]:
            out.append(j)
            seen.add(j)
    return out


def rrf_fuse(rank_lists, k=60):
    """RRF 融合多路排名"""
    score = {}
    for ranks in rank_lists:
        for r, ci in enumerate(ranks, 1):
            score[ci] = score.get(ci, 0.0) + 1.0 / (k + r)
    return [ci for ci, _ in sorted(score.items(), key=lambda x: -x[1])]


def eval_colbert(queries, chunks, qvecs_tok, docvecs):
    """ColBERT 式 late-interaction（MaxSim）"""
    import numpy as np
    agg = {"hit@1": [], "hit@5": [], "recall@5": [], "mrr": [], "ndcg@5": []}
    split = {"术语型": {"hit@5": [], "mrr": []}, "标签型": {"hit@5": [], "mrr": []}}
    for qi, it in enumerate(queries):
        q = qvecs_tok[qi]  # (Lq, d)
        sims = []
        for d in docvecs:  # (Ld, d)
            if d.shape[0] == 0:
                sims.append(-1e9)
                continue
            m = q @ d.T if d.ndim == 2 else q @ d
            sims.append(float(m.max(axis=1).sum()))
        top = np.argsort(-np.array(sims))[:5]
        rels = [1 if hit_any(it["gold_texts"], chunks[int(i)]["raw"]) else 0 for i in top]
        rels += [0] * (5 - len(rels))
        h1, h5, r5, mrr, ndcg = metrics5(rels)
        for k, v in zip(("hit@1", "hit@5", "recall@5", "mrr", "ndcg@5"), (h1, h5, r5, mrr, ndcg)):
            agg[k].append(v)
        qt = it.get("qtype", "术语型")
        split[qt]["hit@5"].append(h5)
        split[qt]["mrr"].append(mrr)
    out = {k: round(sum(v) / len(v), 4) for k, v in agg.items()}
    for qt, d in split.items():
        if d["hit@5"]:
            out[f"{qt}_hit@5"] = round(sum(d["hit@5"]) / len(d["hit@5"]), 4)
            out[f"{qt}_mrr"] = round(sum(d["mrr"]) / len(d["mrr"]), 4)
    return out


def encode_token_embeddings(texts, max_tok=192):
    """bge-m3 token 级向量（ColBERT 用），磁盘缓存"""
    import numpy as np
    import hashlib
    enc = get_encoder()
    if enc is None or enc[0] == "tfidf":
        print("  [token 编码需要 bge-m3，跳过 ColBERT]")
        return None
    model = enc[1]
    key = hashlib.md5(("tok|" + "|".join(t[:120] for t in texts[:40]) + f"|{len(texts)}").encode()).hexdigest()[:16]
    f = Path(r"F:\项目\ai教学辅助系统\experiments\emb_cache") / f"tok_{key}.npy"
    if f.exists():
        mat = np.load(f, allow_pickle=True)
        if len(mat) == len(texts):
            return mat
    out = []
    for i in range(0, len(texts), 32):
        batch = [t[:1200] for t in texts[i:i + 32]]
        emb = model.encode(batch, output_value="token_embeddings",
                           normalize_embeddings=True, show_progress_bar=False)
        for e in emb:
            arr = np.asarray(e, dtype=np.float16)[:max_tok]
            out.append(arr)
        if i % 256 == 0:
            print(f"    [tok-embed {i + len(batch)}/{len(texts)}]", flush=True)
            np.save(f, np.array(out, dtype=object), allow_pickle=True)
    np.save(f, np.array(out, dtype=object), allow_pickle=True)
    return out


def flag_dense_entail(claim, evidence, model=None, threshold=0.55):
    """稠密蕴含基线：claim↔证据句最大余弦相似度（NLI 核查的无监督近似）"""
    import numpy as np
    if model is None:
        model = get_encoder()[1] if get_encoder() and get_encoder()[0] == "bge" else None
    if model is None:
        return False
    cv = np.asarray(model.encode([claim], normalize_embeddings=True, show_progress_bar=False)[0])
    ev_sents = []
    for e in evidence:
        ev_sents += [s for s in re.split(r"[。！？\n；;]", e.get("content_text", "")) if len(s.strip()) >= 8]
    if not ev_sents:
        return True
    ev = np.asarray(model.encode(ev_sents[:10], normalize_embeddings=True, show_progress_bar=False))
    best = float((ev @ cv).max())
    return best < threshold


# ═══════════════════════ B. 组装模块（消融用）═══════════════════════
def assemble(chunks, top_idxs, use_m2, use_m3, budget=4800):
    """top-k 块 → 上下文文本；M2=同节邻域组装，M3=教法依赖回链"""
    chosen, seen = [], set()
    for i in top_idxs:
        if i not in seen:
            chosen.append(i)
            seen.add(i)
    if use_m2:
        for i in top_idxs:
            c = chunks[i]
            for j, o in enumerate(chunks):
                if j in seen:
                    continue
                if o["doc"] == c["doc"] and abs(o["order"] - c["order"]) <= 1 \
                        and o["section_path"] == c["section_path"]:
                    chosen.append(j)
                    seen.add(j)
    if use_m3:
        pool_text = [(j, chunks[j]) for j in range(len(chunks))]
        for i in list(chosen):
            # 显式引用：定理 1 / 公式 (1.37) / 定义2 —— 兼容 **粗体** 与括号编号
            refs = set(re.findall(
                r"(定义|定理|引理|公式)\s*[(（]?\s*([\d.]+?)\s*[)）]?(?!\d)", chunks[i]["raw"]))
            for lab, num in refs:
                num = num.rstrip(".")
                for j, o in pool_text:
                    if j in seen:
                        continue
                    if re.search(rf"\*{{0,2}}\s*{lab}\s*{num}\b", o["raw"]):
                        chosen.append(j)
                        seen.add(j)
    total, keep = 0, []
    for j in chosen:
        seg = chunks[j]["raw"]
        if total + len(seg) > budget and keep:
            continue
        keep.append(j)
        total += len(seg)
    return "\n".join(chunks[j]["raw"] for j in keep)


def eval_modules(queries, chunks, idx, m1_label):
    """2^3 组合：M1 由调用方按分块策略体现；此处 M2/M3 开关，输出 CtxRecall@5"""
    rows = {}
    for use_m2 in (False, True):
        for use_m3 in (False, True):
            key = f"M1={'on' if m1_label else 'off'}+M2={'on' if use_m2 else 'off'}+M3={'on' if use_m3 else 'off'}"
            hit = 0
            for it in queries:
                res = idx.search(it["q"], limit=5)
                top = [ci for ci, _ in res]
                ctx = assemble(chunks, top, use_m2, use_m3)
                if hit_any(it["gold_texts"], ctx):
                    hit += 1
            rows[key] = round(hit / len(queries), 4)
    return rows


# ═══════════════════════ C. 忠实度挑战集 ═══════════════════════
def build_challenge(golds, cap=80):
    """挑战集设计：
    - pos：原句 + 表述变换正例（0.6↔3/5 等归一化等价改写，不应误报）
    - 数值篡改：数字集保持型（3/5→5/3，词面基线抓不到）
    - 绑定值篡改：符号绑定改值（数字集保持）
    - 公式改写：改运算符/结构（词面成分基本不变）
    - 无支撑：错配证据
    """
    pos, neg_num, neg_bound, neg_formula, neg_unrel = [], [], [], [], []
    frac_re = re.compile(r"(\d+)\s*/\s*(\d+)")
    bound_re = re.compile(r"([A-Za-zP][A-Za-z0-9()|,]{0,10})\s*[=＝]\s*(\d+\s*/\s*\d+|\d[\d.]*)")
    for gi, g in enumerate(golds):
        t = g["text"]
        if len(t) < 30:
            continue
        ev = [{"content_text": t, "title": g["section"], "source_type": "textbook"}]
        if len(pos) < cap:
            pos.append({"claim": t, "evidence": ev, "label": 0})
        # 表述变换正例：把首个分数 3/5 改写为等值小数 0.6（不应判伪）
        mf = frac_re.search(t)
        if mf and len(pos) < cap * 2:
            a, b = int(mf.group(1)), int(mf.group(2))
            if b != 0 and a < b:
                dec = f"{a / b:.2f}".rstrip("0").rstrip(".")
                pos.append({"claim": t.replace(mf.group(0), dec, 1),
                            "evidence": ev, "label": 0})
        # 数值篡改（数字集保持）：3/5 → 5/3；0.32 → 0.23（小数位交换）
        if mf and len(neg_num) < cap:
            swapped = f"{mf.group(2)}/{mf.group(1)}"
            neg_num.append({"claim": t.replace(mf.group(0), swapped, 1),
                            "evidence": ev, "label": 1})
        md = re.search(r"\d+\.\d+", t)
        if md and len(neg_num) < cap:
            s = md.group(0)
            head, tail = s.split(".", 1)
            flipped = f"{head}.{tail[::-1]}"
            if flipped != s:
                neg_num.append({"claim": t.replace(s, flipped, 1),
                                "evidence": ev, "label": 1})
        # 绑定值篡改（数字集保持）：P(A)=3/5 → P(A)=5/3
        mb = bound_re.search(t)
        if mb and len(neg_bound) < cap:
            val = mb.group(2)
            if "/" in val:
                a, b = val.split("/", 1)
                newval = f"{b.strip()}/{a.strip()}"
            else:
                newval = val + "0" if val != "0" else "10"
            neg_bound.append({"claim": t.replace(mb.group(0), f"{mb.group(1)}={newval}", 1),
                              "evidence": ev, "label": 1})
        # 公式改写（语义级，改写点落在公式内部）：∑→∏ / 指数改变 / 变量对换
        if "=" in t and len(neg_formula) < cap:
            head, tail = t.split("=", 1)
            bad_tail = None
            for pat, rep in ((r"\\sum", r"\\prod"), (r"\^{2}", r"^{3}"),
                             (r"\\frac\{([^{}]+)\}\{n\}", r"\\frac{\1}{n^2}"),
                             (r"\\mu", r"\\sigma"), (r"P\(A\|B\)", r"P(B|A)")):
                if re.search(pat, tail):
                    bad_tail = re.sub(pat, rep, tail, count=1)
                    break
            if bad_tail is None:
                # 兜底：公式内首个数字替换（1.37→1.87 式语义改写）
                md = re.search(r"\d+\.\d+", tail)
                if md:
                    s = md.group(0)
                    flipped = s[0] + ("8" if s[2] != "8" else "9") + s[2:]
                    bad_tail = tail.replace(s, flipped, 1)
            if bad_tail and bad_tail != tail:
                neg_formula.append({"claim": head + "=" + bad_tail, "evidence": ev, "label": 1})
        # 无支撑（错配证据）
        if len(neg_unrel) < cap:
            other = golds[(gi + 11) % len(golds)]
            if other["text"] != t:
                neg_unrel.append({"claim": t, "evidence": [{"content_text": other["text"],
                                  "title": other["section"], "source_type": "textbook"}], "label": 1})
    return {"pos": pos, "数值篡改(数字集保持)": neg_num, "绑定值篡改(数字集保持)": neg_bound,
            "公式改写": neg_formula, "无支撑": neg_unrel}


def prf(items, flag_fn):
    tp = fp = tn = fn = 0
    for it in items:
        pred = flag_fn(it["claim"], it["evidence"])
        if it["label"] == 1:
            tp, fn = (tp + 1, fn) if pred else (tp, fn + 1)
        else:
            fp, tn = (fp + 1, tn) if pred else (fp, tn + 1)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return {"P": round(p, 4), "R": round(r, 4), "F1": round(f1, 4), "FPR": round(fpr, 4)}


def make_flag(use_norm, use_bound, use_formula):
    from services.faithfulness_verifier import FaithfulnessVerifier
    v = FaithfulnessVerifier(use_norm=use_norm, use_bound=use_bound, use_formula=use_formula)

    def flag(claim, evidence):
        rep = v.verify(claim, evidence)
        return any(c.missing_numbers or c.status == "unsupported" for c in rep.claims) \
            or rep.verdict in ("unfaithful", "insufficient_evidence")
    return flag


def flag_overlap_only(claim, evidence):
    ev = " ".join(e.get("content_text", "") for e in evidence)
    from core.text_utils import containment

    def tok(t):
        return set(re.findall(r"[\u4e00-\u9fff]{2}|[a-zA-Z0-9.]+", t))
    return containment(tok(claim), tok(ev)) < 0.6


def flag_lexical_num(claim, evidence):
    ev = " ".join(e.get("content_text", "") for e in evidence)
    from core.text_utils import extract_numbers
    nums = extract_numbers(claim)
    return bool(nums) and not all(n in ev for n in nums)


# ═══════════════════════ 主流程 ═══════════════════════
def main():
    R = {}
    docs = load_corpus()
    golds = extract_gold(docs)
    queries = build_queries(golds)
    print(f"文档 {len(docs)} | 金标 {len(golds)} | 查询 {len(queries)}")
    R["n_docs"], R["n_gold"], R["n_queries"] = len(docs), len(golds), len(queries)

    print("\n══ A. 检索方法对比（BM25，同一查询集）══")
    strategies = {}
    fixed_all, para_all, sem_all, tpre_all, ctxp_all, par_all, lear_all = [], [], [], [], [], [], []
    for di, d in enumerate(docs):
        fixed_all += chunks_fixed(d["text"], d["section"])
        para_all += chunks_para(d["text"], d["section"])
        sem_all += chunks_semantic(d["text"], d["section"])
        tpre_all += chunks_title_prefix(d["text"], d["section"])
        ctxp_all += chunks_ctx_prefix(d["text"], d["section"])
        par_all += chunks_parent_children(d["text"], d["section"])
        lear_all += chunks_lear(d["text"], d["section"], di)
    lear_clus_all = []
    for di, d in enumerate(docs):
        lear_clus_all += chunks_lear_clustered(d["text"], d["section"], di)
    strategies = {
        "固定长度分块（vanilla）": fixed_all,
        "段落分块": para_all,
        "语义分块": sem_all,
        "标题链前缀[19]": tpre_all,
        "上下文化前缀(Late Chunking近似)[18]": ctxp_all,
        "小块检索-大块返回(small-to-big)": par_all,
        "LEAR单元粒度（消融）": lear_all,
        "LEAR教学语义簇（本文）": lear_clus_all,
    }
    for name, chunks in strategies.items():
        idx = build_index(chunks)
        pmap = None
        if "small-to-big" in name:
            pmap = {}
            merged, slot = [], {}
            for i, c in enumerate(chunks):
                key = (c["doc"], c["order"] // 3)
                if key in slot:
                    pmap[i] = slot[key]
                else:
                    merged.append(c)
                    slot[key] = len(merged) - 1
                    pmap[i] = len(merged) - 1
            chunks = merged
            idx = build_index(chunks)
        m = eval_strategy(queries, chunks, idx, parent_map=pmap)
        R[f"{name} [BM25]"] = m
        print(f"{name:40s} BM25 {m}")
        # 向量检索（BGE-M3，系统实际检索器）
        cmat = embed_batch([c["text"] for c in chunks])
        if cmat is not None:
            qvecs = embed_batch([it["q"] for it in queries])
            mv = eval_strategy_vec(queries, chunks, qvecs, cmat)
            R[f"{name} [Vec]"] = mv
            print(f"{'':40s} Vec  {mv}")

    print("\n══ A2. SOTA 家族强基线 ══")
    sota = {}
    # Hybrid RRF（BM25 + 向量双路融合，业界标准强实践）
    idx_lear = build_index(lear_clus_all)
    cmat_lear = embed_batch([c["text"] for c in lear_clus_all])
    qmat = embed_batch([it["q"] for it in queries]) if cmat_lear is not None else None
    if cmat_lear is not None:
        import numpy as np
        cnorm = cmat_lear / (np.linalg.norm(cmat_lear, axis=1, keepdims=True) + 1e-9)
        hit = 0
        split_rrf = {"术语型": [0, 0], "标签型": [0, 0]}  # [hit, n]
        for qi, it in enumerate(queries):
            bm = [ci for ci, _ in idx_lear.search(it["q"], limit=10)]
            q = qmat[qi] / (np.linalg.norm(qmat[qi]) + 1e-9)
            vec = list(np.argsort(-(cnorm @ q))[:10])
            fused = rrf_fuse([bm, vec])[:5]
            rels = [1 if hit_any(it["gold_texts"], lear_clus_all[ci]["raw"]) else 0 for ci in fused]
            ok = 1.0 if any(rels) else 0.0
            hit += ok
            qt = it.get("qtype", "术语型")
            split_rrf[qt][0] += ok
            split_rrf[qt][1] += 1
        sota["Hybrid-RRF(BM25+Vec)"] = {"hit@5": round(hit / len(queries), 4),
            "术语型_hit@5": round(split_rrf["术语型"][0] / max(split_rrf["术语型"][1], 1), 4),
            "标签型_hit@5": round(split_rrf["标签型"][0] / max(split_rrf["标签型"][1], 1), 4)}
        print(f"  Hybrid-RRF: {sota['Hybrid-RRF(BM25+Vec)']}")

    # GraphRAG-lite（块级共现图扩展）：在 LEAR top-5 上扩展
    hit_g, n_g = 0, 0
    for it in queries:
        top = [ci for ci, _ in idx_lear.search(it["q"], limit=3)]
        expanded = graph_expansion(lear_clus_all, top)[:5]
        ctx = "\n".join(lear_clus_all[j]["raw"] for j in expanded)
        hit_g += 1 if hit_any(it["gold_texts"], ctx) else 0
        n_g += 1
    sota["GraphRAG-lite(图扩展)"] = {"ctx_recall@5": round(hit_g / max(n_g, 1), 4)}
    print(f"  GraphRAG-lite: {sota['GraphRAG-lite(图扩展)']}")

    # RAPTOR 式层级检索（抽取式变体）：叶子块 + TextRank 要点节点
    raptor_all = []
    for di, d in enumerate(docs):
        leaves = chunks_lear(d["text"], d["section"], di)
        raptor_all += chunks_raptor_nodes(d["text"], d["section"], leaves)
    idx_rap = build_index(raptor_all)
    m_rap = eval_strategy(queries, raptor_all, idx_rap)
    sota["RAPTOR式(抽取式层级)"] = m_rap
    print(f"  RAPTOR-lite: {m_rap}")

    # ColBERT 式 MaxSim（late-interaction，SOTA 家族代表）：固定/标题前缀/LEAR 三策略
    print("  ColBERT-MaxSim 编码中（token 级向量，首次较慢）...")
    q_toks = encode_token_embeddings([it["q"] for it in queries])
    if q_toks is not None:
        for label, chs in (("固定长度分块", fixed_all), ("标题链前缀[19]", tpre_all),
                           ("LEAR教学语义簇（本文）", lear_clus_all)):
            d_toks = encode_token_embeddings([c["text"] for c in chs])
            if d_toks is not None:
                mc = eval_colbert(queries, chs, q_toks, d_toks)
                sota[f"ColBERT-MaxSim+{label}"] = mc
                print(f"  ColBERT+{label}: {mc}")
    R["sota_baselines"] = sota

    print("\n══ B. 模块消融 2^3（CtxRecall@5；M1=结构分块，M2=同节邻域组装，M3=依赖回链）══")
    abl = {}
    abl.update(eval_modules(queries, fixed_all, build_index(fixed_all), m1_label=False))
    abl.update(eval_modules(queries, lear_clus_all, build_index(lear_clus_all), m1_label=True))
    for k, v in abl.items():
        print(f"  {k:28s} CtxRecall@5={v}")
    R["ablation_modules"] = abl

    print("\n══ C. 忠实度：外部基线 + 通道消融 2^3 ══")
    ch = build_challenge(golds)
    all_items = sum(ch.values(), [])
    print(f"  挑战集: " + " ".join(f"{k}={len(v)}" for k, v in ch.items()))
    baselines = {
        "词面重叠基线": flag_overlap_only,
        "词面数字锚点基线": flag_lexical_num,
        "稠密蕴含基线(NLI近似)": (lambda c, e: flag_dense_entail(c, e)),
        "符号锚点（本文全量）": make_flag(True, True, True),
    }
    faith = {}
    for name, fn in baselines.items():
        faith[name] = prf(all_items, fn)
        print(f"  {name:16s} {faith[name]}")
    abl_ch = {}
    for use_n in (False, True):
        for use_b in (False, True):
            for use_f in (False, True):
                key = f"F1={'on' if use_n else 'off'}+F2={'on' if use_b else 'off'}+F3={'on' if use_f else 'off'}"
                abl_ch[key] = prf(all_items, make_flag(use_n, use_b, use_f))
    for k, v in abl_ch.items():
        print(f"  {k:30s} {v}")
    # 分类别召回
    cat = {}
    full = make_flag(True, True, True)
    lex = flag_lexical_num
    for cname, items in ch.items():
        if cname == "pos":
            continue
        cat[cname] = {"本文": prf(items, full)["R"], "词面基线": prf(items, lex)["R"]}
    print("  类别召回:", cat)
    faith["ablation_channels"] = abl_ch
    faith["by_category"] = cat
    R["faithfulness"] = faith

    OUT_JSON.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {OUT_JSON}")


if __name__ == "__main__":
    main()
