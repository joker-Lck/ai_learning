"""
学生画像智能体 - 对话式构建动态学生画像
支持≥6维度:知识基础、认知风格、学习目标、易错点、学习历史、兴趣领域等
"""

import json
from datetime import datetime

from core.json_utils import safe_parse_json
from core.logger import error, info, warning
from core.prompts import ProfilePrompts
from services.qa_service import qa_service


class ProfileAgent:
    """学生画像智能体"""

    def __init__(self):
        self.dimensions = [
            "knowledge_base",      # 知识基础
            "cognitive_style",     # 认知风格
            "learning_goals",      # 学习目标
            "weak_points",         # 易错点偏好
            "learning_history",    # 学习历史
            "interest_areas",      # 兴趣领域
            "preferred_resources", # 资源偏好
            "major",              # 专业
            "grade_level"         # 年级
        ]
        info("学生画像智能体初始化完成")

    def build_profile(self, user_id: int, input_data: dict) -> dict:
        """
        构建学生画像
        
        Args:
            user_id: 用户ID
            input_data: 输入数据,包含对话历史或基本信息
            
        Returns:
            画像数据
        """
        info(f"开始构建学生画像, 用户: {user_id}")

        try:
            # Step 1: 提取已有信息
            existing_profile = self._get_existing_profile(user_id)

            # Step 2: 通过对话或输入数据提取特征
            conversation_log = input_data.get("conversation_log", [])
            basic_info = input_data.get("basic_info", {})

            # Step 3: AI分析提取画像维度
            profile_data = self._extract_profile_features(
                conversation_log,
                basic_info,
                existing_profile
            )

            # Step 4: 验证画像完整性(确保≥6维度)
            validated_profile = self._validate_profile(profile_data)

            # Step 5: 保存到数据库
            profile_id = self._save_profile(user_id, validated_profile, conversation_log)

            result = {
                "profile_id": profile_id,
                "profile": validated_profile,
                "dimensions_count": len([v for v in validated_profile.values() if v]),
                "summary": validated_profile.get("summary", ""),
                "message": f"成功构建包含 {len([v for v in validated_profile.values() if v])} 个维度的学生画像"
            }

            info(f"学生画像构建完成: {result['dimensions_count']} 个维度")
            return result

        except Exception as e:
            error(f"构建学生画像失败: {e!s}")
            return {
                "success": False,
                "message": f"构建失败: {e!s}"
            }

    def get_or_build_profile(self, user_id: int) -> dict:
        """获取已有画像,如无则返回空模板"""
        profile = self._get_existing_profile(user_id)

        if profile:
            return {
                "success": True,
                "profile": profile,
                "message": "获取已有画像"
            }
        else:
            # 返回空模板,等待对话构建
            return {
                "success": True,
                "profile": self._create_empty_profile(),
                "message": "暂无画像,请通过对话构建"
            }

    def update_profile_from_learning(self, user_id: int, learning_data: dict) -> dict:
        """
        根据学习行为动态更新画像
        
        Args:
            user_id: 用户ID
            learning_data: 学习行为数据
            
        Returns:
            更新后的画像
        """
        info(f"动态更新学生画像, 用户: {user_id}")

        try:
            # 获取现有画像
            profile = self._get_existing_profile(user_id)
            if not profile:
                profile = self._create_empty_profile()

            # 更新学习历史
            if "learning_history" not in profile:
                profile["learning_history"] = []

            profile["learning_history"].append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "activity": learning_data.get("activity"),
                "duration": learning_data.get("duration"),
                "performance": learning_data.get("performance")
            })

            # 限制历史记录长度
            if len(profile["learning_history"]) > 50:
                profile["learning_history"] = profile["learning_history"][-50:]

            # 基于表现更新薄弱点
            if learning_data.get("weak_topics"):
                if "weak_points" not in profile:
                    profile["weak_points"] = []

                for topic in learning_data["weak_topics"]:
                    if topic not in profile["weak_points"]:
                        profile["weak_points"].append(topic)

            # 更新时间戳
            profile["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 保存更新
            self._save_profile(user_id, profile, [])

            return {
                "success": True,
                "profile": profile,
                "message": "画像动态更新成功"
            }

        except Exception as e:
            error(f"更新学生画像失败: {e!s}")
            return {
                "success": False,
                "message": f"更新失败: {e!s}"
            }

    def _extract_profile_features(self, conversation_log: list,
                                  basic_info: dict,
                                  existing_profile: dict) -> dict:
        """通过AI从对话和基本信息中提取画像特征"""

        # 构建提示词
        prompt = ProfilePrompts.build_extraction_prompt(
            conversation_log,
            basic_info,
            existing_profile
        )

        try:
            # 调用大模型提取特征
            response = qa_service.call_ai(prompt, max_tokens=3000)

            # 解析JSON响应
            profile_data = safe_parse_json(response)

            # 如果解析失败，使用降级方案
            if not profile_data:
                warning("AI 返回的画像数据无法解析，使用降级方案")
                return self._fallback_extract(basic_info, existing_profile)

            # 如果返回的是数组，取第一个元素
            if isinstance(profile_data, list) and len(profile_data) > 0:
                info("AI 返回了数组格式，取第一个元素")
                profile_data = profile_data[0] if isinstance(profile_data[0], dict) else {"learning_style": "balanced"}

            if not isinstance(profile_data, dict):
                warning(f"AI 返回的画像数据类型无效: {type(profile_data)}，使用降级方案")
                return self._fallback_extract(basic_info, existing_profile)

            # 合并到现有画像
            if existing_profile:
                for key, value in profile_data.items():
                    if value:  # 只更新非空值
                        existing_profile[key] = value
                return existing_profile
            else:
                return profile_data

        except Exception as e:
            error(f"AI提取画像特征失败: {e!s}")
            # 降级:使用基本信息填充
            return self._fallback_extract(basic_info, existing_profile)

    def _fallback_extract(self, basic_info: dict, existing_profile: dict) -> dict:
        """降级方案:直接使用基本信息"""
        profile = existing_profile or self._create_empty_profile()

        if basic_info.get("major"):
            profile["major"] = basic_info["major"]
        if basic_info.get("grade_level"):
            profile["grade_level"] = basic_info["grade_level"]
        if basic_info.get("learning_goals"):
            profile["learning_goals"] = basic_info["learning_goals"]

        profile["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return profile

    def _validate_profile(self, profile: dict) -> dict:
        """验证画像完整性,确保至少6个维度有值"""
        required_dimensions = [
            "knowledge_base",
            "cognitive_style",
            "learning_goals",
            "weak_points",
            "learning_history",
            "interest_areas"
        ]

        filled_dimensions = [dim for dim in required_dimensions if profile.get(dim)]

        if len(filled_dimensions) < 6:
            # 补充默认值
            for dim in required_dimensions:
                if not profile.get(dim):
                    profile[dim] = self._get_default_value(dim)

        profile["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return profile

    def _get_default_value(self, dimension: str):
        """获取维度的默认值"""
        defaults = {
            "knowledge_base": {"level": "intermediate", "topics": []},
            "cognitive_style": "visual",  # 视觉型
            "learning_goals": ["提升专业技能", "通过考试"],
            "weak_points": [],
            "learning_history": [],
            "interest_areas": [],
            "preferred_resources": ["document", "video"],
            "major": "未设置",
            "grade_level": "未设置"
        }
        return defaults.get(dimension, [])

    def _create_empty_profile(self) -> dict:
        """创建空画像模板"""
        return {
            "knowledge_base": {"level": "beginner", "topics": []},
            "cognitive_style": "",
            "learning_goals": [],
            "weak_points": [],
            "learning_history": [],
            "interest_areas": [],
            "preferred_resources": [],
            "major": "",
            "grade_level": "",
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _get_existing_profile(self, user_id: int) -> dict | None:
        """从数据库获取已有画像"""
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
            error(f"获取画像失败: {e!s}")
            return None

    def _save_profile(self, user_id: int, profile_data: dict,
                     conversation_log: list) -> int:
        """保存画像到数据库"""
        try:
            from data.db_operations import profile_db
            with profile_db:
                # 检查是否已有画像
                sql_check = "SELECT id, version FROM student_profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql_check, (user_id,))
                existing = profile_db.cursor.fetchone()

                if existing:
                    existing = dict(existing)
                    # 更新现有画像,版本号+1
                    new_version = existing["version"] + 1
                    sql_update = """
                        UPDATE student_profiles
                        SET profile_data = ?, conversation_log = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """
                    profile_db.cursor.execute(sql_update, (
                        json.dumps(profile_data, ensure_ascii=False),
                        json.dumps(conversation_log, ensure_ascii=False),
                        new_version,
                        existing["id"]
                    ))
                    profile_id = existing["id"]
                else:
                    # 创建新画像
                    sql_insert = """
                        INSERT INTO student_profiles (user_id, profile_data, conversation_log, version)
                        VALUES (?, ?, ?, 1)
                    """
                    profile_db.cursor.execute(sql_insert, (
                        user_id,
                        json.dumps(profile_data, ensure_ascii=False),
                        json.dumps(conversation_log, ensure_ascii=False)
                    ))
                    profile_id = profile_db.cursor.lastrowid

                profile_db.conn.commit()

                info(f"画像保存成功, ID: {profile_id}")
                return profile_id

        except Exception as e:
            error(f"保存画像失败: {e!s}")
            raise

    def update_profile_field(self, user_id: int, field: str, value: Any) -> dict:
        """更新画像单个字段"""
        allowed = {'major', 'grade_level', 'cognitive_style', 'knowledge_base',
                    'learning_goals', 'weak_points', 'interest_areas', 'preferred_resources'}
        if field not in allowed:
            return {"success": False, "message": f"不允许修改字段: {field}"}

        try:
            from data.db_operations import profile_db
            with profile_db:
                sql = "SELECT id, profile_data, conversation_log, version FROM student_profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql, (user_id,))
                row = profile_db.cursor.fetchone()

                if not row:
                    return {"success": False, "message": "暂无画像数据，请先构建画像"}

                row = dict(row)
                profile = json.loads(row["profile_data"]) if isinstance(row["profile_data"], str) else row["profile_data"]
                old_value = profile.get(field)
                profile[field] = value
                profile["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_version = row["version"] + 1
                sql_update = "UPDATE student_profiles SET profile_data=?, version=?, updated_at=CURRENT_TIMESTAMP WHERE id=?"
                profile_db.cursor.execute(sql_update, (
                    json.dumps(profile, ensure_ascii=False), new_version, row["id"]
                ))
                profile_db.conn.commit()

                info(f"画像字段更新: user={user_id}, field={field}")
                return {"success": True, "data": profile, "message": f"已更新{field}"}

        except Exception as e:
            error(f"更新画像字段失败: {e}")
            return {"success": False, "message": str(e)}
