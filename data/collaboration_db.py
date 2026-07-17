"""
协同学习小组数据库操作
"""

import json
import sqlite3
import time
from datetime import datetime

from core.logger import error, info, warning


class CollaborationDB:
    """协同学习小组数据库"""

    def __init__(self):
        self.db_path = None
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        try:
            from data.config import get_assessment_db_path
            self.db_path = get_assessment_db_path()
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self._init_tables()
            return True
        except Exception as e:
            error(f"协同学习数据库连接失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

    def _init_tables(self):
        """初始化表结构"""
        try:
            # 小组表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    creator_id INTEGER NOT NULL,
                    invite_code TEXT UNIQUE NOT NULL,
                    max_members INTEGER DEFAULT 50,
                    subject TEXT DEFAULT '综合',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 成员关系表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(group_id, user_id),
                    FOREIGN KEY (group_id) REFERENCES study_groups(id)
                )
            """)

            # 共享资源表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    resource_type TEXT DEFAULT 'document',
                    shared_by INTEGER NOT NULL,
                    shared_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES study_groups(id)
                )
            """)

            # 学习动态表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_activities_feed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES study_groups(id)
                )
            """)

            # 互评表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS peer_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    reviewer_id INTEGER NOT NULL,
                    rating INTEGER DEFAULT 0,
                    comment TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES study_groups(id)
                )
            """)

            self.conn.commit()
        except Exception as e:
            error(f"初始化协同学习表失败: {e}")

    # ═══════════════════════════════════════
    # 小组管理
    # ═══════════════════════════════════════

    def create_group(self, name: str, creator_id: int, description: str = "",
                     subject: str = "综合", max_members: int = 50) -> dict:
        """创建学习小组"""
        try:
            import random
            import string
            invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            self.cursor.execute("""
                INSERT INTO study_groups (name, description, creator_id, invite_code, subject, max_members)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, description, creator_id, invite_code, subject, max_members))

            group_id = self.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]

            # 创建者自动成为组长
            self.cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, 'admin')
            """, (group_id, creator_id))

            self.conn.commit()
            info(f"创建小组: {name}, ID={group_id}, 邀请码={invite_code}")

            return {
                "success": True,
                "group_id": group_id,
                "invite_code": invite_code,
                "name": name,
            }
        except Exception as e:
            error(f"创建小组失败: {e}")
            return {"success": False, "message": str(e)}

    def join_group(self, invite_code: str, user_id: int) -> dict:
        """通过邀请码加入小组"""
        try:
            # 查找小组
            self.cursor.execute("SELECT * FROM study_groups WHERE invite_code = ?", (invite_code,))
            group = self.cursor.fetchone()
            if not group:
                return {"success": False, "message": "邀请码无效"}

            group_id = group["id"]

            # 检查是否已是成员
            self.cursor.execute(
                "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            if self.cursor.fetchone():
                return {"success": False, "message": "已经是小组成员"}

            # 检查人数上限
            self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM group_members WHERE group_id = ?",
                (group_id,)
            )
            count = self.cursor.fetchone()["cnt"]
            if count >= group["max_members"]:
                return {"success": False, "message": "小组已满"}

            # 加入
            self.cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (?, ?, 'member')
            """, (group_id, user_id))

            self.conn.commit()
            info(f"用户 {user_id} 加入小组 {group_id}")

            return {
                "success": True,
                "group_id": group_id,
                "group_name": group["name"],
            }
        except Exception as e:
            error(f"加入小组失败: {e}")
            return {"success": False, "message": str(e)}

    def leave_group(self, group_id: int, user_id: int) -> dict:
        """退出小组"""
        try:
            self.cursor.execute(
                "DELETE FROM group_members WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_user_groups(self, user_id: int) -> list:
        """获取用户加入的所有小组"""
        try:
            self.cursor.execute("""
                SELECT sg.*, gm.role, gm.joined_at,
                       (SELECT COUNT(*) FROM group_members WHERE group_id = sg.id) as member_count
                FROM study_groups sg
                JOIN group_members gm ON sg.id = gm.group_id
                WHERE gm.user_id = ?
                ORDER BY gm.joined_at DESC
            """, (user_id,))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            error(f"获取用户小组失败: {e}")
            return []

    def get_group_members(self, group_id: int) -> list:
        """获取小组成员列表"""
        try:
            self.cursor.execute("""
                SELECT gm.user_id, gm.role, gm.joined_at
                FROM group_members gm
                WHERE gm.group_id = ?
                ORDER BY gm.role DESC, gm.joined_at ASC
            """, (group_id,))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            error(f"获取小组成员失败: {e}")
            return []

    def get_group_info(self, group_id: int) -> dict | None:
        """获取小组详情"""
        try:
            self.cursor.execute("""
                SELECT sg.*,
                       (SELECT COUNT(*) FROM group_members WHERE group_id = sg.id) as member_count
                FROM study_groups sg
                WHERE sg.id = ?
            """, (group_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            error(f"获取小组信息失败: {e}")
            return None

    # ═══════════════════════════════════════
    # 资源共享
    # ═══════════════════════════════════════

    def share_resource(self, group_id: int, resource_id: int, shared_by: int,
                       resource_type: str = "document") -> dict:
        """共享资源到小组"""
        try:
            self.cursor.execute("""
                INSERT INTO shared_resources (group_id, resource_id, resource_type, shared_by)
                VALUES (?, ?, ?, ?)
            """, (group_id, resource_id, resource_type, shared_by))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_shared_resources(self, group_id: int, limit: int = 50) -> list:
        """获取小组共享资源"""
        try:
            self.cursor.execute("""
                SELECT sr.*, gm.user_id as sharer_id
                FROM shared_resources sr
                JOIN group_members gm ON sr.shared_by = gm.user_id AND sr.group_id = gm.group_id
                WHERE sr.group_id = ?
                ORDER BY sr.shared_at DESC
                LIMIT ?
            """, (group_id, limit))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            error(f"获取共享资源失败: {e}")
            return []

    # ═══════════════════════════════════════
    # 学习动态
    # ═══════════════════════════════════════

    def add_activity(self, group_id: int, user_id: int, activity_type: str,
                     content: str = "", metadata: dict | None = None) -> bool:
        """添加学习动态"""
        try:
            self.cursor.execute("""
                INSERT INTO learning_activities_feed (group_id, user_id, activity_type, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, user_id, activity_type, content,
                  json.dumps(metadata or {}, ensure_ascii=False)))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"添加学习动态失败: {e}")
            return False

    def get_group_activities(self, group_id: int, limit: int = 30) -> list:
        """获取小组学习动态"""
        try:
            self.cursor.execute("""
                SELECT * FROM learning_activities_feed
                WHERE group_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (group_id, limit))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            error(f"获取小组动态失败: {e}")
            return []

    # ═══════════════════════════════════════
    # 互评
    # ═══════════════════════════════════════

    def add_review(self, group_id: int, resource_id: int, reviewer_id: int,
                   rating: int, comment: str = "") -> dict:
        """添加互评"""
        try:
            self.cursor.execute("""
                INSERT INTO peer_reviews (group_id, resource_id, reviewer_id, rating, comment)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, resource_id, reviewer_id, max(1, min(5, rating)), comment))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_resource_reviews(self, group_id: int, resource_id: int) -> list:
        """获取资源的互评"""
        try:
            self.cursor.execute("""
                SELECT * FROM peer_reviews
                WHERE group_id = ? AND resource_id = ?
                ORDER BY created_at DESC
            """, (group_id, resource_id))
            return [dict(r) for r in self.cursor.fetchall()]
        except Exception as e:
            error(f"获取互评失败: {e}")
            return []

    # ═══════════════════════════════════════
    # 学习进度对比
    # ═══════════════════════════════════════

    def get_group_learning_stats(self, group_id: int) -> dict:
        """获取小组学习统计数据（用于进度对比）"""
        try:
            members = self.get_group_members(group_id)
            if not members:
                return {"members": [], "stats": {}}

            from data.db_operations import assessment_db, resource_db

            member_stats = []
            for member in members:
                user_id = member["user_id"]
                stats = {"user_id": user_id, "role": member["role"]}

                # 学习资源数
                try:
                    if resource_db.connect():
                        resource_db.cursor.execute(
                            "SELECT COUNT(*) as cnt FROM learning_resources WHERE user_id=?",
                            (user_id,)
                        )
                        stats["resource_count"] = resource_db.cursor.fetchone()["cnt"]
                        resource_db.close()
                except Exception:
                    stats["resource_count"] = 0

                # 学习活动数
                try:
                    if assessment_db.connect():
                        assessment_db.cursor.execute(
                            "SELECT COUNT(*) as cnt FROM learning_activities WHERE user_id=?",
                            (user_id,)
                        )
                        stats["activity_count"] = assessment_db.cursor.fetchone()["cnt"]
                        assessment_db.close()
                except Exception:
                    stats["activity_count"] = 0

                member_stats.append(stats)

            return {
                "members": member_stats,
                "total_members": len(member_stats),
            }
        except Exception as e:
            error(f"获取小组学习统计失败: {e}")
            return {"members": [], "stats": {}}


# 全局单例
collaboration_db = CollaborationDB()
