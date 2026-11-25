# -*- coding: utf-8 -*-
"""表3 两行补充指标：A+标记重排 / 意图路由系统"""
import sys, re
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
import os
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
import numpy as np
spec = u.spec_from_file_location("ev", r"F:\项目\ai教学辅助系统\experiments\eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

docs = ev.load_corpus()
golds = ev.extract_gold(docs)
queries = ev.build_queries(golds)


def ortho_clusters(text, section, doc_id, head_n=80):
    clus = ev.chunks_lear_clustered(text, section, doc_id)
    head = re.sub(r"\s+", " ", text)[:head_n]
    return [{**c, "text": f"{c['section_path']} >> {head} >> {c['raw']}"} for c in clus]


viewA, viewB = [], []
for di, d in enumerate(docs):
    viewA += ev.chunks_lear(d["text"], d["section"], di)
    viewB += ortho_clusters(d["text"], d["section"], di)


def ranks_of(view):
    cmat = ev.embed_batch([c["text"] for c in view])
    qmat = ev.embed_batch([it["q"] for it in queries])
    cnorm = cmat / (np.linalg.norm(cmat, axis=1, keepdims=True) + 1e-9)
    out = []
    for qi in range(len(queries)):
        q = qmat[qi] / (np.linalg.norm(qmat[qi]) + 1e-9)
        out.append(list(np.argsort(-(cnorm @ q))[:20]))
    return out


A_r, B_r = ranks_of(viewA), ranks_of(viewB)


def metrics_of(get_top):
    agg = {k: [] for k in ("h1", "h5", "mrr", "ndcg")}
    split = {"术语型": [], "标签型": []}
    for qi, it in enumerate(queries):
        top = get_top(qi)
        rels = [1 if ev.hit_any(it["gold_texts"], c["raw"]) else 0 for c in top[:5]]
        rels += [0] * (5 - len(rels))
        h1, h5, r5, mrr, ndcg = ev.metrics5(rels)
        for k, v in zip(("h1", "h5", "mrr", "ndcg"), (h1, h5, mrr, ndcg)):
            agg[k].append(v)
        split[it.get("qtype", "术语型")].append(h5)
    out = {k: round(sum(v) / len(v), 4) for k, v in agg.items()}
    for qt, lst in split.items():
        if lst:
            out[f"{qt}_h5"] = round(sum(lst) / len(lst), 4)
    return out


def boosted(qi):
    ranked = list(A_r[qi])
    it = queries[qi]
    if it["qtype"] == "标签型":
        m = re.search(r"(定义|定理|引理|例题|例|公式)\s*(\d+)", it["q"])
        if m:
            pat = re.compile(rf"\*{{0,2}}\s*{m.group(1)}\s*{m.group(2)}\b")
            front = [ci for ci in ranked if pat.search(viewA[ci]["raw"][:30])]
            rest = [ci for ci in ranked if ci not in set(front)]
            ranked = front + rest
    return [viewA[ci] for ci in ranked]


def routed(qi):
    it = queries[qi]
    if it["qtype"] == "标签型":
        return boosted(qi)
    return [viewB[ci] for ci in B_r[qi]]


print("RESULT A_boost:", metrics_of(boosted))
print("RESULT routed:", metrics_of(routed))
