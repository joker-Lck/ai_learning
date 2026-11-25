# -*- coding: utf-8 -*-
"""调试：chunk 偏移语义与 GT 对齐"""
import os
import re
import sys

ROOT = r"F:\项目\ai教学辅助系统"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from data.structure_chunker import StructureChunker

CORPUS = os.path.join(ROOT, "experiments", "corpus_textbook")
chapter = "第一章 随机事件及其概率"
cdir = os.path.join(CORPUS, chapter)
files = [f for f in os.listdir(cdir) if re.match(r"^\d+\.\d+\s.*\.md$", f)]
files.sort(key=lambda s: [int(x) for x in re.findall(r"\d+", s.split(" ")[0])])
parts = [chapter]
for f in files:
    t = open(os.path.join(cdir, f), encoding="utf-8").read()
    t = re.sub(r"^#{1,4}\s*", "", t, flags=re.M)
    parts.append(t)
text = "\n\n".join(parts)

tree = StructureChunker(max_length=900, min_length=60).chunk(text, doc_id=1)
print("text len:", len(text), "chunks:", len(tree.chunks))
for c in tree.chunks[:6]:
    seg = text[c.char_start:c.char_end]
    match = seg.strip() == c.text.strip()
    print(f"[{c.order}] kind={c.kind} span=({c.char_start},{c.char_end}) match={match}")
    print("   chunk.text head:", c.text[:60].replace("\n", " "))
    print("   text[span] head:", seg[:60].replace("\n", " "))
    print("   path:", c.section_path[:50])
