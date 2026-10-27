"""
主观题批改服务
手写图识别（专用 OCR + 视觉兜底）→ RAG 知识库匹配评分依据
→ AI 评分（分数 + 评语 + 知识点诊断）→ 教师复核改分 → 班级批改报告
"""

import json
import re
import time
from pathlib import Path

from core.json_utils import safe_parse_json
from core.logger import error, info, warning

from data.config import get_assessments_db_path, get_auth_db_path
from services.exam_paper_service import (
    OBJECTIVE_TYPES,
    _conn,
    _normalize_type,
    _row,
    _rows,
)

UPLOAD_DIR = Path("uploads/exam_answers")

GRADE_SUBJECTIVE_PROMPT = """你是严格而公正的阅卷老师。请根据参考答案和评分要点批改学生的主观题作答。只输出 JSON，不要输出其它内容。

## 题目
{question}

## 参考答案
{reference_answer}

## 评分要点（本题共 {max_score} 分，按要点给分）
{scoring_points}

## 知识库参考依据（评分时作为标准依据）
{rag_evidence}

## 学生作答（OCR 识别文本，可能存在识别误差，请结合题意理解，识别错别字不要扣分）
{student_answer}

## 输出 JSON 格式
{{
  "score": 得分（0 到 {max_score} 之间的数字，可带小数）,
  "percentage": 百分制得分（0-100 整数）,
  "comment": "针对性评语（指出优点与问题，50~120字）",
  "knowledge_point_hits": ["学生答到的知识点或要点"],
  "missing_points": ["缺失或错误的要点"],
  "improvement": "具体改进建议（一句话）"
}}"""


def _norm_text(s: str) -> str:
    """归一化文本用于客观题比对"""
    s = (s or "").strip().lower()
    s = re.sub(r"[\s　。，,.、;；:：!！?？\"'“”‘’()（）\[\]【】]", "", s)
    return s


class GradingService:
    """提交管理 + OCR + AI 批改 + 复核 + 报告"""

    # ==================== 提交管理 ====================

    def get_or_create_submission(self, assignment_id: int, paper_id: int, student_id: int) -> dict:
        conn = _conn(get_assessments_db_path())
        try:
            sub = _row(conn.execute(
                "SELECT * FROM exam_submissions WHERE assignment_id = ? AND student_id = ?",
                (assignment_id, student_id),
            ))
            if sub:
                return {"success": True, "data": sub, "created": False}
            cur = conn.execute(
                """INSERT INTO exam_submissions (assignment_id, paper_id, student_id, status)
                   VALUES (?, ?, ?, 'in_progress')""",
                (assignment_id, paper_id, student_id),
            )
            conn.commit()
            sub = _row(conn.execute("SELECT * FROM exam_submissions WHERE id = ?", (cur.lastrowid,)))
            return {"success": True, "data": sub, "created": True}
        except Exception as e:
            error(f"创建提交记录失败: {e}")
            return {"success": False, "message": f"创建失败: {e}"}
        finally:
            conn.close()

    def list_submissions(self, assignment_id: int) -> list[dict]:
        conn = _conn(get_assessments_db_path())
        try:
            subs = _rows(conn.execute(
                """SELECT * FROM exam_submissions WHERE assignment_id = ?
                   ORDER BY status, id""",
                (assignment_id,),
            ))
            if not subs:
                return []
            # 补学生名（auth 库）
            names = self._user_names([s["student_id"] for s in subs])
            for s in subs:
                s["student_name"] = names.get(s["student_id"], f"学生{s['student_id']}")
                s["answer_count"] = int(conn.execute(
                    "SELECT COUNT(*) AS c FROM exam_answers WHERE submission_id = ?", (s["id"],)
                ).fetchone()["c"])
                s["graded_count"] = int(conn.execute(
                    "SELECT COUNT(*) AS c FROM exam_answers WHERE submission_id = ? AND grade_status != 'pending'",
                    (s["id"],),
                ).fetchone()["c"])
            return subs
        except Exception as e:
            error(f"查询提交列表失败: {e}")
            return []
        finally:
            conn.close()

    def get_submission_detail(self, submission_id: int) -> dict | None:
        conn = _conn(get_assessments_db_path())
        try:
            sub = _row(conn.execute("SELECT * FROM exam_submissions WHERE id = ?", (submission_id,)))
            if not sub:
                return None
            names = self._user_names([sub["student_id"]])
            sub["student_name"] = names.get(sub["student_id"], f"学生{sub['student_id']}")
            answers = _rows(conn.execute(
                "SELECT * FROM exam_answers WHERE submission_id = ? ORDER BY q_index", (submission_id,)
            ))
            for a in answers:
                a["scoring_points"] = []
                a["rag_evidence"] = safe_parse_json(a.get("rag_evidence") or "[]") or []
                a["knowledge_hits"] = safe_parse_json(a.get("knowledge_hits") or "{}") or {}
            sub["answers"] = answers
            return sub
        except Exception as e:
            error(f"查询提交详情失败: {e}")
            return None
        finally:
            conn.close()

    def _user_names(self, user_ids: list[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        try:
            conn = _conn(get_auth_db_path())
            try:
                placeholders = ",".join(["?"] * len(user_ids))
                rows = _rows(conn.execute(
                    f"SELECT id, username FROM users WHERE id IN ({placeholders})", user_ids
                ))
                return {r["id"]: r["username"] for r in rows}
            finally:
                conn.close()
        except Exception as e:
            warning(f"查询学生姓名失败: {e}")
            return {}

    def save_answer(self, submission_id: int, question_id: int, *,
                    answer_text: str | None = None) -> dict:
        """保存/更新单题文字作答"""
        conn = _conn(get_assessments_db_path())
        try:
            ans = _row(conn.execute(
                "SELECT * FROM exam_answers WHERE submission_id = ? AND question_id = ?",
                (submission_id, question_id),
            ))
            if ans:
                if answer_text is not None:
                    conn.execute(
                        "UPDATE exam_answers SET answer_text = ? WHERE id = ?", (answer_text, ans["id"])
                    )
                answer_id = ans["id"]
            else:
                q = _row(conn.execute("SELECT * FROM exam_questions WHERE id = ?", (question_id,)))
                if not q:
                    return {"success": False, "message": "题目不存在"}
                cur = conn.execute(
                    """INSERT INTO exam_answers
                       (submission_id, question_id, q_index, question_type, question_text,
                        answer_text, correct_answer, reference_answer, max_score, grade_status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
                    (
                        submission_id, question_id, q["q_index"],
                        _normalize_type(q["question_type"]), q["question_text"],
                        answer_text or "", q.get("correct_answer") or "",
                        q.get("reference_answer") or "", float(q.get("score") or 0),
                    ),
                )
                answer_id = cur.lastrowid
            conn.commit()
            return {"success": True, "answer_id": answer_id}
        except Exception as e:
            error(f"保存作答失败: {e}")
            return {"success": False, "message": f"保存失败: {e}"}
        finally:
            conn.close()

    def save_answer_image(self, submission_id: int, question_id: int,
                          image_bytes: bytes, filename: str = "") -> dict:
        """保存手写答案图片（返回 answer_id + 图片相对路径）"""
        saved = self.save_answer(submission_id, question_id)
        if not saved.get("success"):
            return saved
        answer_id = saved["answer_id"]
        try:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            sub_dir = UPLOAD_DIR / str(submission_id)
            sub_dir.mkdir(parents=True, exist_ok=True)
            ext = Path(filename).suffix.lower() if filename else ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
                ext = ".jpg"
            rel = sub_dir / f"q{question_id}_{int(time.time() * 1000)}{ext}"
            rel.write_bytes(image_bytes)
            conn = _conn(get_assessments_db_path())
            try:
                conn.execute(
                    "UPDATE exam_answers SET answer_image_path = ? WHERE id = ?",
                    (str(rel).replace("\\", "/"), answer_id),
                )
                conn.commit()
            finally:
                conn.close()
            return {"success": True, "answer_id": answer_id,
                    "image_path": str(rel).replace("\\", "/")}
        except Exception as e:
            error(f"保存手写图失败: {e}")
            return {"success": False, "message": f"图片保存失败: {e}"}

    def ocr_answer(self, answer_id: int, image_bytes: bytes | None = None) -> dict:
        """手写识别：优先用已存图片，也可直接传图；识别结果写回 ocr_text"""
        conn = _conn(get_assessments_db_path())
        try:
            ans = _row(conn.execute("SELECT * FROM exam_answers WHERE id = ?", (answer_id,)))
            if not ans:
                return {"success": False, "message": "作答记录不存在"}
            if image_bytes is None:
                img_path = ans.get("answer_image_path")
                if not img_path or not Path(img_path).exists():
                    return {"success": False, "message": "请先上传手写答案图片"}
                image_bytes = Path(img_path).read_bytes()

            from services.handwriting_ocr_service import handwriting_ocr

            result = handwriting_ocr.recognize(image_bytes)
            if not result.get("success"):
                return {"success": False, "message": "识别失败，请重拍或手动输入"}

            ocr_text = result["text"]
            # 默认用 OCR 文本填充作答（教师可再改）
            conn.execute(
                """UPDATE exam_answers
                   SET ocr_text = ?, ocr_confidence = ?, ocr_engine = ?, answer_text = ?
                   WHERE id = ?""",
                (ocr_text, result.get("confidence") or 0, result.get("engine") or "",
                 ocr_text, answer_id),
            )
            conn.commit()
            return {
                "success": True, "ocr_text": ocr_text,
                "confidence": result.get("confidence"), "engine": result.get("engine"),
                "low_confidence": result.get("low_confidence", False),
                "segments": result.get("segments") or [],
            }
        except Exception as e:
            error(f"手写识别失败: {e}")
            return {"success": False, "message": f"识别失败: {e}"}
        finally:
            conn.close()

    def submit(self, submission_id: int) -> dict:
        conn = _conn(get_assessments_db_path())
        try:
            sub = _row(conn.execute("SELECT * FROM exam_submissions WHERE id = ?", (submission_id,)))
            if not sub:
                return {"success": False, "message": "提交记录不存在"}
            conn.execute(
                """UPDATE exam_submissions
                   SET status = 'submitted', submitted_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (submission_id,),
            )
            conn.commit()
            return {"success": True, "message": "已交卷"}
        except Exception as e:
            return {"success": False, "message": f"交卷失败: {e}"}
        finally:
            conn.close()

    # ==================== AI 判分 ====================

    def grade_answer(self, answer_id: int) -> dict:
        """单题批改：客观题自动判分，主观题 RAG + AI 评分"""
        conn = _conn(get_assessments_db_path())
        try:
            ans = _row(conn.execute("SELECT * FROM exam_answers WHERE id = ?", (answer_id,)))
            if not ans:
                return {"success": False, "message": "作答记录不存在"}
            qtype = _normalize_type(ans.get("question_type"))
            max_score = float(ans.get("max_score") or 0)
            student_text = (ans.get("answer_text") or "").strip()
            if not student_text and not ans.get("answer_image_path"):
                return {"success": False, "message": "该题暂无作答内容"}

            if qtype in OBJECTIVE_TYPES:
                result = self._grade_objective(ans, max_score)
            else:
                result = self._grade_subjective(ans, max_score)

            conn.execute(
                """UPDATE exam_answers
                   SET ai_score = ?, score = ?, feedback = ?, rag_evidence = ?,
                       knowledge_hits = ?, is_correct = ?, grade_status = 'ai_graded'
                   WHERE id = ?""",
                (
                    result["score"], result["score"], result.get("comment") or "",
                    json.dumps(result.get("rag_evidence") or [], ensure_ascii=False),
                    json.dumps(result.get("knowledge_hits") or {}, ensure_ascii=False),
                    1 if result.get("is_correct") else 0, answer_id,
                ),
            )
            conn.commit()
            self._refresh_submission_totals(ans["submission_id"])
            result["success"] = True
            return result
        except Exception as e:
            error(f"批改失败: {e}")
            return {"success": False, "message": f"批改失败: {e}"}
        finally:
            conn.close()

    def _grade_objective(self, ans: dict, max_score: float) -> dict:
        """客观题判分"""
        qtype = _normalize_type(ans.get("question_type"))
        user = _norm_text(ans.get("answer_text") or "")
        correct = _norm_text(ans.get("correct_answer") or "")
        if qtype == "judge":
            truthy = {"true", "t", "yes", "y", "对", "正确", "√", "1"}
            falsy = {"false", "f", "no", "n", "错", "错误", "×", "0"}
            u = user.strip()
            c = correct.strip()
            is_correct = (u in truthy and c in truthy) or (u in falsy and c in falsy) or (u == c)
        elif qtype == "multiple_choice":
            u = re.sub(r"[^a-d]", "", user)[:1]
            c = re.sub(r"[^a-d]", "", correct)[:1]
            is_correct = bool(u) and u == c
        else:  # fill_blank
            is_correct = bool(correct) and (user == correct or correct in user or user in correct)
        score = max_score if is_correct else 0.0
        comment = "回答正确。" if is_correct else f"回答错误，正确答案：{ans.get('correct_answer') or '（见解析）'}"
        return {
            "score": score, "is_correct": is_correct, "comment": comment,
            "knowledge_hits": {"hits": [ans.get("knowledge_point")] if is_correct else [],
                               "missing": [] if is_correct else [ans.get("knowledge_point")]},
            "rag_evidence": [],
        }

    def _grade_subjective(self, ans: dict, max_score: float) -> dict:
        """主观题：RAG 匹配依据 + AI 评分"""
        question = ans.get("question_text") or ""
        reference = ans.get("reference_answer") or ""
        student_text = (ans.get("answer_text") or "").strip()
        if not student_text:
            student_text = "（学生未作答）"

        # 评分要点与学科：评分要点存于 exam_questions.scoring_points
        scoring_points: list[str] = []
        subject = ""
        knowledge_point = ""
        try:
            conn = _conn(get_assessments_db_path())
            try:
                q = _row(conn.execute("SELECT scoring_points, knowledge_point FROM exam_questions WHERE id = ?",
                                      (ans.get("question_id"),)))
                if q:
                    scoring_points = safe_parse_json(q.get("scoring_points") or "[]") or []
                    knowledge_point = q.get("knowledge_point") or ""
                row = _row(conn.execute(
                    """SELECT p.subject FROM exam_submissions s
                       JOIN exam_papers p ON p.id = s.paper_id WHERE s.id = ?""",
                    (ans.get("submission_id"),),
                ))
                if row:
                    subject = row.get("subject") or ""
            finally:
                conn.close()
        except Exception as e:
            warning(f"读取评分要点失败: {e}")

        # RAG 知识库匹配评分依据
        rag_evidence = self._rag_evidence(question, student_text, ans.get("subject"), knowledge_point)
        evidence_text = "\n".join(
            f"- 《{e.get('title', '资料')}》：{e.get('content', '')[:300]}" for e in rag_evidence
        ) or "（知识库暂无相关内容，按通用评分标准评阅）"

        points_text = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(scoring_points)) or "（按参考答案要点给分）"

        prompt = GRADE_SUBJECTIVE_PROMPT.format(
            question=question, reference_answer=reference or "（无）",
            max_score=max_score, scoring_points=points_text,
            rag_evidence=evidence_text, student_answer=student_text[:2000],
        )

        result = None
        try:
            from services.spark_client import spark_client

            raw = spark_client.chat(prompt, max_tokens=2000, temperature=0.2)
            data = safe_parse_json(raw) if raw else None
            if data and isinstance(data, dict):
                result = {
                    "score": min(float(data.get("score") or 0), max_score),
                    "comment": str(data.get("comment") or "").strip(),
                    "knowledge_hits": {
                        "hits": [str(x) for x in (data.get("knowledge_point_hits") or [])],
                        "missing": [str(x) for x in (data.get("missing_points") or [])],
                    },
                    "improvement": str(data.get("improvement") or "").strip(),
                }
        except Exception as e:
            error(f"AI 评分异常: {e}")

        if result is None:
            # 兜底：按评分要点关键词覆盖给分
            result = self._fallback_grade(student_text, scoring_points, max_score)

        result["rag_evidence"] = rag_evidence
        if result.get("improvement"):
            result["comment"] = (result.get("comment") or "") + f" 建议：{result['improvement']}"
        return result

    def _fallback_grade(self, student_text: str, scoring_points: list[str], max_score: float) -> dict:
        """LLM 失败时的规则兜底评分"""
        if not scoring_points:
            pct = 0.6 if len(student_text) > 30 else (0.3 if student_text else 0.0)
        else:
            hits = []
            for p in scoring_points:
                chunks = [c.strip() for c in re.split(r"[，,、;；。.()（）\s]+", p) if len(c.strip()) >= 2]
                if any(c in student_text for c in chunks) or (len(p) >= 4 and p[:4] in student_text):
                    hits.append(p)
            pct = len(hits) / len(scoring_points)
        score = round(max_score * pct, 1)
        return {
            "score": score,
            "comment": f"（AI 精评暂不可用，按要点覆盖度初评 {score}/{max_score} 分，请教师复核）",
            "knowledge_hits": {"hits": [], "missing": [p for p in scoring_points if p not in student_text]},
            "improvement": "",
        }

    def _rag_evidence(self, question: str, student_text: str,
                      subject: str | None, knowledge_point: str) -> list[dict]:
        """从 RAG 知识库匹配评分依据"""
        evidence: list[dict] = []
        seen: set[str] = set()
        query = f"{question} {student_text[:120]}".strip()
        try:
            from services.advanced_retrieval_service import retrieval_service

            docs = retrieval_service.smart_search(None, query, subject=subject, limit=4) or []
            for d in docs:
                title = d.get("title") or "资料"
                content = (d.get("content") or d.get("content_text") or "")[:400]
                if title in seen or not content:
                    continue
                seen.add(title)
                evidence.append({"title": title, "content": content,
                                 "score": d.get("score") or d.get("similarity") or 0,
                                 "source": "hybrid_search"})
        except Exception as e:
            warning(f"RAG 混合检索失败: {e}")
        if knowledge_point:
            try:
                from data.rag_knowledge_base import rag_kb

                rows = rag_kb.search_by_knowledge_point(knowledge_point, limit=3) or []
                for r in rows:
                    title = r.get("title") or "资料"
                    content = (r.get("content_text") or r.get("content") or "")[:400]
                    if title in seen or not content:
                        continue
                    seen.add(title)
                    evidence.append({"title": title, "content": content,
                                     "score": 1.0, "source": f"knowledge_point:{knowledge_point}"})
            except Exception as e:
                warning(f"RAG 知识点检索失败: {e}")
        return evidence[:5]

    def grade_submission(self, submission_id: int) -> dict:
        """整卷批改"""
        detail = self.get_submission_detail(submission_id)
        if not detail:
            return {"success": False, "message": "提交记录不存在"}
        graded, failed = 0, 0
        for ans in detail.get("answers") or []:
            r = self.grade_answer(ans["id"])
            if r.get("success"):
                graded += 1
            else:
                failed += 1
        self._refresh_submission_totals(submission_id)
        return {"success": True, "message": f"批改完成：{graded} 题"
                + (f"（{failed} 题失败）" if failed else ""),
                "graded": graded, "failed": failed}

    def review_answer(self, answer_id: int, teacher_score: float | None,
                      teacher_feedback: str | None = None) -> dict:
        """教师复核改分（最终成绩以教师为准）"""
        conn = _conn(get_assessments_db_path())
        try:
            ans = _row(conn.execute("SELECT * FROM exam_answers WHERE id = ?", (answer_id,)))
            if not ans:
                return {"success": False, "message": "作答记录不存在"}
            max_score = float(ans.get("max_score") or 0)
            if teacher_score is not None:
                teacher_score = max(0.0, min(float(teacher_score), max_score))
            conn.execute(
                """UPDATE exam_answers
                   SET teacher_score = ?, teacher_feedback = ?,
                       grade_status = 'teacher_reviewed', reviewed_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (teacher_score, teacher_feedback or "", answer_id),
            )
            conn.commit()
            self._refresh_submission_totals(ans["submission_id"])
            return {"success": True, "message": "已复核"}
        except Exception as e:
            return {"success": False, "message": f"复核失败: {e}"}
        finally:
            conn.close()

    def _refresh_submission_totals(self, submission_id: int) -> None:
        """汇总：客观分 / AI 分 / 最终分（教师复核优先）"""
        conn = _conn(get_assessments_db_path())
        try:
            answers = _rows(conn.execute(
                "SELECT * FROM exam_answers WHERE submission_id = ?", (submission_id,)
            ))
            if not answers:
                return
            objective = sum(float(a.get("max_score") or 0) for a in answers
                            if _normalize_type(a.get("question_type")) in OBJECTIVE_TYPES
                            and (a.get("is_correct") or 0))
            ai_total = sum(float(a.get("ai_score") or 0) for a in answers)
            final = 0.0
            all_reviewed = True
            any_graded = False
            for a in answers:
                if a.get("grade_status") == "teacher_reviewed":
                    final += float(a.get("teacher_score") if a.get("teacher_score") is not None
                                   else a.get("score") or 0)
                elif a.get("grade_status") == "ai_graded":
                    any_graded = True
                    final += float(a.get("score") or 0)
                else:
                    all_reviewed = False
            status = "reviewed" if all_reviewed and answers else (
                "graded" if any_graded or all_reviewed else "submitted")
            conn.execute(
                """UPDATE exam_submissions
                   SET objective_score = ?, ai_score = ?, final_score = ?, total_score = ?,
                       status = ?, graded_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (objective, ai_total, final, final, status, submission_id),
            )
            conn.commit()
        except Exception as e:
            error(f"汇总提交分数失败: {e}")
        finally:
            conn.close()

    # ==================== 班级批改报告 ====================

    def class_report(self, assignment_id: int) -> dict:
        """班级批改报告：得分分布 + 逐题统计 + 共性薄弱知识点"""
        conn = _conn(get_assessments_db_path())
        try:
            subs = _rows(conn.execute(
                "SELECT * FROM exam_submissions WHERE assignment_id = ? AND status IN ('submitted','graded','reviewed')",
                (assignment_id,),
            ))
            questions = _rows(conn.execute(
                """SELECT q.* FROM exam_questions q
                   JOIN exam_assignments a ON a.paper_id = q.paper_id
                   WHERE a.id = ? ORDER BY q.q_index""",
                (assignment_id,),
            ))
            names = self._user_names([s["student_id"] for s in subs]) if subs else {}
            paper = _row(conn.execute(
                """SELECT p.total_score, p.title, p.subject FROM exam_assignments a
                   JOIN exam_papers p ON p.id = a.paper_id WHERE a.id = ?""",
                (assignment_id,),
            ))
            total_score = float((paper or {}).get("total_score") or 100)

            scores = [float(s.get("final_score") or 0) for s in subs]
            graded_subs = [s for s in subs if s.get("status") in ("graded", "reviewed")]
            dist = {"90%以上": 0, "80%~90%": 0, "70%~80%": 0, "60%~70%": 0, "60%以下": 0}
            for s in scores:
                pct = s / total_score * 100 if total_score else 0
                if pct >= 90:
                    dist["90%以上"] += 1
                elif pct >= 80:
                    dist["80%~90%"] += 1
                elif pct >= 70:
                    dist["70%~80%"] += 1
                elif pct >= 60:
                    dist["60%~70%"] += 1
                else:
                    dist["60%以下"] += 1

            # 逐题统计
            question_stats = []
            for q in questions:
                ans_rows = _rows(conn.execute(
                    "SELECT * FROM exam_answers WHERE question_id = ?", (q["id"],)
                ))
                graded_rows = [a for a in ans_rows if a.get("grade_status") != "pending"]
                if not graded_rows:
                    question_stats.append({
                        "question_id": q["id"], "q_index": q["q_index"],
                        "question_type": q["question_type"],
                        "knowledge_point": q.get("knowledge_point") or "",
                        "avg_score": 0, "avg_rate": 0, "graded_count": 0,
                    })
                    continue
                avg = sum(float(a.get("score") or 0) for a in graded_rows) / len(graded_rows)
                q_max = float(q.get("score") or 1) or 1
                question_stats.append({
                    "question_id": q["id"], "q_index": q["q_index"],
                    "question_type": q["question_type"],
                    "knowledge_point": q.get("knowledge_point") or "",
                    "avg_score": round(avg, 2),
                    "avg_rate": round(avg / q_max * 100, 1),
                    "graded_count": len(graded_rows),
                })

            # 共性薄弱知识点（统计 missing_points）
            missing_counter: dict[str, int] = {}
            for s in subs:
                for a in _rows(conn.execute(
                    "SELECT knowledge_hits FROM exam_answers WHERE submission_id = ?",
                    (s["id"],),
                )):
                    kh = safe_parse_json(a.get("knowledge_hits") or "{}") or {}
                    for m in (kh.get("missing") or []):
                        if m:
                            missing_counter[str(m)] = missing_counter.get(str(m), 0) + 1
            weak_points = sorted(missing_counter.items(), key=lambda x: -x[1])[:10]

            ranked = sorted(
                [{"student_id": s["student_id"],
                  "student_name": names.get(s["student_id"], f"学生{s['student_id']}"),
                  "final_score": float(s.get("final_score") or 0),
                  "status": s.get("status")} for s in subs],
                key=lambda x: -x["final_score"],
            )

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0
            return {
                "success": True,
                "data": {
                    "assignment_id": assignment_id,
                    "title": (paper or {}).get("title") or "",
                    "total_score": total_score,
                    "submission_count": len(subs),
                    "graded_count": len(graded_subs),
                    "avg_score": avg_score,
                    "avg_rate": round(avg_score / total_score * 100, 1) if total_score else 0,
                    "max_score": max(scores) if scores else 0,
                    "min_score": min(scores) if scores else 0,
                    "score_distribution": dist,
                    "question_stats": question_stats,
                    "weak_points": [{"point": p, "miss_count": c} for p, c in weak_points],
                    "ranking": ranked,
                },
            }
        except Exception as e:
            error(f"生成班级报告失败: {e}")
            return {"success": False, "message": f"报告生成失败: {e}"}
        finally:
            conn.close()


grading_service = GradingService()
