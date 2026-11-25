# -*- coding: utf-8 -*-
"""T2.3 Part B: 把 data/rag_knowledge_base.py (76KB) 拆为包"""
import io
import os
import shutil

ROOT = r"F:\项目\ai教学辅助系统"
SRC = os.path.join(ROOT, "data", "rag_knowledge_base.py")
PKG = os.path.join(ROOT, "data", "rag_knowledge_base")

lines = io.open(SRC, encoding="utf-8").read().splitlines()

def region(a, b):
    """1-indexed inclusive -> text"""
    return "\n".join(lines[a - 1 : b]) + "\n"

caches_body = region(18, 167)      # LRUCache, SemanticCache, 实例, _clear_search_cache
vector_body = region(169, 508)     # Milvus 常量, VectorIndexManager, 两个单例
core_body = region(511, 1843)      # RAGKnowledgeBase, rag_kb

assert "class LRUCache" in caches_body and "class SemanticCache" in caches_body
assert "class VectorIndexManager" in vector_body and "chunk_vector_index" in vector_body
assert "class RAGKnowledgeBase" in core_body and core_body.rstrip().endswith("rag_kb = RAGKnowledgeBase()")

# 修复 core 区域里游离的错误注释
core_body = core_body.replace("    # 创建全局 RAG 知识库实例\n", "")

os.makedirs(PKG, exist_ok=True)

files = {
    "_caches.py": (
        '"""检索缓存：LRU 结果缓存 + 语义近似缓存"""\n\n'
        "import threading\nimport time\nfrom collections import OrderedDict\n\n"
        "import numpy as np\n\nfrom core.logger import info\n\n\n"
        + caches_body
    ),
    "_vector_index.py": (
        '"""Milvus/FAISS 向量索引管理器（文档级 + 教学分块级）"""\n\n'
        "import os\nimport threading\nimport time\n\n"
        "import numpy as np\n\nfrom core.logger import info, warning\n\n\n"
        + vector_body
    ),
    "_core.py": (
        '"""RAG 知识库主体：文档 CRUD、向量/全文/BM25/混合检索、结构分块检索"""\n\n'
        "import json\nfrom datetime import datetime\n\n"
        "import numpy as np\n\n"
        "from core.logger import error, info, warning\n"
        "from data import dbapi as dbapi\n"
        "from data.config import get_rag_db_path\n\n"
        "from ._caches import _clear_search_cache, _semantic_cache\n"
        "from ._vector_index import chunk_vector_index, vector_index\n\n\n"
        + core_body
    ),
    "__init__.py": (
        '"""RAG 知识库包：对外导出 rag_kb / vector_index / chunk_vector_index"""\n\n'
        "from ._caches import LRUCache, SemanticCache, _clear_search_cache\n"
        "from ._core import RAGKnowledgeBase, rag_kb\n"
        "from ._vector_index import VectorIndexManager, chunk_vector_index, vector_index\n\n"
        "__all__ = [\n"
        '    "LRUCache",\n'
        '    "RAGKnowledgeBase",\n'
        '    "SemanticCache",\n'
        '    "VectorIndexManager",\n'
        '    "chunk_vector_index",\n'
        '    "rag_kb",\n'
        '    "vector_index",\n'
        "]\n"
    ),
}

for name, content in files.items():
    p = os.path.join(PKG, name)
    io.open(p, "w", encoding="utf-8", newline="\n").write(content)
    print(f"wrote data/rag_knowledge_base/{name} ({len(content.splitlines())} lines)")

os.remove(SRC)
print("removed data/rag_knowledge_base.py")
