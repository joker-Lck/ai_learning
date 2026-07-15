"""
数据访问对象 (DAO) 层
封装所有数据库 CRUD 操作，消除路由层的重复数据库代码
"""

import json
from typing import Any

from core.logger import error


class ResourceDAO:
    """学习资源数据访问"""

    def __init__(self, db):
        self._db = db

    def save(self, user_id: int, title: str, resource_type: str,
             subject: str, topic: str, difficulty: str,
             content_data: Any, duration_minutes: int | None = None,
             generated_by: str | None = None) -> int | None:
        """保存学习资源，返回资源 ID"""
        try:
            with self._db:
                self._db.cursor.execute("""
                    INSERT INTO learning_resources
                    (user_id, title, resource_type, subject, topic,
                     difficulty_level, content_data, generated_by_agent, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, title, resource_type, subject, topic,
                    difficulty,
                    json.dumps(content_data, ensure_ascii=False) if not isinstance(content_data, str) else content_data,
                    generated_by or f"user_{user_id}",
                    duration_minutes,
                ))
                self._db.conn.commit()
                return self._db.cursor.lastrowid
        except Exception as e:
            error(f"保存资源失败: {e}")
            return None

    def get_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取用户的资源列表"""
        try:
            with self._db:
                self._db.cursor.execute("""
                    SELECT id, title, resource_type, subject, topic,
                           difficulty_level, content_data, created_at
                    FROM learning_resources
                    WHERE user_id = ? OR (user_id IS NULL AND generated_by_agent = ?)
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                """, (user_id, f"user_{user_id}", limit, offset))
                rows = [dict(row) for row in self._db.cursor.fetchall()]
                for row in rows:
                    if row.get("content_data") and isinstance(row["content_data"], str):
                        try:
                            row["content_data"] = json.loads(row["content_data"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if row.get("created_at"):
                        row["created_at"] = str(row["created_at"])
                return rows
        except Exception as e:
            error(f"获取用户资源失败: {e}")
            return []

    def count_by_user(self, user_id: int) -> int:
        """统计用户资源数量"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(*) as cnt FROM learning_resources WHERE user_id = ? OR (user_id IS NULL AND generated_by_agent = ?)",
                    (user_id, f"user_{user_id}")
                )
                row = self._db.cursor.fetchone()
                return dict(row)["cnt"] if row else 0
        except Exception as e:
            error(f"统计资源数量失败: {e}")
            return 0

    def delete(self, resource_id: int, user_id: int) -> bool:
        """删除资源（仅限拥有者）"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "DELETE FROM learning_resources WHERE id = ? AND user_id = ?",
                    (resource_id, user_id)
                )
                self._db.conn.commit()
                return self._db.cursor.rowcount > 0
        except Exception as e:
            error(f"删除资源失败: {e}")
            return False


class ActivityDAO:
    """学习活动日志数据访问"""

    def __init__(self, db):
        self._db = db

    def record(self, user_id: int, activity_type: str,
               metadata: dict | None = None, duration_seconds: int = 0) -> int | None:
        """记录一条活动日志"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "INSERT INTO learning_activities (user_id, activity_type, metadata, duration_seconds) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, activity_type,
                     json.dumps(metadata, ensure_ascii=False) if metadata else None,
                     duration_seconds)
                )
                self._db.conn.commit()
                return self._db.cursor.lastrowid
        except Exception as e:
            error(f"记录活动日志失败: {e}")
            return None

    def get_recent(self, user_id: int, limit: int = 10) -> list[dict]:
        """获取最近活动日志"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT id, activity_type, metadata, created_at "
                    "FROM learning_activities WHERE user_id = ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
                rows = [dict(row) for row in self._db.cursor.fetchall()]
                for row in rows:
                    if row.get("metadata") and isinstance(row["metadata"], str):
                        try:
                            row["metadata"] = json.loads(row["metadata"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if row.get("created_at"):
                        row["created_at"] = str(row["created_at"])
                return rows
        except Exception as e:
            error(f"获取活动日志失败: {e}")
            return []

    def count_by_user(self, user_id: int) -> int:
        """统计用户活动数"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(*) as cnt FROM learning_activities WHERE user_id = ?",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["cnt"] if row else 0
        except Exception:
            return 0

    def get_login_days(self, user_id: int) -> int:
        """获取用户登录天数"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(DISTINCT DATE(created_at)) as days "
                    "FROM learning_activities WHERE user_id = ? "
                    "AND activity_type IN ('login', 'resource_generate', 'tutor_query', 'assessment')",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["days"] if row else 0
        except Exception:
            return 0

    def get_total_study_seconds(self, user_id: int) -> int:
        """获取总学习时长"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COALESCE(SUM(duration_seconds), 0) as total "
                    "FROM learning_activities WHERE user_id = ? AND activity_type = 'session'",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["total"] if row else 0
        except Exception:
            return 0


# 全局 DAO 实例（延迟初始化）
_resource_dao: ResourceDAO | None = None
_activity_dao: ActivityDAO | None = None


def get_resource_dao() -> ResourceDAO:
    global _resource_dao
    if _resource_dao is None:
        from data.db_operations import resource_db
        _resource_dao = ResourceDAO(resource_db)
    return _resource_dao


def get_activity_dao() -> ActivityDAO:
    global _activity_dao
    if _activity_dao is None:
        from data.db_operations import assessment_db
        _activity_dao = ActivityDAO(assessment_db)
    return _activity_dao

