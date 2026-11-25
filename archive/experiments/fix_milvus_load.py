# -*- coding: utf-8 -*-
"""修复 VectorIndexManager 跨进程 released 问题：检索/写入前确保 load_collection"""
import io
import os

P = r"F:\项目\ai教学辅助系统\data\rag_knowledge_base\_vector_index.py"
raw = io.open(P, "r", encoding="utf-8", newline="").read()
crlf = "\r\n" in raw
text = raw.replace("\r\n", "\n")

pairs = [
    # 1. helper 方法（插在 _has_data 前）
    ('''    def _has_data(self) -> bool:''',
     '''    def _ensure_loaded(self):
        """确保 collection 已加载（跨进程已存在的 collection 默认 released）"""
        if getattr(self, "_loaded", False):
            return
        try:
            self._client.load_collection(self._collection)
            self._loaded = True
        except Exception as e:
            warning(f"Milvus load_collection 失败: {e}")

    def _has_data(self) -> bool:'''),
    # 2. search 前加载
    ('''        with self._lock:
            if not self._milvus_available or not self._has_data():
                return []
            try:
                vec = self._normalize(query_embedding)''',
     '''        with self._lock:
            if not self._milvus_available or not self._has_data():
                return []
            self._ensure_loaded()
            try:
                vec = self._normalize(query_embedding)'''),
    # 3. add_vectors 前加载
    ('''                self._ensure_collection(dim)
                rows = [''',
     '''                self._ensure_collection(dim)
                self._ensure_loaded()
                rows = ['''),
    # 4. remove_by_ids 前加载
    ('''        with self._lock:
            try:
                ids = [int(i) for i in doc_ids]
                self._client.delete(collection_name=self._collection, filter=f"id in {ids}")''',
     '''        with self._lock:
            self._ensure_loaded()
            try:
                ids = [int(i) for i in doc_ids]
                self._client.delete(collection_name=self._collection, filter=f"id in {ids}")'''),
    # 5. 重建后重置加载标记
    ('''            if self._client.has_collection(self._collection):
                self._client.drop_collection(self._collection)
            self._count_cache = 0
            self._dimension = 0''',
     '''            if self._client.has_collection(self._collection):
                self._client.drop_collection(self._collection)
            self._count_cache = 0
            self._dimension = 0
            self._loaded = False'''),
]

for old, new in pairs:
    assert old in text, f"NOT FOUND: {old[:80]}"
    text = text.replace(old, new, 1)

if crlf:
    text = text.replace("\n", "\r\n")
io.open(P, "w", encoding="utf-8", newline="").write(text)
print("fixed _vector_index.py: lazy load_collection added")
