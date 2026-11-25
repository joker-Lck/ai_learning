# -*- coding: utf-8 -*-
"""删除 ai_rag_knowledge.db 前，把有价值的文档正文提取为语料 JSON"""
import sqlite3
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "databases", "ai_rag_knowledge.db")
OUT = os.path.join(ROOT, "experiments", "corpus_from_local_db.json")

conn = sqlite3.connect(DB)
rows = conn.execute("SELECT id, title, subject, file_type, document_data FROM knowledge_documents").fetchall()
corpus = []
for did, title, subject, ftype, ddata in rows:
    try:
        parsed = json.loads(ddata) if ddata else {}
    except Exception:
        continue
    content = parsed.get("content") or {}
    raw = content.get("raw_text") or ""
    if len(raw) < 5000:  # 只保留有实质正文的文档
        continue
    corpus.append({
        "source": f"local_db:knowledge_documents#{did}",
        "title": title,
        "subject": subject,
        "file_type": ftype,
        "chars": len(raw),
        "text": raw,
    })
conn.close()

# 去重（title+chars 完全相同的只留一份）
seen, uniq = set(), []
for c in corpus:
    key = (c["title"], c["chars"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(c)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(uniq, f, ensure_ascii=False, indent=1)
print(f"extracted {len(uniq)} docs -> {OUT}")
for c in uniq:
    print(f"  [{c['chars']}] {c['title']}")
