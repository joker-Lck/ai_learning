# -*- coding: utf-8 -*-
"""BM25 / 向量 / 混合检索效果对比评测"""
import sys
sys.path.insert(0, ".")
import math

from data.rag_knowledge_base import rag_kb
from data.embedding_service import embedding_service as es
from data.bm25_softmax import bm25_retriever

EVAL_SET = [
    ("机器学习入门", {1, 8, 9}),
    ("神经网络 深度学习", {1, 8, 9}),
    ("knn 算法 代码", {8, 9}),
    ("时间序列分析 Python", {3, 5, 7}),
    ("计算机体系结构 AI", {4, 6}),
    ("学习安排 计划", {10, 11}),
    ("数据库索引优化", set()),
]

def metrics(ranked_ids, relevant, k=5):
    if not ranked_ids:
        return {"hit@k": 0.0, "precision@k": 0.0, "recall@k": 0.0, "mrr": 0.0, "nDCG@k": 0.0}
    topk = ranked_ids[:k]
    hits = [1 if i in relevant else 0 for i in topk]
    hit = 1.0 if any(hits) else 0.0
    precision = sum(hits) / len(topk)
    recall = (sum(hits) / len(relevant)) if relevant else 0.0
    mrr = 0.0
    for rank, i in enumerate(topk, 1):
        if i in relevant:
            mrr = 1.0 / rank
            break
    dcg = sum(h / math.log2(rank + 1) for rank, h in enumerate(hits, 1))
    ideal = [1] * min(len(relevant), k)
    idcg = sum(h / math.log2(rank + 1) for rank, h in enumerate(ideal, 1))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0
    return {"hit@k": hit, "precision@k": precision, "recall@k": recall, "mrr": mrr, "nDCG@k": ndcg}

def bm25_fn(q, limit=5):
    return rag_kb.search_documents_by_bm25(q, limit=limit)

def vector_fn(q, limit=5):
    emb = es.get_embedding(q)
    return rag_kb.search_documents_by_vector(emb, limit=limit)

def hybrid_fn(q, limit=5):
    emb = es.get_embedding(q)
    return rag_kb.search_hybrid_bm25_vector(q, query_embedding=emb, limit=limit)

METHODS = [("BM25", bm25_fn), ("Vector", vector_fn), ("Hybrid", hybrid_fn)]

print("预热索引（使用全局 embedding_service 单例）...")
rag_kb._build_bm25_index(bm25_retriever)
es.get_embedding("预热查询")
rag_kb._build_vector_index()
print(f"  embedding dim = {es._dim}")
print(f"  vector index  = {__import__('data.rag_knowledge_base', fromlist=['x']).vector_index.index_info}")

print("\n" + "=" * 84)
print(f"{'查询':<22} {'方法':<8} {'Hit@5':<7} {'P@5':<7} {'R@5':<7} {'MRR':<7} {'nDCG@5':<7} {'Top结果'}")
print("=" * 84)

agg = {name: {k: [] for k in ("hit@k", "precision@k", "recall@k", "mrr", "nDCG@k")} for name, _ in METHODS}

for query, relevant in EVAL_SET:
    for name, fn in METHODS:
        try:
            raw = fn(query, limit=5)
            ids = [r["id"] for r in raw]
        except Exception as e:
            ids = []
            print(f"  [{name}] error: {e}")
        m = metrics(ids, relevant, k=5)
        for k, v in m.items():
            agg[name][k].append(v)
        top = ",".join(str(i) for i in ids[:3]) or "-"
        rel_mark = "✓" if any(i in relevant for i in ids) else ("—" if not relevant else "✗")
        print(f"{query:<22} {name:<8} {m['hit@k']:<7.1f} {m['precision@k']:<7.2f} {m['recall@k']:<7.2f} {m['mrr']:<7.2f} {m['nDCG@k']:<7.2f} {top} {rel_mark}")
    print("-" * 84)

print("\n" + "=" * 84)
print("汇总（7 条查询平均）")
print("=" * 84)
print(f"{'方法':<10} {'Hit@5':<8} {'P@5':<8} {'R@5':<8} {'MRR':<8} {'nDCG@5':<8}")
print("-" * 84)
for name, _ in METHODS:
    n = len(EVAL_SET)
    row = {k: sum(v) / n for k, v in agg[name].items()}
    print(f"{name:<10} {row['hit@k']:<8.3f} {row['precision@k']:<8.3f} {row['recall@k']:<8.3f} {row['mrr']:<8.3f} {row['nDCG@k']:<8.3f}")

print("\n融合权重对比（query='机器学习入门'）")
for w in ([0.3, 0.7], [0.5, 0.5], [0.7, 0.3]):
    emb = es.get_embedding("机器学习入门")
    rs = rag_kb.search_hybrid_bm25_vector("机器学习入门", query_embedding=emb, limit=5, weights=w)
    print(f"  w_bm25={w[0]}, w_vec={w[1]}:  "
          + "  ".join(f"id={r['id']}({r['probability']:.3f})" for r in rs[:4]))
