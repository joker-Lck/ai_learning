"""
学习效果评估智能体 - 多维度精准评估学习成效
基于实际学生数据（成绩、课程、错题、学习计划）生成评估
"""

import json
from datetime import datetime, timedelta

from core.json_utils import safe_parse_json
from core.logger import error, info
from services.spark_client import spark_client


class AssessmentAgent:
    """学习效果评估智能体"""

    def __init__(self):
        info("学习效果评估智能体初始化完成")

    def assess(self, user_id: int, input_data: dict) -> dict:
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
            # 兼容前端传入的 comprehensive 类型
            if assessment_type == "comprehensive":
                assessment_type = "monthly"
            period_start = input_data.get("period_start")
            period_end = input_data.get("period_end")

            # 如果没有指定日期,自动计算
            if not period_start or not period_end:
                period_start, period_end = self._calculate_period(assessment_type)

            # 收集所有学生数据
            student_data = self._collect_student_data(user_id)

            # AI生成评估报告
            assessment_result = self._generate_assessment_report(
                user_id, student_data, assessment_type, period_start, period_end
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
            error(f"学习效果评估失败: {e!s}")
            return {
                "success": False,
                "message": f"评估失败: {e!s}"
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

    def _collect_student_data(self, user_id: int) -> dict:
        """收集所有学生数据"""
        try:
            from data.db_operations import profile_db

            result = {
                "grades": [],
                "courses": [],
                "error_notes": [],
                "study_plans": [],
                "profile": None,
            }

            with profile_db:
                # 获取成绩数据（所有学期）
                profile_db.cursor.execute(
                    "SELECT * FROM student_grades WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
                result["grades"] = [dict(row) for row in profile_db.cursor.fetchall()] or []

                # 获取课程数据（所有学期）
                profile_db.cursor.execute(
                    "SELECT * FROM course_schedules WHERE user_id = ?",
                    (user_id,)
                )
                result["courses"] = [dict(row) for row in profile_db.cursor.fetchall()] or []

                # 获取错题数据
                profile_db.cursor.execute(
                    "SELECT * FROM error_notes WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
                result["error_notes"] = [dict(row) for row in profile_db.cursor.fetchall()] or []

                # 获取学习计划
                profile_db.cursor.execute(
                    "SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
                result["study_plans"] = [dict(row) for row in profile_db.cursor.fetchall()] or []

                # 获取学生画像
                profile_db.cursor.execute(
                    "SELECT profile_data FROM student_profiles WHERE user_id = ? ORDER BY version DESC LIMIT 1",
                    (user_id,)
                )
                profile_row = profile_db.cursor.fetchone()
                if profile_row:
                    profile_row = dict(profile_row)
                    if profile_row.get("profile_data"):
                        result["profile"] = json.loads(profile_row["profile_data"])

            info(f"收集学生数据完成: 成绩{len(result['grades'])}条, 课程{len(result['courses'])}条, "
                 f"错题{len(result['error_notes'])}条, 计划{len(result['study_plans'])}条")
            return result

        except Exception as e:
            error(f"收集学生数据失败: {e!s}")
            return {"grades": [], "courses": [], "error_notes": [], "study_plans": [], "profile": None}

    def _generate_assessment_report(self, user_id: int, student_data: dict,
                                   assessment_type: str,
                                   period_start: str, period_end: str) -> dict:
        """通过AI生成评估报告"""

        # 构建数据摘要
        grades = student_data["grades"]
        courses = student_data["courses"]
        error_notes = student_data["error_notes"]
        study_plans = student_data["study_plans"]
        profile = student_data["profile"]

        # 成绩统计
        grade_summary = ""
        if grades:
            scores = [g.get("score", 0) for g in grades if g.get("score")]
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            grade_items = []
            for g in grades[:10]:  # 最近10条
                grade_items.append(f"- {g.get('course_name', '未知')}: {g.get('score', 'N/A')}分 ({g.get('semester', '')})")
            grade_summary = f"""
成绩统计:
- 总课程数: {len(grades)}
- 平均分: {avg_score:.1f}
- 最高分: {max_score}
- 最低分: {min_score}
成绩明细(最近):
{chr(10).join(grade_items)}
"""
        else:
            grade_summary = "暂无成绩数据"

        # 课程统计
        course_summary = ""
        if courses:
            course_names = []
            for c in courses:
                if isinstance(c.get("courses"), str):
                    try:
                        course_list = json.loads(c["courses"])
                        for cl in course_list:
                            course_names.append(cl.get("name", ""))
                    except (json.JSONDecodeError, TypeError, KeyError):
                        pass
            course_summary = f"本学期课程: {', '.join(set(course_names)) if course_names else '暂无'}"
        else:
            course_summary = "暂无课程数据"

        # 错题统计
        error_summary = ""
        if error_notes:
            mastered = sum(1 for e in error_notes if e.get("mastery"))
            error_summary = f"""
错题统计:
- 总错题数: {len(error_notes)}
- 已掌握: {mastered}
- 未掌握: {len(error_notes) - mastered}
- 掌握率: {mastered/len(error_notes)*100:.1f}%
"""
        else:
            error_summary = "暂无错题数据"

        # 学习计划
        plan_summary = ""
        if study_plans:
            plan_items = []
            for p in study_plans[:3]:
                plan_items.append(f"- {p.get('title', '未命名')} ({p.get('plan_type', '')})")
            plan_summary = f"学习计划:\n{chr(10).join(plan_items)}"
        else:
            plan_summary = "暂无学习计划"

        # 画像信息
        profile_summary = ""
        if profile:
            profile_summary = f"""
学生画像:
- 专业: {profile.get('major', '未填写')}
- 年级: {profile.get('grade_level', '未填写')}
- 认知风格: {profile.get('cognitive_style', '未填写')}
- 学习目标: {', '.join(profile.get('learning_goals', []))}
- 兴趣领域: {', '.join(profile.get('interest_areas', []))}
- 薄弱点: {', '.join(profile.get('weak_points', []))}
"""
        else:
            profile_summary = "暂无学生画像"

        prompt = f"""你是一位资深的教育评估专家。请基于以下学生的真实学习数据，生成一份详细、专业、有深度的学习效果评估报告。

评估周期: {period_start} 至 {period_end}
评估类型: {assessment_type}

=== 学生数据 ===
{grade_summary}

{course_summary}

{error_summary}

{plan_summary}

{profile_summary}

=== 评估要求 ===
1. 基于真实数据分析，不要编造数据
2. 多维度评估：知识掌握度、学习态度、薄弱环节、进步空间
3. 针对具体课程和错题给出分析
4. 提供可操作的改进建议
5. 给出综合评分(0-100)，评分要合理，基于实际数据

严格输出JSON格式(不要输出其他内容):
{{
    "overall_score": 82,
    "grade": "良好",
    "dimensions": [
        {{"name": "知识掌握", "score": 85, "max_score": 100, "level": "良好", "feedback": "基于成绩分析的具体评价"}},
        {{"name": "学习态度", "score": 70, "max_score": 100, "level": "中等", "feedback": "基于课程和计划的分析"}},
        {{"name": "薄弱环节", "score": 60, "max_score": 100, "level": "中等", "feedback": "基于错题的分析"}},
        {{"name": "进步空间", "score": 75, "max_score": 100, "level": "良好", "feedback": "综合评估"}}
    ],
    "knowledge_mastery": {{
        "overall_score": 0.75,
        "topics": {{"高等数学": 0.85, "英语": 0.65}}
    }},
    "skill_progress": {{
        "improvement_areas": ["需要提升的具体技能"],
        "progress_rate": 0.15
    }},
    "engagement_level": 0.85,
    "time_investment": 10.5,
    "strengths": ["具体优势1", "具体优势2"],
    "weaknesses": ["具体不足1", "具体不足2"],
    "improvements": ["具体改进建议1", "具体改进建议2"],
    "recommendations": ["具体学习建议1", "具体学习建议2"],
    "recommendation": "综合建议文本，要详细有深度",
    "next_focus": ["下一步重点1", "下一步重点2"],
    "motivational_message": "鼓励性话语",
    "grade_trend": "上升/稳定/下降",
    "analysis_summary": "详细的分析总结文字，200字以上，要体现专业性和针对性"
}}
"""

        try:
            response = spark_client.advanced(prompt, max_tokens=3000)
            if not response or response.startswith("错误:"):
                error(f"AI 调用失败: {response}")
                return self._fallback_assessment(student_data, period_start, period_end)

            assessment_data = safe_parse_json(response)

            if not isinstance(assessment_data, dict):
                error(f"AI 返回非 dict: type={type(assessment_data).__name__}, response[:200]={str(response)[:200]}")
                return self._fallback_assessment(student_data, period_start, period_end)

            # 添加元数据
            assessment_data["assessment_type"] = assessment_type
            assessment_data["period_start"] = period_start
            assessment_data["period_end"] = period_end
            assessment_data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 添加原始数据供前端绘图
            assessment_data["raw_data"] = {
                "grades": grades,
                "error_notes_count": len(error_notes),
                "courses_count": len(courses),
                "plans_count": len(study_plans),
            }

            return assessment_data

        except Exception as e:
            error(f"生成评估报告失败: {e!s}，使用降级方案")
            return self._fallback_assessment(student_data, period_start, period_end)

    def _fallback_assessment(self, student_data: dict, period_start: str, period_end: str) -> dict:
        """降级方案:基于实际学生数据生成多维度评估"""

        grades = student_data.get("grades", [])
        error_notes = student_data.get("error_notes", [])
        courses = student_data.get("courses", [])
        study_plans = student_data.get("study_plans", [])

        # 成绩统计
        scores = [g.get("score", 0) for g in grades if g.get("score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0

        # 错题统计
        mastered_count = sum(1 for e in error_notes if e.get("mastery"))
        error_count = len(error_notes)
        mastery_rate = mastered_count / error_count if error_count > 0 else 0

        # 课程统计
        course_count = len(courses)

        # 多维度评分
        knowledge_score = round(avg_score, 1) if avg_score > 0 else 50.0
        attitude_score = min(100, round(course_count * 15 + len(study_plans) * 10))
        weakness_score = round(mastery_rate * 100) if error_count > 0 else 50.0
        progress_score = round(knowledge_score * 0.5 + attitude_score * 0.3 + weakness_score * 0.2)

        overall_score = round(progress_score)
        overall_score = max(0, min(100, overall_score))

        grade = "优秀" if overall_score >= 90 else "良好" if overall_score >= 75 else "中等" if overall_score >= 60 else "待提升"

        # 主题掌握度
        topics = {}
        for g in grades:
            name = g.get("course_name", "")
            score = g.get("score", 0)
            if name and score:
                topics[name] = round(score / 100, 2)

        if not topics:
            topics = {"综合学习": 0.5}

        # 优势与不足
        strengths = []
        weaknesses = []

        if avg_score >= 80:
            strengths.append(f"平均成绩 {avg_score:.1f} 分，学习基础扎实")
        if course_count >= 5:
            strengths.append(f"选修 {course_count} 门课程，学习覆盖面广")
        if mastery_rate >= 0.7:
            strengths.append(f"错题掌握率 {mastery_rate*100:.0f}%，复习效果好")
        if len(study_plans) > 0:
            strengths.append("有学习计划，学习有规划")

        if avg_score < 60 and avg_score > 0:
            weaknesses.append(f"平均分 {avg_score:.1f}，需要加强基础")
        if error_count > 0 and mastery_rate < 0.5:
            weaknesses.append(f"错题掌握率仅 {mastery_rate*100:.0f}%，需加强复习")
        if course_count == 0:
            weaknesses.append("暂无课程数据，建议完善课表")
        if len(study_plans) == 0:
            weaknesses.append("暂无学习计划，建议制定学习规划")

        if not strengths:
            strengths.append("已开始记录学习数据，这是进步的第一步")
        if not weaknesses:
            weaknesses.append("可以尝试更多学习活动来全面评估")

        # 建议
        recommendations = []
        if avg_score < 70 and avg_score > 0:
            recommendations.append("建议针对低分课程进行重点复习")
        if error_count > 0 and mastery_rate < 0.7:
            recommendations.append(f"还有 {error_count - mastered_count} 道错题未掌握，建议定期复习")
        if len(study_plans) == 0:
            recommendations.append("建议制定学期学习计划，明确学习目标")
        recommendations.append("保持学习记录，便于持续跟踪学习进度")

        next_focus = []
        weak_courses = [g.get("course_name") for g in grades if g.get("score", 100) < 70]
        if weak_courses:
            next_focus.append(f"重点提升: {', '.join(weak_courses[:3])}")
        if error_count > mastered_count:
            next_focus.append(f"复习未掌握的 {error_count - mastered_count} 道错题")
        next_focus.append("巩固已学知识，预习新内容")

        # 成绩趋势数据（供前端绘图）
        grade_trend = []
        for g in sorted(grades, key=lambda x: x.get("created_at", "")):
            if g.get("score"):
                grade_trend.append({
                    "course": g.get("course_name", ""),
                    "score": g.get("score", 0),
                    "semester": g.get("semester", ""),
                })

        return {
            "overall_score": overall_score,
            "grade": grade,
            "knowledge_mastery": {
                "overall_score": round(knowledge_score / 100, 2),
                "topics": topics,
            },
            "skill_progress": {
                "improvement_areas": [t for t in topics if topics[t] < 0.6] or ["综合能力"],
                "progress_rate": round(progress_score / 100, 2),
            },
            "engagement_level": round(min(course_count / 8, 1.0), 2),
            "time_investment": 0,
            "dimensions": [
                {
                    "name": "知识掌握",
                    "score": knowledge_score,
                    "max_score": 100,
                    "level": "优秀" if knowledge_score >= 85 else "良好" if knowledge_score >= 70 else "中等" if knowledge_score >= 50 else "待提升",
                    "feedback": f"平均得分 {avg_score:.1f} 分，共 {len(scores)} 门课程有成绩" if scores else "暂无成绩数据",
                },
                {
                    "name": "学习态度",
                    "score": attitude_score,
                    "max_score": 100,
                    "level": "优秀" if attitude_score >= 85 else "良好" if attitude_score >= 60 else "中等" if attitude_score >= 30 else "待提升",
                    "feedback": f"已录入 {course_count} 门课程，{len(study_plans)} 个学习计划",
                },
                {
                    "name": "薄弱环节",
                    "score": weakness_score,
                    "max_score": 100,
                    "level": "优秀" if weakness_score >= 85 else "良好" if weakness_score >= 60 else "中等" if weakness_score >= 30 else "待提升",
                    "feedback": f"错题 {error_count} 道，已掌握 {mastered_count} 道" if error_count > 0 else "暂无错题数据",
                },
                {
                    "name": "进步空间",
                    "score": progress_score,
                    "max_score": 100,
                    "level": "优秀" if progress_score >= 85 else "良好" if progress_score >= 60 else "中等" if progress_score >= 30 else "待提升",
                    "feedback": "综合评估各项指标",
                },
            ],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvements": weaknesses,
            "recommendations": recommendations,
            "recommendation": "；".join(recommendations),
            "next_focus": next_focus,
            "motivational_message": self._get_motivational_message(overall_score, len(grades)),
            "grade_trend": "上升" if avg_score >= 75 else "稳定" if avg_score >= 60 else "需努力",
            "analysis_summary": f"基于 {len(grades)} 门课程成绩、{error_count} 道错题、{len(study_plans)} 个学习计划的综合评估。平均分 {avg_score:.1f} 分，错题掌握率 {mastery_rate*100:.0f}%。" + ("建议加强薄弱环节的学习。" if avg_score < 70 else "学习状态良好，继续保持。"),
            "raw_data": {
                "grades": grades,
                "grade_trend": grade_trend,
                "error_notes_count": error_count,
                "courses_count": course_count,
                "plans_count": len(study_plans),
            },
            "assessment_type": "auto_generated",
            "period_start": period_start,
            "period_end": period_end,
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

    def _save_assessment(self, user_id: int, assessment_data: dict,
                        assessment_type: str, period_start: str,
                        period_end: str) -> int:
        """保存评估结果到数据库"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                sql = """
                    INSERT INTO learning_assessments
                    (user_id, assessment_type, assessment_data, period_start, period_end, overall_score)
                    VALUES (?, ?, ?, ?, ?, ?)
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
            error(f"保存评估结果失败: {e!s}")
            raise

    def _get_user_profile(self, user_id: int) -> dict | None:
        """获取用户画像"""
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
            error(f"获取用户画像失败: {e!s}")
            return None
