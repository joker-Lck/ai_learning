"""
自适应学习路径排序 — 基于知识图谱拓扑 + 掌握度动态调整
纯规则实现，零 LLM 调用
"""

from dataclasses import dataclass
from core.logger import info


@dataclass
class RankedStep:
    """排序后的学习步骤"""
    step: dict
    priority: float
    reason: str


class AdaptivePathPlanner:
    """自适应学习路径规划器"""

    def replan(
        self,
        original_steps: list[dict],
        mastery: dict[str, float],
        completed: set | None = None,
    ) -> list[dict]:
        """根据当前掌握度重新排序学习步骤"""
        completed = completed or set()
        scored: list[RankedStep] = []

        for step in original_steps:
            step_id = step.get("step_number") or step.get("id") or step.get("title", "")
            topic = step.get("topic", "") or step.get("title", "")
            prereqs = step.get("prerequisites", [])

            # 跳过已完成
            if step_id in completed or topic in completed:
                continue

            priority, reason = self._score_step(
                step_id, topic, prereqs, mastery, completed, original_steps
            )
            scored.append(RankedStep(step=step, priority=priority, reason=reason))

        # 按优先级排序
        scored.sort(key=lambda x: x.priority, reverse=True)

        # 重新编号
        result = []
        for i, rs in enumerate(scored):
            step = rs.step.copy()
            step["step_number"] = i + 1
            step["priority_reason"] = rs.reason
            result.append(step)

        info(f"路径重排: {len(original_steps)}步 → {len(result)}步待学")
        return result

    def _score_step(
        self,
        step_id: str,
        topic: str,
        prereqs: list,
        mastery: dict[str, float],
        completed: set,
        all_steps: list[dict],
    ) -> tuple[float, str]:
        """计算步骤优先级分数"""
        priority = 0.0
        reasons = []

        # 1. 前置依赖是否满足
        prereq_met = all(p in completed for p in prereqs)
        if not prereq_met:
            priority -= 100
            reasons.append("前置未满足")
        else:
            priority += 10
            reasons.append("前置已满足")

        # 2. 掌握度越低，优先级越高
        topic_mastery = mastery.get(topic, 0.3)
        priority += (1 - topic_mastery) * 50
        if topic_mastery < 0.3:
            reasons.append("薄弱项")
        elif topic_mastery < 0.5:
            reasons.append("需巩固")

        # 3. 是其他步骤的前置 → 提高优先级（解锁后续）
        is_prereq_for = any(
            step_id in s.get("prerequisites", [])
            for s in all_steps
            if (s.get("step_number") or s.get("id")) != step_id
        )
        if is_prereq_for:
            priority += 25
            reasons.append("解锁后续")

        # 4. 短期收益：简单但不掌握的内容优先（快速得分）
        if topic_mastery < 0.5 and topic_mastery > 0.2:
            priority += 10
            reasons.append("快速提分")

        return priority, "；".join(reasons)


# 全局单例
adaptive_path = AdaptivePathPlanner()
