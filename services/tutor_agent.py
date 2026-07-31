"""
智能辅导智能体 - 多模态答疑解惑（集成记忆增强）
提供文字解答、图解说明、短视频讲解等多样化形式
集成无限长时记忆架构：短期/情景/语义/实体记忆 + 遗忘机制
集成算法增强层：Query理解、个性化Prompt、上下文压缩、质量评分、引用标注
"""

import json
from datetime import datetime

from core.json_utils import safe_parse_json
from core.logger import debug, error, info, warning
from services.qa_service import qa_service


class TutorAgent:
    """智能辅导智能体（集成记忆增强）"""

    def __init__(self):
        info("智能辅导智能体初始化完成")

    # ==========================================
    # 核心问答（带记忆增强）
    # ==========================================

    def answer_query(self, user_id: int, input_data: dict) -> dict:
        """
        回答学生问题 - 记忆增强版 + Self-RAG 决策

        流程：
        1. Self-RAG 前置判断：是否需要检索
        2. 策略路由：按题型选择最优检索策略
        3. 记忆增强 + 检索
        4. 生成回答
        5. 后置校验：结果质量验证
        """
        info(f"开始智能辅导答疑, 用户: {user_id}")

        question = input_data.get("question", "")
        subject = input_data.get("subject", "综合")
        session_id = input_data.get("session_id", "default")

        # ── 查询预处理（QueryProcessor）──
        try:
            from services.query_processor import query_processor
            processed_query = query_processor.process(question)
            question = processed_query.corrected  # 使用纠错后的查询
            if processed_query.entities.get("subject") and subject == "综合":
                subject = processed_query.entities["subject"]
            debug(f"[QueryProcessor] intent={processed_query.intent}, entities={processed_query.entities}")
        except Exception as e:
            debug(f"QueryProcessor 降级: {e}")

        # ── Self-RAG 前置判断 ──
        try:
            from services.self_rag import self_rag
            gate_result = self_rag.retrieval_gate(question, subject)

            if not gate_result["needs_retrieval"]:
                info(f"[Self-RAG] 跳过检索: reason={gate_result['reason']}")
                direct = gate_result.get("direct_answer")
                if direct:
                    return {
                        "answer": {"text_answer": {"summary": direct, "steps": []}},
                        "message": "直接回答（无需检索）",
                        "self_rag": {"skipped": True, "reason": gate_result["reason"]},
                    }
                # 无直接回答，让 LLM 生成（不带检索上下文）
                return self._fallback_answer(user_id, input_data)

            # 策略路由
            route_result = self_rag.strategy_router(question, subject)
            preferred_strategy = route_result["strategy"]
            info(f"[Self-RAG] 策略路由: {preferred_strategy} (type={route_result['question_type']}, "
                 f"conf={route_result['confidence']:.2f})")
        except Exception as e:
            debug(f"Self-RAG 决策降级: {e}")
            preferred_strategy = None

        # 尝试使用记忆增强，失败则降级
        try:
            from services.memory_service import memory_service

            with memory_service as ms:
                # 1. 检索相关记忆（使用 Self-RAG 策略路由）
                try:
                    ms.ensure_connected()
                    relevant_memories = self._retrieve_memories(
                        ms, user_id, question, subject, preferred_strategy
                    )
                except Exception as e:
                    debug(f"记忆检索失败: {e}")
                    relevant_memories = {'semantic': [], 'episodic': [], 'entity': [], 'rag_docs': []}

                # 2. 获取用户知识背景
                try:
                    user_context = self._build_user_context(ms, user_id, subject)
                except Exception as e:
                    debug(f"构建用户上下文失败: {e}")
                    user_context = {'knowledge_level': 'beginner', 'known_concepts': [], 'learning_goals': [], 'preferences': {}}

                # 3. 获取对话历史
                try:
                    conversation_history = ms.get_short_term_context(user_id, session_id, max_tokens=2000)
                except Exception as e:
                    debug(f"获取对话历史失败: {e}")
                    conversation_history = []

                # 4. 构建增强上下文
                enhanced_context = self._build_enhanced_context(
                    question, subject, relevant_memories, user_context, conversation_history
                )

                # 5. 合并上下文
                original_context = input_data.get("context", "")
                merged_context = f"{original_context}\n\n{enhanced_context}".strip()

                # 5.5 上下文压缩（ContextCompressor）
                try:
                    from services.context_compressor import context_compressor
                    if len(merged_context) > 3000:
                        compressed = context_compressor.compress(
                            [{"role": "user", "content": question},
                             {"role": "assistant", "content": merged_context}]
                        )
                        if compressed.compressed:
                            merged_context = context_compressor.format_for_prompt(compressed)
                except Exception as e:
                    debug(f"上下文压缩跳过: {e}")

                # 6. 获取画像并生成回答
                profile = self._get_user_profile(user_id)
                answer_data = self._generate_multimodal_answer(
                    question, subject, merged_context, profile,
                    input_data.get("preferred_format", "all")
                )

                # 6.1 答案质量快速评分（AnswerQualityScorer）
                answer_text_raw = answer_data.get('text_answer', {})
                if isinstance(answer_text_raw, dict):
                    answer_text_raw = answer_text_raw.get('summary', str(answer_text_raw))
                try:
                    from services.answer_quality_scorer import answer_quality_scorer
                    quality = answer_quality_scorer.score(question, str(answer_text_raw), merged_context[:2000])
                    answer_data['quality_score'] = {
                        "total": quality.total,
                        "dimensions": quality.dimensions,
                        "flags": quality.flags,
                        "suggestion": quality.suggestion,
                    }
                    # 低分且无更好结果时才触发 LLM 反思
                    answer_data['_needs_llm_review'] = quality.needs_llm_review
                    debug(f"[QualityScorer] score={quality.total}, flags={quality.flags}")
                except Exception as e:
                    debug(f"QualityScorer 降级: {e}")

                # 6.2 引用标注（CitationAnnotator）
                try:
                    from services.citation_annotator import citation_annotator
                    rag_docs = relevant_memories.get('rag_docs', [])
                    if rag_docs and answer_text_raw:
                        citation_result = citation_annotator.annotate(str(answer_text_raw), rag_docs)
                        if citation_result.citation_count > 0:
                            if isinstance(answer_data.get('text_answer'), dict):
                                answer_data['text_answer']['summary'] = citation_result.annotated_text
                            answer_data['citations'] = {
                                "count": citation_result.citation_count,
                                "sources": citation_result.source_map,
                            }
                            debug(f"[CitationAnnotator] {citation_result.citation_count}处引用")
                except Exception as e:
                    debug(f"CitationAnnotator 降级: {e}")

                # 6.5 反思验证：评估答案质量，低分触发二次检索重新生成
                try:
                    from services.reflector import reflector
                    answer_text_for_reflect = answer_data.get('text_answer', {})
                    if isinstance(answer_text_for_reflect, dict):
                        answer_text_for_reflect = answer_text_for_reflect.get('summary', str(answer_text_for_reflect))
                    reflection = reflector.reflect_and_improve(
                        query=question,
                        answer=str(answer_text_for_reflect),
                        context=merged_context[:3000],
                        user_id=user_id
                    )
                    if reflection.get("improved"):
                        improved = reflection.get("final_answer", "")
                        if improved and not improved.startswith("错误"):
                            answer_data["text_answer"] = {"summary": improved, "steps": []}
                            answer_data["reflector"] = {
                                "improved": True,
                                "retries": reflection.get("retries", 0),
                                "quality_score": reflection.get("reflection", {}).get("quality_score"),
                            }
                except Exception as reflect_err:
                    debug(f"反思验证跳过: {reflect_err}")

                # 6.6 Self-RAG 后置校验：检索结果是否充分
                try:
                    from services.self_rag import self_rag
                    answer_text_for_verify = answer_data.get('text_answer', {})
                    if isinstance(answer_text_for_verify, dict):
                        answer_text_for_verify = answer_text_for_verify.get('summary', str(answer_text_for_verify))
                    verify_result = self_rag.result_verifier(
                        question, relevant_memories.get('rag_docs', []), str(answer_text_for_verify)
                    )
                    answer_data['self_rag'] = {
                        "quality_score": verify_result["quality_score"],
                        "is_sufficient": verify_result["is_sufficient"],
                        "strategy_used": preferred_strategy,
                    }
                    # 如果质量不足且应重试，用新策略重新检索
                    if verify_result["should_retry"] and verify_result["retry_strategy"]:
                        retry_strategy = verify_result["retry_strategy"]
                        info(f"[Self-RAG] 质量不足，重试策略: {retry_strategy}")
                        ms.ensure_connected()
                        retry_results = self._retrieve_memories(
                            ms, user_id, question, subject, retry_strategy
                        )
                        if retry_results.get('rag_docs'):
                            # 用新检索结果重新生成
                            retry_context = self._build_enhanced_context(
                                question, subject, retry_results, user_context, conversation_history
                            )
                            retry_merged = f"{original_context}\n\n{retry_context}".strip()
                            retry_answer = self._generate_multimodal_answer(
                                question, subject, retry_merged, profile,
                                input_data.get("preferred_format", "all")
                            )
                            # 如果重试结果更好，使用重试结果
                            retry_text = retry_answer.get('text_answer', {})
                            if isinstance(retry_text, dict):
                                retry_text = retry_text.get('summary', str(retry_text))
                            if retry_text and len(str(retry_text)) > len(str(answer_text_for_verify)):
                                answer_data = retry_answer
                                answer_data['self_rag'] = {
                                    "quality_score": verify_result["quality_score"],
                                    "retried": True,
                                    "retry_strategy": retry_strategy,
                                    "strategy_used": retry_strategy,
                                }
                except Exception as self_rag_err:
                    debug(f"Self-RAG 后置校验跳过: {self_rag_err}")

                # 7. 保存问答记录
                self._save_tutor_record(user_id, question, answer_data)

                # 8. 保存短期记忆（cursor 可能已关闭，自动重连）
                try:
                    ms.ensure_connected()
                    ms.add_short_term(user_id, session_id, 'user', question)
                    answer_text = answer_data.get('text_answer', {})
                    if isinstance(answer_text, dict):
                        answer_text = answer_text.get('summary', '')
                    if answer_text:
                        ms.add_short_term(user_id, session_id, 'assistant', str(answer_text))
                except Exception as mem_err:
                    debug(f"保存短期记忆失败（cursor 可能已关闭）: {mem_err}")

                # 9. 提取并保存长期记忆
                try:
                    ms.ensure_connected()
                    answer_text = answer_data.get('text_answer', {})
                    if isinstance(answer_text, dict):
                        answer_text = answer_text.get('summary', '')
                    self._extract_and_save_memories(ms, user_id, session_id, question, str(answer_text), subject)
                except Exception as mem_err:
                    debug(f"保存长期记忆失败: {mem_err}")

                # 生成交互ID（用于反馈追踪）
                interaction_id = ""
                try:
                    from services.self_learning_service import self_learning_service
                    interaction_id = self_learning_service.generate_interaction_id()
                except Exception:
                    pass

                result = {
                    "answer": answer_data,
                    "message": "智能辅导回答生成完成",
                    "interaction_id": interaction_id,
                    "memory_context": {
                        "relevant_memories_count": len(relevant_memories.get('semantic', [])),
                        "user_knowledge_level": user_context.get('knowledge_level', 'unknown'),
                        "conversation_turns": len(conversation_history)
                    },
                    "self_rag": answer_data.get('self_rag', {
                        "strategy_used": preferred_strategy,
                    }),
                }

                info(f"智能辅导完成, 解答类型: {answer_data.get('formats', [])}")
                return result

        except Exception as e:
            import traceback
            warning(f"记忆增强失败，降级到普通问答: {e!s}")
            debug(f"异常堆栈: {traceback.format_exc()}")
            return self._fallback_answer(user_id, input_data)

    def _fallback_answer(self, user_id: int, input_data: dict) -> dict:
        """降级问答（无记忆）"""
        try:
            question = input_data.get("question", "")
            subject = input_data.get("subject", "综合")
            context = input_data.get("context", "")
            profile = self._get_user_profile(user_id)
            answer_data = self._generate_multimodal_answer(
                question, subject, context, profile,
                input_data.get("preferred_format", "all")
            )
            self._save_tutor_record(user_id, question, answer_data)
            return {"answer": answer_data, "message": "智能辅导回答生成完成（降级模式）"}
        except Exception as e:
            error(f"辅导失败: {e!s}")
            return {"answer": None, "message": f"辅导失败: {e!s}"}

    # ==========================================
    # 记忆检索与上下文构建
    # ==========================================

    def _retrieve_memories(self, ms, user_id: int, question: str, subject: str,
                           preferred_strategy: str | None = None) -> dict:
        """检索相关记忆（集成高级检索 + Self-RAG 策略路由）"""
        memories = {'semantic': [], 'episodic': [], 'entity': [], 'rag_docs': []}
        try:
            memories['semantic'] = ms.search_semantic(user_id, question, limit=5)
            memories['episodic'] = ms.search_episodic(user_id, question, limit=3)
            memories['entity'] = ms.search_entities(user_id, question, limit=3)
            if subject and subject != '综合':
                subject_facts = ms.get_facts_by_subject(user_id, subject)
                if subject_facts:
                    memories['semantic'].extend(subject_facts[:3])

            # 高级 RAG 检索（根据 Self-RAG 策略选择）
            try:
                from services.advanced_retrieval_service import retrieval_service
                info(f"[RAG] 开始检索, 策略={preferred_strategy or 'graph'}, query={question[:50]}")
                if preferred_strategy:
                    rag_results = retrieval_service.smart_search(
                        user_id=user_id, query=question, subject=subject,
                        strategy=preferred_strategy, limit=3
                    )
                else:
                    rag_results = retrieval_service.graph_enhanced_search(
                        user_id=user_id, query=question, subject=subject, limit=3
                    )
                if rag_results:
                    memories['rag_docs'] = rag_results
                    info(f"[RAG] 检索到 {len(rag_results)} 篇文档, 策略={preferred_strategy or 'graph'}")
                else:
                    info(f"[RAG] 检索结果为空, 策略={preferred_strategy or 'graph'}")
            except Exception as e:
                import traceback
                warning(f"[RAG] 检索异常: {e}")
                debug(f"[RAG] 异常堆栈: {traceback.format_exc()}")
        except Exception as e:
            warning(f"检索记忆失败: {e!s}")
        return memories

    def _build_user_context(self, ms, user_id: int, subject: str) -> dict:
        """构建用户知识背景"""
        context = {'knowledge_level': 'beginner', 'known_concepts': [], 'learning_goals': [], 'preferences': {}}
        try:
            skills = ms.search_entities(user_id, '', entity_type='skill', limit=10)
            context['known_concepts'] = [s['entity_name'] for s in skills]
            goals = ms.search_semantic(user_id, '', fact_type='goal', limit=5)
            context['learning_goals'] = [g['object'] for g in goals]
            preferences = ms.search_semantic(user_id, '', fact_type='preference', limit=5)
            for pref in preferences:
                context['preferences'][pref['subject']] = pref['object']
            if len(context['known_concepts']) > 10:
                context['knowledge_level'] = 'advanced'
            elif len(context['known_concepts']) > 5:
                context['knowledge_level'] = 'intermediate'
        except Exception as e:
            warning(f"构建用户上下文失败: {e!s}")
        return context

    def _build_enhanced_context(self, question: str, subject: str,
                                relevant_memories: dict, user_context: dict,
                                conversation_history: list) -> str:
        """构建增强上下文（集成 RAG 知识文档）"""
        parts = []
        if user_context.get('known_concepts'):
            parts.append(f"用户已掌握: {', '.join(user_context['known_concepts'][:5])}")
        if user_context.get('learning_goals'):
            parts.append(f"学习目标: {', '.join(user_context['learning_goals'][:3])}")
        if relevant_memories.get('semantic'):
            facts = [f"- {f['subject']} {f['predicate']} {f['object']}" for f in relevant_memories['semantic'][:3]]
            if facts:
                parts.append("相关知识:\n" + "\n".join(facts))
        if relevant_memories.get('episodic'):
            eps = [f"- {e.get('title', '对话')}: {e.get('summary', '')[:100]}" for e in relevant_memories['episodic'][:2]]
            if eps:
                parts.append("历史对话:\n" + "\n".join(eps))

        # 注入 RAG 知识文档
        rag_docs = relevant_memories.get('rag_docs', [])
        if rag_docs:
            doc_parts = []
            for doc in rag_docs[:2]:
                title = doc.get('title', '未知文档')
                content = doc.get('content_text', '')[:300]
                method = doc.get('retrieval_method', '')
                doc_parts.append(f"- [{title}]({method}): {content}")
            if doc_parts:
                parts.append("知识库参考:\n" + "\n".join(doc_parts))

        if conversation_history:
            recent = conversation_history[-3:]
            history = [f"{'用户' if m['role'] == 'user' else '助手'}: {m['content'][:100]}" for m in recent]
            if history:
                parts.append("最近对话:\n" + "\n".join(history))
        return "\n\n".join(parts) if parts else ""

    def _extract_and_save_memories(self, ms, user_id: int, session_id: str,
                                   question: str, answer: str, subject: str):
        """提取并保存记忆"""
        try:
            from services.memory_extractor import memory_extractor
            facts = memory_extractor.extract_facts_from_text(question)
            entities = memory_extractor.extract_entities_from_text(question)
            for fact in facts:
                ms.add_semantic(user_id=user_id, fact_type=fact['type'], subject=fact['subject'],
                                predicate=fact['predicate'], object_val=fact['object'],
                                confidence=fact['confidence'], source=f"tutor:{session_id}")
            for entity in entities:
                ms.add_entity(user_id=user_id, entity_type=entity['type'],
                              entity_name=entity['name'], description=entity.get('description', ''))
            if len(question) > 10 and answer and len(answer) > 50:
                ms.add_episodic(user_id=user_id, episode_type='question', title=f"问答: {subject}",
                                summary=f"问题: {question[:100]}...", content=f"Q: {question}\nA: {answer[:500]}",
                                context={'session_id': session_id, 'subject': subject}, importance=0.6)
        except Exception as e:
            warning(f"提取记忆失败: {e!s}")

    # ==========================================
    # 知识图谱与学习推荐
    # ==========================================

    def get_user_knowledge_map(self, user_id: int) -> dict:
        """获取用户知识图谱"""
        try:
            from services.memory_service import memory_service
            with memory_service as ms:
                stats = ms.get_memory_stats(user_id)
                skills = ms.search_entities(user_id, '', entity_type='skill', limit=50)
                concepts = ms.search_entities(user_id, '', entity_type='concept', limit=50)
                courses = ms.search_entities(user_id, '', entity_type='course', limit=20)
                return {
                    'skills': [{'name': s['entity_name'], 'level': s.get('attributes', {}).get('level', 'unknown')} for s in skills],
                    'concepts': [c['entity_name'] for c in concepts],
                    'courses': [c['entity_name'] for c in courses],
                    'stats': stats
                }
        except Exception as e:
            error(f"获取知识图谱失败: {e!s}")
            return {'skills': [], 'concepts': [], 'courses': [], 'stats': {}}

    def get_learning_recommendations(self, user_id: int, subject: str | None = None) -> list[dict]:
        """专业学习规划师：综合分析薄弱点，提供个性化学习建议"""
        recommendations = []
        try:
            from data.db_operations import profile_db
            from services.memory_service import memory_service

            # ── 1. 收集多维度学习数据 ──
            grades = []
            error_notes = []
            study_plans = []
            profile = None

            # 成绩数据
            try:
                if profile_db.connect():
                    try:
                        profile_db.cursor.execute(
                            "SELECT course_name, score, credits, semester FROM student_grades WHERE user_id=? ORDER BY created_at DESC LIMIT 30",
                            (user_id,)
                        )
                        grades = [dict(r) for r in profile_db.cursor.fetchall()]
                    finally:
                        profile_db.close()
            except Exception:
                pass

            # 错题数据
            try:
                if profile_db.connect():
                    try:
                        profile_db.cursor.execute(
                            "SELECT subject, chapter, question, error_reason, mastery, created_at FROM error_notes WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
                            (user_id,)
                        )
                        error_notes = [dict(r) for r in profile_db.cursor.fetchall()]
                    finally:
                        profile_db.close()
            except Exception:
                pass

            # 学习计划
            try:
                if profile_db.connect():
                    try:
                        profile_db.cursor.execute(
                            "SELECT plan_type, plan_data, status, semester FROM study_plans WHERE user_id=? AND status='active' ORDER BY created_at DESC LIMIT 5",
                            (user_id,)
                        )
                        study_plans = [dict(r) for r in profile_db.cursor.fetchall()]
                    finally:
                        profile_db.close()
            except Exception:
                pass

            # 学生画像
            try:
                if profile_db.connect():
                    try:
                        profile_db.cursor.execute(
                            "SELECT profile_data FROM student_profiles WHERE user_id=? ORDER BY updated_at DESC LIMIT 1",
                            (user_id,)
                        )
                        row = profile_db.cursor.fetchone()
                        if row:
                            row = dict(row)
                            if row.get('profile_data'):
                                profile = json.loads(row['profile_data']) if isinstance(row['profile_data'], str) else row['profile_data']
                    finally:
                        profile_db.close()
            except Exception:
                pass

            # ── 2. 分析薄弱点 ──
            weak_analysis = self._analyze_weaknesses(grades, error_notes, profile)

            # ── 3. 基于薄弱点生成针对性建议 ──
            for weak in weak_analysis:
                recommendations.append({
                    'type': 'weakness',
                    'topic': weak['subject'],
                    'reason': weak['reason'],
                    'priority': weak['priority'],
                    'category': 'weakness',
                    'action': weak.get('action', 'review'),
                    'detail': weak.get('detail', ''),
                })

            # ── 4. 基于记忆系统推荐遗忘内容 ──
            with memory_service as ms:
                semantic_memories = ms.search_semantic(user_id, subject or '', limit=20)
                for mem in semantic_memories:
                    if mem.get('access_count', 0) > 0 and mem.get('last_accessed_at'):
                        last_accessed = mem['last_accessed_at']
                        if isinstance(last_accessed, str):
                            try:
                                last_accessed = datetime.strptime(last_accessed, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                continue
                        days = (datetime.now() - last_accessed).days
                        if days > 7:
                            priority = min(0.95, 0.6 + days * 0.02)
                            recommendations.append({
                                'type': 'review',
                                'topic': f"{mem['subject']} - {mem['predicate']}",
                                'reason': f"已{days}天未复习，根据遗忘曲线建议巩固",
                                'priority': priority,
                                'category': 'review',
                                'action': 'review',
                                'detail': f"该知识点上次访问于{last_accessed.strftime('%m月%d日')}，间隔越久遗忘越多",
                            })

            # ── 5. 基于遗忘曲线的错题复习提醒 ──
            now = datetime.now()
            review_intervals = [1, 3, 7, 14, 30]
            due_subjects = {}
            for note in error_notes:
                if note.get('mastery') == 1:
                    continue
                created = note.get('created_at', '')
                if not created:
                    continue
                try:
                    created_dt = datetime.strptime(str(created)[:19], '%Y-%m-%d %H:%M:%S')
                except Exception:
                    continue
                days = (now - created_dt).days
                subj = note.get('subject', '')
                for interval in review_intervals:
                    if days >= interval and days < interval * 2:
                        if subj not in due_subjects:
                            due_subjects[subj] = {'count': 0, 'max_days': 0}
                        due_subjects[subj]['count'] += 1
                        due_subjects[subj]['max_days'] = max(due_subjects[subj]['max_days'], days)
                        break
                if days >= 30 and subj:
                    if subj not in due_subjects:
                        due_subjects[subj] = {'count': 0, 'max_days': 0}
                    due_subjects[subj]['count'] += 1
                    due_subjects[subj]['max_days'] = max(due_subjects[subj]['max_days'], days)

            total_due = sum(d['count'] for d in due_subjects.values())
            if total_due > 0:
                top_subjects = sorted(due_subjects.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
                subject_list = '、'.join(s[0] for s in top_subjects)
                recommendations.append({
                    'type': 'review',
                    'topic': f'{total_due}道错题待复习',
                    'reason': f'涉及{subject_list}，现在是最佳复习时间',
                    'priority': min(0.95, 0.7 + total_due * 0.02),
                    'category': 'review',
                    'action': 'profile',
                    'detail': '根据遗忘曲线，及时复习可将记忆保留率提升至90%以上',
                })

            # ── 6. 基于学习计划推荐 ──
            if not study_plans:
                recommendations.append({
                    'type': 'plan',
                    'topic': '制定学习计划',
                    'reason': '暂无进行中的学习计划，有计划的学习效率更高',
                    'priority': 0.6,
                    'category': 'planning',
                    'action': 'plan',
                    'detail': '研究表明，有明确计划的学习者完成率提高40%',
                })

            # ── 7. 基于认知风格推荐学习策略 ──
            if profile:
                cognitive_style = profile.get('cognitive_style', '')
                if '视觉' in cognitive_style:
                    recommendations.append({
                        'type': 'strategy',
                        'topic': '视觉学习策略',
                        'reason': '你是视觉型学习者，建议多用图表和思维导图',
                        'priority': 0.5,
                        'category': 'strategy',
                        'action': 'resources',
                        'detail': '使用颜色标注、流程图、概念图来辅助记忆',
                    })
                elif '听觉' in cognitive_style:
                    recommendations.append({
                        'type': 'strategy',
                        'topic': '听觉学习策略',
                        'reason': '你是听觉型学习者，建议多听讲解和讨论',
                        'priority': 0.5,
                        'category': 'strategy',
                        'action': 'resources',
                        'detail': '尝试录音回听、小组讨论、朗读笔记等方式',
                    })
                elif '动觉' in cognitive_style:
                    recommendations.append({
                        'type': 'strategy',
                        'topic': '实践学习策略',
                        'reason': '你是动觉型学习者，建议多做实操练习',
                        'priority': 0.5,
                        'category': 'strategy',
                        'action': 'resources',
                        'detail': '通过动手实验、项目实践、模拟演练来加深理解',
                    })

            # ── 8. 去重、排序、截取 ──
            seen_topics = set()
            unique_recs = []
            for rec in recommendations:
                key = rec.get('topic', '')
                if key and key not in seen_topics:
                    seen_topics.add(key)
                    unique_recs.append(rec)

            unique_recs.sort(key=lambda x: x.get('priority', 0), reverse=True)
            return unique_recs[:8]

        except Exception as e:
            error(f"获取学习推荐失败: {e!s}")
            return []

    def _analyze_weaknesses(self, grades: list, error_notes: list, profile: dict | None) -> list[dict]:
        """综合分析学习薄弱点"""
        weaknesses = []

        # ── 基于成绩分析 ──
        if grades:
            subject_scores = {}
            for g in grades:
                name = g.get('course_name', '')
                score = g.get('score', 0)
                if name and score:
                    if name not in subject_scores:
                        subject_scores[name] = []
                    subject_scores[name].append(score)

            for subject, scores in subject_scores.items():
                avg = sum(scores) / len(scores)
                if avg < 60:
                    weaknesses.append({
                        'subject': subject,
                        'reason': f"平均分仅{avg:.0f}分，严重低于及格线",
                        'priority': 0.95,
                        'action': 'tutor',
                        'detail': f"共{len(scores)}次成绩记录，建议立即加强基础学习",
                    })
                elif avg < 75:
                    weaknesses.append({
                        'subject': subject,
                        'reason': f"平均分{avg:.0f}分，有较大提升空间",
                        'priority': 0.8,
                        'action': 'tutor',
                        'detail': "建议针对薄弱章节进行专项练习",
                    })

        # ── 基于错题分析 ──
        if error_notes:
            subject_errors = {}
            for e in error_notes:
                subj = e.get('subject', '')
                if subj:
                    if subj not in subject_errors:
                        subject_errors[subj] = {'total': 0, 'mastered': 0, 'reasons': []}
                    subject_errors[subj]['total'] += 1
                    if e.get('mastery') == 1:
                        subject_errors[subj]['mastered'] += 1
                    if e.get('error_reason'):
                        subject_errors[subj]['reasons'].append(e['error_reason'])

            for subj, data in subject_errors.items():
                total = data['total']
                mastered = data['mastered']
                mastery_rate = mastered / total if total > 0 else 0

                if total >= 3 and mastery_rate < 0.5:
                    # 分析主要错误原因
                    reason_counts = {}
                    for r in data['reasons']:
                        reason_counts[r] = reason_counts.get(r, 0) + 1
                    top_reason = max(reason_counts, key=reason_counts.get) if reason_counts else '知识掌握不牢'

                    weaknesses.append({
                        'subject': subj,
                        'reason': f"错题{total}道，掌握率仅{mastery_rate*100:.0f}%",
                        'priority': 0.9,
                        'action': 'tutor',
                        'detail': f"主要问题：{top_reason}，建议系统复习",
                    })
                elif total >= 5:
                    weaknesses.append({
                        'subject': subj,
                        'reason': f"累计错题{total}道，需持续关注",
                        'priority': 0.7,
                        'action': 'review',
                        'detail': f"已掌握{mastered}道，还有{total - mastered}道需要巩固",
                    })

        # ── 基于画像薄弱点 ──
        if profile:
            weak_points = profile.get('weak_points', [])
            for wp in weak_points[:3]:
                # 避免与已有的重复
                if not any(w['subject'] == wp for w in weaknesses):
                    weaknesses.append({
                        'subject': wp,
                        'reason': '画像标记的薄弱领域',
                        'priority': 0.65,
                        'action': 'tutor',
                        'detail': '建议定期复习巩固',
                    })

        return weaknesses

    def apply_memory_maintenance(self, user_id: int | None = None) -> dict:
        """应用记忆维护（遗忘曲线、清理等）"""
        try:
            from services.memory_service import memory_service
            with memory_service as ms:
                forgetting_result = ms.apply_forgetting_curve(user_id)
                cleanup_count = ms.cleanup_forgotten_memories(user_id, days=90)
                return {'forgetting': forgetting_result, 'cleanup': cleanup_count}
        except Exception as e:
            error(f"记忆维护失败: {e!s}")
            return {'forgetting': {'forgotten': 0, 'reinforced': 0}, 'cleanup': 0}

    # ==========================================
    # 多模态解答生成
    # ==========================================

    def _generate_multimodal_answer(self, question: str, subject: str,
                                   context: str, profile: dict,
                                   preferred_format: str) -> dict:
        """生成多模态解答"""
        cognitive_style = profile.get("cognitive_style", "visual") if profile else "visual"
        weak_points = profile.get("weak_points", []) if profile else []

        formats_to_generate = []
        if preferred_format == "all":
            formats_to_generate = ["text", "diagram", "example"]
        elif preferred_format == "text":
            formats_to_generate = ["text"]
        elif preferred_format == "diagram":
            formats_to_generate = ["text", "diagram"]
        elif preferred_format == "video":
            formats_to_generate = ["text", "example"]
        else:
            formats_to_generate = ["text", "diagram", "example"]

        answer_data = {
            "question": question,
            "subject": subject,
            "formats": [],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if "text" in formats_to_generate:
            text_answer = self._generate_text_answer(question, subject, context, cognitive_style, profile)
            if text_answer:
                answer_data["text_answer"] = text_answer
                answer_data["formats"].append("text")

        if "diagram" in formats_to_generate:
            diagram = self._generate_diagram_explanation(question, subject, cognitive_style)
            if diagram:
                answer_data["diagram"] = diagram
                answer_data["formats"].append("diagram")

        if "example" in formats_to_generate:
            example = self._generate_example(question, subject, weak_points)
            if example:
                answer_data["example"] = example
                answer_data["formats"].append("example")

        return answer_data

    def _generate_text_answer(self, question: str, subject: str,
                             context: str, cognitive_style: str,
                             profile: dict = None) -> dict:
        """生成文字解答（集成个性化 Prompt）"""
        base_prompt = f"""请详细回答以下{subject}课程的问题。

问题: {question}
{f'上下文: {context}' if context else ''}

要求:
1. 给出准确、清晰的答案
2. 分步骤解释,逻辑清晰
3. 标注关键概念和公式

输出JSON格式:
{{
    "summary": "简要总结(1-2句)",
    "detailed_explanation": "详细解释(Markdown格式)",
    "key_concepts": ["概念1", "概念2"],
    "common_mistakes": ["常见错误1", "常见错误2"],
    "tips": ["学习建议1", "学习建议2"]
}}"""

        # 个性化 Prompt
        try:
            from services.prompt_personalizer import prompt_personalizer
            if profile:
                personalized = prompt_personalizer.personalize(
                    base_prompt, profile, intent="explanation", context=context[:1500]
                )
                prompt = personalized.prompt
                max_tokens = personalized.max_tokens
            else:
                prompt = base_prompt
                max_tokens = 1500
        except Exception:
            prompt = base_prompt
            max_tokens = 1500

        try:
            response = qa_service.call_ai(prompt, max_tokens=max_tokens)
            return safe_parse_json(response)
        except Exception as e:
            error(f"生成文字解答失败: {e!s}")
            return None

    def _generate_diagram_explanation(self, question: str, subject: str,
                                     cognitive_style: str) -> dict:
        """生成图解说明 — 返回 Mermaid 语法"""
        prompt = f"""请为以下{subject}问题生成一个 Mermaid.js 图表代码。

问题: {question}

要求:
1. 选择最合适的图表类型(flowchart/graph/sequenceDiagram/classDiagram等)
2. 用中文标注节点和关系
3. 适合{cognitive_style}型学习者理解
4. 直接输出合法的 Mermaid 语法，不要用代码块包裹

示例输出格式:
graph TD
    A[变量声明] --> B[赋值]
    B --> C[使用变量]
    C --> D{{条件判断}}
    D -->|是| E[执行分支1]
    D -->|否| F[执行分支2]

请直接输出 Mermaid 语法:"""
        try:
            response = qa_service.call_ai(prompt, max_tokens=800)
            mermaid_code = response.strip()
            if mermaid_code.startswith("```"):
                lines = mermaid_code.split("\n")
                mermaid_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return {"mermaid": mermaid_code.strip()}
        except Exception as e:
            error(f"生成图解说明失败: {e!s}")
            return None

    def _generate_example(self, question: str, subject: str,
                         weak_points: list[str]) -> dict:
        """生成实例讲解或代码示例"""
        weak_points_str = ', '.join(weak_points[:2]) if weak_points else '无'
        prompt = f"""请为以下{subject}问题提供一个具体的实例或代码示例。

问题: {question}
学生薄弱点: {weak_points_str}

要求:
1. 提供与问题相关的具体实例
2. 如果是编程问题,提供完整可运行代码
3. 逐步解释实例的执行过程或解题思路
4. 针对薄弱点进行特别说明
5. 提供变式练习

输出JSON格式:
{{
    "example_title": "实例标题",
    "description": "实例说明",
    "steps": [{{"step_number": 1, "action": "操作步骤", "explanation": "原理解释"}}],
    "code_example": {{"language": "python/java/none", "code": "代码内容", "output": "预期输出"}},
    "practice_variations": ["变式1", "变式2"],
    "key_takeaways": ["要点1", "要点2"]
}}"""
        try:
            response = qa_service.call_ai(prompt, max_tokens=1800)
            return safe_parse_json(response)
        except Exception as e:
            error(f"生成实例讲解失败: {e!s}")
            return None

    # ==========================================
    # 工具方法
    # ==========================================

    def _get_user_profile(self, user_id: int) -> dict | None:
        """获取用户画像"""
        try:
            from data.db_operations import profile_db
            with profile_db:
                sql = "SELECT profile_data FROM student_profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql, (user_id,))
                result = profile_db.cursor.fetchone()
                if result:
                    row = dict(result)
                    if row.get("profile_data"):
                        return json.loads(row["profile_data"])
                return None
        except Exception as e:
            error(f"获取用户画像失败: {e!s}")
            return None

    def _save_tutor_record(self, user_id: int, question: str, answer_data: dict):
        """保存辅导记录"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                sql = """INSERT INTO learning_activities (user_id, activity_type, metadata, duration_seconds)
                         VALUES (?, ?, ?, ?)"""
                assessment_db.cursor.execute(sql, (
                    user_id, "tutor_query",
                    json.dumps({"question": question,
                                "answer_summary": answer_data.get("text_answer", {}).get("summary", ""),
                                "formats": answer_data.get("formats", [])}, ensure_ascii=False),
                    0
                ))
                assessment_db.conn.commit()
        except Exception as e:
            error(f"保存辅导记录失败: {e!s}")


# 全局单例
tutor_agent = TutorAgent()
