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

严格输出JSON格式(不要输出其他内容):
{{
    "overall_score": 82,
    "grade": "良好",
    "dimensions": [
        {{"name": "知识掌握", "score": 85, "max_score": 100, "level": "良好", "feedback": "具体评价"}},
        {{"name": "学习参与度", "score": 70, "max_score": 100, "level": "中等", "feedback": "具体评价"}},
        {{"name": "时间投入", "score": 60, "max_score": 100, "level": "中等", "feedback": "具体评价"}},
        {{"name": "技能进步", "score": 75, "max_score": 100, "level": "良好", "feedback": "具体评价"}}
    ],
    "knowledge_mastery": {{
        "overall_score": 0.75,
        "topics": {{"主题1": 0.85, "主题2": 0.65}}
    }},
    "skill_progress": {{
        "improvement_areas": ["技能1", "技能2"],
        "progress_rate": 0.15
    }},
    "engagement_level": 0.85,
    "time_investment": {learning_data['total_duration_hours']},
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "improvements": ["改进建议1", "改进建议2"],
    "recommendations": ["学习建议1", "学习建议2"],
    "recommendation": "综合建议文本",
    "next_focus": ["下一步重点1", "下一步重点2"],
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
        """降级方案:基于实际学习数据生成多维度评估"""

        total_hours = learning_data["total_duration_hours"]
        avg_score = learning_data["average_score"]
        total_activities = learning_data["total_activities"]
        activity_stats = learning_data.get("activity_stats", {})
        activities = learning_data.get("activities", [])

        # ── 多维度评分计算 ──
        # 知识掌握度：基于平均分
        knowledge_score = round(avg_score, 1) if avg_score > 0 else 50.0
        # 参与度：基于活动次数（10次=满分）
        engagement = round(min(total_activities / 10, 1.0) * 100, 1)
        # 时间投入：基于学习时长（10h=满分）
        time_score = round(min(total_hours / 10, 1.0) * 100, 1)
        # 技能进步：基于有分数的活动占比
        scored_activities = [a for a in activities if a.get("score")]
        progress_rate = round(min(len(scored_activities) / max(total_activities, 1), 1.0) * 100, 1)

        # 综合评分
        overall_score = round(
            knowledge_score * 0.4 + engagement * 0.3 + time_score * 0.2 + progress_rate * 0.1, 1
        )
        overall_score = max(0, min(100, overall_score))

        if overall_score >= 90:
            grade = "优秀"
        elif overall_score >= 75:
            grade = "良好"
        elif overall_score >= 60:
            grade = "中等"
        else:
            grade = "待提升"

        # ── 从活动数据提取知识点 ──
        topics = {}
        for act_type, stats in activity_stats.items():
            type_name = {
                "quiz": "测验练习", "reading": "阅读学习", "practice": "实践操作",
                "video": "视频学习", "discussion": "讨论交流", "review": "复习巩固",
            }.get(act_type, act_type)
            # 该类型的活动频率作为掌握度参考
            mastery = round(min(stats["count"] / 5, 1.0) * 0.9 + 0.1, 2)
            topics[type_name] = mastery

        # 如果没有任何活动数据，给默认维度
        if not topics:
            topics = {"综合学习": 0.5}

        # ── 识别优势与不足 ──
        strengths = []
        weaknesses = []

        if total_activities >= 5:
            strengths.append(f"学习频率较高，共完成 {total_activities} 次学习活动")
        if total_hours >= 3:
            strengths.append(f"学习时长充足，累计投入 {total_hours} 小时")
        if avg_score >= 80:
            strengths.append(f"平均得分 {avg_score} 分，知识掌握扎实")
        if engagement >= 60:
            strengths.append("学习参与度良好，保持了持续学习的习惯")

        if total_activities < 3:
            weaknesses.append("学习活动偏少，建议增加学习频率")
        if total_hours < 1:
            weaknesses.append("学习时长不足，建议每天投入更多时间")
        if avg_score < 60 and avg_score > 0:
            weaknesses.append(f"平均得分 {avg_score} 分，需要加强薄弱环节")
        if engagement < 40:
            weaknesses.append("学习参与度偏低，建议制定规律的学习计划")

        # 确保至少各有一条
        if not strengths:
            strengths.append("已开始学习旅程，这是进步的第一步")
        if not weaknesses:
            weaknesses.append("可以尝试更多不同类型的学习活动")

        # ── 改进建议 ──
        recommendations = []
        if total_activities < 5:
            recommendations.append("建议每周至少完成 5 次学习活动，保持学习节奏")
        if total_hours < 3:
            recommendations.append("建议每天投入 30 分钟以上进行系统学习")
        if avg_score < 70 and avg_score > 0:
            recommendations.append("建议针对薄弱知识点进行专项练习和复习")
        if len(activity_stats) < 2:
            recommendations.append("建议尝试多种学习方式（阅读、测验、实践），全面提升能力")
        recommendations.append("定期进行自我评估，跟踪学习进度")

        # ── 下一步重点 ──
        next_focus = ["巩固已学基础知识"]
        if avg_score < 70 and avg_score > 0:
            next_focus.append("重点复习得分较低的知识点")
        if total_activities < 5:
            next_focus.append("增加学习频率，养成每日学习习惯")
        next_focus.append("尝试更具挑战性的学习内容")

        return {
            "overall_score": overall_score,
            "grade": grade,
            "knowledge_mastery": {
                "overall_score": round(knowledge_score / 100, 2),
                "topics": topics,
            },
            "skill_progress": {
                "improvement_areas": [t for t in topics if topics[t] < 0.6] or ["综合能力"],
                "progress_rate": round(progress_rate / 100, 2),
            },
            "engagement_level": round(engagement / 100, 2),
            "time_investment": total_hours,
            "dimensions": [
                {
                    "name": "知识掌握",
                    "score": knowledge_score,
                    "max_score": 100,
                    "level": "优秀" if knowledge_score >= 85 else "良好" if knowledge_score >= 70 else "中等" if knowledge_score >= 50 else "待提升",
                    "feedback": f"平均得分 {avg_score} 分" if avg_score > 0 else "暂无测验数据",
                },
                {
                    "name": "学习参与度",
                    "score": engagement,
                    "max_score": 100,
                    "level": "优秀" if engagement >= 85 else "良好" if engagement >= 60 else "中等" if engagement >= 30 else "待提升",
                    "feedback": f"完成 {total_activities} 次学习活动",
                },
                {
                    "name": "时间投入",
                    "score": time_score,
                    "max_score": 100,
                    "level": "优秀" if time_score >= 85 else "良好" if time_score >= 60 else "中等" if time_score >= 30 else "待提升",
                    "feedback": f"累计学习 {total_hours} 小时",
                },
                {
                    "name": "技能进步",
                    "score": progress_rate,
                    "max_score": 100,
                    "level": "优秀" if progress_rate >= 85 else "良好" if progress_rate >= 60 else "中等" if progress_rate >= 30 else "待提升",
                    "feedback": f"完成 {len(scored_activities)} 次有评分的学习",
                },
            ],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": weaknesses,
            "recommendations": recommendations,
            "recommendation": "；".join(recommendations),
            "next_focus": next_focus,
            "motivational_message": self._get_motivational_message(overall_score, total_activities),
            "assessment_type": "auto_generated",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_motivational_message(self, score: float, activities: int) -> str:
        """根据评分生成鼓励话语"""
        if score >= 90:
            return "太棒了！你的学习表现非常出色，继续保持！"
        elif score >= 75:
            return "做得很好！你正在稳步进步，再加把劲就能更上一层楼！"
        elif score >= 60:
            return "不错的开始！坚持学习，你会看到明显的进步。"
        elif activities > 0:
            return "每一步都是进步！制定一个学习计划，你会发现自己的潜力。"
        else:
            return "学习旅程从第一步开始！今天就开始你的学习吧。"
    
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
