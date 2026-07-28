"""
数据管理模块
统一管理缓存和环境配置
"""
import os
import threading
import time


class SimpleCache:
    """简单的 TTL 缓存"""

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
            'api_key': os.getenv('MIMO_API_KEY', ''),
            'base_url': os.getenv('MIMO_BASE_URL', 'https://api.xiaomimimo.com/v1')
        }
        _cache.set("env_config", config, ttl=3600)
        return config

    @staticmethod
    def clear_cache(cache_type="all"):
        """清除缓存"""
        _cache.clear()
