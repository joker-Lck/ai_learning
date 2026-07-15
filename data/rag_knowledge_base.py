from core.logger import error, info, warning

"""RAG 知识库管理模块（JSON 格式存储）"""

import json
import os
import sqlite3
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


_query_cache = LRUCache(max_size=200, ttl=600)
_CACHE_TTL = 600

def _clear_search_cache():
    """清空搜索缓存"""
    _query_cache.clear(prefix='rag:')


# ═══════════════════════════════════════════
# FAISS 向量索引管理器
# ═══════════════════════════════════════════

# FAISS不支持中文路径，使用用户目录下的.faiss_index
_INDEX_DIR = os.path.join(os.path.expanduser('~'), '.faiss_index')
_INDEX_PATH = os.path.join(_INDEX_DIR, 'knowledge.index')
_IDS_PATH = os.path.join(_INDEX_DIR, 'doc_ids.json')


class VectorIndexManager:
    """
    基于 FAISS 的向量索引管理器
    - 内存驻留索引，O(log n) 近似最近邻检索
    - 自动持久化到磁盘，重启后快速加载
    - 文档变更时惰性重建
    - 支持定期全量重建以修正漂移
    """

    def __init__(self):
        self._index = None
        self._doc_ids = []
        self._dimension = 0
        self._lock = threading.Lock()
        self._dirty = False
        self._last_rebuild = 0
        self._rebuild_interval = 3600
        self._faiss_available = False
        try:
            import faiss as _faiss
            self._faiss = _faiss
            self._faiss_available = True
        except ImportError:
            self._faiss = None

    # ── 公开接口 ──────────────────────────────

    def search(self, query_embedding: list, limit: int = 5) -> list:
        """
        检索最相似的文档

        返回: [{'id': doc_id, 'score': float}, ...]
        """
        with self._lock:
            if not self._faiss_available or self._index is None or self._index.ntotal == 0:
                return []

            vec = np.array([query_embedding], dtype='float32')
            self._faiss.normalize_L2(vec)

            k = min(limit, self._index.ntotal)
            scores, indices = self._index.search(vec, k)

            results = []
            for score, idx in zip(scores[0], indices[0], strict=False):
                if idx < 0 or idx >= len(self._doc_ids):
                    continue
                results.append({
                    'id': self._doc_ids[idx],
                    'score': float(score)
                })
            return results

    def add_vectors(self, doc_ids: list, embeddings: list):
        """增量添加向量"""
        if not doc_ids or not embeddings:
            return
        if not self._faiss_available:
            return

        with self._lock:
            dim = len(embeddings[0])
            if self._index is None:
                self._dimension = dim
                self._index = self._create_index(dim)
            elif dim != self._dimension:
                self._rebuild_internal([], [])

            vecs = np.array(embeddings, dtype='float32')
            self._faiss.normalize_L2(vecs)
            self._index.add(vecs)
            self._doc_ids.extend(doc_ids)
            self._dirty = True

    def remove_by_ids(self, doc_ids: set):
        """按 ID 移除向量（FAISS 不支持原生删除，需重建）"""
        with self._lock:
            if not self._faiss_available or self._index is None or not doc_ids:
                return

            keep_mask = [i for i, did in enumerate(self._doc_ids) if did not in doc_ids]
            if len(keep_mask) == len(self._doc_ids):
                return

            if len(keep_mask) == 0:
                self._index = self._create_index(self._dimension)
                self._doc_ids = []
            else:
                all_vecs = np.array(
                    [self._index.reconstruct(i) for i in keep_mask], dtype='float32'
                )
                self._index = self._create_index(self._dimension)
                self._index.add(all_vecs)
                self._doc_ids = [self._doc_ids[i] for i in keep_mask]

            self._dirty = True

    def rebuild(self, doc_ids: list, embeddings: list):
        """全量重建索引"""
        with self._lock:
            self._rebuild_internal(doc_ids, embeddings)

    def save(self):
        """持久化索引到磁盘"""
        with self._lock:
            if not self._dirty or self._index is None:
                return
            os.makedirs(_INDEX_DIR, exist_ok=True)
            try:
                self._faiss.write_index(self._index, _INDEX_PATH)
            except Exception as e:
                warning(f"FAISS索引持久化失败: {e}")
            try:
                with open(_IDS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self._doc_ids, f)
            except Exception as e:
                warning(f"文档ID映射持久化失败: {e}")
            self._dirty = False

    def load(self) -> bool:
        """从磁盘加载索引"""
        with self._lock:
            if not self._faiss_available:
                return False
            if not os.path.exists(_INDEX_PATH) or not os.path.exists(_IDS_PATH):
                return False
            try:
                self._index = self._faiss.read_index(_INDEX_PATH)
                with open(_IDS_PATH, encoding='utf-8') as f:
                    self._doc_ids = json.load(f)
                self._dimension = self._index.d
                self._dirty = False
                return True
            except Exception:
                return False

    @property
    def is_ready(self) -> bool:
        return self._faiss_available and self._index is not None and self._index.ntotal > 0

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal if self._index else 0

    def maybe_rebuild(self, rebuild_fn):
        if time.time() - self._last_rebuild > self._rebuild_interval:
            try:
                rebuild_fn()
                self._last_rebuild = time.time()
            except Exception as e:
                warning(f"定期重建FAISS索引失败: {e}")

    # ── 内部方法 ──────────────────────────────

    def _rebuild_internal(self, doc_ids: list, embeddings: list):
        """内部重建（需已持有锁）"""
        if not embeddings:
            self._index = None
            self._doc_ids = []
            self._dimension = 0
            self._dirty = True
            return

        self._dimension = len(embeddings[0])
        self._index = self._create_index(self._dimension)
        vecs = np.array(embeddings, dtype='float32')
        self._faiss.normalize_L2(vecs)
        self._index.add(vecs)
        self._doc_ids = list(doc_ids)
        self._dirty = True

    def _create_index(self, dim: int):
        """创建 FAISS FlatIP 索引（归一化后内积等价余弦相似度）"""
        if dim <= 0 or not self._faiss_available:
            return None
        return self._faiss.IndexFlatIP(dim)


# 全局单例
vector_index = VectorIndexManager()


class RAGKnowledgeBase:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db_path = get_rag_db_path()
        self._init_fts()

    def _init_fts(self):
        """初始化 FTS5 虚拟表（如果表已存在）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_documents'"
            )
            if cursor.fetchone() is None:
                conn.close()
                return
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_documents_fts
                USING fts5(title, subject, content='knowledge_documents', content_rowid='id')
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_documents_ai
                AFTER INSERT ON knowledge_documents BEGIN
                    INSERT INTO knowledge_documents_fts(rowid, title, subject)
                    VALUES (new.id, new.title, new.subject);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_documents_ad
                AFTER DELETE ON knowledge_documents BEGIN
                    INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                    VALUES('delete', old.id, old.title, old.subject);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS knowledge_documents_au
                AFTER UPDATE ON knowledge_documents BEGIN
                    INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                    VALUES('delete', old.id, old.title, old.subject);
                    INSERT INTO knowledge_documents_fts(rowid, title, subject)
                    VALUES (new.id, new.title, new.subject);
                END
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            warning(f"FTS5 初始化失败：{e!s}")

    def _get_connection(self):
        """获取 SQLite 连接"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def connect(self):
        """连接数据库"""
        try:
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
                    "raw_text": content_text[:50000] if content_text else "",  # 限制长度
                    "text_length": len(content_text) if content_text else 0,
                    "paragraphs": self._split_paragraphs(content_text) if content_text else []
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

            # 增量更新 FAISS 索引
            if embedding and vector_index._faiss_available:
                try:
                    vector_index.add_vectors([doc_id], [embedding])
                    vector_index.save()
                except Exception:
                    pass  # 索引更新失败不影响文档写入

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

    def _split_paragraphs(self, text, max_length=500):
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
                # 按句子分割
                sentences = para.split('。')
                current = ""
                for sentence in sentences:
                    if len(current + sentence) <= max_length:
                        current += sentence + "。"
                    else:
                        if current:
                            result.append(current.strip())
                        current = sentence + "。"
                if current:
                    result.append(current.strip())

        return result[:100]  # 最多保留 100 个段落

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
            for record in results:
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
            for record in results:
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

            for record in results:
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

    def search_documents_by_vector(self, query_embedding, limit=5):
        """
        基于向量相似度检索文档（优先 FAISS，回退暴力搜索）

        参数：
        - query_embedding: 查询文本的向量
        - limit: 返回数量限制

        返回：
        - list: 按相似度排序的文档列表
        """
        vector_index.maybe_rebuild(self._build_faiss_index)

        if vector_index.is_ready:
            return self._faiss_search(query_embedding, limit)

        if vector_index._faiss_available:
            try:
                self._build_faiss_index()
                if vector_index.is_ready:
                    return self._faiss_search(query_embedding, limit)
            except Exception as e:
                warning(f"FAISS 索引构建失败，回退暴力搜索: {e}")

        return self._brute_force_vector_search(query_embedding, limit)

    def _faiss_search(self, query_embedding, limit):
        """FAISS 检索 + 批量取文档"""
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
                doc_data = row.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                raw_text = doc_data.get('content', {}).get('raw_text', '')
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'subject': row['subject'],
                    'content_text': raw_text[:1000],
                    'similarity': score_map[did],
                    'document_data': doc_data
                })
            return results
        except Exception as e:
            error(f"FAISS 检索异常: {e}")
            return self._brute_force_vector_search(query_embedding, limit)
        finally:
            self.close()

    def _build_faiss_index(self):
        """从数据库加载所有 embedding 构建 FAISS 索引"""
        self.connect()
        sql = """SELECT id, document_data FROM knowledge_documents
                 WHERE embedding IS NOT NULL"""
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        doc_ids = []
        embeddings = []
        for row in rows:
            doc_data = row.get('document_data')
            if isinstance(doc_data, str):
                doc_data = json.loads(doc_data)
            emb = doc_data.get('embedding') if doc_data else None
            if emb:
                doc_ids.append(row['id'])
                embeddings.append(emb)

        if embeddings:
            vector_index.rebuild(doc_ids, embeddings)
            vector_index.save()
            info(f"FAISS 索引构建完成: {len(embeddings)} 条向量")
        self.close()

    def _brute_force_vector_search(self, query_embedding, limit=5):
        """暴力搜索（FAISS 不可用时的回退方案）- 使用numpy向量化加速"""
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
                doc_data = doc.get('document_data')
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
            return enriched[:limit]

        except Exception as e:
            warning(f"FULLTEXT 检索失败，降级 LIKE: {e}")
            return self._simple_search(keywords, subject, limit)
        finally:
            self.close()

    def _fulltext_title_search(self, keywords, subject, limit):
        """FTS5 全文检索"""
        try:
            # FTS5 查询：用双引号包裹关键词作为字面量
            fts_query = " ".join(f'"{kw}"' for kw in keywords.split() if len(kw) > 1)
            if not fts_query:
                return []

            if subject:
                sql = """SELECT kd.id, kd.title, kd.subject, kd.document_data, rank
                         FROM knowledge_documents_fts fts
                         JOIN knowledge_documents kd ON fts.rowid = kd.id
                         WHERE knowledge_documents_fts MATCH ?
                           AND kd.subject = ?
                         ORDER BY rank
                         LIMIT ?"""
                self.cursor.execute(sql, (fts_query, subject, limit))
            else:
                sql = """SELECT kd.id, kd.title, kd.subject, kd.document_data, rank
                         FROM knowledge_documents_fts fts
                         JOIN knowledge_documents kd ON fts.rowid = kd.id
                         WHERE knowledge_documents_fts MATCH ?
                         ORDER BY rank
                         LIMIT ?"""
                self.cursor.execute(sql, (fts_query, limit))

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
                    'similarity': float(row.get('rank', 0)) * -1,  # rank 是负数，越小越好
                    'document_data': doc_data,
                    'retrieval_method': 'fts5',
                })
            return results
        except Exception as e:
            warning(f"FTS5 标题检索失败: {e}")
            return []

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
                doc_data = row.get('document_data')
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
            for record in results:
                doc_data = record.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)

                record['content_text'] = doc_data.get('content', {}).get('raw_text', '')
                record['ai_summary'] = doc_data.get('analysis', {}).get('summary', '')
                record['knowledge_points'] = doc_data.get('analysis', {}).get('knowledge_points', [])

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
            if record and record.get('document_data'):
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

            # 从 FAISS 索引中移除
            if vector_index._faiss_available:
                try:
                    vector_index.remove_by_ids({doc_id})
                    vector_index.save()
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
