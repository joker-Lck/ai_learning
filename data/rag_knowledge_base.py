from core.logger import error, info, warning

"""RAG 知识库管理模块（JSON 格式存储）"""

import json
import os
from data import dbapi as dbapi
import threading
import time
from collections import OrderedDict
from datetime import datetime

import numpy as np

from .config import get_rag_db_path


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
_CACHE_TTL = 600

def _clear_search_cache():
    """清空搜索缓存"""
    _query_cache.clear(prefix='rag:')
    _semantic_cache.clear(prefix='rag:')


# ═══════════════════════════════════════════
# Milvus 向量索引管理器
# ═══════════════════════════════════════════

# Milvus Lite 不支持中文路径，存放在用户目录
_INDEX_DIR = os.path.join(os.path.expanduser("~"), ".milvus")
_MILVUS_URI = os.path.join(_INDEX_DIR, "ai_learning.db")
_COLLECTION = "knowledge_vectors"


class VectorIndexManager:
    """
    基于 Milvus 的向量索引管理器
    - Milvus Lite 本地文件存储（可平滑切换到 Milvus Server / Zilliz Cloud）
    - 支持原生向量删除（优于 FAISS 的重建方案）
    - COSINE 余弦相似度
    - 文档变更时惰性重建
    - 支持定期全量重建以修正漂移
    """

    def __init__(self):
        self._client = None
        self._dimension = 0
        self._lock = threading.Lock()
        self._dirty = False
        self._last_rebuild = 0
        self._rebuild_interval = 3600
        self._milvus_available = False
        self._count_cache = 0
        self._index_kind = "AUTOINDEX"
        try:
            from pymilvus import MilvusClient  # noqa: F401

            self._milvus_available = True
            self._connect()
        except ImportError:
            pass
        except Exception as e:
            warning(f"Milvus 连接失败：{e}")
            self._milvus_available = False

    # ── 兼容旧属性名 ──────────────────────────
    @property
    def _faiss_available(self) -> bool:
        return self._milvus_available

    @_faiss_available.setter
    def _faiss_available(self, value: bool):
        self._milvus_available = value

    @property
    def is_available(self) -> bool:
        return self._milvus_available

    # ── 公开接口 ──────────────────────────────

    def search(self, query_embedding: list, limit: int = 5) -> list:
        """
        检索最相似的文档

        返回: [{'id': doc_id, 'score': float}, ...]
        """
        with self._lock:
            if not self._milvus_available or not self._has_data():
                return []
            try:
                vec = self._normalize(query_embedding)
                # 维度守卫：与 collection 维度不一致时直接返回，避免检索崩溃
                if self._dimension and len(vec) != self._dimension:
                    warning(f"查询向量维度 {len(vec)} != 索引维度 {self._dimension}，跳过 Milvus 检索")
                    return []
                hits = self._client.search(
                    collection_name=_COLLECTION,
                    data=[vec],
                    limit=limit,
                    output_fields=["id"],
                    search_params=getattr(self, "_search_params", None),
                )
                results = []
                for hit in hits[0] if hits else []:
                    results.append({
                        "id": hit.get("id") if "id" in hit else hit.get("entity", {}).get("id"),
                        "score": float(hit.get("distance", 0.0)),
                    })
                return results
            except Exception as e:
                warning(f"Milvus 检索失败: {e}")
                return []

    def add_vectors(self, doc_ids: list, embeddings: list):
        """增量添加向量"""
        if not doc_ids or not embeddings or not self._milvus_available:
            return
        with self._lock:
            dim = len(embeddings[0])
            if dim <= 0:
                return
            if self._dimension == 0:
                self._dimension = dim
            elif dim != self._dimension:
                # 维度不一致时全量重建
                warning(f"向量维度变化 {self._dimension} → {dim}，跳过增量添加")
                return

            try:
                self._ensure_collection(dim)
                rows = [
                    {"id": int(did), "vector": self._normalize(emb)}
                    for did, emb in zip(doc_ids, embeddings, strict=False)
                ]
                self._client.insert(collection_name=_COLLECTION, data=rows)
                self._count_cache += len(rows)
                self._dirty = True
            except Exception as e:
                warning(f"Milvus 增量添加失败: {e}")

    def remove_by_ids(self, doc_ids: set):
        """按 ID 移除向量（Milvus 原生删除）"""
        if not doc_ids or not self._milvus_available:
            return
        with self._lock:
            try:
                ids = [int(i) for i in doc_ids]
                self._client.delete(collection_name=_COLLECTION, filter=f"id in {ids}")
                self._count_cache = max(0, self._count_cache - len(ids))
                self._dirty = True
            except Exception as e:
                warning(f"Milvus 删除失败: {e}")

    def rebuild(self, doc_ids: list, embeddings: list):
        """全量重建索引"""
        with self._lock:
            self._rebuild_internal(doc_ids, embeddings)

    def save(self):
        """持久化（Milvus Lite 自动落盘，此处仅 flush）"""
        with self._lock:
            if not self._milvus_available or not self._dirty:
                return
            try:
                self._client.flush(_COLLECTION)
                self._dirty = False
            except Exception as e:
                warning(f"Milvus flush 失败: {e}")

    def load(self) -> bool:
        """加载索引（Milvus Lite 自动加载，校验连通性）"""
        with self._lock:
            if not self._milvus_available:
                return False
            try:
                self._connect()
                return self._has_data() or self._client.has_collection(_COLLECTION)
            except Exception:
                return False

    @property
    def is_ready(self) -> bool:
        return self._milvus_available and self._has_data()

    @property
    def total_vectors(self) -> int:
        if not self._milvus_available:
            return 0
        try:
            with self._lock:
                if not self._client.has_collection(_COLLECTION):
                    return 0
                res = self._client.query(
                    collection_name=_COLLECTION,
                    filter="",
                    output_fields=["count(*)"],
                )
                if res:
                    self._count_cache = int(list(res[0].values())[0])
                return self._count_cache
        except Exception:
            return self._count_cache

    @property
    def index_type(self) -> str:
        """返回当前索引类型名称"""
        if not self._milvus_available or not self._has_data():
            return "none"
        return self._index_kind

    @property
    def index_info(self) -> dict:
        """返回索引详细信息"""
        return {
            "type": self.index_type,
            "engine": "Milvus",
            "total_vectors": self.total_vectors,
            "dimension": self._dimension,
            "is_ready": self.is_ready,
        }

    def maybe_rebuild(self, rebuild_fn):
        if time.time() - self._last_rebuild > self._rebuild_interval:
            try:
                rebuild_fn()
                self._last_rebuild = time.time()
            except Exception as e:
                warning(f"定期重建向量索引失败: {e}")

    # ── 内部方法 ──────────────────────────────

    def _connect(self):
        """连接 Milvus（Lite 本地文件 / Server URI）"""
        from pymilvus import MilvusClient

        uri = os.getenv("MILVUS_URI", _MILVUS_URI)
        token = os.getenv("MILVUS_TOKEN") or None
        os.makedirs(os.path.dirname(uri) or ".", exist_ok=True)
        self._client = MilvusClient(uri=uri, token=token) if token else MilvusClient(uri=uri)

    def _has_data(self) -> bool:
        try:
            return self._client is not None and self._client.has_collection(_COLLECTION)
        except Exception:
            return False

    def _ensure_collection(self, dim: int):
        """确保 collection 存在且维度匹配"""
        if self._client is None:
            self._connect()
        if self._client.has_collection(_COLLECTION):
            desc = self._client.describe_collection(_COLLECTION)
            existing_dim = 0
            for f in desc.get("fields", []):
                if f.get("name") == "vector":
                    existing_dim = int((f.get("params") or {}).get("dim", 0))
            if existing_dim and existing_dim != dim:
                info(f"[Milvus] 维度变更 {existing_dim} → {dim}，重建 collection")
                self._client.drop_collection(_COLLECTION)
            else:
                self._dimension = existing_dim or dim
                return

        self._client.create_collection(
            collection_name=_COLLECTION,
            dimension=dim,
            metric_type="COSINE",
            auto_id=False,
        )
        self._dimension = dim
        self._count_cache = 0
        self._pick_index_kind(dim)
        self._create_index()
        info(f"[Milvus] collection 创建完成: dim={dim}, metric=COSINE, index={self._index_kind}")

    def _pick_index_kind(self, dim: int):
        """按规模选择索引类型"""
        n = self._count_cache
        if n >= 100_000:
            self._index_kind = "HNSW"
        elif n >= 10_000:
            self._index_kind = "IVF_FLAT"
        else:
            self._index_kind = "FLAT"

    def _create_index(self):
        """为向量字段建索引（HNSW/IVF_FLAT/FLAT 参数按规模调优）"""
        if self._client is None:
            return
        try:
            from pymilvus.milvus_client.index import IndexParams

            if self._index_kind == "HNSW":
                index_params = IndexParams(
                    index_type="HNSW",
                    metric_type="COSINE",
                    params={"M": 32, "efConstruction": 200},
                )
                search_params = {"metric_type": "COSINE", "params": {"ef": 128}}
            elif self._index_kind == "IVF_FLAT":
                nlist = max(16, min(int((self._count_cache or 1024) ** 0.5), 4096))
                index_params = IndexParams(
                    index_type="IVF_FLAT",
                    metric_type="COSINE",
                    params={"nlist": nlist},
                )
                search_params = {"metric_type": "COSINE", "params": {"nprobe": min(max(1, nlist // 10), 64)}}
            else:
                index_params = IndexParams(index_type="FLAT", metric_type="COSINE", params={})
                search_params = {"metric_type": "COSINE", "params": {}}

            self._client.create_index(
                collection_name=_COLLECTION,
                index_params=index_params,
            )
            self._search_params = search_params
            debug(f"[Milvus] 索引创建: {self._index_kind}")
        except Exception as e:
            warning(f"[Milvus] 索引创建失败（AUTOINDEX 兜底）: {e}")
            self._search_params = {"metric_type": "COSINE", "params": {}}

    @staticmethod
    def _normalize(embedding) -> list:
        """L2 归一化，配合 COSINE/内积"""
        vec = np.asarray(embedding, dtype="float32").reshape(-1)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _rebuild_internal(self, doc_ids: list, embeddings: list):
        """内部重建（需已持有锁）"""
        if not self._milvus_available:
            return
        try:
            if self._client.has_collection(_COLLECTION):
                self._client.drop_collection(_COLLECTION)
            self._count_cache = 0
            self._dimension = 0

            if not embeddings:
                self._dirty = True
                return

            dim = len(embeddings[0])
            self._ensure_collection(dim)
            rows = [
                {"id": int(did), "vector": self._normalize(emb)}
                for did, emb in zip(doc_ids, embeddings, strict=False)
            ]
            self._client.insert(collection_name=_COLLECTION, data=rows)
            self._client.flush(_COLLECTION)
            self._count_cache = len(rows)
            self._pick_index_kind(dim)
            self._dirty = False
        except Exception as e:
            warning(f"Milvus 重建失败: {e}")


# 全局单例
vector_index = VectorIndexManager()


class RAGKnowledgeBase:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db_path = get_rag_db_path()
        self._init_fts()

    def _init_fts(self):
        """初始化 MySQL FULLTEXT 索引（迁移期兼容入口，DDL 已在建表脚本中完成）"""
        try:
            conn = dbapi.connect(self.db_path)
            conn.execute("SELECT 1 FROM knowledge_documents LIMIT 1")
            conn.close()
        except Exception as e:
            warning(f"FULLTEXT 初始化检查失败：{e!s}")

    def _get_connection(self):
        """获取 MySQL 连接"""
        conn = dbapi.connect(self.db_path, timeout=10)
        conn.row_factory = dbapi.Row
        return conn

    def connect(self):
        """连接数据库（已连且可用时复用，避免重复握手）"""
        try:
            # 复用健康连接
            if self.conn is not None and self.cursor is not None:
                try:
                    self.cursor.execute("SELECT 1")
                    return True
                except Exception:
                    try:
                        self.close()
                    except Exception:
                        pass
            self.conn = self._get_connection()
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            self.conn = None
            self.cursor = None
            raise ConnectionError(f"RAG 知识库连接失败：{e!s}")

    def _ensure_connected(self):
        """确保数据库已连接，返回 True/False"""
        if self.cursor is not None and self.conn is not None:
            return True
        return self.connect()

    def close(self):
        """关闭连接"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            warning(f"关闭连接失败：{e!s}")

    # ========== 知识文档相关操作 ==========

    def add_document(self, title, subject, file_path, file_type, content_text,
                     knowledge_points=None, ai_summary=None, uploaded_by=None,
                     file_size=0, embedding=None):
        """
        添加知识文档到库中（JSON 格式存储）

        参数：
        - title: 文档标题
        - subject: 所属学科（语文、数学、英语等）
        - file_path: 文件存储路径
        - file_type: 文件类型（pdf/doc/ppt/txt）
        - content_text: 提取的文本内容
        - knowledge_points: 知识点列表（可以是列表或 JSON 字符串）
        - ai_summary: AI 生成的摘要
        - uploaded_by: 上传者
        - file_size: 文件大小（字节）
        - embedding: 文档向量（可选）
        """
        try:
            self.connect()

            # 构建完整的 JSON 数据结构
            document_data = {
                "metadata": {
                    "title": title,
                    "subject": subject,
                    "file_type": file_type,
                    "file_path": file_path,
                    "uploaded_by": uploaded_by,
                    "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version": "1.0"
                },
                "content": {
                    "raw_text": content_text[:500000] if content_text else "",  # 电子书支持50万字符
                    "text_length": len(content_text) if content_text else 0,
                    "paragraphs": self._split_paragraphs(content_text, max_length=800, max_count=2000) if content_text else []
                },
                "analysis": {
                    "knowledge_points": knowledge_points if isinstance(knowledge_points, list) else [],
                    "summary": ai_summary or "",
                    "difficulty_level": "中等",
                    "tags": []
                }
            }

            # 如果有向量，添加到 JSON 数据中
            if embedding:
                document_data["embedding"] = embedding

            # 检查 embedding 列是否存在
            has_embedding_col = False
            try:
                self.cursor.execute("SHOW COLUMNS FROM knowledge_documents LIKE 'embedding'")
                has_embedding_col = self.cursor.fetchone() is not None
            except Exception:
                pass

            if has_embedding_col:
                sql = """INSERT INTO knowledge_documents
                        (title, subject, file_path, file_type, file_size, document_data, embedding, uploaded_by, upload_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                params = (
                    title, subject, file_path, file_type, file_size,
                    json.dumps(document_data, ensure_ascii=False),
                    json.dumps(embedding, ensure_ascii=False) if embedding else None,
                    uploaded_by, datetime.now()
                )
            else:
                sql = """INSERT INTO knowledge_documents
                        (title, subject, file_path, file_type, file_size, document_data, uploaded_by, upload_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
                params = (
                    title, subject, file_path, file_type, file_size,
                    json.dumps(document_data, ensure_ascii=False),
                    uploaded_by, datetime.now()
                )
            self.cursor.execute(sql, params)
            self.conn.commit()
            doc_id = self.cursor.lastrowid

            # 如果有关键词，添加到关键词表
            if knowledge_points:
                self._add_knowledge_points(doc_id, knowledge_points)

            # 添加文档后清空搜索缓存
            _clear_search_cache()

            # 增量更新向量索引 + BM25 索引
            if embedding and vector_index.is_available:
                try:
                    vector_index.add_vectors([doc_id], [embedding])
                    vector_index.save()
                except Exception:
                    pass  # 索引更新失败不影响文档写入
            try:
                from data.bm25_softmax import bm25_retriever

                bm25_text = " ".join(
                    filter(None, [title or "", subject or "",
                                  (document_data or {}).get("analysis", {}).get("summary", "") if isinstance(document_data, dict) else "",
                                  content_text or ""])
                )
                bm25_retriever.index.upsert(int(doc_id), bm25_text[:5000])
            except Exception:
                pass

            return doc_id
        except Exception as e:
            error(f"添加文档失败：{e!s}")
            return None
        finally:
            self.close()

    def _add_knowledge_points(self, doc_id, knowledge_points_str):
        """添加知识点到关联表"""
        try:
            # 解析知识点（支持列表或字符串）
            if isinstance(knowledge_points_str, list):
                points = knowledge_points_str
            else:
                points = [p.strip() for p in str(knowledge_points_str).split(',') if p.strip()]

            for point in points:
                sql = "INSERT OR IGNORE INTO knowledge_points (doc_id, point_name) VALUES (?, ?)"
                self.cursor.execute(sql, (doc_id, point))

            self.conn.commit()
        except Exception as e:
            error(f"添加知识点失败：{e!s}")

    def _split_paragraphs(self, text, max_length=500, max_count=100):
        """将文本分割为段落"""
        if not text:
            return []

        # 按换行符分割
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        # 如果段落太长，进一步分割
        result = []
        for para in paragraphs:
            if len(para) <= max_length:
                result.append(para)
            else:
                # 按句号、分号等分割
                for sep in ['。', '；', '!', '？', '.', ';', '!', '?']:
                    if sep in para:
                        sentences = para.split(sep)
                        current = ""
                        for sentence in sentences:
                            if len(current + sentence) <= max_length:
                                current += sentence + sep
                            else:
                                if current:
                                    result.append(current.strip())
                                current = sentence + sep
                        if current:
                            result.append(current.strip())
                        break
                else:
                    # 没有句号，按字符数强制分割
                    for i in range(0, len(para), max_length):
                        result.append(para[i:i + max_length])

        return result[:max_count]

    def get_documents_by_subject(self, subject, limit=50):
        """获取指定学科的所有文档（解析 JSON 数据）"""
        try:
            self.connect()
            sql = """SELECT * FROM knowledge_documents
                    WHERE subject = ?
                    ORDER BY upload_time DESC
                    LIMIT ?"""
            self.cursor.execute(sql, (subject, limit))
            results = self.cursor.fetchall()

            # 解析 JSON 字段
            for i, record in enumerate(results):
                record = dict(record)
                results[i] = record
                if record.get('document_data'):
                    record['document_data'] = json.loads(record['document_data'])
                    # 兼容旧代码：提取常用字段
                    doc_data = record['document_data']
                    record['content_text'] = doc_data.get('content', {}).get('raw_text', '')
                    record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', [])
                    record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '')

            return results
        except Exception as e:
            error(f"获取学科文档失败：{e!s}")
            return []
        finally:
            self.close()

    def get_all_documents(self, limit=100, offset=0):
        """获取所有文档（按上传时间倒序，最新在前）"""
        try:
            self.connect()
            sql = """SELECT * FROM knowledge_documents
                    ORDER BY upload_time DESC
                    LIMIT ? OFFSET ?"""
            self.cursor.execute(sql, (limit, offset))
            results = self.cursor.fetchall()

            # 解析 JSON 字段
            for i, record in enumerate(results):
                record = dict(record)
                results[i] = record
                if record.get('document_data'):
                    record['document_data'] = json.loads(record['document_data'])
                    # 兼容旧代码
                    doc_data = record['document_data']

                    # ✅ 兼容两种格式：
                    # 1. 旧格式：doc_data['content']['raw_text']（嵌套对象）
                    # 2. 新格式：doc_data['content']（直接文本字符串，如 CSV 导入）
                    content = doc_data.get('content', '')
                    if isinstance(content, dict):
                        # 旧格式：嵌套对象
                        record['content_text'] = content.get('raw_text', '')
                    else:
                        # 新格式：直接文本字符串
                        record['content_text'] = content

                    record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', [])
                    record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '')

            return results
        except Exception as e:
            error(f"获取所有文档失败：{e!s}")
            return []
        finally:
            self.close()

    def get_documents_by_user(self, user_id, limit=100, offset=0):
        """获取指定用户上传的文档"""
        try:
            self.connect()
            sql = """SELECT * FROM knowledge_documents
                    WHERE uploaded_by = ?
                    ORDER BY upload_time DESC
                    LIMIT ? OFFSET ?"""
            self.cursor.execute(sql, (int(user_id), limit, offset))
            results = self.cursor.fetchall()

            for i, record in enumerate(results):
                record = dict(record)
                results[i] = record
                if record.get('document_data'):
                    record['document_data'] = json.loads(record['document_data'])
                    doc_data = record['document_data']
                    content = doc_data.get('content', '')
                    if isinstance(content, dict):
                        record['content_text'] = content.get('raw_text', '')
                    else:
                        record['content_text'] = content
                    record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', [])
                    record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '')

            return results
        except Exception as e:
            error(f"获取用户文档失败：{e!s}")
            return []
        finally:
            self.close()

    def search_documents_by_vector(self, query_embedding, limit=5, cache_ns="vector"):
        """
        基于向量相似度检索文档（优先 Milvus，回退暴力搜索）

        参数：
        - query_embedding: 查询文本的向量
        - limit: 返回数量限制
        - cache_ns: 语义缓存命名空间（hyde/ann 等调用方各自隔离）

        返回：
        - list: 按相似度排序的文档列表
        """
        # 语义缓存命中检查（key 需含查询指纹，避免不同查询命中同一缓存）
        qhash = abs(hash(tuple(round(x, 4) for x in (query_embedding or [])[:8])))
        cache_key = f"rag:{cache_ns}:{limit}:{qhash}"
        cached = _semantic_cache.get(cache_key, query_embedding)
        if cached is not None:
            return cached

        vector_index.maybe_rebuild(self._build_vector_index)

        if vector_index.is_ready:
            results = self._vector_search(query_embedding, limit)
            if results:
                _semantic_cache.set(cache_key, results, query_embedding)
            return results

        if vector_index.is_available:
            try:
                self._build_vector_index()
                if vector_index.is_ready:
                    results = self._vector_search(query_embedding, limit)
                    if results:
                        _semantic_cache.set(cache_key, results, query_embedding)
                    return results
            except Exception as e:
                warning(f"向量索引构建失败，回退暴力搜索: {e}")

        results = self._brute_force_vector_search(query_embedding, limit)
        if results:
            _semantic_cache.set(cache_key, results, query_embedding)
        return results

    def _vector_search(self, query_embedding, limit):
        """Milvus 检索 + 批量取文档"""
        try:
            hits = vector_index.search(query_embedding, limit)
            if not hits:
                return []

            doc_ids = [h['id'] for h in hits]
            score_map = {h['id']: h['score'] for h in hits}

            self.connect()
            placeholders = ','.join(['?'] * len(doc_ids))
            sql = f"""SELECT id, title, subject, document_data
                      FROM knowledge_documents WHERE id IN ({placeholders})"""
            self.cursor.execute(sql, doc_ids)
            rows = {row['id']: row for row in self.cursor.fetchall()}

            results = []
            for did in doc_ids:
                row = rows.get(did)
                if not row:
                    continue
                doc_data = row['document_data']
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                raw_text = doc_data.get('content', {}).get('raw_text', '')
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'subject': row['subject'],
                    'content_text': raw_text[:1000],
                    'similarity': score_map[did],
                    'probability': score_map[did],
                    'document_data': doc_data,
                    'retrieval_method': 'ann',
                })
            return results
        except Exception as e:
            error(f"向量检索异常: {e}")
            return self._brute_force_vector_search(query_embedding, limit)
        finally:
            self.close()

    def _build_vector_index(self):
        """从数据库加载所有 embedding 构建 Milvus 索引"""
        self.connect()
        sql = """SELECT id, embedding, document_data FROM knowledge_documents
                 WHERE embedding IS NOT NULL"""
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        doc_ids = []
        embeddings = []
        for row in rows:
            emb = row['embedding']
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    emb = None
            if not emb:
                doc_data = row['document_data']
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                emb = doc_data.get('embedding') if doc_data else None
            if emb:
                doc_ids.append(row['id'])
                embeddings.append(emb)

        if embeddings:
            vector_index.rebuild(doc_ids, embeddings)
            vector_index.save()
            info(f"向量索引构建完成: {len(embeddings)} 条向量")
        self.close()

    def _brute_force_vector_search(self, query_embedding, limit=5):
        """暴力搜索（Milvus 不可用时的回退方案）- 使用numpy向量化加速"""
        try:
            self.connect()
            sql = """SELECT id, title, subject, document_data
                    FROM knowledge_documents
                    WHERE document_data->>'$.embedding' IS NOT NULL
                    LIMIT 200"""
            self.cursor.execute(sql)
            docs = self.cursor.fetchall()

            if not docs:
                return []

            doc_ids = []
            doc_titles = []
            doc_subjects = []
            doc_texts = []
            doc_datas = []
            embeddings_list = []

            for doc in docs:
                doc_data = doc['document_data']
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                doc_embedding = doc_data.get('embedding')
                if doc_embedding:
                    doc_ids.append(doc['id'])
                    doc_titles.append(doc['title'])
                    doc_subjects.append(doc['subject'])
                    raw_text = doc_data.get('content', {}).get('raw_text', '')
                    doc_texts.append(raw_text[:1000])
                    doc_datas.append(doc_data)
                    embeddings_list.append(doc_embedding)

            if not embeddings_list:
                return []

            import numpy as np
            query_vec = np.array(query_embedding, dtype='float32')
            doc_matrix = np.array(embeddings_list, dtype='float32')

            query_norm = np.linalg.norm(query_vec)
            doc_norms = np.linalg.norm(doc_matrix, axis=1)

            if query_norm == 0:
                return []

            similarities = np.dot(doc_matrix, query_vec) / (doc_norms * query_norm)

            top_indices = np.argsort(similarities)[::-1][:limit]

            results = []
            for idx in top_indices:
                results.append({
                    'id': doc_ids[idx],
                    'title': doc_titles[idx],
                    'subject': doc_subjects[idx],
                    'content_text': doc_texts[idx],
                    'similarity': float(similarities[idx]),
                    'document_data': doc_datas[idx]
                })

            return results

        except Exception as e:
            error(f"暴力向量检索失败: {e!s}")
            return []
        finally:
            self.close()

    def search_documents_by_fulltext(self, keywords, subject=None, limit=10):
        """
        KNN 关键词检索：FULLTEXT 标题匹配 + JSON LIKE 补充

        1. MATCH(title) AGAINST — FULLTEXT 精确匹配（高权重）
        2. JSON_EXTRACT LIKE — 摘要/知识点模糊匹配（补充覆盖）
        3. 去重合并，FULLTEXT 命中的排前面
        """
        # 语义缓存命中检查
        cache_key = f"rag:knn:{keywords}:{subject}:{limit}"
        cached = _semantic_cache.get(cache_key, None)
        if cached is not None:
            return cached

        try:
            self.connect()

            seen_ids = set()
            enriched = []

            # ── 路径 1: FULLTEXT 标题匹配 ──
            ft_results = self._fulltext_title_search(keywords, subject, limit)
            for doc in ft_results:
                seen_ids.add(doc['id'])
                enriched.append(doc)

            # ── 路径 2: JSON LIKE 补充（摘要 + 知识点）──
            like_results = self._json_like_search(keywords, subject, limit)
            for doc in like_results:
                if doc['id'] not in seen_ids:
                    seen_ids.add(doc['id'])
                    doc['similarity'] = doc.get('similarity', 0) * 0.5
                    enriched.append(doc)

            if not enriched:
                return self._simple_search(keywords, subject, limit)

            enriched.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            results = enriched[:limit]
            _semantic_cache.set(cache_key, results, None)
            return results

        except Exception as e:
            warning(f"FULLTEXT 检索失败，降级 LIKE: {e}")
            return self._simple_search(keywords, subject, limit)
        finally:
            self.close()

    def _fulltext_title_search(self, keywords, subject, limit):
        """MySQL FULLTEXT 全文检索（ngram 解析器，支持中文）"""
        try:
            terms = [kw.strip() for kw in keywords.split() if len(kw.strip()) > 1]
            if not terms:
                # 单字查询也放行，ngram 可命中
                terms = [keywords.strip()] if keywords.strip() else []
            if not terms:
                return []
            # ngram 解析器下用自然语言模式更稳
            fts_query = " ".join(terms)

            if subject:
                sql = """SELECT id, title, subject, document_data,
                                MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE) AS rank_score
                         FROM knowledge_documents
                         WHERE MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE)
                           AND subject = %s
                         ORDER BY rank_score DESC
                         LIMIT %s"""
                self.cursor.execute(sql, (fts_query, fts_query, subject, limit))
            else:
                sql = """SELECT id, title, subject, document_data,
                                MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE) AS rank_score
                         FROM knowledge_documents
                         WHERE MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE)
                         ORDER BY rank_score DESC
                         LIMIT %s"""
                self.cursor.execute(sql, (fts_query, fts_query, limit))

            results = []
            for row in self.cursor.fetchall():
                row = dict(row)
                doc_data = row.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                raw_text = doc_data.get('content', {}).get('raw_text', '')
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'subject': row['subject'],
                    'content_text': raw_text[:1000],
                    'similarity': float(row.get('rank_score') or 0),
                    'document_data': doc_data,
                    'retrieval_method': 'fulltext',
                })
            return results
        except Exception as e:
            warning(f"FULLTEXT 标题检索失败: {e}")
            return []

    def search_documents_by_bm25(self, query, subject=None, limit=10, temperature=1.0):
        """
        BM25 + Softmax 检索

        参数：
        - query: 查询文本
        - subject: 学科过滤（可选）
        - limit: 返回数量
        - temperature: Softmax 温度（<1 更尖锐，>1 更平缓）

        返回：
        - list: 文档列表，含 probability（Softmax 概率）
        """
        # 语义缓存命中检查
        cache_key = f"rag:bm25:{query}:{subject}:{limit}:{temperature}"
        cached = _semantic_cache.get(cache_key, None)
        if cached is not None:
            return cached

        try:
            from data.bm25_softmax import bm25_retriever

            if not bm25_retriever.is_ready:
                self._build_bm25_index(bm25_retriever)

            hits = bm25_retriever.retrieve(query, limit=limit * 2, temperature=temperature)
            if not hits:
                return self._simple_search(query, subject, limit)

            self.connect()
            doc_ids = [h["id"] for h in hits]
            placeholders = ",".join(["?"] * len(doc_ids))
            sql = f"""SELECT id, title, subject, document_data
                      FROM knowledge_documents WHERE id IN ({placeholders})"""
            self.cursor.execute(sql, doc_ids)
            rows = {row["id"]: row for row in self.cursor.fetchall()}

            results = []
            for h in hits:
                row = rows.get(h["id"])
                if not row:
                    continue
                if subject and row["subject"] != subject:
                    continue
                doc_data = row["document_data"]
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                raw_text = doc_data.get("content", {}).get("raw_text", "")
                results.append({
                    "id": row["id"],
                    "title": row["title"],
                    "subject": row["subject"],
                    "content_text": raw_text[:1000],
                    "similarity": h["score"],
                    "probability": h["probability"],
                    "document_data": doc_data,
                    "retrieval_method": "bm25_softmax",
                })
                if len(results) >= limit:
                    break

            # 最终结果重归一化，保证 probability 对返回列表求和为 1
            if results:
                from data.bm25_softmax import softmax

                probs = softmax([r["similarity"] for r in results], temperature=temperature)
                for r, p in zip(results, probs, strict=False):
                    r["probability"] = p

            _semantic_cache.set(cache_key, results, None)
            return results
        except Exception as e:
            warning(f"BM25 检索失败: {e}")
            return self._simple_search(query, subject, limit)
        finally:
            self.close()

    def _build_bm25_index(self, retriever):
        """从数据库加载文档构建 BM25 索引"""
        self.connect()
        self.cursor.execute(
            """SELECT id, title, subject, document_data FROM knowledge_documents"""
        )
        rows = []
        for row in self.cursor.fetchall():
            doc_data = row["document_data"]
            if isinstance(doc_data, str):
                try:
                    doc_data = json.loads(doc_data)
                except Exception:
                    doc_data = {}
            raw_text = (doc_data or {}).get("content", {}).get("raw_text", "")
            summary = (doc_data or {}).get("analysis", {}).get("summary", "")
            rows.append({
                "id": row["id"],
                "title": row["title"],
                "subject": row["subject"],
                "text": f"{summary} {raw_text}"[:5000],
            })
        n = retriever.build_from_rows(rows)
        info(f"BM25 索引构建完成: {n} 篇文档")
        self.close()

    def _json_like_search(self, keywords, subject, limit):
        """JSON 字段 LIKE 检索（摘要 + 知识点）"""
        try:
            search_term = f"%{keywords}%"
            if subject:
                sql = """SELECT id, title, subject, document_data
                         FROM knowledge_documents
                         WHERE subject = ?
                           AND (json_extract(document_data, '$.analysis.summary') LIKE ?
                                OR document_data LIKE ?)
                         ORDER BY usage_count DESC
                         LIMIT ?"""
                self.cursor.execute(sql, (subject, search_term, search_term, limit))
            else:
                sql = """SELECT id, title, subject, document_data
                         FROM knowledge_documents
                         WHERE json_extract(document_data, '$.analysis.summary') LIKE ?
                            OR document_data LIKE ?
                         ORDER BY usage_count DESC
                         LIMIT ?"""
                self.cursor.execute(sql, (search_term, search_term, limit))

            results = []
            for row in self.cursor.fetchall():
                doc_data = row['document_data']
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                raw_text = doc_data.get('content', {}).get('raw_text', '')
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'subject': row['subject'],
                    'content_text': raw_text[:1000],
                    'similarity': 0.3,
                    'document_data': doc_data,
                    'retrieval_method': 'knn_json_like',
                })
            return results
        except Exception as e:
            warning(f"JSON LIKE 检索失败: {e}")
            return []

    def search_hybrid_bm25_vector(self, query, query_embedding=None, subject=None,
                                  limit=5, temperature=1.0, weights=None):
        """
        BM25 + 向量 Softmax 概率融合混合检索

        流程:
          1. BM25 词项排序 → Softmax 概率
          2. Milvus 向量检索 → Softmax 概率
          3. 加权融合: fused = w_bm25·p_bm25 + w_vec·p_vec

        参数：
          query: 查询文本
          query_embedding: 查询向量（可选，缺失时退化为纯 BM25）
          subject: 学科过滤
          limit: 返回数量
          temperature: Softmax 温度
          weights: [bm25权重, 向量权重]，默认 [0.8, 0.2]（BM25 优先）

        返回：
          文档列表，含 probability（融合概率，和为 1）、bm25_score、vector_score
        """
        from data.bm25_softmax import fuse_probabilities

        if weights is None:
            weights = [0.8, 0.2]
        w_bm25, w_vec = float(weights[0]), float(weights[1])

        pool = max(limit * 3, 15)

        # ── 路径 1: BM25 ──
        bm25_hits = self.search_documents_by_bm25(query, subject=subject, limit=pool,
                                                  temperature=temperature)
        bm25_pairs = [(d["id"], d["similarity"]) for d in bm25_hits if d.get("id") is not None]
        bm25_map = {d["id"]: d for d in bm25_hits if d.get("id") is not None}

        # ── 路径 2: 向量 ──
        vec_pairs = []
        vec_map = {}
        if query_embedding:
            vec_hits = self.search_documents_by_vector(query_embedding, limit=pool)
            for d in vec_hits:
                if d.get("id") is None:
                    continue
                if subject and d.get("subject") != subject:
                    continue
                vec_pairs.append((d["id"], d["similarity"]))
                vec_map[d["id"]] = d

        # ── 融合 ──
        score_lists = [p for p in (bm25_pairs, vec_pairs) if p]
        active_w = []
        if bm25_pairs:
            active_w.append(w_bm25)
        if vec_pairs:
            active_w.append(w_vec)
        if not score_lists:
            return []
        if not active_w:
            active_w = [1.0] * len(score_lists)

        fused = fuse_probabilities(score_lists, weights=active_w, temperature=temperature)

        # ── 直接复用两路已取到的文档元数据，省掉第三次查库 ──
        data_map = {**bm25_map, **vec_map}

        results = []
        for doc_id, prob in fused[:limit]:
            src = data_map.get(doc_id)
            if not src:
                continue
            results.append({
                "id": doc_id,
                "title": src.get("title", ""),
                "subject": src.get("subject", ""),
                "content_text": src.get("content_text", ""),
                "similarity": prob,
                "probability": prob,
                "bm25_score": bm25_map.get(doc_id, {}).get("similarity"),
                "vector_score": vec_map.get(doc_id, {}).get("similarity"),
                "document_data": src.get("document_data"),
                "retrieval_method": "bm25_vector_hybrid",
            })

        if results:
            from data.bm25_softmax import softmax

            probs = softmax([r["similarity"] for r in results], temperature=temperature)
            for r, p in zip(results, probs, strict=False):
                r["probability"] = p
                r["similarity"] = p

        _semantic_cache.set(
            f"rag:bm25vec:{query}:{subject}:{limit}",
            results,
            query_embedding,
        )
        return results

    def hybrid_search(self, query, query_embedding=None, subject=None,
                      limit=5, rrf_k=60):
        """
        混合检索：KNN 关键词 + ANN 向量 → RRF 融合排序

        RRF 公式: RRF_score(d) = Σ 1/(k + rank_i(d)),  k=60

        参数：
          query: 关键词查询文本
          query_embedding: 查询向量（可选，为 None 时跳过 ANN）
          subject: 学科过滤
          limit: 返回数量
          rrf_k: RRF 平滑常数
        """
        # ── 语义缓存命中检查 ──
        cache_key = f"rag:hybrid:{query}:{subject}:{limit}"
        cached = _semantic_cache.get(cache_key, query_embedding)
        if cached is not None:
            return cached

        rrf_scores = {}
        data_map = {}

        # ── KNN 关键词路径 ──
        knn_results = self.search_documents_by_fulltext(query, subject, limit=limit * 3)
        for rank, doc in enumerate(knn_results):
            doc_id = doc.get('id')
            if doc_id is None:
                continue
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            data_map[doc_id] = doc

        # ── ANN 向量路径 ──
        if query_embedding:
            ann_results = self.search_documents_by_vector(query_embedding, limit=limit * 3)
            for rank, doc in enumerate(ann_results):
                doc_id = doc.get('id')
                if doc_id is None:
                    continue
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
                if doc_id not in data_map:
                    data_map[doc_id] = doc

        if not rrf_scores:
            return []

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        results = []
        for doc_id in sorted_ids[:limit]:
            doc = data_map[doc_id]
            doc['rrf_score'] = rrf_scores[doc_id]
            doc['retrieval_method'] = 'hybrid_knn_ann'
            results.append(doc)

        # 写入语义缓存
        _semantic_cache.set(cache_key, results, query_embedding)
        return results

    def _simple_search(self, keywords, subject=None, limit=10):
        """简单的 LIKE 搜索（回退方案）"""
        try:
            keyword_list = [f"%{kw}%" for kw in keywords.split() if len(kw) > 1]

            conditions = []
            params = []
            for kw in keyword_list[:3]:  # 最多 3 个关键词
                conditions.append("(title LIKE ? OR json_extract(document_data, '$.content.raw_text') LIKE ?)")
                params.extend([kw, kw])

            where_sql = " AND ".join(conditions)

            if subject:
                sql = f"""SELECT id, title, subject, document_data, 0.5 as relevance
                         FROM knowledge_documents
                         WHERE subject = ? AND ({where_sql})
                         LIMIT ?"""
                params = [subject, *params, limit]
            else:
                sql = f"""SELECT id, title, subject, document_data, 0.5 as relevance
                         FROM knowledge_documents
                         WHERE {where_sql}
                         LIMIT ?"""
                params = [*params, limit]

            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()

            # 解析 JSON 数据并提取所需字段
            for i, record in enumerate(results):
                record = dict(record)
                results[i] = record
                doc_data = record.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)

                record['content_text'] = doc_data.get('content', {}).get('raw_text', '') if doc_data else ''
                record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '') if doc_data else ''
                record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', []) if doc_data else []

            return results

        except Exception as e:
            error(f"简单搜索失败：{e!s}")
            return []

    def get_document_by_id(self, doc_id):
        """根据 ID 获取文档详情（解析 JSON 数据）"""
        try:
            self.connect()
            sql = "SELECT * FROM knowledge_documents WHERE id = ?"
            self.cursor.execute(sql, (doc_id,))
            record = self.cursor.fetchone()

            # 解析 JSON 字段
            if record:
                record = dict(record)
                if record.get('document_data'):
                    record['document_data'] = json.loads(record['document_data'])
                    # 兼容旧代码
                    doc_data = record['document_data']
                    record['content_text'] = doc_data.get('content', {}).get('raw_text', '')
                    record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', [])
                    record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '')

            return record
        except Exception as e:
            error(f"获取文档详情失败：{e!s}")
            return None
        finally:
            self.close()

    def update_document_usage(self, doc_id):
        """更新文档使用次数"""
        try:
            self.connect()
            sql = "UPDATE knowledge_documents SET usage_count = usage_count + 1 WHERE id = ?"
            self.cursor.execute(sql, (doc_id,))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新使用次数失败：{e!s}")
            return False
        finally:
            self.close()

    def delete_document(self, doc_id):
        """删除文档"""
        try:
            self.connect()
            # 先删除关联的知识点
            sql = "DELETE FROM knowledge_points WHERE doc_id = ?"
            self.cursor.execute(sql, (doc_id,))

            # 删除文档
            sql = "DELETE FROM knowledge_documents WHERE id = ?"
            self.cursor.execute(sql, (doc_id,))
            self.conn.commit()

            # 从向量索引 / BM25 索引中移除
            if vector_index.is_available:
                try:
                    vector_index.remove_by_ids({doc_id})
                    vector_index.save()
                except Exception:
                    pass
            try:
                from data.bm25_softmax import bm25_retriever

                bm25_retriever.index.remove(int(doc_id))
            except Exception:
                pass

            _clear_search_cache()
            return True
        except Exception as e:
            error(f"删除文档失败：{e!s}")
            return False
        finally:
            self.close()

    # ========== 知识点相关操作 ==========

    def get_knowledge_points_by_doc(self, doc_id):
        """获取文档的所有知识点"""
        try:
            self.connect()
            sql = "SELECT point_name FROM knowledge_points WHERE doc_id = ?"
            self.cursor.execute(sql, (doc_id,))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取知识点失败：{e!s}")
            return []
        finally:
            self.close()

    def search_by_knowledge_point(self, point_name, limit=20):
        """根据知识点搜索相关文档"""
        try:
            self.connect()
            sql = """SELECT kd.*, kp.point_name
                    FROM knowledge_documents kd
                    JOIN knowledge_points kp ON kd.id = kp.doc_id
                    WHERE kp.point_name LIKE ?
                    ORDER BY kd.upload_time DESC
                    LIMIT ?"""
            self.cursor.execute(sql, (f"%{point_name}%", limit))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"按知识点搜索失败：{e!s}")
            return []
        finally:
            self.close()

    # ========== 统计功能 ==========

    def get_statistics(self):
        """获取知识库统计信息"""
        try:
            self.connect()

            # 总文档数
            sql_total = "SELECT COUNT(*) as total_docs FROM knowledge_documents"
            self.cursor.execute(sql_total)
            total_docs = self.cursor.fetchone()['total_docs']

            # 各学科文档数
            sql_subject = """SELECT subject, COUNT(*) as count
                            FROM knowledge_documents
                            GROUP BY subject"""
            self.cursor.execute(sql_subject)
            subject_stats = self.cursor.fetchall()

            # 总知识点数
            sql_points = "SELECT COUNT(DISTINCT point_name) as total_points FROM knowledge_points"
            self.cursor.execute(sql_points)
            total_points = self.cursor.fetchone()['total_points']

            # 平均使用次数
            sql_usage = "SELECT AVG(usage_count) as avg_usage FROM knowledge_documents"
            self.cursor.execute(sql_usage)
            avg_usage = self.cursor.fetchone()['avg_usage'] or 0

            return {
                'total_documents': total_docs,
                'subject_distribution': subject_stats,
                'total_knowledge_points': total_points,
                'average_usage': round(avg_usage, 2)
            }
        except Exception as e:
            error(f"获取统计信息失败：{e!s}")
            return {}
        finally:
            self.close()


# 创建全局 RAG 知识库实例
rag_kb = RAGKnowledgeBase()
