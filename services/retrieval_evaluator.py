"""
检索评测模块 — NDCG@k / MRR / Recall@k
用于量化评估检索策略质量，支持 A/B 对比。
"""

import json
import os
import sqlite3
import time
from datetime import datetime

import numpy as np

from core.logger import error, info, warning


class RetrievalEvaluator:
    """检索质量评测器"""

    def __init__(self):
        self._db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'retrieval_eval.db'
        )
        self._init_db()

    def _init_db(self):
        """初始化评测数据库"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    relevant_doc_ids TEXT NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES eval_datasets(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS eval_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    strategy TEXT NOT NULL,
                    ndcg_at_k REAL,
                    mrr REAL,
                    recall_at_k REAL,
                    k INTEGER DEFAULT 5,
                    total_queries INTEGER,
                    run_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (dataset_id) REFERENCES eval_datasets(id)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            error(f"初始化评测数据库失败: {e}")

    def create_dataset(self, name: str, description: str = "") -> dict:
        """创建评测数据集"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO eval_datasets (name, description) VALUES (?, ?)",
                (name, description)
            )
            conn.commit()
            dataset_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()
            return {"success": True, "dataset_id": dataset_id}
        except sqlite3.IntegrityError:
            return {"success": False, "message": f"数据集 '{name}' 已存在"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def add_query(self, dataset_id: int, query: str, relevant_doc_ids: list) -> dict:
        """向数据集添加评测查询（带标注的相关文档ID列表）"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO eval_queries (dataset_id, query, relevant_doc_ids) VALUES (?, ?, ?)",
                (dataset_id, query, json.dumps(relevant_doc_ids, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_datasets(self) -> list:
        """获取所有评测数据集"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT d.*, COUNT(q.id) as query_count "
                "FROM eval_datasets d LEFT JOIN eval_queries q ON d.id = q.dataset_id "
                "GROUP BY d.id ORDER BY d.created_at DESC"
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            error(f"获取数据集失败: {e}")
            return []

    def get_dataset_queries(self, dataset_id: int) -> list:
        """获取数据集的所有评测查询"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM eval_queries WHERE dataset_id = ?", (dataset_id,)
            ).fetchall()
            conn.close()
            result = []
            for r in rows:
                d = dict(r)
                d['relevant_doc_ids'] = json.loads(d['relevant_doc_ids'])
                result.append(d)
            return result
        except Exception as e:
            error(f"获取评测查询失败: {e}")
            return []

    def run_evaluation(self, dataset_id: int, retrieval_fn, strategy_name: str,
                       k: int = 5) -> dict:
        """
        运行评测：对数据集中的每个查询调用检索函数，计算指标。

        参数:
            dataset_id: 评测数据集ID
            retrieval_fn: 检索函数，签名 fn(query: str) -> list[dict]
                          返回结果需包含 'id' 字段
            strategy_name: 策略名称（用于记录）
            k: NDCG 和 Recall 的截断值

        返回:
            {"ndcg_at_k": float, "mrr": float, "recall_at_k": float, ...}
        """
        queries = self.get_dataset_queries(dataset_id)
        if not queries:
            return {"success": False, "message": "数据集中无评测查询"}

        ndcg_scores = []
        mrr_scores = []
        recall_scores = []

        for q_data in queries:
            query = q_data['query']
            relevant = set(q_data['relevant_doc_ids'])

            try:
                results = retrieval_fn(query)
                result_ids = [r.get('id') for r in results[:k] if r.get('id') is not None]
            except Exception as e:
                warning(f"评测查询失败: {query[:30]}... error={e}")
                continue

            if not result_ids:
                ndcg_scores.append(0.0)
                mrr_scores.append(0.0)
                recall_scores.append(0.0)
                continue

            # NDCG@k
            ndcg_scores.append(self._ndcg_at_k(result_ids, relevant, k))

            # MRR (第一个相关结果的倒数排名)
            mrr_scores.append(self._mrr(result_ids, relevant))

            # Recall@k
            recall_scores.append(self._recall_at_k(result_ids, relevant, k))

        if not ndcg_scores:
            return {"success": False, "message": "所有评测查询均失败"}

        result = {
            "success": True,
            "strategy": strategy_name,
            "k": k,
            "total_queries": len(ndcg_scores),
            "ndcg_at_k": round(np.mean(ndcg_scores), 4),
            "mrr": round(np.mean(mrr_scores), 4),
            "recall_at_k": round(np.mean(recall_scores), 4),
            "ndcg_std": round(float(np.std(ndcg_scores)), 4),
            "mrr_std": round(float(np.std(mrr_scores)), 4),
            "recall_std": round(float(np.std(recall_scores)), 4),
        }

        # 保存结果
        self._save_result(dataset_id, result)
        info(f"[Eval] {strategy_name} NDCG@{k}={result['ndcg_at_k']:.4f} "
             f"MRR={result['mrr']:.4f} Recall@{k}={result['recall_at_k']:.4f}")

        return result

    def get_history(self, dataset_id: int | None = None, limit: int = 20) -> list:
        """获取评测历史"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            if dataset_id:
                rows = conn.execute(
                    "SELECT * FROM eval_results WHERE dataset_id = ? ORDER BY run_at DESC LIMIT ?",
                    (dataset_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM eval_results ORDER BY run_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            error(f"获取评测历史失败: {e}")
            return []

    def compare_strategies(self, dataset_id: int, k: int = 5) -> dict:
        """对比同一数据集上不同策略的评测结果"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM eval_results WHERE dataset_id = ? AND k = ? ORDER BY ndcg_at_k DESC",
                (dataset_id, k)
            ).fetchall()
            conn.close()
            return {
                "success": True,
                "strategies": [dict(r) for r in rows]
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── 指标计算 ──────────────────────────────

    @staticmethod
    def _dcg_at_k(retrieved_ids: list, relevant: set, k: int) -> float:
        """DCG@k = Σ rel_i / log2(i+1)"""
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k]):
            rel = 1.0 if doc_id in relevant else 0.0
            dcg += rel / np.log2(i + 2)  # i+2 因为 log2(1)=0
        return dcg

    @staticmethod
    def _ndcg_at_k(retrieved_ids: list, relevant: set, k: int) -> float:
        """NDCG@k = DCG@k / IDCG@k"""
        dcg = RetrievalEvaluator._dcg_at_k(retrieved_ids, relevant, k)
        # IDCG: 理想排序（所有相关文档排在前面）
        ideal_ids = list(relevant)[:k]
        idcg = RetrievalEvaluator._dcg_at_k(ideal_ids, relevant, k)
        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def _mrr(retrieved_ids: list, relevant: set) -> float:
        """MRR = 1/rank of first relevant result"""
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in relevant:
                return 1.0 / (i + 1)
        return 0.0

    @staticmethod
    def _recall_at_k(retrieved_ids: list, relevant: set, k: int) -> float:
        """Recall@k = |retrieved ∩ relevant| / |relevant|"""
        if not relevant:
            return 0.0
        retrieved_set = set(retrieved_ids[:k])
        return len(retrieved_set & relevant) / len(relevant)

    # ── 内部方法 ──────────────────────────────

    def _save_result(self, dataset_id: int, result: dict):
        """保存评测结果"""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT INTO eval_results
                   (dataset_id, strategy, ndcg_at_k, mrr, recall_at_k, k, total_queries, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (dataset_id, result['strategy'], result['ndcg_at_k'],
                 result['mrr'], result['recall_at_k'], result['k'],
                 result['total_queries'], json.dumps(result, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            error(f"保存评测结果失败: {e}")


# 全局单例
retrieval_evaluator = RetrievalEvaluator()
