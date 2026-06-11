"""
学习路径规划智能体 - 基于学生画像生成个性化学习路径
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from core.logger import info, error
from core.json_utils import safe_parse_json
from services.qa_service import qa_service


class PathAgent:
    """学习路径规划智能体"""
    
    def __init__(self):
        info("学习路径规划智能体初始化完成")
    
    def plan_path(self, user_id: int, input_data: Dict) -> Dict:
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
                "path_id": path_id,
                "path": result_path,
                "message": f"学习路径规划完成,共 {result_path['total_steps']} 个步骤"
            }

            info(f"学习路径规划完成: {result_path['total_steps']} 个步骤")
            return result
            
        except Exception as e:
            error(f"规划学习路径失败: {str(e)}")
            return {
                "success": False,
                "message": f"规划失败: {str(e)}"
            }
    
    def _format_steps(self, steps: List[Dict]) -> List[Dict]:
        """格式化步骤数据，确保符合前端期望"""
        formatted = []
        for i, step in enumerate(steps):
            formatted.append({
                "step_number": step.get("step_id", i + 1),
                "title": step.get("title", f"步骤 {i + 1}"),
                "description": step.get("description", step.get("learning_objective", "")),
                "estimated_time": f"{step.get('estimated_time', 30)}分钟",
                "prerequisites": step.get("prerequisites", []),
                "resource_type": step.get("resource_type", ""),
                "resource_id": step.get("resource_id")
            })
        return formatted

    def _generate_learning_path(self, profile: Dict, resources: List, 
                               learning_goal: str) -> Dict:
        """通过AI生成学习路径"""
        
        cognitive_style = profile.get("cognitive_style", "visual")
        weak_points = profile.get("weak_points", [])
        preferred_resources = profile.get("preferred_resources", ["document"])
        
        # 构建资源描述
        resources_desc = []
        for res in resources[:10]:  # 限制数量
            resources_desc.append({
                "id": res.get("id"),
                "type": res.get("type"),
                "title": res.get("title"),
                "duration": res.get("duration_minutes")
            })
        
        prompt = f"""请基于学生画像和学习目标,规划一个个性化的学习路径。

学生特征:
- 认知风格: {cognitive_style}
- 薄弱点: {', '.join(weak_points[:3]) if weak_points else '无'}
- 资源偏好: {', '.join(preferred_resources[:3])}
- 学习目标: {learning_goal}

可用资源:
{json.dumps(resources_desc, ensure_ascii=False, indent=2)}

要求:
1. 将资源组织成有序的学习步骤
2. 考虑前置知识依赖关系
3. 针对薄弱点安排更多练习
4. 适合{cognitive_style}型学习者的学习顺序
5. 每个步骤标注预计学习时间
6. 总时长控制在合理范围(2-8小时)

输出JSON格式:
{{
    "path_name": "路径名称",
    "description": "路径描述",
    "steps": [
        {{
            "step_id": 1,
            "title": "步骤标题",
            "resource_id": 资源ID,
            "resource_type": "资源类型",
            "estimated_time": 30,
            "prerequisites": [],
            "next_steps": [2],
            "description": "步骤说明",
            "learning_objective": "学习目标"
        }}
    ],
    "total_steps": 5,
    "estimated_hours": 3.5,
    "difficulty_progression": "easy_to_hard",
    "adaptation_notes": "适配说明"
}}
"""
        
        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            path_data = safe_parse_json(response)

            # 如果解析失败，使用降级方案
            if not path_data or not isinstance(path_data, dict):
                warning(f"AI 返回的学习路径数据无效，使用降级方案")
                return self._fallback_path(resources)

            # 添加元数据
            path_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            path_data["status"] = "active"
            path_data["current_step"] = 1
            path_data["completed_steps"] = 0

            return path_data

        except Exception as e:
            error(f"AI生成学习路径失败: {str(e)}")
            # 降级方案:简单线性路径
            return self._fallback_path(resources)
    
    def _fallback_path(self, resources: List) -> Dict:
        """降级方案:简单的线性路径"""
        steps = []
        total_time = 0
        
        for i, res in enumerate(resources[:8]):
            step = {
                "step_id": i + 1,
                "title": res.get("title", f"步骤{i+1}"),
                "resource_id": res.get("id"),
                "resource_type": res.get("type"),
                "estimated_time": res.get("duration_minutes", 20),
                "prerequisites": [i] if i > 0 else [],
                "next_steps": [i + 2] if i < len(resources) - 1 else [],
                "description": f"学习{res.get('title')}",
                "learning_objective": "掌握相关知识"
            }
            steps.append(step)
            total_time += step["estimated_time"]
        
        return {
            "path_name": "基础学习路径",
            "description": "按顺序学习所有资源",
            "steps": steps,
            "total_steps": len(steps),
            "estimated_hours": round(total_time / 60, 2),
            "difficulty_progression": "linear",
            "adaptation_notes": "使用默认线性路径",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "current_step": 1,
            "completed_steps": 0
        }
    
    def _save_path(self, user_id: int, path_data: Dict) -> int:
        """保存学习路径到数据库"""
        try:
            from data.db_operations import path_db
            with path_db:
                sql = """
                    INSERT INTO learning_paths
                    (user_id, path_name, description, path_data, current_step, total_steps, estimated_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
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
            error(f"保存学习路径失败: {str(e)}")
            raise
    
    def update_path_progress(self, path_id: int, completed_step: int) -> Dict:
        """更新学习路径进度"""
        try:
            from data.db_operations import path_db
            with path_db:
                # 获取当前路径
                sql = "SELECT path_data, total_steps FROM learning_paths WHERE id = %s"
                path_db.cursor.execute(sql, (path_id,))
                result = path_db.cursor.fetchone()

                if not result:
                    return {"success": False, "message": "路径不存在"}

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
                    SET path_data = %s, current_step = %s, completed_steps = %s, status = %s
                    WHERE id = %s
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
            error(f"更新路径进度失败: {str(e)}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
