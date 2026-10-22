"""单元测试：BM25 + Softmax 检索模块"""
import math

from data.bm25_softmax import (
    BM25Index,
    BM25SoftmaxRetriever,
    softmax,
    fuse_probabilities,
)


class TestSoftmax:
    def test_basic(self):
        probs = softmax([1.0, 2.0, 3.0])
        assert abs(sum(probs) - 1.0) < 1e-9
        assert probs[2] > probs[1] > probs[0]

    def test_temperature(self):
        sharp = softmax([1.0, 2.0, 3.0], temperature=0.1)
        flat = softmax([1.0, 2.0, 3.0], temperature=10.0)
        # 低温更尖锐：最大值占比更高
        assert max(sharp) > max(flat)

    def test_empty(self):
        assert softmax([]) == []

    def test_stability(self):
        # 大数值不溢出
        probs = softmax([1000.0, 1001.0, 1002.0])
        assert abs(sum(probs) - 1.0) < 1e-9
        assert all(math.isfinite(p) for p in probs)


class TestBM25Index:
    def _sample_index(self):
        idx = BM25Index()
        idx.build([
            {"id": 1, "text": "机器学习入门指南 监督学习 无监督学习"},
            {"id": 2, "text": "深度学习神经网络 反向传播"},
            {"id": 3, "text": "数据库系统 MySQL 索引优化"},
            {"id": 4, "text": "机器学习实战 特征工程 决策树"},
        ])
        return idx

    def test_build(self):
        idx = self._sample_index()
        assert idx.num_docs == 4
        assert idx.vocab_size > 0
        assert idx.avgdl > 0

    def test_search_relevance(self):
        idx = self._sample_index()
        hits = idx.search("机器学习", limit=3)
        assert hits, "应命中相关文档"
        top_ids = [h[0] for h in hits]
        # 含「机器学习」的文档应在前列
        assert 1 in top_ids or 4 in top_ids
        assert 3 not in top_ids[:1]

    def test_search_scores_desc(self):
        idx = self._sample_index()
        hits = idx.search("机器学习 神经网络", limit=10)
        scores = [s for _, s in hits]
        assert scores == sorted(scores, reverse=True)

    def test_search_no_match(self):
        idx = self._sample_index()
        assert idx.search("量子计算 纠缠") == []

    def test_upsert_and_remove(self):
        idx = self._sample_index()
        n0 = idx.num_docs
        idx.upsert(5, "强化学习 Q-learning")
        assert idx.num_docs == n0 + 1
        hits = idx.search("强化学习")
        assert hits and hits[0][0] == 5

        idx.remove(5)
        assert idx.num_docs == n0
        hits2 = idx.search("强化学习")
        assert all(h[0] != 5 for h in hits2)

    def test_idf_rare_term_higher(self):
        idx = BM25Index()
        idx.build([
            {"id": 1, "text": "苹果 苹果 苹果"},
            {"id": 2, "text": "苹果 香蕉"},
            {"id": 3, "text": "香蕉 橘子"},
            {"id": 4, "text": "香蕉 葡萄"},
        ])
        # 「橘子」只在 1 篇出现，IDF 高；「香蕉」在 3 篇
        hits_rare = idx.search("橘子", limit=10)
        hits_common = idx.search("香蕉", limit=10)
        assert hits_rare and hits_common
        assert hits_rare[0][1] > hits_common[0][1]


class TestBM25SoftmaxRetriever:
    def test_retrieve_format(self):
        r = BM25SoftmaxRetriever(temperature=1.0)
        r.build_from_rows([
            {"id": 1, "title": "机器学习入门", "subject": "AI", "text": "监督学习"},
            {"id": 2, "title": "数据库原理", "subject": "CS", "text": "SQL 优化"},
        ])
        results = r.retrieve("机器学习", limit=2)
        assert results
        assert results[0]["id"] == 1
        assert "probability" in results[0]
        assert results[0]["retrieval_method"] == "bm25_softmax"
        # 概率和为 1
        assert abs(sum(x["probability"] for x in results) - 1.0) < 1e-6

    def test_probs_sum_to_one(self):
        r = BM25SoftmaxRetriever()
        r.build_from_rows([
            {"id": i, "title": f"文档{i} 机器学习", "text": "机器学习 深度学习"}
            for i in range(10)
        ])
        results = r.retrieve("机器学习", limit=5)
        assert abs(sum(x["probability"] for x in results) - 1.0) < 1e-6

    def test_not_ready(self):
        r = BM25SoftmaxRetriever()
        assert not r.is_ready
        assert r.retrieve("任何查询") == []


class TestFuseProbabilities:
    def test_fuse(self):
        bm25 = [(1, 5.0), (2, 3.0), (3, 1.0)]
        vector = [(1, 0.9), (3, 0.8), (4, 0.7)]
        fused = fuse_probabilities([bm25, vector], weights=[0.5, 0.5])
        ids = [d for d, _ in fused]
        assert set(ids) == {1, 2, 3, 4}
        # 两路都高分的 doc 1 应排第一
        assert ids[0] == 1
        # 概率和为 1
        assert abs(sum(p for _, p in fused) - 1.0) < 1e-6

    def test_empty(self):
        assert fuse_probabilities([]) == []

    def test_weight_bias(self):
        """提高 BM25 权重后，BM25 高分文档概率上升"""
        bm25 = [(1, 10.0), (2, 1.0)]
        vector = [(1, 0.1), (2, 0.9)]
        f1 = dict(fuse_probabilities([bm25, vector], weights=[0.9, 0.1]))
        f2 = dict(fuse_probabilities([bm25, vector], weights=[0.1, 0.9]))
        assert f1[1] > f2[1]


class TestHybridFusion:
    """BM25 + 向量混合检索融合逻辑"""

    def test_hybrid_superset(self):
        """混合结果应覆盖两路候选的并集"""
        bm25 = [(1, 5.0), (2, 3.0)]
        vector = [(2, 0.8), (3, 0.7)]
        fused = fuse_probabilities([bm25, vector], weights=[0.5, 0.5])
        ids = {d for d, _ in fused}
        assert ids == {1, 2, 3}

    def test_hybrid_agreement_boost(self):
        """两路共同命中的文档应获得更高融合概率"""
        bm25 = [(1, 5.0), (2, 4.0), (3, 1.0)]
        vector = [(1, 0.95), (3, 0.5), (4, 0.4)]
        fused = dict(fuse_probabilities([bm25, vector], weights=[0.5, 0.5]))
        # doc1 两路都靠前 → 概率应高于仅单路命中的 doc4
        assert fused[1] > fused[4]

    def test_probs_normalized(self):
        bm25 = [(1, 2.0), (2, 1.0)]
        vector = [(3, 0.5)]
        fused = fuse_probabilities([bm25, vector], weights=[0.5, 0.5])
        assert abs(sum(p for _, p in fused) - 1.0) < 1e-6
