"""
记忆提取服务 - 从对话中提取记忆
使用 AI 分析对话内容，提取事实、实体、情景
"""

import json
import re

from core.logger import error, warning
from services.memory_service import memory_service


class MemoryExtractor:
    """记忆提取器"""

    # 标准关系类型本体
    RELATION_TYPE_MAP = {
        'uses': 'uses', 'use': 'uses', 'uses_for': 'uses', 'is_used_for': 'uses',
        '用于': 'uses', '使用': 'uses', '利用': 'uses',
        'is_a': 'is_a', 'is_type_of': 'is_a', '属于': 'is_a', '是一种': 'is_a',
        'part_of': 'part_of', 'belongs_to': 'part_of', '包含': 'part_of',
        'depends_on': 'depends_on', 'requires': 'depends_on', '依赖': 'depends_on', '需要': 'depends_on',
        'improves': 'improves', 'enhances': 'improves', '提升': 'improves', '改善': 'improves',
        'causes': 'causes', 'leads_to': 'causes', '导致': 'causes', '引起': 'causes',
        'related_to': 'related_to', 'related': 'related_to', '相关': 'related_to', '关联': 'related_to',
        'teaches': 'teaches', 'covers': 'teaches', '教授': 'teaches', '涵盖': 'teaches',
        'prerequisite': 'prerequisite', '前置': 'prerequisite', '基础': 'prerequisite',
        'contradicts': 'contradicts', 'opposes': 'contradicts', '矛盾': 'contradicts', '相反': 'contradicts',
    }

    def _normalize_relation_type(self, raw_type: str) -> str:
        """规范化关系类型到标准本体"""
        t = raw_type.strip().lower()
        if t in self.RELATION_TYPE_MAP:
            return self.RELATION_TYPE_MAP[t]
        for key, val in self.RELATION_TYPE_MAP.items():
            if key in t or t in key:
                return val
        return 'related_to'

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def _clean_entity(self, entity: dict) -> dict | None:
        """实体后处理：清洗、标准化、过滤"""
        name = entity.get('name', '').strip()
        # 过滤空名称、纯标点、超长名称
        if not name or len(name) > 100:
            return None
        # 过滤纯标点/数字
        import re
        if re.match(r'^[\d\s\W]+$', name):
            return None
        # 清洗：去除多余空格和特殊字符
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.strip('。，、；：""''（）【】《》')
        if not name or len(name) < 2:
            return None
        entity['name'] = name
        # 规范化类型
        entity['type'] = entity.get('type', 'concept').strip().lower()
        return entity

    def extract_from_conversation(self, user_id: int, session_id: str,
                                  user_message: str, assistant_response: str) -> dict[str, int]:
        """从对话中提取记忆"""
        results = {
            'short_term': 0,
            'episodic': 0,
            'semantic': 0,
            'entity': 0,
            'relations': 0
        }

        try:
            with memory_service as ms:
                # 1. 保存短期记忆
                ms.add_short_term(user_id, session_id, 'user', user_message)
                ms.add_short_term(user_id, session_id, 'assistant', assistant_response)
                results['short_term'] = 2

                # 2. 使用 AI 提取长期记忆
                extracted = {}
                if self.ai_client:
                    extracted = self._extract_with_ai(user_message, assistant_response)

                # 2.5 规则方法补充（AI 未提取到的内容）
                rule_facts = self.extract_facts_from_text(user_message)
                rule_entities = self.extract_entities_from_text(user_message)
                existing_fact_keys = {(f.get('subject',''), f.get('predicate',''), f.get('object',''))
                                      for f in extracted.get('facts', [])}
                existing_entity_names = {e.get('name','').lower() for e in extracted.get('entities', [])}
                for rf in rule_facts:
                    key = (rf.get('subject',''), rf.get('predicate',''), rf.get('object',''))
                    if key not in existing_fact_keys:
                        extracted.setdefault('facts', []).append(rf)
                for re_ in rule_entities:
                    if re_.get('name','').lower() not in existing_entity_names:
                        extracted.setdefault('entities', []).append(re_)

                # 3. 保存语义记忆（事实）
                for fact in extracted.get('facts', []):
                    ms.add_semantic(
                        user_id=user_id,
                        fact_type=fact.get('type', 'knowledge'),
                        subject=fact['subject'],
                        predicate=fact['predicate'],
                        object_val=fact['object'],
                        confidence=fact.get('confidence', 0.7),
                        source=f"session:{session_id}"
                    )
                    results['semantic'] += 1

                # 4. 保存实体记忆（含后处理）
                entity_ids = {}
                seen_names = set()  # 批次内去重
                for entity in extracted.get('entities', []):
                    entity = self._clean_entity(entity)
                    if not entity:
                        continue
                    name = entity['name']
                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    entity_id = ms.add_entity(
                        user_id=user_id,
                        entity_type=entity.get('type', 'concept'),
                        entity_name=entity['name'],
                        attributes=entity.get('attributes'),
                        description=entity.get('description', '')
                    )
                    entity_ids[entity['name']] = entity_id
                    results['entity'] += 1

                # 5. 保存实体关系（支持跨对话）
                for relation in extracted.get('relations', []):
                    source_name = relation.get('source')
                    target_name = relation.get('target')
                    rel_type = self._normalize_relation_type(relation.get('type', 'related'))

                    # 查找源实体 ID（先当前批次，再数据库）
                    source_id = entity_ids.get(source_name)
                    if not source_id:
                        found = ms.search_entities(user_id, source_name, limit=1)
                        if found:
                            source_id = found[0]['id']

                    # 查找目标实体 ID
                    target_id = entity_ids.get(target_name)
                    if not target_id:
                        found = ms.search_entities(user_id, target_name, limit=1)
                        if found:
                            target_id = found[0]['id']

                    if source_id and target_id:
                        ms.add_relation(
                            user_id=user_id,
                            source_entity_id=source_id,
                            target_entity_id=target_id,
                            relation_type=rel_type,
                            relation_label=relation.get('label', '')
                        )
                        results['relations'] += 1

                # 6. 保存情景记忆（如果对话有意义）
                if extracted.get('episode'):
                    episode = extracted['episode']
                    ms.add_episodic(
                        user_id=user_id,
                        episode_type=episode.get('type', 'conversation'),
                        title=episode.get('title', ''),
                        summary=episode.get('summary', ''),
                        content=f"用户: {user_message}\n助手: {assistant_response}",
                        context={'session_id': session_id},
                        importance=episode.get('importance', 0.5)
                    )
                    results['episodic'] += 1

        except Exception as e:
            error(f"记忆提取失败: {e!s}")

        return results

    def _extract_with_ai(self, user_message: str, assistant_response: str) -> dict:
        """使用 AI 提取记忆信息"""
        try:
            prompt = f"""分析以下对话，提取有价值的记忆信息。返回 JSON 格式。

对话内容：
用户: {user_message}
助手: {assistant_response}

请提取以下信息并以 JSON 格式返回：

{{
    "facts": [
        {{
            "type": "preference|knowledge|skill|habit|goal|constraint",
            "subject": "主题",
            "predicate": "关系/属性",
            "object": "值/目标",
            "confidence": 0.0-1.0
        }}
    ],
    "entities": [
        {{
            "type": "person|concept|skill|course|tool|organization|other",
            "name": "实体名称",
            "description": "简短描述",
            "attributes": {{"key": "value"}}
        }}
    ],
    "relations": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型(uses/is_a/part_of/depends_on/improves/causes/teaches/prerequisite/related_to)",
            "label": "关系描述"
        }}
    ],
    "episode": {{
        "type": "conversation|learning|question|task|event",
        "title": "对话标题",
        "summary": "对话摘要",
        "importance": 0.0-1.0
    }}
}}

注意：
1. 只提取有价值的信息，不要提取闲聊内容
2. facts 应该是明确的事实陈述
3. entities 应该是有意义的实体
4. confidence 根据信息的确定性评分
5. 如果没有有价值的信息，返回空数组

返回纯 JSON，不要包含其他文字。"""

            response = self.ai_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            # 解析 JSON
            content = response.strip()
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}

        except Exception as e:
            warning(f"AI 记忆提取失败: {e!s}")
            return {}

    def extract_facts_from_text(self, text: str) -> list[dict]:
        """从文本中提取事实（规则方法）"""
        facts = []

        # 常见模式
        patterns = [
            # "我是..." 模式
            (r'我是(.+?)(?:，|。|$)', 'person', 'is', 0.9),
            # "我喜欢..." 模式
            (r'我喜欢(.+?)(?:，|。|$)', 'preference', 'likes', 0.8),
            # "我不喜欢..." 模式
            (r'我不喜欢(.+?)(?:，|。|$)', 'preference', 'dislikes', 0.8),
            # "我在学..." 模式
            (r'我在学(?:习)?(.+?)(?:，|。|$)', 'knowledge', 'learning', 0.7),
            # "我擅长..." 模式
            (r'我擅长(.+?)(?:，|。|$)', 'skill', 'good_at', 0.8),
            # "我想..." 模式
            (r'我想(.+?)(?:，|。|$)', 'goal', 'wants', 0.7),
            # "..." 是 ... 模式
            (r'(.+?)是(.+?)(?:，|。|$)', 'knowledge', 'is', 0.6),
        ]

        for pattern, fact_type, predicate, confidence in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    subject, obj = match
                else:
                    subject = "用户"
                    obj = match

                facts.append({
                    'type': fact_type,
                    'subject': subject.strip(),
                    'predicate': predicate,
                    'object': obj.strip(),
                    'confidence': confidence
                })

        return facts

    def extract_entities_from_text(self, text: str) -> list[dict]:
        """从文本中提取实体（规则方法）"""
        entities = []

        # 课程名称模式
        course_patterns = [
            r'(?:学习|学|上|选修|修了?)\s*[""「]?(.+?)[""」]?(?:课|课程|专业)',
            r'(.+?)(?:课|课程|专业)(?:的|是)',
        ]

        for pattern in course_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({
                    'type': 'course',
                    'name': match.strip(),
                    'description': f'课程: {match.strip()}'
                })

        # 技能名称模式
        skill_patterns = [
            r'(?:会|懂|学过|掌握|熟悉)\s*(.+?)(?:，|。|$)',
            r'(.+?)(?:技术|技能|语言|框架|工具)',
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) < 20:  # 避免过长的匹配
                    entities.append({
                        'type': 'skill',
                        'name': match.strip(),
                        'description': f'技能: {match.strip()}'
                    })

        return entities


# 全局单例
memory_extractor = MemoryExtractor()
