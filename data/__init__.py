"""
数据访问层
包含数据库配置、数据操作、文档解析和向量化服务
"""

from .config import get_db_config, get_qa_db_config, get_rag_db_config
from .db_operations import Database, db
from .qa_db_operations import QADatabase, qa_db
from .rag_knowledge_base import RAGKnowledgeBase, rag_kb, VectorIndexManager, vector_index
from .document_parser import DocumentParser
from .embedding_service import EmbeddingService, embedding_service
from .data_manager import LearningDataManager

__all__ = [
    # Config
    'get_db_config', 'get_qa_db_config', 'get_rag_db_config',
    
    # Database Operations
    'Database', 'db',
    'QADatabase', 'qa_db',
    'RAGKnowledgeBase', 'rag_kb', 'VectorIndexManager', 'vector_index',
    
    # Document & Embedding
    'DocumentParser',
    'EmbeddingService', 'embedding_service',
    
    # Data Manager
    'LearningDataManager'
]
