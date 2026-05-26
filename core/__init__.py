"""
核心支持模块
包含日志、工具函数、UI组件和提示词模板等基础功能
"""

from .logger import logger, debug, info, warning, error, critical
from .logger import (
    db_connect_success, db_connect_failed,
    db_operation_success, db_operation_failed,
    ai_request_start, ai_request_success, ai_request_failed,
    user_login, user_upload_file, user_download_file,
    user_generate_courseware, rag_search, rag_add_document
)
from .utils import (
    clean_json_string, format_file_size, extract_urls,
    truncate_text, safe_get, validate_email, generate_filename
)
from .ui_components import CustomCSS, PageLayout, UIComponents
from .prompts import (
    CoursewarePrompts, AnalysisPrompts, 
    DocumentAnalysisPrompts, ClarificationPrompts, VoiceQAPrompts
)

__all__ = [
    # Logger
    'logger', 'debug', 'info', 'warning', 'error', 'critical',
    'db_connect_success', 'db_connect_failed',
    'db_operation_success', 'db_operation_failed',
    'ai_request_start', 'ai_request_success', 'ai_request_failed',
    'user_login', 'user_upload_file', 'user_download_file',
    'user_generate_courseware', 'rag_search', 'rag_add_document',
    
    # Utils
    'clean_json_string', 'format_file_size', 'extract_urls',
    'truncate_text', 'safe_get', 'validate_email', 'generate_filename',
    
    # UI Components
    'CustomCSS', 'PageLayout', 'UIComponents',
    
    # Prompts
    'CoursewarePrompts', 'AnalysisPrompts',
    'DocumentAnalysisPrompts', 'ClarificationPrompts', 'VoiceQAPrompts'
]
