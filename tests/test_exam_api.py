"""
AI 出题 / 组卷 + 主观题批改 — 单元测试
覆盖：试卷表存在、分值分配、客观题判分、兜底主观题评分、试卷 DOCX 导出、手写 OCR 服务
"""

import io

import pytest


# ==================== 数据层 ====================

class TestExamTables:

    def test_exam_tables_exist(self):
        from data import dbapi as dbapi
        from data.config import get_assessments_db_path
        conn = dbapi.connect(get_assessments_db_path())
        db_name = get_assessments_db_path()
        expected = [
            "exam_papers", "exam_questions", "exam_assignments",
            "exam_submissions", "exam_answers", "question_bank",
        ]
        rows = conn.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = ? AND TABLE_NAME IN ({})".format(
                ",".join(["?"] * len(expected))
            ),
            [db_name] + expected,
        ).fetchall()
        conn.close()
        found = {r[0] for r in rows}
        assert set(expected) <= found, f"缺少表: {set(expected) - found}"


# ==================== 组卷服务 ====================

class TestExamPaperService:

    def test_normalize_type(self):
        from services.exam_paper_service import _normalize_type
        assert _normalize_type("choice") == "multiple_choice"
        assert _normalize_type("选择题") == "multiple_choice"
        assert _normalize_type("judge") == "judge"
        assert _normalize_type("fill") == "fill_blank"
        assert _normalize_type("subjective") == "short_answer"
        assert _normalize_type("解答题") == "short_answer"

    def test_allocate_scores_sum_to_total(self):
        from services.exam_paper_service import exam_paper_service
        questions = [
            {"type": "multiple_choice", "question": "q1"},
            {"type": "multiple_choice", "question": "q2"},
            {"type": "judge", "question": "q3"},
            {"type": "short_answer", "question": "q4"},
        ]
        result = exam_paper_service._allocate_scores(questions, 100.0)
        total = sum(q["score"] for q in result)
        assert abs(total - 100.0) < 0.01
        assert all(q["score"] > 0 for q in result)

    def test_fallback_questions(self):
        from services.exam_paper_service import exam_paper_service
        qs = exam_paper_service._fallback_questions(
            {"multiple_choice": 1, "judge": 1, "fill_blank": 1, "short_answer": 1},
            "数学", "函数",
        )
        assert len(qs) == 4
        types = {q["type"] for q in qs}
        assert types == {"multiple_choice", "judge", "fill_blank", "short_answer"}
        short = [q for q in qs if q["type"] == "short_answer"][0]
        assert short["scoring_points"], "主观题必须带评分要点"

    def test_generate_paper_fallback_without_llm(self, monkeypatch):
        """LLM 不可用时组卷仍成功（走兜底模板题）"""
        from services import exam_paper_service as eps
        from services.spark_client import spark_client

        def _fail_chat(*args, **kwargs):
            raise RuntimeError("LLM unavailable")

        monkeypatch.setattr(spark_client, "chat", _fail_chat)
        result = eps.exam_paper_service.generate_paper({
            "teacher_id": 999, "subject": "测试学科", "topic": "测试主题",
            "question_spec": {"multiple_choice": 1, "short_answer": 1},
            "use_bank": False, "total_score": 50,
        })
        assert result["success"]
        assert len(result["data"]["questions"]) == 2
        assert abs(sum(q["score"] for q in result["data"]["questions"]) - 50) < 0.01


# ==================== 批改服务 ====================

class TestGradingService:

    def test_grade_objective_choice(self):
        from services.grading_service import grading_service
        ans = {"question_type": "multiple_choice", "answer_text": "A",
               "correct_answer": "A", "max_score": 3.0}
        res = grading_service._grade_objective(ans, 3.0)
        assert res["score"] == 3.0 and res["is_correct"]
        ans["answer_text"] = "B"
        res = grading_service._grade_objective(ans, 3.0)
        assert res["score"] == 0.0 and not res["is_correct"]

    def test_grade_objective_judge(self):
        from services.grading_service import grading_service
        for user, correct, ok in [("对", "true", True), ("错", "true", False),
                                  ("false", "false", True), ("×", "true", False)]:
            ans = {"question_type": "judge", "answer_text": user,
                   "correct_answer": correct, "max_score": 2.0}
            res = grading_service._grade_objective(ans, 2.0)
            assert res["is_correct"] is ok, f"{user} vs {correct}"

    def test_grade_objective_fill(self):
        from services.grading_service import grading_service
        ans = {"question_type": "fill_blank", "answer_text": "光合作用",
               "correct_answer": "光合作用", "max_score": 4.0}
        assert grading_service._grade_objective(ans, 4.0)["score"] == 4.0
        ans["answer_text"] = "呼吸作用"
        assert grading_service._grade_objective(ans, 4.0)["score"] == 0.0

    def test_fallback_grade_by_points(self):
        from services.grading_service import grading_service
        res = grading_service._fallback_grade(
            "函数是一种映射关系，定义域和值域",
            ["映射关系", "单调性"], 10.0,
        )
        assert 0 < res["score"] < 10.0  # 命中 1/2 要点

    def test_fallback_grade_empty(self):
        from services.grading_service import grading_service
        res = grading_service._fallback_grade("", ["要点一"], 10.0)
        assert res["score"] == 0.0


# ==================== DOCX 导出 ====================

class TestExamDocx:

    def test_export_roundtrip(self, tmp_path, monkeypatch):
        from services import exam_docx_service as eds
        monkeypatch.setattr(eds, "EXPORT_DIR", tmp_path)
        paper = {
            "title": "单元测试卷", "subject": "数学", "grade": "高一",
            "total_score": 30, "duration_minutes": 40,
            "questions": [
                {"type": "multiple_choice", "question": "1+1=?", "options": ["A. 1", "B. 2"],
                 "answer": "B", "explanation": "加法", "score": 10},
                {"type": "judge", "question": "1>0", "answer": "true", "score": 10},
                {"type": "short_answer", "question": "简述函数", "reference_answer": "略",
                 "scoring_points": ["要点1", "要点2"], "score": 10},
            ],
        }
        result = eds.exam_docx_service.export(paper, with_answers=True)
        assert result["success"], result
        saved = tmp_path / result["filename"]
        assert saved.exists() and saved.stat().st_size > 1000


# ==================== 手写 OCR 服务 ====================

class TestHandwritingOCR:

    def _fake_image(self) -> bytes:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (500, 140), "white")
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 36)
        except Exception:
            font = ImageFont.load_default()
        d.text((20, 45), "手写识别测试OK", fill="black", font=font)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_recognize_returns_text(self):
        from services.handwriting_ocr_service import handwriting_ocr
        result = handwriting_ocr.recognize(self._fake_image(), use_vision_fallback=False)
        assert result["success"]
        assert result["engine"] == "rapidocr"
        assert "手写" in result["text"] or "识别" in result["text"]
        assert 0 < result["confidence"] <= 1

    def test_empty_image_fails(self):
        from services.handwriting_ocr_service import handwriting_ocr
        result = handwriting_ocr.recognize(b"", use_vision_fallback=False)
        assert not result["success"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
