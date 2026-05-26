"""
数据库配置模块 - 统一管理所有数据库连接配置
使用环境变量管理敏感配置
多数据库架构: 每个核心功能配备独立数据库
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def get_auth_db_config():
    """获取认证数据库配置"""
    return {
        'host': os.getenv('AUTH_DB_HOST', 'localhost'),
        'port': int(os.getenv('AUTH_DB_PORT', '3306')),
        'user': os.getenv('AUTH_DB_USER', 'root'),
        'password': os.getenv('AUTH_DB_PASSWORD', ''),
        'database': os.getenv('AUTH_DB_NAME', 'ai_auth'),
        'charset': 'utf8mb4'
    }


def get_profile_db_config():
    """获取学生画像数据库配置"""
    return {
        'host': os.getenv('PROFILE_DB_HOST', 'localhost'),
        'port': int(os.getenv('PROFILE_DB_PORT', '3306')),
        'user': os.getenv('PROFILE_DB_USER', 'root'),
        'password': os.getenv('PROFILE_DB_PASSWORD', ''),
        'database': os.getenv('PROFILE_DB_NAME', 'ai_profiles'),
        'charset': 'utf8mb4'
    }


def get_resources_db_config():
    """获取学习资源数据库配置"""
    return {
        'host': os.getenv('RESOURCES_DB_HOST', 'localhost'),
        'port': int(os.getenv('RESOURCES_DB_PORT', '3306')),
        'user': os.getenv('RESOURCES_DB_USER', 'root'),
        'password': os.getenv('RESOURCES_DB_PASSWORD', ''),
        'database': os.getenv('RESOURCES_DB_NAME', 'ai_resources'),
        'charset': 'utf8mb4'
    }


def get_paths_db_config():
    """获取学习路径数据库配置"""
    return {
        'host': os.getenv('PATHS_DB_HOST', 'localhost'),
        'port': int(os.getenv('PATHS_DB_PORT', '3306')),
        'user': os.getenv('PATHS_DB_USER', 'root'),
        'password': os.getenv('PATHS_DB_PASSWORD', ''),
        'database': os.getenv('PATHS_DB_NAME', 'ai_paths'),
        'charset': 'utf8mb4'
    }


def get_tutor_db_config():
    """获取智能辅导数据库配置"""
    return {
        'host': os.getenv('TUTOR_DB_HOST', 'localhost'),
        'port': int(os.getenv('TUTOR_DB_PORT', '3306')),
        'user': os.getenv('TUTOR_DB_USER', 'root'),
        'password': os.getenv('TUTOR_DB_PASSWORD', ''),
        'database': os.getenv('TUTOR_DB_NAME', 'ai_tutor'),
        'charset': 'utf8mb4'
    }


def get_assessments_db_config():
    """获取学习评估数据库配置"""
    return {
        'host': os.getenv('ASSESSMENTS_DB_HOST', 'localhost'),
        'port': int(os.getenv('ASSESSMENTS_DB_PORT', '3306')),
        'user': os.getenv('ASSESSMENTS_DB_USER', 'root'),
        'password': os.getenv('ASSESSMENTS_DB_PASSWORD', ''),
        'database': os.getenv('ASSESSMENTS_DB_NAME', 'ai_assessments'),
        'charset': 'utf8mb4'
    }


def get_agents_db_config():
    """获取智能体协作数据库配置"""
    return {
        'host': os.getenv('AGENTS_DB_HOST', 'localhost'),
        'port': int(os.getenv('AGENTS_DB_PORT', '3306')),
        'user': os.getenv('AGENTS_DB_USER', 'root'),
        'password': os.getenv('AGENTS_DB_PASSWORD', ''),
        'database': os.getenv('AGENTS_DB_NAME', 'ai_agents'),
        'charset': 'utf8mb4'
    }


def get_rag_db_config():
    """获取RAG知识库配置"""
    return {
        'host': os.getenv('RAG_DB_HOST', 'localhost'),
        'port': int(os.getenv('RAG_DB_PORT', '3306')),
        'user': os.getenv('RAG_DB_USER', 'root'),
        'password': os.getenv('RAG_DB_PASSWORD', ''),
        'database': os.getenv('RAG_DB_NAME', 'ai_rag_knowledge'),
        'charset': 'utf8mb4'
    }


# ==================== 向后兼容函数 ====================

def get_db_config():
    """获取默认数据库配置（向后兼容，返回auth数据库配置）"""
    return get_auth_db_config()

def get_qa_db_config():
    """获取QA数据库配置（向后兼容，返回tutor数据库配置）"""
    return get_tutor_db_config()

def get_accounts_db_config():
    """获取账号数据库配置（向后兼容，返回auth数据库配置）"""
    return get_auth_db_config()


def get_connection_string(db_type='auth'):
    """获取数据库连接字符串"""
    config_funcs = {
        'auth': get_auth_db_config,
        'profile': get_profile_db_config,
        'resources': get_resources_db_config,
        'paths': get_paths_db_config,
        'tutor': get_tutor_db_config,
        'assessments': get_assessments_db_config,
        'agents': get_agents_db_config,
        'rag': get_rag_db_config,
    }
    
    config_func = config_funcs.get(db_type, get_auth_db_config)
    config = config_func()
    
    return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset=utf8mb4"
