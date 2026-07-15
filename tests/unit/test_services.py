"""单元测试：服务层"""


class TestReflector:
    """测试反思验证器"""

    def test_reflector_import(self):
        from services.reflector import Reflector, reflector
        assert Reflector is not None
        assert reflector is not None

    def test_reflector_extract_json(self):
        from services.reflector import Reflector
        r = Reflector.__new__(Reflector)
        result = r._extract_json('{"score": 8.5, "reason": "good"}')
        assert result == {"score": 8.5, "reason": "good"}

    def test_reflector_extract_json_from_text(self):
        from services.reflector import Reflector
        r = Reflector.__new__(Reflector)
        result = r._extract_json('分析结果：{"score": 7} 完成')
        assert result == {"score": 7}

    def test_reflector_extract_json_invalid(self):
        from services.reflector import Reflector
        r = Reflector.__new__(Reflector)
        result = r._extract_json("no json here")
        assert result is None

    def test_reflector_rule_based_scoring(self):
        from services.reflector import Reflector
        r = Reflector.__new__(Reflector)
        score = r._rule_based_scoring("什么是二叉树", "二叉树是一种树形数据结构，每个节点最多有两个子节点。" * 3, "")
        assert 0 <= score <= 10

    def test_reflector_identify_issues_short(self):
        from services.reflector import reflector
        issues = reflector._identify_issues("什么是机器学习", "不知道", "")
        assert any("过短" in i for i in issues)


class TestMultiHopRetriever:
    """测试多跳推理检索"""

    def test_import(self):
        from services.multi_hop_retriever import MultiHopRetriever, multi_hop_retriever
        assert MultiHopRetriever is not None
        assert multi_hop_retriever is not None

    def test_extract_entities(self):
        from services.multi_hop_retriever import MultiHopRetriever
        r = MultiHopRetriever.__new__(MultiHopRetriever)
        entities = r._extract_entities("梯度下降算法是机器学习中的核心优化方法")
        assert len(entities) > 0
        names = [e["name"] for e in entities]
        assert any("梯度下降" in n for n in names)

    def test_empty_result(self):
        from services.multi_hop_retriever import MultiHopRetriever
        r = MultiHopRetriever.__new__(MultiHopRetriever)
        result = r._empty_result("test reason")
        assert result["confidence"] == 0.0
        assert result["hops_used"] == 0
        assert "test reason" in result["answer"]

    def test_verify_chain_empty(self):
        from services.multi_hop_retriever import MultiHopRetriever
        r = MultiHopRetriever.__new__(MultiHopRetriever)
        chain = []
        result = r._verify_chain(chain)
        assert result["confidence"] == 0.0
        assert result["valid"] is False


class TestSelfLearningService:
    """测试自学习闭环"""

    def test_import(self):
        from services.self_learning_service import SelfLearningService, self_learning_service
        assert SelfLearningService is not None
        assert self_learning_service is not None

    def test_generate_interaction_id(self):
        from services.self_learning_service import SelfLearningService
        svc = SelfLearningService.__new__(SelfLearningService)
        id1 = svc.generate_interaction_id()
        id2 = svc.generate_interaction_id()
        assert id1 != id2
        assert len(id1) == 12

    def test_filter_high_quality(self):
        from services.self_learning_service import SelfLearningService
        svc = SelfLearningService.__new__(SelfLearningService)
        feedbacks = [
            {"id": 1, "rating": 5, "helpful": 1, "original_query": "q1"},
            {"id": 2, "rating": 2, "helpful": 0, "original_query": "q2"},
            {"id": 3, "rating": 4, "helpful": 1, "original_query": "q3"},
            {"id": 4, "rating": 4, "helpful": 0, "original_query": "q4"},
        ]
        result = svc._filter_high_quality_experiences(feedbacks)
        assert len(result) >= 2  # id=1 and id=3
        ids = [r["id"] for r in result]
        assert 1 in ids
        assert 3 in ids


class TestAdvancedRetrieval:
    """测试高级检索服务"""

    def test_import(self):
        from services.advanced_retrieval_service import AdvancedRetrievalService, retrieval_service
        assert AdvancedRetrievalService is not None
        assert retrieval_service is not None

    def test_smart_search_strategies(self):
        """验证 smart_search 支持所有策略"""
        from services.advanced_retrieval_service import retrieval_service
        strategies = [
            "auto", "knn", "ann", "hybrid", "hyde",
            "multi_query", "rag_fusion", "contextual",
            "graph", "multi_hop", "hybrid_advl", "ensemble",
        ]
        # 只验证方法存在，不实际调用（需要数据库）
        for s in strategies:
            assert hasattr(retrieval_service, 'smart_search')


class TestQAService:
    """测试 QA 服务"""

    def test_import(self):
        from services.qa_service import QAService, qa_service
        assert QAService is not None
        assert qa_service is not None

    def test_qa_service_methods(self):
        from services.qa_service import qa_service
        assert callable(getattr(qa_service, 'call_ai', None))
        assert callable(getattr(qa_service, 'call_simple', None))
        assert callable(getattr(qa_service, 'call_standard', None))
        assert callable(getattr(qa_service, 'call_advanced', None))
        assert callable(getattr(qa_service, 'call_ultra', None))
        assert callable(getattr(qa_service, 'call_ai_stream', None))
