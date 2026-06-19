"""
QA服务 — 供各智能体调用的 AI 文本生成
底层委托给 spark_client（讯飞星火 OpenAI 兼容接口）
"""

import os
from typing import Optional, Generator
from openai import OpenAI
from dotenv import load_dotenv
from services.spark_client import spark_client, MODEL_STANDARD
from core.logger import info, error

load_dotenv(override=True)


class QAService:
    """QA 服务，供各 Agent 调用"""

    def __init__(self):
        self._mimo_client = None
        info("QA服务初始化完成（讯飞星火）")

    def _get_mimo_client(self):
        """获取 MiMo 客户端（懒加载）"""
        if self._mimo_client is None:
            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")
            if api_key:
                self._mimo_client = OpenAI(api_key=api_key, base_url=base_url)
        return self._mimo_client

    def call_ai(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
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

    def call_mimo(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        MiMo 模型调用（更快）

        Args:
            prompt: 用户提示词
            max_tokens: 最大 token 数
            system_prompt: 系统提示词

        Returns:
            模型输出文本
        """
        try:
            client = self._get_mimo_client()
            if not client:
                return self.call_ai(prompt, max_tokens, system_prompt)
            
            model = os.getenv("MIMO_MODEL", "MiMo-V2.5")
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            error(f"MiMo 调用失败，降级到讯飞: {e}")
            return self.call_ai(prompt, max_tokens, system_prompt)

    # 向后兼容别名
    call_kimi_api = call_ai  # 已迁移到讯飞星火，保留别名兼容

    def call_ai_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
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
