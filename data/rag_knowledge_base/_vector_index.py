"""Milvus/FAISS 向量索引管理器（文档级 + 教学分块级）"""

import os
import threading
import time

import numpy as np

from core.logger import info, warning


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

    def __init__(self, collection: str | None = None):
        self._client = None
        self._dimension = 0
        self._lock = threading.Lock()
        self._dirty = False
        self._last_rebuild = 0
        self._rebuild_interval = 3600
        self._milvus_available = False
        self._count_cache = 0
        self._index_kind = "AUTOINDEX"
        self._collection = collection or _COLLECTION
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
            self._ensure_loaded()
            try:
                vec = self._normalize(query_embedding)
                # 维度守卫：与 collection 维度不一致时直接返回，避免检索崩溃
                if self._dimension and len(vec) != self._dimension:
                    warning(f"查询向量维度 {len(vec)} != 索引维度 {self._dimension}，跳过 Milvus 检索")
                    return []
                hits = self._client.search(
                    collection_name=self._collection,
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
                self._ensure_loaded()
                rows = [
                    {"id": int(did), "vector": self._normalize(emb)}
                    for did, emb in zip(doc_ids, embeddings, strict=False)
                ]
                self._client.insert(collection_name=self._collection, data=rows)
                self._count_cache += len(rows)
                self._dirty = True
            except Exception as e:
                warning(f"Milvus 增量添加失败: {e}")

    def remove_by_ids(self, doc_ids: set):
        """按 ID 移除向量（Milvus 原生删除）"""
        if not doc_ids or not self._milvus_available:
            return
        with self._lock:
            self._ensure_loaded()
            try:
                ids = [int(i) for i in doc_ids]
                self._client.delete(collection_name=self._collection, filter=f"id in {ids}")
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
                self._client.flush(self._collection)
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
                return self._has_data() or self._client.has_collection(self._collection)
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
                if not self._client.has_collection(self._collection):
                    return 0
                res = self._client.query(
                    collection_name=self._collection,
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

    def _ensure_loaded(self):
        """确保 collection 已加载（跨进程已存在的 collection 默认 released）"""
        if getattr(self, "_loaded", False):
            return
        try:
            self._client.load_collection(self._collection)
            self._loaded = True
        except Exception as e:
            warning(f"Milvus load_collection 失败: {e}")

    def _has_data(self) -> bool:
        try:
            return self._client is not None and self._client.has_collection(self._collection)
        except Exception:
            return False

    def _ensure_collection(self, dim: int):
        """确保 collection 存在且维度匹配"""
        if self._client is None:
            self._connect()
        if self._client.has_collection(self._collection):
            desc = self._client.describe_collection(self._collection)
            existing_dim = 0
            for f in desc.get("fields", []):
                if f.get("name") == "vector":
                    existing_dim = int((f.get("params") or {}).get("dim", 0))
            if existing_dim and existing_dim != dim:
                info(f"[Milvus] 维度变更 {existing_dim} → {dim}，重建 collection")
                self._client.drop_collection(self._collection)
            else:
                self._dimension = existing_dim or dim
                return

        self._client.create_collection(
            collection_name=self._collection,
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
                collection_name=self._collection,
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
            if self._client.has_collection(self._collection):
                self._client.drop_collection(self._collection)
            self._count_cache = 0
            self._dimension = 0
            self._loaded = False

            if not embeddings:
                self._dirty = True
                return

            dim = len(embeddings[0])
            self._ensure_collection(dim)
            rows = [
                {"id": int(did), "vector": self._normalize(emb)}
                for did, emb in zip(doc_ids, embeddings, strict=False)
            ]
            self._client.insert(collection_name=self._collection, data=rows)
            self._client.flush(self._collection)
            self._count_cache = len(rows)
            self._pick_index_kind(dim)
            self._dirty = False
        except Exception as e:
            warning(f"Milvus 重建失败: {e}")


# 全局单例
vector_index = VectorIndexManager()
# 分块级向量索引（教学结构感知 RAG：检索粒度=文本块而非整文档）
chunk_vector_index = VectorIndexManager(collection="knowledge_chunk_vectors")
