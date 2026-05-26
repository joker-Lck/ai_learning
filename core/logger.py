"""
日志管理模块
"""

import logging
import os
from datetime import datetime

# 初始化日志目录
if not os.path.exists('logs'):
    os.makedirs('logs')

log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AI_Teaching_Assistant')
# 基础日志函数
def debug(msg):
    """调试信息"""
    logger.debug(msg)

def info(msg):
    """一般信息"""
    logger.info(msg)

def warning(msg):
    """警告信息"""
    logger.warning(msg)

def error(msg):
    """错误信息"""
    logger.error(msg)

def critical(msg):
    """严重错误"""
    logger.critical(msg)
# 数据库日志
def db_connect_success(db_name):
    """数据库连接成功"""
    info(f"✅ 数据库连接成功：{db_name}")

def db_connect_failed(db_name, err_msg):
    """数据库连接失败"""
    error(f"❌ 数据库连接失败：{db_name} - {err_msg}")

def db_operation_success(operation, details=""):
    """数据库操作成功"""
    info(f"✅ 数据库操作成功：{operation} {details}")

def db_operation_failed(operation, err_msg):
    """数据库操作失败"""
    error(f"❌ 数据库操作失败：{operation} - {err_msg}")
# AI 调用日志
def ai_request_start(model):
    """AI 请求开始"""
    info(f"🤖 开始调用 AI 模型：{model}")

def ai_request_success(model, tokens=None, time_ms=None):
    """AI 请求成功"""
    info(f"✅ AI 调用成功：{model}, Tokens: {tokens}, 耗时：{time_ms}ms")

def ai_request_failed(model, err_msg):
    """AI 请求失败"""
    error(f"❌ AI 调用失败：{model} - {err_msg}")
# 用户操作日志
def user_login(username, success=True):
    """用户登录"""
    if success:
        info(f"👤 用户登录成功：{username}")
    else:
        warning(f"⚠️ 用户登录失败：{username}")

def user_upload_file(username, filename, file_type):
    """用户上传文件"""
    info(f"📤 用户上传文件：{username} - {filename} ({file_type})")

def user_download_file(username, filename):
    """用户下载文件"""
    info(f"📥 用户下载文件：{username} - {filename}")

def user_generate_courseware(username, topic, subject):
    """用户生成课件"""
    info(f"🎓 用户生成课件：{username} - {topic} ({subject})")
# RAG 日志
def rag_search(keywords, results_count):
    """RAG 检索"""
    info(f"🔍 RAG 检索：{keywords} - 找到 {results_count} 条结果")

def rag_add_document(title, subject):
    """添加知识文档"""
    info(f"📚 添加知识文档：{title} ({subject})")
