"""检索缓存：LRU 结果缓存 + 语义近似缓存"""

import threading
import time
from collections import OrderedDict

import numpy as np

from core.logger import info


class LRUCache:
    """LRU缓存 - 基于OrderedDict实现，自动淘汰最久未使用的条目"""

    def __init__(self, max_size: int = 200, ttl: int = 600):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key: str):
        """获取缓存值，过期或不存在返回None"""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    self._cache.move_to_end(key)
                    return value
                else:
                    del self._cache[key]
            return None

    def set(self, key: str, value):
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time())

    def clear(self, prefix: str | None = None):
        """清空缓存，可选按前缀过滤"""
        with self._lock:
            if prefix:
                keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
            else:
                self._cache.clear()

    def __len__(self):
        return len(self._cache)


class SemanticCache:
    """
    语义缓存 — 基于向量相似度的缓存匹配
    在精确匹配 LRUCache 基础上，增加 embedding 相似度匹配，
    相似问题 (>0.92) 直接复用缓存结果，减少 API 调用。
    """

    def __init__(self, max_size: int = 200, ttl: int = 600, similarity_threshold: float = 0.92):
        self._entries: list[dict] = []  # [{key, value, timestamp, embedding}]
        self._max_size = max_size
        self._ttl = ttl
        self._threshold = similarity_threshold
        self._lock = threading.Lock()

    def get(self, key: str, query_embedding: list[float] | None = None):
        """
        获取缓存值。
        1. 先精确匹配 key
        2. 若失败且有 query_embedding，计算向量相似度匹配
        """
        with self._lock:
            # 精确匹配
            for i, entry in enumerate(self._entries):
                if entry["key"] == key:
                    if time.time() - entry["timestamp"] < self._ttl:
                        # 移到最前（LRU）
                        self._entries.insert(0, self._entries.pop(i))
                        return entry["value"]
                    else:
                        self._entries.pop(i)
                        return None

            # 语义相似度匹配（仅限同一策略命名空间，防止跨策略串结果）
            if query_embedding is not None:
                # 命名空间 = key 的策略前缀（如 rag:bm25 / rag:hybrid）
                ns = ":".join(key.split(":")[:2]) if ":" in key else key
                query_vec = np.array(query_embedding, dtype='float32')
                query_norm = np.linalg.norm(query_vec)
                if query_norm > 0:
                    query_vec = query_vec / query_norm

                    best_sim = 0.0
                    best_idx = -1
                    for i, entry in enumerate(self._entries):
                        if entry.get("embedding") is None:
                            continue
                        # 只在同一命名空间内做语义匹配
                        entry_ns = ":".join(entry["key"].split(":")[:2]) if ":" in entry["key"] else entry["key"]
                        if entry_ns != ns:
                            continue
                        if time.time() - entry["timestamp"] >= self._ttl:
                            continue
                        emb_vec = np.array(entry["embedding"], dtype='float32')
                        emb_norm = np.linalg.norm(emb_vec)
                        if emb_norm > 0:
                            sim = float(np.dot(query_vec, emb_vec / emb_norm))
                            if sim > best_sim:
                                best_sim = sim
                                best_idx = i

                    if best_sim >= self._threshold and best_idx >= 0:
                        entry = self._entries[best_idx]
                        # 移到最前
                        self._entries.insert(0, self._entries.pop(best_idx))
                        info(f"[SemanticCache] 语义命中 sim={best_sim:.3f} key='{key[:30]}'")
                        return entry["value"]

            return None

    def set(self, key: str, value, embedding: list[float] | None = None):
        """设置缓存值，可选存储 embedding 向量"""
        with self._lock:
            # 移除已有的同 key 条目
            self._entries = [e for e in self._entries if e["key"] != key]
            # 淘汰超限
            while len(self._entries) >= self._max_size:
                self._entries.pop()  # 移除最旧的
            # 插入到最前
            self._entries.insert(0, {
                "key": key,
                "value": value,
                "timestamp": time.time(),
                "embedding": embedding,
            })

    def clear(self, prefix: str | None = None):
        """清空缓存，可选按前缀过滤"""
        with self._lock:
            if prefix:
                self._entries = [e for e in self._entries if not e["key"].startswith(prefix)]
            else:
                self._entries.clear()

    def __len__(self):
        return len(self._entries)


_query_cache = LRUCache(max_size=200, ttl=600)
_semantic_cache = SemanticCache(max_size=200, ttl=600, similarity_threshold=0.92)

def _clear_search_cache():
    """清空搜索缓存"""
    _query_cache.clear(prefix='rag:')
    _semantic_cache.clear(prefix='rag:')

