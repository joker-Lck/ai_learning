"""
贝叶斯知识追踪 (BKT) — 追踪每个知识点的掌握概率
经典 BKT 算法，纯数学实现

参数:
- p_L0: 初始掌握概率 (prior)
- p_T:  学习转移概率 (学会的概率)
- p_S:  失误概率 (会但答错)
- p_G:  猜对概率 (不会但答对)

公式:
- P(L|correct) = P(L)*(1-P_S) / [P(L)*(1-P_S) + (1-P(L))*P_G]
- P(L|wrong)   = P(L)*P_S / [P(L)*P_S + (1-P(L))*(1-P_G)]
- P(L_new)     = P(L|obs) + (1 - P(L|obs)) * P_T
"""

from dataclasses import dataclass, field
from core.logger import info


@dataclass
class BKTParams:
    """BKT 参数"""
    p_L0: float = 0.3    # 初始掌握概率
    p_T: float = 0.1     # 学习转移概率
    p_S: float = 0.1     # 失误概率
    p_G: float = 0.25    # 猜对概率


@dataclass
class KnowledgeState:
    """知识点掌握状态"""
    knowledge_point: str
    mastery: float        # 当前掌握概率
    attempts: int         # 尝试次数
    correct: int          # 正确次数
    last_update: str = ""


class BayesianKnowledgeTracer:
    """贝叶斯知识追踪器"""

    # 题型对应的猜对概率
    TYPE_GUESS = {
        "multiple_choice": 0.33,  # 四选一
        "judge": 0.50,            # 判断题
        "fill_blank": 0.10,       # 填空题
    }

    def __init__(self, params: BKTParams | None = None):
        self.params = params or BKTParams()
        self.states: dict[str, KnowledgeState] = {}

    def get_mastery(self, knowledge_point: str) -> float:
        """获取某知识点的当前掌握概率"""
        if knowledge_point in self.states:
            return self.states[knowledge_point].mastery
        return self.params.p_L0

    def update(self, knowledge_point: str, is_correct: bool, question_type: str = "fill_blank"):
        """根据答题结果更新掌握概率"""
        if knowledge_point not in self.states:
            self.states[knowledge_point] = KnowledgeState(
                knowledge_point=knowledge_point,
                mastery=self.params.p_L0,
                attempts=0,
                correct=0,
            )

        state = self.states[knowledge_point]
        state.attempts += 1
        if is_correct:
            state.correct += 1

        p_L = state.mastery
        p_T = self.params.p_T
        p_S = self.params.p_S
        p_G = self.TYPE_GUESS.get(question_type, self.params.p_G)

        # 贝叶斯更新
        if is_correct:
            numerator = p_L * (1 - p_S)
            denominator = p_L * (1 - p_S) + (1 - p_L) * p_G
        else:
            numerator = p_L * p_S
            denominator = p_L * p_S + (1 - p_L) * (1 - p_G)

        p_L_given = numerator / max(denominator, 1e-10)

        # 学习转移
        p_L_new = p_L_given + (1 - p_L_given) * p_T
        p_L_new = min(max(p_L_new, 0.01), 0.99)

        state.mastery = round(p_L_new, 4)

    def get_weak_topics(self, threshold: float = 0.5) -> list[KnowledgeState]:
        """获取掌握概率低于阈值的知识点"""
        weak = [s for s in self.states.values() if s.mastery < threshold]
        weak.sort(key=lambda s: s.mastery)
        return weak

    def get_strong_topics(self, threshold: float = 0.8) -> list[KnowledgeState]:
        """获取掌握概率高于阈值的知识点"""
        strong = [s for s in self.states.values() if s.mastery >= threshold]
        strong.sort(key=lambda s: s.mastery, reverse=True)
        return strong

    def get_summary(self) -> dict:
        """获取整体掌握情况"""
        if not self.states:
            return {"avg_mastery": 0, "weak_count": 0, "strong_count": 0, "total": 0}

        values = [s.mastery for s in self.states.values()]
        return {
            "avg_mastery": round(sum(values) / len(values), 2),
            "weak_count": sum(1 for v in values if v < 0.5),
            "moderate_count": sum(1 for v in values if 0.5 <= v < 0.8),
            "strong_count": sum(1 for v in values if v >= 0.8),
            "total": len(values),
            "topics": {s.knowledge_point: round(s.mastery, 2) for s in sorted(self.states.values(), key=lambda x: x.mastery)},
        }

    def recommend_difficulty(self, knowledge_point: str, recent_accuracy: float = 0.5) -> str:
        """推荐题目难度"""
        mastery = self.get_mastery(knowledge_point)
        combined = 0.6 * mastery + 0.4 * recent_accuracy

        if combined >= 0.8:
            return "hard"
        elif combined >= 0.5:
            return "medium"
        else:
            return "easy"

    def to_dict(self) -> dict:
        """序列化"""
        return {
            kp: {"mastery": s.mastery, "attempts": s.attempts, "correct": s.correct}
            for kp, s in self.states.items()
        }

    def load_dict(self, data: dict):
        """从字典加载"""
        for kp, d in data.items():
            self.states[kp] = KnowledgeState(
                knowledge_point=kp,
                mastery=d.get("mastery", self.params.p_L0),
                attempts=d.get("attempts", 0),
                correct=d.get("correct", 0),
            )


# 全局单例
knowledge_tracer = BayesianKnowledgeTracer()
