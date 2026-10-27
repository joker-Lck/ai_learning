"""
AI 出题 / 组卷服务（教师端）
RAG 知识库取材 + 题库复用 + LLM 生成，支持练习卷/考试卷，题目可编辑、导出、发布到班级
"""

import json
from datetime import datetime

from core.json_utils import safe_parse_json
from core.logger import error, info, warning

from data.config import get_assessments_db_path

# ── 题型定义 ──
QUESTION_TYPES = ["multiple_choice", "judge", "fill_blank", "short_answer"]
TYPE_LABELS = {
    "multiple_choice": "选择题",
    "judge": "判断题",
    "fill_blank": "填空题",
    "short_answer": "简答题",
    "subjective": "简答题",
    "choice": "选择题",
    "fill": "填空题",
}
OBJECTIVE_TYPES = {"multiple_choice", "judge", "fill_blank"}
# 用于分值折算的基准分（相对权重）
TYPE_BASE_SCORE = {
    "multiple_choice": 3.0,
    "judge": 2.0,
    "fill_blank": 4.0,
    "short_answer": 10.0,
}
DEFAULT_SPEC = {
    "multiple_choice": 5,
    "judge": 3,
    "fill_blank": 3,
    "short_answer": 2,
}

PAPER_GEN_PROMPT = """你是资深命题专家。请严格按要求生成一份{paper_type_label}的试题，只输出 JSON。

## 命题要求
- 学科：{subject}
- 年级：{grade}
- 主题/范围：{topic}
- 知识点：{knowledge_points}
- 难度：{difficulty_label}
- 题型与数量（必须严格满足）：{spec_desc}

## 教材参考依据（命题须贴合以下材料）
{rag_context}

## 输出 JSON 格式（不要输出其它内容）
{{
  "title": "试卷标题",
  "questions": [
    {{
      "type": "multiple_choice|judge|fill_blank|short_answer",
      "question": "题干",
      "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
      "answer": "A",
      "reference_answer": "主观题参考答案（客观题留空字符串）",
      "scoring_points": ["评分要点1", "评分要点2"],
      "explanation": "解析",
      "knowledge_point": "知识点",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

注意：
1. 选择题 options 为 4 项，answer 只填字母（A/B/C/D）；判断题 answer 只填 "true" 或 "false"，options 为空数组；填空题 answer 填完整答案；简答题 answer 留空、必须给出 reference_answer 和 scoring_points（3~5 条评分要点）。
2. 题目内容必须准确、无科学性错误，贴合教材依据。
3. 简答题（主观题）要留出足够作答空间，考查理解与表达。"""


def _conn(db_path: str):
    from data import dbapi as dbapi

    c = dbapi.connect(db_path, timeout=10)
    c.row_factory = dbapi.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def _row(cur) -> dict | None:
    r = cur.fetchone()
    return dict(r) if r else None


def _normalize_type(qtype: str) -> str:
    t = (qtype or "").strip().lower()
    mapping = {
        "choice": "multiple_choice",
        "single_choice": "multiple_choice",
        "multiple_choice": "multiple_choice",
        "judge": "judge",
        "true_false": "judge",
        "fill": "fill_blank",
        "fill_blank": "fill_blank",
        "short_answer": "short_answer",
        "subjective": "short_answer",
        "essay": "short_answer",
        "解答题": "short_answer",
        "简答题": "short_answer",
        "选择题": "multiple_choice",
        "判断题": "judge",
        "填空题": "fill_blank",
    }
    return mapping.get(t, "short_answer" if t else "short_answer")


class ExamPaperService:
    """试卷生成与管理"""

    # ==================== 试卷生成 ====================

    def generate_paper(self, params: dict) -> dict:
        """
        AI 组卷。params:
            teacher_id, subject, grade, topic, knowledge_points(list), difficulty,
            paper_type(practice/exam), title, total_score, duration_minutes,
            question_spec{type: count}, use_bank(bool)
        """
        teacher_id = params.get("teacher_id")
        subject = (params.get("subject") or "综合").strip()
        grade = (params.get("grade") or "").strip()
        topic = (params.get("topic") or "").strip()
        kps = [str(k).strip() for k in (params.get("knowledge_points") or []) if str(k).strip()]
        difficulty = (params.get("difficulty") or "medium").strip()
        paper_type = params.get("paper_type") or "practice"
        total_score = float(params.get("total_score") or 100)
        duration = int(params.get("duration_minutes") or 60)
        use_bank = params.get("use_bank", True)

        spec: dict[str, int] = {}
        raw_spec = params.get("question_spec") or DEFAULT_SPEC
        for t, n in raw_spec.items():
            nt = _normalize_type(t)
            try:
                n = int(n)
            except (TypeError, ValueError):
                continue
            if n > 0:
                spec[nt] = spec.get(nt, 0) + n
        if not spec:
            spec = dict(DEFAULT_SPEC)

        difficulty_label = {"easy": "基础（偏易）", "medium": "中等", "hard": "较难（提高）",
                            "mixed": "难易混合"}.get(difficulty, "中等")
        paper_type_label = "考试卷" if paper_type == "exam" else "练习卷"
        spec_desc = "、".join(f"{TYPE_LABELS.get(t, t)}{n}道" for t, n in spec.items())

        # 1. RAG 知识库取材
        rag_context = self._gather_rag_context(subject, topic, kps)

        # 2. 题库复用
        bank_questions: list[dict] = []
        if use_bank:
            bank_questions = self._pick_from_bank(subject, spec, kps)

        # 3. LLM 生成剩余题
        need: dict[str, int] = {}
        got: dict[str, int] = {}
        for q in bank_questions:
            got[q["type"]] = got.get(q["type"], 0) + 1
        for t, n in spec.items():
            remain = n - got.get(t, 0)
            if remain > 0:
                need[t] = remain

        ai_questions: list[dict] = []
        if need:
            ai_questions = self._generate_questions(
                subject=subject, grade=grade, topic=topic, kps=kps,
                difficulty_label=difficulty_label, need=need,
                rag_context=rag_context, paper_type_label=paper_type_label,
            )
        if not ai_questions and not bank_questions:
            return {"success": False, "message": "出题失败，请稍后重试或调整参数"}

        # 4. 组装（按题型分组排序 → 分值分配）
        questions: list[dict] = []
        for t in QUESTION_TYPES:
            qs = [q for q in bank_questions + ai_questions if q.get("type") == t][: spec.get(t, 0)]
            questions.extend(qs)
        questions = self._allocate_scores(questions, total_score)

        source = "mixed" if (bank_questions and ai_questions) else ("bank" if bank_questions else "ai")
        title = (params.get("title") or "").strip() or f"{subject}{topic and '·' + topic or ''}{paper_type_label}"
        paper = {
            "teacher_id": teacher_id,
            "title": title,
            "subject": subject,
            "grade": grade,
            "topic": topic,
            "paper_type": paper_type,
            "total_score": total_score,
            "duration_minutes": duration,
            "difficulty": difficulty,
            "knowledge_points": kps,
            "question_source": source,
            "status": "draft",
            "questions": questions,
        }
        info(f"组卷完成: {title} | {len(questions)}题 | 来源 {source}")
        return {"success": True, "message": f"生成成功（{len(questions)} 题）", "data": paper}

    def _gather_rag_context(self, subject: str, topic: str, kps: list[str]) -> str:
        """从 RAG 知识库检索教材依据，注入命题 prompt"""
        query = " ".join(filter(None, [subject, topic, " ".join(kps)])).strip()
        if not query:
            return "（无特定教材依据，请按通用教学大纲命题）"
        try:
            from services.advanced_retrieval_service import retrieval_service

            docs = retrieval_service.smart_search(None, query, subject=subject, limit=5) or []
        except Exception as e:
            warning(f"RAG 取材失败，按通用大纲命题: {e}")
            docs = []
        if not docs:
            return "（无特定教材依据，请按通用教学大纲命题）"
        parts = []
        for d in docs[:5]:
            text = (d.get("content") or d.get("content_text") or "")[:800]
            title = d.get("title") or "参考资料"
            if text:
                parts.append(f"### {title}\n{text}")
        return "\n\n".join(parts)[:3500] or "（无特定教材依据，请按通用教学大纲命题）"

    def _pick_from_bank(self, subject: str, spec: dict[str, int], kps: list[str]) -> list[dict]:
        """从题库选题（每题型最多 50%，按知识点优先）"""
        try:
            from data.dao import get_quiz_dao

            quiz_dao = get_quiz_dao()
            total_needed = sum(spec.values())
            pool = quiz_dao.get_from_bank(subject=subject, count=max(total_needed * 2, 20)) or []
        except Exception as e:
            warning(f"题库取题失败: {e}")
            return []

        picked: list[dict] = []
        used: set = set()
        got: dict[str, int] = {}
        kp_lower = [k.lower() for k in kps]
        # 知识点命中的优先
        pool.sort(key=lambda q: 0 if any(k in (q.get("knowledge_point") or "").lower() for k in kp_lower) else 1)
        for q in pool:
            qtype = _normalize_type(q.get("type") or q.get("question_type"))
            need_n = spec.get(qtype, 0)
            # 每题型上限 50%（至少 1 道），保证新鲜度
            cap = max(1, need_n // 2) if need_n > 1 else need_n
            if need_n == 0 or got.get(qtype, 0) >= cap:
                continue
            qid = q.get("id")
            if qid in used:
                continue
            used.add(qid)
            got[qtype] = got.get(qtype, 0) + 1
            picked.append({
                "bank_id": qid,
                "type": qtype,
                "question": q.get("question") or q.get("question_text") or "",
                "options": q.get("options") or [],
                "answer": q.get("answer") or q.get("correct_answer") or "",
                "reference_answer": "",
                "scoring_points": [],
                "explanation": q.get("explanation") or "",
                "knowledge_point": q.get("knowledge_point") or "",
                "difficulty": q.get("difficulty") or "medium",
            })
        if used:
            try:
                quiz_dao.mark_bank_used(list(used))
            except Exception as e:
                warning(f"标记题库使用次数失败: {e}")
        info(f"题库复用 {len(picked)} 题")
        return picked

    def _generate_questions(self, *, subject, grade, topic, kps, difficulty_label,
                            need: dict[str, int], rag_context: str, paper_type_label: str) -> list[dict]:
        """LLM 生成题目（含主观题参考答案+评分要点）"""
        from services.spark_client import spark_client

        spec_desc = "、".join(f"{TYPE_LABELS.get(t, t)}{n}道" for t, n in need.items())
        prompt = PAPER_GEN_PROMPT.format(
            subject=subject, grade=grade or "不限", topic=topic or "本学科核心内容",
            knowledge_points="、".join(kps) or "不限",
            difficulty_label=difficulty_label, spec_desc=spec_desc,
            rag_context=rag_context, paper_type_label=paper_type_label,
        )
        for attempt in range(2):
            try:
                raw = spark_client.chat(prompt, max_tokens=6000, temperature=0.7 if attempt == 0 else 0.4)
                data = safe_parse_json(raw) if raw else None
                if not data or not isinstance(data, dict):
                    continue
                questions = data.get("questions") or []
                result = []
                for q in questions:
                    if not isinstance(q, dict):
                        continue
                    qtype = _normalize_type(q.get("type"))
                    text = (q.get("question") or "").strip()
                    if not text:
                        continue
                    options = q.get("options") or []
                    if isinstance(options, str):
                        options = safe_parse_json(options) or []
                    answer = str(q.get("answer") or "").strip()
                    result.append({
                        "type": qtype,
                        "question": text,
                        "options": [str(o) for o in options],
                        "answer": answer,
                        "reference_answer": str(q.get("reference_answer") or "").strip(),
                        "scoring_points": [str(s) for s in (q.get("scoring_points") or []) if str(s).strip()],
                        "explanation": str(q.get("explanation") or "").strip(),
                        "knowledge_point": str(q.get("knowledge_point") or "").strip(),
                        "difficulty": str(q.get("difficulty") or "medium").strip(),
                    })
                if result:
                    info(f"LLM 生成 {len(result)} 题")
                    return result
            except Exception as e:
                error(f"LLM 出题失败(第{attempt + 1}次): {e}")
        warning("LLM 出题失败，使用兜底模板题")
        return self._fallback_questions(need, subject, topic)

    def _fallback_questions(self, need: dict[str, int], subject: str, topic: str) -> list[dict]:
        """出题兜底模板（保证功能可用）"""
        fallback = []
        templates = {
            "multiple_choice": {
                "question": f"关于「{topic or subject}」，下列说法正确的是（  ）",
                "options": ["A. 说法一", "B. 说法二", "C. 说法三", "D. 以上都不对"],
                "answer": "D",
                "explanation": "模板题，请教师编辑修改。",
            },
            "judge": {
                "question": f"「{topic or subject}」的相关结论总是成立。（  ）",
                "options": [], "answer": "false", "explanation": "模板题，请教师编辑修改。",
            },
            "fill_blank": {
                "question": f"「{topic or subject}」的核心概念是______。",
                "options": [], "answer": "核心概念", "explanation": "模板题，请教师编辑修改。",
            },
            "short_answer": {
                "question": f"请简述「{topic or subject}」的主要内容与你的理解。",
                "options": [], "answer": "",
                "reference_answer": "（参考答案待补充）",
                "scoring_points": ["要点一", "要点二", "要点三"],
                "explanation": "模板题，请教师编辑修改。",
            },
        }
        for t, n in need.items():
            tpl = templates.get(t, templates["short_answer"])
            for _ in range(n):
                item = dict(tpl)
                item["type"] = t
                item.setdefault("reference_answer", "")
                item.setdefault("scoring_points", [])
                item.setdefault("knowledge_point", topic or subject)
                item.setdefault("difficulty", "medium")
                fallback.append(item)
        return fallback

    def _allocate_scores(self, questions: list[dict], total_score: float) -> list[dict]:
        """按题型权重折算每题分值，合计等于 total_score"""
        if not questions:
            return questions
        weights = [TYPE_BASE_SCORE.get(q["type"], 3.0) for q in questions]
        w_sum = sum(weights) or 1.0
        allocated = 0.0
        for i, q in enumerate(questions):
            if i == len(questions) - 1:
                score = round(total_score - allocated, 1)
            else:
                score = round(total_score * weights[i] / w_sum, 1)
                allocated += score
            q["score"] = max(score, 0.5)
        return questions

    # ==================== 试卷持久化 ====================

    def save_paper(self, paper: dict) -> dict:
        """保存生成/编辑后的试卷（新建）"""
        try:
            conn = _conn(get_assessments_db_path())
            try:
                cur = conn.execute(
                    """INSERT INTO exam_papers
                       (teacher_id, title, subject, grade, topic, paper_type, total_score,
                        duration_minutes, difficulty, knowledge_points, question_source, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        paper.get("teacher_id"), paper.get("title") or "未命名试卷",
                        paper.get("subject") or "", paper.get("grade") or "",
                        paper.get("topic") or "", paper.get("paper_type") or "practice",
                        float(paper.get("total_score") or 100), int(paper.get("duration_minutes") or 60),
                        paper.get("difficulty") or "medium",
                        json.dumps(paper.get("knowledge_points") or [], ensure_ascii=False),
                        paper.get("question_source") or "ai", paper.get("status") or "draft",
                    ),
                )
                paper_id = cur.lastrowid
                self._replace_questions(conn, paper_id, paper.get("questions") or [])
                conn.commit()
                return {"success": True, "message": "试卷已保存", "paper_id": paper_id}
            finally:
                conn.close()
        except Exception as e:
            error(f"保存试卷失败: {e}")
            return {"success": False, "message": f"保存失败: {e}"}

    def _replace_questions(self, conn, paper_id: int, questions: list[dict]) -> None:
        conn.execute("DELETE FROM exam_questions WHERE paper_id = ?", (paper_id,))
        for idx, q in enumerate(questions):
            conn.execute(
                """INSERT INTO exam_questions
                   (paper_id, q_index, question_type, question_text, options, correct_answer,
                    reference_answer, scoring_points, explanation, knowledge_point, difficulty, score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    paper_id, idx, _normalize_type(q.get("type")),
                    q.get("question") or q.get("question_text") or "",
                    json.dumps(q.get("options") or [], ensure_ascii=False),
                    q.get("answer") or q.get("correct_answer") or "",
                    q.get("reference_answer") or "",
                    json.dumps(q.get("scoring_points") or [], ensure_ascii=False),
                    q.get("explanation") or "", q.get("knowledge_point") or "",
                    q.get("difficulty") or "medium", float(q.get("score") or 0),
                ),
            )

    def list_papers(self, teacher_id: int, subject: str | None = None,
                    paper_type: str | None = None) -> list[dict]:
        try:
            conn = _conn(get_assessments_db_path())
            try:
                sql = "SELECT * FROM exam_papers WHERE teacher_id = ?"
                params: list = [teacher_id]
                if subject:
                    sql += " AND subject = ?"
                    params.append(subject)
                if paper_type:
                    sql += " AND paper_type = ?"
                    params.append(paper_type)
                sql += " ORDER BY created_at DESC"
                papers = _rows(conn.execute(sql, params))
                for p in papers:
                    p["knowledge_points"] = safe_parse_json(p.get("knowledge_points") or "[]") or []
                    cnt = conn.execute(
                        "SELECT COUNT(*) AS c FROM exam_questions WHERE paper_id = ?", (p["id"],)
                    ).fetchone()
                    p["question_count"] = int(cnt["c"]) if cnt else 0
                return papers
            finally:
                conn.close()
        except Exception as e:
            error(f"查询试卷列表失败: {e}")
            return []

    def get_paper(self, paper_id: int, teacher_id: int | None = None) -> dict | None:
        try:
            conn = _conn(get_assessments_db_path())
            try:
                paper = _row(conn.execute("SELECT * FROM exam_papers WHERE id = ?", (paper_id,)))
                if not paper:
                    return None
                if teacher_id is not None and paper["teacher_id"] != teacher_id:
                    return None
                paper["knowledge_points"] = safe_parse_json(paper.get("knowledge_points") or "[]") or []
                questions = _rows(conn.execute(
                    "SELECT * FROM exam_questions WHERE paper_id = ? ORDER BY q_index", (paper_id,)
                ))
                for q in questions:
                    q["options"] = safe_parse_json(q.get("options") or "[]") or []
                    q["scoring_points"] = safe_parse_json(q.get("scoring_points") or "[]") or []
                    q["answer"] = q.pop("correct_answer", "")
                paper["questions"] = questions
                return paper
            finally:
                conn.close()
        except Exception as e:
            error(f"查询试卷失败: {e}")
            return None

    def update_paper(self, paper_id: int, teacher_id: int, fields: dict) -> dict:
        paper = self.get_paper(paper_id, teacher_id)
        if not paper:
            return {"success": False, "message": "试卷不存在或无权限"}
        try:
            conn = _conn(get_assessments_db_path())
            try:
                allowed = {"title", "subject", "grade", "topic", "paper_type", "total_score",
                           "duration_minutes", "difficulty", "status"}
                sets, params = [], []
                for k in allowed:
                    if k in fields and fields[k] is not None:
                        sets.append(f"{k} = ?")
                        params.append(fields[k])
                if "knowledge_points" in fields:
                    sets.append("knowledge_points = ?")
                    params.append(json.dumps(fields.get("knowledge_points") or [], ensure_ascii=False))
                if sets:
                    params.append(paper_id)
                    conn.execute(f"UPDATE exam_papers SET {', '.join(sets)} WHERE id = ?", params)
                if fields.get("questions") is not None:
                    self._replace_questions(conn, paper_id, fields["questions"])
                conn.commit()
                return {"success": True, "message": "已更新"}
            finally:
                conn.close()
        except Exception as e:
            error(f"更新试卷失败: {e}")
            return {"success": False, "message": f"更新失败: {e}"}

    def delete_paper(self, paper_id: int, teacher_id: int) -> dict:
        paper = self.get_paper(paper_id, teacher_id)
        if not paper:
            return {"success": False, "message": "试卷不存在或无权限"}
        try:
            conn = _conn(get_assessments_db_path())
            try:
                conn.execute("DELETE FROM exam_questions WHERE paper_id = ?", (paper_id,))
                conn.execute("DELETE FROM exam_papers WHERE id = ?", (paper_id,))
                conn.commit()
                return {"success": True, "message": "已删除"}
            finally:
                conn.close()
        except Exception as e:
            error(f"删除试卷失败: {e}")
            return {"success": False, "message": f"删除失败: {e}"}

    # ==================== 发布到班级 ====================

    def assign_paper(self, paper_id: int, teacher_id: int, class_id: int,
                     due_at: str | None = None, title: str | None = None,
                     allow_late: bool = True) -> dict:
        paper = self.get_paper(paper_id, teacher_id)
        if not paper:
            return {"success": False, "message": "试卷不存在或无权限"}
        try:
            from services.class_service import class_service

            cls = class_service.get_class(class_id, teacher_id=teacher_id)
            if not cls:
                return {"success": False, "message": "班级不存在或无权限"}
            conn = _conn(get_assessments_db_path())
            try:
                cur = conn.execute(
                    """INSERT INTO exam_assignments
                       (paper_id, class_id, assigned_by, title, due_at, status, allow_late)
                       VALUES (?, ?, ?, ?, ?, 'active', ?)""",
                    (paper_id, class_id, teacher_id, title or paper.get("title") or "",
                     due_at or None, 1 if allow_late else 0),
                )
                assignment_id = cur.lastrowid
                conn.execute("UPDATE exam_papers SET status = 'published' WHERE id = ?", (paper_id,))
                conn.commit()
                return {"success": True, "message": "已发布到班级", "assignment_id": assignment_id}
            finally:
                conn.close()
        except Exception as e:
            error(f"发布试卷失败: {e}")
            return {"success": False, "message": f"发布失败: {e}"}

    def list_assignments(self, teacher_id: int) -> list[dict]:
        try:
            conn = _conn(get_assessments_db_path())
            try:
                rows = _rows(conn.execute(
                    """SELECT a.*, p.title AS paper_title, p.subject, p.total_score,
                              p.paper_type, p.duration_minutes
                       FROM exam_assignments a
                       JOIN exam_papers p ON p.id = a.paper_id
                       WHERE a.assigned_by = ?
                       ORDER BY a.created_at DESC""",
                    (teacher_id,),
                ))
                for r in rows:
                    r["submission_count"] = int(conn.execute(
                        "SELECT COUNT(*) AS c FROM exam_submissions WHERE assignment_id = ?",
                        (r["id"],),
                    ).fetchone()["c"])
                    r["graded_count"] = int(conn.execute(
                        "SELECT COUNT(*) AS c FROM exam_submissions WHERE assignment_id = ? AND status = 'graded'",
                        (r["id"],),
                    ).fetchone()["c"])
                return rows
            finally:
                conn.close()
        except Exception as e:
            error(f"查询发布列表失败: {e}")
            return []

    def get_assignment(self, assignment_id: int, teacher_id: int | None = None) -> dict | None:
        try:
            conn = _conn(get_assessments_db_path())
            try:
                a = _row(conn.execute(
                    """SELECT a.*, p.title AS paper_title, p.subject, p.total_score,
                              p.paper_type, p.duration_minutes, p.grade
                       FROM exam_assignments a
                       JOIN exam_papers p ON p.id = a.paper_id
                       WHERE a.id = ?""",
                    (assignment_id,),
                ))
                if not a:
                    return None
                if teacher_id is not None and a["assigned_by"] != teacher_id:
                    return None
                return a
            finally:
                conn.close()
        except Exception as e:
            error(f"查询发布详情失败: {e}")
            return None

    def close_assignment(self, assignment_id: int, teacher_id: int) -> dict:
        a = self.get_assignment(assignment_id, teacher_id)
        if not a:
            return {"success": False, "message": "发布记录不存在或无权限"}
        try:
            conn = _conn(get_assessments_db_path())
            try:
                conn.execute("UPDATE exam_assignments SET status = 'closed' WHERE id = ?", (assignment_id,))
                conn.commit()
                return {"success": True, "message": "已截止"}
            finally:
                conn.close()
        except Exception as e:
            return {"success": False, "message": f"操作失败: {e}"}


exam_paper_service = ExamPaperService()
