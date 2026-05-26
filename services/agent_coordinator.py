"""
多智能体协调器 - 负责任务分发、智能体调度、结果整合
实现多智能体协同工作机制
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.logger import info, error, debug
from services.profile_agent import ProfileAgent
from services.resource_agent import ResourceAgent
from services.path_agent import PathAgent
from services.tutor_agent import TutorAgent
from services.assessment_agent import AssessmentAgent


class AgentCoordinator:
    """智能体协调器 - 多智能体系统的核心控制器"""
    
    def __init__(self):
        # 初始化各专业智能体
        self.profile_agent = ProfileAgent()
        self.resource_agent = ResourceAgent()
        self.path_agent = PathAgent()
        self.tutor_agent = TutorAgent()
        self.assessment_agent = AssessmentAgent()
        
        info("多智能体协调器初始化完成")
    
    def execute_task(self, 
                    task_type: str, 
                    user_id: int,
                    input_data: Dict[str, Any],
                    session_id: str = None) -> Dict[str, Any]:
        """
        执行任务 - 根据任务类型调度相应智能体
        
        Args:
            task_type: 任务类型 (build_profile/generate_resource/plan_path/tutor/assess)
            user_id: 用户ID
            input_data: 输入数据
            session_id: 会话ID
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        if not session_id:
            session_id = f"session_{int(time.time())}_{user_id}"
        
        result = {
            "success": False,
            "session_id": session_id,
            "task_type": task_type,
            "data": None,
            "message": "",
            "execution_time_ms": 0
        }
        
        try:
            info(f"开始执行任务: {task_type}, 用户: {user_id}, 会话: {session_id}")
            
            if task_type == "build_profile":
                # 构建学生画像
                result["data"] = self._build_student_profile(user_id, input_data)
                result["success"] = True
                result["message"] = "学生画像构建成功"
                
            elif task_type == "generate_resources":
                # 生成多模态学习资源
                result["data"] = self._generate_learning_resources(user_id, input_data)
                result["success"] = True
                result["message"] = f"成功生成 {len(result['data']['resources'])} 个学习资源"
                
            elif task_type == "plan_learning_path":
                # 规划学习路径
                result["data"] = self._plan_learning_path(user_id, input_data)
                result["success"] = True
                result["message"] = "个性化学习路径规划完成"
                
            elif task_type == "tutor_query":
                # 智能辅导答疑
                result["data"] = self._tutor_answer(user_id, input_data)
                result["success"] = True
                result["message"] = "智能辅导回答生成完成"
                
            elif task_type == "assess_learning":
                # 学习效果评估
                result["data"] = self._assess_learning(user_id, input_data)
                result["success"] = True
                result["message"] = "学习效果评估完成"
                
            elif task_type == "comprehensive_learning_plan":
                # 综合学习计划(多智能体协同)
                result["data"] = self._comprehensive_plan(user_id, input_data)
                result["success"] = True
                result["message"] = "综合学习计划生成完成"
                
            else:
                result["message"] = f"未知任务类型: {task_type}"
                error(f"未知任务类型: {task_type}")
            
        except Exception as e:
            result["message"] = f"任务执行失败: {str(e)}"
            error(f"任务执行失败 [{task_type}]: {str(e)}")
        
        finally:
            execution_time = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time
            
            # 记录协作日志
            self._log_collaboration(session_id, user_id, task_type, input_data, result)
            
            info(f"任务完成: {task_type}, 耗时: {execution_time}ms")
        
        return result
    
    def _build_student_profile(self, user_id: int, input_data: Dict) -> Dict:
        """构建学生画像 - 调用画像智能体"""
        return self.profile_agent.build_profile(user_id, input_data)
    
    def _generate_learning_resources(self, user_id: int, input_data: Dict) -> Dict:
        """生成学习资源 - 调用资源智能体"""
        return self.resource_agent.generate_resources(user_id, input_data)
    
    def _plan_learning_path(self, user_id: int, input_data: Dict) -> Dict:
        """规划学习路径 - 调用路径智能体"""
        return self.path_agent.plan_path(user_id, input_data)
    
    def _tutor_answer(self, user_id: int, input_data: Dict) -> Dict:
        """智能辅导 - 调用辅导智能体"""
        return self.tutor_agent.answer_query(user_id, input_data)
    
    def _assess_learning(self, user_id: int, input_data: Dict) -> Dict:
        """学习效果评估 - 调用评估智能体"""
        return self.assessment_agent.assess(user_id, input_data)
    
    def _comprehensive_plan(self, user_id: int, input_data: Dict) -> Dict:
        """
        综合学习计划 - 多智能体协同工作
        1. 分析学生画像
        2. 生成针对性资源
        3. 规划学习路径
        4. 整合输出
        """
        info(f"开始综合学习计划, 用户: {user_id}")
        
        # Step 1: 获取或构建学生画像
        profile_data = input_data.get("profile")
        if not profile_data:
            profile_result = self.profile_agent.get_or_build_profile(user_id)
            profile_data = profile_result.get("profile")
        
        # Step 2: 基于画像生成资源
        resource_input = {
            "subject": input_data.get("subject"),
            "topic": input_data.get("topic"),
            "profile": profile_data,
            "resource_types": input_data.get("resource_types", ["document", "quiz", "mindmap"])
        }
        resources_result = self.resource_agent.generate_resources(user_id, resource_input)
        
        # Step 3: 基于资源和画像规划路径
        path_input = {
            "profile": profile_data,
            "resources": resources_result.get("resources", []),
            "learning_goal": input_data.get("learning_goal")
        }
        path_result = self.path_agent.plan_path(user_id, path_input)
        
        # Step 4: 整合结果
        comprehensive_result = {
            "profile": profile_data,
            "resources": resources_result.get("resources", []),
            "learning_path": path_result.get("path"),
            "recommendations": self._generate_recommendations(profile_data, resources_result, path_result),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        info(f"综合学习计划完成, 生成 {len(comprehensive_result['resources'])} 个资源")
        return comprehensive_result
    
    def _generate_recommendations(self, profile, resources_result, path_result) -> List[str]:
        """基于画像、资源和路径生成学习建议"""
        recommendations = []
        
        # 基于认知风格推荐
        cognitive_style = profile.get("cognitive_style", "")
        if "视觉" in cognitive_style:
            recommendations.append("建议优先观看视频资源,配合图表学习")
        elif "听觉" in cognitive_style:
            recommendations.append("建议通过讲解音频和讨论加深理解")
        elif "动觉" in cognitive_style:
            recommendations.append("建议多做实操练习和项目实践")
        
        # 基于薄弱点推荐
        weak_points = profile.get("weak_points", [])
        if weak_points:
            recommendations.append(f"重点关注薄弱环节: {', '.join(weak_points[:3])}")
        
        # 基于学习路径推荐
        if path_result.get("path"):
            total_steps = path_result["path"].get("total_steps", 0)
            estimated_hours = path_result["path"].get("estimated_hours", 0)
            recommendations.append(f"学习路径包含 {total_steps} 个步骤,预计需要 {estimated_hours} 小时")
        
        return recommendations
    
    def _log_collaboration(self, session_id: str, user_id: int, 
                          task_type: str, input_data: Dict, result: Dict):
        """记录智能体协作日志"""
        try:
            from data.db_operations import db
            
            log_data = {
                "session_id": session_id,
                "user_id": user_id,
                "task_type": task_type,
                "coordinator_input": {
                    "task_type": task_type,
                    "input_summary": str(input_data)[:500]  # 限制长度
                },
                "final_result": {
                    "success": result["success"],
                    "message": result["message"],
                    "execution_time_ms": result["execution_time_ms"]
                },
                "status": "success" if result["success"] else "failed",
                "error_message": result.get("message") if not result["success"] else None
            }
            
            # 这里可以保存到数据库,暂时只记录日志
            debug(f"协作日志: {json.dumps(log_data, ensure_ascii=False)}")
            
        except Exception as e:
            error(f"记录协作日志失败: {str(e)}")


# 全局协调器实例
agent_coordinator = AgentCoordinator()
