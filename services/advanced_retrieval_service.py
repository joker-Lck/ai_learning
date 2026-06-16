"""
高级检索服务 — 2023-2026 新型检索方法
实现 5 种现代 RAG 检索策略：
  1. HyDE（假设性文档嵌入）           — Gao et al., 2023
  2. Multi-Query（多查询检索）         — LangChain, 2023
  3. RAG-Fusion + RRF（查询融合）      — Raudaschl, 2023
  4. Contextual Retrieval（上下文检索） — Anthropic, 2024
  5. Graph-Enhanced RAG（图谱增强）     — Microsoft GraphRAG, 2024

使用方式：
    from services.advanced_retrieval_service import retrieval_service
    results = retrieval_service.hyde_search(user_id, "梯度下降原理")
    results = retrieval_service.rag_fusion_search(user_id, "梯度下降原理")
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from core.logger import info, error, warning, debug


class AdvancedRetrievalService:
    """高级检索服务（懒加载，首次调用时初始化依赖）"""

    def __init__(self):
        self._embedding_service = None
        self._qa_service = None
        self._rag_kb = None
        self._memory_service = None

    # ── 懒加载 ──────────────────────────────

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from data.embedding_service import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    @property
    def qa_service(self):
        if self._qa_service is None:
            from services.qa_service import qa_service
            self._qa_service = qa_service
        return self._qa_service

    @property
    def rag_kb(self):
        if self._rag_kb is None:
            from data.rag_knowledge_base import rag_kb
            self._rag_kb = rag_kb
        return self._rag_kb

    @property
    def memory_service(self):
        if self._memory_service is None:
            from services.memory_service import memory_service
            self._memory_service = memory_service
        return self._memory_service

    # ══════════════════════════════════════════
    # 1. HyDE — 假设性文档嵌入
    # ══════════════════════════════════════════

    def hyde_search(
        self,
        query: str,
        subject: str = None,
        limit: int = 5,
        model: str = "simple",
    ) -> List[Dict]:
        """
        HyDE 检索：LLM 生成假设答案 → 向量化 → 检索

        流程：
          query → LLM生成假设文档 → embedding → FAISS检索

        参数：
          query: 用户查询
          subject: 学科过滤
          limit: 返回数量
          model: LLM 模型级别 (simple/standard/advanced)

        返回：
          按相似度排序的文档列表
        """
        try:
            hypothetical_doc = self._generate_hypothetical_document(query, subject, model)
            if not hypothetical_doc:
                warning("HyDE: 假设文档生成失败，降级为普通检索")
                return self._fallback_vector_search(query, limit)

            doc_embedding = self.embedding_service.get_embedding(hypothetical_doc)
            if not doc_embedding:
                warning("HyDE: 假设文档向量化失败，降级为普通检索")
                return self._fallback_vector_search(query, limit)

            results = self.rag_kb.search_documents_by_vector(doc_embedding, limit=limit)
            for r in results:
                r['retrieval_method'] = 'hyde'
            return results

        except Exception as e:
            error(f"HyDE 检索失败: {e}")
            return self._fallback_vector_search(query, limit)

    def _generate_hypothetical_document(
        self, query: str, subject: str = None, model: str = "simple"
    ) -> Optional[str]:
        """用 LLM 生成假设性答案文档"""
        subject_hint = f"（学科：{subject}）" if subject else ""
        prompt = (
            f"请针对以下问题{subject_hint}，写一段详细的教学内容作为参考答案。"
            f"要求：200-400字，包含核心概念解释、关键公式或原理、示例说明。\n\n"
            f"问题：{query}"
        )
        try:
            if model == "advanced":
                return self.qa_service.call_advanced(prompt, max_tokens=600)
            elif model == "standard":
                return self.qa_service.call_standard(prompt, max_tokens=600)
            else:
                return self.qa_service.call_simple(prompt, max_tokens=600)
        except Exception as e:
            error(f"HyDE LLM 调用失败: {e}")
            return None

    # ══════════════════════════════════════════
    # 2. Multi-Query — 多查询检索
    # ══════════════════════════════════════════

    def multi_query_search(
        self,
        query: str,
        subject: str = None,
        limit: int = 5,
        num_variants: int = 3,
    ) -> List[Dict]:
        """
        多查询检索：LLM 生成多个查询变体 → 分别检索 → 合并去重

        流程：
          query → LLM生成N个变体 → 每个变体检索 → 去重合并

        参数：
          query: 原始查询
          subject: 学科过滤
          limit: 最终返回数量
          num_variants: 查询变体数量 (2-5)
        """
        try:
            variants = self._generate_query_variants(query, num_variants)
            all_queries = [query] + variants

            seen_ids = set()
            all_results = []
            for q in all_queries:
                q_embedding = self.embedding_service.get_embedding(q)
                if q_embedding:
                    hits = self.rag_kb.search_documents_by_vector(q_embedding, limit=limit)
                    for h in hits:
                        doc_id = h.get('id')
                        if doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            h['matched_query'] = q
                            all_results.append(h)

            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            for r in all_results[:limit]:
                r['retrieval_method'] = 'multi_query'
            return all_results[:limit]

        except Exception as e:
            error(f"Multi-Query 检索失败: {e}")
            return self._fallback_vector_search(query, limit)

    def _generate_query_variants(self, query: str, num_variants: int = 3) -> List[str]:
        """用 LLM 生成语义等价的查询变体"""
        prompt = (
            f"请将以下查询改写为 {num_variants} 个不同的表述方式，保持语义一致但措辞不同。\n"
            f"每个变体单独一行，不要编号，不要其他说明。\n\n"
            f"原始查询：{query}"
        )
        try:
            response = self.qa_service.call_simple(prompt, max_tokens=300)
            variants = [line.strip() for line in response.strip().split('\n') if line.strip()]
            return variants[:num_variants]
        except Exception as e:
            error(f"生成查询变体失败: {e}")
            return []

    # ══════════════════════════════════════════
    # 3. RAG-Fusion + RRF — 查询融合
    # ══════════════════════════════════════════

    def rag_fusion_search(
        self,
        query: str,
        subject: str = None,
        limit: int = 5,
        num_variants: int = 4,
        rrf_k: int = 60,
    ) -> List[Dict]:
        """
        RAG-Fusion：多查询 + Reciprocal Rank Fusion 排序

        流程：
          query → LLM生成N个变体 → 每个变体检索 → RRF融合排序

        RRF 公式：
          score(d) = Σ 1/(k + rank_i(d))
          其中 k=60 为平滑常数，rank_i(d) 为文档d在第i个查询结果中的排名

        参数：
          query: 原始查询
          subject: 学科过滤
          limit: 最终返回数量
          num_variants: 查询变体数量
          rrf_k: RRF 平滑常数 (默认60)
        """
        try:
            variants = self._generate_query_variants(query, num_variants)
            all_queries = [query] + variants

            ranked_lists = []
            for q in all_queries:
                q_embedding = self.embedding_service.get_embedding(q)
                if q_embedding:
                    hits = self.rag_kb.search_documents_by_vector(q_embedding, limit=limit * 3)
                    ranked_lists.append(hits)

            if not ranked_lists:
                return self._fallback_vector_search(query, limit)

            rrf_scores = {}
            doc_data_map = {}
            for ranked in ranked_lists:
                for rank, doc in enumerate(ranked):
                    doc_id = doc.get('id')
                    if doc_id is None:
                        continue
                    rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
                    doc_data_map[doc_id] = doc

            sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
            results = []
            for doc_id in sorted_ids[:limit]:
                doc = doc_data_map[doc_id]
                doc['rrf_score'] = rrf_scores[doc_id]
                doc['retrieval_method'] = 'rag_fusion'
                results.append(doc)

            return results

        except Exception as e:
            error(f"RAG-Fusion 检索失败: {e}")
            return self._fallback_vector_search(query, limit)

    # ══════════════════════════════════════════
    # 4. Contextual Retrieval — 上下文检索
    # ══════════════════════════════════════════

    def contextual_search(
        self,
        query: str,
        subject: str = None,
        limit: int = 5,
    ) -> List[Dict]:
        """
        上下文检索：先粗粒度召回，再用 LLM 对候选文档做上下文相关性评分

        流程：
          query → 向量粗召回(top 20) → LLM上下文评分 → 精排返回

        参考：Anthropic Contextual Retrieval (2024)
        """
        try:
            query_embedding = self.embedding_service.get_embedding(query)
            if not query_embedding:
                return self._fallback_vector_search(query, limit)

            candidates = self.rag_kb.search_documents_by_vector(query_embedding, limit=20)
            if not candidates:
                return []

            if len(candidates) <= limit:
                for r in candidates:
                    r['retrieval_method'] = 'contextual'
                return candidates

            reranked = self._contextual_rerank(query, candidates, subject)
            return reranked[:limit]

        except Exception as e:
            error(f"Contextual 检索失败: {e}")
            return self._fallback_vector_search(query, limit)

    def _contextual_rerank(
        self, query: str, candidates: List[Dict], subject: str = None
    ) -> List[Dict]:
        """用 LLM 对候选文档做上下文相关性评分"""
        doc_summaries = []
        for i, doc in enumerate(candidates):
            title = doc.get('title', '未知')
            summary = ''
            doc_data = doc.get('document_data', {})
            if isinstance(doc_data, dict):
                summary = doc_data.get('analysis', {}).get('summary', '')[:200]
            content_preview = doc.get('content_text', '')[:300]
            doc_summaries.append(
                f"[{i}] 标题：{title}\n摘要：{summary}\n内容：{content_preview}"
            )

        subject_hint = f"（学科：{subject}）" if subject else ""
        docs_text = '\n---\n'.join(doc_summaries)
        prompt = (
            f"你是一个教育文档相关性评估器。请对以下文档与查询的相关性进行评分。\n\n"
            f"查询{subject_hint}：{query}\n\n"
            f"候选文档：\n{docs_text}\n\n"
            f"请输出 JSON 数组，每个元素包含 index(文档编号) 和 score(0-10的相关性评分)，"
            f"按相关性从高到低排序。只输出 JSON，不要其他文字。\n"
            f"示例：[{{\"index\": 0, \"score\": 9}}, {{\"index\": 2, \"score\": 7}}]"
        )

        try:
            response = self.qa_service.call_simple(prompt, max_tokens=500)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                for r in candidates:
                    r['retrieval_method'] = 'contextual'
                return candidates

            scores = json.loads(json_match.group())
            scored_map = {item['index']: item['score'] for item in scores if 'index' in item}

            for i, doc in enumerate(candidates):
                ctx_score = scored_map.get(i, 0)
                vec_score = doc.get('similarity', 0)
                doc['contextual_score'] = ctx_score
                doc['combined_score'] = 0.4 * vec_score + 0.6 * (ctx_score / 10.0)
                doc['retrieval_method'] = 'contextual'

            candidates.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            return candidates

        except Exception as e:
            warning(f"上下文评分失败，返回原始排序: {e}")
            for r in candidates:
                r['retrieval_method'] = 'contextual'
            return candidates

    # ══════════════════════════════════════════
    # 5. Graph-Enhanced RAG — 图谱增强检索
    # ══════════════════════════════════════════

    def graph_enhanced_search(
        self,
        user_id: int,
        query: str,
        subject: str = None,
        limit: int = 5,
        graph_depth: int = 2,
    ) -> List[Dict]:
        """
        图谱增强检索：实体识别 → 图谱遍历 → 查询扩展 → 融合检索

        流程：
          query → LLM提取实体 → 图谱1-2跳遍历 → 扩展查询
          → 向量检索 + 图谱上下文 → 融合排序

        参考：Microsoft GraphRAG (2024) 简化版
        """
        try:
            entities = self._extract_entities(query)
            graph_context = self._traverse_graph(user_id, entities, graph_depth)
            expanded_query = self._expand_query_with_graph(query, graph_context)

            expanded_embedding = self.embedding_service.get_embedding(expanded_query)
            if expanded_embedding:
                results = self.rag_kb.search_documents_by_vector(expanded_embedding, limit=limit * 2)
            else:
                results = self._fallback_vector_search(query, limit * 2)

            if subject:
                results = [r for r in results if r.get('subject') == subject] + \
                          [r for r in results if r.get('subject') != subject]

            for r in results[:limit]:
                r['retrieval_method'] = 'graph_enhanced'
                r['graph_entities'] = entities
                r['graph_relations'] = graph_context.get('relations', [])[:5]

            return results[:limit]

        except Exception as e:
            error(f"Graph-Enhanced 检索失败: {e}")
            return self._fallback_vector_search(query, limit)

    def _extract_entities(self, query: str) -> List[str]:
        """用 LLM 从查询中提取教育领域实体"""
        prompt = (
            f"从以下教育相关查询中提取核心知识实体（概念、方法、算法、定理等）。\n"
            f"输出 JSON 数组，只包含实体名称，不要其他文字。\n\n"
            f"查询：{query}\n\n"
            f"示例：[\"梯度下降\", \"损失函数\", \"学习率\"]"
        )
        try:
            response = self.qa_service.call_simple(prompt, max_tokens=200)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
            return [query]
        except Exception as e:
            error(f"实体提取失败: {e}")
            return [query]

    def _traverse_graph(
        self, user_id: int, entities: List[str], depth: int = 2
    ) -> Dict:
        """在知识图谱中遍历关联实体"""
        graph_data = {'entities': [], 'relations': [], 'related_concepts': []}
        try:
            with self.memory_service as ms:
                for entity_name in entities[:3]:
                    found = ms.search_entities(user_id, entity_name, limit=1)
                    if not found:
                        continue

                    center_id = found[0]['id']
                    graph = ms.get_entity_graph(user_id, center_id, depth=depth)

                    for node in graph.get('nodes', []):
                        graph_data['entities'].append({
                            'name': node.get('entity_name', ''),
                            'type': node.get('entity_type', ''),
                        })
                        if node.get('entity_name') != entity_name:
                            graph_data['related_concepts'].append(node['entity_name'])

                    for edge in graph.get('edges', []):
                        graph_data['relations'].append({
                            'source': edge.get('source'),
                            'target': edge.get('target'),
                            'label': edge.get('label', ''),
                        })

        except Exception as e:
            warning(f"图谱遍历失败: {e}")

        graph_data['related_concepts'] = list(set(graph_data['related_concepts']))[:10]
        return graph_data

    def _expand_query_with_graph(self, query: str, graph_context: Dict) -> str:
        """用图谱上下文扩展查询"""
        related = graph_context.get('related_concepts', [])
        if not related:
            return query
        expansion = ' '.join(related[:5])
        return f"{query} {expansion}"

    # ══════════════════════════════════════════
    # 6. Contextual Chunking（预处理）
    # ══════════════════════════════════════════

    def add_contextual_document(
        self,
        title: str,
        subject: str,
        content_text: str,
        file_path: str = '',
        file_type: str = 'txt',
        knowledge_points: List[str] = None,
        uploaded_by: int = None,
    ) -> Optional[int]:
        """
        上下文分块入库：为每个段落添加上下文前缀后再嵌入

        参考：Anthropic Contextual Retrieval (2024)

        流程：
          文档 → 分段 → LLM为每段生成上下文前缀 → 拼接 → 向量化 → 入库
        """
        try:
            paragraphs = self._split_paragraphs(content_text)
            if not paragraphs:
                return None

            contextualized = self._add_context_to_paragraphs(title, subject, paragraphs)
            full_text = '\n\n'.join(contextualized)

            summary_prompt = (
                f"请为以下文档生成一段100字以内的摘要：\n\n"
                f"标题：{title}\n学科：{subject}\n内容：{content_text[:2000]}"
            )
            ai_summary = self.qa_service.call_simple(summary_prompt, max_tokens=200)

            embedding = self.embedding_service.get_embedding(full_text[:4000])

            doc_id = self.rag_kb.add_document(
                title=title,
                subject=subject,
                file_path=file_path,
                file_type=file_type,
                content_text=full_text,
                knowledge_points=knowledge_points,
                ai_summary=ai_summary,
                uploaded_by=uploaded_by,
                embedding=embedding,
            )

            info(f"上下文分块入库完成: {title}, doc_id={doc_id}")
            return doc_id

        except Exception as e:
            error(f"上下文分块入库失败: {e}")
            return None

    def _add_context_to_paragraphs(
        self, title: str, subject: str, paragraphs: List[str]
    ) -> List[str]:
        """为每个段落生成上下文前缀"""
        batch_size = 5
        contextualized = []
        for i in range(0, len(paragraphs), batch_size):
            batch = paragraphs[i:i + batch_size]
            numbered = '\n'.join(f"[{j}] {p}" for j, p in enumerate(batch))
            prompt = (
                f"文档标题：{title}，学科：{subject}\n\n"
                f"以下是文档的几个段落，请为每个段落生成一句话的上下文前缀，"
                f"说明该段落在文档中的位置和讨论的主题。\n\n"
                f"段落：\n{numbered}\n\n"
                f"输出格式（每行一个，对应段落编号）：\n"
                f"[0] <前缀> | <原始段落>\n[1] <前缀> | <原始段落>\n..."
            )
            try:
                response = self.qa_service.call_simple(prompt, max_tokens=800)
                for line in response.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            prefix = re.sub(r'^\[\d+\]\s*', '', parts[0]).strip()
                            content = parts[1].strip()
                            contextualized.append(f"[{prefix}] {content}")
                        else:
                            contextualized.append(parts[1].strip())
                    else:
                        clean = re.sub(r'^\[\d+\]\s*', '', line).strip()
                        if clean:
                            contextualized.append(clean)
            except Exception as e:
                warning(f"上下文生成失败，使用原始段落: {e}")
                contextualized.extend(batch)

        return contextualized if contextualized else paragraphs

    def _split_paragraphs(self, text: str, max_length: int = 500) -> List[str]:
        """将文本分割为段落"""
        if not text:
            return []
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        result = []
        for para in paragraphs:
            if len(para) <= max_length:
                result.append(para)
            else:
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
        return result[:100]

    # ══════════════════════════════════════════
    # 7. 统一入口 — 智能路由
    # ══════════════════════════════════════════

    def smart_search(
        self,
        user_id: int,
        query: str,
        subject: str = None,
        limit: int = 5,
        strategy: str = "auto",
    ) -> List[Dict]:
        """
        智能检索入口：根据策略选择最佳检索方法

        参数：
          strategy:
            - "auto"         — 自动选择（默认）
            - "hyde"         — 假设性文档嵌入
            - "multi_query"  — 多查询检索
            - "rag_fusion"   — RAG-Fusion（推荐）
            - "contextual"   — 上下文精排
            - "graph"        — 图谱增强
            - "hybrid"       — HyDE + RAG-Fusion 组合
            - "ensemble"     — 全方法集成（取并集）
        """
        strategy = strategy.lower()

        if strategy == "hyde":
            return self.hyde_search(query, subject, limit)
        elif strategy == "multi_query":
            return self.multi_query_search(query, subject, limit)
        elif strategy == "rag_fusion":
            return self.rag_fusion_search(query, subject, limit)
        elif strategy == "contextual":
            return self.contextual_search(query, subject, limit)
        elif strategy == "graph":
            return self.graph_enhanced_search(user_id, query, subject, limit)
        elif strategy == "hybrid":
            return self._hybrid_search(user_id, query, subject, limit)
        elif strategy == "ensemble":
            return self._ensemble_search(user_id, query, subject, limit)
        else:
            return self._auto_search(user_id, query, subject, limit)

    def _auto_search(
        self, user_id: int, query: str, subject: str, limit: int
    ) -> List[Dict]:
        """自动策略：短查询用 HyDE，长查询用 RAG-Fusion"""
        if len(query) < 15:
            return self.hyde_search(query, subject, limit)
        else:
            return self.rag_fusion_search(query, subject, limit)

    def _hybrid_search(
        self, user_id: int, query: str, subject: str, limit: int
    ) -> List[Dict]:
        """HyDE + RAG-Fusion 组合"""
        hyde_results = self.hyde_search(query, subject, limit=limit * 2)
        fusion_results = self.rag_fusion_search(query, subject, limit=limit * 2)

        rrf_k = 60
        scores = {}
        data_map = {}

        for rank, doc in enumerate(hyde_results):
            doc_id = doc.get('id')
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            data_map[doc_id] = doc

        for rank, doc in enumerate(fusion_results):
            doc_id = doc.get('id')
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            data_map[doc_id] = doc

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for doc_id in sorted_ids[:limit]:
            doc = data_map[doc_id]
            doc['retrieval_method'] = 'hybrid'
            doc['hybrid_score'] = scores[doc_id]
            results.append(doc)
        return results

    def _ensemble_search(
        self, user_id: int, query: str, subject: str, limit: int
    ) -> List[Dict]:
        """全方法集成：5种方法取并集，RRF 融合"""
        rrf_k = 60
        scores = {}
        data_map = {}

        methods = [
            ('hyde', lambda: self.hyde_search(query, subject, limit * 2)),
            ('multi_query', lambda: self.multi_query_search(query, subject, limit * 2)),
            ('rag_fusion', lambda: self.rag_fusion_search(query, subject, limit * 2)),
            ('contextual', lambda: self.contextual_search(query, subject, limit * 2)),
            ('graph', lambda: self.graph_enhanced_search(user_id, query, subject, limit * 2)),
        ]

        for method_name, method_fn in methods:
            try:
                results = method_fn()
                for rank, doc in enumerate(results):
                    doc_id = doc.get('id')
                    scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
                    data_map[doc_id] = doc
            except Exception as e:
                warning(f"Ensemble 中 {method_name} 失败: {e}")

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for doc_id in sorted_ids[:limit]:
            doc = data_map[doc_id]
            doc['retrieval_method'] = 'ensemble'
            doc['ensemble_score'] = scores[doc_id]
            results.append(doc)
        return results

    # ── 回退方法 ──────────────────────────────

    def _fallback_vector_search(self, query: str, limit: int) -> List[Dict]:
        """降级：普通向量检索"""
        try:
            embedding = self.embedding_service.get_embedding(query)
            if embedding:
                return self.rag_kb.search_documents_by_vector(embedding, limit=limit)
        except Exception as e:
            error(f"降级向量检索也失败: {e}")
        return []

    def lightweight_rerank(
        self, query: str, candidates: List[Dict], limit: int = 5
    ) -> List[Dict]:
        """
        轻量级重排序：基于词项覆盖度 + 向量分数融合
        不依赖 LLM，适合高并发场景

        融合公式：
          final_score = 0.6 * vector_score + 0.4 * term_overlap
        """
        if not candidates:
            return []

        query_terms = set(query.lower().split())
        if not query_terms:
            return candidates[:limit]

        for doc in candidates:
            title = doc.get('title', '').lower()
            summary = ''
            doc_data = doc.get('document_data', {})
            if isinstance(doc_data, dict):
                summary = doc_data.get('analysis', {}).get('summary', '').lower()
            content = doc.get('content_text', '').lower()[:500]

            doc_text = f"{title} {summary} {content}"
            doc_terms = set(doc_text.split())
            overlap = len(query_terms & doc_terms) / len(query_terms)

            vec_score = doc.get('similarity', 0)
            doc['term_overlap'] = overlap
            doc['rerank_score'] = 0.6 * vec_score + 0.4 * overlap
            doc['retrieval_method'] = doc.get('retrieval_method', 'vector') + '+rerank'

        candidates.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        return candidates[:limit]


# 全局单例
retrieval_service = AdvancedRetrievalService()
