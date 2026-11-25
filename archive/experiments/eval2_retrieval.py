# -*- coding: utf-8 -*-
"""
E2 检索对比实验：结构感知检索 vs 基线（等语料、等嵌入、等预算）
臂：
  fixed_vec    固定700分块 + 向量检索
  struct_vec   结构分块 + 向量检索
  struct_bm25  结构分块 + BM25
  struct_hybrid结构分块 + BM25×向量 RRF
  lear         struct_hybrid 命中 + 同节邻域组装（expand_context）
指标：Recall@5 / MRR@5 / nDCG@5（金标准=语义单元 span，命中=覆盖≥60%）
"""
import json
import math
import os
import re
import sys

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from data.structure_chunker import StructureChunker, expand_context  # noqa: E402
from data.bm25_softmax import BM25Index  # noqa: E402

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
QFILE = os.path.join(ROOT, "experiments", "eval2_queries.json")
OUT = os.path.join(ROOT, "experiments", "eval2_retrieval_results.json")
TOPK = 5

UNIT_START = re.compile(
    r"(?:^\*\*(定义|定理|引理|推论|性质|公式|例)\s*(\d+)?\*\*)|(?:^(证|证明|解)\s*[：:])|(?:^(注意)\s*[：:])",
    re.M,
)
KIND_MAP = {"定义": "definition", "定理": "theorem", "引理": "theorem", "推论": "theorem",
            "性质": "theorem", "公式": "theorem", "例": "example",
            "证": "proof", "证明": "proof", "解": "proof", "注意": "note"}


def load_docs():
    docs = {}
    for chapter in sorted(os.listdir(CORPUS)):
        cdir = os.path.join(CORPUS, chapter)
        if not os.path.isdir(cdir) or not re.match(r"第[一二三四五六七]章", chapter):
            continue
        files = [f for f in os.listdir(cdir) if re.match(r"^\d+\.\d+\s.*\.md$", f)]
        if not files:
            continue
        files.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s.split(" ")[0])])
        parts = [chapter]
        for f in files:
            t = re.sub(r"^#{1,4}\s*", "", open(os.path.join(cdir, f), encoding="utf-8").read(), flags=re.M)
            parts.append(t)
        docs[chapter] = "\n\n".join(parts)
    return docs


def gt_units(text):
    units = []
    for m in UNIT_START.finditer(text):
        label = m.group(1) or m.group(3) or m.group(4)
        units.append({"start": m.start(), "kind": KIND_MAP[label]})
    for i, u in enumerate(units):
        u["end"] = units[i + 1]["start"] if i + 1 < len(units) else len(text)
    return units


def fixed_chunks(text, size=700):
    n = math.ceil(len(text) / size)
    return [{"chunk_id": f"f{i}", "order": i, "char_start": i * size,
             "char_end": min((i + 1) * size, len(text)), "text": text[i * size:(i + 1) * size],
             "section_path": "", "doc_id": "fixed", "kind": "body"}
            for i in range(n)]


def embed_all(texts, tag):
    from data.embedding_service import embedding_service as es
    vecs = []
    for i in range(0, len(texts), 32):
        batch = texts[i:i + 32]
        vecs.extend(es._encode_batch(batch))
        if (i // 32) % 10 == 0:
            print(f"  [{tag}] {i+len(batch)}/{len(texts)}")
    return vecs


def cos_topk(qv, matrix, k):
    import numpy as np
    q = np.asarray(qv, dtype="float32")
    m = np.asarray(matrix, dtype="float32")
    sims = m @ q / (np.linalg.norm(m, axis=1) * np.linalg.norm(q) + 1e-9)
    idx = np.argsort(-sims)[:k]
    return [(int(i), float(sims[i])) for i in idx]


def rrf_fuse(lists, k=60, limit=TOPK):
    scores = {}
    for ranked in lists:
        for rank, (cid, _) in enumerate(ranked):
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])[:limit]


def span_coverage(item_spans, u):
    """item_spans: [(lo,hi)] 与单元 [s,e) 的覆盖率"""
    s, e = u["unit_start"], u["unit_end"]
    covered = 0
    for lo, hi in item_spans:
        covered += max(0, min(hi, e) - max(lo, s))
    return covered / max(e - s, 1)


def rank_metrics(hits):
    """hits: [0/1] 按排名"""
    recall = 1.0 if any(hits) else 0.0
    mrr = 0.0
    for r, h in enumerate(hits, 1):
        if h:
            mrr = 1.0 / r
            break
    dcg = sum(h / math.log2(r + 1) for r, h in enumerate(hits, 1))
    ideal = [1] * min(1, len(hits))
    idcg = sum(h / math.log2(r + 1) for r, h in enumerate(ideal, 1))
    return recall, mrr, dcg / idcg if idcg else 0.0


def main():
    docs = load_docs()
    queries = json.load(open(QFILE, encoding="utf-8"))
    print(f"docs={len(docs)} queries={len(queries)}")

    # ── 建块 ──
    chunker = StructureChunker(max_length=900, min_length=60)
    struct_chunks, fixed_chunks_all = [], []
    struct_by_doc, fixed_by_doc = {}, {}
    for doc, text in docs.items():
        tree = chunker.chunk(text, doc_id=doc)
        for c in tree.chunks:
            d = c.to_dict()
            d["doc_id"] = doc
            struct_chunks.append(d)
        struct_by_doc[doc] = struct_chunks[-len(tree.chunks):]
        fc = fixed_chunks(text)
        for c in fc:
            c["doc_id"] = doc
        fixed_chunks_all.extend(fc)
        fixed_by_doc[doc] = fc
    print(f"struct chunks={len(struct_chunks)} fixed chunks={len(fixed_chunks_all)}")

    # ── 嵌入 ──
    struct_vecs = embed_all([c["text"] for c in struct_chunks], "struct")
    fixed_vecs = embed_all([c["text"] for c in fixed_chunks_all], "fixed")
    query_vecs = embed_all([q["query"] for q in queries], "query")

    # ── BM25（结构块与固定块各建一份）──
    bm25_s = BM25Index()
    bm25_s.build([{"id": i, "text": c["text"]} for i, c in enumerate(struct_chunks)])
    bm25_f = BM25Index()
    bm25_f.build([{"id": i, "text": c["text"]} for i, c in enumerate(fixed_chunks_all)])

    import numpy as np
    s_mat = np.asarray(struct_vecs, dtype="float32")
    f_mat = np.asarray(fixed_vecs, dtype="float32")
    s_norm = s_mat / (np.linalg.norm(s_mat, axis=1, keepdims=True) + 1e-9)
    f_norm = f_mat / (np.linalg.norm(f_mat, axis=1, keepdims=True) + 1e-9)

    arms = ["fixed_vec", "struct_vec", "struct_bm25", "struct_hybrid", "lear"]
    agg = {a: {"recall": [], "mrr": [], "ndcg": []} for a in arms}
    per_kind = {a: {} for a in arms}

    for qi, q in enumerate(queries):
        u = {"unit_start": q["unit_start"], "unit_end": q["unit_end"]}
        qv = query_vecs[qi]

        # 各臂取 top-k 个 (chunk_index, score)
        sv = cos_topk(qv, s_norm, TOPK)
        fv = cos_topk(qv, f_norm, TOPK)
        sb = bm25_s.search(q["query"], TOPK)
        fb = bm25_f.search(q["query"], TOPK)
        hybrid = rrf_fuse([sv, sb], limit=TOPK)

        def hits_from(pairs, spans_lookup):
            out = []
            for cid, _ in pairs:
                out.append(1 if span_coverage(spans_lookup(cid), u) >= 0.6 else 0)
            while len(out) < TOPK:
                out.append(0)
            return out[:TOPK]

        s_spans = lambda cid: [(struct_chunks[cid]["char_start"], struct_chunks[cid]["char_end"])]
        f_spans = lambda cid: [(fixed_chunks_all[cid]["char_start"], fixed_chunks_all[cid]["char_end"])]

        arm_hits = {
            "fixed_vec": hits_from(fv, f_spans),
            "struct_vec": hits_from(sv, s_spans),
            "struct_bm25": hits_from(sb, s_spans),
            "struct_hybrid": hits_from(hybrid, s_spans),
        }

        # LEAR：hybrid top3 命中各自组装（同节邻域），按组装覆盖判定
        lear_hits = []
        for cid, _ in hybrid[:3]:
            hit = struct_chunks[cid]
            doc_chunks = struct_by_doc.get(hit["doc_id"], [])
            got = expand_context([hit], doc_chunks, max_chars=4800, neighbor_window=2)
            spans = []
            by_id = {c["chunk_id"]: c for c in doc_chunks}
            for g in got:
                for ccid in g.get("chunk_ids") or []:
                    cc = by_id.get(ccid)
                    if cc:
                        spans.append((cc["char_start"], cc["char_end"]))
            lear_hits.append(1 if span_coverage(spans, u) >= 0.6 else 0)
        while len(lear_hits) < TOPK:
            lear_hits.append(0)
        arm_hits["lear"] = lear_hits[:TOPK]

        for a in arms:
            r, m, n = rank_metrics(arm_hits[a])
            agg[a]["recall"].append(r)
            agg[a]["mrr"].append(m)
            agg[a]["ndcg"].append(n)
            per_kind[a].setdefault(q["kind"], []).append(r)

        if (qi + 1) % 30 == 0:
            print(f"  [{qi+1}/{len(queries)}]")

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    results = {
        "n_queries": len(queries),
        "n_chunks": {"struct": len(struct_chunks), "fixed": len(fixed_chunks_all)},
        "overall": {a: {m: mean(agg[a][m]) for m in ("recall", "mrr", "ndcg")} for a in arms},
        "recall_by_kind": {a: {k: mean(v) for k, v in per_kind[a].items()} for a in arms},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
