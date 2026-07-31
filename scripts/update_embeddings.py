"""更新知识库 embedding（增量：只为缺失的文档生成）"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from data.embedding_service import embedding_service

db_path = os.path.join(ROOT, "data", "databases", "ai_rag_knowledge.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, title, subject, document_data, embedding FROM knowledge_documents")
docs = cur.fetchall()
print(f"共 {len(docs)} 篇文档")

updated = 0
for doc in docs:
    doc_id = doc["id"]
    title = doc["title"]
    subject = doc["subject"]
    has_emb_col = doc["embedding"] is not None

    dd = doc["document_data"]
    if isinstance(dd, str):
        dd = json.loads(dd)
    if dd is None:
        dd = {}
    has_emb_json = "embedding" in dd and dd["embedding"] is not None

    if has_emb_col and has_emb_json:
        continue

    parts = [title, subject]
    content = dd.get("content", {})
    if isinstance(content, dict):
        raw = content.get("raw_text", "")
        if raw:
            parts.append(raw[:3000])
        summary = content.get("summary", "")
        if summary:
            parts.append(summary)
    text_to_embed = " ".join(parts)

    if not text_to_embed.strip():
        continue

    emb = embedding_service.get_embedding(text_to_embed)
    if not emb:
        continue

    emb_blob = json.dumps(emb).encode("utf-8")
    cur.execute("UPDATE knowledge_documents SET embedding = ? WHERE id = ?", (emb_blob, doc_id))
    dd["embedding"] = emb
    cur.execute("UPDATE knowledge_documents SET document_data = ? WHERE id = ?",
                (json.dumps(dd, ensure_ascii=False), doc_id))
    updated += 1
    print(f"  [{doc_id}] {title}: embedding 生成成功 (dim={len(emb)})")

conn.commit()
conn.close()
print(f"\n更新完成: {updated} 篇新增, {len(docs) - updated} 篇已有")
