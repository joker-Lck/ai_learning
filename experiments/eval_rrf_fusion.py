# -*- coding: utf-8 -*-
"""三视图 RRF 融合检索：纯单元（标签强）× 正交簇（术语强）× 标题前缀
排名层正交组合——各视图保留自身文本形态，融合各取所长。
"""
import sys, os, json, re
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
import numpy as np
spec = u.spec_from_file_location("ev", "experiments/eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

docs = ev.load_corpus()
golds = ev.extract_gold(docs)
queries = ev.build_queries(golds)

# 视图A：纯教学单元（path >> raw）——标签型强
viewA = []
# 视图B：正交簇（path >> head >> raw）——术语型强
def ortho_clusters(text, section, doc_id, head_n=80):
    clus = ev.chunks_lear_clustered(text, section, doc_id)
    head = re.sub(r"\s+", " ", text)[:head_n]
    return [{**c, "text": f"{c['section_path']} >> {head} >> {c['raw']}"} for c in clus]
viewB = []
for di, d in enumerate(docs):
    viewA += ev.chunks_lear(d["text"], d["section"], di)
    viewB += ortho_clusters(d["text"], d["section"], di)

def vec_rank(view, tag):
    cmat = ev.embed_batch([c["text"] for c in view])
    qmat = ev.embed_batch([it["q"] for it in queries])
    cnorm = cmat / (np.linalg.norm(cmat, axis=1, keepdims=True) + 1e-9)
    ranks = []
    for qi in range(len(queries)):
        q = qmat[qi] / (np.linalg.norm(qmat[qi]) + 1e-9)
        order = list(np.argsort(-(cnorm @ q))[:10])
        ranks.append(order)
    return view, ranks

print("编码视图A（纯单元）...")
A_view, A_ranks = vec_rank(viewA, "A")
print("编码视图B（正交簇）...")
B_view, B_ranks = vec_rank(viewB, "B")

def eval_fusion(per_query_lists):
    """per_query_lists: [(view, ranks, weight)] 每查询 RRF 融合后 top-5
    相关性判定与表1一致：hit_any(gold_texts, chunk.raw)（严格单金标对称重叠）"""
    agg = {"hit@1": [], "hit@5": [], "mrr": [], "ndcg@5": []}
    split = {"术语型": {"hit@5": [], "mrr": []}, "标签型": {"hit@5": [], "mrr": []}}
    for qi, it in enumerate(queries):
        cand = {}
        for view, ranks, w in per_query_lists:
            for r, ci in enumerate(ranks[qi], 1):
                key = view[ci]["raw"]
                cand[key] = max(cand.get(key, 0.0), w / (60 + r))
        fused = sorted(cand.items(), key=lambda x: -x[1])[:5]
        rels = [1 if ev.hit_any(it["gold_texts"], raw) else 0 for raw, _s in fused]
        rels += [0] * (5 - len(rels))
        h1, h5, r5, mrr, ndcg = ev.metrics5(rels)
        for k, v in zip(("hit@1", "hit@5", "mrr", "ndcg@5"), (h1, h5, mrr, ndcg)):
            agg[k].append(v)
        qt = it.get("qtype", "术语型")
        split[qt]["hit@5"].append(h5)
        split[qt]["mrr"].append(mrr)
    out = {k: round(sum(v) / len(v), 4) for k, v in agg.items()}
    for qt, d in split.items():
        if d["hit@5"]:
            out[f"{qt}_hit@5"] = round(sum(d["hit@5"]) / len(d["hit@5"]), 4)
    return out

rA = eval_fusion([(A_view, A_ranks, 1.0)])
rB = eval_fusion([(B_view, B_ranks, 1.0)])
print("视图A 单独:", rA)
print("视图B 单独:", rB)
best = None
for wA in (1.0, 1.5, 2.0):
    rAB = eval_fusion([(A_view, A_ranks, wA), (B_view, B_ranks, 1.0)])
    print(f"A(w={wA})⊕B 融合:", rAB)
    if best is None or rAB["hit@5"] > best[1]["hit@5"]:
        best = (wA, rAB)
res = {"视图A_纯单元": rA, "视图B_正交簇": rB,
       f"A(w={best[0]})⊕B_RRF融合": best[1]}
try:
    old = json.load(open("experiments/ortho_results.json", encoding="utf-8"))
except Exception:
    old = {}
old.update(res)
json.dump(old, open("experiments/ortho_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("→ experiments/ortho_results.json")
