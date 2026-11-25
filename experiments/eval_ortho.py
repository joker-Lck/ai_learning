# -*- coding: utf-8 -*-
"""正交组合检索实验：教学结构分块 × (标题链 + 上下文头注入)
回应"核心卖点结构证据在检索指标上没兑现"——测量组合后能否不落后/领先。
"""
import sys, os, json, re
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
spec = u.spec_from_file_location("ev", "experiments/eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

docs = ev.load_corpus()
golds = ev.extract_gold(docs)
queries = ev.build_queries(golds)
print("queries:", len(queries))

def ortho_units(text, section, doc_id, head_n=80):
    """结构单元 + 标题链 + 文档头注入（正交组合）"""
    tree_chunks = ev.chunks_lear(text, section, doc_id)
    head = re.sub(r"\s+", " ", text)[:head_n]
    out = []
    for c in tree_chunks:
        out.append({**c, "text": f"{c['section_path']} >> {head} >> {c['raw']}"})
    return out

def ortho_clusters(text, section, doc_id, head_n=80):
    clus = ev.chunks_lear_clustered(text, section, doc_id)
    head = re.sub(r"\s+", " ", text)[:head_n]
    out = []
    for c in clus:
        out.append({**c, "text": f"{c['section_path']} >> {head} >> {c['raw']}"})
    return out

for name, fn in (("LEAR-Ortho单元", ortho_units), ("LEAR-Ortho簇", ortho_clusters)):
    chunks = []
    for di, d in enumerate(docs):
        chunks += fn(d["text"], d["section"], di)
    idx = ev.build_index(chunks)
    m = ev.eval_strategy(queries, chunks, idx)
    print(f"{name} BM25: {m}")
    cmat = ev.embed_batch([c["text"] for c in chunks])
    qmat = ev.embed_batch([it["q"] for it in queries])
    mv = ev.eval_strategy_vec(queries, chunks, qmat, cmat)
    print(f"{name} Vec : {mv}")
    try:
        jf = json.load(open("experiments/ortho_results.json", encoding="utf-8"))
    except Exception:
        jf = {}
    jf[f"{name} [BM25]"] = m
    jf[f"{name} [Vec]"] = mv
    json.dump(jf, open("experiments/ortho_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("→ experiments/ortho_results.json")
