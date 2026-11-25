# -*- coding: utf-8 -*-
"""QA：验证改稿后的 docx"""
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

P = r"C:\Users\Administrator\Desktop\edu-rag-papers\教育RAG创新论文（实验数据版）.docx"
d = docx.Document(P)
print("opened OK | paragraphs:", len(d.paragraphs), "tables:", len(d.tables))

bad = [p.text for p in d.paragraphs if any(k in p.text for k in ("TODO", "TBD", "{{", "lorem", "XXXX"))]
print("placeholder residue:", bad or "none")

print("\n--- 第 4 章内容 ---")
in4 = False
n_tbl = 0
for el in d.element.body:
    if el.tag.endswith("}p"):
        p = Paragraph(el, d)
        t = p.text.strip()
        if t.startswith("4　实验与分析"):
            in4 = True
        if t.startswith("5　结论"):
            in4 = False
        if in4 and t:
            print(f"P: {t[:80]}")
    elif el.tag.endswith("}tbl") and in4:
        tb = Table(el, d)
        n_tbl += 1
        print(f"TABLE#{n_tbl} {len(tb.rows)}x{len(tb.columns)}: {' | '.join(c.text[:10] for c in tb.rows[0].cells)}")
        for row in tb.rows[1:]:
            print("   ", " | ".join(c.text[:16] for c in row.cells))

print("\n--- 摘要首尾 ---")
for p in d.paragraphs:
    if p.text.startswith("摘要："):
        print(p.text[:120], "……", p.text[-120:])
