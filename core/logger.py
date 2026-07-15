"""
日志管理模块 — 企业级结构化日志
支持 JSON 格式输出、请求上下文、日志轮转
"""

import json
import logging
import os
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ── 日志目录 ──
if not os.path.exists('logs'):
    os.makedirs('logs')

# ── 请求上下文（线程安全）──
_context = threading.local()

def set_request_context(request_id: str = None, user_id: int = None):
    """设置当前请求的上下文信息"""
    _context.request_id = request_id
    _context.user_id = user_id

def clear_request_context():
    """清除请求上下文"""
    _context.request_id = None
    _context.user_id = None

def get_request_context() -> dict:
    """获取当前请求上下文"""
    return {
        'request_id': getattr(_context, 'request_id', None),
        'user_id': getattr(_context, 'user_id', None),
    }


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # 注入请求上下文
        ctx = get_request_context()
        if ctx.get('request_id'):
            log_entry['request_id'] = ctx['request_id']
        if ctx.get('user_id'):
            log_entry['user_id'] = ctx['user_id']

        # 异常信息
        if record.exc_info and record.exc_info[1]:
            log_entry['exception'] = {
                'type': type(record.exc_info[1]).__name__,
                'message': str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """人类可读的日志格式化器（控制台输出）"""

    def format(self, record):
        ctx = get_request_context()
        req_id = ctx.get('request_id', '')
        prefix = f"[{req_id}] " if req_id else ""
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {record.name} - {record.levelname} - {prefix}{record.getMessage()}"


# ── 日志器配置 ──
logger = logging.getLogger('AI_Teaching_Assistant')
logger.setLevel(logging.DEBUG)

# 控制台输出（可读格式）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ReadableFormatter())

# 文件输出（JSON 格式 + 轮转）
file_handler = RotatingFileHandler(
    f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=30,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(StructuredFormatter())

logger.addHandler(console_handler)
logger.addHandler(file_handler)


# ── 便捷日志函数 ──
def debug(msg):
    logger.debug(msg)

def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def critical(msg):
    logger.critical(msg)


# ── 业务日志函数 ──
def db_connect_success(db_name):
    info(f"数据库连接成功: {db_name}")

def db_connect_failed(db_name, err_msg):
    error(f"数据库连接失败: {db_name} - {err_msg}")

def db_operation_success(operation, details=""):
    info(f"数据库操作成功: {operation} {details}")

def db_operation_failed(operation, err_msg):
    error(f"数据库操作失败: {operation} - {err_msg}")

def ai_request_start(model):
    info(f"AI请求开始: {model}")

def ai_request_success(model, tokens=None, time_ms=None):
    info(f"AI请求成功: {model}, tokens={tokens}, time={time_ms}ms")

def ai_request_failed(model, err_msg):
    error(f"AI请求失败: {model} - {err_msg}")

def user_login(username, success=True):
    if success:
        info(f"用户登录成功: {username}")
    else:
        warning(f"用户登录失败: {username}")

def user_upload_file(username, filename, file_type):
    info(f"用户上传文件: {username} - {filename} ({file_type})")

def user_download_file(username, filename):
    info(f"用户下载文件: {username} - {filename}")

def rag_search(keywords, results_count):
    info(f"RAG检索: {keywords} - {results_count}条结果")

def rag_add_document(title, subject):
    info(f"添加知识文档: {title} ({subject})")
