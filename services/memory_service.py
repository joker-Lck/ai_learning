"""
无限长时记忆架构 - 记忆管理服务
支持短期记忆、情景记忆、语义记忆、实体记忆、遗忘机制、冲突修正
"""

import json
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import mysql.connector
from data.config import get_memory_db_config
from core.logger import info, error, warning


@dataclass
class MemoryItem:
    """记忆项基类"""
    id: Optional[int] = None
    user_id: int = 0
    content: str = ""
    importance: float = 0.5
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class ShortTermMemory(MemoryItem):
    """短期记忆"""
    session_id: str = ""
    role: str = "user"
    token_count: int = 0
    context_window_position: int = 0


@dataclass
class EpisodicMemory(MemoryItem):
    """情景记忆"""
    episode_type: str = "conversation"
    title: str = ""
    summary: str = ""
    context: Optional[Dict] = None
    emotions: Optional[Dict] = None
    embedding: Optional[bytes] = None


@dataclass
class SemanticMemory(MemoryItem):
    """语义记忆（事实知识）"""
    fact_type: str = "knowledge"
    subject: str = ""
    predicate: str = ""
    object: str = ""
    confidence: float = 0.8
    source: str = ""
    is_verified: bool = False
    conflict_resolution: Optional[Dict] = None


@dataclass
class EntityMemory(MemoryItem):
    """实体记忆"""
    entity_type: str = "concept"
    entity_name: str = ""
    entity_alias: str = ""
    attributes: Optional[Dict] = None
    description: str = ""


@dataclass
class EntityRelation:
    """实体关系"""
    id: Optional[int] = None
    user_id: int = 0
    source_entity_id: int = 0
    target_entity_id: int = 0
    relation_type: str = ""
    relation_label: str = ""
    weight: float = 1.0
    context: str = ""


class MemoryService:
    """记忆管理服务"""
    
    # 遗忘曲线参数
    DEFAULT_DECAY_RATE = 0.1
    MIN_IMPORTANCE = 0.1
    FORGET_THRESHOLD = 0.2
    REINFORCEMENT_BOOST = 0.15
    
    # 上下文窗口大小
    MAX_CONTEXT_TOKENS = 4000
    
    def __init__(self):
        self.config = get_memory_db_config()
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = mysql.connector.connect(**self.config, use_pure=True)
            self.cursor = self.conn.cursor(dictionary=True)
        except Exception as e:
            error(f"记忆数据库连接失败: {str(e)}")
            raise
            
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    # ==========================================
    # 短期记忆管理
    # ==========================================
    
    def add_short_term(self, user_id: int, session_id: str, role: str, content: str) -> int:
        """添加短期记忆（对话上下文）"""
        try:
            token_count = len(content) // 4  # 粗略估计 token 数
            
            sql = """
                INSERT INTO short_term_memory 
                (user_id, session_id, role, content, token_count, context_window_position)
                VALUES (%s, %s, %s, %s, %s, 
                    (SELECT COALESCE(MAX(t.context_window_position), 0) + 1 
                     FROM (SELECT context_window_position FROM short_term_memory 
                           WHERE user_id = %s AND session_id = %s) t))
            """
            self.cursor.execute(sql, (user_id, session_id, role, content, token_count, user_id, session_id))
            self.conn.commit()
            
            memory_id = self.cursor.lastrowid
            self._log_access(user_id, 'short_term', memory_id, 'write')
            
            # 清理过期的短期记忆
            self._cleanup_short_term(user_id, session_id)
            
            return memory_id
        except Exception as e:
            error(f"添加短期记忆失败: {str(e)}")
            self.conn.rollback()
            raise
            
    def get_short_term_context(self, user_id: int, session_id: str, max_tokens: int = None) -> List[Dict]:
        """获取短期记忆上下文"""
        if max_tokens is None:
            max_tokens = self.MAX_CONTEXT_TOKENS
            
        try:
            sql = """
                SELECT role, content, token_count, created_at
                FROM short_term_memory
                WHERE user_id = %s AND session_id = %s
                ORDER BY context_window_position DESC
            """
            self.cursor.execute(sql, (user_id, session_id))
            rows = self.cursor.fetchall()
            
            # 从最新到最旧，直到达到 token 限制
            context = []
            total_tokens = 0
            for row in rows:
                if total_tokens + row['token_count'] > max_tokens:
                    break
                context.insert(0, {
                    'role': row['role'],
                    'content': row['content'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })
                total_tokens += row['token_count']
                
            return context
        except Exception as e:
            error(f"获取短期记忆上下文失败: {str(e)}")
            return []
            
    def _cleanup_short_term(self, user_id: int, session_id: str, keep_recent: int = 50):
        """清理过期的短期记忆，保留最近的 N 条"""
        try:
            sql = """
                DELETE FROM short_term_memory
                WHERE user_id = %s AND session_id = %s
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM short_term_memory
                        WHERE user_id = %s AND session_id = %s
                        ORDER BY context_window_position DESC
                        LIMIT %s
                    ) t
                )
            """
            self.cursor.execute(sql, (user_id, session_id, user_id, session_id, keep_recent))
            self.conn.commit()
        except Exception as e:
            warning(f"清理短期记忆失败: {str(e)}")
            
    # ==========================================
    # 情景记忆管理
    # ==========================================
    
    def add_episodic(self, user_id: int, episode_type: str, title: str, 
                     summary: str, content: str, context: Dict = None, 
                     emotions: Dict = None, importance: float = 0.5) -> int:
        """添加情景记忆"""
        try:
            sql = """
                INSERT INTO episodic_memory 
                (user_id, episode_type, title, summary, context, content, emotions, importance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (
                user_id, episode_type, title, summary,
                json.dumps(context, ensure_ascii=False) if context else None,
                content,
                json.dumps(emotions, ensure_ascii=False) if emotions else None,
                importance
            ))
            self.conn.commit()
            
            memory_id = self.cursor.lastrowid
            self._create_metadata('episodic', memory_id, user_id, importance)
            self._log_access(user_id, 'episodic', memory_id, 'write')
            
            return memory_id
        except Exception as e:
            error(f"添加情景记忆失败: {str(e)}")
            self.conn.rollback()
            raise
            
    def search_episodic(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """搜索情景记忆"""
        try:
            sql = """
                SELECT id, episode_type, title, summary, context, content, 
                       importance, access_count, created_at
                FROM episodic_memory
                WHERE user_id = %s 
                  AND (title LIKE %s OR summary LIKE %s OR content LIKE %s)
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """
            search_term = f"%{query}%"
            self.cursor.execute(sql, (user_id, search_term, search_term, search_term, limit))
            results = self.cursor.fetchall()
            
            # 更新访问计数
            for row in results:
                self._update_access('episodic', row['id'], user_id)
                
            return results
        except Exception as e:
            error(f"搜索情景记忆失败: {str(e)}")
            return []
            
    def get_recent_episodes(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取最近的情景记忆"""
        try:
            sql = """
                SELECT id, episode_type, title, summary, importance, created_at
                FROM episodic_memory
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            self.cursor.execute(sql, (user_id, limit))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取最近情景记忆失败: {str(e)}")
            return []
            
    # ==========================================
    # 语义记忆管理（事实知识）
    # ==========================================
    
    def add_semantic(self, user_id: int, fact_type: str, subject: str, 
                     predicate: str, object_val: str, confidence: float = 0.8,
                     source: str = "") -> int:
        """添加语义记忆（事实知识）"""
        try:
            # 检查是否存在冲突
            conflict = self._detect_conflict(user_id, subject, predicate, object_val)
            
            sql = """
                INSERT INTO semantic_memory 
                (user_id, fact_type, subject, predicate, object, confidence, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    object = VALUES(object),
                    confidence = VALUES(confidence),
                    source = VALUES(source),
                    access_count = access_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """
            self.cursor.execute(sql, (user_id, fact_type, subject, predicate, object_val, confidence, source))
            self.conn.commit()
            
            memory_id = self.cursor.lastrowid
            
            # 如果检测到冲突，记录冲突
            if conflict:
                self._record_conflict(user_id, 'fact_contradiction', 
                                     'semantic', conflict['id'], 'semantic', memory_id)
                                     
            self._create_metadata('semantic', memory_id, user_id, confidence)
            self._log_access(user_id, 'semantic', memory_id, 'write')
            
            return memory_id
        except Exception as e:
            error(f"添加语义记忆失败: {str(e)}")
            self.conn.rollback()
            raise
            
    def search_semantic(self, user_id: int, query: str, fact_type: str = None, 
                       limit: int = 10) -> List[Dict]:
        """搜索语义记忆"""
        try:
            conditions = ["user_id = %s", "(subject LIKE %s OR predicate LIKE %s OR object LIKE %s)"]
            params = [user_id, f"%{query}%", f"%{query}%", f"%{query}%"]
            
            if fact_type:
                conditions.append("fact_type = %s")
                params.append(fact_type)
                
            sql = f"""
                SELECT id, fact_type, subject, predicate, object, confidence, 
                       source, is_verified, access_count, created_at
                FROM semantic_memory
                WHERE {' AND '.join(conditions)}
                ORDER BY confidence DESC, access_count DESC
                LIMIT %s
            """
            params.append(limit)
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            
            # 更新访问计数
            for row in results:
                self._update_access('semantic', row['id'], user_id)
                
            return results
        except Exception as e:
            error(f"搜索语义记忆失败: {str(e)}")
            return []
            
    def get_facts_by_subject(self, user_id: int, subject: str) -> List[Dict]:
        """获取某个主题的所有事实"""
        try:
            sql = """
                SELECT id, fact_type, subject, predicate, object, confidence, created_at
                FROM semantic_memory
                WHERE user_id = %s AND subject = %s
                ORDER BY confidence DESC
            """
            self.cursor.execute(sql, (user_id, subject))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取主题事实失败: {str(e)}")
            return []
            
    def _detect_conflict(self, user_id: int, subject: str, predicate: str, object_val: str) -> Optional[Dict]:
        """检测事实冲突"""
        try:
            sql = """
                SELECT id, object, confidence
                FROM semantic_memory
                WHERE user_id = %s AND subject = %s AND predicate = %s AND object != %s
                ORDER BY confidence DESC
                LIMIT 1
            """
            self.cursor.execute(sql, (user_id, subject, predicate, object_val))
            return self.cursor.fetchone()
        except Exception as e:
            warning(f"检测冲突失败: {str(e)}")
            return None
            
    def _record_conflict(self, user_id: int, conflict_type: str,
                         old_type: str, old_id: int, new_type: str, new_id: int):
        """记录记忆冲突"""
        try:
            sql = """
                INSERT INTO memory_conflicts 
                (user_id, conflict_type, old_memory_type, old_memory_id, new_memory_type, new_memory_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (user_id, conflict_type, old_type, old_id, new_type, new_id))
            self.conn.commit()
        except Exception as e:
            warning(f"记录冲突失败: {str(e)}")
            
    # ==========================================
    # 实体记忆管理（KV + 图谱）
    # ==========================================
    
    def add_entity(self, user_id: int, entity_type: str, entity_name: str,
                   attributes: Dict = None, description: str = "", 
                   entity_alias: str = "", importance: float = 0.5) -> int:
        """添加实体记忆"""
        try:
            sql = """
                INSERT INTO entity_memory 
                (user_id, entity_type, entity_name, entity_alias, attributes, description, importance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    entity_alias = COALESCE(VALUES(entity_alias), entity_alias),
                    attributes = JSON_MERGE_PATCH(attributes, VALUES(attributes)),
                    description = COALESCE(NULLIF(VALUES(description), ''), description),
                    importance = GREATEST(importance, VALUES(importance)),
                    access_count = access_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """
            self.cursor.execute(sql, (
                user_id, entity_type, entity_name, entity_alias,
                json.dumps(attributes, ensure_ascii=False) if attributes else None,
                description, importance
            ))
            self.conn.commit()
            
            entity_id = self.cursor.lastrowid
            self._create_metadata('entity', entity_id, user_id, importance)
            self._log_access(user_id, 'entity', entity_id, 'write')
            
            return entity_id
        except Exception as e:
            error(f"添加实体记忆失败: {str(e)}")
            self.conn.rollback()
            raise
            
    def add_relation(self, user_id: int, source_entity_id: int, target_entity_id: int,
                     relation_type: str, relation_label: str = "", 
                     weight: float = 1.0, context: str = "") -> int:
        """添加实体关系"""
        try:
            sql = """
                INSERT INTO entity_relations 
                (user_id, source_entity_id, target_entity_id, relation_type, relation_label, weight, context)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    weight = GREATEST(weight, VALUES(weight)),
                    context = COALESCE(NULLIF(VALUES(context), ''), context),
                    updated_at = CURRENT_TIMESTAMP
            """
            self.cursor.execute(sql, (
                user_id, source_entity_id, target_entity_id,
                relation_type, relation_label, weight, context
            ))
            self.conn.commit()
            
            relation_id = self.cursor.lastrowid
            self._create_metadata('relation', relation_id, user_id, weight)
            
            return relation_id
        except Exception as e:
            error(f"添加实体关系失败: {str(e)}")
            self.conn.rollback()
            raise
            
    def search_entities(self, user_id: int, query: str, entity_type: str = None,
                       limit: int = 10) -> List[Dict]:
        """搜索实体"""
        try:
            conditions = ["user_id = %s", "(entity_name LIKE %s OR entity_alias LIKE %s OR description LIKE %s)"]
            params = [user_id, f"%{query}%", f"%{query}%", f"%{query}%"]
            
            if entity_type:
                conditions.append("entity_type = %s")
                params.append(entity_type)
                
            sql = f"""
                SELECT id, entity_type, entity_name, entity_alias, attributes, 
                       description, importance, access_count, created_at
                FROM entity_memory
                WHERE {' AND '.join(conditions)}
                ORDER BY importance DESC, access_count DESC
                LIMIT %s
            """
            params.append(limit)
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            
            # 更新访问计数
            for row in results:
                self._update_access('entity', row['id'], user_id)
                # 解析 JSON 字段
                if row.get('attributes'):
                    row['attributes'] = json.loads(row['attributes']) if isinstance(row['attributes'], str) else row['attributes']
                    
            return results
        except Exception as e:
            error(f"搜索实体失败: {str(e)}")
            return []
            
    def get_entity_relations(self, user_id: int, entity_id: int, direction: str = 'both') -> List[Dict]:
        """获取实体的关系"""
        try:
            relations = []
            
            if direction in ('out', 'both'):
                sql = """
                    SELECT er.*, em.entity_name as target_name, em.entity_type as target_type
                    FROM entity_relations er
                    JOIN entity_memory em ON er.target_entity_id = em.id
                    WHERE er.source_entity_id = %s AND er.user_id = %s
                """
                self.cursor.execute(sql, (entity_id, user_id))
                out_relations = self.cursor.fetchall()
                for r in out_relations:
                    r['direction'] = 'out'
                relations.extend(out_relations)
                
            if direction in ('in', 'both'):
                sql = """
                    SELECT er.*, em.entity_name as source_name, em.entity_type as source_type
                    FROM entity_relations er
                    JOIN entity_memory em ON er.source_entity_id = em.id
                    WHERE er.target_entity_id = %s AND er.user_id = %s
                """
                self.cursor.execute(sql, (entity_id, user_id))
                in_relations = self.cursor.fetchall()
                for r in in_relations:
                    r['direction'] = 'in'
                relations.extend(in_relations)
                
            return relations
        except Exception as e:
            error(f"获取实体关系失败: {str(e)}")
            return []
            
    def get_entity_graph(self, user_id: int, center_entity_id: int, depth: int = 2) -> Dict:
        """获取实体图谱（BFS 遍历）"""
        try:
            visited = set()
            nodes = []
            edges = []
            queue = [(center_entity_id, 0)]
            
            while queue:
                entity_id, current_depth = queue.pop(0)
                
                if entity_id in visited or current_depth > depth:
                    continue
                    
                visited.add(entity_id)
                
                # 获取实体信息
                sql = "SELECT * FROM entity_memory WHERE id = %s AND user_id = %s"
                self.cursor.execute(sql, (entity_id, user_id))
                entity = self.cursor.fetchone()
                
                if entity:
                    if entity.get('attributes'):
                        entity['attributes'] = json.loads(entity['attributes']) if isinstance(entity['attributes'], str) else entity['attributes']
                    nodes.append(entity)
                    
                    # 获取关系
                    relations = self.get_entity_relations(user_id, entity_id, 'both')
                    for rel in relations:
                        target_id = rel.get('target_entity_id') if rel['direction'] == 'out' else rel.get('source_entity_id')
                        if target_id and target_id not in visited:
                            queue.append((target_id, current_depth + 1))
                            
                        edges.append({
                            'source': rel.get('source_entity_id'),
                            'target': rel.get('target_entity_id'),
                            'relation': rel.get('relation_type'),
                            'label': rel.get('relation_label'),
                            'weight': rel.get('weight')
                        })
                        
            return {'nodes': nodes, 'edges': edges}
        except Exception as e:
            error(f"获取实体图谱失败: {str(e)}")
            return {'nodes': [], 'edges': []}
            
    # ==========================================
    # 遗忘机制
    # ==========================================
    
    def _create_metadata(self, memory_type: str, memory_id: int, user_id: int, importance: float):
        """创建记忆元数据"""
        try:
            sql = """
                INSERT INTO memory_metadata 
                (memory_type, memory_id, user_id, importance, decay_rate, last_accessed_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            # 重要性越高，衰减越慢
            decay_rate = self.DEFAULT_DECAY_RATE * (1 - importance * 0.5)
            self.cursor.execute(sql, (memory_type, memory_id, user_id, importance, decay_rate))
            self.conn.commit()
        except Exception as e:
            warning(f"创建记忆元数据失败: {str(e)}")
            
    def _update_access(self, memory_type: str, memory_id: int, user_id: int):
        """更新记忆访问记录"""
        try:
            # 更新原表
            table_map = {
                'episodic': 'episodic_memory',
                'semantic': 'semantic_memory',
                'entity': 'entity_memory'
            }
            table = table_map.get(memory_type)
            if table:
                sql = f"""
                    UPDATE {table} 
                    SET access_count = access_count + 1, last_accessed_at = NOW()
                    WHERE id = %s
                """
                self.cursor.execute(sql, (memory_id,))
                
            # 更新元数据
            sql = """
                UPDATE memory_metadata 
                SET access_count = access_count + 1, last_accessed_at = NOW(),
                    importance = LEAST(1.0, importance + %s)
                WHERE memory_type = %s AND memory_id = %s AND user_id = %s
            """
            self.cursor.execute(sql, (self.REINFORCEMENT_BOOST * 0.1, memory_type, memory_id, user_id))
            self.conn.commit()
        except Exception as e:
            warning(f"更新访问记录失败: {str(e)}")
            
    def _log_access(self, user_id: int, memory_type: str, memory_id: int, access_type: str):
        """记录访问日志"""
        try:
            sql = """
                INSERT INTO memory_access_log (user_id, memory_type, memory_id, access_type)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(sql, (user_id, memory_type, memory_id, access_type))
            self.conn.commit()
        except Exception as e:
            warning(f"记录访问日志失败: {str(e)}")
            
    def apply_forgetting_curve(self, user_id: int = None):
        """应用遗忘曲线，衰减记忆重要性"""
        try:
            # 获取所有记忆元数据
            sql = """
                SELECT id, memory_type, memory_id, user_id, importance, 
                       decay_rate, last_accessed_at, access_count
                FROM memory_metadata
                WHERE is_forgotten = FALSE
            """
            params = []
            if user_id:
                sql += " AND user_id = %s"
                params.append(user_id)
                
            self.cursor.execute(sql, params)
            memories = self.cursor.fetchall()
            
            forgotten_count = 0
            reinforced_count = 0
            
            for mem in memories:
                # 计算时间衰减
                if mem['last_accessed_at']:
                    days_since_access = (datetime.now() - mem['last_accessed_at']).total_seconds() / 86400
                else:
                    days_since_access = 30  # 默认 30 天
                    
                # 遗忘曲线公式：R = e^(-t/S)
                # R: 保留率, t: 时间, S: 稳定性
                stability = max(1, mem['access_count'] * 2)  # 访问次数越多，稳定性越高
                retention = np.exp(-days_since_access / stability)
                
                # 计算新的重要性
                new_importance = mem['importance'] * retention
                
                if new_importance < self.FORGET_THRESHOLD:
                    # 标记为遗忘
                    sql = """
                        UPDATE memory_metadata 
                        SET is_forgotten = TRUE, forgotten_at = NOW(), importance = %s
                        WHERE id = %s
                    """
                    self.cursor.execute(sql, (new_importance, mem['id']))
                    forgotten_count += 1
                else:
                    # 更新重要性
                    sql = """
                        UPDATE memory_metadata 
                        SET importance = %s
                        WHERE id = %s
                    """
                    self.cursor.execute(sql, (new_importance, mem['id']))
                    reinforced_count += 1
                    
            self.conn.commit()
            info(f"遗忘曲线应用完成: 遗忘 {forgotten_count} 条, 保留 {reinforced_count} 条")
            
            return {'forgotten': forgotten_count, 'reinforced': reinforced_count}
        except Exception as e:
            error(f"应用遗忘曲线失败: {str(e)}")
            self.conn.rollback()
            return {'forgotten': 0, 'reinforced': 0}
            
    def reinforce_memory(self, memory_type: str, memory_id: int, user_id: int, boost: float = None):
        """强化记忆"""
        if boost is None:
            boost = self.REINFORCEMENT_BOOST
            
        try:
            sql = """
                UPDATE memory_metadata 
                SET importance = LEAST(1.0, importance + %s),
                    reinforcement_count = reinforcement_count + 1,
                    access_count = access_count + 1,
                    last_accessed_at = NOW()
                WHERE memory_type = %s AND memory_id = %s AND user_id = %s
            """
            self.cursor.execute(sql, (boost, memory_type, memory_id, user_id))
            self.conn.commit()
            
            self._log_access(user_id, memory_type, memory_id, 'reinforce')
        except Exception as e:
            warning(f"强化记忆失败: {str(e)}")
            
    # ==========================================
    # 冲突修正
    # ==========================================
    
    def get_pending_conflicts(self, user_id: int) -> List[Dict]:
        """获取待解决的冲突"""
        try:
            sql = """
                SELECT mc.*, 
                       om.subject as old_subject, om.predicate as old_predicate, om.object as old_object,
                       nm.subject as new_subject, nm.predicate as new_predicate, nm.object as new_object
                FROM memory_conflicts mc
                LEFT JOIN semantic_memory om ON mc.old_memory_id = om.id AND mc.old_memory_type = 'semantic'
                LEFT JOIN semantic_memory nm ON mc.new_memory_id = nm.id AND mc.new_memory_type = 'semantic'
                WHERE mc.user_id = %s AND mc.resolved = FALSE
                ORDER BY mc.created_at DESC
            """
            self.cursor.execute(sql, (user_id,))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取待解决冲突失败: {str(e)}")
            return []
            
    def resolve_conflict(self, conflict_id: int, strategy: str, user_id: int) -> bool:
        """解决冲突"""
        try:
            # 获取冲突信息
            sql = "SELECT * FROM memory_conflicts WHERE id = %s AND user_id = %s"
            self.cursor.execute(sql, (conflict_id, user_id))
            conflict = self.cursor.fetchone()
            
            if not conflict:
                return False
                
            resolution_result = {}
            
            if strategy == 'keep_old':
                # 保留旧记忆，删除新记忆
                self._delete_memory(conflict['new_memory_type'], conflict['new_memory_id'])
                resolution_result = {'action': 'kept_old', 'deleted_new': conflict['new_memory_id']}
                
            elif strategy == 'keep_new':
                # 保留新记忆，删除旧记忆
                self._delete_memory(conflict['old_memory_type'], conflict['old_memory_id'])
                resolution_result = {'action': 'kept_new', 'deleted_old': conflict['old_memory_id']}
                
            elif strategy == 'merge':
                # 合并记忆（保留两者，标记为已验证）
                self._verify_memory(conflict['old_memory_type'], conflict['old_memory_id'])
                self._verify_memory(conflict['new_memory_type'], conflict['new_memory_id'])
                resolution_result = {'action': 'merged', 'verified_both': True}
                
            # 更新冲突状态
            sql = """
                UPDATE memory_conflicts 
                SET resolved = TRUE, resolved_at = NOW(), 
                    resolution_strategy = %s, resolution_result = %s
                WHERE id = %s
            """
            self.cursor.execute(sql, (strategy, json.dumps(resolution_result), conflict_id))
            self.conn.commit()
            
            return True
        except Exception as e:
            error(f"解决冲突失败: {str(e)}")
            self.conn.rollback()
            return False
            
    def _delete_memory(self, memory_type: str, memory_id: int):
        """删除记忆"""
        table_map = {
            'episodic': 'episodic_memory',
            'semantic': 'semantic_memory',
            'entity': 'entity_memory'
        }
        table = table_map.get(memory_type)
        if table:
            sql = f"DELETE FROM {table} WHERE id = %s"
            self.cursor.execute(sql, (memory_id,))
            
            # 删除元数据
            sql = "DELETE FROM memory_metadata WHERE memory_type = %s AND memory_id = %s"
            self.cursor.execute(sql, (memory_type, memory_id))
            
    def _verify_memory(self, memory_type: str, memory_id: int):
        """标记记忆为已验证"""
        if memory_type == 'semantic':
            sql = "UPDATE semantic_memory SET is_verified = TRUE WHERE id = %s"
            self.cursor.execute(sql, (memory_id,))
            
    # ==========================================
    # 统计与清理
    # ==========================================
    
    def get_memory_stats(self, user_id: int) -> Dict:
        """获取记忆统计信息"""
        try:
            stats = {}
            
            # 短期记忆数量
            sql = "SELECT COUNT(*) as cnt FROM short_term_memory WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            stats['short_term'] = self.cursor.fetchone()['cnt']
            
            # 情景记忆数量
            sql = "SELECT COUNT(*) as cnt FROM episodic_memory WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            stats['episodic'] = self.cursor.fetchone()['cnt']
            
            # 语义记忆数量
            sql = "SELECT COUNT(*) as cnt FROM semantic_memory WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            stats['semantic'] = self.cursor.fetchone()['cnt']
            
            # 实体记忆数量
            sql = "SELECT COUNT(*) as cnt FROM entity_memory WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            stats['entity'] = self.cursor.fetchone()['cnt']
            
            # 关系数量
            sql = "SELECT COUNT(*) as cnt FROM entity_relations WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            stats['relations'] = self.cursor.fetchone()['cnt']
            
            # 待解决冲突数量
            sql = "SELECT COUNT(*) as cnt FROM memory_conflicts WHERE user_id = %s AND resolved = FALSE"
            self.cursor.execute(sql, (user_id,))
            stats['pending_conflicts'] = self.cursor.fetchone()['cnt']
            
            # 已遗忘记忆数量
            sql = "SELECT COUNT(*) as cnt FROM memory_metadata WHERE user_id = %s AND is_forgotten = TRUE"
            self.cursor.execute(sql, (user_id,))
            stats['forgotten'] = self.cursor.fetchone()['cnt']
            
            return stats
        except Exception as e:
            error(f"获取记忆统计失败: {str(e)}")
            return {}
            
    def cleanup_forgotten_memories(self, user_id: int = None, days: int = 30):
        """清理已被遗忘超过指定天数的记忆"""
        try:
            # 获取要清理的记忆
            sql = """
                SELECT memory_type, memory_id 
                FROM memory_metadata
                WHERE is_forgotten = TRUE 
                  AND forgotten_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            params = [days]
            if user_id:
                sql += " AND user_id = %s"
                params.append(user_id)
                
            self.cursor.execute(sql, params)
            to_cleanup = self.cursor.fetchall()
            
            deleted_count = 0
            for mem in to_cleanup:
                self._delete_memory(mem['memory_type'], mem['memory_id'])
                deleted_count += 1
                
            self.conn.commit()
            info(f"清理遗忘记忆完成: 删除 {deleted_count} 条")
            
            return deleted_count
        except Exception as e:
            error(f"清理遗忘记忆失败: {str(e)}")
            self.conn.rollback()
            return 0


# 全局单例
memory_service = MemoryService()
