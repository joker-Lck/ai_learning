from core.logger import info, error, warning
"""RAG 知识库管理模块（JSON 格式存储）"""

import mysql.connector
from mysql.connector import pooling
import json
import time
import threading
from .config import get_rag_db_config
from datetime import datetime
import os
import numpy as np

# 查询缓存
_query_cache = {}
_CACHE_TTL = 600

def _get_cache_key(sql, params):
    """生成缓存键"""
    return f"rag:{sql}:{str(params)}"

def _get_cached_result(cache_key):
    """获取缓存结果"""
    if cache_key in _query_cache:
        result, timestamp = _query_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL:
            return result
        else:
            del _query_cache[cache_key]
    return None

def _set_cache_result(cache_key, result):
    """设置缓存结果"""
    _query_cache[cache_key] = (result, time.time())
    if len(_query_cache) > 200:
        oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]

def _clear_search_cache():
    """清空搜索缓存"""
    keys_to_delete = [k for k in _query_cache.keys() if k.startswith('rag:')]
    for key in keys_to_delete:
        del _query_cache[key]


# ═══════════════════════════════════════════
# FAISS 向量索引管理器
# ═══════════════════════════════════════════

_INDEX_DIR = os.path.join(os.path.dirname(__file__), 'faiss_index')
_INDEX_PATH = os.path.join(_INDEX_DIR, 'knowledge.index')
_IDS_PATH = os.path.join(_INDEX_DIR, 'doc_ids.json')


class VectorIndexManager:
    """
    基于 FAISS 的向量索引管理器
    - 内存驻留索引，O(log n) 近似最近邻检索
    - 自动持久化到磁盘，重启后快速加载
    - 文档变更时惰性重建
    """

    def __init__(self):
        self._index = None
        self._doc_ids = []        # 与 FAISS 行号对齐的文档 ID 列表
        self._dimension = 0
        self._lock = threading.Lock()
        self._dirty = False
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
            for score, idx in zip(scores[0], indices[0]):
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
            except Exception:
                pass
            try:
                with open(_IDS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self._doc_ids, f)
            except Exception:
                pass
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
                with open(_IDS_PATH, 'r', encoding='utf-8') as f:
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
        self.conn_pool = None
        self.conn = None
        self.cursor = None
        self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        try:
            config = get_rag_db_config()
            config['use_pure'] = True
            self.conn_pool = pooling.MySQLConnectionPool(
                pool_name="rag_pool",
                pool_size=5,
                pool_reset_session=True,
                **config
            )
        except Exception as e:
            error(f"RAG 连接池初始化失败：{str(e)}")
    
    def _get_connection(self):
        """从连接池获取连接"""
        if self.conn_pool:
            return self.conn_pool.get_connection()
        config = get_rag_db_config()
        config['use_pure'] = True
        return mysql.connector.connect(**config)
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = self._get_connection()
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except Exception as e:
            self.conn = None
            self.cursor = None
            raise ConnectionError(f"RAG 知识库连接失败：{str(e)}")

    def _ensure_connected(self):
        """确保数据库已连接，返回 True/False"""
        if self.cursor is not None and self.conn is not None:
            try:
                self.conn.ping(reconnect=False)
                return True
            except Exception:
                pass
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
            warning(f"关闭连接失败：{str(e)}")
    
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
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                params = (
                    title, subject, file_path, file_type, file_size,
                    json.dumps(document_data, ensure_ascii=False),
                    json.dumps(embedding, ensure_ascii=False) if embedding else None,
                    uploaded_by, datetime.now()
                )
            else:
                sql = """INSERT INTO knowledge_documents
                        (title, subject, file_path, file_type, file_size, document_data, uploaded_by, upload_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
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
            error(f"添加文档失败：{str(e)}")
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
                sql = """INSERT INTO knowledge_points (doc_id, point_name) 
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE point_name = point_name"""
                self.cursor.execute(sql, (doc_id, point))
            
            self.conn.commit()
        except Exception as e:
            error(f"添加知识点失败：{str(e)}")
    
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
                    WHERE subject = %s 
                    ORDER BY upload_time DESC 
                    LIMIT %s"""
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
            error(f"获取学科文档失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def get_all_documents(self, limit=100, offset=0):
        """获取所有文档（按上传时间倒序，最新在前）"""
        try:
            self.connect()
            sql = """SELECT * FROM knowledge_documents
                    ORDER BY upload_time DESC
                    LIMIT %s OFFSET %s"""
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
            error(f"获取所有文档失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def get_documents_by_user(self, user_id, limit=100, offset=0):
        """获取指定用户上传的文档"""
        try:
            self.connect()
            sql = """SELECT * FROM knowledge_documents
                    WHERE uploaded_by = %s
                    ORDER BY upload_time DESC
                    LIMIT %s OFFSET %s"""
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
            error(f"获取用户文档失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def search_documents(self, keywords, subject=None, limit=10):
        """搜索知识文档"""
        try:
            # 检查缓存
            cache_key = _get_cache_key("search_docs", (keywords[:50], subject, limit))
            cached = _get_cached_result(cache_key)
            if cached:
                return cached
            
            self.connect()
            
            # 直接搜索 title、ai_summary、knowledge_points
            if subject:
                sql = """SELECT id, title, subject, document_data
                        FROM knowledge_documents
                        WHERE subject = %s
                          AND (title LIKE %s 
                               OR JSON_EXTRACT(document_data, '$.analysis.summary') LIKE %s
                               OR JSON_SEARCH(document_data, 'one', %s, NULL, '$.analysis.knowledge_points[*]') IS NOT NULL)
                        ORDER BY usage_count DESC, upload_time DESC
                        LIMIT %s"""
                search_term = f"%{keywords}%"
                self.cursor.execute(sql, (subject, search_term, search_term, keywords, limit))
            else:
                sql = """SELECT id, title, subject, document_data
                        FROM knowledge_documents
                        WHERE title LIKE %s 
                           OR JSON_EXTRACT(document_data, '$.analysis.summary') LIKE %s
                           OR JSON_SEARCH(document_data, 'one', %s, NULL, '$.analysis.knowledge_points[*]') IS NOT NULL
                        ORDER BY usage_count DESC, upload_time DESC
                        LIMIT %s"""
                search_term = f"%{keywords}%"
                self.cursor.execute(sql, (search_term, search_term, keywords, limit))
            
            results = self.cursor.fetchall()
            
            if not results:
                # 回退到简单搜索
                return self._simple_search(keywords, subject, limit)
            
            # 解析 JSON 数据并计算相似度
            keyword_set = set(keywords.lower().split())
            enriched_results = []
            
            for result in results:
                doc_data = result.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)
                
                # 只提取必要字段
                ai_summary = doc_data.get('analysis', {}).get('summary', '')
                knowledge_points = doc_data.get('analysis', {}).get('knowledge_points', [])
                raw_text = doc_data.get('content', {}).get('raw_text', '')[:1000]
                
                # 计算相似度
                text = f"{result.get('title', '')} {ai_summary} {','.join(knowledge_points)}"
                text_words = set(text.lower().split())
                common = len(keyword_set & text_words)
                total = len(keyword_set | text_words)
                similarity = common / total if total > 0 else 0
                
                enriched_results.append({
                    'id': result['id'],
                    'title': result['title'],
                    'subject': result['subject'],
                    'content_text': raw_text,
                    'ai_summary': ai_summary,
                    'knowledge_points': knowledge_points,
                    'similarity': similarity,
                    'usage_count': result.get('usage_count', 0)
                })
            
            # 按相似度排序
            enriched_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = enriched_results[:limit]
            
            # 缓存结果
            if final_results:
                _set_cache_result(cache_key, final_results)
            
            return final_results
            
        except Exception as e:
            error(f"搜索文档失败：{str(e)}")
            return self._simple_search(keywords, subject, limit)
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
        # ── 路径 1：FAISS 检索 ──
        if vector_index.is_ready:
            return self._faiss_search(query_embedding, limit)

        # 索引未就绪 → 尝试从 DB 加载并构建
        if vector_index._faiss_available:
            try:
                self._build_faiss_index()
                if vector_index.is_ready:
                    return self._faiss_search(query_embedding, limit)
            except Exception as e:
                warning(f"FAISS 索引构建失败，回退暴力搜索: {e}")

        # ── 路径 2：原有暴力搜索（兜底）──
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
            placeholders = ','.join(['%s'] * len(doc_ids))
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
        """原有暴力搜索（FAISS 不可用时的回退方案）"""
        try:
            from .embedding_service import embedding_service

            self.connect()
            sql = """SELECT id, title, subject, document_data
                    FROM knowledge_documents
                    WHERE document_data->>'$.embedding' IS NOT NULL
                    LIMIT 100"""
            self.cursor.execute(sql)
            docs = self.cursor.fetchall()

            results = []
            for doc in docs:
                doc_data = doc.get('document_data')
                if isinstance(doc_data, str):
                    doc_data = json.loads(doc_data)

                doc_embedding = doc_data.get('embedding')
                if doc_embedding:
                    similarity = embedding_service.cosine_similarity(query_embedding, doc_embedding)
                    raw_text = doc_data.get('content', {}).get('raw_text', '')
                    results.append({
                        'id': doc['id'],
                        'title': doc['title'],
                        'subject': doc['subject'],
                        'content_text': raw_text[:1000],
                        'similarity': float(similarity),
                        'document_data': doc_data
                    })

            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

        except Exception as e:
            error(f"暴力向量检索失败: {str(e)}")
            return []
        finally:
            self.close()
    
    def _simple_search(self, keywords, subject=None, limit=10):
        """简单的 LIKE 搜索（回退方案）"""
        try:
            keyword_list = [f"%{kw}%" for kw in keywords.split() if len(kw) > 1]
            
            conditions = []
            params = []
            for kw in keyword_list[:3]:  # 最多 3 个关键词
                conditions.append("(title LIKE %s OR JSON_EXTRACT(document_data, '$.content.raw_text') LIKE %s)")
                params.extend([kw, kw])
            
            where_sql = " AND ".join(conditions)
            
            if subject:
                sql = f"""SELECT id, title, subject, document_data, 0.5 as relevance
                         FROM knowledge_documents
                         WHERE subject = %s AND ({where_sql})
                         LIMIT %s"""
                params = [subject] + params + [limit]
            else:
                sql = f"""SELECT id, title, subject, document_data, 0.5 as relevance
                         FROM knowledge_documents
                         WHERE {where_sql}
                         LIMIT %s"""
                params = params + [limit]
            
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
            error(f"简单搜索失败：{str(e)}")
            return []
    
    def get_document_by_id(self, doc_id):
        """根据 ID 获取文档详情（解析 JSON 数据）"""
        try:
            self.connect()
            sql = "SELECT * FROM knowledge_documents WHERE id = %s"
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
            error(f"获取文档详情失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def update_document_usage(self, doc_id):
        """更新文档使用次数"""
        try:
            self.connect()
            sql = "UPDATE knowledge_documents SET usage_count = usage_count + 1 WHERE id = %s"
            self.cursor.execute(sql, (doc_id,))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新使用次数失败：{str(e)}")
            return False
        finally:
            self.close()
    
    def delete_document(self, doc_id):
        """删除文档"""
        try:
            self.connect()
            # 先删除关联的知识点
            sql = "DELETE FROM knowledge_points WHERE doc_id = %s"
            self.cursor.execute(sql, (doc_id,))

            # 删除文档
            sql = "DELETE FROM knowledge_documents WHERE id = %s"
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
            error(f"删除文档失败：{str(e)}")
            return False
        finally:
            self.close()
    
    # ========== 知识点相关操作 ==========
    
    def get_knowledge_points_by_doc(self, doc_id):
        """获取文档的所有知识点"""
        try:
            self.connect()
            sql = "SELECT point_name FROM knowledge_points WHERE doc_id = %s"
            self.cursor.execute(sql, (doc_id,))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取知识点失败：{str(e)}")
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
                    WHERE kp.point_name LIKE %s
                    ORDER BY kd.upload_time DESC
                    LIMIT %s"""
            self.cursor.execute(sql, (f"%{point_name}%", limit))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"按知识点搜索失败：{str(e)}")
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
            error(f"获取统计信息失败：{str(e)}")
            return {}
        finally:
            self.close()


# 创建全局 RAG 知识库实例
rag_kb = RAGKnowledgeBase()
