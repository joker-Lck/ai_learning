"""
核心支持模块
包含日志、工具函数、UI组件和提示词模板等基础功能
"""

from .logger import (
    ai_request_failed,
    ai_request_start,
    ai_request_success,
    critical,
    db_connect_failed,
    db_connect_success,
    db_operation_failed,
    db_operation_success,
    debug,
    error,
    info,
    logger,
    rag_add_document,
    rag_search,
    user_download_file,
    user_login,
    user_upload_file,
    warning,
)
from .prompts import AnalysisPrompts, DocumentAnalysisPrompts, VoiceQAPrompts
from .ui_components import CustomCSS, PageLayout, UIComponents
from .utils import (
    clean_json_string,
    extract_urls,
    format_file_size,
    generate_filename,
    safe_get,
    truncate_text,
    validate_email,
)

__all__ = [
    # Logger
    'logger', 'debug', 'info', 'warning', 'error', 'critical',
    'db_connect_success', 'db_connect_failed',
    'db_operation_success', 'db_operation_failed',
    'ai_request_start', 'ai_request_success', 'ai_request_failed',
    'user_login', 'user_upload_file', 'user_download_file',
    'rag_search', 'rag_add_document',

    # Utils
    'clean_json_string', 'format_file_size', 'extract_urls',
    'truncate_text', 'safe_get', 'validate_email', 'generate_filename',

    # UI Components
    'CustomCSS', 'PageLayout', 'UIComponents',

    # Prompts
    'AnalysisPrompts', 'DocumentAnalysisPrompts', 'VoiceQAPrompts'
]
