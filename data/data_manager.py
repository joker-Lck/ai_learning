"""
数据管理模块
统一管理数据持久化、缓存和数据库连接
"""
from datetime import datetime
import json
import os
import time
import threading
from .db_operations import db
from .qa_db_operations import qa_db
from .rag_knowledge_base import rag_kb
from core.logger import info, warning, error


class SimpleCache:
    """简单的 TTL 缓存（替代 Streamlit cache）"""

    def __init__(self):
        self._cache: dict = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["ts"] < entry["ttl"]:
                    return entry["val"]
                del self._cache[key]
        return None

    def set(self, key: str, value, ttl: int = 300):
        with self._lock:
            self._cache[key] = {"val": value, "ts": time.time(), "ttl": ttl}

    def clear(self):
        with self._lock:
            self._cache.clear()


# 全局缓存实例
_cache = SimpleCache()


class LearningDataManager:
    """学习数据管理器"""

    @staticmethod
    def save_learning_data(learning_data: dict = None):
        """保存学习数据到本地文件"""
        try:
            if learning_data is None:
                learning_data = {"questions": [], "interactions": []}
            data_to_save = {
                "questions": learning_data.get("questions", []),
                "interactions": learning_data.get("interactions", []),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open("learning_data_backup.json", "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            error(f"保存学习数据失败：{str(e)}")
            return False

    @staticmethod
    def load_learning_data():
        """从本地文件加载学习数据"""
        try:
            if os.path.exists("learning_data_backup.json"):
                with open("learning_data_backup.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    info(f"✅ 从本地备份恢复了学习数据")
                    return data
        except Exception as e:
            warning(f"⚠️ 加载学习数据失败：{str(e)}")
        return None


class DatabaseManager:
    """数据库连接管理器"""

    @staticmethod
    def get_database_connections():
        """获取数据库连接状态"""
        cached = _cache.get("db_connections")
        if cached is not None:
            return cached

        connections = {
            'main': False,
            'qa': False,
            'rag': False
        }

        try:
            connections['main'] = db.connect()
            if connections['main']:
                info("✅ 主数据库连接成功")
        except Exception as e:
            error(f"主数据库连接异常：{str(e)}")

        try:
            connections['qa'] = qa_db.connect()
            if connections['qa']:
                info("✅ 答疑数据库连接成功")
        except Exception as e:
            error(f"答疑数据库连接异常：{str(e)}")

        try:
            connections['rag'] = rag_kb.connect()
            if connections['rag']:
                info("✅ RAG 知识库连接成功")
        except Exception as e:
            error(f"RAG 知识库连接异常：{str(e)}")

        _cache.set("db_connections", connections, ttl=3600)
        return connections

    @staticmethod
    def check_all_connections():
        """检查所有数据库连接状态"""
        status = {
            'main': db.is_connected() if hasattr(db, 'is_connected') else False,
            'qa': qa_db.is_connected() if hasattr(qa_db, 'is_connected') else False,
            'rag': rag_kb.is_connected() if hasattr(rag_kb, 'is_connected') else False
        }
        return status


class CacheManager:
    """缓存管理器"""

    @staticmethod
    def load_env_config():
        """加载环境变量配置（带缓存）"""
        cached = _cache.get("env_config")
        if cached is not None:
            return cached

        from dotenv import load_dotenv
        load_dotenv()
        config = {
            'api_key': os.getenv('KIMI_API_KEY', ''),
            'base_url': os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        }
        _cache.set("env_config", config, ttl=3600)
        return config

    @staticmethod
    def clear_cache(cache_type="all"):
        """清除缓存"""
        _cache.clear()
