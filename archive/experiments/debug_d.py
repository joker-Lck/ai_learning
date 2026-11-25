# -*- coding: utf-8 -*-
"""诊断 D 指标失败样本"""
import os
import re
import sys

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from data.structure_chunker import StructureChunker, expand_context

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
UNIT_START = re.compile(
    r"(?:^\*\*(定义|定理|引理|推论|性质|公式|例)\s*(\d+)?\*\*)|(?:^(证|证明|解)\s*[：:])|(?:^(注意)\s*[：:])",
    re.M,
)

chapter = "第一章 随机事件及其概率"
cdir = os.path.join(CORPUS, chapter)
files = [f for f in os.listdir(cdir) if re.match(r"^\d+\.\d+\s.*\.md$", f)]
files.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s.split(" ")[0])])
parts = [chapter]
for f in files:
    t = re.sub(r"^#{1,4}\s*", "", open(os.path.join(cdir, f), encoding="utf-8").read(), flags=re.M)
    parts.append(t)
text = "\n\n".join(parts)

units = []
for m in UNIT_START.finditer(text):
    units.append({"start": m.start(), "label": m.group(1) or m.group(3) or m.group(4)})
for i, u in enumerate(units):
    u["end"] = units[i + 1]["start"] if i + 1 < len(units) else len(text)

tree = StructureChunker(max_length=900, min_length=60).chunk(text, doc_id=1)
s_chunks = [c.to_dict() for c in tree.chunks]
by_id = {c["chunk_id"]: c for c in s_chunks}
avg = sum(len(c["text"]) for c in s_chunks) / len(s_chunks)
w = max(1, int(4800 / avg / 2))
print(f"chunks={len(s_chunks)} avg={avg:.0f} w={w}")

fails = 0
for u in units:
    span = u["end"] - u["start"]
    if span < 30:
        continue
    hit = next((c for c in s_chunks if c["char_start"] <= u["start"] < c["char_end"]), None)
    if not hit:
        continue
    got = expand_context([hit], s_chunks, max_chars=4800, neighbor_window=w)
    covered = 0
    ids = []
    for g in got:
        ids += g.get("chunk_ids") or []
        for cid in g.get("chunk_ids") or []:
            cc = by_id.get(cid)
            if cc:
                covered += max(0, min(cc["char_end"], u["end"]) - max(cc["char_start"], u["start"]))
    ratio = covered / span
    if ratio < 0.95:
        fails += 1
        if fails <= 6:
            print(f"\nFAIL kind={u['label']} span=({u['start']},{u['end']}) len={span} cover={ratio:.2f}")
            print(f"  unit head: {text[u['start']:u['start']+50]!r}")
            print(f"  hit order={hit.get('order')} path={hit.get('section_path')!r}")
            spans = sorted((by_id[c]['char_start'], by_id[c]['char_end']) for c in ids if c in by_id)
            if spans:
                print(f"  assembled span=({spans[0][0]},{spans[-1][1]}) n={len(spans)}")
                gap_lo = spans[0][0] - u['start']
                gap_hi = u['end'] - spans[-1][1]
                print(f"  miss_left={gap_lo} miss_right={gap_hi}")
            else:
                print("  assembled=EMPTY")
print(f"\ntotal fails shown from doc1: {fails}")
