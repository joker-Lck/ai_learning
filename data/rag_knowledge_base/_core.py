"""RAG 知识库主体：文档 CRUD、向量/全文/BM25/混合检索、结构分块检索"""

import json
from datetime import datetime

import numpy as np

from core.logger import error, info, warning
from data import dbapi as dbapi
from data.config import get_rag_db_path

from ._caches import _clear_search_cache, _semantic_cache
from ._vector_index import chunk_vector_index, vector_index


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

            # 教学结构感知分块索引（T1）：分块级向量 + 章节路径元数据
            try:
                self.index_document_chunks(doc_id, content_text, title=title)
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
        """将文本分割为段落（共享实现见 core.text_utils）"""
        from core.text_utils import split_paragraphs

        return split_paragraphs(text, max_length=max_length, max_count=max_count)

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
    # ─── 教学结构感知检索（分块级索引 + 长上下文组装）──────────

    def ensure_chunk_table(self):
        """确保 knowledge_chunks 表存在（分块级索引，独立于文档级索引）"""
        try:
            self.connect()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    doc_id BIGINT NOT NULL,
                    chunk_order INT DEFAULT 0,
                    chunk_id VARCHAR(64),
                    level INT DEFAULT 4,
                    section_path VARCHAR(512),
                    heading VARCHAR(255),
                    kind VARCHAR(32) DEFAULT 'body',
                    content_text LONGTEXT,
                    char_start INT DEFAULT 0,
                    char_end INT DEFAULT 0,
                    KEY idx_knowledge_chunks_doc (doc_id),
                    KEY idx_knowledge_chunks_chunk (chunk_id),
                    CONSTRAINT fk_knowledge_chunks_doc FOREIGN KEY (doc_id)
                        REFERENCES knowledge_documents(id) ON DELETE CASCADE
                )""")
            self.conn.commit()
            return True
        except Exception as e:
            warning(f"knowledge_chunks 建表失败: {e}")
            return False
        finally:
            self.close()

    def index_document_chunks(self, doc_id, content_text, title=""):
        """按教学结构切块并建立分块级索引（结构感知 RAG 的入库路径）

        - 切块携带 section_path / kind 元数据（见 data/structure_chunker.py）
        - 分块向量写入 Milvus collection `knowledge_chunk_vectors`
        - 元数据落 knowledge_chunks 表，检索时可回溯教学位置

        返回: 分块数量（失败返回 0，不影响文档主入库）
        """
        if not content_text or not content_text.strip():
            return 0
        try:
            from data.structure_chunker import StructureChunker

            tree = StructureChunker(max_length=900, min_length=60).chunk(content_text, doc_id=doc_id)
            if not tree.chunks:
                return 0

            self.ensure_chunk_table()
            self.connect()

            # 批量取块向量（BGE-M3；TF-IDF 回退路径同样可用）
            texts = [c.text for c in tree.chunks]
            try:
                from data.embedding_service import embedding_service
                vectors = embedding_service.get_embeddings(texts)
            except Exception as e:
                warning(f"分块向量生成失败，仅存文本: {e}")
                vectors = [None] * len(texts)

            sql = """INSERT INTO knowledge_chunks
                    (doc_id, chunk_order, chunk_id, level, section_path, heading,
                     kind, content_text, char_start, char_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            chunk_db_ids = []
            chunk_vecs = []
            for c, vec in zip(tree.chunks, vectors):
                self.cursor.execute(sql, (
                    doc_id, c.order, c.chunk_id, c.level,
                    (c.section_path or "")[:512], (c.heading or "")[:255],
                    c.kind, c.text, c.char_start, c.char_end,
                ))
                chunk_db_ids.append(self.cursor.lastrowid)
                if vec:
                    chunk_vecs.append(vec)
            self.conn.commit()

            # 分块向量入 Milvus（id=chunk 表主键，与文档级索引隔离）
            if chunk_db_ids and chunk_vecs and len(chunk_vecs) == len(chunk_db_ids):
                try:
                    chunk_vector_index.add_vectors(chunk_db_ids, chunk_vecs)
                    chunk_vector_index.save()
                except Exception as e:
                    warning(f"分块向量入索引失败: {e}")

            info(f"文档 {doc_id} 结构化分块完成: {len(tree.chunks)} 块, "
                 f"结构节点 {tree.stats.get('n_sections', 0)}")
            return len(tree.chunks)
        except Exception as e:
            warning(f"分块索引失败（文档主数据不受影响）: {e}")
            return 0
        finally:
            self.close()

    def search_chunks_structural(self, query_embedding, subject=None, limit=5,
                                 expand=True, neighbor_window=1, max_chars=4800):
        """结构感知检索：分块级向量命中 → 长上下文组装

        参数:
            query_embedding: 查询向量
            subject: 学科过滤（可选）
            limit: 返回上下文条数
            expand: 是否做邻域上下文组装（长上下文）
            neighbor_window: 命中块前后各取几个同节邻接块
            max_chars: 组装预算（字符）

        返回: [{id(=doc_id), title, subject, content_text(组装后上下文),
                section_path, chunk_ids, similarity, probability,
                retrieval_method: 'structural', expanded}]
        """
        if not query_embedding:
            return []
        if not chunk_vector_index.is_available:
            return []
        try:
            from data.structure_chunker import expand_context

            hits = chunk_vector_index.search(query_embedding, max(limit * 3, 15))
            if not hits:
                return []
            chunk_ids = [h["id"] for h in hits]
            score_map = {h["id"]: h["score"] for h in hits}

            self.connect()
            placeholders = ",".join(["?"] * len(chunk_ids))
            sql = f"""SELECT c.id, c.doc_id, c.chunk_order, c.chunk_id, c.level,
                             c.section_path, c.heading, c.kind, c.content_text,
                             d.title, d.subject
                      FROM knowledge_chunks c
                      JOIN knowledge_documents d ON d.id = c.doc_id
                      WHERE c.id IN ({placeholders})"""
            self.cursor.execute(sql, chunk_ids)
            rows = self.cursor.fetchall()

            hit_chunks = []
            for r in rows:
                r = dict(r)
                if subject and r.get("subject") != subject:
                    continue
                hit_chunks.append({
                    "chunk_db_id": r["id"],
                    "doc_id": r["doc_id"],
                    "order": r["chunk_order"],
                    "chunk_id": r["chunk_id"],
                    "section_path": r["section_path"] or "",
                    "heading": r["heading"] or "",
                    "kind": r["kind"] or "body",
                    "text": r["content_text"] or "",
                    "title": r["title"] or "",
                    "subject": r["subject"] or "",
                    "similarity": score_map.get(r["id"], 0.0),
                })
            if not hit_chunks:
                return []

            if not expand:
                results = [{
                    "id": c["doc_id"],
                    "title": c["title"],
                    "subject": c["subject"],
                    "content_text": c["text"][:1000],
                    "section_path": c["section_path"],
                    "kind": c["kind"],
                    "chunk_ids": [c["chunk_id"]],
                    "similarity": c["similarity"],
                    "probability": c["similarity"],
                    "retrieval_method": "structural",
                    "expanded": False,
                } for c in hit_chunks[:limit]]
                return results

            # 长上下文组装：同文档全量块参与邻域扩展
            doc_ids = {c["doc_id"] for c in hit_chunks}
            ph = ",".join(["?"] * len(doc_ids))
            self.cursor.execute(
                f"""SELECT id, doc_id, chunk_order, chunk_id, section_path,
                           heading, kind, content_text
                    FROM knowledge_chunks WHERE doc_id IN ({ph})""",
                list(doc_ids))
            all_chunks = []
            for r in self.cursor.fetchall():
                r = dict(r)
                all_chunks.append({
                    "chunk_db_id": r["id"],
                    "doc_id": r["doc_id"],
                    "order": r["chunk_order"],
                    "chunk_id": r["chunk_id"],
                    "section_path": r["section_path"] or "",
                    "heading": r["heading"] or "",
                    "kind": r["kind"] or "body",
                    "text": r["content_text"] or "",
                })

            ctx_list = expand_context(hit_chunks, all_chunks, max_chars=max_chars,
                                      neighbor_window=neighbor_window)
            results = []
            for ctx in ctx_list[:limit]:
                results.append({
                    "id": ctx.get("doc_id"),
                    "title": ctx.get("title", ""),
                    "subject": next((c["subject"] for c in hit_chunks
                                     if c["doc_id"] == ctx.get("doc_id")), ""),
                    "content_text": ctx["context_text"],
                    "section_path": ctx.get("section_path", ""),
                    "kind": "context",
                    "chunk_ids": ctx.get("chunk_ids", []),
                    "similarity": ctx.get("score", 0.0),
                    "probability": ctx.get("score", 0.0),
                    "retrieval_method": "structural",
                    "expanded": ctx.get("expanded", False),
                })
            return results
        except Exception as e:
            warning(f"结构检索失败: {e}")
            return []
        finally:
            self.close()

    def get_chunks_by_doc(self, doc_id):
        """取文档全量分块（评估/调试用）"""
        try:
            self.ensure_chunk_table()
            self.connect()
            self.cursor.execute(
                """SELECT id, chunk_order, chunk_id, level, section_path, heading,
                          kind, content_text, char_start, char_end
                   FROM knowledge_chunks WHERE doc_id = ? ORDER BY chunk_order""",
                (doc_id,))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            warning(f"取分块失败: {e}")
            return []
        finally:
            self.close()


rag_kb = RAGKnowledgeBase()
