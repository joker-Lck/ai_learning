"""
学习效果评估智能体 - 多维度精准评估学习成效
"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from core.logger import info, error
from core.json_utils import safe_parse_json
from services.qa_service import qa_service


class AssessmentAgent:
    """学习效果评估智能体"""
    
    def __init__(self):
        info("学习效果评估智能体初始化完成")
    
    def assess(self, user_id: int, input_data: Dict) -> Dict:
        """
        评估学习效果
        
        Args:
            user_id: 用户ID
            input_data: {
                "assessment_type": weekly/monthly/custom,
                "period_start": 开始日期,
                "period_end": 结束日期
            }
            
        Returns:
            评估结果
        """
        info(f"开始学习效果评估, 用户: {user_id}")
        
        try:
            assessment_type = input_data.get("assessment_type", "weekly")
            period_start = input_data.get("period_start")
            period_end = input_data.get("period_end")
            
            # 如果没有指定日期,自动计算
            if not period_start or not period_end:
                period_start, period_end = self._calculate_period(assessment_type)
            
            # 收集学习数据
            learning_data = self._collect_learning_data(user_id, period_start, period_end)
            
            # 获取学生画像
            profile = self._get_user_profile(user_id)
            
            # AI生成评估报告
            assessment_result = self._generate_assessment_report(
                user_id, learning_data, profile, assessment_type, period_start, period_end
            )
            
            # 保存到数据库
            assessment_id = self._save_assessment(user_id, assessment_result, 
                                                  assessment_type, period_start, period_end)
            
            result = {
                "success": True,
                "assessment_id": assessment_id,
                "assessment": assessment_result,
                "data": {"assessment": assessment_result},
                "message": f"{assessment_type}评估完成"
            }
            
            info(f"学习效果评估完成, ID: {assessment_id}")
            return result
            
        except Exception as e:
            error(f"学习效果评估失败: {str(e)}")
            return {
                "success": False,
                "message": f"评估失败: {str(e)}"
            }
    
    def _calculate_period(self, assessment_type: str):
        """计算评估周期"""
        end_date = datetime.now()
        
        if assessment_type == "weekly":
            start_date = end_date - timedelta(days=7)
        elif assessment_type == "monthly":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        return (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
    
    def _collect_learning_data(self, user_id: int, period_start: str,
                              period_end: str) -> Dict:
        """收集学习数据"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                # 查询学习行为记录
                sql = """
                    SELECT activity_type, duration_seconds, score, progress_percentage, metadata
                    FROM learning_activities
                    WHERE user_id = %s AND created_at >= %s AND created_at <= %s
                    ORDER BY created_at DESC
                """
                assessment_db.cursor.execute(sql, (user_id, period_start, period_end))
                activities = assessment_db.cursor.fetchall()

            # 统计分析
            total_duration = sum(a.get("duration_seconds", 0) for a in activities)
            total_activities = len(activities)

            # 按类型统计
            activity_stats = {}
            for activity in activities:
                act_type = activity["activity_type"]
                if act_type not in activity_stats:
                    activity_stats[act_type] = {"count": 0, "total_duration": 0}
                activity_stats[act_type]["count"] += 1
                activity_stats[act_type]["total_duration"] += activity.get("duration_seconds", 0)

            # 计算平均得分
            scores = [a.get("score") for a in activities if a.get("score")]
            avg_score = sum(scores) / len(scores) if scores else 0

            return {
                "activities": activities,
                "total_duration_hours": round(total_duration / 3600, 2),
                "total_activities": total_activities,
                "activity_stats": activity_stats,
                "average_score": round(avg_score, 2),
                "period_start": period_start,
                "period_end": period_end
            }

        except Exception as e:
            error(f"收集学习数据失败: {str(e)}")
            return {
                "activities": [],
                "total_duration_hours": 0,
                "total_activities": 0,
                "activity_stats": {},
                "average_score": 0,
                "period_start": period_start,
                "period_end": period_end
            }
    
    def _generate_assessment_report(self, user_id: int, learning_data: Dict,
                                   profile: Dict, assessment_type: str,
                                   period_start: str, period_end: str) -> Dict:
        """通过AI生成评估报告"""
        
        # 构建学习数据摘要
        data_summary = {
            "total_study_hours": learning_data["total_duration_hours"],
            "total_activities": learning_data["total_activities"],
            "average_score": learning_data["average_score"],
            "activity_breakdown": learning_data["activity_stats"]
        }
        
        prompt = f"""请基于以下学习数据,生成一份详细的学习效果评估报告。

评估周期: {period_start} 至 {period_end}
评估类型: {assessment_type}

学生学习数据:
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

学生画像信息:
{json.dumps(profile, ensure_ascii=False, indent=2) if profile else '无'}

要求:
1. 多维度评估:知识掌握度、技能进步、参与度、时间投入等
2. 识别学生的优势和不足
3. 提供具体的改进建议
4. 推荐下一步学习重点
5. 给出综合评分(0-100)

输出JSON格式:
{{
    "knowledge_mastery": {{
        "overall_score": 0.75,
        "topics": {{
            "主题1": 0.85,
            "主题2": 0.65
        }}
    }},
    "skill_progress": {{
        "improvement_areas": ["技能1", "技能2"],
        "progress_rate": 0.15
    }},
    "engagement_level": 0.85,
    "time_investment": {learning_data['total_duration_hours']},
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "recommendation": "详细的改进建议",
    "next_focus": ["下一步重点1", "下一步重点2"],
    "overall_score": 82,
    "grade": "良好",
    "motivational_message": "鼓励性话语"
}}
"""
        
        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            assessment_data = safe_parse_json(response)
            
            # 添加元数据
            assessment_data["assessment_type"] = assessment_type
            assessment_data["period_start"] = period_start
            assessment_data["period_end"] = period_end
            assessment_data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return assessment_data
            
        except Exception as e:
            error(f"生成评估报告失败: {str(e)}")
            # 降级方案:简单评估
            return self._fallback_assessment(learning_data)
    
    def _fallback_assessment(self, learning_data: Dict) -> Dict:
        """降级方案:基于数据的简单评估"""
        
        total_hours = learning_data["total_duration_hours"]
        avg_score = learning_data["average_score"]
        total_activities = learning_data["total_activities"]
        
        # 简单计算综合评分
        engagement = min(total_activities / 10, 1.0)  # 假设10次活动为满分
        time_score = min(total_hours / 10, 1.0)  # 假设10小时为满分
        overall_score = round((avg_score * 0.4 + engagement * 30 + time_score * 30), 2)
        
        if overall_score >= 90:
            grade = "优秀"
        elif overall_score >= 75:
            grade = "良好"
        elif overall_score >= 60:
            grade = "中等"
        else:
            grade = "待提升"
        
        return {
            "knowledge_mastery": {
                "overall_score": round(avg_score / 100, 2),
                "topics": {}
            },
            "skill_progress": {
                "improvement_areas": [],
                "progress_rate": 0.1
            },
            "engagement_level": round(engagement, 2),
            "time_investment": total_hours,
            "strengths": ["学习态度积极"],
            "weaknesses": ["需要更多练习"],
            "recommendation": "建议增加学习时间,多做练习题",
            "next_focus": ["基础知识巩固"],
            "overall_score": overall_score,
            "grade": grade,
            "motivational_message": "继续努力,你会越来越棒!",
            "assessment_type": "auto_generated",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _save_assessment(self, user_id: int, assessment_data: Dict,
                        assessment_type: str, period_start: str,
                        period_end: str) -> int:
        """保存评估结果到数据库"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                sql = """
                    INSERT INTO learning_assessments
                    (user_id, assessment_type, assessment_data, period_start, period_end, overall_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                assessment_db.cursor.execute(sql, (
                    user_id,
                    assessment_type,
                    json.dumps(assessment_data, ensure_ascii=False),
                    period_start,
                    period_end,
                    assessment_data.get("overall_score", 0)
                ))

                assessment_id = assessment_db.cursor.lastrowid
                assessment_db.conn.commit()

                info(f"评估结果保存成功, ID: {assessment_id}")
                return assessment_id

        except Exception as e:
            error(f"保存评估结果失败: {str(e)}")
            raise
    
    def _get_user_profile(self, user_id: int) -> Optional[Dict]:
        """获取用户画像"""
        try:
            from data.db_operations import profile_db
            with profile_db:
                sql = "SELECT profile_data FROM student_profiles WHERE user_id = %s ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql, (user_id,))
                result = profile_db.cursor.fetchone()

                if result and result.get("profile_data"):
                    return json.loads(result["profile_data"])
                return None

        except Exception as e:
            error(f"获取用户画像失败: {str(e)}")
            return None
