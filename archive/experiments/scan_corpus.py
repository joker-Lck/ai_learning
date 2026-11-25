# -*- coding: utf-8 -*-
"""扫描教材语料的标题/语义标记模式"""
import os
import re
import collections

ROOT = r"F:\项目\ai教学辅助系统\experiments\corpus_textbook"
pat_heading = re.compile(r"^(#{1,4})\s*(.+)$", re.M)
pat_units = [
    ("定义", re.compile(r"定义\s*\d*\s*[：:．.]?")),
    ("定理", re.compile(r"定理\s*\d*\s*[（(][^）)]{0,20}[）)]?\s*[：:．.]?")),
    ("例", re.compile(r"例题?\s*\d+\s*[：:．.]?|例\s*[：:．.]")),
    ("证明", re.compile(r"证明\s*[：:．.]")),
    ("注意", re.compile(r"注意\s*[：:．.]")),
    ("公式", re.compile(r"公式\s*[：:．.]")),
]
stats = collections.Counter()
heading_levels = collections.Counter()
samples = collections.defaultdict(list)

for dp, dn, fn in os.walk(ROOT):
    for f in sorted(fn):
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
        for m in pat_heading.finditer(t):
            heading_levels[len(m.group(1))] += 1
            if len(samples["h" + m.group(1)]) < 3:
                samples["h" + m.group(1)].append(m.group(2)[:50])
        for name, p in pat_units:
            for m in p.finditer(t):
                stats[name] += 1
                if len(samples[name]) < 3:
                    samples[name].append(t[m.start():m.start() + 40].replace("\n", " "))

print("heading levels:", dict(heading_levels))
print("unit markers:", dict(stats))
for k in sorted(samples):
    print(f"--- {k} ---")
    for s in samples[k]:
        print("   ", s)
