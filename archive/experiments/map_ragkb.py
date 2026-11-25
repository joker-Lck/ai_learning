# -*- coding: utf-8 -*-
"""摸清 rag_knowledge_base.py 内部依赖与外部引用"""
import re
import os

os.chdir(r"F:\项目\ai教学辅助系统")
src = open("data/rag_knowledge_base.py", encoding="utf-8").read()
lines = src.splitlines()
print("total lines:", len(lines))
print("--- head imports (1-30) ---")
for i, l in enumerate(lines[:30], 1):
    print(i, l)
print("--- module-level name counts ---")
for name in ["vector_index", "chunk_vector_index", "_semantic_cache", "_lru_cache", "_clear_search_cache", "MILVUS", "embedding_service", "LRUCache", "SemanticCache", "_cache"]:
    n = len(re.findall(r"\b" + name + r"\b", src))
    print(f"  {name}: {n}")
print("--- external importers of internals ---")
for dp, dn, fn in os.walk("."):
    dn[:] = [d for d in dn if d not in (".git", ".venv", "node_modules", "__pycache__", "experiments", "frontend")]
    for f in fn:
        if f.endswith(".py"):
            p = os.path.join(dp, f)
            if p.endswith(os.path.join("data", "rag_knowledge_base.py")):
                continue
            t = open(p, encoding="utf-8", errors="replace").read()
            if "rag_knowledge_base" in t:
                for m in re.finditer(r"(?:from data\.rag_knowledge_base|from \.rag_knowledge_base) import ([^\n]+)", t):
                    print(" ", p, "->", m.group(1).strip()[:80])
                if re.search(r"import data\.rag_knowledge_base|import rag_knowledge_base", t):
                    print(" ", p, "-> module import")
