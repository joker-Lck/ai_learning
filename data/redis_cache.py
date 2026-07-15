"""
Redis 缓存模块
提供热点数据缓存，降低数据库压力
"""

import hashlib
import json
from typing import Any

from core.logger import info, warning

_redis_client = None
_redis_available = False


def _get_redis():
    global _redis_client, _redis_available
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        from .config import get_redis_config
        config = get_redis_config()
        _redis_client = redis.Redis(**config)
        _redis_client.ping()
        _redis_available = True
        info("Redis 连接成功")
        return _redis_client
    except Exception as e:
        _redis_available = False
        warning(f"Redis 不可用，将跳过缓存: {e}")
        return None


def _make_key(prefix: str, *args) -> str:
    raw = f"{prefix}:{':'.join(str(a) for a in args)}"
    if len(raw) > 200:
        return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"
    return raw


def cache_get(prefix: str, *args) -> Any | None:
    r = _get_redis()
    if r is None:
        return None
    key = _make_key(prefix, *args)
    try:
        data = r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def cache_set(prefix: str, value: Any, ttl: int = 600, *args):
    r = _get_redis()
    if r is None:
        return
    key = _make_key(prefix, *args)
    try:
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass


def cache_delete(prefix: str, *args):
    r = _get_redis()
    if r is None:
        return
    key = _make_key(prefix, *args)
    try:
        r.delete(key)
    except Exception:
        pass


def cache_clear_prefix(prefix: str):
    r = _get_redis()
    if r is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor, match=f"{prefix}:*", count=100)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass
