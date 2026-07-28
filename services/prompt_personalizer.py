"""
个性化 Prompt 调度器 — 基于用户画像动态调整 prompt 结构和参数
纯规则实现，零 LLM 调用
"""

from dataclasses import dataclass

from core.logger import info


@dataclass
class PersonalizedPrompt:
    """个性化后的 prompt"""
    prompt: str
    temperature: float
    max_tokens: int
    structure_hint: str


# 认知风格 → 回答结构映射
STYLE_STRUCTURES = {
    "visual": "先用文字概述要点，再用 Mermaid 图解可视化说明，最后举一个具体例子",
    "图解": "先用文字概述要点，再用 Mermaid 图解可视化说明，最后举一个具体例子",
    "实践": "先给核心结论，再用代码或步骤演示，最后给出一道练习题",
    "动手": "先给核心结论，再用代码或步骤演示，最后给出一道练习题",
    "逻辑": "先给出定义和前提，再逐步推导过程，最后总结公式或规则",
    "推理": "先给出定义和前提，再逐步推导过程，最后总结公式或规则",
    "阅读": "分段详细解释，每段标注关键概念，文末给出总结",
    "听觉": "用口语化表达，多用类比和故事，避免大段公式",
}

# 知识水平 → 难度指令
LEVEL_INSTRUCTIONS = {
    "beginner": "用通俗易懂的语言解释，避免过多专业术语，多用生活中的类比帮助理解",
    "intermediate": "适当使用专业术语并给出解释，提供标准的学术表述",
    "advanced": "直接使用专业术语，关注边界条件、特殊情况和深层原理",
}

# 意图 → temperature 映射
INTENT_TEMPERATURE = {
    "definition": 0.3,   # 定义类需要准确
    "code": 0.4,         # 代码需要准确
    "comparison": 0.5,   # 对比需要结构化
    "explanation": 0.7,  # 解释可以灵活
    "example": 0.8,      # 例子可以多样
    "practice": 0.6,     # 练习题需要一定变化
}

# 意图 → token 预算
INTENT_TOKENS = {
    "definition": 800,
    "code": 1500,
    "comparison": 1200,
    "explanation": 1500,
    "example": 1000,
    "practice": 1200,
}


class PromptPersonalizer:
    """Prompt 个性化调度器"""

    def personalize(
        self,
        base_prompt: str,
        profile: dict,
        intent: str = "explanation",
        context: str = "",
    ) -> PersonalizedPrompt:
        """根据画像个性化 prompt"""
        style = self._detect_style(profile)
        level = self._infer_level(profile)
        weak_points = profile.get("weak_points", [])

        # 1. 回答结构
        structure = STYLE_STRUCTURES.get(style, "分步骤解释，标注关键概念")

        # 2. 难度适配
        level_instruction = LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS["intermediate"])

        # 3. 薄弱点提醒
        weak_instruction = ""
        if weak_points and isinstance(weak_points, list):
            topics = "、".join(weak_points[:3])
            weak_instruction = f"\n重点关注：学生在{topics}方面较薄弱，请适当加强解释"

        # 4. 组装 prompt
        parts = [base_prompt]
        if context:
            parts.append(f"\n参考上下文：{context[:1500]}")
        parts.append(f"\n回答风格：{structure}")
        parts.append(f"难度适配：{level_instruction}")
        if weak_instruction:
            parts.append(weak_instruction)

        final_prompt = "\n".join(parts)

        # 5. 参数
        temperature = INTENT_TEMPERATURE.get(intent, 0.7)
        max_tokens = INTENT_TOKENS.get(intent, 1500)

        # 根据水平微调 token
        if level == "beginner":
            max_tokens = int(max_tokens * 1.2)  # 新手需要更详细
        elif level == "advanced":
            max_tokens = int(max_tokens * 0.9)  # 高手可以精简

        info(f"Prompt个性化: style={style}, level={level}, intent={intent}, temp={temperature}")

        return PersonalizedPrompt(
            prompt=final_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            structure_hint=structure,
        )

    def _detect_style(self, profile: dict) -> str:
        """检测认知风格"""
        style = profile.get("cognitive_style", "")
        if isinstance(style, list):
            style = style[0] if style else ""
        style = str(style).lower()

        for key in STYLE_STRUCTURES:
            if key in style:
                return key
        return "visual"  # 默认视觉型

    def _infer_level(self, profile: dict) -> str:
        """推断知识水平"""
        kb = profile.get("knowledge_base", {})
        if isinstance(kb, dict):
            level = kb.get("level", "")
            if level in ("beginner", "intermediate", "advanced"):
                return level
            topics = kb.get("topics", [])
            if isinstance(topics, list):
                if len(topics) >= 8:
                    return "advanced"
                elif len(topics) >= 4:
                    return "intermediate"
        elif isinstance(kb, str):
            if "高级" in kb or "深入" in kb:
                return "advanced"
            elif "基础" in kb or "入门" in kb:
                return "beginner"

        # 从年级推断
        grade = profile.get("grade_level", "")
        if "大三" in str(grade) or "大四" in str(grade) or "研究生" in str(grade):
            return "intermediate"
        elif "大一" in str(grade) or "大二" in str(grade):
            return "beginner"

        return "intermediate"


# 全局单例
prompt_personalizer = PromptPersonalizer()
