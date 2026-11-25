# -*- coding: utf-8 -*-
"""扫 rag_knowledge_base.py 的类/实例边界"""
import re

src = open(r"F:\项目\ai教学辅助系统\data\rag_knowledge_base.py", encoding="utf-8").read()
lines = src.splitlines()
marks = [
    r"^class ", r"^def ", r"^\w+\s*=\s*LRUCache", r"^\w+\s*=\s*SemanticCache",
    r"^vector_index\s*=", r"^chunk_vector_index\s*=", r"^rag_kb\s*=",
    r"^_clear_search_cache", r"^# ",
]
print("total:", len(lines))
for i, l in enumerate(lines, 1):
    for m in marks:
        if re.match(m, l):
            print(f"{i:5d}  {l[:90]}")
            break
