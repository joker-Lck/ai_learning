"""
数据访问层
包含数据库配置、数据操作和向量化服务
"""

from .config import get_db_config
from .db_operations import Database, db
from .embedding_service import EmbeddingService, embedding_service
from .qa_db_operations import qa_db
from .rag_knowledge_base import rag_kb, vector_index

__all__ = [
    'Database',
    'EmbeddingService',
    'db',
    'embedding_service',
    'get_db_config',
    'qa_db',
    'rag_kb',
    'vector_index',
]
