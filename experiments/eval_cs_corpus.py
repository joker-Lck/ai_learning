# -*- coding: utf-8 -*-
"""跨学科鲁棒性实验：计算机学科语料（无教学标记的段落式文本）
目的：验证方法在缺少教学标记/章节结构的语料上不劣化（泛化边界）。
协议：段落=知识单元；查询="什么是X"（X=段落首术语）；严格单金标；BM25+向量。
"""
import sys, os, re
sys.path.insert(0, r"F:\项目\ai教学辅助系统")
os.chdir(r"F:\项目\ai教学辅助系统")
import importlib.util as u
import numpy as np
spec = u.spec_from_file_location("ev", r"F:\项目\ai教学辅助系统\experiments\eval_lear_paper.py")
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

# ── 语料与金标（段落式）──
text = open(r"F:\项目\ai教学辅助系统\data\corpus\education_corpus.txt", encoding="utf-8").read()
paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if len(p.strip()) >= 60]
golds = []
for p in paras:
    m = re.match(r"^([一-鿿A-Za-z]{2,12})(是|为)", p)
    if m:
        golds.append({"kind": "body", "label": "段落", "term": m.group(1),
                      "text": p[:900], "section": "计算机学科基础", "doc": 0})
seen = set()
uniq = []
for g in golds:
    if g["term"] not in seen:
        seen.add(g["term"])
        uniq.append(g)
golds = uniq
print(f"段落金标: {len(golds)}")

queries = []
for i, g in enumerate(golds):
    for q in (f"什么是{g['term']}？", f"请解释{g['term']}"):
        if 4 <= len(q) <= 30:
            queries.append({"q": q, "gold": g, "qtype": "术语型", "gold_texts": [g["text"]]})
print(f"查询: {len(queries)}")

# ── 各策略（同一 flat 语料）──
def learr_units(text, section):
    return ev.chunks_lear(text, section, 0)

strategies = {
    "固定长度分块": ev.chunks_fixed(text, "计算机学科基础"),
    "段落分块": ev.chunks_para(text, "计算机学科基础"),
    "LEAR单元(无结构语料)": learr_units(text, "计算机学科基础"),
}

for name, chunks in strategies.items():
    idx = ev.build_index(chunks)
    m = ev.eval_strategy(queries, chunks, idx)
    cmat = ev.embed_batch([c["text"] for c in chunks])
    qmat = ev.embed_batch([it["q"] for it in queries])
    mv = ev.eval_strategy_vec(queries, chunks, qmat, cmat)
    print(f"RESULT {name} BM25: {m}")
    print(f"RESULT {name} Vec : {mv}")
