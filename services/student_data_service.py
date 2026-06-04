"""
学生数据服务 — 课程表 / 成绩 / 错题 / 学习计划 CRUD + AI 学习规划生成
"""

import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from core.logger import info, error
from data.db_operations import profile_db
from services.qa_service import qa_service


class StudentDataService:
    """学生课程/成绩/错题/学习计划管理"""

    # ==================== 学期课程表 ====================

    def save_course_schedule(self, user_id: int, semester: str, courses: List[Dict]) -> Dict:
        """保存/更新学期课程表"""
        try:
            profile_db.connect()
            # UPSERT
            sql = """
                INSERT INTO course_schedules (user_id, semester, courses)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE courses = VALUES(courses), updated_at = NOW()
            """
            profile_db.cursor.execute(sql, (user_id, semester, json.dumps(courses, ensure_ascii=False)))
            profile_db.conn.commit()
            info(f"课程表保存成功: user={user_id}, semester={semester}")
            return {"success": True, "message": "课程表保存成功"}
        except Exception as e:
            error(f"课程表保存失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    def get_course_schedule(self, user_id: int, semester: str) -> Dict:
        """获取指定学期课程表"""
        try:
            profile_db.connect()
            sql = "SELECT * FROM course_schedules WHERE user_id = %s AND semester = %s"
            profile_db.cursor.execute(sql, (user_id, semester))
            row = profile_db.cursor.fetchone()
            if row:
                row['courses'] = json.loads(row['courses']) if isinstance(row['courses'], str) else row['courses']
                return {"success": True, "data": row}
            return {"success": True, "data": None}
        except Exception as e:
            error(f"获取课程表失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    def list_semesters(self, user_id: int) -> Dict:
        """列出用户所有学期"""
        try:
            profile_db.connect()
            sql = "SELECT DISTINCT semester FROM course_schedules WHERE user_id = %s ORDER BY semester DESC"
            profile_db.cursor.execute(sql, (user_id,))
            rows = profile_db.cursor.fetchall()
            semesters = [r['semester'] for r in rows]
            return {"success": True, "data": semesters}
        except Exception as e:
            error(f"获取学期列表失败: {e}")
            return {"success": False, "data": []}
        finally:
            profile_db.close()

    # ==================== 学习成绩 ====================

    def save_grades(self, user_id: int, semester: str, grades: List[Dict]) -> Dict:
        """批量保存成绩（先删后插）"""
        try:
            profile_db.connect()
            # 删除该学期旧数据
            profile_db.cursor.execute(
                "DELETE FROM student_grades WHERE user_id = %s AND semester = %s",
                (user_id, semester)
            )
            # 批量插入
            sql = """INSERT INTO student_grades (user_id, semester, course_name, score, credits, grade_type)
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            for g in grades:
                profile_db.cursor.execute(sql, (
                    user_id, semester, g['course_name'],
                    g.get('score'), g.get('credits'), g.get('grade_type', 'overall')
                ))
            profile_db.conn.commit()
            info(f"成绩保存成功: user={user_id}, semester={semester}, count={len(grades)}")
            return {"success": True, "message": f"保存 {len(grades)} 条成绩"}
        except Exception as e:
            error(f"成绩保存失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    def get_grades(self, user_id: int, semester: Optional[str] = None) -> Dict:
        """获取成绩列表"""
        try:
            profile_db.connect()
            if semester:
                sql = "SELECT * FROM student_grades WHERE user_id = %s AND semester = %s ORDER BY created_at DESC"
                profile_db.cursor.execute(sql, (user_id, semester))
            else:
                sql = "SELECT * FROM student_grades WHERE user_id = %s ORDER BY semester DESC, created_at DESC"
                profile_db.cursor.execute(sql, (user_id,))
            rows = profile_db.cursor.fetchall()
            # Decimal → float
            for r in rows:
                if r.get('score') is not None:
                    r['score'] = float(r['score'])
                if r.get('credits') is not None:
                    r['credits'] = float(r['credits'])
                if r.get('created_at'):
                    r['created_at'] = str(r['created_at'])
            return {"success": True, "data": rows}
        except Exception as e:
            error(f"获取成绩失败: {e}")
            return {"success": False, "data": []}
        finally:
            profile_db.close()

    # ==================== 错题记录 ====================

    def save_error_note(self, user_id: int, note: Dict) -> Dict:
        """添加一条错题"""
        try:
            profile_db.connect()
            sql = """INSERT INTO error_notes (user_id, subject, chapter, question, my_answer, correct_answer, error_reason, tags)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            tags_json = json.dumps(note.get('tags', []), ensure_ascii=False) if note.get('tags') else None
            profile_db.cursor.execute(sql, (
                user_id, note['subject'], note.get('chapter'),
                note['question'], note.get('my_answer'), note.get('correct_answer'),
                note.get('error_reason'), tags_json
            ))
            profile_db.conn.commit()
            note_id = profile_db.cursor.lastrowid
            return {"success": True, "data": {"id": note_id}, "message": "错题添加成功"}
        except Exception as e:
            error(f"错题添加失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    def get_error_notes(self, user_id: int, subject: Optional[str] = None, mastery: Optional[int] = None) -> Dict:
        """获取错题列表"""
        try:
            profile_db.connect()
            conditions = ["user_id = %s"]
            params: list = [user_id]
            if subject:
                conditions.append("subject = %s")
                params.append(subject)
            if mastery is not None:
                conditions.append("mastery = %s")
                params.append(mastery)
            sql = f"SELECT * FROM error_notes WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT 200"
            profile_db.cursor.execute(sql, params)
            rows = profile_db.cursor.fetchall()
            for r in rows:
                if r.get('tags') and isinstance(r['tags'], str):
                    r['tags'] = json.loads(r['tags'])
                if r.get('created_at'):
                    r['created_at'] = str(r['created_at'])
            return {"success": True, "data": rows}
        except Exception as e:
            error(f"获取错题失败: {e}")
            return {"success": False, "data": []}
        finally:
            profile_db.close()

    def update_error_note_mastery(self, user_id: int, note_id: int, mastery: int) -> Dict:
        """标记错题已掌握/未掌握"""
        try:
            profile_db.connect()
            sql = "UPDATE error_notes SET mastery = %s WHERE id = %s AND user_id = %s"
            profile_db.cursor.execute(sql, (mastery, note_id, user_id))
            profile_db.conn.commit()
            return {"success": True, "message": "已更新"}
        except Exception as e:
            error(f"更新错题掌握状态失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    def delete_error_note(self, user_id: int, note_id: int) -> Dict:
        """删除错题"""
        try:
            profile_db.connect()
            sql = "DELETE FROM error_notes WHERE id = %s AND user_id = %s"
            profile_db.cursor.execute(sql, (note_id, user_id))
            profile_db.conn.commit()
            return {"success": True, "message": "已删除"}
        except Exception as e:
            error(f"删除错题失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            profile_db.close()

    # ==================== 学习计划 ====================

    def generate_study_plan(self, user_id: int, data: Dict) -> Dict:
        """AI 生成学习计划"""
        try:
            semester = data.get('semester', '')
            plan_type = data.get('plan_type', 'weekly')  # weekly / exam / custom
            custom_goal = data.get('custom_goal', '')  # 用户自定义想学的内容
            user_requirements = data.get('user_requirements', '')  # 用户自由描述的需求
            exam_date = data.get('exam_date', '')  # 备考日期
            exam_subjects = data.get('exam_subjects', [])  # 备考科目

            # 收集上下文
            schedule = self.get_course_schedule(user_id, semester)
            grades = self.get_grades(user_id, semester)
            errors = self.get_error_notes(user_id)

            courses = schedule.get('data', {}).get('courses', []) if schedule.get('data') else []
            grade_list = grades.get('data', []) if grades.get('data') else []
            error_list = errors.get('data', []) if errors.get('data') else []

            # 统计薄弱学科（成绩低 + 错题多）
            weak_subjects = self._analyze_weak_subjects(grade_list, error_list)

            # 计算空闲时间（周一到周日，排除课程时间）
            free_slots = self._calculate_free_slots(courses)

            prompt = self._build_plan_prompt(
                plan_type=plan_type,
                courses=courses,
                grades=grade_list,
                errors=error_list[:20],  # 限制错题数量
                weak_subjects=weak_subjects,
                free_slots=free_slots,
                custom_goal=custom_goal,
                user_requirements=user_requirements,
                exam_date=exam_date,
                exam_subjects=exam_subjects,
                semester=semester,
            )

            result = qa_service.chat(prompt)
            plan_data = self._parse_plan_result(result)

            # 保存到数据库
            profile_db.connect()
            sql = """INSERT INTO study_plans (user_id, semester, plan_type, plan_data)
                     VALUES (%s, %s, %s, %s)"""
            profile_db.cursor.execute(sql, (
                user_id, semester, plan_type, json.dumps(plan_data, ensure_ascii=False)
            ))
            profile_db.conn.commit()
            plan_id = profile_db.cursor.lastrowid
            plan_data['id'] = plan_id
            profile_db.close()

            info(f"学习计划生成成功: user={user_id}, type={plan_type}")
            return {"success": True, "data": plan_data, "message": "学习计划生成成功"}

        except Exception as e:
            error(f"学习计划生成失败: {e}")
            # 降级：生成基础计划
            fallback = self._fallback_plan(data)
            return {"success": True, "data": fallback, "message": "已生成基础计划（AI 暂不可用）"}

    def get_study_plans(self, user_id: int, semester: Optional[str] = None, status: str = 'active') -> Dict:
        """获取学习计划列表"""
        try:
            profile_db.connect()
            conditions = ["user_id = %s", "status = %s"]
            params: list = [user_id, status]
            if semester:
                conditions.append("semester = %s")
                params.append(semester)
            sql = f"SELECT * FROM study_plans WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT 20"
            profile_db.cursor.execute(sql, params)
            rows = profile_db.cursor.fetchall()
            for r in rows:
                if r.get('plan_data') and isinstance(r['plan_data'], str):
                    r['plan_data'] = json.loads(r['plan_data'])
                if r.get('created_at'):
                    r['created_at'] = str(r['created_at'])
            return {"success": True, "data": rows}
        except Exception as e:
            error(f"获取学习计划失败: {e}")
            return {"success": False, "data": []}
        finally:
            profile_db.close()

    # ==================== 辅助方法 ====================

    def _analyze_weak_subjects(self, grades: List[Dict], errors: List[Dict]) -> List[Dict]:
        """分析薄弱学科"""
        subject_stats: Dict[str, Dict] = {}

        for g in grades:
            name = g.get('course_name', '')
            score = g.get('score', 100)
            if name not in subject_stats:
                subject_stats[name] = {'scores': [], 'error_count': 0}
            if score is not None:
                subject_stats[name]['scores'].append(float(score))

        for e in errors:
            subj = e.get('subject', '')
            if subj not in subject_stats:
                subject_stats[subj] = {'scores': [], 'error_count': 0}
            subject_stats[subj]['error_count'] += 1

        weak = []
        for name, stat in subject_stats.items():
            avg = sum(stat['scores']) / len(stat['scores']) if stat['scores'] else 100
            if avg < 80 or stat['error_count'] >= 3:
                weak.append({
                    'subject': name,
                    'avg_score': round(avg, 1),
                    'error_count': stat['error_count'],
                    'priority': 'high' if avg < 60 or stat['error_count'] >= 5 else 'medium'
                })

        weak.sort(key=lambda x: (0 if x['priority'] == 'high' else 1, x['avg_score']))
        return weak

    def _calculate_free_slots(self, courses: List[Dict]) -> Dict[str, List[str]]:
        """根据课程表计算每周空闲时段"""
        # 默认每天 8:00-22:00 为可学习时间
        all_hours = [f"{h:02d}:00" for h in range(8, 22)]
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        busy: Dict[str, set] = {d: set() for d in days}
        for c in courses:
            day = c.get('day', '')
            start = c.get('start_time', '')
            end = c.get('end_time', '')
            if day in busy and start and end:
                # 简单标记占用时段
                try:
                    sh = int(start.split(':')[0])
                    eh = int(end.split(':')[0])
                    for h in range(sh, eh + 1):
                        busy[day].add(f"{h:02d}:00")
                except (ValueError, IndexError):
                    pass

        free: Dict[str, List[str]] = {}
        for d in days:
            free[d] = [h for h in all_hours if h not in busy[d]]

        return free

    def _build_plan_prompt(self, **kwargs) -> str:
        """构建学习计划生成提示词"""
        plan_type = kwargs.get('plan_type', 'weekly')
        courses = kwargs.get('courses', [])
        weak_subjects = kwargs.get('weak_subjects', [])
        free_slots = kwargs.get('free_slots', {})
        custom_goal = kwargs.get('custom_goal', '')
        user_requirements = kwargs.get('user_requirements', '')
        exam_date = kwargs.get('exam_date', '')
        exam_subjects = kwargs.get('exam_subjects', [])
        semester = kwargs.get('semester', '')

        courses_text = '\n'.join([
            f"  - {c.get('name', '')} ({c.get('day', '')} {c.get('start_time', '')}-{c.get('end_time', '')})"
            for c in courses
        ]) if courses else '  (未录入课程表)'

        weak_text = '\n'.join([
            f"  - {w['subject']}: 平均分 {w['avg_score']}, 错题 {w['error_count']} 道 [{w['priority']}]"
            for w in weak_subjects
        ]) if weak_subjects else '  (暂无薄弱学科数据)'

        # 每天空闲时段摘要
        free_text = '\n'.join([
            f"  {day}: {', '.join(slots[:8])}{'...' if len(slots) > 8 else ''}"
            for day, slots in free_slots.items() if slots
        ]) if free_slots else '  (未录入课程表，全天可用)'

        type_desc = {
            'weekly': '周学习计划',
            'exam': f'备考计划（考试日期: {exam_date}，科目: {", ".join(exam_subjects)}）',
            'custom': f'自定义学习计划（目标: {custom_goal}）'
        }

        prompt = f"""你是一位专业的学习规划师。请根据以下信息为学生制定一份{type_desc.get(plan_type, '学习计划')}。

{f'## ⭐ 学生需求（最重要，请优先满足）:\n{user_requirements}' if user_requirements else ''}

## 学期: {semester}

## 当前课程安排:
{courses_text}

## 薄弱学科分析:
{weak_text}

## 每周空闲时段:
{free_text}

{f'## 自定义学习目标: {custom_goal}' if custom_goal else ''}
{f'## 考试日期: {exam_date}' if exam_date else ''}
{f'## 备考科目: {", ".join(exam_subjects)}' if exam_subjects else ''}

## 要求:
1. 优先围绕「学生需求」制定计划，需求中提到的时间、科目、目标必须覆盖
2. 根据空闲时段合理安排每日学习任务
3. 薄弱学科安排更多复习时间
4. 每天任务不超过 3 小时（课余时间）
5. 如有自定义目标，将其融入课余规划中
6. 如有考试，制定阶段性备考方案（基础巩固→强化练习→模拟冲刺）

请用以下 JSON 格式输出:
{{
  "title": "计划标题",
  "summary": "一句话总结",
  "total_days": 7,
  "daily_plans": [
    {{
      "day": "周一",
      "tasks": [
        {{"time": "19:00-20:00", "subject": "科目", "task": "具体任务", "type": "复习/预习/练习/备考"}},
        ...
      ]
    }}
  ],
  "focus_areas": ["重点关注领域1", "重点关注领域2"],
  "tips": ["建议1", "建议2"]
}}"""

        return prompt

    def _parse_plan_result(self, result: str) -> Dict:
        """解析 AI 返回的学习计划"""
        try:
            from core.json_utils import safe_parse_json
            parsed = safe_parse_json(result)
            if parsed and isinstance(parsed, dict) and 'daily_plans' in parsed:
                return parsed
        except Exception:
            pass

        # 降级：返回原始文本
        return {
            "title": "学习计划",
            "summary": result[:200] if result else "暂无",
            "total_days": 7,
            "daily_plans": [],
            "raw_text": result,
            "focus_areas": [],
            "tips": []
        }

    def _fallback_plan(self, data: Dict) -> Dict:
        """AI 不可用时的降级计划"""
        semester = data.get('semester', '')
        plan_type = data.get('plan_type', 'weekly')
        custom_goal = data.get('custom_goal', '')

        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        daily_plans = []
        for day in days:
            tasks = []
            if day in ['周六', '周日']:
                tasks = [
                    {"time": "09:00-10:30", "subject": "薄弱科目", "task": "复习重点知识点", "type": "复习"},
                    {"time": "14:00-15:30", "subject": "练习", "task": "做练习题巩固", "type": "练习"},
                ]
                if custom_goal:
                    tasks.append({"time": "16:00-17:00", "subject": "自主学习", "task": custom_goal, "type": "预习"})
            else:
                tasks = [
                    {"time": "19:00-20:00", "subject": "当日课程复习", "task": "整理笔记，回顾课堂内容", "type": "复习"},
                    {"time": "20:30-21:30", "subject": "作业/练习", "task": "完成作业并做拓展练习", "type": "练习"},
                ]
            daily_plans.append({"day": day, "tasks": tasks})

        title = "备考计划" if plan_type == 'exam' else ("自定义学习计划" if plan_type == 'custom' else "周学习计划")
        if custom_goal:
            title += f" — {custom_goal[:20]}"

        return {
            "title": title,
            "summary": f"{semester} {title}：工作日每晚 2 小时，周末每天 3 小时",
            "total_days": 7,
            "daily_plans": daily_plans,
            "focus_areas": ["薄弱科目重点突破", "当日课程及时复习"] + ([custom_goal] if custom_goal else []),
            "tips": ["每天保持规律作息", "先复习再做题", "错题及时整理", "每周末回顾本周学习情况"]
        }


student_data_service = StudentDataService()


# ==================== 文件导入扩展 ====================

class StudentDataImportMixin:
    """文件导入扩展 — AI 识别课程表/成绩/错题"""

    def _parse_upload_file(self, filename: str, content: bytes) -> str:
        """解析上传文件为文本"""
        from services.document_analysis_service import document_analysis_service
        return document_analysis_service._parse_file(filename, content)

    def import_courses_from_file(self, user_id: int, filename: str, content: bytes) -> Dict:
        """从文件中 AI 识别课程表"""
        try:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            is_image = ext in ('jpg', 'jpeg', 'png', 'bmp', 'webp')

            prompt = """请从以下内容中识别出课程表信息，提取每门课程的：
- 课程名称 (name)
- 星期几上课 (day: 周一~周日)
- 开始时间 (start_time: HH:MM 格式)
- 结束时间 (end_time: HH:MM 格式)
- 上课地点 (location，可为空)
- 授课教师 (teacher，可为空)

严格输出 JSON 数组格式（不要输出其他内容），例如:
[
  {"name": "高等数学", "day": "周一", "start_time": "08:00", "end_time": "09:40", "location": "教学楼A301", "teacher": "张教授"}
]

如果内容中没有课程表信息，返回空数组 []"""

            if is_image:
                image_b64 = base64.b64encode(content).decode('utf-8')
                from services.spark_client import spark_client
                response = spark_client.chat_with_image(prompt, image_b64)
            else:
                text = self._parse_upload_file(filename, content)
                if not text or text.startswith("["):
                    return {"success": False, "message": "文件解析失败，请上传 txt/pdf/docx/jpg/png 格式"}
                response = qa_service.call_ai(f"{prompt}\n\n文件内容:\n{text[:6000]}", max_tokens=3000)
            from core.json_utils import safe_parse_json
            courses = safe_parse_json(response)

            if not isinstance(courses, list):
                return {"success": False, "message": "AI 未能识别出课程表信息，请检查文件内容"}

            # 验证和清理数据
            valid_courses = []
            for c in courses:
                if isinstance(c, dict) and c.get('name') and c.get('day'):
                    valid_courses.append({
                        'name': str(c['name']),
                        'day': str(c.get('day', '')),
                        'start_time': str(c.get('start_time', '')),
                        'end_time': str(c.get('end_time', '')),
                        'location': str(c.get('location', '')),
                        'teacher': str(c.get('teacher', '')),
                    })

            info(f"AI 识别课程表: user={user_id}, 识别 {len(valid_courses)} 门课程")
            return {
                "success": True,
                "data": valid_courses,
                "message": f"成功识别 {len(valid_courses)} 门课程",
            }

        except Exception as e:
            error(f"文件导入课程表失败: {e}")
            return {"success": False, "message": f"导入失败: {str(e)}"}

    def import_grades_from_file(self, user_id: int, filename: str, content: bytes) -> Dict:
        """从文件中 AI 识别成绩"""
        try:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            is_image = ext in ('jpg', 'jpeg', 'png', 'bmp', 'webp')

            prompt = """请从以下内容中识别出成绩信息，提取每条成绩的：
- 课程名称 (course_name)
- 分数 (score: 数字，0-100)
- 学分 (credits: 数字，可选)
- 成绩类型 (grade_type: exam=期末/quiz=测验/homework=作业/overall=总评)
- 考试时间 (exam_date: YYYY-MM-DD 格式，可选，用于排序)

严格输出 JSON 数组格式（不要输出其他内容），例如:
[
  {"course_name": "高等数学", "score": 85, "credits": 4.0, "grade_type": "overall", "exam_date": "2026-01-15"}
]

如果内容中没有成绩信息，返回空数组 []"""

            if is_image:
                image_b64 = base64.b64encode(content).decode('utf-8')
                from services.spark_client import spark_client
                response = spark_client.chat_with_image(prompt, image_b64)
            else:
                text = self._parse_upload_file(filename, content)
                if not text or text.startswith("["):
                    return {"success": False, "message": "文件解析失败，请上传 txt/pdf/docx/jpg/png 格式"}
                response = qa_service.call_ai(f"{prompt}\n\n文件内容:\n{text[:6000]}", max_tokens=3000)
            from core.json_utils import safe_parse_json
            grades = safe_parse_json(response)

            if not isinstance(grades, list):
                return {"success": False, "message": "AI 未能识别出成绩信息，请检查文件内容"}

            valid_grades = []
            for g in grades:
                if isinstance(g, dict) and g.get('course_name') and g.get('score') is not None:
                    valid_grades.append({
                        'course_name': str(g['course_name']),
                        'score': float(g['score']),
                        'credits': float(g.get('credits', 0)) if g.get('credits') else None,
                        'grade_type': str(g.get('grade_type', 'overall')),
                        'exam_date': str(g.get('exam_date', '')) if g.get('exam_date') else None,
                    })

            info(f"AI 识别成绩: user={user_id}, 识别 {len(valid_grades)} 条成绩")
            return {
                "success": True,
                "data": valid_grades,
                "message": f"成功识别 {len(valid_grades)} 条成绩",
            }

        except Exception as e:
            error(f"文件导入成绩失败: {e}")
            return {"success": False, "message": f"导入失败: {str(e)}"}

    def import_errors_from_file(self, user_id: int, filename: str, content: bytes) -> Dict:
        """从文件中 AI 识别错题"""
        try:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            is_image = ext in ('jpg', 'jpeg', 'png', 'bmp', 'webp')

            prompt = """请从以下内容中识别出错题信息，提取每道错题的：
- 学科 (subject)
- 章节 (chapter，可选)
- 题目内容 (question)
- 我的答案 (my_answer，可选)
- 正确答案 (correct_answer，可选)
- 错误原因 (error_reason，可选)
- 标签 (tags: 字符串数组，可选)

严格输出 JSON 数组格式（不要输出其他内容），例如:
[
  {"subject": "高等数学", "chapter": "第三章 导数", "question": "求 f(x)=x³+2x 的导数", "my_answer": "3x²+2x", "correct_answer": "3x²+2", "error_reason": "对常数项求导错误", "tags": ["导数", "计算错误"]}
]

如果内容中没有错题信息，返回空数组 []"""

            if is_image:
                image_b64 = base64.b64encode(content).decode('utf-8')
                from services.spark_client import spark_client
                response = spark_client.chat_with_image(prompt, image_b64)
            else:
                text = self._parse_upload_file(filename, content)
                if not text or text.startswith("["):
                    return {"success": False, "message": "文件解析失败，请上传 txt/pdf/docx/jpg/png 格式"}
                response = qa_service.call_ai(f"{prompt}\n\n文件内容:\n{text[:6000]}", max_tokens=4000)
            from core.json_utils import safe_parse_json
            errors = safe_parse_json(response)

            if not isinstance(errors, list):
                return {"success": False, "message": "AI 未能识别出错题信息，请检查文件内容"}

            valid_errors = []
            for e in errors:
                if isinstance(e, dict) and e.get('subject') and e.get('question'):
                    valid_errors.append({
                        'subject': str(e['subject']),
                        'chapter': str(e.get('chapter', '')),
                        'question': str(e['question']),
                        'my_answer': str(e.get('my_answer', '')),
                        'correct_answer': str(e.get('correct_answer', '')),
                        'error_reason': str(e.get('error_reason', '')),
                        'tags': e.get('tags', []) if isinstance(e.get('tags'), list) else [],
                    })

            info(f"AI 识别错题: user={user_id}, 识别 {len(valid_errors)} 道错题")
            return {
                "success": True,
                "data": valid_errors,
                "message": f"成功识别 {len(valid_errors)} 道错题",
            }

        except Exception as e:
            error(f"文件导入错题失败: {e}")
            return {"success": False, "message": f"导入失败: {str(e)}"}


# 给 StudentDataService 添加导入能力
StudentDataService.import_courses_from_file = StudentDataImportMixin.import_courses_from_file
StudentDataService.import_grades_from_file = StudentDataImportMixin.import_grades_from_file
StudentDataService.import_errors_from_file = StudentDataImportMixin.import_errors_from_file
StudentDataService._parse_upload_file = StudentDataImportMixin._parse_upload_file
