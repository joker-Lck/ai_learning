"""
智能上下文压缩 — 滑动窗口 + 规则摘要
纯规则实现，零 LLM 调用
"""

import re
from dataclasses import dataclass

from core.logger import info

# 停用词
_STOP = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
         "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看",
         "好", "自己", "这", "他", "她", "它", "吗", "什么", "怎么", "请", "帮"}


@dataclass
class CompressedContext:
    """压缩后的上下文"""
    summary: str           # 历史摘要
    recent_messages: list  # 最近消息（原文保留）
    total_tokens_est: int  # 估算 token 数
    compressed: bool       # 是否发生了压缩


class ContextCompressor:
    """对话上下文压缩器"""

    def __init__(self, recent_count: int = 4, token_budget: int = 3000):
        self.recent_count = recent_count
        self.token_budget = token_budget

    def compress(self, messages: list) -> CompressedContext:
        """压缩对话历史"""
        if not messages:
            return CompressedContext(summary="", recent_messages=[], total_tokens_est=0, compressed=False)

        total_est = self._estimate_tokens(messages)

        # 未超限，直接返回
        if total_est <= self.token_budget:
            return CompressedContext(
                summary="",
                recent_messages=messages,
                total_tokens_est=total_est,
                compressed=False,
            )

        # 分段：最近 N 轮保留原文 + 旧对话做摘要
        recent = messages[-self.recent_count:]
        older = messages[:-self.recent_count]

        summary = self._rule_summary(older)
        recent_est = self._estimate_tokens(recent)

        info(f"上下文压缩: {len(messages)}条 → 摘要+最近{self.recent_count}条, 节省~{total_est - recent_est} tokens")

        return CompressedContext(
            summary=summary,
            recent_messages=recent,
            total_tokens_est=recent_est + len(summary),
            compressed=True,
        )

    def format_for_prompt(self, ctx: CompressedContext) -> str:
        """格式化为 prompt 可用的文本"""
        parts = []
        if ctx.summary:
            parts.append(f"【历史摘要】{ctx.summary}")
        for msg in ctx.recent_messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            parts.append(f"{role}: {msg.get('content', '')[:500]}")
        return "\n\n".join(parts)

    def _rule_summary(self, messages: list) -> str:
        """规则摘要：提取关键词和主题"""
        topics = []
        questions = []
        answers = []

        for msg in messages:
            content = msg.get("content", "")
            if msg.get("role") == "user":
                # 提取问句核心词
                keywords = self._extract_keywords(content)
                topics.extend(keywords)
                # 保留简短问题
                if len(content) < 100:
                    questions.append(content)
            else:
                # 提取答案要点（前 50 字）
                if len(content) > 20:
                    answers.append(content[:50])

        # 去重取 top 关键词
        seen = set()
        unique_topics = []
        for t in topics:
            if t not in seen and len(t) >= 2:
                seen.add(t)
                unique_topics.append(t)
                if len(unique_topics) >= 8:
                    break

        summary_parts = []
        if unique_topics:
            summary_parts.append(f"讨论过: {'、'.join(unique_topics)}")
        if questions:
            summary_parts.append(f"提过{len(questions)}个问题")

        return "；".join(summary_parts) if summary_parts else "（无有效历史）"

    def _extract_keywords(self, text: str) -> list:
        """提取关键词（简单规则）"""
        # 去除标点
        clean = re.sub(r'[^\u4e00-\u9fffa-zA-Z0-9]', ' ', text)
        words = clean.split()
        # 过滤停用词和短词
        return [w for w in words if len(w) >= 2 and w not in _STOP][:10]

    def _estimate_tokens(self, messages: list) -> int:
        """估算 token 数（中文约 1.5 字/token）"""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return int(total_chars / 1.5)


# 全局单例
context_compressor = ContextCompressor()
