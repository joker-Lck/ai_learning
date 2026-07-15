"""多跳推理检索：逻辑图构建 + 多跳探索 + 证据链验证"""

import json
import re
import sqlite3

from core.logger import error, info, warning


class MultiHopRetriever:
    """多跳推理检索层：支持 2-5 跳的深度推理检索"""

    MAX_HOPS = 5
    DEFAULT_HOPS = 3
    CONFIDENCE_THRESHOLD = 0.4

    def __init__(self):
        self._embedding_service = None
        self._rag_kb = None
        self._qa_service = None

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from data.embedding_service import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    @property
    def rag_kb(self):
        if self._rag_kb is None:
            from data.rag_knowledge_base import rag_kb
            self._rag_kb = rag_kb
        return self._rag_kb

    @property
    def qa_service(self):
        if self._qa_service is None:
            from services.qa_service import qa_service
            self._qa_service = qa_service
        return self._qa_service

    def retrieve(self, query: str, user_id: int = 0, max_hops: int = None,
                 limit: int = 5) -> dict:
        """
        主入口：多跳推理检索

        Returns:
            {
                "answer": str,
                "evidence_chain": List[Dict],
                "confidence": float,
                "hops_used": int,
                "logic_graph": Dict
            }
        """
        if max_hops is None:
            max_hops = self.DEFAULT_HOPS
        max_hops = min(max_hops, self.MAX_HOPS)

        try:
            # Step 1: 初始种子检索
            seed_docs = self._seed_retrieval(query, limit=limit)
            if not seed_docs:
                return self._empty_result("未找到相关文档")

            # Step 2: 构建逻辑图
            logic_graph = self._build_logic_graph(seed_docs)

            # Step 3: 多跳探索
            evidence_chain = self._multi_hop_explore(query, seed_docs, max_hops)

            # Step 4: 验证证据链
            chain_result = self._verify_chain(evidence_chain)

            # Step 5: 综合答案
            answer = self._synthesize_answer(query, evidence_chain)

            hops_used = max((e.get("hop", 0) for e in evidence_chain), default=0)

            info(f"[MultiHop] 查询='{query[:30]}' 跳数={hops_used} "
                 f"证据链={len(evidence_chain)} 置信度={chain_result['confidence']:.3f}")

            return {
                "answer": answer,
                "evidence_chain": evidence_chain,
                "confidence": chain_result["confidence"],
                "hops_used": hops_used,
                "logic_graph": logic_graph,
            }

        except Exception as e:
            error(f"[MultiHop] 多跳检索失败: {e}")
            return self._empty_result(str(e))

    def _seed_retrieval(self, query: str, limit: int = 5) -> list[dict]:
        """初始种子检索：混合检索获取起点文档"""
        try:
            embedding = self.embedding_service.get_embedding(query)
            results = self.rag_kb.hybrid_search(
                query=query,
                query_embedding=embedding,
                limit=limit
            )
            return results if results else []
        except Exception as e:
            warning(f"[MultiHop] 种子检索失败: {e}")
            return []

    def _build_logic_graph(self, seed_docs: list[dict]) -> dict:
        """从种子文档构建实体-关系逻辑图"""
        nodes = []
        edges = []

        for i, doc in enumerate(seed_docs):
            doc_id = doc.get("id", i)
            title = doc.get("title", f"doc_{doc_id}")
            nodes.append({
                "id": f"doc_{doc_id}",
                "label": title[:30],
                "type": "document",
            })

            # 提取实体并存储到图
            content = doc.get("content", "") or doc.get("content_text", "")
            if content:
                entities = self._extract_entities(content)
                for ent in entities[:5]:
                    ent_id = f"ent_{ent['name']}"
                    if not any(n["id"] == ent_id for n in nodes):
                        nodes.append({
                            "id": ent_id,
                            "label": ent["name"],
                            "type": "entity",
                        })
                    edges.append({
                        "source": f"doc_{doc_id}",
                        "target": ent_id,
                        "relation": "contains",
                    })

        return {"nodes": nodes, "edges": edges}

    def _extract_entities(self, text: str) -> list[dict]:
        """从文本中提取实体（基于规则 + LLM）"""
        entities = []

        # 规则提取：中文名词短语
        patterns = [
            r'[\u4e00-\u9fff]{2,6}(?:算法|方法|技术|原理|概念|定理|公式|模型|框架|协议)',
            r'[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text[:2000])
            for m in matches[:10]:
                if len(m) >= 2:
                    entities.append({"name": m, "type": "concept"})

        # 去重
        seen = set()
        unique = []
        for e in entities:
            if e["name"] not in seen:
                seen.add(e["name"])
                unique.append(e)
        return unique[:15]

    def _multi_hop_explore(self, query: str, seed_docs: list[dict],
                           max_hops: int) -> list[dict]:
        """多跳探索：从种子段落沿逻辑边逐步扩展"""
        evidence_chain = []
        visited_ids = set()

        # 添加种子文档为第0跳
        for doc in seed_docs[:3]:
            doc_id = doc.get("id", 0)
            evidence_chain.append({
                "hop": 0,
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "content": (doc.get("content", "") or doc.get("content_text", ""))[:500],
                "score": doc.get("score", 0.5),
                "relation": "seed",
            })
            visited_ids.add(doc_id)

        # 逐跳扩展
        current_query = query
        for hop in range(1, max_hops + 1):
            next_docs = self._hop_retrieve(current_query, visited_ids, limit=3)
            if not next_docs:
                break

            for doc in next_docs:
                doc_id = doc.get("id", 0)
                if doc_id in visited_ids:
                    continue
                visited_ids.add(doc_id)

                content = doc.get("content", "") or doc.get("content_text", "")
                relation = self._infer_relation(
                    evidence_chain[-1]["content"] if evidence_chain else "",
                    content[:500]
                )

                evidence_chain.append({
                    "hop": hop,
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "content": content[:500],
                    "score": doc.get("score", 0.4),
                    "relation": relation,
                })

            # 更新查询：基于当前证据链生成下一轮查询
            current_query = self._derive_next_query(query, evidence_chain)

        return evidence_chain

    def _hop_retrieve(self, query: str, visited_ids: set, limit: int = 3) -> list[dict]:
        """单跳检索：排除已访问文档"""
        try:
            embedding = self.embedding_service.get_embedding(query)
            results = self.rag_kb.hybrid_search(
                query=query,
                query_embedding=embedding,
                limit=limit + len(visited_ids)
            )
            # 过滤已访问
            return [r for r in (results or []) if r.get("id") not in visited_ids][:limit]
        except Exception:
            return []

    def _infer_relation(self, source_text: str, target_text: str) -> str:
        """推断两段文本的关系类型"""
        if not source_text or not target_text:
            return "related"

        # 简单规则推断
        source_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', source_text[:300]))
        target_words = set(re.findall(r'[\u4e00-\u9fff]{2,}', target_text[:300]))
        overlap = source_words & target_words

        if len(overlap) > 5:
            return "elaborates"
        elif len(overlap) > 2:
            return "related"
        else:
            return "extends"

    def _derive_next_query(self, original_query: str, chain: list[dict]) -> str:
        """基于证据链生成下一轮查询"""
        if not chain:
            return original_query

        last_evidence = chain[-1]
        content = last_evidence.get("content", "")[:300]

        prompt = f"""基于以下信息，生成一个进一步探索的查询（20-50字）。

原始问题：{original_query}
已找到信息：{content}

只输出查询文本，不要其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=100)
            if result and len(result) > 5 and not result.startswith("错误"):
                return result.strip()
        except Exception:
            pass

        # 降级：使用最后一段证据的关键词
        keywords = re.findall(r'[\u4e00-\u9fff]{3,}', content[:200])
        return " ".join(keywords[:5]) if keywords else original_query

    def _verify_chain(self, evidence_chain: list[dict]) -> dict:
        """验证证据链：逻辑连贯性 + 置信度计算 + 剪枝"""
        if not evidence_chain:
            return {"confidence": 0.0, "valid": False, "pruned": []}

        scores = [e.get("score", 0) for e in evidence_chain]
        hop_weights = {0: 1.0, 1: 0.9, 2: 0.8, 3: 0.7, 4: 0.6, 5: 0.5}

        weighted_scores = []
        for e in evidence_chain:
            hop = e.get("hop", 0)
            weight = hop_weights.get(hop, 0.5)
            weighted_scores.append(e.get("score", 0) * weight)

        confidence = sum(weighted_scores) / max(len(weighted_scores), 1)

        # 剪枝：移除低分证据
        pruned = []
        valid_chain = []
        for e in evidence_chain:
            if e.get("score", 0) >= self.CONFIDENCE_THRESHOLD:
                valid_chain.append(e)
            else:
                pruned.append(e)

        evidence_chain.clear()
        evidence_chain.extend(valid_chain)

        return {
            "confidence": min(confidence, 1.0),
            "valid": len(valid_chain) > 0,
            "pruned": pruned,
        }

    def _synthesize_answer(self, query: str, evidence_chain: list[dict]) -> str:
        """基于证据链综合生成答案"""
        if not evidence_chain:
            return "未找到足够信息来回答此问题。"

        evidence_text = ""
        for i, e in enumerate(evidence_chain[:8]):
            evidence_text += f"\n[证据{i+1}] (跳数:{e.get('hop',0)}, 关系:{e.get('relation','')})\n"
            evidence_text += f"标题: {e.get('title', '')}\n"
            evidence_text += f"内容: {e.get('content', '')[:300]}\n"

        prompt = f"""基于以下多跳检索的证据链，综合回答用户问题。
请引用具体证据编号，确保回答有据可查。

【用户问题】
{query}

【证据链】
{evidence_text}

请提供准确、有条理的回答，并标注引用来源。"""

        try:
            result = self.qa_service.call_standard(prompt, max_tokens=2000)
            if result and not result.startswith("错误"):
                return result
        except Exception as e:
            error(f"[MultiHop] 答案综合失败: {e}")

        # 降级：拼接证据
        return "\n\n".join(
            f"**{e.get('title', '文档')}**\n{e.get('content', '')[:200]}"
            for e in evidence_chain[:3]
        )

    def _empty_result(self, reason: str) -> dict:
        return {
            "answer": reason,
            "evidence_chain": [],
            "confidence": 0.0,
            "hops_used": 0,
            "logic_graph": {"nodes": [], "edges": []},
        }

    def store_entity_graph(self, doc_id: int, subject: str, content: str) -> bool:
        """将文档实体关系存入 knowledge_entity_graph 表"""
        try:
            entities = self._extract_entities(content)
            if not entities:
                return False

            from data.config import get_rag_db_path
            conn = sqlite3.connect(get_rag_db_path())
            cursor = conn.cursor()

            for ent in entities:
                related = [e["name"] for e in entities if e["name"] != ent["name"]][:10]
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_entity_graph
                    (doc_id, subject, entity_name, entity_type, related_entities)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, subject, ent["name"], ent.get("type", "concept"),
                      json.dumps(related, ensure_ascii=False)))

            conn.commit()
            conn.close()
            info(f"[MultiHop] 存储实体图: doc_id={doc_id} 实体数={len(entities)}")
            return True
        except Exception as e:
            error(f"[MultiHop] 存储实体图失败: {e}")
            return False


# 全局单例
multi_hop_retriever = MultiHopRetriever()
