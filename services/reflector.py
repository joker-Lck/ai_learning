"""反思验证器：答案质量评分 + 证据链检查 + 低分触发二次检索"""

import json
import re

from core.logger import error, info, warning


class Reflector:
    """反思验证器：对 AI 生成的答案进行质量评估和验证"""

    QUALITY_THRESHOLD = 6.0      # 质量评分阈值（0-10）
    EVIDENCE_THRESHOLD = 0.5     # 证据链完整性阈值（0-1）
    MAX_RETRIES = 2              # 最大重试次数

    def __init__(self):
        self._qa_service = None
        self._anti_hallucination = None
        self._retrieval_service = None

    @property
    def qa_service(self):
        if self._qa_service is None:
            from services.qa_service import qa_service
            self._qa_service = qa_service
        return self._qa_service

    @property
    def anti_hallucination(self):
        if self._anti_hallucination is None:
            from services.content_safety_service import anti_hallucination_service
            self._anti_hallucination = anti_hallucination_service
        return self._anti_hallucination

    @property
    def retrieval_service(self):
        if self._retrieval_service is None:
            from services.advanced_retrieval_service import retrieval_service
            self._retrieval_service = retrieval_service
        return self._retrieval_service

    def reflect(self, query: str, answer: str, context: str, user_id: int = 0) -> dict:
        """
        主入口：对答案进行反思评估

        Args:
            query: 用户原始问题
            answer: AI 生成的答案
            context: 检索到的上下文
            user_id: 用户 ID

        Returns:
            {
                "quality_score": float,      # 0-10 质量评分
                "evidence_score": float,     # 0-1 证据链完整性
                "issues": List[str],         # 发现的问题
                "should_regenerate": bool,   # 是否需要重新生成
                "improved_query": str,       # 改进后的查询
                "suggestions": List[str]     # 改进建议
            }
        """
        try:
            quality_score = self._score_answer_quality(query, answer, context)
            evidence_result = self._check_evidence_chain(answer, context)
            issues = self._identify_issues(query, answer, context)

            should_regenerate = (
                quality_score < self.QUALITY_THRESHOLD
                or evidence_result["score"] < self.EVIDENCE_THRESHOLD
            )

            improved_query = ""
            suggestions = []
            if should_regenerate:
                improved_query = self._generate_improved_query(query, issues)
                suggestions = self._generate_suggestions(issues)

            result = {
                "quality_score": round(quality_score, 2),
                "evidence_score": round(evidence_result["score"], 3),
                "evidence_details": evidence_result.get("details", []),
                "issues": issues,
                "should_regenerate": should_regenerate,
                "improved_query": improved_query,
                "suggestions": suggestions,
            }

            info(f"[Reflector] 质量={quality_score:.1f} 证据={evidence_result['score']:.3f} "
                 f"重生成={should_regenerate} 问题数={len(issues)}")

            return result

        except Exception as e:
            error(f"[Reflector] 反思评估失败: {e}")
            return {
                "quality_score": 7.0,
                "evidence_score": 0.6,
                "issues": [],
                "should_regenerate": False,
                "improved_query": "",
                "suggestions": [],
            }

    def reflect_and_improve(self, query: str, answer: str, context: str,
                            user_id: int = 0, retry_count: int = 0) -> dict:
        """
        反思并改进：评估 → 低分时二次检索 → 重新生成

        Returns:
            {
                "final_answer": str,
                "reflection": Dict,
                "retries": int,
                "improved": bool
            }
        """
        reflection = self.reflect(query, answer, context, user_id)

        if not reflection["should_regenerate"] or retry_count >= self.MAX_RETRIES:
            return {
                "final_answer": answer,
                "reflection": reflection,
                "retries": retry_count,
                "improved": False,
            }

        # 二次检索：使用改进查询 + ensemble 策略获取更全面上下文
        improved_query = reflection["improved_query"] or query
        try:
            new_docs = self.retrieval_service.smart_search(
                user_id=user_id,
                query=improved_query,
                limit=8,
                strategy="ensemble"
            )
            new_context = "\n".join(d.get("content", "") for d in new_docs if d.get("content"))

            if new_context and len(new_context) > 100:
                context = context + "\n\n[补充检索结果]\n" + new_context
        except Exception as e:
            warning(f"[Reflector] 二次检索失败: {e}")

        # 重新生成
        improved_answer = self._regenerate_with_feedback(
            query, reflection["suggestions"], context
        )

        if improved_answer and not improved_answer.startswith("错误"):
            # 递归评估改进后的答案
            return self.reflect_and_improve(
                query, improved_answer, context, user_id, retry_count + 1
            )

        return {
            "final_answer": answer,
            "reflection": reflection,
            "retries": retry_count,
            "improved": False,
        }

    def _score_answer_quality(self, query: str, answer: str, context: str) -> float:
        """答案质量评分（0-10）"""
        prompt = f"""请对以下AI回答进行质量评分（0-10分）。

【用户问题】
{query}

【AI回答】
{answer[:2000]}

【参考上下文】
{context[:1500] if context else "无"}

评分维度：
1. 准确性（0-2.5）：回答是否与参考上下文一致，无明显错误
2. 完整性（0-2.5）：是否完整回答了用户问题，无遗漏关键点
3. 相关性（0-2.5）：是否紧扣问题主题，无无关内容
4. 逻辑性（0-2.5）：论述是否条理清晰，逻辑连贯

请只输出一个JSON对象：{{"score": 数字, "reason": "简要理由"}}
不要输出其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=200)
            parsed = self._extract_json(result)
            if parsed and "score" in parsed:
                score = float(parsed["score"])
                return max(0, min(10, score))
        except Exception as e:
            warning(f"[Reflector] 质量评分失败: {e}")

        # 降级：基于简单规则评分
        return self._rule_based_scoring(query, answer, context)

    def _rule_based_scoring(self, query: str, answer: str, context: str) -> float:
        """规则降级评分"""
        score = 5.0

        # 长度合理性
        if 50 < len(answer) < 5000:
            score += 1.0
        elif len(answer) < 20:
            score -= 2.0

        # 是否包含"不知道""无法""抱歉"等低质量标记
        low_quality_markers = ["不知道", "无法回答", "抱歉", "没有相关信息", "错误"]
        for marker in low_quality_markers:
            if marker in answer:
                score -= 0.5

        # 上下文相关性（简单关键词匹配）
        if context:
            query_chars = set(query.replace("?", "").replace("？", ""))
            context_chars = set(context[:500])
            overlap = len(query_chars & context_chars) / max(len(query_chars), 1)
            score += overlap * 2

        return max(0, min(10, score))

    def _check_evidence_chain(self, answer: str, context: str) -> dict:
        """证据链完整性检查"""
        if not context or len(context) < 50:
            return {"score": 0.3, "details": ["缺少参考上下文"]}

        try:
            verification = self.anti_hallucination.verify_with_rag(
                claim=answer[:1500],
                knowledge_context=context[:2000],
                threshold=0.5
            )
            confidence = verification.get("confidence", 0.5)
            return {
                "score": confidence,
                "details": verification.get("evidence", []),
            }
        except Exception as e:
            warning(f"[Reflector] 证据链检查失败: {e}")
            return {"score": 0.5, "details": [str(e)]}

    def _identify_issues(self, query: str, answer: str, context: str) -> list[str]:
        """识别答案中的具体问题"""
        issues = []

        # 检测不确定性表述
        uncertainty = self.anti_hallucination.detect_uncertainty_markers(answer)
        if len(uncertainty) > 3:
            issues.append(f"答案包含过多不确定性表述({len(uncertainty)}处)")

        # 答案过短
        if len(answer) < 50:
            issues.append("答案过短，可能不完整")

        # 答案与问题不相关
        query_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', query))
        answer_text = answer[:500]
        matched = sum(1 for kw in query_keywords if kw in answer_text)
        if query_keywords and matched / len(query_keywords) < 0.3:
            issues.append("答案与问题相关性较低")

        return issues

    def _generate_improved_query(self, query: str, issues: list[str]) -> str:
        """基于问题生成改进查询"""
        if not issues:
            return query

        prompt = f"""用户问题是：{query}

当前回答存在以下问题：
{chr(10).join('- ' + i for i in issues)}

请生成一个改进的检索查询，帮助找到更准确的信息。只输出查询文本，不要其他内容。"""

        try:
            result = self.qa_service.call_simple(prompt, max_tokens=200)
            if result and len(result) > 5 and not result.startswith("错误"):
                return result.strip()
        except Exception:
            pass

        return query + " " + " ".join(issues[:2])

    def _generate_suggestions(self, issues: list[str]) -> list[str]:
        """基于问题生成改进建议"""
        suggestions = []
        for issue in issues:
            if "不确定性" in issue:
                suggestions.append("建议提供更多确定性信息，减少模糊表述")
            elif "过短" in issue:
                suggestions.append("建议补充更详细的解释和示例")
            elif "相关性" in issue:
                suggestions.append("建议更准确地理解用户问题，聚焦核心要点")
        return suggestions

    def _regenerate_with_feedback(self, query: str, suggestions: list[str],
                                  context: str) -> str | None:
        """带反馈的二次生成"""
        feedback_text = "\n".join(f"- {s}" for s in suggestions) if suggestions else "请提供更准确、完整的回答。"

        prompt = f"""请重新回答以下问题。请注意改进要求。

【用户问题】
{query}

【改进要求】
{feedback_text}

【参考信息】
{context[:3000]}

请提供准确、完整、有条理的回答。"""

        try:
            result = self.qa_service.call_standard(prompt, max_tokens=3000)
            return result if result and not result.startswith("错误") else None
        except Exception as e:
            error(f"[Reflector] 二次生成失败: {e}")
            return None

    def _extract_json(self, text: str) -> dict | None:
        """从文本中提取 JSON 对象"""
        if not text:
            return None
        try:
            match = re.search(r'\{[^{}]*\}', text)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, Exception):
            pass
        return None


# 全局单例
reflector = Reflector()
