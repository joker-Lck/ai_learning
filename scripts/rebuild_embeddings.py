import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
from data.rag_knowledge_base import rag_kb
from data.embedding_service import embedding_service
from data.rag_knowledge_base import vector_index

def rebuild_all():
    docs = rag_kb.get_all_documents(limit=1000)
    print(f'Found {len(docs)} documents')

    doc_ids = []
    embeddings = []
    success = 0
    failed = 0

    for d in docs:
        doc_id = d.get('id')
        title = d.get('title', '')
        doc_data = d.get('document_data', {})
        if isinstance(doc_data, str):
            doc_data = json.loads(doc_data)

        # 跳过已有embedding的
        existing_emb = doc_data.get('embedding')
        if existing_emb and len(existing_emb) > 0:
            doc_ids.append(doc_id)
            embeddings.append(existing_emb)
            success += 1
            continue

        content = doc_data.get('content', {})
        if isinstance(content, dict):
            text = content.get('raw_text', '')[:4000]
        else:
            text = str(content)[:4000]

        if not text or len(text) < 10:
            failed += 1
            continue

        # 重试3次
        emb = None
        for attempt in range(3):
            emb = embedding_service.get_embedding(text)
            if emb:
                break
            time.sleep(1)

        if emb:
            doc_data['embedding'] = emb
            try:
                rag_kb.connect()
                update_sql = "UPDATE knowledge_documents SET document_data = %s WHERE id = %s"
                rag_kb.cursor.execute(update_sql, (json.dumps(doc_data, ensure_ascii=False), doc_id))
                rag_kb.conn.commit()
                rag_kb.close()
                doc_ids.append(doc_id)
                embeddings.append(emb)
                success += 1
                print(f'  OK: {doc_id} - {title[:30]}')
            except Exception as e:
                print(f'  DB Error: {doc_id} - {e}')
                failed += 1
        else:
            print(f'  FAIL: {doc_id} - {title[:30]}')
            failed += 1

    if embeddings:
        print(f'\nRebuilding FAISS index with {len(embeddings)} vectors...')
        vector_index.rebuild(doc_ids, embeddings)
        vector_index.save()
        print(f'FAISS index: {vector_index.total_vectors} vectors')

    print(f'\nResult: {success} success, {failed} failed')

if __name__ == '__main__':
    rebuild_all()
