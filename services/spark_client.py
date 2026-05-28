"""
Kimi (Moonshot) API 客户端 — OpenAI 兼容 HTTP 接口
所有 API Key 仅存后端 .env

模型分层策略:
  moonshot-v1-8k    — 简单解析 / SVG 生成
  moonshot-v1-32k   — 练习题、文档、思维导图
  moonshot-v1-128k  — 画像分析、路径规划、辅导答疑、效果评估
"""

import os
from typing import Optional, List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error

load_dotenv()

# ── 模型路由表 ──────────────────────────────────────────────
MODEL_SIMPLE = os.getenv("KIMI_MODEL_SIMPLE", "moonshot-v1-8k")
MODEL_STANDARD = os.getenv("KIMI_MODEL_STANDARD", "moonshot-v1-32k")
MODEL_ADVANCED = os.getenv("KIMI_MODEL_ADVANCED", "moonshot-v1-128k")
MODEL_ULTRA = os.getenv("KIMI_MODEL_ULTRA", "moonshot-v1-128k")


class KimiClient:
    """Kimi (Moonshot) OpenAI 兼容客户端（单例，懒加载）"""

    _instance: Optional["KimiClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    @property
    def client(self):
        if self._client is None:
            api_key = os.getenv("KIMI_API_KEY", "")
            base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
            if not api_key:
                raise RuntimeError(
                    "KIMI_API_KEY 未配置，请在 .env 文件中设置。参考 .env.example"
                )
            self._client = OpenAI(api_key=api_key, base_url=base_url)
            info(f"Kimi 客户端初始化完成 (base_url={base_url})")
        return self._client

    # ── 核心调用 ──────────────────────────────────────────────
    def chat(
        self,
        prompt: str,
        *,
        model: str = MODEL_STANDARD,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        通用文本生成

        Args:
            prompt: 用户提示词
            model: Kimi 模型 ID
            max_tokens: 最大输出 token
            temperature: 温度
            system_prompt: 系统提示词

        Returns:
            模型输出文本
        """
        try:
            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content or ""
            return content

        except Exception as e:
            error(f"Kimi API 调用失败 (model={model}): {e}")
            return f"错误: {e}"

    # ── 便捷方法：按任务复杂度选模型 ──────────────────────────
    def simple(self, prompt: str, **kw) -> str:
        """简单任务 — 8K"""
        return self.chat(prompt, model=MODEL_SIMPLE, **kw)

    def standard(self, prompt: str, **kw) -> str:
        """标准任务 — 32K"""
        return self.chat(prompt, model=MODEL_STANDARD, **kw)

    def advanced(self, prompt: str, **kw) -> str:
        """高级任务 — 128K"""
        return self.chat(prompt, model=MODEL_ADVANCED, **kw)

    def ultra(self, prompt: str, **kw) -> str:
        """最强推理 — 128K"""
        return self.chat(prompt, model=MODEL_ULTRA, **kw)


# ── 全局单例 ──────────────────────────────────────────────────
spark_client = KimiClient()  # 保持变量名兼容，避免改所有 import
