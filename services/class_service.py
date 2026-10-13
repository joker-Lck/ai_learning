"""
班级管理与学情代查服务
Class management + student monitoring proxy (teacher-side)
"""

import secrets
import string

from core.logger import error, info

from data.config import (
    get_assessments_db_path,
    get_auth_db_path,
    get_paths_db_path,
    get_profile_db_path,
    get_resources_db_path,
)


def _conn(db_path: str):
    import sqlite3
    c = sqlite3.connect(db_path, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def _rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def _row(cur) -> dict | None:
    r = cur.fetchone()
    return dict(r) if r else None


# ── 邀请码生成 ──

def _generate_invite_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ==================== 班级管理 ====================

class ClassService:
    """班级 CRUD + 师生关联"""

    # ── 创建班级 ──
    def create_class(self, teacher_id: int, name: str, subject: str = "",
                     grade_level: str = "", semester: str = "",
                     description: str = "", max_students: int | None = None) -> dict:
        conn = _conn(get_auth_db_path())
        try:
            code = _generate_invite_code()
            # 确保邀请码唯一
            while conn.execute("SELECT 1 FROM classes WHERE invite_code=?", (code,)).fetchone():
                code = _generate_invite_code()

            cur = conn.execute(
                """INSERT INTO classes
                   (name, teacher_id, subject, grade_level, semester,
                    invite_code, max_students, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, teacher_id, subject, grade_level, semester,
                 code, max_students, description)
            )
            conn.commit()
            class_id = cur.lastrowid
            info(f"教师 {teacher_id} 创建班级 {name} (id={class_id})")
            return {"success": True, "class_id": class_id, "invite_code": code}
        except Exception as e:
            conn.rollback()
            error(f"创建班级失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    # ── 我的班级列表 ──
    def list_classes(self, teacher_id: int) -> list[dict]:
        conn = _conn(get_auth_db_path())
        try:
            cur = conn.execute("""
                SELECT c.*, COUNT(cs.id) AS student_count
                FROM classes c
                LEFT JOIN class_students cs ON cs.class_id = c.id AND cs.status = 'active'
                WHERE c.teacher_id = ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
            """, (teacher_id,))
            return _rows(cur)
        except Exception as e:
            error(f"查询班级列表失败: {e}")
            return []
        finally:
            conn.close()

    # ── 班级详情 ──
    def get_class(self, class_id: int, teacher_id: int | None = None) -> dict | None:
        conn = _conn(get_auth_db_path())
        try:
            sql = """
                SELECT c.*, COUNT(cs.id) AS student_count
                FROM classes c
                LEFT JOIN class_students cs ON cs.class_id = c.id AND cs.status = 'active'
                WHERE c.id = ?
            """
            params: list = [class_id]
            if teacher_id is not None:
                sql += " AND c.teacher_id = ?"
                params.append(teacher_id)
            sql += " GROUP BY c.id"
            return _row(conn.execute(sql, params))
        except Exception as e:
            error(f"查询班级详情失败: {e}")
            return None
        finally:
            conn.close()

    # ── 更新班级 ──
    def update_class(self, class_id: int, teacher_id: int, **fields) -> dict:
        allowed = {"name", "subject", "grade_level", "semester", "description", "max_students"}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if not updates:
            return {"success": False, "message": "无有效更新字段"}
        set_clause = ", ".join(f"{k}=?" for k in updates)
        conn = _conn(get_auth_db_path())
        try:
            cur = conn.execute(
                f"UPDATE classes SET {set_clause} WHERE id=? AND teacher_id=?",
                (*updates.values(), class_id, teacher_id)
            )
            conn.commit()
            return {"success": cur.rowcount > 0, "message": "更新成功" if cur.rowcount else "班级不存在"}
        except Exception as e:
            conn.rollback()
            error(f"更新班级失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    # ── 重置邀请码 ──
    def reset_invite_code(self, class_id: int, teacher_id: int) -> dict:
        conn = _conn(get_auth_db_path())
        try:
            code = _generate_invite_code()
            while conn.execute("SELECT 1 FROM classes WHERE invite_code=?", (code,)).fetchone():
                code = _generate_invite_code()
            cur = conn.execute(
                "UPDATE classes SET invite_code=? WHERE id=? AND teacher_id=?",
                (code, class_id, teacher_id)
            )
            conn.commit()
            return {"success": cur.rowcount > 0, "invite_code": code}
        except Exception as e:
            conn.rollback()
            error(f"重置邀请码失败: {e}")
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    # ── 关闭/开启入班 ──
    def set_class_open(self, class_id: int, teacher_id: int, is_open: bool) -> dict:
        conn = _conn(get_auth_db_path())
        try:
            cur = conn.execute(
                "UPDATE classes SET is_open=? WHERE id=? AND teacher_id=?",
                (1 if is_open else 0, class_id, teacher_id)
            )
            conn.commit()
            return {"success": cur.rowcount > 0}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    # ── 学生名单 ──
    def list_students(self, class_id: int) -> list[dict]:
        conn = _conn(get_auth_db_path())
        try:
            cur = conn.execute("""
                SELECT u.id, u.username, u.email, cs.joined_at, cs.status
                FROM class_students cs
                JOIN users u ON u.id = cs.student_id
                WHERE cs.class_id = ? AND cs.status = 'active'
                ORDER BY cs.joined_at
            """, (class_id,))
            return _rows(cur)
        except Exception as e:
            error(f"查询学生名单失败: {e}")
            return []
        finally:
            conn.close()

    # ── 移除学生 ──
    def remove_student(self, class_id: int, student_id: int, teacher_id: int) -> dict:
        conn = _conn(get_auth_db_path())
        try:
            # 验证班级归属
            cls = conn.execute(
                "SELECT 1 FROM classes WHERE id=? AND teacher_id=?", (class_id, teacher_id)
            ).fetchone()
            if not cls:
                return {"success": False, "message": "班级不存在或无权限"}
            cur = conn.execute(
                "UPDATE class_students SET status='removed' WHERE class_id=? AND student_id=?",
                (class_id, student_id)
            )
            conn.commit()
            return {"success": cur.rowcount > 0, "message": "已移除" if cur.rowcount else "学生不在班级"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            conn.close()

    # ── 班级概览 ──
    def get_overview(self, class_id: int) -> dict:
        conn = _conn(get_auth_db_path())
        try:
            cls = _row(conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)))
            if not cls:
                return {}
            student_count = conn.execute(
                "SELECT COUNT(*) c FROM class_students WHERE class_id=? AND status='active'",
                (class_id,)
            ).fetchone()["c"]
            return {
                "class": cls,
                "student_count": student_count,
            }
        except Exception as e:
            error(f"查询班级概览失败: {e}")
            return {}
        finally:
            conn.close()

    # ── 验证学生是否在老师任一班级内 ──
    def assert_student_in_teacher_class(self, teacher_id: int, student_id: int) -> bool:
        conn = _conn(get_auth_db_path())
        try:
            row = conn.execute("""
                SELECT 1 FROM class_students cs
                JOIN classes c ON c.id = cs.class_id
                WHERE c.teacher_id = ? AND cs.student_id = ? AND cs.status = 'active'
                LIMIT 1
            """, (teacher_id, student_id)).fetchone()
            return row is not None
        except Exception as e:
            error(f"验证师生关系失败: {e}")
            return False
        finally:
            conn.close()

    # ── 老师全部学生（跨班） ──
    def list_all_students(self, teacher_id: int) -> list[dict]:
        conn = _conn(get_auth_db_path())
        try:
            cur = conn.execute("""
                SELECT u.id, u.username, u.email,
                       cs.joined_at, cs.status,
                       c.id AS class_id, c.name AS class_name
                FROM class_students cs
                JOIN classes c ON c.id = cs.class_id
                JOIN users u ON u.id = cs.student_id
                WHERE c.teacher_id = ? AND cs.status = 'active'
                ORDER BY c.name, cs.joined_at
            """, (teacher_id,))
            return _rows(cur)
        except Exception as e:
            error(f"查询全部学生失败: {e}")
            return []
        finally:
            conn.close()


# ==================== 学情代查 ====================

class StudentMonitorService:
    """按 target_user_id 查询学生学情数据（跨 4 个分库）"""

    # ── 学生摘要 ──
    def get_student_brief(self, student_id: int) -> dict:
        result: dict = {"user_id": student_id}

        # 画像评分
        try:
            conn = _conn(get_profile_db_path())
            row = conn.execute("""
                SELECT knowledge_base, cognitive_style, learning_goals,
                       interest_areas, preferred_resources, learning_history,
                       weak_points, learning_breadth, learning_stage
                FROM profile_evaluations
                WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
            """, (student_id,)).fetchone()
            if row:
                result["profile_scores"] = dict(row)
            conn.close()
        except Exception:
            pass

        # 资源数
        try:
            conn = _conn(get_resources_db_path())
            row = conn.execute(
                "SELECT COUNT(*) c FROM learning_resources WHERE user_id=?",
                (student_id,)
            ).fetchone()
            result["resource_count"] = row["c"] if row else 0
            conn.close()
        except Exception:
            result["resource_count"] = 0

        # 测验均分
        try:
            conn = _conn(get_assessments_db_path())
            row = conn.execute("""
                SELECT COUNT(*) c, COALESCE(AVG(score),0) avg_score
                FROM quiz_sessions WHERE user_id=? AND status='completed'
            """, (student_id,)).fetchone()
            result["quiz_count"] = row["c"] if row else 0
            result["quiz_avg_score"] = round(row["avg_score"], 1) if row else 0

            # 学习时长
            row = conn.execute(
                "SELECT COALESCE(SUM(duration_seconds),0) s FROM learning_activities WHERE user_id=?",
                (student_id,)
            ).fetchone()
            result["study_seconds"] = row["s"] if row else 0
            conn.close()
        except Exception:
            result["quiz_count"] = 0
            result["quiz_avg_score"] = 0
            result["study_seconds"] = 0

        return result

    # ── 画像 ──
    def get_profile(self, student_id: int) -> dict:
        conn = _conn(get_profile_db_path())
        try:
            row = conn.execute(
                "SELECT * FROM student_profiles WHERE user_id=? ORDER BY updated_at DESC LIMIT 1",
                (student_id,)
            ).fetchone()
            if not row:
                return {}
            d = dict(row)
            import json
            for k in ("profile_data", "conversation_log"):
                if d.get(k) and isinstance(d[k], str):
                    try:
                        d[k] = json.loads(d[k])
                    except Exception:
                        pass
            return d
        except Exception as e:
            error(f"查询学生画像失败: {e}")
            return {}
        finally:
            conn.close()

    # ── 课程表 ──
    def get_course_schedule(self, student_id: int) -> list[dict]:
        conn = _conn(get_profile_db_path())
        try:
            cur = conn.execute(
                "SELECT * FROM course_schedules WHERE user_id=? ORDER BY semester DESC",
                (student_id,)
            )
            result = []
            import json
            for d in _rows(cur):
                if d.get("courses") and isinstance(d["courses"], str):
                    try:
                        d["courses"] = json.loads(d["courses"])
                    except Exception:
                        pass
                result.append(d)
            return result
        except Exception as e:
            error(f"查询课程表失败: {e}")
            return []
        finally:
            conn.close()

    # ── 资源列表 ──
    def get_resources(self, student_id: int, limit: int = 50) -> list[dict]:
        conn = _conn(get_resources_db_path())
        try:
            cur = conn.execute("""
                SELECT id, title, resource_type, subject, topic,
                       difficulty_level, created_at
                FROM learning_resources
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (student_id, limit))
            return _rows(cur)
        except Exception as e:
            error(f"查询学生资源失败: {e}")
            return []
        finally:
            conn.close()

    # ── 学习路径 ──
    def get_learning_paths(self, student_id: int) -> list[dict]:
        conn = _conn(get_paths_db_path())
        try:
            cur = conn.execute("""
                SELECT id, path_name, description, current_step,
                       status, total_steps, completed_steps,
                       estimated_hours, created_at
                FROM learning_paths
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 20
            """, (student_id,))
            return _rows(cur)
        except Exception as e:
            error(f"查询学习路径失败: {e}")
            return []
        finally:
            conn.close()

    # ── 做题数据 ──
    def get_quiz_data(self, student_id: int) -> dict:
        conn = _conn(get_assessments_db_path())
        try:
            # 最近测验记录
            cur = conn.execute("""
                SELECT id, subject, topic, total_questions, correct_count,
                       score, duration_seconds, mode, status, created_at
                FROM quiz_sessions
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT 20
            """, (student_id,))
            sessions = _rows(cur)

            # 做题统计
            row = conn.execute("""
                SELECT COUNT(*) c, COALESCE(AVG(score),0) avg_score
                FROM quiz_sessions WHERE user_id=? AND status='completed'
            """, (student_id,)).fetchone()
            stats = dict(row) if row else {}

            # 薄弱知识点
            cur = conn.execute("""
                SELECT knowledge_point, COUNT(*) total,
                       SUM(is_correct) correct,
                       ROUND(CAST(SUM(is_correct) AS REAL) / COUNT(*) * 100, 1) accuracy
                FROM quiz_answers
                WHERE user_id=? AND knowledge_point IS NOT NULL
                GROUP BY knowledge_point HAVING total >= 2
                ORDER BY accuracy ASC LIMIT 10
            """, (student_id,))
            weak_topics = _rows(cur)

            return {"sessions": sessions, "stats": stats, "weak_topics": weak_topics}
        except Exception as e:
            error(f"查询做题数据失败: {e}")
            return {"sessions": [], "stats": {}, "weak_topics": []}
        finally:
            conn.close()

    # ── 评估报告 ──
    def get_assessments(self, student_id: int, limit: int = 5) -> list[dict]:
        conn = _conn(get_assessments_db_path())
        try:
            cur = conn.execute("""
                SELECT id, assessment_type, overall_score,
                       improvement_suggestions, created_at
                FROM learning_assessments
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (student_id, limit))
            return _rows(cur)
        except Exception as e:
            error(f"查询评估报告失败: {e}")
            return []
        finally:
            conn.close()

    # ── 学情分析指标 ──
    def get_analytics(self, student_id: int, metric: str) -> dict | list:
        conn = _conn(get_assessments_db_path())
        try:
            if metric == "overview":
                row = conn.execute("""
                    SELECT COUNT(*) c, COALESCE(AVG(score),0) avg_score,
                           COALESCE(SUM(duration_seconds),0) total_seconds
                    FROM quiz_sessions WHERE user_id=? AND status='completed'
                """, (student_id,)).fetchone()
                return dict(row) if row else {}

            elif metric == "subject-breakdown":
                cur = conn.execute("""
                    SELECT subject, COUNT(*) c, COALESCE(AVG(score),0) avg_score
                    FROM quiz_sessions
                    WHERE user_id=? AND subject IS NOT NULL AND status='completed'
                    GROUP BY subject
                """, (student_id,))
                return _rows(cur)

            elif metric == "quiz-trend":
                cur = conn.execute("""
                    SELECT DATE(created_at) day, AVG(score) avg_score, COUNT(*) c
                    FROM quiz_sessions
                    WHERE user_id=? AND status='completed'
                    GROUP BY DATE(created_at)
                    ORDER BY day DESC LIMIT 30
                """, (student_id,))
                return _rows(cur)

            elif metric == "study-trend":
                cur = conn.execute("""
                    SELECT DATE(created_at) day,
                           SUM(duration_seconds) seconds, COUNT(*) c
                    FROM learning_activities
                    WHERE user_id=?
                    GROUP BY DATE(created_at)
                    ORDER BY day DESC LIMIT 30
                """, (student_id,))
                return _rows(cur)

            elif metric == "knowledge-mastery":
                cur = conn.execute("""
                    SELECT knowledge_point,
                           COUNT(*) total, SUM(is_correct) correct,
                           ROUND(CAST(SUM(is_correct) AS REAL) / COUNT(*) * 100, 1) accuracy
                    FROM quiz_answers
                    WHERE user_id=? AND knowledge_point IS NOT NULL
                    GROUP BY knowledge_point
                    ORDER BY accuracy DESC
                """, (student_id,))
                return _rows(cur)

            elif metric == "weekly-report":
                return self._weekly_report(student_id, conn)

            else:
                return {}
        except Exception as e:
            error(f"查询学情指标 {metric} 失败: {e}")
            return {}
        finally:
            conn.close()

    @staticmethod
    def _weekly_report(student_id: int, conn) -> dict:
        row = conn.execute("""
            SELECT COALESCE(SUM(duration_seconds),0) seconds
            FROM learning_activities
            WHERE user_id=? AND created_at >= DATE('now','weekday 0','-7 days')
        """, (student_id,)).fetchone()
        quiz = conn.execute("""
            SELECT COUNT(*) c, COALESCE(AVG(score),0) avg_score
            FROM quiz_sessions
            WHERE user_id=? AND status='completed'
                  AND created_at >= DATE('now','weekday 0','-7 days')
        """, (student_id,)).fetchone()
        return {
            "study_seconds": row["seconds"] if row else 0,
            "quiz_count": quiz["c"] if quiz else 0,
            "quiz_avg_score": round(quiz["avg_score"], 1) if quiz else 0,
        }

    # ── 活跃度 ──
    def get_activities(self, student_id: int, limit: int = 30) -> list[dict]:
        conn = _conn(get_assessments_db_path())
        try:
            cur = conn.execute("""
                SELECT activity_type, metadata, duration_seconds, created_at
                FROM learning_activities
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (student_id, limit))
            return _rows(cur)
        except Exception as e:
            error(f"查询活跃度失败: {e}")
            return []
        finally:
            conn.close()

    # ── 错题本 ──
    def get_error_notes(self, student_id: int, limit: int = 50) -> list[dict]:
        conn = _conn(get_profile_db_path())
        try:
            cur = conn.execute("""
                SELECT id, subject, chapter, question, my_answer,
                       correct_answer, error_reason, tags, mastery,
                       review_count, created_at
                FROM error_notes
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (student_id, limit))
            return _rows(cur)
        except Exception as e:
            error(f"查询错题本失败: {e}")
            return []
        finally:
            conn.close()

    # ── 成绩 ──
    def get_grades(self, student_id: int) -> list[dict]:
        conn = _conn(get_profile_db_path())
        try:
            cur = conn.execute("""
                SELECT semester, course_name, score, credits, grade_type, created_at
                FROM student_grades
                WHERE user_id = ?
                ORDER BY semester DESC, created_at DESC
            """, (student_id,))
            return _rows(cur)
        except Exception as e:
            error(f"查询成绩失败: {e}")
            return []
        finally:
            conn.close()


# 全局实例
class_service = ClassService()
student_monitor_service = StudentMonitorService()
