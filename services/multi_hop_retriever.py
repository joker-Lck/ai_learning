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

    def retrieve(self, query: str, user_id: int = 0, max_hops: int | None = None,
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

        [e.get("score", 0) for e in evidence_chain]
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

    def react_retrieve(self, query: str, user_id: int = 0,
                       max_steps: int = 3, limit: int = 5) -> dict:
        """
        ReAct 推理-检索交替检索

        流程：
        1. LLM 推理一步 → 判断需要什么信息
        2. 针对性检索
        3. 基于新信息继续推理
        4. 重复直到信息充分或达到步数上限

        适配：理科推导、多步骤答疑、需要逐步构建答案的场景
        """
        info(f"[ReAct] 开始推理-检索交替: query='{query[:50]}'")

        reasoning_steps = []
        evidence_chain = []
        visited_ids = set()
        current_context = ""

        for step in range(max_steps):
            # Step 1: 推理 — 基于当前信息，判断下一步需要什么
            reasoning = self._reasoning_step(query, current_context, step)
            if not reasoning:
                break

            reasoning_steps.append({
                "step": step,
                "thought": reasoning.get("thought", ""),
                "need_info": reasoning.get("need_info", ""),
                "is_sufficient": reasoning.get("is_sufficient", False),
            })

            # 如果推理认为信息已充分，停止
            if reasoning.get("is_sufficient"):
                info(f"[ReAct] Step {step}: 信息充分，停止检索")
                break

            # Step 2: 检索 — 针对推理出的需求检索
            search_query = reasoning.get("need_info", query)
            docs = self._hop_retrieve(search_query, visited_ids, limit=3)

            if not docs:
                # 尝试用原始查询
                docs = self._hop_retrieve(query, visited_ids, limit=3)

            if not docs:
                break

            # Step 3: 整合新证据
            for doc in docs:
                doc_id = doc.get("id", 0)
                if doc_id in visited_ids:
                    continue
                visited_ids.add(doc_id)
                content = doc.get("content", "") or doc.get("content_text", "")

                evidence_chain.append({
                    "hop": step,
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "content": content[:500],
                    "score": doc.get("score", 0.4),
                    "relation": f"react_step_{step}",
                })
                current_context += f"\n[证据] {doc.get('title', '')}: {content[:300]}"

            # 构建逻辑图
            if step == 0:
                logic_graph = self._build_logic_graph(docs)
            else:
                # 扩展逻辑图
                new_graph = self._build_logic_graph(docs)
                logic_graph["nodes"].extend(new_graph["nodes"])
                logic_graph["edges"].extend(new_graph["edges"])

        # 综合答案
        answer = self._synthesize_answer(query, evidence_chain)

        # 验证
        chain_result = self._verify_chain(evidence_chain)
        hops_used = max((e.get("hop", 0) for e in evidence_chain), default=0)

        info(f"[ReAct] 完成: steps={len(reasoning_steps)} evidence={len(evidence_chain)} "
             f"confidence={chain_result['confidence']:.3f}")

        return {
            "answer": answer,
            "evidence_chain": evidence_chain,
            "confidence": chain_result["confidence"],
            "hops_used": hops_used,
            "reasoning_steps": reasoning_steps,
            "logic_graph": logic_graph if evidence_chain else {"nodes": [], "edges": []},
        }

    def _reasoning_step(self, query: str, current_context: str, step: int) -> dict | None:
        """
        ReAct 推理步骤：LLM 分析当前信息，判断下一步需要什么

        返回:
        {
            "thought": str,       # 推理过程
            "need_info": str,     # 需要检索的信息
            "is_sufficient": bool # 当前信息是否已充分
        }
        """
        prompt = f"""你是一个推理助手。根据用户问题和已知信息，判断下一步需要什么。

【用户问题】
{query}

【已知信息】
{current_context if current_context else "暂无"}

【当前步骤】第 {step + 1} 步

请用 JSON 格式回答：
{{
  "thought": "你的推理过程（简短）",
  "need_info": "下一步需要检索的信息（用于搜索的关键词/问题）",
  "is_sufficient": true/false（当前信息是否已足够回答问题）
}}

只输出 JSON，不要其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=200)
            if result and not result.startswith("错误"):
                import json
                # 提取 JSON
                match = re.search(r'\{[^{}]*\}', result)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            debug(f"[ReAct] 推理步骤失败: {e}")

        # 降级：使用规则推理
        if step == 0:
            return {
                "thought": "初始检索",
                "need_info": query,
                "is_sufficient": False,
            }
        return None

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

    def build_knowledge_graph(self, doc_id: int, subject: str, content: str) -> dict:
        """
        知识图谱自动构建流水线 — LLM-based NER + RE

        1. 规则提取实体（快速）
        2. LLM 补充实体 + 抽取关系（精准）
        3. 合并去重
        4. 存入 knowledge_entity_graph 表

        返回:
        {
            "entities": [...],
            "relations": [...],
            "stored": bool
        }
        """
        info(f"[KG] 开始构建知识图谱: doc_id={doc_id}")

        # 1. 规则提取
        rule_entities = self._extract_entities(content)

        # 2. LLM 提取实体 + 关系
        llm_result = self._llm_extract_entities_relations(content[:4000])
        llm_entities = llm_result.get("entities", [])
        relations = llm_result.get("relations", [])

        # 3. 合并去重
        all_entities = self._merge_entities(rule_entities, llm_entities)

        # 4. 存储
        stored = self._store_graph_data(doc_id, subject, all_entities, relations)

        result = {
            "entities": all_entities,
            "relations": relations,
            "stored": stored,
            "entity_count": len(all_entities),
            "relation_count": len(relations),
        }

        info(f"[KG] 知识图谱构建完成: entities={len(all_entities)} relations={len(relations)}")
        return result

    def _llm_extract_entities_relations(self, text: str) -> dict:
        """LLM 提取实体和关系"""
        prompt = f"""从以下文本中提取实体和它们之间的关系。

【文本】
{text}

请用 JSON 格式输出：
{{
  "entities": [
    {{"name": "实体名", "type": "concept|person|algorithm|formula|method"}}
  ],
  "relations": [
    {{"source": "实体A", "target": "实体B", "relation": "关系类型"}}
  ]
}}

关系类型包括：is_a, part_of, uses, depends_on, improves, related_to, causes, equals
只输出 JSON，不要其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=1500)
            if result and not result.startswith("错误"):
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    return {
                        "entities": data.get("entities", []),
                        "relations": data.get("relations", []),
                    }
        except Exception as e:
            debug(f"[KG] LLM 实体关系提取失败: {e}")

        return {"entities": [], "relations": []}

    def _merge_entities(self, rule_entities: list, llm_entities: list) -> list:
        """合并去重规则提取和 LLM 提取的实体"""
        seen = set()
        merged = []

        for ent in rule_entities:
            name = ent.get("name", "")
            if name and name not in seen:
                seen.add(name)
                merged.append({"name": name, "type": ent.get("type", "concept"), "source": "rule"})

        for ent in llm_entities:
            name = ent.get("name", "")
            if name and name not in seen:
                seen.add(name)
                merged.append({"name": name, "type": ent.get("type", "concept"), "source": "llm"})

        return merged

    def _store_graph_data(self, doc_id: int, subject: str,
                          entities: list, relations: list) -> bool:
        """存储实体和关系到数据库"""
        try:
            from data.config import get_rag_db_path
            conn = sqlite3.connect(get_rag_db_path())
            cursor = conn.cursor()

            # 存储实体
            for ent in entities:
                related_names = []
                for rel in relations:
                    if rel.get("source") == ent["name"]:
                        related_names.append(rel.get("target", ""))
                    elif rel.get("target") == ent["name"]:
                        related_names.append(rel.get("source", ""))

                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_entity_graph
                    (doc_id, subject, entity_name, entity_type, related_entities)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, subject, ent["name"], ent.get("type", "concept"),
                      json.dumps(related_names[:10], ensure_ascii=False)))

            # 存储关系（如果有 relations 表）
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS entity_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id INTEGER,
                        source_entity TEXT,
                        target_entity TEXT,
                        relation_type TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                for rel in relations:
                    cursor.execute("""
                        INSERT INTO entity_relations (doc_id, source_entity, target_entity, relation_type)
                        VALUES (?, ?, ?, ?)
                    """, (doc_id, rel.get("source", ""), rel.get("target", ""),
                          rel.get("relation", "related_to")))
            except Exception:
                pass

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            error(f"[KG] 存储图谱数据失败: {e}")
            return False


# 全局单例
multi_hop_retriever = MultiHopRetriever()
