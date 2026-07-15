"""自学习闭环：反馈收集 → 经验筛选 → 数据增强 → 知识库增量更新"""

import json
import sqlite3
import uuid

from core.logger import error, info, warning


class SelfLearningService:
    """自学习闭环服务"""

    CONFIDENCE_THRESHOLD = 0.7
    RATING_THRESHOLD = 4
    AUGMENT_BATCH_SIZE = 10

    def __init__(self):
        self._rag_kb = None
        self._embedding_service = None
        self._qa_service = None

    @property
    def rag_kb(self):
        if self._rag_kb is None:
            from data.rag_knowledge_base import rag_kb
            self._rag_kb = rag_kb
        return self._rag_kb

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from data.embedding_service import embedding_service
            self._embedding_service = embedding_service
        return self._embedding_service

    @property
    def qa_service(self):
        if self._qa_service is None:
            from services.qa_service import qa_service
            self._qa_service = qa_service
        return self._qa_service

    def generate_interaction_id(self) -> str:
        return str(uuid.uuid4())[:12]

    def collect_feedback(self, user_id: int, interaction_id: str,
                         feedback: dict) -> bool:
        """
        收集用户反馈

        feedback: {
            "rating": int (1-5),
            "helpful": bool,
            "comment": str,
            "interaction_type": str ("tutor"/"resource"/"assessment"),
            "original_query": str,
            "original_answer": str
        }
        """
        try:
            from data.config import get_memory_db_path
            conn = sqlite3.connect(get_memory_db_path())
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO user_feedback
                (user_id, interaction_id, interaction_type, rating, helpful,
                 comment, original_query, original_answer, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                user_id,
                interaction_id,
                feedback.get("interaction_type", "tutor"),
                feedback.get("rating", 3),
                1 if feedback.get("helpful") else 0,
                feedback.get("comment", ""),
                feedback.get("original_query", ""),
                feedback.get("original_answer", ""),
            ))

            conn.commit()
            conn.close()

            info(f"[SelfLearning] 收集反馈: user={user_id} interaction={interaction_id} "
                 f"rating={feedback.get('rating')} helpful={feedback.get('helpful')}")
            return True

        except Exception as e:
            error(f"[SelfLearning] 收集反馈失败: {e}")
            return False

    def process_feedback_batch(self, batch_size: int = 50) -> dict:
        """
        批量处理反馈：筛选高置信度经验

        Returns:
            {processed, accepted, rejected, augmented}
        """
        stats = {"processed": 0, "accepted": 0, "rejected": 0, "augmented": 0}

        try:
            from data.config import get_memory_db_path
            conn = sqlite3.connect(get_memory_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 获取未处理的反馈
            cursor.execute("""
                SELECT * FROM user_feedback
                WHERE processed = 0
                ORDER BY created_at ASC
                LIMIT ?
            """, (batch_size,))
            feedbacks = [dict(row) for row in cursor.fetchall()]

            if not feedbacks:
                conn.close()
                return stats

            high_quality = self._filter_high_quality_experiences(feedbacks)
            stats["processed"] = len(feedbacks)
            stats["accepted"] = len(high_quality)
            stats["rejected"] = stats["processed"] - stats["accepted"]

            # 对高质量经验进行数据增强
            for exp in high_quality:
                augmented = self._augment_data(exp)
                for aug in augmented:
                    cursor.execute("""
                        INSERT INTO learning_experiences
                        (source_feedback_id, user_id, experience_type, content,
                         confidence, augmented, applied)
                        VALUES (?, ?, ?, ?, ?, 1, 0)
                    """, (
                        exp["id"], exp["user_id"], "qa_pair",
                        json.dumps(aug, ensure_ascii=False),
                        aug.get("confidence", 0.8),
                    ))
                    stats["augmented"] += 1

            # 标记反馈为已处理
            feedback_ids = [f["id"] for f in feedbacks]
            placeholders = ",".join("?" * len(feedback_ids))
            cursor.execute(f"""
                UPDATE user_feedback SET processed = 1
                WHERE id IN ({placeholders})
            """, feedback_ids)

            conn.commit()
            conn.close()

            info(f"[SelfLearning] 批量处理: {stats}")

            # 将经验应用到知识库
            if stats["accepted"] > 0:
                self._apply_experiences_to_rag()

            return stats

        except Exception as e:
            error(f"[SelfLearning] 批量处理失败: {e}")
            return stats

    def _filter_high_quality_experiences(self, feedbacks: list[dict]) -> list[dict]:
        """筛选：评分 >= 4 且 helpful=True 的交互"""
        high_quality = []
        for fb in feedbacks:
            rating = fb.get("rating", 0)
            helpful = fb.get("helpful", 0)

            if (rating >= self.RATING_THRESHOLD and helpful) or (rating >= self.RATING_THRESHOLD and fb.get("original_query")):
                high_quality.append(fb)

        return high_quality

    def _augment_data(self, experience: dict) -> list[dict]:
        """数据增强：基于高质量 QA 对生成变体"""
        augmented = []
        query = experience.get("original_query", "")
        answer = experience.get("original_answer", "")

        if not query or not answer:
            return augmented

        # 原始 QA 对
        augmented.append({
            "query": query,
            "answer": answer,
            "type": "original",
            "confidence": 0.9,
        })

        # 生成变体
        try:
            variants = self._generate_variants(query, answer)
            for v in variants:
                augmented.append({
                    "query": v.get("query", query),
                    "answer": v.get("answer", answer),
                    "type": "augmented",
                    "confidence": 0.75,
                })
        except Exception as e:
            warning(f"[SelfLearning] 数据增强失败: {e}")

        return augmented[:self.AUGMENT_BATCH_SIZE]

    def _generate_variants(self, query: str, answer: str) -> list[dict]:
        """生成 QA 变体"""
        prompt = f"""基于以下问答对，生成2个不同角度的变体，用于训练数据增强。

原始问题：{query}
原始回答：{answer[:500]}

请输出JSON数组：[{{"query": "变体问题", "answer": "变体回答"}}]
只输出JSON，不要其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=500)
            if result:
                import re
                match = re.search(r'\[.*\]', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception:
            pass
        return []

    def _apply_experiences_to_rag(self) -> int:
        """将未应用的经验写入 RAG 知识库"""
        applied_count = 0

        try:
            from data.config import get_memory_db_path
            conn = sqlite3.connect(get_memory_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM learning_experiences
                WHERE applied = 0 AND confidence >= ?
                LIMIT 20
            """, (self.CONFIDENCE_THRESHOLD,))
            experiences = [dict(row) for row in cursor.fetchall()]

            if not experiences:
                conn.close()
                return 0

            for exp in experiences:
                try:
                    content = json.loads(exp["content"]) if isinstance(exp["content"], str) else exp["content"]
                    query = content.get("query", "")
                    answer = content.get("answer", "")

                    if not query or not answer:
                        continue

                    combined = f"问：{query}\n答：{answer}"
                    doc_id = self.rag_kb.add_document(
                        title=f"[自学习] {query[:50]}",
                        subject="自学习经验",
                        content_text=combined,
                        file_type="auto_generated",
                    )

                    if doc_id:
                        cursor.execute("""
                            UPDATE learning_experiences
                            SET applied = 1, rag_doc_id = ?
                            WHERE id = ?
                        """, (doc_id, exp["id"]))
                        applied_count += 1

                except Exception as e:
                    warning(f"[SelfLearning] 应用经验失败: {e}")

            conn.commit()
            conn.close()

            if applied_count > 0:
                info(f"[SelfLearning] 应用 {applied_count} 条经验到 RAG 知识库")

        except Exception as e:
            error(f"[SelfLearning] 应用经验到 RAG 失败: {e}")

        return applied_count

    def get_learning_stats(self, user_id: int | None = None) -> dict:
        """获取自学习统计"""
        try:
            from data.config import get_memory_db_path
            conn = sqlite3.connect(get_memory_db_path())
            cursor = conn.cursor()

            stats = {}

            # 反馈统计
            if user_id:
                cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE user_id=?", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM user_feedback")
            stats["total_feedbacks"] = cursor.fetchone()[0]

            if user_id:
                cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE user_id=? AND processed=0", (user_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE processed=0")
            stats["pending_feedbacks"] = cursor.fetchone()[0]

            # 经验统计
            cursor.execute("SELECT COUNT(*) FROM learning_experiences")
            stats["total_experiences"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM learning_experiences WHERE applied=1")
            stats["applied_experiences"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM learning_experiences WHERE applied=0 AND confidence>=?",
                          (self.CONFIDENCE_THRESHOLD,))
            stats["ready_to_apply"] = cursor.fetchone()[0]

            # 平均评分
            if user_id:
                cursor.execute("SELECT AVG(rating) FROM user_feedback WHERE user_id=? AND rating IS NOT NULL", (user_id,))
            else:
                cursor.execute("SELECT AVG(rating) FROM user_feedback WHERE rating IS NOT NULL")
            avg = cursor.fetchone()[0]
            stats["average_rating"] = round(avg, 2) if avg else 0

            conn.close()
            return stats

        except Exception as e:
            error(f"[SelfLearning] 获取统计失败: {e}")
            return {}

    def trigger_learning_cycle(self) -> dict:
        """手动触发一次完整的学习循环"""
        info("[SelfLearning] 手动触发学习循环")
        result = self.process_feedback_batch()
        result["stats"] = self.get_learning_stats()
        return result


# 全局单例
self_learning_service = SelfLearningService()
