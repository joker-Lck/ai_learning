import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from data.rag_knowledge_base import rag_kb

docs = rag_kb.get_all_documents(limit=5)
print(f'Total docs sample: {len(docs)}')

for d in docs:
    doc_data = d.get('document_data', {})
    if isinstance(doc_data, str):
        doc_data = json.loads(doc_data)
    emb = doc_data.get('embedding')
    dim = len(emb) if emb else 0
    doc_id = d.get('id')
    title = d.get('title', '')[:30]
    print(f'  ID: {doc_id}, Title: {title}, Embedding dim: {dim}')
