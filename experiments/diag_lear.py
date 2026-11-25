# -*- coding: utf-8 -*-
"""诊断：LEAR 术语型查询失分原因 —— 算法问题 or 指标/实现问题"""
import sys, re
sys.path.insert(0, r'F:\项目\ai教学辅助系统')
import os
os.chdir(r'F:\项目\ai教学辅助系统')
from pathlib import Path
import importlib.util as u
spec = u.spec_from_file_location('ev', r'F:\项目\ai教学辅助系统\experiments\eval_lear_paper.py')
ev = u.module_from_spec(spec)
spec.loader.exec_module(ev)

docs = ev.load_corpus()
golds = ev.extract_gold(docs)
queries = ev.build_queries(golds)

# 构建 LEAR 单元粒度与固定分块
lear_all, fixed_all = [], []
for di, d in enumerate(docs):
    lear_all += ev.chunks_lear(d['text'], d['section'], di)
    fixed_all += ev.chunks_fixed(d['text'], d['section'])

idx_lear = ev.build_index(lear_all)
idx_fixed = ev.build_index(fixed_all)

def term_of(q):
    m = re.match(r'^什么是(.+?)？', q['q'])
    return m.group(1) if m else (re.match(r'^(.+?)的定义是什么？', q['q']) or ['',''])[1]

n_term = lear_miss_fixed_hit = 0
both_miss = 0
gold_has_term = 0
term_in_chunk = 0
samples = []
for it in queries:
    if it['qtype'] != '术语型':
        continue
    n_term += 1
    term = term_of(it)
    rels_l = [ev.hit_any(it['gold_texts'], lear_all[ci]['raw']) for ci, _ in idx_lear.search(it['q'], 5)]
    rels_f = [ev.hit_any(it['gold_texts'], fixed_all[ci]['raw']) for ci, _ in idx_fixed.search(it['q'], 5)]
    hit_l, hit_f = any(rels_l), any(rels_f)
    # 术语是否出现在金标文本中
    g_in = any(term[:4] in gt for gt in it['gold_texts'])
    if g_in:
        gold_has_term += 1
    if not hit_l:
        if hit_f:
            lear_miss_fixed_hit += 1
            if len(samples) < 8:
                # 看 LEAR 检索回来了什么
                tops = idx_lear.search(it['q'], 3)
                samples.append((it['q'], term, [(lear_all[ci]['kind'], lear_all[ci]['raw'][:38].replace('\n',' ')) for ci, _ in tops],
                                [gt[:38].replace('\n',' ') for gt in it['gold_texts'][:2]],
                                any(term[:4] in lear_all[ci]['raw'] for ci, _ in tops)))
        else:
            both_miss += 1

print(f'术语型查询总数: {n_term}')
print(f'金标文本含术语(前4字)的比例: {gold_has_term}/{n_term} = {gold_has_term/n_term:.2f}')
print(f'LEAR失分且固定分块命中: {lear_miss_fixed_hit}')
print(f'两者都失分: {both_miss}')
print()
for q, term, tops, golds_t, term_in_top in samples:
    print(f'Q: {q}  (术语={term})')
    print(f'   gold : {golds_t}')
    print(f'   LEAR : {tops}')
    print(f'   top含术语: {term_in_top}')
    print()

# 块长分布
import statistics
ll = [len(c['raw']) for c in lear_all]
fl = [len(c['raw']) for c in fixed_all]
print(f'LEAR 块长: mean={statistics.mean(ll):.0f} median={statistics.median(ll):.0f} max={max(ll)}')
print(f'固定 块长: mean={statistics.mean(fl):.0f} median={statistics.median(fl):.0f}')
# 金标跨块情况：金标是否被单块完全覆盖
covered = 0
for g in golds:
    if any(ev.is_relevant(g['text'], c['raw']) for c in lear_all):
        covered += 1
print(f'金标被 LEAR 单块以对称判据覆盖: {covered}/{len(golds)}')
