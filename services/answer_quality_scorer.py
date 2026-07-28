"""
答案质量快速评分 — 5 维度纯规则评估
零 LLM 调用，毫秒级完成
"""

import re
from dataclasses import dataclass

from core.logger import info

# 不确定性标记
UNCERTAINTY_MARKERS = [
    "可能", "也许", "不确定", "不太清楚", "建议咨询", "仅供参考",
    "我不确定", "我不太了解", "无法确定", "需要进一步", "大概",
]


@dataclass
class QualityScore:
    """质量评分结果"""
    total: float                # 总分 0-1
    dimensions: dict            # 各维度分数
    needs_llm_review: bool      # 是否需要 LLM 复查
    flags: list                 # 危险信号
    suggestion: str             # 改进建议


class AnswerQualityScorer:
    """答案质量快速评分器"""

    WEIGHTS = {
        "completeness": 0.20,
        "structure": 0.15,
        "relevance": 0.30,
        "confidence": 0.15,
        "groundedness": 0.20,
    }

    # 中文停用词
    _STOP = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
             "一", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
             "没有", "看", "好", "自己", "这", "他", "她", "它", "吗", "什么",
             "怎么", "请", "帮", "能", "可以", "给", "把", "被", "让", "对"}

    def score(self, question: str, answer: str, context: str = "") -> QualityScore:
        """快速评分"""
        dimensions = {}

        # 1. 完整性（长度合理性）
        dimensions["completeness"] = self._score_completeness(answer)

        # 2. 结构化程度
        dimensions["structure"] = self._score_structure(answer)

        # 3. 相关性（关键词覆盖）
        dimensions["relevance"] = self._score_relevance(question, answer)

        # 4. 置信度（不确定性标记）
        dimensions["confidence"] = self._score_confidence(answer)

        # 5. 有据性（上下文引用）
        dimensions["groundedness"] = self._score_groundedness(answer, context)

        # 加权总分
        total = sum(dimensions[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        total = round(min(max(total, 0), 1.0), 2)

        # 危险信号
        flags = self._detect_flags(answer)

        # 是否需要 LLM 复查
        needs_review = total < 0.6 or "unclosed_code_block" in flags

        # 改进建议
        suggestion = self._generate_suggestion(dimensions, flags)

        return QualityScore(
            total=total,
            dimensions=dimensions,
            needs_llm_review=needs_review,
            flags=flags,
            suggestion=suggestion,
        )

    def _score_completeness(self, answer: str) -> float:
        """长度合理性评分"""
        length = len(answer)
        if length < 30:
            return 0.15
        elif length < 80:
            return 0.4
        elif length < 200:
            return 0.7
        elif length <= 3000:
            return 1.0
        elif length <= 5000:
            return 0.8
        else:
            return 0.6  # 过长扣分

    def _score_structure(self, answer: str) -> float:
        """结构化程度评分"""
        score = 0.2  # 基础分

        # 编号列表
        if re.search(r'(?:^|\n)\s*(?:\d+[\.\)、]|\-\s|\*\s)', answer, re.MULTILINE):
            score += 0.2
        # 代码块
        if "```" in answer:
            score += 0.2
        # 加粗/标题
        if re.search(r'\*\*[^*]+\*\*|^#{1,3}\s', answer, re.MULTILINE):
            score += 0.15
        # 分段（多个换行）
        if answer.count("\n\n") >= 2:
            score += 0.1
        # 逻辑符号
        if re.search(r'[→⇒∴∵│├└─]', answer):
            score += 0.1

        return min(score, 1.0)

    def _score_relevance(self, question: str, answer: str) -> float:
        """关键词覆盖度"""
        q_words = set(self._tokenize(question)) - self._STOP
        a_words = set(self._tokenize(answer))

        if not q_words:
            return 0.5

        overlap = len(q_words & a_words) / len(q_words)
        return min(overlap * 1.8, 1.0)

    def _score_confidence(self, answer: str) -> float:
        """置信度（不确定性标记检测）"""
        count = sum(1 for marker in UNCERTAINTY_MARKERS if marker in answer)
        return max(0, 1.0 - count * 0.15)

    def _score_groundedness(self, answer: str, context: str) -> float:
        """有据性（上下文关键词引用）"""
        if not context:
            return 0.5

        c_words = set(self._tokenize(context)) - self._STOP
        a_words = set(self._tokenize(answer))

        if not c_words:
            return 0.5

        overlap = len(c_words & a_words) / len(c_words)
        return min(overlap * 2.5, 1.0)

    def _detect_flags(self, answer: str) -> list:
        """检测危险信号"""
        flags = []

        # 道歉式短回答
        if ("抱歉" in answer or "对不起" in answer) and len(answer) < 100:
            flags.append("apologetic_short")

        # 明确不知道
        if re.search(r'我不(知道|确定|清楚|了解)', answer):
            flags.append("uncertain")

        # 未闭合代码块
        if answer.count("```") % 2 != 0:
            flags.append("unclosed_code_block")

        # 重复内容（连续重复句子）
        sentences = [s.strip() for s in answer.split("。") if len(s.strip()) > 10]
        if len(sentences) >= 3:
            for i in range(len(sentences) - 2):
                if sentences[i] == sentences[i + 1] == sentences[i + 2]:
                    flags.append("repetitive")
                    break

        return flags

    def _generate_suggestion(self, dimensions: dict, flags: list) -> str:
        """生成改进建议"""
        suggestions = []

        if dimensions.get("completeness", 1) < 0.4:
            suggestions.append("回答过短，需要补充更多细节")
        if dimensions.get("structure", 1) < 0.4:
            suggestions.append("缺少结构化，建议使用列表或分步骤")
        if dimensions.get("relevance", 1) < 0.4:
            suggestions.append("与问题相关性低，可能跑题")
        if dimensions.get("confidence", 1) < 0.5:
            suggestions.append("包含过多不确定性表述")
        if "unclosed_code_block" in flags:
            suggestions.append("代码块未闭合")

        return "；".join(suggestions) if suggestions else "质量良好"

    def _tokenize(self, text: str) -> list:
        """简单分词"""
        # 中文按字，英文按词
        tokens = []
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                tokens.append(char)
            elif char.isalnum():
                tokens.append(char)
        # 英文词
        for word in re.findall(r'[a-zA-Z]+', text):
            tokens.append(word.lower())
        return tokens


# 全局单例
answer_quality_scorer = AnswerQualityScorer()
