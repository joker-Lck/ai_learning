"""
学生数据服务 — 课程表 / 成绩 / 错题 / 学习计划 CRUD + AI 学习规划生成
"""

import json
import base64
import io
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from core.logger import info, error, warning
from data.db_operations import profile_db
from services.qa_service import qa_service


def _compress_image(content: bytes, max_size: int = 4096, quality: int = 90) -> str:
    """压缩图片并返回 base64 — 降低 API 传输量但保持可读性"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        orig_size = len(content)
        # 缩放：最长边不超过 max_size
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        # 转 RGB（PNG 透明通道需转换）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        result = buf.getvalue()
        info(f"图片压缩: {orig_size//1024}KB -> {len(result)//1024}KB, 尺寸: {w}x{h} -> {img.size[0]}x{img.size[1]}")
        return base64.b64encode(result).decode('utf-8')
    except Exception as e:
        error(f"图片压缩失败，使用原图: {e}")
        return base64.b64encode(content).decode('utf-8')


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

            result = qa_service.call_ai(prompt)
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
        import re as _re
        try:
            from core.json_utils import safe_parse_json
            parsed = safe_parse_json(result)
            if parsed and isinstance(parsed, dict) and 'daily_plans' in parsed:
                return parsed
        except Exception:
            pass

        # 清理代码块标记
        cleaned = result.strip()
        code_match = _re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', cleaned, _re.DOTALL)
        if code_match:
            cleaned = code_match.group(1).strip()
            # 再次尝试解析清理后的 JSON
            try:
                from core.json_utils import safe_parse_json
                parsed = safe_parse_json(cleaned)
                if parsed and isinstance(parsed, dict) and 'daily_plans' in parsed:
                    return parsed
            except Exception:
                pass

        # 降级：返回原始文本（已清理代码块标记）
        return {
            "title": "学习计划",
            "summary": cleaned[:200] if cleaned else "暂无",
            "total_days": 7,
            "daily_plans": [],
            "raw_text": cleaned,
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

    def _pdf_to_image(self, content: bytes) -> Optional[str]:
        """将 PDF 第一页转为 base64 图片（用于扫描版 PDF 的 OCR）"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            if doc.page_count == 0:
                return None
            # 只取第一页
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 放大提高识别率
            img_bytes = pix.tobytes("jpeg")
            doc.close()
            return base64.b64encode(img_bytes).decode('utf-8')
        except ImportError:
            warning("PyMuPDF 未安装，无法处理扫描版 PDF。请运行: pip install PyMuPDF")
            return None
        except Exception as e:
            error(f"PDF 转图片失败: {e}")
            return None

    def import_courses_from_file(self, user_id: int, filename: str, content: bytes) -> Dict:
        """从文件中 AI 识别课程表"""
        try:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            is_image = ext in ('jpg', 'jpeg', 'png', 'bmp', 'webp')

            if is_image:
                prompt = """你是一个课程表识别专家。请仔细分析这张课程表图片，逐行逐列读取每个单元格。

识别规则：
1. 先确定表头：第1行是星期（周一~周日），第1列是节次/时间
2. 遍历每个单元格，提取课程信息
3. 节次→时间映射（按图片实际时间，如无则用默认）：
   - 第1-2节 → 08:00-09:40
   - 第3-4节 → 10:00-11:40
   - 第5-6节 → 14:00-15:40
   - 第7-8节 → 16:00-17:40
   - 第9-10节 → 19:00-20:40
4. 如果图片中有具体时间，以图片时间为准
5. 空白单元格跳过，不要输出

输出格式（严格JSON数组）：
[
  {"name":"高等数学","day":"周一","start_time":"08:00","end_time":"09:40","location":"教A301","teacher":"张三"},
  {"name":"英语","day":"周三","start_time":"14:00","end_time":"15:40","location":"","teacher":""}
]

只输出JSON数组，不要任何其他文字。"""
                system_prompt = "你是一个精确的课程表识别系统。只输出JSON数组，不要解释。"
            else:
                prompt = """你是一个课程表识别专家。请分析以下文本内容。

判断规则（宽松判断）：
- 如果包含「星期」「节次」「上课时间」「课程」等关键词，或包含类似表格结构（星期一~星期日 + 节次/时间），则判定为课程表
- 如果包含「周」「节」「教室」「老师」等与课程相关的词，也判定为课程表
- 只有明确是成绩单、错题本、实验报告、论文、简历等完全无关内容时，才输出：NOT_SCHEDULE

如果是课程表，请提取课程信息，输出严格JSON数组：
[
  {"name":"高等数学","day":"周一","start_time":"08:00","end_time":"09:40","location":"教A301","teacher":"张三"}
]

注意：
1. 如果文本编码有问题（乱码），尝试从乱码中提取课程信息
2. 如果只看到部分信息（如 "(1-2节)1-16Th"），尽量推断并提取
3. 节次→时间：第1-2节=08:00-09:40，第3-4节=10:00-11:40，第5-6节=14:00-15:40，第7-8节=16:00-17:40，第9-10节=19:00-20:40
4. 星期映射：Mon=周一，Tue=周二，Wed=周三，Thu=周四，Fri=周五，Sat=周六，Sun=周日

只输出JSON数组或NOT_SCHEDULE，不要其他文字。"""
                system_prompt = None

            from services.spark_client import spark_client
            
            if is_image:
                # 使用 OCR 提取文字，再用 AI 解析
                image_b64 = _compress_image(content)
                
                # 1. 先用 OCR 提取文字
                ocr_text = spark_client.ocr_image(image_b64)
                
                if ocr_text and len(ocr_text) > 10:
                    # 2. 用 AI 解析 OCR 提取的文字
                    info(f"OCR 提取文字成功: {len(ocr_text)} 字符")
                    response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                else:
                    # OCR 失败，降级到图片理解
                    info("OCR 提取失败，降级到图片理解")
                    response = spark_client.chat_with_image(
                        prompt, image_b64, max_tokens=4000,
                        system_prompt=system_prompt,
                    )
                    
                    # 检查图片理解是否成功
                    if not response or not response.strip():
                        warning("图片理解返回空结果，可能是 API 凭证或配额问题")
                        return {
                            "success": False,
                            "message": "图片识别失败：AI 图片理解服务暂时不可用。请尝试以下方案：\n1. 将课程表截图后重新上传\n2. 使用「手动添加」按钮逐条录入课程\n3. 联系管理员检查 API 配额"
                        }
            else:
                text = self._parse_upload_file(filename, content)
                # 检查解析结果
                if text and text.startswith("[") and "需要安装" in text:
                    # 依赖缺失，返回明确的安装提示
                    return {"success": False, "message": text}
                if not text or text.startswith("["):
                    # 解析失败，尝试作为图片处理（可能是扫描版 PDF）
                    if ext == 'pdf':
                        info("PDF 文本提取失败，尝试 OCR 识别扫描版 PDF")
                        # 将 PDF 转为图片再 OCR
                        image_b64 = self._pdf_to_image(content)
                        if image_b64:
                            ocr_text = spark_client.ocr_image(image_b64)
                            if ocr_text and len(ocr_text) > 10:
                                info(f"扫描版 PDF OCR 成功: {len(ocr_text)} 字符")
                                response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                            else:
                                # OCR 也失败，使用图片理解
                                response = spark_client.chat_with_image(
                                    prompt, image_b64, max_tokens=4000,
                                    system_prompt=system_prompt,
                                )
                                
                                # 检查图片理解是否成功
                                if not response or not response.strip():
                                    warning("PDF 图片理解返回空结果，可能是 API 凭证或配额问题")
                                    return {
                                        "success": False,
                                        "message": "PDF 识别失败：AI 图片理解服务暂时不可用。请尝试以下方案：\n1. 将课表截图后以图片形式上传\n2. 使用「手动添加」按钮逐条录入课程\n3. 联系管理员检查 API 配额"
                                    }
                        else:
                            return {"success": False, "message": "PDF 解析失败，请确保文件未损坏，或尝试将课表截图后上传"}
                    else:
                        return {"success": False, "message": "文件解析失败，请上传 txt/pdf/doc/docx/ppt/pptx/xls/xlsx/csv/jpg/png 等格式"}
                else:
                    response = spark_client.simple(f"{prompt}\n\n文件内容:\n{text[:8000]}", max_tokens=4000)

            info(f"AI 识别课程表原始响应 (前300字): {response[:300]}")
            
            # 检查是否为非课程表内容
            if 'NOT_SCHEDULE' in response or 'not_schedule' in response.lower():
                return {"success": False, "message": "该文件不是课程表，请上传包含课程时间安排的文件（如课表截图、选课结果、教学日历等）"}
            
            from core.json_utils import safe_parse_json
            courses = safe_parse_json(response)
            info(f"AI 识别课程表解析结果: {courses}")

            if not isinstance(courses, list):
                # 尝试从文本中提取数组
                import re
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    import json
                    try:
                        courses = json.loads(match.group(0))
                    except Exception:
                        pass
            if not isinstance(courses, list):
                return {"success": False, "message": "AI 未能识别出课程表，可能是文件内容编码问题。请使用「手动添加」按钮逐条录入课程。"}

            # 验证和清理数据
            valid_courses = []
            seen = set()
            for c in courses:
                if not isinstance(c, dict):
                    continue
                name = str(c.get('name', '')).strip()
                day = str(c.get('day', '')).strip()
                if not name or not day:
                    continue
                # 标准化星期
                day = day.replace('星期', '周').replace('礼拜', '周')
                if day not in ('周一','周二','周三','周四','周五','周六','周日'):
                    continue
                start_time = str(c.get('start_time', '')).strip()
                end_time = str(c.get('end_time', '')).strip()
                # 去重
                key = f"{name}_{day}_{start_time}"
                if key in seen:
                    continue
                seen.add(key)
                valid_courses.append({
                    'name': name,
                    'day': day,
                    'start_time': start_time,
                    'end_time': end_time,
                    'location': str(c.get('location', '')).strip(),
                    'teacher': str(c.get('teacher', '')).strip(),
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

            prompt = """你是一个成绩识别专家。请先判断以下内容是否为成绩单/成绩查询/分数记录。

判断规则：
- 如果包含「成绩」「分数」「学分」「绩点」「GPA」等关键词，或包含课程名+分数的结构，则判定为成绩单
- 如果是课程表、错题本、简历、论文等非成绩内容，直接输出：NOT_GRADES

如果是成绩单，请提取每条成绩：
- course_name: 课程名称
- score: 分数（0-100数字）
- credits: 学分（可选）
- grade_type: 成绩类型（exam=期末/quiz=测验/homework=作业/overall=总评）
- exam_date: 考试时间（YYYY-MM-DD，可选）

严格输出JSON数组，不要输出其他内容。
示例: [{"course_name":"高等数学","score":85,"credits":4.0,"grade_type":"overall"}]
如果没有成绩信息，返回空数组 []"""

            if is_image:
                # 使用 OCR 提取文字，再用 AI 解析
                image_b64 = _compress_image(content)
                from services.spark_client import spark_client
                
                # 1. 先用 OCR 提取文字
                ocr_text = spark_client.ocr_image(image_b64)
                
                if ocr_text and len(ocr_text) > 10:
                    # 2. 用 AI 解析 OCR 提取的文字
                    info(f"OCR 提取文字成功: {len(ocr_text)} 字符")
                    response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                else:
                    # OCR 失败，降级到图片理解
                    info("OCR 提取失败，降级到图片理解")
                    response = spark_client.chat_with_image(prompt, image_b64)
            else:
                text = self._parse_upload_file(filename, content)
                # 检查解析结果
                if text and text.startswith("[") and "需要安装" in text:
                    return {"success": False, "message": text}
                if not text or text.startswith("["):
                    # 解析失败，尝试作为图片处理（可能是扫描版 PDF）
                    if ext == 'pdf':
                        info("PDF 文本提取失败，尝试 OCR 识别扫描版 PDF")
                        from services.spark_client import spark_client
                        image_b64 = self._pdf_to_image(content)
                        if image_b64:
                            ocr_text = spark_client.ocr_image(image_b64)
                            if ocr_text and len(ocr_text) > 10:
                                info(f"扫描版 PDF OCR 成功: {len(ocr_text)} 字符")
                                response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                            else:
                                response = spark_client.chat_with_image(prompt, image_b64)
                        else:
                            return {"success": False, "message": "PDF 解析失败，请确保文件未损坏，或尝试将成绩单截图后上传"}
                    else:
                        return {"success": False, "message": "文件解析失败，请上传 txt/pdf/doc/docx/ppt/pptx/xls/xlsx/csv/jpg/png 等格式"}
                else:
                    from services.spark_client import spark_client
                    response = spark_client.simple(f"{prompt}\n\n文件内容:\n{text[:8000]}", max_tokens=4000)
            
            info(f"AI 识别成绩原始响应 (前300字): {response[:300]}")
            
            # 检查是否为非成绩内容
            if 'NOT_GRADES' in response or 'not_grades' in response.lower():
                return {"success": False, "message": "该文件不是成绩单，请上传包含课程成绩的文件（如成绩单截图、成绩查询页面等）"}
            
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

            prompt = """你是一个错题识别专家。请先判断以下内容是否为错题本/试卷订正/易错题记录。

判断规则：
- 如果包含「错题」「订正」「错误答案」「正确答案」「易错」等关键词，或包含题目+批改痕迹的结构，则判定为错题
- 如果是课程表、成绩单、简历、论文等非错题内容，直接输出：NOT_ERRORS

如果是错题，请提取所有错题信息：
- subject: 学科名称（必填）
- chapter: 章节/知识点（可选）
- question: 题目内容，尽量完整（必填）
- my_answer: 错误答案/学生答案（可选）
- correct_answer: 正确答案（可选）
- error_reason: 错误原因分析（可选）
- tags: 相关标签数组（可选）

注意：只提取做错的题目，做对的不要。

严格输出JSON数组，不要输出其他内容。
示例: [{"subject":"高等数学","chapter":"导数","question":"求f(x)=x²的导数","my_answer":"2x","correct_answer":"2x","error_reason":"计算错误","tags":["导数"]}]
如果没有错题信息，返回空数组 []"""

            if is_image:
                # 使用 OCR 提取文字，再用 AI 解析
                image_b64 = _compress_image(content)
                from services.spark_client import spark_client
                
                # 1. 先用 OCR 提取文字
                ocr_text = spark_client.ocr_image(image_b64)
                
                if ocr_text and len(ocr_text) > 10:
                    # 2. 用 AI 解析 OCR 提取的文字
                    info(f"OCR 提取文字成功: {len(ocr_text)} 字符")
                    response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                else:
                    # OCR 失败，降级到图片理解
                    info("OCR 提取失败，降级到图片理解")
                    response = spark_client.chat_with_image(prompt, image_b64, max_tokens=4000)
            else:
                text = self._parse_upload_file(filename, content)
                # 检查解析结果
                if text and text.startswith("[") and "需要安装" in text:
                    return {"success": False, "message": text}
                if not text or text.startswith("["):
                    # 解析失败，尝试作为图片处理（可能是扫描版 PDF）
                    if ext == 'pdf':
                        info("PDF 文本提取失败，尝试 OCR 识别扫描版 PDF")
                        from services.spark_client import spark_client
                        image_b64 = self._pdf_to_image(content)
                        if image_b64:
                            ocr_text = spark_client.ocr_image(image_b64)
                            if ocr_text and len(ocr_text) > 10:
                                info(f"扫描版 PDF OCR 成功: {len(ocr_text)} 字符")
                                response = spark_client.simple(f"{prompt}\n\nOCR提取内容:\n{ocr_text[:8000]}", max_tokens=4000)
                            else:
                                response = spark_client.chat_with_image(prompt, image_b64, max_tokens=4000)
                        else:
                            return {"success": False, "message": "PDF 解析失败，请确保文件未损坏，或尝试将错题截图后上传"}
                    else:
                        return {"success": False, "message": "文件解析失败，请上传 txt/pdf/doc/docx/ppt/pptx/xls/xlsx/csv/jpg/png 等格式"}
                else:
                    from services.spark_client import spark_client
                    response = spark_client.simple(f"{prompt}\n\n文件内容:\n{text[:8000]}", max_tokens=4000)
            
            info(f"AI 识别错题原始响应 (前300字): {response[:300]}")
            
            # 检查是否为非错题内容
            if 'NOT_ERRORS' in response or 'not_errors' in response.lower():
                return {"success": False, "message": "该文件不是错题本，请上传包含错题/订正内容的文件（如试卷订正、错题本截图等）"}
            
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
