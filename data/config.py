"""
数据库配置模块 - SQLite 版本
9个独立 .db 文件，与原 MySQL 架构一一对应
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 数据库文件存放目录
DB_DIR = Path(os.getenv("SQLITE_DB_DIR", "data/databases"))


def _db_path(name: str) -> str:
    """返回 .db 文件的绝对路径"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return str(DB_DIR / f"{name}.db")


def get_auth_db_path() -> str:
    return _db_path("ai_auth")


def get_profile_db_path() -> str:
    return _db_path("ai_profiles")


def get_resources_db_path() -> str:
    return _db_path("ai_resources")


def get_paths_db_path() -> str:
    return _db_path("ai_paths")


def get_tutor_db_path() -> str:
    return _db_path("ai_tutor")


def get_assessments_db_path() -> str:
    return _db_path("ai_assessments")


def get_agents_db_path() -> str:
    return _db_path("ai_agents")


def get_rag_db_path() -> str:
    return _db_path("ai_rag_knowledge")


def get_memory_db_path() -> str:
    return _db_path("ai_memory")


# ==================== 向后兼容函数 ====================

def get_auth_db_config():
    """获取认证数据库配置"""
    return {"database": get_auth_db_path()}


def get_profile_db_config():
    """获取学生画像数据库配置"""
    return {"database": get_profile_db_path()}


def get_resources_db_config():
    """获取学习资源数据库配置"""
    return {"database": get_resources_db_path()}


def get_paths_db_config():
    """获取学习路径数据库配置"""
    return {"database": get_paths_db_path()}


def get_tutor_db_config():
    """获取智能辅导数据库配置"""
    return {"database": get_tutor_db_path()}


def get_assessments_db_config():
    """获取学习评估数据库配置"""
    return {"database": get_assessments_db_path()}


def get_agents_db_config():
    """获取智能体协作数据库配置"""
    return {"database": get_agents_db_path()}


def get_rag_db_config():
    """获取RAG知识库配置"""
    return {"database": get_rag_db_path()}


def get_memory_db_config():
    """获取记忆系统配置"""
    return {"database": get_memory_db_path()}


def get_db_config():
    """获取默认数据库配置（向后兼容，返回auth数据库配置）"""
    return get_auth_db_config()


def get_qa_db_config():
    """获取QA数据库配置（向后兼容，返回tutor数据库配置）"""
    return get_tutor_db_config()


def get_accounts_db_config():
    """获取账号数据库配置（向后兼容，返回auth数据库配置）"""
    return get_auth_db_config()


def get_redis_config():
    """获取Redis配置"""
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD", None),
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True,
    }
