"""
QA服务 — 供各智能体调用的 AI 文本生成
底层委托给 spark_client（MiMo API OpenAI 兼容接口）
"""

from collections.abc import Generator

from core.logger import error, info
from services.spark_client import spark_client


class QAService:
    """QA 服务，供各 Agent 调用"""

    def __init__(self):
        info("QA服务初始化完成（MiMo API）")

    def call_ai(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> str:
        """
        标准 AI 调用（Spark Pro）

        Args:
            prompt: 用户提示词
            max_tokens: 最大 token 数
            system_prompt: 系统提示词

        Returns:
            模型输出文本
        """
        try:
            return spark_client.standard(
                prompt,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )
        except Exception as e:
            error(f"QA 服务调用失败: {e}")
            return f"错误: {e}"

    # 向后兼容别名
    call_kimi_api = call_ai  # 已迁移到 MiMo API，保留别名兼容

    def call_ai_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> Generator[str, None, None]:
        """流式 AI 调用，逐 chunk 返回"""
        return spark_client.chat_stream(
            prompt,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

    # ── 新接口：按任务复杂度调用 ──────────────────────────────
    def call_simple(self, prompt: str, max_tokens: int = 1500, system_prompt: str = None) -> str:
        """简单任务 — Spark Lite（免费）"""
        return spark_client.simple(prompt, max_tokens=max_tokens, system_prompt=system_prompt)

    def call_standard(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """标准任务 — Spark Pro"""
        return spark_client.standard(prompt, max_tokens=max_tokens, system_prompt=system_prompt)

    def call_advanced(self, prompt: str, max_tokens: int = 3000, system_prompt: str = None) -> str:
        """高级任务 — Spark Max"""
        return spark_client.advanced(prompt, max_tokens=max_tokens, system_prompt=system_prompt)

    def call_ultra(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """最强推理 — Spark 4.0 Ultra"""
        return spark_client.ultra(prompt, max_tokens=max_tokens, system_prompt=system_prompt)


# 单例
qa_service = QAService()
