"""单元测试：RAGAS 评估框架（取代旧 NDCG/MRR 检索评测）"""

from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import pytest

from services.ragas_evaluator import DEFAULT_METRICS, RagasEvaluator


def _evaluator() -> RagasEvaluator:
    with patch.object(RagasEvaluator, "_init_db", lambda self: None):
        return RagasEvaluator()


class TestHelpers:
    def test_default_metrics(self):
        assert set(DEFAULT_METRICS) == {
            "faithfulness", "context_precision", "context_recall",
            "answer_relevancy", "factual_correctness",
        }

    def test_extract_contexts(self):
        docs = [
            {"content_text": "二叉树是树形结构"},
            {"content": "每个节点最多两个子节点"},
            {"text": "  前序遍历  "},
            {"title": "仅有标题"},
            {"content_text": ""},
            "纯字符串文档",
        ]
        contexts = RagasEvaluator._extract_contexts(docs)
        assert contexts == [
            "二叉树是树形结构",
            "每个节点最多两个子节点",
            "前序遍历",
            "仅有标题",
            "纯字符串文档",
        ]

    def test_extract_contexts_empty_and_truncate(self):
        assert RagasEvaluator._extract_contexts([]) == []
        assert RagasEvaluator._extract_contexts(None) == []
        assert len(RagasEvaluator._extract_contexts([{"content_text": "x" * 2000}], max_len=100)[0]) == 100

    def test_extract_scores_dict(self):
        scores = RagasEvaluator._extract_scores(
            {"faithfulness": 0.8, "context_recall": 0.6}, ["faithfulness", "context_recall"]
        )
        assert scores["faithfulness"] == 0.8
        assert scores["context_recall"] == 0.6
        assert scores["context_precision"] is None

    def test_extract_scores_rounds_and_bad_values(self):
        scores = RagasEvaluator._extract_scores(
            {"faithfulness": 0.123456789, "context_precision": "bad"},
            ["faithfulness", "context_precision"],
        )
        assert scores["faithfulness"] == 0.1235
        assert scores["context_precision"] is None


class TestRunEvaluation:
    def test_missing_ragas(self):
        ev = _evaluator()
        with patch("services.ragas_evaluator._require_ragas", return_value=False):
            result = ev.run_evaluation(1, retrieval_fn=lambda q: [])
        assert result["success"] is False
        assert "ragas" in result["message"]

    def test_empty_dataset(self):
        ev = _evaluator()
        with (
            patch("services.ragas_evaluator._require_ragas", return_value=True),
            patch.object(ev, "get_dataset_samples", return_value=[]),
        ):
            assert ev.run_evaluation(1, retrieval_fn=lambda q: [])["success"] is False

    def test_invalid_metrics(self):
        ev = _evaluator()
        with (
            patch("services.ragas_evaluator._require_ragas", return_value=True),
            patch.object(ev, "get_dataset_samples", return_value=[{"user_input": "q", "reference": "r"}]),
        ):
            assert ev.run_evaluation(1, retrieval_fn=lambda q: [], metrics=["nope"])["success"] is False

    def test_run_with_mocked_scoring(self):
        ev = _evaluator()
        samples = [{
            "user_input": "什么是二叉树？",
            "reference": "二叉树是每个节点最多两个子节点的树",
            "reference_contexts": ["二叉树定义"],
        }]
        scores = {
            "faithfulness": 0.9, "context_precision": 0.8, "context_recall": 0.7,
            "answer_relevancy": 0.85, "factual_correctness": 0.75,
        }
        with (
            patch("services.ragas_evaluator._require_ragas", return_value=True),
            patch.object(ev, "get_dataset_samples", return_value=samples),
            patch.object(ev, "_score_rows", return_value=scores),
            patch.object(ev, "_save_result") as save,
        ):
            result = ev.run_evaluation(
                dataset_id=1,
                retrieval_fn=lambda q: [{"id": 1, "content_text": "二叉树是树形数据结构"}],
                strategy_name="hybrid",
                generate_fn=lambda q, c: "二叉树是一种树形数据结构",
            )

        assert result["success"] is True
        assert result["framework"] == "ragas"
        assert result["metrics"] == scores
        assert result["faithfulness"] == 0.9  # 展平字段
        assert result["total_samples"] == 1
        save.assert_called_once()

    def test_skips_reference_metrics_without_reference(self):
        ev = _evaluator()
        with (
            patch("services.ragas_evaluator._require_ragas", return_value=True),
            patch.object(ev, "get_dataset_samples", return_value=[{"user_input": "问题", "reference": ""}]),
            patch.object(ev, "_score_rows", return_value={"faithfulness": 1.0}) as score,
            patch.object(ev, "_save_result"),
        ):
            result = ev.run_evaluation(
                1,
                retrieval_fn=lambda q: [{"content_text": "ctx"}],
                generate_fn=lambda q, c: "ans",
            )

        assert result["success"] is True
        assert set(result["skipped_metrics"]) >= {"context_recall", "factual_correctness"}
        used = score.call_args[0][1]
        assert "faithfulness" in used and "context_recall" not in used


class TestSurfaceAndCleanup:
    def test_module_exports(self):
        import services.ragas_evaluator as m
        assert all(hasattr(m, n) for n in ("RagasEvaluator", "ragas_evaluator", "DEFAULT_METRICS"))

    def test_public_methods(self):
        ev = _evaluator()
        for name in (
            "create_dataset", "add_sample", "get_datasets", "get_dataset_samples",
            "run_evaluation", "get_history", "compare_strategies",
        ):
            assert callable(getattr(ev, name))

    def test_old_framework_removed(self):
        assert not Path("services/retrieval_evaluator.py").exists()
        assert find_spec("services.retrieval_evaluator") is None
        # 旧 NDCG/MRR/Recall 计算已删除
        assert not hasattr(RagasEvaluator, "_ndcg_at_k")
        assert not hasattr(RagasEvaluator, "_mrr")
        assert not hasattr(RagasEvaluator, "_recall_at_k")

    def test_default_generate_no_context(self):
        assert "未检索到" in RagasEvaluator._default_generate("问题", [])


@pytest.mark.unit
def test_compare_strategies_sort_fallback():
    ev = _evaluator()
    with patch.object(ev, "_db") as db:
        db.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = []
        result = ev.compare_strategies(1, sort_by="not_a_metric")
    assert result["sort_by"] == "faithfulness"
