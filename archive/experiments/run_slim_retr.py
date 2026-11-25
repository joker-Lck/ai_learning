# -*- coding: utf-8 -*-
"""T2.1: advanced_retrieval_service 内部去重 + rag_kb 分段函数走共享工具"""
import io
import os

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"

# ── 1. rag_knowledge_base._split_paragraphs 委托 text_utils ──
p = os.path.join(ROOT, "data", "rag_knowledge_base.py")
src = io.open(p, encoding="utf-8").read()
old = '''    def _split_paragraphs(self, text, max_length=500, max_count=100):
        """将文本分割为段落"""
        if not text:
            return []

        # 按换行符分割
        paragraphs = [p.strip() for p in text.split('\\n') if p.strip()]

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

        return result[:max_count]'''
new = '''    def _split_paragraphs(self, text, max_length=500, max_count=100):
        """将文本分割为段落（共享实现见 core.text_utils）"""
        from core.text_utils import split_paragraphs

        return split_paragraphs(text, max_length=max_length, max_count=max_count)'''
assert old in src, "rag_kb._split_paragraphs block not found"
src = src.replace(old, new)
io.open(p, "w", encoding="utf-8").write(src)
print("rag_knowledge_base.py: _split_paragraphs -> text_utils")

# ── 2. advanced_retrieval_service 内部去重 ──
p = os.path.join(ROOT, "services", "advanced_retrieval_service.py")
src = io.open(p, encoding="utf-8").read()

# 2a. _split_paragraphs 委托 text_utils
old = '''    def _split_paragraphs(self, text: str, max_length: int = 500) -> list[str]:
        """将文本分割为段落"""
        if not text:
            return []
        paragraphs = [p.strip() for p in text.split('\\n') if p.strip()]
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
        return result[:100]'''
new = '''    def _split_paragraphs(self, text: str, max_length: int = 500) -> list[str]:
        """将文本分割为段落（共享实现见 core.text_utils）"""
        from core.text_utils import split_paragraphs

        return split_paragraphs(text, max_length=max_length)'''
assert old in src, "advanced._split_paragraphs not found"
src = src.replace(old, new)

# 2b. 模块级 RRF 融合助手（插在类定义之前）
anchor = "class AdvancedRetrievalService"
assert anchor in src
helper = '''def _rrf_fuse(
    ranked_lists: list[list[dict]],
    rrf_k: int,
    limit: int,
    method: str,
    score_key: str = "rrf_score",
) -> list[dict]:
    """RRF 融合多路排名列表：score(d) = Σ 1/(k + rank_i(d))"""
    rrf_scores: dict = {}
    data_map: dict = {}
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked):
            doc_id = doc.get("id")
            if doc_id is None:
                continue
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            data_map[doc_id] = doc

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    results = []
    for doc_id in sorted_ids[:limit]:
        doc = data_map[doc_id]
        doc[score_key] = rrf_scores[doc_id]
        doc["retrieval_method"] = method
        results.append(doc)
    return results


'''
src = src.replace(anchor, helper + anchor, 1)

# 2c. rag_fusion_search 的内联 RRF → _rrf_fuse
old = '''            if not ranked_lists:
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

            return results'''
new = '''            if not ranked_lists:
                return self._fallback_vector_search(query, limit)

            return _rrf_fuse(ranked_lists, rrf_k, limit, 'rag_fusion')'''
assert old in src, "rag_fusion RRF block not found"
src = src.replace(old, new)

# 2d. _hybrid_advanced_search 的内联 RRF → _rrf_fuse
old = '''        rrf_k = 60
        scores = {}
        data_map = {}

        methods = [
            ('base_hybrid', lambda: self._base_hybrid_search(query, subject, limit * 2)),
            ('hyde', lambda: self.hyde_search(query, subject, limit * 2)),
            ('rag_fusion', lambda: self.rag_fusion_search(query, subject, limit * 2)),
        ]

        for method_name, method_fn in methods:
            try:
                results = method_fn()
                for rank, doc in enumerate(results):
                    doc_id = doc.get('id')
                    if doc_id is None:
                        continue
                    scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
                    data_map[doc_id] = doc
            except Exception as e:
                warning(f"Hybrid_Advl 中 {method_name} 失败: {e}")

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        results = []
        for doc_id in sorted_ids[:limit]:
            doc = data_map[doc_id]
            doc['retrieval_method'] = 'hybrid_advl'
            doc['hybrid_score'] = scores[doc_id]
            results.append(doc)
        return results'''
new = '''        rrf_k = 60
        ranked_lists = []
        methods = [
            ('base_hybrid', lambda: self._base_hybrid_search(query, subject, limit * 2)),
            ('hyde', lambda: self.hyde_search(query, subject, limit * 2)),
            ('rag_fusion', lambda: self.rag_fusion_search(query, subject, limit * 2)),
        ]

        for method_name, method_fn in methods:
            try:
                ranked_lists.append(method_fn())
            except Exception as e:
                warning(f"Hybrid_Advl 中 {method_name} 失败: {e}")

        return _rrf_fuse(ranked_lists, rrf_k, limit, 'hybrid_advl', score_key='hybrid_score')'''
assert old in src, "_hybrid_advanced_search block not found"
src = src.replace(old, new)

# 2e. _ensemble_search 的内联 RRF → _rrf_fuse
old = '''        rrf_k = 60
        scores = {}
        data_map = {}

        methods = [
            ('base_hybrid', lambda: self._base_hybrid_search(query, subject, limit * 2)),
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
                    if doc_id is None:
                        continue
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
        return results'''
new = '''        rrf_k = 60
        ranked_lists = []
        methods = [
            ('base_hybrid', lambda: self._base_hybrid_search(query, subject, limit * 2)),
            ('hyde', lambda: self.hyde_search(query, subject, limit * 2)),
            ('multi_query', lambda: self.multi_query_search(query, subject, limit * 2)),
            ('rag_fusion', lambda: self.rag_fusion_search(query, subject, limit * 2)),
            ('contextual', lambda: self.contextual_search(query, subject, limit * 2)),
            ('graph', lambda: self.graph_enhanced_search(user_id, query, subject, limit * 2)),
        ]

        for method_name, method_fn in methods:
            try:
                ranked_lists.append(method_fn())
            except Exception as e:
                warning(f"Ensemble 中 {method_name} 失败: {e}")

        return _rrf_fuse(ranked_lists, rrf_k, limit, 'ensemble', score_key='ensemble_score')'''
assert old in src, "_ensemble_search block not found"
src = src.replace(old, new)

# 2f. rag_fusion 内层 embed+hybrid 样板 → _base_hybrid_search
old = '''            ranked_lists = []
            for q in all_queries:
                q_embedding = self.embedding_service.get_embedding(q)
                hits = self.rag_kb.hybrid_search(
                    query=q, query_embedding=q_embedding,
                    subject=subject, limit=limit * 3,
                )
                if hits:
                    ranked_lists.append(hits)'''
new = '''            ranked_lists = []
            for q in all_queries:
                hits = self._base_hybrid_search(q, subject, limit * 3)
                if hits:
                    ranked_lists.append(hits)'''
assert old in src, "rag_fusion inner embed block not found"
src = src.replace(old, new)

# 2g. contextual_search 内层 embed+hybrid 样板 → _base_hybrid_search
old = '''        try:
            query_embedding = self.embedding_service.get_embedding(query)
            candidates = self.rag_kb.hybrid_search(
                query=query, query_embedding=query_embedding,
                subject=subject, limit=20,
            )
            if not candidates:
                return []'''
new = '''        try:
            candidates = self._base_hybrid_search(query, subject, 20)
            if not candidates:
                return []'''
assert old in src, "contextual inner embed block not found"
src = src.replace(old, new)

# 2h. graph_enhanced_search 内层 embed+hybrid 样板 → _base_hybrid_search
old = '''            expanded_embedding = self.embedding_service.get_embedding(expanded_query)
            results = self.rag_kb.hybrid_search(
                query=expanded_query, query_embedding=expanded_embedding,
                subject=subject, limit=limit * 2,
            )'''
new = '''            results = self._base_hybrid_search(expanded_query, subject, limit * 2)'''
assert old in src, "graph inner embed block not found"
src = src.replace(old, new)

io.open(p, "w", encoding="utf-8").write(src)
print("advanced_retrieval_service.py: RRF x3 fused, embed boilerplate x3 collapsed, split_paragraphs delegated")
