"""
智能辅导智能体 - 多模态答疑解惑（集成记忆增强）
提供文字解答、图解说明、短视频讲解等多样化形式
集成无限长时记忆架构：短期/情景/语义/实体记忆 + 遗忘机制
"""

from core.json_utils import safe_parse_json

import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from core.logger import info, error, warning
from services.qa_service import qa_service


class TutorAgent:
    """智能辅导智能体（集成记忆增强）"""

    def __init__(self):
        info("智能辅导智能体初始化完成")

    # ==========================================
    # 核心问答（带记忆增强）
    # ==========================================

    def answer_query(self, user_id: int, input_data: Dict) -> Dict:
        """
        回答学生问题 - 记忆增强版

        自动检索用户记忆上下文，构建增强 Prompt，生成个性化回答
        """
        info(f"开始智能辅导答疑, 用户: {user_id}")

        question = input_data.get("question", "")
        subject = input_data.get("subject", "综合")
        session_id = input_data.get("session_id", "default")

        # 尝试使用记忆增强，失败则降级
        try:
            from services.memory_service import memory_service

            with memory_service as ms:
                # 1. 检索相关记忆
                relevant_memories = self._retrieve_memories(ms, user_id, question, subject)

                # 2. 获取用户知识背景
                user_context = self._build_user_context(ms, user_id, subject)

                # 3. 获取对话历史
                conversation_history = ms.get_short_term_context(user_id, session_id, max_tokens=2000)

                # 4. 构建增强上下文
                enhanced_context = self._build_enhanced_context(
                    question, subject, relevant_memories, user_context, conversation_history
                )

                # 5. 合并上下文
                original_context = input_data.get("context", "")
                merged_context = f"{original_context}\n\n{enhanced_context}".strip()

                # 6. 获取画像并生成回答
                profile = self._get_user_profile(user_id)
                answer_data = self._generate_multimodal_answer(
                    question, subject, merged_context, profile,
                    input_data.get("preferred_format", "all")
                )

                # 7. 保存问答记录
                self._save_tutor_record(user_id, question, answer_data)

                # 8. 保存短期记忆
                ms.add_short_term(user_id, session_id, 'user', question)
                answer_text = answer_data.get('text_answer', {})
                if isinstance(answer_text, dict):
                    answer_text = answer_text.get('summary', '')
                if answer_text:
                    ms.add_short_term(user_id, session_id, 'assistant', str(answer_text))

                # 9. 提取并保存长期记忆
                self._extract_and_save_memories(ms, user_id, session_id, question, str(answer_text), subject)

                result = {
                    "answer": answer_data,
                    "message": "智能辅导回答生成完成",
                    "memory_context": {
                        "relevant_memories_count": len(relevant_memories.get('semantic', [])),
                        "user_knowledge_level": user_context.get('knowledge_level', 'unknown'),
                        "conversation_turns": len(conversation_history)
                    }
                }

                info(f"智能辅导完成, 解答类型: {answer_data.get('formats', [])}")
                return result

        except Exception as e:
            warning(f"记忆增强失败，降级到普通问答: {str(e)}")
            return self._fallback_answer(user_id, input_data)

    def _fallback_answer(self, user_id: int, input_data: Dict) -> Dict:
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
            return {"answer": answer_data, "message": "智能辅导回答生成完成"}
        except Exception as e:
            error(f"辅导失败: {str(e)}")
            return {"success": False, "message": f"辅导失败: {str(e)}"}

    # ==========================================
    # 记忆检索与上下文构建
    # ==========================================

    def _retrieve_memories(self, ms, user_id: int, question: str, subject: str) -> Dict:
        """检索相关记忆"""
        memories = {'semantic': [], 'episodic': [], 'entity': []}
        try:
            memories['semantic'] = ms.search_semantic(user_id, question, limit=5)
            memories['episodic'] = ms.search_episodic(user_id, question, limit=3)
            memories['entity'] = ms.search_entities(user_id, question, limit=3)
            if subject and subject != '综合':
                subject_facts = ms.get_facts_by_subject(user_id, subject)
                if subject_facts:
                    memories['semantic'].extend(subject_facts[:3])
        except Exception as e:
            warning(f"检索记忆失败: {str(e)}")
        return memories

    def _build_user_context(self, ms, user_id: int, subject: str) -> Dict:
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
            warning(f"构建用户上下文失败: {str(e)}")
        return context

    def _build_enhanced_context(self, question: str, subject: str,
                                relevant_memories: Dict, user_context: Dict,
                                conversation_history: List) -> str:
        """构建增强上下文"""
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
            warning(f"提取记忆失败: {str(e)}")

    # ==========================================
    # 知识图谱与学习推荐
    # ==========================================

    def get_user_knowledge_map(self, user_id: int) -> Dict:
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
            error(f"获取知识图谱失败: {str(e)}")
            return {'skills': [], 'concepts': [], 'courses': [], 'stats': {}}

    def get_learning_recommendations(self, user_id: int, subject: str = None) -> List[Dict]:
        """基于记忆获取学习推荐"""
        recommendations = []
        try:
            from services.memory_service import memory_service
            with memory_service as ms:
                user_context = self._build_user_context(ms, user_id, subject or '')
                known = set(user_context.get('known_concepts', []))
                if subject:
                    related = ms.search_entities(user_id, subject, entity_type='concept', limit=10)
                    for c in related:
                        if c['entity_name'] not in known:
                            recommendations.append({'type': 'concept', 'name': c['entity_name'],
                                                    'reason': f"与{subject}相关的新概念", 'priority': c.get('importance', 0.5)})
                semantic_memories = ms.search_semantic(user_id, subject or '', limit=20)
                for mem in semantic_memories:
                    if mem.get('access_count', 0) > 0 and mem.get('last_accessed_at'):
                        days = (datetime.now() - mem['last_accessed_at']).days
                        if days > 7:
                            recommendations.append({'type': 'review', 'name': f"{mem['subject']} - {mem['predicate']}",
                                                    'reason': f"已{days}天未复习，建议巩固", 'priority': 0.7})
                recommendations.sort(key=lambda x: x.get('priority', 0), reverse=True)
                return recommendations[:10]
        except Exception as e:
            error(f"获取学习推荐失败: {str(e)}")
            return []

    def apply_memory_maintenance(self, user_id: int = None) -> Dict:
        """应用记忆维护（遗忘曲线、清理等）"""
        try:
            from services.memory_service import memory_service
            with memory_service as ms:
                forgetting_result = ms.apply_forgetting_curve(user_id)
                cleanup_count = ms.cleanup_forgotten_memories(user_id, days=90)
                return {'forgetting': forgetting_result, 'cleanup': cleanup_count}
        except Exception as e:
            error(f"记忆维护失败: {str(e)}")
            return {'forgetting': {'forgotten': 0, 'reinforced': 0}, 'cleanup': 0}

    # ==========================================
    # 多模态解答生成
    # ==========================================

    def _generate_multimodal_answer(self, question: str, subject: str,
                                   context: str, profile: Dict,
                                   preferred_format: str) -> Dict:
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
            text_answer = self._generate_text_answer(question, subject, context, cognitive_style)
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
                             context: str, cognitive_style: str) -> Dict:
        """生成文字解答"""
        prompt = f"""请详细回答以下{subject}课程的问题。

问题: {question}
{f'上下文: {context}' if context else ''}

学习者认知风格: {cognitive_style}

要求:
1. 给出准确、清晰的答案
2. 分步骤解释,逻辑清晰
3. 针对{cognitive_style}型学习者优化表达方式
4. 标注关键概念和公式
5. 长度适中,约300-500字

输出JSON格式:
{{
    "summary": "简要总结(1-2句)",
    "detailed_explanation": "详细解释(Markdown格式)",
    "key_concepts": ["概念1", "概念2"],
    "common_mistakes": ["常见错误1", "常见错误2"],
    "tips": ["学习建议1", "学习建议2"]
}}"""
        try:
            response = qa_service.call_ai(prompt, max_tokens=1500)
            return safe_parse_json(response)
        except Exception as e:
            error(f"生成文字解答失败: {str(e)}")
            return None

    def _generate_diagram_explanation(self, question: str, subject: str,
                                     cognitive_style: str) -> Dict:
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
            error(f"生成图解说明失败: {str(e)}")
            return None

    def _generate_example(self, question: str, subject: str,
                         weak_points: List[str]) -> Dict:
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
            error(f"生成实例讲解失败: {str(e)}")
            return None

    # ==========================================
    # 工具方法
    # ==========================================

    def _get_user_profile(self, user_id: int) -> Optional[Dict]:
        """获取用户画像"""
        try:
            from data.db_operations import profile_db
            with profile_db:
                sql = "SELECT profile_data FROM student_profiles WHERE user_id = %s ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql, (user_id,))
                result = profile_db.cursor.fetchone()
                if result and result.get("profile_data"):
                    return json.loads(result["profile_data"])
                return None
        except Exception as e:
            error(f"获取用户画像失败: {str(e)}")
            return None

    def _save_tutor_record(self, user_id: int, question: str, answer_data: Dict):
        """保存辅导记录"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                sql = """INSERT INTO learning_activities (user_id, activity_type, metadata, duration_seconds)
                         VALUES (%s, %s, %s, %s)"""
                assessment_db.cursor.execute(sql, (
                    user_id, "tutor_query",
                    json.dumps({"question": question,
                                "answer_summary": answer_data.get("text_answer", {}).get("summary", ""),
                                "formats": answer_data.get("formats", [])}, ensure_ascii=False),
                    0
                ))
                assessment_db.conn.commit()
        except Exception as e:
            error(f"保存辅导记录失败: {str(e)}")


# 全局单例
tutor_agent = TutorAgent()
