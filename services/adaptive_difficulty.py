"""
自适应难度引擎 — 基于 BKT 掌握概率动态选题
纯规则实现，零 LLM 调用
"""

from dataclasses import dataclass
from core.logger import info


@dataclass
class DifficultyDecision:
    """难度决策"""
    difficulty: str          # easy/medium/hard
    reason: str              # 决策原因
    weak_topics: list        # 薄弱知识点
    distribution: dict       # 题量分配


class AdaptiveDifficultyEngine:
    """自适应难度引擎"""

    # 三区模型
    ZONES = {
        "remedial": {"difficulty": "easy", "ratio": 0.5, "desc": "补救区"},
        "consolidation": {"difficulty": "medium", "ratio": 0.3, "desc": "巩固区"},
        "challenge": {"difficulty": "hard", "ratio": 0.2, "desc": "拓展区"},
    }

    def select_difficulty(self, mastery_prob: float, recent_accuracy: float = 0.5) -> str:
        """选择题目难度"""
        combined = 0.6 * mastery_prob + 0.4 * recent_accuracy

        if combined >= 0.8:
            return "hard"
        elif combined >= 0.5:
            return "medium"
        else:
            return "easy"

    def build_distribution(
        self,
        mastery_data: dict[str, float],
        total_count: int,
    ) -> dict:
        """按掌握度分配题量"""
        # 分组
        weak = [(kp, p) for kp, p in mastery_data.items() if p < 0.5]
        medium = [(kp, p) for kp, p in mastery_data.items() if 0.5 <= p < 0.8]
        strong = [(kp, p) for kp, p in mastery_data.items() if p >= 0.8]

        # 分配题量
        weak_count = max(1, round(total_count * 0.5))
        medium_count = max(1, round(total_count * 0.3))
        hard_count = max(0, total_count - weak_count - medium_count)

        distribution = {
            "easy": {"count": weak_count, "topics": [kp for kp, _ in weak[:3]]},
            "medium": {"count": medium_count, "topics": [kp for kp, _ in medium[:3]]},
            "hard": {"count": hard_count, "topics": [kp for kp, _ in strong[:3]]},
        }

        info(f"题量分配: easy={weak_count}, medium={medium_count}, hard={hard_count}")
        return distribution

    def build_adaptive_prompt(
        self,
        subject: str,
        mastery_data: dict[str, float],
        count: int,
        weak_info: str = "",
    ) -> str:
        """构建自适应出题 prompt"""
        dist = self.build_distribution(mastery_data, count)

        prompt = f"请针对「{subject}」相关知识点生成 {count} 道练习题，按以下分配：\n注意：「{subject}」是学科名或知识点关键词，请围绕其涉及的学科知识出题，不要把题目本身当成知识点来出题。\n每道题必须考察具体的学科知识内容，不要出空洞题目。\n\n"

        easy = dist["easy"]
        if easy["topics"]:
            topics = "、".join(easy["topics"])
            prompt += f"【补救区 {easy['count']} 题】知识点：{topics}，难度：简单，帮助巩固基础\n"

        med = dist["medium"]
        if med["topics"]:
            topics = "、".join(med["topics"])
            prompt += f"【巩固区 {med['count']} 题】知识点：{topics}，难度：中等\n"

        hard = dist["hard"]
        if hard["topics"] and hard["count"] > 0:
            topics = "、".join(hard["topics"])
            prompt += f"【拓展区 {hard['count']} 题】知识点：{topics}，难度：困难，考察深层理解\n"

        if weak_info:
            prompt += f"\n{weak_info}"

        prompt += """
要求：题型包含选择题(type="multiple_choice")、判断题(type="judge")、填空题(type="fill_blank")。
选择题options格式：["A. xxx", "B. xxx", "C. xxx", "D. xxx"]，answer填字母如"A"。
判断题options留空数组，answer填"true"或"false"。
填空题options留空数组，answer填答案文本。

只输出JSON，不要输出其他内容：
{"questions":[{"id":1,"type":"multiple_choice","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"A","explanation":"...","difficulty":"easy","knowledge_point":"..."}]}"""

        return prompt


# 全局单例
adaptive_difficulty = AdaptiveDifficultyEngine()
