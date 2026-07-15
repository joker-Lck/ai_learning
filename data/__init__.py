"""
数据访问层
包含数据库配置、数据操作、文档解析和向量化服务
"""

from .config import get_db_config, get_qa_db_config, get_rag_db_config
from .data_manager import LearningDataManager
from .db_operations import Database, db
from .document_parser import DocumentParser
from .embedding_service import EmbeddingService, embedding_service
from .qa_db_operations import QADatabase, qa_db
from .rag_knowledge_base import RAGKnowledgeBase, VectorIndexManager, rag_kb, vector_index

__all__ = [
    # Database Operations
    'Database',
    # Document & Embedding
    'DocumentParser',
    'EmbeddingService',
    # Data Manager
    'LearningDataManager',
    'QADatabase',
    'RAGKnowledgeBase',
    'VectorIndexManager',
    'db',
    'embedding_service',
    # Config
    'get_db_config',
    'get_qa_db_config',
    'get_rag_db_config',
    'qa_db',
    'rag_kb',
    'vector_index'
]
