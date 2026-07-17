"""
协同学习小组服务层
"""

from core.logger import error, info, warning


class CollaborationService:
    """协同学习小组服务"""

    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            from data.collaboration_db import collaboration_db
            self._db = collaboration_db
        return self._db

    def create_group(self, user_id: int, name: str, description: str = "",
                     subject: str = "综合") -> dict:
        """创建学习小组"""
        if not self.db.connect():
            return {"success": False, "message": "数据库连接失败"}
        try:
            result = self.db.create_group(name, user_id, description, subject)
            if result["success"]:
                self.db.add_activity(
                    result["group_id"], user_id, "group_created",
                    f"创建了小组「{name}」"
                )
            return result
        finally:
            self.db.close()

    def join_group(self, user_id: int, invite_code: str) -> dict:
        """加入小组"""
        if not self.db.connect():
            return {"success": False, "message": "数据库连接失败"}
        try:
            result = self.db.join_group(invite_code, user_id)
            if result["success"]:
                self.db.add_activity(
                    result["group_id"], user_id, "member_joined",
                    "加入了小组"
                )
            return result
        finally:
            self.db.close()

    def leave_group(self, user_id: int, group_id: int) -> dict:
        """退出小组"""
        if not self.db.connect():
            return {"success": False, "message": "数据库连接失败"}
        try:
            return self.db.leave_group(group_id, user_id)
        finally:
            self.db.close()

    def get_user_groups(self, user_id: int) -> list:
        """获取用户的小组列表"""
        if not self.db.connect():
            return []
        try:
            return self.db.get_user_groups(user_id)
        finally:
            self.db.close()

    def get_group_detail(self, group_id: int, user_id: int) -> dict | None:
        """获取小组详情（含成员信息和用户角色）"""
        if not self.db.connect():
            return None
        try:
            group = self.db.get_group_info(group_id)
            if not group:
                return None

            members = self.db.get_group_members(group_id)
            group["members"] = members
            group["is_member"] = any(m["user_id"] == user_id for m in members)
            group["is_admin"] = any(
                m["user_id"] == user_id and m["role"] == "admin" for m in members
            )

            return group
        finally:
            self.db.close()

    def share_resource(self, user_id: int, group_id: int, resource_id: int,
                       resource_type: str = "document") -> dict:
        """共享资源到小组"""
        if not self.db.connect():
            return {"success": False, "message": "数据库连接失败"}
        try:
            result = self.db.share_resource(group_id, resource_id, user_id, resource_type)
            if result["success"]:
                self.db.add_activity(
                    group_id, user_id, "resource_shared",
                    f"共享了一份{resource_type}",
                    {"resource_id": resource_id, "resource_type": resource_type}
                )
            return result
        finally:
            self.db.close()

    def get_shared_resources(self, group_id: int) -> list:
        """获取小组共享资源"""
        if not self.db.connect():
            return []
        try:
            return self.db.get_shared_resources(group_id)
        finally:
            self.db.close()

    def get_group_activities(self, group_id: int, limit: int = 30) -> list:
        """获取小组动态"""
        if not self.db.connect():
            return []
        try:
            return self.db.get_group_activities(group_id, limit)
        finally:
            self.db.close()

    def add_activity(self, group_id: int, user_id: int, activity_type: str,
                     content: str = "", metadata: dict | None = None) -> bool:
        """添加学习动态"""
        if not self.db.connect():
            return False
        try:
            return self.db.add_activity(group_id, user_id, activity_type, content, metadata)
        finally:
            self.db.close()

    def add_review(self, user_id: int, group_id: int, resource_id: int,
                   rating: int, comment: str = "") -> dict:
        """添加互评"""
        if not self.db.connect():
            return {"success": False, "message": "数据库连接失败"}
        try:
            result = self.db.add_review(group_id, resource_id, user_id, rating, comment)
            if result["success"]:
                self.db.add_activity(
                    group_id, user_id, "peer_review",
                    f"评价了资源（{rating}星）",
                    {"resource_id": resource_id, "rating": rating}
                )
            return result
        finally:
            self.db.close()

    def get_group_learning_stats(self, group_id: int) -> dict:
        """获取小组学习统计（进度对比）"""
        if not self.db.connect():
            return {"members": []}
        try:
            return self.db.get_group_learning_stats(group_id)
        finally:
            self.db.close()


# 全局单例
collaboration_service = CollaborationService()
