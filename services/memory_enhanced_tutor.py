"""
记忆增强型辅导服务 - 集成无限长时记忆架构
将记忆系统与问答/辅导服务深度集成
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.logger import info, error, warning
from services.memory_service import memory_service
from services.memory_extractor import memory_extractor
from services.tutor_agent import TutorAgent
from services.qa_service import qa_service


class MemoryEnhancedTutor:
    """记忆增强型辅导服务"""
    
    def __init__(self, kimi_client=None):
        self.tutor_agent = TutorAgent()
        self.kimi_client = kimi_client
        if kimi_client:
            memory_extractor.kimi_client = kimi_client
        
    def answer_with_memory(self, user_id: int, input_data: Dict) -> Dict:
        """
        带记忆的问答 - 会参考历史对话和用户知识
        
        Args:
            user_id: 用户ID
            input_data: 问题数据
            
        Returns:
            增强型回答
        """
        question = input_data.get("question", "")
        subject = input_data.get("subject", "综合")
        session_id = input_data.get("session_id", "default")
        
        try:
            with memory_service as ms:
                # 1. 检索相关记忆
                relevant_memories = self._retrieve_relevant_memories(ms, user_id, question, subject)
                
                # 2. 获取用户知识背景
                user_context = self._build_user_context(ms, user_id, subject)
                
                # 3. 获取对话历史
                conversation_history = ms.get_short_term_context(user_id, session_id, max_tokens=2000)
                
                # 4. 构建增强上下文
                enhanced_context = self._build_enhanced_context(
                    question, subject, relevant_memories, user_context, conversation_history
                )
                
                # 5. 生成回答
                enhanced_input = {
                    **input_data,
                    "context": enhanced_context
                }
                
                result = self.tutor_agent.answer_query(user_id, enhanced_input)
                
                # 6. 保存短期记忆
                ms.add_short_term(user_id, session_id, 'user', question)
                
                answer_text = result.get('answer', {}).get('text', '')
                if answer_text:
                    ms.add_short_term(user_id, session_id, 'assistant', answer_text)
                    
                # 7. 提取并保存长期记忆
                self._extract_and_save_memories(ms, user_id, session_id, question, answer_text, subject)
                
                # 8. 添加记忆摘要到结果
                result['memory_context'] = {
                    'relevant_memories_count': len(relevant_memories.get('semantic', [])),
                    'user_knowledge_level': user_context.get('knowledge_level', 'unknown'),
                    'conversation_turns': len(conversation_history)
                }
                
                return result
                
        except Exception as e:
            error(f"记忆增强问答失败: {str(e)}")
            # 降级到普通问答
            return self.tutor_agent.answer_query(user_id, input_data)
            
    def _retrieve_relevant_memories(self, ms, user_id: int, question: str, subject: str) -> Dict:
        """检索相关记忆"""
        memories = {
            'semantic': [],
            'episodic': [],
            'entity': []
        }
        
        try:
            # 搜索语义记忆（事实知识）
            memories['semantic'] = ms.search_semantic(user_id, question, limit=5)
            
            # 搜索情景记忆（历史对话）
            memories['episodic'] = ms.search_episodic(user_id, question, limit=3)
            
            # 搜索相关实体
            memories['entity'] = ms.search_entities(user_id, question, limit=3)
            
            # 如果有学科信息，搜索该学科的知识
            if subject and subject != '综合':
                subject_facts = ms.get_facts_by_subject(user_id, subject)
                if subject_facts:
                    memories['semantic'].extend(subject_facts[:3])
                    
        except Exception as e:
            warning(f"检索记忆失败: {str(e)}")
            
        return memories
        
    def _build_user_context(self, ms, user_id: int, subject: str) -> Dict:
        """构建用户知识背景"""
        context = {
            'knowledge_level': 'beginner',
            'known_concepts': [],
            'learning_goals': [],
            'preferences': {}
        }
        
        try:
            # 获取用户的技能实体
            skills = ms.search_entities(user_id, '', entity_type='skill', limit=10)
            context['known_concepts'] = [s['entity_name'] for s in skills]
            
            # 获取用户的学习目标
            goals = ms.search_semantic(user_id, '', fact_type='goal', limit=5)
            context['learning_goals'] = [g['object'] for g in goals]
            
            # 获取用户偏好
            preferences = ms.search_semantic(user_id, '', fact_type='preference', limit=5)
            for pref in preferences:
                context['preferences'][pref['subject']] = pref['object']
                
            # 根据已知概念判断知识水平
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
        context_parts = []
        
        # 1. 用户知识背景
        if user_context.get('known_concepts'):
            context_parts.append(f"用户已掌握的概念: {', '.join(user_context['known_concepts'][:5])}")
            
        if user_context.get('learning_goals'):
            context_parts.append(f"用户学习目标: {', '.join(user_context['learning_goals'][:3])}")
            
        # 2. 相关事实知识
        if relevant_memories.get('semantic'):
            facts = []
            for fact in relevant_memories['semantic'][:3]:
                facts.append(f"- {fact['subject']} {fact['predicate']} {fact['object']}")
            if facts:
                context_parts.append("相关知识:\n" + "\n".join(facts))
                
        # 3. 历史对话摘要
        if relevant_memories.get('episodic'):
            episodes = []
            for ep in relevant_memories['episodic'][:2]:
                episodes.append(f"- {ep.get('title', '对话')}: {ep.get('summary', '')[:100]}")
            if episodes:
                context_parts.append("相关历史对话:\n" + "\n".join(episodes))
                
        # 4. 最近对话上下文
        if conversation_history:
            recent = conversation_history[-3:]  # 最近3轮
            history_text = []
            for msg in recent:
                role = "用户" if msg['role'] == 'user' else "助手"
                history_text.append(f"{role}: {msg['content'][:100]}")
            if history_text:
                context_parts.append("最近对话:\n" + "\n".join(history_text))
                
        return "\n\n".join(context_parts) if context_parts else ""
        
    def _extract_and_save_memories(self, ms, user_id: int, session_id: str,
                                   question: str, answer: str, subject: str):
        """提取并保存记忆"""
        try:
            # 使用规则方法提取
            facts = memory_extractor.extract_facts_from_text(question)
            entities = memory_extractor.extract_entities_from_text(question)
            
            # 保存提取的事实
            for fact in facts:
                ms.add_semantic(
                    user_id=user_id,
                    fact_type=fact['type'],
                    subject=fact['subject'],
                    predicate=fact['predicate'],
                    object_val=fact['object'],
                    confidence=fact['confidence'],
                    source=f"tutor_session:{session_id}"
                )
                
            # 保存提取的实体
            for entity in entities:
                ms.add_entity(
                    user_id=user_id,
                    entity_type=entity['type'],
                    entity_name=entity['name'],
                    description=entity.get('description', '')
                )
                
            # 保存情景记忆（如果有意义的问答）
            if len(question) > 10 and len(answer) > 50:
                ms.add_episodic(
                    user_id=user_id,
                    episode_type='question',
                    title=f"问答: {subject}",
                    summary=f"问题: {question[:100]}...",
                    content=f"Q: {question}\nA: {answer[:500]}",
                    context={'session_id': session_id, 'subject': subject},
                    importance=0.6
                )
                
        except Exception as e:
            warning(f"提取记忆失败: {str(e)}")
            
    def get_user_knowledge_map(self, user_id: int) -> Dict:
        """获取用户知识图谱"""
        try:
            with memory_service as ms:
                stats = ms.get_memory_stats(user_id)
                
                # 获取所有技能实体
                skills = ms.search_entities(user_id, '', entity_type='skill', limit=50)
                
                # 获取知识概念
                concepts = ms.search_entities(user_id, '', entity_type='concept', limit=50)
                
                # 获取课程
                courses = ms.search_entities(user_id, '', entity_type='course', limit=20)
                
                # 构建知识图谱
                knowledge_map = {
                    'skills': [{'name': s['entity_name'], 'level': s.get('attributes', {}).get('level', 'unknown')} 
                              for s in skills],
                    'concepts': [c['entity_name'] for c in concepts],
                    'courses': [c['entity_name'] for c in courses],
                    'stats': stats
                }
                
                return knowledge_map
                
        except Exception as e:
            error(f"获取知识图谱失败: {str(e)}")
            return {'skills': [], 'concepts': [], 'courses': [], 'stats': {}}
            
    def get_learning_recommendations(self, user_id: int, subject: str = None) -> List[Dict]:
        """基于记忆获取学习推荐"""
        recommendations = []
        
        try:
            with memory_service as ms:
                # 获取用户知识水平
                user_context = self._build_user_context(ms, user_id, subject or '')
                
                # 获取学习目标
                goals = user_context.get('learning_goals', [])
                
                # 获取已知概念
                known = set(user_context.get('known_concepts', []))
                
                # 搜索相关的高级概念
                if subject:
                    related_concepts = ms.search_entities(user_id, subject, entity_type='concept', limit=10)
                    
                    for concept in related_concepts:
                        if concept['entity_name'] not in known:
                            recommendations.append({
                                'type': 'concept',
                                'name': concept['entity_name'],
                                'reason': f"与{subject}相关的新概念",
                                'priority': concept.get('importance', 0.5)
                            })
                            
                # 基于遗忘曲线推荐复习
                # 获取需要复习的记忆
                semantic_memories = ms.search_semantic(user_id, subject or '', limit=20)
                for mem in semantic_memories:
                    if mem.get('access_count', 0) > 0:
                        # 计算需要复习的程度
                        days_since_access = 0
                        if mem.get('last_accessed_at'):
                            days_since_access = (datetime.now() - mem['last_accessed_at']).days
                            
                        if days_since_access > 7:  # 超过7天未访问
                            recommendations.append({
                                'type': 'review',
                                'name': f"{mem['subject']} - {mem['predicate']}",
                                'reason': f"已{days_since_access}天未复习，建议巩固",
                                'priority': 0.7
                            })
                            
                # 按优先级排序
                recommendations.sort(key=lambda x: x.get('priority', 0), reverse=True)
                
                return recommendations[:10]
                
        except Exception as e:
            error(f"获取学习推荐失败: {str(e)}")
            return []
            
    def apply_memory_maintenance(self, user_id: int = None):
        """应用记忆维护（遗忘曲线、清理等）"""
        try:
            with memory_service as ms:
                # 应用遗忘曲线
                forgetting_result = ms.apply_forgetting_curve(user_id)
                
                # 清理已遗忘的记忆
                cleanup_count = ms.cleanup_forgotten_memories(user_id, days=90)
                
                return {
                    'forgetting': forgetting_result,
                    'cleanup': cleanup_count
                }
                
        except Exception as e:
            error(f"记忆维护失败: {str(e)}")
            return {'forgetting': {'forgotten': 0, 'reinforced': 0}, 'cleanup': 0}


# 全局单例
memory_enhanced_tutor = MemoryEnhancedTutor()
