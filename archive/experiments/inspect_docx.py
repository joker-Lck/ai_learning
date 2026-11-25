# -*- coding: utf-8 -*-
"""检查论文 docx 的正文结构：段落与表格顺序"""
import docx

P = r"C:\Users\Administrator\Desktop\edu-rag-papers\教育RAG创新论文.docx"
d = docx.Document(P)
print("paragraphs:", len(d.paragraphs), "tables:", len(d.tables))
print("--- body 元素顺序（段落/表格）---")
from docx.table import Table
from docx.text.paragraph import Paragraph
for i, el in enumerate(d.element.body):
    if el.tag.endswith("}p"):
        p = Paragraph(el, d)
        t = p.text[:60]
        if t.strip():
            print(f"[{i}] P style={p.style.name!r}: {t}")
    elif el.tag.endswith("}tbl"):
        tb = Table(el, d)
        head = " | ".join(c.text[:12] for c in tb.rows[0].cells) if tb.rows else ""
        print(f"[{i}] TABLE {len(tb.rows)}x{len(tb.columns)} head: {head}")
