# -*- coding: utf-8 -*-
"""扫 rag_knowledge_base.py 各区域对模块级名字的引用"""
import re

src = open(r"F:\项目\ai教学辅助系统\data\rag_knowledge_base.py", encoding="utf-8").read()
lines = src.splitlines()
regions = {
    "caches (18-167)": (17, 167),
    "vector_index (169-508)": (168, 508),
    "core (511-1843)": (510, 1843),
}
names = ["_query_cache", "_semantic_cache", "_clear_search_cache", "LRUCache", "SemanticCache",
         "VectorIndexManager", "vector_index", "chunk_vector_index", "dbapi", "get_rag_db_path",
         "np", "json", "os", "threading", "time", "datetime", "OrderedDict", "error", "info", "warning"]
for rname, (a, b) in regions.items():
    body = "\n".join(lines[a:b])
    used = []
    for n in names:
        if re.search(r"\b" + n + r"\b", body):
            used.append(n)
    print(rname, "->", used)
