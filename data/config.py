"""
数据库配置模块 - MySQL 版本
9 个独立 schema，与原 SQLite 文件一一对应。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# MySQL 连接参数
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

# 历史遗留：SQLite 目录（仅迁移脚本读取源数据用）
SQLITE_DB_DIR = Path(os.getenv("SQLITE_DB_DIR", "data/databases"))

# 库名映射
DB_AUTH = "ai_auth"
DB_PROFILES = "ai_profiles"
DB_RESOURCES = "ai_resources"
DB_PATHS = "ai_paths"
DB_TUTOR = "ai_tutor"
DB_ASSESSMENTS = "ai_assessments"
DB_AGENTS = "ai_agents"
DB_RAG = "ai_rag_knowledge"
DB_MEMORY = "ai_memory"


def mysql_params() -> dict:
    """返回 PyMySQL 连接参数。"""
    return {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": MYSQL_CHARSET,
        "autocommit": False,
    }


# ==================== 库名获取（兼容旧 get_*_db_path） ====================
# 旧代码写的是 sqlite3.connect(get_auth_db_path())，
# 现在返回 MySQL 库名，由 data.dbapi.connect 解析。

def get_auth_db_path() -> str:
    return DB_AUTH


def get_profile_db_path() -> str:
    return DB_PROFILES


def get_resources_db_path() -> str:
    return DB_RESOURCES


def get_paths_db_path() -> str:
    return DB_PATHS


def get_tutor_db_path() -> str:
    return DB_TUTOR


def get_assessments_db_path() -> str:
    return DB_ASSESSMENTS


def get_agents_db_path() -> str:
    return DB_AGENTS


def get_rag_db_path() -> str:
    return DB_RAG


def get_memory_db_path() -> str:
    return DB_MEMORY


# ==================== 向后兼容函数 ====================

def get_auth_db_config():
    return {"database": DB_AUTH, **mysql_params()}


def get_profile_db_config():
    return {"database": DB_PROFILES, **mysql_params()}


def get_resources_db_config():
    return {"database": DB_RESOURCES, **mysql_params()}


def get_paths_db_config():
    return {"database": DB_PATHS, **mysql_params()}


def get_assessments_db_config():
    return {"database": DB_ASSESSMENTS, **mysql_params()}


def get_agents_db_config():
    return {"database": DB_AGENTS, **mysql_params()}


def get_db_config():
    """默认数据库配置（向后兼容，返回 auth）。"""
    return get_auth_db_config()


def get_accounts_db_config():
    """账号库配置（向后兼容，返回 auth）。"""
    return get_auth_db_config()
