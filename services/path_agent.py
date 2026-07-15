"""
学习路径规划智能体 - 基于学生画像生成个性化学习路径
"""

import json
from datetime import datetime

from core.json_utils import safe_parse_json
from core.logger import error, info, warning
from services.qa_service import qa_service


class PathAgent:
    """学习路径规划智能体"""

    def __init__(self):
        info("学习路径规划智能体初始化完成")

    def plan_path(self, user_id: int, input_data: dict) -> dict:
        """
        规划个性化学习路径
        
        Args:
            user_id: 用户ID
            input_data: {
                "profile": 学生画像,
                "resources": 可用资源列表,
                "learning_goal": 学习目标
            }
            
        Returns:
            学习路径数据
        """
        info(f"开始规划学习路径, 用户: {user_id}")

        try:
            profile = input_data.get("profile", {})
            resources = input_data.get("resources", [])
            learning_goal = input_data.get("learning_goal", "")

            # AI规划学习路径
            path_data = self._generate_learning_path(profile, resources, learning_goal)

            # 确保返回格式符合前端期望
            result_path = {
                "goal": learning_goal or path_data.get("path_name", "学习路径"),
                "total_steps": path_data.get("total_steps", len(path_data.get("steps", []))),
                "estimated_duration": f"{path_data.get('estimated_hours', 0)}小时",
                "steps": self._format_steps(path_data.get("steps", []))
            }

            # 保存到数据库
            path_id = self._save_path(user_id, path_data)

            result = {
                "success": True,
                "path_id": path_id,
                "path": result_path,
                "message": f"学习路径规划完成,共 {result_path['total_steps']} 个步骤"
            }

            info(f"学习路径规划完成: {result_path['total_steps']} 个步骤")
            return result

        except Exception as e:
            error(f"规划学习路径失败: {e!s}")
            return {
                "success": False,
                "message": f"规划失败: {e!s}"
            }

    def _format_steps(self, steps: list[dict]) -> list[dict]:
        """格式化步骤数据，确保符合前端期望"""
        formatted = []
        for i, step in enumerate(steps):
            resource_type = step.get("resource_type", "")
            formatted.append({
                "step_number": step.get("step_id", i + 1),
                "title": step.get("title", f"步骤 {i + 1}"),
                "description": step.get("description", step.get("learning_objective", "")),
                "estimated_time": f"{step.get('estimated_time', 30)}分钟",
                "prerequisites": step.get("prerequisites", []),
                "resources": [resource_type] if resource_type else [],
                "resource_type": resource_type,
                "resource_id": step.get("resource_id")
            })
        return formatted

    def _generate_learning_path(self, profile: dict, resources: list,
                               learning_goal: str) -> dict:
        """通过AI生成学习路径"""

        cognitive_style = profile.get("cognitive_style", "visual")
        weak_points = profile.get("weak_points", [])
        preferred_resources = profile.get("preferred_resources", ["document"])

        # 构建资源描述
        resources_desc = ""
        if resources:
            res_list = []
            for res in resources[:10]:
                res_list.append(f"- ID:{res.get('id')}, 类型:{res.get('type')}, 标题:{res.get('title')}, 时长:{res.get('duration_minutes', '未知')}分钟")
            resources_desc = "\n可用资源:\n" + "\n".join(res_list)

        prompt = f"""你是一个专业的学习规划师。请为学生规划一个个性化的学习路径。

学习目标: {learning_goal or '掌握相关知识'}

学生特征:
- 认知风格: {cognitive_style}
- 薄弱点: {', '.join(weak_points[:3]) if weak_points else '无'}
- 资源偏好: {', '.join(preferred_resources[:3])}
{resources_desc}

请严格按照以下JSON格式输出，不要输出其他内容:
```json
{{
    "path_name": "给路径起一个具体的名称",
    "description": "用一句话描述这个学习路径",
    "steps": [
        {{
            "step_id": 1,
            "title": "步骤标题（具体的学习内容）",
            "resource_id": null,
            "resource_type": "document",
            "estimated_time": 30,
            "prerequisites": [],
            "next_steps": [2],
            "description": "详细说明这一步要学什么、怎么学",
            "learning_objective": "完成这一步后能掌握什么"
        }},
        {{
            "step_id": 2,
            "title": "步骤标题",
            "resource_id": null,
            "resource_type": "quiz",
            "estimated_time": 20,
            "prerequisites": [1],
            "next_steps": [3],
            "description": "详细说明",
            "learning_objective": "学习目标"
        }}
    ],
    "total_steps": 5,
    "estimated_hours": 3.5,
    "difficulty_progression": "easy_to_hard",
    "adaptation_notes": "适配说明"
}}
```

要求:
1. 生成4-8个具体的学习步骤
2. 每个步骤必须有明确的title、description和learning_objective
3. 考虑知识依赖关系，prerequisites引用之前的step_id
4. estimated_time单位是分钟，每个步骤20-60分钟
5. resource_type可以从 document/quiz/mindmap/video/code 中选择
6. 总时长控制在2-6小时
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=2500)
            info(f"AI学习路径原始响应: {response[:500] if response else '空'}")
            path_data = safe_parse_json(response)

            # 如果解析失败，使用降级方案
            if not path_data:
                warning("AI 返回的学习路径数据无法解析，使用降级方案")
                return self._fallback_path(resources, learning_goal)

            # 如果返回的是数组，转换为对象格式
            if isinstance(path_data, list):
                info("AI 返回了数组格式，转换为对象格式")
                path_data = {
                    "title": learning_goal or "学习路径",
                    "steps": path_data,
                    "total_time": sum(step.get("estimated_time", 30) for step in path_data if isinstance(step, dict))
                }

            if not isinstance(path_data, dict):
                warning(f"AI 返回的学习路径数据类型无效: {type(path_data)}，使用降级方案")
                return self._fallback_path(resources, learning_goal)

            # 验证steps存在且非空
            steps = path_data.get("steps", [])
            if not steps or not isinstance(steps, list):
                warning("AI 返回的步骤数据无效，使用降级方案")
                return self._fallback_path(resources, learning_goal)

            # 添加元数据
            path_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            path_data["status"] = "active"
            path_data["current_step"] = 1
            path_data["completed_steps"] = 0

            return path_data

        except Exception as e:
            error(f"AI生成学习路径失败: {e!s}")
            return self._fallback_path(resources, learning_goal)

    def _fallback_path(self, resources: list, learning_goal: str = "") -> dict:
        """降级方案:根据学习目标生成有意义的步骤"""
        steps = []
        total_time = 0

        if resources:
            # 有资源时，按资源生成步骤
            for i, res in enumerate(resources[:8]):
                step = {
                    "step_id": i + 1,
                    "title": res.get("title", f"步骤{i+1}"),
                    "resource_id": res.get("id"),
                    "resource_type": res.get("type", "document"),
                    "estimated_time": res.get("duration_minutes", 30),
                    "prerequisites": [i] if i > 0 else [],
                    "next_steps": [i + 2] if i < len(resources) - 1 else [],
                    "description": f"学习并理解{res.get('title', '相关内容')}",
                    "learning_objective": f"掌握{res.get('title', '相关知识')}的核心概念"
                }
                steps.append(step)
                total_time += step["estimated_time"]
        else:
            # 无资源时，根据学习目标生成通用步骤
            goal = learning_goal or "相关知识"
            default_steps = [
                {"title": f"了解{goal}的基础概念", "type": "document", "time": 30,
                 "desc": "阅读基础资料，了解核心概念和术语", "obj": f"理解{goal}的基本定义和原理"},
                {"title": f"学习{goal}的核心知识点", "type": "document", "time": 45,
                 "desc": "深入学习关键知识点，做好笔记", "obj": f"掌握{goal}的核心理论和方法"},
                {"title": f"观看{goal}的讲解视频", "type": "video", "time": 30,
                 "desc": "通过视频直观理解抽象概念", "obj": "通过可视化方式加深理解"},
                {"title": f"完成{goal}的练习题", "type": "quiz", "time": 30,
                 "desc": "做配套练习题，检验学习效果", "obj": "通过练习巩固所学知识"},
                {"title": f"绘制{goal}的思维导图", "type": "mindmap", "time": 25,
                 "desc": "梳理知识点之间的关系，形成知识体系", "obj": "建立完整的知识框架"},
                {"title": f"总结复习{goal}", "type": "document", "time": 20,
                 "desc": "回顾学习内容，查漏补缺", "obj": "巩固学习成果，发现薄弱环节"}
            ]

            for i, s in enumerate(default_steps):
                step = {
                    "step_id": i + 1,
                    "title": s["title"],
                    "resource_id": None,
                    "resource_type": s["type"],
                    "estimated_time": s["time"],
                    "prerequisites": [i] if i > 0 else [],
                    "next_steps": [i + 2] if i < len(default_steps) - 1 else [],
                    "description": s["desc"],
                    "learning_objective": s["obj"]
                }
                steps.append(step)
                total_time += s["time"]

        return {
            "path_name": f"{learning_goal or '基础'}学习路径",
            "description": f"针对「{learning_goal or '相关知识'}」的系统学习路径",
            "steps": steps,
            "total_steps": len(steps),
            "estimated_hours": round(total_time / 60, 1),
            "difficulty_progression": "easy_to_hard",
            "adaptation_notes": "基于学习目标生成的基础学习路径",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "current_step": 1,
            "completed_steps": 0
        }

    def _save_path(self, user_id: int, path_data: dict) -> int:
        """保存学习路径到数据库"""
        try:
            from data.db_operations import path_db
            with path_db:
                sql = """
                    INSERT INTO learning_paths
                    (user_id, path_name, description, path_data, current_step, total_steps, estimated_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                path_db.cursor.execute(sql, (
                    user_id,
                    path_data.get("path_name", "学习路径"),
                    path_data.get("description", ""),
                    json.dumps(path_data, ensure_ascii=False),
                    path_data.get("current_step", 1),
                    path_data.get("total_steps", 0),
                    path_data.get("estimated_hours", 0)
                ))

                path_id = path_db.cursor.lastrowid
                path_db.conn.commit()

                info(f"学习路径保存成功, ID: {path_id}")
                return path_id

        except Exception as e:
            error(f"保存学习路径失败: {e!s}")
            raise

    def update_path_progress(self, path_id: int, completed_step: int, user_id: int = None) -> dict:
        """更新学习路径进度"""
        try:
            from data.db_operations import path_db
            with path_db:
                # 获取当前路径（验证所有权）
                if user_id is not None:
                    sql = "SELECT path_data, total_steps FROM learning_paths WHERE id = ? AND user_id = ?"
                    path_db.cursor.execute(sql, (path_id, user_id))
                else:
                    sql = "SELECT path_data, total_steps FROM learning_paths WHERE id = ?"
                    path_db.cursor.execute(sql, (path_id,))
                result = path_db.cursor.fetchone()

                if not result:
                    return {"success": False, "message": "路径不存在"}

                result = dict(result)
                path_data = json.loads(result["path_data"])
                total_steps = result["total_steps"]

                # 更新进度
                path_data["current_step"] = completed_step + 1
                path_data["completed_steps"] = completed_step

                completion_rate = round(completed_step / total_steps * 100, 2) if total_steps > 0 else 0
                path_data["completion_rate"] = completion_rate

                # 判断是否完成
                status = "completed" if completed_step >= total_steps else "active"

                # 更新数据库
                sql_update = """
                    UPDATE learning_paths
                    SET path_data = ?, current_step = ?, completed_steps = ?, status = ?
                    WHERE id = ?
                """
                path_db.cursor.execute(sql_update, (
                    json.dumps(path_data, ensure_ascii=False),
                    path_data["current_step"],
                    path_data["completed_steps"],
                    status,
                    path_id
                ))

                path_db.conn.commit()

                return {
                    "success": True,
                    "path_data": path_data,
                    "completion_rate": completion_rate,
                    "status": status,
                    "message": f"进度更新成功,完成率: {completion_rate}%"
                }

        except Exception as e:
            error(f"更新路径进度失败: {e!s}")
            return {"success": False, "message": f"更新失败: {e!s}"}
