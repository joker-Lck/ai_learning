"""
无限长时记忆架构 - 记忆管理服务
支持短期记忆、情景记忆、语义记忆、实体记忆、遗忘机制、冲突修正

架构：
  MemoryDB          — 通用数据库操作基类
  ├── ShortTermHandler   — 短期记忆
  ├── EpisodicHandler    — 情景记忆
  ├── SemanticHandler    — 语义记忆（事实知识）
  ├── EntityHandler      — 实体记忆（KV + 图谱）
  ├── ForgettingHandler  — 遗忘机制
  └── ConflictHandler    — 冲突修正
  MemoryService     — 门面类，组合以上 Handler
"""

import json
import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import threading
from data.config import get_memory_db_path
from core.logger import info, error, warning


# ==========================================
# 数据库基类
# ==========================================

class MemoryDB:
    """通用数据库操作基类，封装连接、执行、提交、回滚"""

    # 表名映射（memory_type → 物理表）
    TABLE_MAP = {
        'short_term': 'short_term_memory',
        'episodic':   'episodic_memory',
        'semantic':   'semantic_memory',
        'entity':     'entity_memory',
        'relation':   'entity_relations',
    }

    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    # ── 基础执行 ──────────────────────────────

    def _execute(self, sql: str, params: tuple = None):
        """执行 SQL（不提交）"""
        self.cursor.execute(sql, params or ())

    def _execute_commit(self, sql: str, params: tuple = None):
        """执行 SQL 并提交"""
        self._execute(sql, params)
        self.conn.commit()

    def _fetchone(self, sql: str, params: tuple = None) -> Optional[Dict]:
        self._execute(sql, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def _fetchall(self, sql: str, params: tuple = None) -> List[Dict]:
        self._execute(sql, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def _count(self, table: str, user_id: int, extra: str = "") -> int:
        sql = f"SELECT COUNT(*) as cnt FROM {table} WHERE user_id = ? {extra}"
        return self._fetchone(sql, (user_id,))['cnt']

    def _last_id(self) -> int:
        return self.cursor.lastrowid

    def _table_for(self, memory_type: str) -> str:
        return self.TABLE_MAP[memory_type]


# ==========================================
# 短期记忆
# ==========================================

class ShortTermHandler(MemoryDB):
    """Token 级上下文窗口"""

    MAX_CONTEXT_TOKENS = 4000
    KEEP_RECENT = 50

    def add(self, user_id: int, session_id: str, role: str, content: str) -> int:
        token_count = len(content) // 4
        sql = """
            INSERT INTO short_term_memory
            (user_id, session_id, role, content, token_count, context_window_position)
            VALUES (?, ?, ?, ?, ?,
                (SELECT COALESCE(MAX(t.context_window_position), 0) + 1
                 FROM (SELECT context_window_position FROM short_term_memory
                       WHERE user_id = ? AND session_id = ?) t))
        """
        self._execute_commit(sql, (user_id, session_id, role, content, token_count, user_id, session_id))
        memory_id = self._last_id()
        self._cleanup(user_id, session_id)
        return memory_id

    def get_context(self, user_id: int, session_id: str,
                    max_tokens: int = None) -> List[Dict]:
        max_tokens = max_tokens or self.MAX_CONTEXT_TOKENS
        rows = self._fetchall(
            "SELECT role, content, token_count, created_at "
            "FROM short_term_memory WHERE user_id = ? AND session_id = ? "
            "ORDER BY context_window_position DESC",
            (user_id, session_id)
        )
        context, total = [], 0
        for row in rows:
            if total + row['token_count'] > max_tokens:
                break
            context.insert(0, {
                'role': row['role'],
                'content': row['content'],
                'created_at': row['created_at'],
            })
            total += row['token_count']
        return context

    def _cleanup(self, user_id: int, session_id: str):
        sql = """
            DELETE FROM short_term_memory
            WHERE user_id = ? AND session_id = ?
            AND id NOT IN (
                SELECT id FROM short_term_memory
                WHERE user_id = ? AND session_id = ?
                ORDER BY context_window_position DESC LIMIT ?
            )
        """
        try:
            self._execute_commit(sql, (user_id, session_id, user_id, session_id, self.KEEP_RECENT))
        except Exception as e:
            warning(f"清理短期记忆失败: {e}")

    def count(self, user_id: int) -> int:
        return self._count('short_term_memory', user_id)


# ==========================================
# 情景记忆
# ==========================================

class EpisodicHandler(MemoryDB):
    """对话事件 / 学习场景"""

    def add(self, user_id: int, episode_type: str, title: str,
            summary: str, content: str, context: Dict = None,
            emotions: Dict = None, importance: float = 0.5) -> int:
        sql = """
            INSERT INTO episodic_memory
            (user_id, episode_type, title, summary, context, content, emotions, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self._execute_commit(sql, (
            user_id, episode_type, title, summary,
            json.dumps(context, ensure_ascii=False) if context else None,
            content,
            json.dumps(emotions, ensure_ascii=False) if emotions else None,
            importance
        ))
        return self._last_id()

    def search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        term = f"%{query}%"
        return self._fetchall(
            "SELECT id, episode_type, title, summary, context, content, "
            "importance, access_count, created_at "
            "FROM episodic_memory "
            "WHERE user_id = ? AND (title LIKE ? OR summary LIKE ? OR content LIKE ?) "
            "ORDER BY importance DESC, created_at DESC LIMIT ?",
            (user_id, term, term, term, limit)
        )

    def recent(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self._fetchall(
            "SELECT id, episode_type, title, summary, importance, created_at "
            "FROM episodic_memory WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )

    def count(self, user_id: int) -> int:
        return self._count('episodic_memory', user_id)


# ==========================================
# 语义记忆（SPO 三元组）
# ==========================================

class SemanticHandler(MemoryDB):
    """事实知识存储，支持冲突检测"""

    def add(self, user_id: int, fact_type: str, subject: str,
            predicate: str, object_val: str, confidence: float = 0.8,
            source: str = "") -> int:
        conflict = self._detect_conflict(user_id, subject, predicate, object_val)

        sql = """
            INSERT INTO semantic_memory
            (user_id, fact_type, subject, predicate, object, confidence, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, subject, predicate) DO UPDATE SET
                object = excluded.object, confidence = excluded.confidence,
                source = excluded.source, access_count = access_count + 1,
                updated_at = CURRENT_TIMESTAMP
        """
        self._execute_commit(sql, (user_id, fact_type, subject, predicate, object_val, confidence, source))
        memory_id = self._last_id()

        if conflict:
            self._record_conflict(user_id, 'fact_contradiction',
                                  'semantic', conflict['id'], 'semantic', memory_id)
        return memory_id

    def search(self, user_id: int, query: str, fact_type: str = None,
               limit: int = 10) -> List[Dict]:
        conditions = ["user_id = ?", "(subject LIKE ? OR predicate LIKE ? OR object LIKE ?)"]
        params: list = [user_id, f"%{query}%", f"%{query}%", f"%{query}%"]
        if fact_type:
            conditions.append("fact_type = ?")
            params.append(fact_type)
        params.append(limit)
        return self._fetchall(
            f"SELECT id, fact_type, subject, predicate, object, confidence, "
            f"source, is_verified, access_count, created_at "
            f"FROM semantic_memory WHERE {' AND '.join(conditions)} "
            f"ORDER BY confidence DESC, access_count DESC LIMIT ?",
            tuple(params)
        )

    def get_by_subject(self, user_id: int, subject: str) -> List[Dict]:
        return self._fetchall(
            "SELECT id, fact_type, subject, predicate, object, confidence, created_at "
            "FROM semantic_memory WHERE user_id = ? AND subject = ? "
            "ORDER BY confidence DESC",
            (user_id, subject)
        )

    def _detect_conflict(self, user_id: int, subject: str,
                         predicate: str, object_val: str) -> Optional[Dict]:
        return self._fetchone(
            "SELECT id, object, confidence FROM semantic_memory "
            "WHERE user_id = ? AND subject = ? AND predicate = ? AND object != ? "
            "ORDER BY confidence DESC LIMIT 1",
            (user_id, subject, predicate, object_val)
        )

    def _record_conflict(self, user_id: int, conflict_type: str,
                         old_type: str, old_id: int, new_type: str, new_id: int):
        try:
            self._execute_commit(
                "INSERT INTO memory_conflicts "
                "(user_id, conflict_type, old_memory_type, old_memory_id, new_memory_type, new_memory_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, conflict_type, old_type, old_id, new_type, new_id)
            )
        except Exception as e:
            warning(f"记录冲突失败: {e}")

    def count(self, user_id: int) -> int:
        return self._count('semantic_memory', user_id)


# ==========================================
# 实体记忆（KV + 图谱）
# ==========================================

class EntityHandler(MemoryDB):
    """实体画像存储 + 知识图谱"""

    def add(self, user_id: int, entity_type: str, entity_name: str,
            attributes: Dict = None, description: str = "",
            entity_alias: str = "", importance: float = 0.5) -> int:
        # 先查询已有记录，用于应用层 JSON 合并
        existing = self._fetchone(
            "SELECT id, attributes, importance FROM entity_memory "
            "WHERE user_id = ? AND entity_name = ?",
            (user_id, entity_name)
        )
        if existing:
            # 应用层合并 attributes
            old_attrs = {}
            if existing['attributes']:
                old_attrs = json.loads(existing['attributes']) if isinstance(existing['attributes'], str) else existing['attributes']
            if attributes:
                old_attrs.update(attributes)
            merged_attrs = json.dumps(old_attrs, ensure_ascii=False) if old_attrs else None
            new_importance = max(existing['importance'], importance)
            sql = """
                UPDATE entity_memory SET
                    entity_alias = COALESCE(?, entity_alias),
                    attributes = ?,
                    description = COALESCE(NULLIF(?, ''), description),
                    importance = ?,
                    access_count = access_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self._execute_commit(sql, (entity_alias or None, merged_attrs, description, new_importance, existing['id']))
            return existing['id']
        else:
            sql = """
                INSERT INTO entity_memory
                (user_id, entity_type, entity_name, entity_alias, attributes, description, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self._execute_commit(sql, (
                user_id, entity_type, entity_name, entity_alias,
                json.dumps(attributes, ensure_ascii=False) if attributes else None,
                description, importance
            ))
            return self._last_id()

    def add_relation(self, user_id: int, source_id: int, target_id: int,
                     relation_type: str, label: str = "",
                     weight: float = 1.0, context: str = "") -> int:
        existing = self._fetchone(
            "SELECT id, weight FROM entity_relations "
            "WHERE user_id = ? AND source_entity_id = ? AND target_entity_id = ? AND relation_type = ?",
            (user_id, source_id, target_id, relation_type)
        )
        if existing:
            new_weight = max(existing['weight'], weight)
            sql = """
                UPDATE entity_relations SET
                    weight = ?,
                    context = COALESCE(NULLIF(?, ''), context),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            self._execute_commit(sql, (new_weight, context or None, existing['id']))
            return existing['id']
        else:
            sql = """
                INSERT INTO entity_relations
                (user_id, source_entity_id, target_entity_id, relation_type, relation_label, weight, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self._execute_commit(sql, (user_id, source_id, target_id, relation_type, label, weight, context))
            return self._last_id()

    def search(self, user_id: int, query: str, entity_type: str = None,
               limit: int = 10) -> List[Dict]:
        conditions = ["user_id = ?", "(entity_name LIKE ? OR entity_alias LIKE ? OR description LIKE ?)"]
        params: list = [user_id, f"%{query}%", f"%{query}%", f"%{query}%"]
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)
        params.append(limit)
        rows = self._fetchall(
            f"SELECT id, entity_type, entity_name, entity_alias, attributes, "
            f"description, importance, access_count, created_at "
            f"FROM entity_memory WHERE {' AND '.join(conditions)} "
            f"ORDER BY importance DESC, access_count DESC LIMIT ?",
            tuple(params)
        )
        for row in rows:
            if row.get('attributes') and isinstance(row['attributes'], str):
                row['attributes'] = json.loads(row['attributes'])
        return rows

    def get_relations(self, user_id: int, entity_id: int,
                      direction: str = 'both') -> List[Dict]:
        relations = []
        if direction in ('out', 'both'):
            rows = self._fetchall(
                "SELECT er.*, em.entity_name as target_name, em.entity_type as target_type "
                "FROM entity_relations er JOIN entity_memory em ON er.target_entity_id = em.id "
                "WHERE er.source_entity_id = ? AND er.user_id = ?",
                (entity_id, user_id)
            )
            for r in rows:
                r['direction'] = 'out'
            relations.extend(rows)
        if direction in ('in', 'both'):
            rows = self._fetchall(
                "SELECT er.*, em.entity_name as source_name, em.entity_type as source_type "
                "FROM entity_relations er JOIN entity_memory em ON er.source_entity_id = em.id "
                "WHERE er.target_entity_id = ? AND er.user_id = ?",
                (entity_id, user_id)
            )
            for r in rows:
                r['direction'] = 'in'
            relations.extend(rows)
        return relations

    def get_graph(self, user_id: int, center_id: int, depth: int = 2) -> Dict:
        visited, nodes, edges, queue = set(), [], [], [(center_id, 0)]
        while queue:
            eid, d = queue.pop(0)
            if eid in visited or d > depth:
                continue
            visited.add(eid)
            entity = self._fetchone(
                "SELECT * FROM entity_memory WHERE id = ? AND user_id = ?",
                (eid, user_id)
            )
            if not entity:
                continue
            if entity.get('attributes') and isinstance(entity['attributes'], str):
                entity['attributes'] = json.loads(entity['attributes'])
            nodes.append(entity)
            for rel in self.get_relations(user_id, eid, 'both'):
                tid = rel.get('target_entity_id') if rel['direction'] == 'out' else rel.get('source_entity_id')
                if tid and tid not in visited:
                    queue.append((tid, d + 1))
                edges.append({
                    'source': rel.get('source_entity_id'),
                    'target': rel.get('target_entity_id'),
                    'relation': rel.get('relation_type'),
                    'label': rel.get('relation_label'),
                    'weight': rel.get('weight'),
                })
        return {'nodes': nodes, 'edges': edges}

    def count(self, user_id: int) -> int:
        return self._count('entity_memory', user_id)

    def relation_count(self, user_id: int) -> int:
        return self._count('entity_relations', user_id)


# ==========================================
# 遗忘机制
# ==========================================

class ForgettingHandler(MemoryDB):
    """艾宾浩斯遗忘曲线 + 记忆强化"""

    DEFAULT_DECAY_RATE = 0.1
    FORGET_THRESHOLD  = 0.2
    REINFORCE_BOOST   = 0.15

    def create_metadata(self, memory_type: str, memory_id: int,
                        user_id: int, importance: float):
        decay_rate = self.DEFAULT_DECAY_RATE * (1 - importance * 0.5)
        try:
            self._execute_commit(
                "INSERT INTO memory_metadata "
                "(memory_type, memory_id, user_id, importance, decay_rate, last_accessed_at) "
                "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (memory_type, memory_id, user_id, importance, decay_rate)
            )
        except Exception as e:
            warning(f"创建记忆元数据失败: {e}")

    def update_access(self, memory_type: str, memory_id: int, user_id: int):
        try:
            table = self._table_for(memory_type)
            self._execute(
                f"UPDATE {table} SET access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (memory_id,)
            )
            self._execute(
                "UPDATE memory_metadata SET access_count = access_count + 1, "
                "last_accessed_at = CURRENT_TIMESTAMP, importance = MIN(1.0, importance + ?) "
                "WHERE memory_type = ? AND memory_id = ? AND user_id = ?",
                (self.REINFORCE_BOOST * 0.1, memory_type, memory_id, user_id)
            )
            self.conn.commit()
        except Exception as e:
            warning(f"更新访问记录失败: {e}")

    def log_access(self, user_id: int, memory_type: str,
                   memory_id: int, access_type: str):
        try:
            self._execute_commit(
                "INSERT INTO memory_access_log (user_id, memory_type, memory_id, access_type) "
                "VALUES (?, ?, ?, ?)",
                (user_id, memory_type, memory_id, access_type)
            )
        except Exception as e:
            warning(f"记录访问日志失败: {e}")

    def apply_curve(self, user_id: int = None) -> Dict[str, int]:
        """应用遗忘曲线，返回 {forgotten, reinforced}"""
        try:
            sql = "SELECT id, memory_type, memory_id, user_id, importance, decay_rate, last_accessed_at, access_count FROM memory_metadata WHERE is_forgotten = 0"
            params = []
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            memories = self._fetchall(sql, tuple(params) if params else None)

            forgotten = reinforced = 0
            for mem in memories:
                last_accessed = mem['last_accessed_at']
                if isinstance(last_accessed, str):
                    last_accessed = datetime.fromisoformat(last_accessed)
                days = (datetime.now() - last_accessed).total_seconds() / 86400 if last_accessed else 30
                stability = max(1, (mem['access_count'] or 0) * 2)
                retention = float(np.exp(-days / stability))
                new_imp = (mem['importance'] or 0) * retention

                if new_imp < self.FORGET_THRESHOLD:
                    self._execute("UPDATE memory_metadata SET is_forgotten = 1, forgotten_at = CURRENT_TIMESTAMP, importance = ? WHERE id = ?", (new_imp, mem['id']))
                    forgotten += 1
                else:
                    self._execute("UPDATE memory_metadata SET importance = ? WHERE id = ?", (new_imp, mem['id']))
                    reinforced += 1

            self.conn.commit()
            info(f"遗忘曲线应用完成: 遗忘 {forgotten} 条, 保留 {reinforced} 条")
            return {'forgotten': forgotten, 'reinforced': reinforced}
        except Exception as e:
            error(f"应用遗忘曲线失败: {e}")
            self.conn.rollback()
            return {'forgotten': 0, 'reinforced': 0}

    def reinforce(self, memory_type: str, memory_id: int, user_id: int,
                  boost: float = None):
        boost = boost or self.REINFORCE_BOOST
        try:
            self._execute_commit(
                "UPDATE memory_metadata SET importance = MIN(1.0, importance + ?), "
                "reinforcement_count = reinforcement_count + 1, "
                "access_count = access_count + 1, last_accessed_at = CURRENT_TIMESTAMP "
                "WHERE memory_type = ? AND memory_id = ? AND user_id = ?",
                (boost, memory_type, memory_id, user_id)
            )
        except Exception as e:
            warning(f"强化记忆失败: {e}")

    def forgotten_count(self, user_id: int) -> int:
        return self._count('memory_metadata', user_id, "AND is_forgotten = 1")

    def cleanup(self, user_id: int = None, days: int = 30) -> int:
        """清理超过 N 天的遗忘记忆"""
        try:
            sql = "SELECT memory_type, memory_id FROM memory_metadata WHERE is_forgotten = 1 AND forgotten_at < datetime('now', '-' || ? || ' days')"
            params: list = [days]
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            to_clean = self._fetchall(sql, tuple(params))

            deleted = 0
            for mem in to_clean:
                table = self._table_for(mem['memory_type'])
                self._execute(f"DELETE FROM {table} WHERE id = ?", (mem['memory_id'],))
                self._execute("DELETE FROM memory_metadata WHERE memory_type = ? AND memory_id = ?",
                              (mem['memory_type'], mem['memory_id']))
                deleted += 1
            self.conn.commit()
            info(f"清理遗忘记忆完成: 删除 {deleted} 条")
            return deleted
        except Exception as e:
            error(f"清理遗忘记忆失败: {e}")
            self.conn.rollback()
            return 0


# ==========================================
# 冲突修正
# ==========================================

class ConflictHandler(MemoryDB):
    """记忆冲突检测与修正"""

    def get_pending(self, user_id: int) -> List[Dict]:
        return self._fetchall(
            "SELECT mc.*, "
            "om.subject as old_subject, om.predicate as old_predicate, om.object as old_object, "
            "nm.subject as new_subject, nm.predicate as new_predicate, nm.object as new_object "
            "FROM memory_conflicts mc "
            "LEFT JOIN semantic_memory om ON mc.old_memory_id = om.id AND mc.old_memory_type = 'semantic' "
            "LEFT JOIN semantic_memory nm ON mc.new_memory_id = nm.id AND mc.new_memory_type = 'semantic' "
            "WHERE mc.user_id = ? AND mc.resolved = 0 ORDER BY mc.created_at DESC",
            (user_id,)
        )

    def pending_count(self, user_id: int) -> int:
        return self._count('memory_conflicts', user_id, "AND resolved = 0")

    def resolve(self, conflict_id: int, strategy: str, user_id: int) -> bool:
        try:
            conflict = self._fetchone(
                "SELECT * FROM memory_conflicts WHERE id = ? AND user_id = ?",
                (conflict_id, user_id)
            )
            if not conflict:
                return False

            result = {}
            if strategy == 'keep_old':
                self._delete_memory(conflict['new_memory_type'], conflict['new_memory_id'])
                result = {'action': 'kept_old'}
            elif strategy == 'keep_new':
                self._delete_memory(conflict['old_memory_type'], conflict['old_memory_id'])
                result = {'action': 'kept_new'}
            elif strategy == 'merge':
                self._verify(conflict['old_memory_type'], conflict['old_memory_id'])
                self._verify(conflict['new_memory_type'], conflict['new_memory_id'])
                result = {'action': 'merged'}

            self._execute_commit(
                "UPDATE memory_conflicts SET resolved = 1, resolved_at = CURRENT_TIMESTAMP, "
                "resolution_strategy = ?, resolution_result = ? WHERE id = ?",
                (strategy, json.dumps(result), conflict_id)
            )
            return True
        except Exception as e:
            error(f"解决冲突失败: {e}")
            self.conn.rollback()
            return False

    def _delete_memory(self, memory_type: str, memory_id: int):
        table = self._table_for(memory_type)
        self._execute(f"DELETE FROM {table} WHERE id = ?", (memory_id,))
        self._execute("DELETE FROM memory_metadata WHERE memory_type = ? AND memory_id = ?",
                      (memory_type, memory_id))

    def _verify(self, memory_type: str, memory_id: int):
        if memory_type == 'semantic':
            self._execute("UPDATE semantic_memory SET is_verified = 1 WHERE id = ?", (memory_id,))


# ==========================================
# 门面类 — 对外统一接口
# ==========================================

class MemoryService:
    """记忆管理服务（门面模式）

    用法：
        with MemoryService() as ms:
            ms.short_term.add(user_id, session_id, 'user', '你好')
            facts = ms.semantic.search(user_id, '机器学习')
    """

    def __init__(self):
        self._db_path = get_memory_db_path()
        self._local = threading.local()

    @property
    def conn(self):
        return getattr(self._local, 'conn', None)

    @conn.setter
    def conn(self, value):
        self._local.conn = value

    @property
    def cursor(self):
        return getattr(self._local, 'cursor', None)

    @cursor.setter
    def cursor(self, value):
        self._local.cursor = value

    @property
    def short_term(self):
        return getattr(self._local, 'short_term', None)

    @short_term.setter
    def short_term(self, value):
        self._local.short_term = value

    @property
    def episodic(self):
        return getattr(self._local, 'episodic', None)

    @episodic.setter
    def episodic(self, value):
        self._local.episodic = value

    @property
    def semantic(self):
        return getattr(self._local, 'semantic', None)

    @semantic.setter
    def semantic(self, value):
        self._local.semantic = value

    @property
    def entity(self):
        return getattr(self._local, 'entity', None)

    @entity.setter
    def entity(self, value):
        self._local.entity = value

    @property
    def forgetting(self):
        return getattr(self._local, 'forgetting', None)

    @forgetting.setter
    def forgetting(self, value):
        self._local.forgetting = value

    @property
    def conflict(self):
        return getattr(self._local, 'conflict', None)

    @conflict.setter
    def conflict(self, value):
        self._local.conflict = value

    # ── 连接管理 ──────────────────────────────

    def connect(self):
        self.conn = sqlite3.connect(self._db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.short_term = ShortTermHandler(self.conn, self.cursor)
        self.episodic   = EpisodicHandler(self.conn, self.cursor)
        self.semantic   = SemanticHandler(self.conn, self.cursor)
        self.entity     = EntityHandler(self.conn, self.cursor)
        self.forgetting = ForgettingHandler(self.conn, self.cursor)
        self.conflict   = ConflictHandler(self.conn, self.cursor)

    def close(self):
        if self.cursor: self.cursor.close()
        if self.conn:   self.conn.close()
        self._local.conn = None
        self._local.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # ── 向后兼容 API（代理到各 Handler）─────────

    def add_short_term(self, user_id, session_id, role, content):
        mid = self.short_term.add(user_id, session_id, role, content)
        self.forgetting.log_access(user_id, 'short_term', mid, 'write')
        return mid

    def get_short_term_context(self, user_id, session_id, max_tokens=None):
        return self.short_term.get_context(user_id, session_id, max_tokens)

    def add_episodic(self, user_id, episode_type, title, summary, content,
                     context=None, emotions=None, importance=0.5):
        mid = self.episodic.add(user_id, episode_type, title, summary, content, context, emotions, importance)
        self.forgetting.create_metadata('episodic', mid, user_id, importance)
        self.forgetting.log_access(user_id, 'episodic', mid, 'write')
        return mid

    def search_episodic(self, user_id, query, limit=5, use_vector=True):
        results = self.episodic.search(user_id, query, limit)
        for r in results:
            self.forgetting.update_access('episodic', r['id'], user_id)
        
        if use_vector and not results:
            try:
                from data.embedding_service import embedding_service
                from data.rag_knowledge_base import rag_kb
                query_embedding = embedding_service.get_embedding(query)
                if query_embedding:
                    vector_results = rag_kb.search_documents_by_vector(query_embedding, limit=limit)
                    if vector_results:
                        results = [{
                            'id': vr.get('id'),
                            'title': vr.get('title', ''),
                            'summary': vr.get('content_text', '')[:200],
                            'source': 'vector',
                            'similarity': vr.get('similarity', 0)
                        } for vr in vector_results]
            except Exception as e:
                warning(f"向量检索降级: {e}")
        
        return results

    def get_recent_episodes(self, user_id, limit=10):
        return self.episodic.recent(user_id, limit)

    def add_semantic(self, user_id, fact_type, subject, predicate, object_val,
                     confidence=0.8, source=""):
        mid = self.semantic.add(user_id, fact_type, subject, predicate, object_val, confidence, source)
        self.forgetting.create_metadata('semantic', mid, user_id, confidence)
        self.forgetting.log_access(user_id, 'semantic', mid, 'write')
        return mid

    def search_semantic(self, user_id, query, fact_type=None, limit=10):
        results = self.semantic.search(user_id, query, fact_type, limit)
        for r in results:
            self.forgetting.update_access('semantic', r['id'], user_id)
        return results

    def get_facts_by_subject(self, user_id, subject):
        return self.semantic.get_by_subject(user_id, subject)

    def add_entity(self, user_id, entity_type, entity_name, attributes=None,
                   description="", entity_alias="", importance=0.5):
        eid = self.entity.add(user_id, entity_type, entity_name, attributes, description, entity_alias, importance)
        self.forgetting.create_metadata('entity', eid, user_id, importance)
        self.forgetting.log_access(user_id, 'entity', eid, 'write')
        return eid

    def add_relation(self, user_id, source_id, target_id, relation_type,
                     label="", weight=1.0, context=""):
        rid = self.entity.add_relation(user_id, source_id, target_id, relation_type, label, weight, context)
        self.forgetting.create_metadata('relation', rid, user_id, weight)
        return rid

    def search_entities(self, user_id, query, entity_type=None, limit=10):
        results = self.entity.search(user_id, query, entity_type, limit)
        for r in results:
            self.forgetting.update_access('entity', r['id'], user_id)
        return results

    def get_entity_relations(self, user_id, entity_id, direction='both'):
        return self.entity.get_relations(user_id, entity_id, direction)

    def get_entity_graph(self, user_id, center_id, depth=2):
        return self.entity.get_graph(user_id, center_id, depth)

    def apply_forgetting_curve(self, user_id=None):
        return self.forgetting.apply_curve(user_id)

    def reinforce_memory(self, memory_type, memory_id, user_id, boost=None):
        self.forgetting.reinforce(memory_type, memory_id, user_id, boost)
        self.forgetting.log_access(user_id, memory_type, memory_id, 'reinforce')

    def get_pending_conflicts(self, user_id):
        return self.conflict.get_pending(user_id)

    def resolve_conflict(self, conflict_id, strategy, user_id):
        return self.conflict.resolve(conflict_id, strategy, user_id)

    def get_memory_stats(self, user_id: int) -> Dict:
        try:
            return {
                'short_term':        self.short_term.count(user_id),
                'episodic':          self.episodic.count(user_id),
                'semantic':          self.semantic.count(user_id),
                'entity':            self.entity.count(user_id),
                'relations':         self.entity.relation_count(user_id),
                'pending_conflicts': self.conflict.pending_count(user_id),
                'forgotten':         self.forgetting.forgotten_count(user_id),
            }
        except Exception as e:
            error(f"获取记忆统计失败: {e}")
            return {}

    def cleanup_forgotten_memories(self, user_id=None, days=30):
        return self.forgetting.cleanup(user_id, days)


# 全局单例
memory_service = MemoryService()
