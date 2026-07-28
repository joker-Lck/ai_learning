"""
数据访问对象 (DAO) 层
封装所有数据库 CRUD 操作，消除路由层的重复数据库代码
"""

import json
from typing import Any

from core.logger import error


class ResourceDAO:
    """学习资源数据访问"""

    def __init__(self, db):
        self._db = db

    def save(self, user_id: int, title: str, resource_type: str,
             subject: str, topic: str, difficulty: str,
             content_data: Any, duration_minutes: int | None = None,
             generated_by: str | None = None) -> int | None:
        """保存学习资源，返回资源 ID"""
        try:
            with self._db:
                self._db.cursor.execute("""
                    INSERT INTO learning_resources
                    (user_id, title, resource_type, subject, topic,
                     difficulty_level, content_data, generated_by_agent, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, title, resource_type, subject, topic,
                    difficulty,
                    json.dumps(content_data, ensure_ascii=False) if not isinstance(content_data, str) else content_data,
                    generated_by or f"user_{user_id}",
                    duration_minutes,
                ))
                self._db.conn.commit()
                return self._db.cursor.lastrowid
        except Exception as e:
            error(f"保存资源失败: {e}")
            return None

    def get_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
        """获取用户的资源列表"""
        try:
            with self._db:
                self._db.cursor.execute("""
                    SELECT id, title, resource_type, subject, topic,
                           difficulty_level, content_data, created_at
                    FROM learning_resources
                    WHERE user_id = ? OR (user_id IS NULL AND generated_by_agent = ?)
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                """, (user_id, f"user_{user_id}", limit, offset))
                rows = [dict(row) for row in self._db.cursor.fetchall()]
                for row in rows:
                    if row.get("content_data") and isinstance(row["content_data"], str):
                        try:
                            row["content_data"] = json.loads(row["content_data"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if row.get("created_at"):
                        row["created_at"] = str(row["created_at"])
                return rows
        except Exception as e:
            error(f"获取用户资源失败: {e}")
            return []

    def count_by_user(self, user_id: int) -> int:
        """统计用户资源数量"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(*) as cnt FROM learning_resources WHERE user_id = ? OR (user_id IS NULL AND generated_by_agent = ?)",
                    (user_id, f"user_{user_id}")
                )
                row = self._db.cursor.fetchone()
                return dict(row)["cnt"] if row else 0
        except Exception as e:
            error(f"统计资源数量失败: {e}")
            return 0

    def delete(self, resource_id: int, user_id: int) -> bool:
        """删除资源（仅限拥有者）"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "DELETE FROM learning_resources WHERE id = ? AND user_id = ?",
                    (resource_id, user_id)
                )
                self._db.conn.commit()
                return self._db.cursor.rowcount > 0
        except Exception as e:
            error(f"删除资源失败: {e}")
            return False


class ActivityDAO:
    """学习活动日志数据访问"""

    def __init__(self, db):
        self._db = db

    def record(self, user_id: int, activity_type: str,
               metadata: dict | None = None, duration_seconds: int = 0) -> int | None:
        """记录一条活动日志"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "INSERT INTO learning_activities (user_id, activity_type, metadata, duration_seconds) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, activity_type,
                     json.dumps(metadata, ensure_ascii=False) if metadata else None,
                     duration_seconds)
                )
                self._db.conn.commit()
                return self._db.cursor.lastrowid
        except Exception as e:
            error(f"记录活动日志失败: {e}")
            return None

    def get_recent(self, user_id: int, limit: int = 10) -> list[dict]:
        """获取最近活动日志"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT id, activity_type, metadata, created_at "
                    "FROM learning_activities WHERE user_id = ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
                rows = [dict(row) for row in self._db.cursor.fetchall()]
                for row in rows:
                    if row.get("metadata") and isinstance(row["metadata"], str):
                        try:
                            row["metadata"] = json.loads(row["metadata"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if row.get("created_at"):
                        row["created_at"] = str(row["created_at"])
                return rows
        except Exception as e:
            error(f"获取活动日志失败: {e}")
            return []

    def count_by_user(self, user_id: int) -> int:
        """统计用户活动数"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(*) as cnt FROM learning_activities WHERE user_id = ?",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["cnt"] if row else 0
        except Exception:
            return 0

    def get_login_days(self, user_id: int) -> int:
        """获取用户登录天数"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(DISTINCT DATE(created_at)) as days "
                    "FROM learning_activities WHERE user_id = ? "
                    "AND activity_type IN ('login', 'resource_generate', 'tutor_query', 'assessment')",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["days"] if row else 0
        except Exception:
            return 0

    def get_total_study_seconds(self, user_id: int) -> int:
        """获取总学习时长"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COALESCE(SUM(duration_seconds), 0) as total "
                    "FROM learning_activities WHERE user_id = ? AND activity_type = 'session'",
                    (user_id,)
                )
                row = self._db.cursor.fetchone()
                return dict(row)["total"] if row else 0
        except Exception:
            return 0


# 全局 DAO 实例（延迟初始化）
_resource_dao: ResourceDAO | None = None
_activity_dao: ActivityDAO | None = None


def get_resource_dao() -> ResourceDAO:
    global _resource_dao
    if _resource_dao is None:
        from data.db_operations import resource_db
        _resource_dao = ResourceDAO(resource_db)
    return _resource_dao


def get_activity_dao() -> ActivityDAO:
    global _activity_dao
    if _activity_dao is None:
        from data.db_operations import assessment_db
        _activity_dao = ActivityDAO(assessment_db)
    return _activity_dao


class QuizDAO:
    """在线做题数据访问"""

    def __init__(self, db):
        self._db = db

    def create_session(self, user_id: int, subject: str | None, topic: str | None,
                       total_questions: int, resource_id: int | None = None,
                       mode: str = "practice") -> int | None:
        """创建答题会话"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "INSERT INTO quiz_sessions (user_id, resource_id, subject, topic, total_questions, mode) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, resource_id, subject, topic, total_questions, mode)
                )
                self._db.conn.commit()
                return self._db.cursor.lastrowid
        except Exception as e:
            error(f"创建答题会话失败: {e}")
            return None

    def submit_answer(self, session_id: int, user_id: int, question_index: int,
                      question_type: str, question_text: str, options: list | None,
                      correct_answer: str, user_answer: str, explanation: str | None,
                      knowledge_point: str | None, difficulty: str | None,
                      time_spent: int = 0) -> dict:
        """提交单题答案，返回判题结果"""
        is_correct = 0
        ua = (user_answer or "").strip()
        ca = correct_answer.strip()
        if question_type == "multiple_choice":
            is_correct = 1 if ua.upper() == ca.upper() else 0
        elif question_type == "judge":
            is_correct = 1 if ua in ("true", "对", "正确", "T", "√") and ca in ("true", "对", "正确", "T", "√") or \
                              ua in ("false", "错", "错误", "F", "×") and ca in ("false", "错", "错误", "F", "×") else 0
        else:
            is_correct = 1 if ua == ca else 0

        try:
            with self._db:
                self._db.cursor.execute(
                    "INSERT INTO quiz_answers "
                    "(session_id, user_id, question_index, question_type, question_text, "
                    "options, correct_answer, user_answer, is_correct, explanation, "
                    "knowledge_point, difficulty, time_spent_seconds) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (session_id, user_id, question_index, question_type, question_text,
                     json.dumps(options, ensure_ascii=False) if options else None,
                     correct_answer, user_answer, is_correct, explanation,
                     knowledge_point, difficulty, time_spent)
                )
                self._db.conn.commit()
                return {"is_correct": bool(is_correct), "correct_answer": correct_answer,
                        "explanation": explanation}
        except Exception as e:
            error(f"提交答案失败: {e}")
            return {"is_correct": False, "correct_answer": correct_answer, "explanation": explanation}

    def finish_session(self, session_id: int, user_id: int) -> dict:
        """结束答题会话，计算得分"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT COUNT(*) as total, SUM(is_correct) as correct "
                    "FROM quiz_answers WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id)
                )
                row = dict(self._db.cursor.fetchone())
                total = row["total"] or 0
                correct = row["correct"] or 0
                score = round(correct / total * 100, 1) if total > 0 else 0

                self._db.cursor.execute(
                    "UPDATE quiz_sessions SET status='completed', correct_count=?, score=?, "
                    "completed_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                    (correct, score, session_id, user_id)
                )
                self._db.conn.commit()

                # 获取会话详情用于返回
                self._db.cursor.execute(
                    "SELECT * FROM quiz_sessions WHERE id=?", (session_id,)
                )
                session = dict(self._db.cursor.fetchone())
                session["score"] = score
                session["correct_count"] = correct
                return session
        except Exception as e:
            error(f"结束答题会话失败: {e}")
            return {}

    def get_history(self, user_id: int, limit: int = 20, offset: int = 0) -> list[dict]:
        """获取答题历史"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT id, subject, topic, total_questions, correct_count, score, "
                    "duration_seconds, mode, status, created_at, completed_at "
                    "FROM quiz_sessions WHERE user_id = ? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (user_id, limit, offset)
                )
                rows = [dict(row) for row in self._db.cursor.fetchall()]
                for row in rows:
                    for k in ("created_at", "completed_at"):
                        if row.get(k):
                            row[k] = str(row[k])
                return rows
        except Exception as e:
            error(f"获取答题历史失败: {e}")
            return []

    def get_session_detail(self, session_id: int, user_id: int) -> dict:
        """获取单次答题详情"""
        try:
            with self._db:
                self._db.cursor.execute(
                    "SELECT * FROM quiz_sessions WHERE id = ? AND user_id = ?",
                    (session_id, user_id)
                )
                session_row = self._db.cursor.fetchone()
                if not session_row:
                    return {}
                session = dict(session_row)
                for k in ("created_at", "completed_at"):
                    if session.get(k):
                        session[k] = str(session[k])

                self._db.cursor.execute(
                    "SELECT * FROM quiz_answers WHERE session_id = ? ORDER BY question_index",
                    (session_id,)
                )
                answers = []
                for row in self._db.cursor.fetchall():
                    a = dict(row)
                    if a.get("options") and isinstance(a["options"], str):
                        try:
                            a["options"] = json.loads(a["options"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    a["is_correct"] = bool(a.get("is_correct", 0))
                    if a.get("created_at"):
                        a["created_at"] = str(a["created_at"])
                    answers.append(a)
                session["answers"] = answers
                return session
        except Exception as e:
            error(f"获取答题详情失败: {e}")
            return {}

    def get_stats(self, user_id: int, subject: str | None = None) -> dict:
        """获取答题统计"""
        try:
            with self._db:
                where = "WHERE s.user_id = ? AND s.status = 'completed'"
                params: list = [user_id]
                if subject:
                    where += " AND s.subject = ?"
                    params.append(subject)

                self._db.cursor.execute(f"""
                    SELECT COUNT(*) as total_sessions,
                           COALESCE(SUM(s.total_questions), 0) as total_questions,
                           COALESCE(SUM(s.correct_count), 0) as total_correct,
                           COALESCE(AVG(s.score), 0) as avg_score
                    FROM quiz_sessions s {where}
                """, params)
                stats = dict(self._db.cursor.fetchone())
                stats["avg_score"] = round(stats["avg_score"], 1)

                # 按学科统计
                self._db.cursor.execute(f"""
                    SELECT s.subject, COUNT(*) as sessions, AVG(s.score) as avg_score,
                           SUM(s.total_questions) as questions, SUM(s.correct_count) as correct
                    FROM quiz_sessions s {where} GROUP BY s.subject
                """, params)
                stats["by_subject"] = [
                    {**dict(r), "avg_score": round(r["avg_score"], 1)}
                    for r in self._db.cursor.fetchall()
                ]

                # 按难度统计（从 quiz_answers 表）
                user_where = "WHERE a.user_id = ?"
                user_params: list = [user_id]
                self._db.cursor.execute(f"""
                    SELECT a.difficulty, COUNT(*) as total, SUM(a.is_correct) as correct
                    FROM quiz_answers a {user_where} AND a.difficulty IS NOT NULL
                    GROUP BY a.difficulty
                """, user_params)
                stats["by_difficulty"] = [dict(r) for r in self._db.cursor.fetchall()]

                return stats
        except Exception as e:
            error(f"获取答题统计失败: {e}")
            return {}

    def get_weak_topics(self, user_id: int, limit: int = 10) -> list[dict]:
        """获取薄弱知识点排行（正确率低且题量够）"""
        try:
            with self._db:
                self._db.cursor.execute("""
                    SELECT knowledge_point,
                           COUNT(*) as total,
                           SUM(is_correct) as correct,
                           ROUND(CAST(SUM(is_correct) AS REAL) / COUNT(*) * 100, 1) as accuracy
                    FROM quiz_answers
                    WHERE user_id = ? AND knowledge_point IS NOT NULL AND knowledge_point != ''
                    GROUP BY knowledge_point
                    HAVING total >= 2
                    ORDER BY accuracy ASC, total DESC
                    LIMIT ?
                """, (user_id, limit))
                return [dict(r) for r in self._db.cursor.fetchall()]
        except Exception as e:
            error(f"获取薄弱知识点失败: {e}")
            return []

    def get_questions_for_review(self, user_id: int, subject: str | None = None,
                                 limit: int = 10) -> list[dict]:
        """获取需要复习的错题（用于错题重练）"""
        try:
            with self._db:
                where = "WHERE a.user_id = ? AND a.is_correct = 0"
                params: list = [user_id]
                if subject:
                    where += " AND a.knowledge_point IN (SELECT DISTINCT knowledge_point FROM quiz_answers WHERE user_id = ?)"
                    # 简化：直接按 session 的 subject 过滤
                    where = "WHERE a.user_id = ? AND a.is_correct = 0 AND a.session_id IN (SELECT id FROM quiz_sessions WHERE user_id = ? AND subject = ?)"
                    params = [user_id, user_id, subject]

                self._db.cursor.execute(f"""
                    SELECT a.question_text, a.question_type, a.options, a.correct_answer,
                           a.explanation, a.knowledge_point, a.difficulty
                    FROM quiz_answers a {where}
                    ORDER BY RANDOM() LIMIT ?
                """, params + [limit])
                rows = []
                for r in self._db.cursor.fetchall():
                    row = dict(r)
                    if row.get("options") and isinstance(row["options"], str):
                        try:
                            row["options"] = json.loads(row["options"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    rows.append(row)
                return rows
        except Exception as e:
            error(f"获取复习题目失败: {e}")
            return []

    # ── 题库管理 ──

    def save_to_bank(self, subject: str, questions: list[dict]) -> int:
        """将题目批量存入题库，返回新增数量"""
        saved = 0
        try:
            with self._db:
                for q in questions:
                    qt = (q.get("question") or q.get("question_text") or "").strip()
                    if not qt:
                        continue
                    # 去重：同一学科下相同题目文本不重复存入
                    self._db.cursor.execute(
                        "SELECT id FROM question_bank WHERE subject = ? AND question_text = ?",
                        (subject, qt)
                    )
                    if self._db.cursor.fetchone():
                        continue
                    self._db.cursor.execute(
                        "INSERT INTO question_bank (subject, question_type, question_text, options, correct_answer, explanation, knowledge_point, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            subject,
                            q.get("type") or q.get("question_type") or "fill_blank",
                            qt,
                            json.dumps(q.get("options", []), ensure_ascii=False) if q.get("options") else None,
                            q.get("answer") or q.get("correct_answer") or "",
                            q.get("explanation") or "",
                            q.get("knowledge_point") or "",
                            q.get("difficulty") or "medium",
                        )
                    )
                    saved += 1
                self._db.conn.commit()
        except Exception as e:
            error(f"存入题库失败: {e}")
        return saved

    def get_from_bank(self, subject: str | None = None, count: int = 10) -> list[dict]:
        """从题库取题，优先取使用次数少的"""
        try:
            with self._db:
                if subject:
                    self._db.cursor.execute(
                        "SELECT * FROM question_bank WHERE subject = ? ORDER BY use_count ASC, RANDOM() LIMIT ?",
                        (subject, count)
                    )
                else:
                    self._db.cursor.execute(
                        "SELECT * FROM question_bank ORDER BY use_count ASC, RANDOM() LIMIT ?",
                        (count,)
                    )
                rows = []
                for r in self._db.cursor.fetchall():
                    row = dict(r)
                    if row.get("options") and isinstance(row["options"], str):
                        try:
                            row["options"] = json.loads(row["options"])
                        except (json.JSONDecodeError, TypeError):
                            pass
                    # 映射为前端期望的字段名
                    rows.append({
                        "id": row["id"],
                        "type": row.get("question_type", "fill_blank"),
                        "question": row["question_text"],
                        "options": row.get("options") or [],
                        "answer": row.get("correct_answer", ""),
                        "explanation": row.get("explanation", ""),
                        "difficulty": row.get("difficulty", "medium"),
                        "knowledge_point": row.get("knowledge_point", ""),
                    })
                return rows
        except Exception as e:
            error(f"从题库取题失败: {e}")
            return []

    def mark_bank_used(self, question_ids: list[int]) -> None:
        """标记题库中的题目已被使用（use_count + 1）"""
        try:
            with self._db:
                for qid in question_ids:
                    self._db.cursor.execute(
                        "UPDATE question_bank SET use_count = use_count + 1 WHERE id = ?", (qid,)
                    )
                self._db.conn.commit()
        except Exception as e:
            error(f"标记题库使用失败: {e}")


_quiz_dao: QuizDAO | None = None


def get_quiz_dao() -> QuizDAO:
    global _quiz_dao
    if _quiz_dao is None:
        from data.db_operations import assessment_db
        _quiz_dao = QuizDAO(assessment_db)
    return _quiz_dao


class AnalyticsDAO:
    """学情分析聚合查询"""

    def __init__(self, resource_db, assessment_db):
        self._resource_db = resource_db
        self._assessment_db = assessment_db

    def get_subject_breakdown(self, user_id: int) -> list[dict]:
        """按学科聚合资源和学习数据"""
        try:
            with self._resource_db:
                self._resource_db.cursor.execute("""
                    SELECT subject, COUNT(*) as resource_count,
                           COALESCE(SUM(duration_minutes), 0) as total_minutes
                    FROM learning_resources
                    WHERE user_id = ? AND subject IS NOT NULL AND subject != ''
                    GROUP BY subject ORDER BY resource_count DESC
                """, (user_id,))
                return [dict(r) for r in self._resource_db.cursor.fetchall()]
        except Exception as e:
            error(f"获取学科分布失败: {e}")
            return []

    def get_resource_type_breakdown(self, user_id: int) -> list[dict]:
        """按资源类型聚合"""
        try:
            with self._resource_db:
                self._resource_db.cursor.execute("""
                    SELECT resource_type, COUNT(*) as count
                    FROM learning_resources WHERE user_id = ?
                    GROUP BY resource_type ORDER BY count DESC
                """, (user_id,))
                return [dict(r) for r in self._resource_db.cursor.fetchall()]
        except Exception as e:
            error(f"获取资源类型分布失败: {e}")
            return []

    def get_study_trend(self, user_id: int, days: int = 30) -> list[dict]:
        """获取学习时间趋势（按日）"""
        try:
            with self._assessment_db:
                self._assessment_db.cursor.execute("""
                    SELECT DATE(created_at) as date,
                           COALESCE(SUM(duration_seconds), 0) as seconds
                    FROM learning_activities
                    WHERE user_id = ? AND activity_type = 'session'
                          AND created_at >= DATE('now', ? || ' days')
                    GROUP BY DATE(created_at) ORDER BY date
                """, (user_id, f"-{days}"))
                return [dict(r) for r in self._assessment_db.cursor.fetchall()]
        except Exception as e:
            error(f"获取学习趋势失败: {e}")
            return []

    def get_quiz_trend(self, user_id: int, days: int = 30) -> list[dict]:
        """获取做题正确率趋势"""
        try:
            with self._assessment_db:
                self._assessment_db.cursor.execute("""
                    SELECT DATE(created_at) as date,
                           ROUND(AVG(score), 1) as avg_score,
                           COUNT(*) as quiz_count,
                           SUM(total_questions) as total_q,
                           SUM(correct_count) as total_correct
                    FROM quiz_sessions
                    WHERE user_id = ? AND status = 'completed'
                          AND created_at >= DATE('now', ? || ' days')
                    GROUP BY DATE(created_at) ORDER BY date
                """, (user_id, f"-{days}"))
                return [dict(r) for r in self._assessment_db.cursor.fetchall()]
        except Exception as e:
            error(f"获取做题趋势失败: {e}")
            return []

    def get_knowledge_mastery(self, user_id: int) -> list[dict]:
        """获取知识点掌握度"""
        try:
            with self._assessment_db:
                self._assessment_db.cursor.execute("""
                    SELECT knowledge_point,
                           COUNT(*) as total,
                           SUM(is_correct) as correct,
                           ROUND(CAST(SUM(is_correct) AS REAL) / COUNT(*) * 100, 1) as accuracy
                    FROM quiz_answers
                    WHERE user_id = ? AND knowledge_point IS NOT NULL AND knowledge_point != ''
                    GROUP BY knowledge_point ORDER BY accuracy ASC
                """, (user_id,))
                return [dict(r) for r in self._assessment_db.cursor.fetchall()]
        except Exception as e:
            error(f"获取知识点掌握度失败: {e}")
            return []

    def get_weekly_report(self, user_id: int) -> dict:
        """生成周报数据"""
        try:
            report: dict = {}
            with self._assessment_db:
                # 本周学习时长
                self._assessment_db.cursor.execute("""
                    SELECT COALESCE(SUM(duration_seconds), 0) as seconds
                    FROM learning_activities
                    WHERE user_id = ? AND activity_type = 'session'
                          AND created_at >= DATE('now', 'weekday 0', '-7 days')
                """, (user_id,))
                row = self._assessment_db.cursor.fetchone()
                report["study_seconds"] = dict(row)["seconds"] if row else 0

                # 本周做题统计
                self._assessment_db.cursor.execute("""
                    SELECT COUNT(*) as quiz_count,
                           COALESCE(SUM(total_questions), 0) as questions,
                           COALESCE(SUM(correct_count), 0) as correct,
                           COALESCE(AVG(score), 0) as avg_score
                    FROM quiz_sessions
                    WHERE user_id = ? AND status = 'completed'
                          AND created_at >= DATE('now', 'weekday 0', '-7 days')
                """, (user_id,))
                row = self._db_cursor_or_dict(self._assessment_db.cursor.fetchone())
                report["quiz"] = row

                # 本周薄弱知识点
                self._assessment_db.cursor.execute("""
                    SELECT knowledge_point, COUNT(*) as total,
                           SUM(is_correct) as correct,
                           ROUND(CAST(SUM(is_correct) AS REAL) / COUNT(*) * 100, 1) as accuracy
                    FROM quiz_answers
                    WHERE user_id = ? AND knowledge_point IS NOT NULL
                          AND created_at >= DATE('now', 'weekday 0', '-7 days')
                    GROUP BY knowledge_point HAVING total >= 2
                    ORDER BY accuracy ASC LIMIT 5
                """, (user_id,))
                report["weak_topics"] = [dict(r) for r in self._assessment_db.cursor.fetchall()]

            with self._resource_db:
                # 本周新增资源
                self._resource_db.cursor.execute("""
                    SELECT COUNT(*) as count FROM learning_resources
                    WHERE user_id = ? AND created_at >= DATE('now', 'weekday 0', '-7 days')
                """, (user_id,))
                row = self._resource_db.cursor.fetchone()
                report["new_resources"] = dict(row)["count"] if row else 0

            return report
        except Exception as e:
            error(f"生成周报失败: {e}")
            return {}

    @staticmethod
    def _db_cursor_or_dict(row):
        return dict(row) if row else {}


_analytics_dao: AnalyticsDAO | None = None


def get_analytics_dao() -> AnalyticsDAO:
    global _analytics_dao
    if _analytics_dao is None:
        from data.db_operations import resource_db, assessment_db
        _analytics_dao = AnalyticsDAO(resource_db, assessment_db)
    return _analytics_dao

