"""
讯飞星火 API 客户端 — OpenAI 兼容 HTTP 接口
替代原 Kimi/Moonshot，所有 API Key 仅存后端 .env

模型分层策略:
  general       (Spark Lite)  — 免费，简单解析 / SVG 生成
  generalv3     (Spark Pro)   — 练习题、文档、思维导图
  generalv3.5   (Spark Max)   — 画像分析、路径规划
  4.0Ultra      (Spark 4.0)   — 辅导答疑、效果评估（最强推理）
"""

import os
from typing import Optional, List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error

load_dotenv()

# ── 模型路由表 ──────────────────────────────────────────────
MODEL_SIMPLE = os.getenv("SPARK_MODEL_SIMPLE", "general")          # Lite
MODEL_STANDARD = os.getenv("SPARK_MODEL_STANDARD", "generalv3")    # Pro
MODEL_ADVANCED = os.getenv("SPARK_MODEL_ADVANCED", "generalv3.5")  # Max
MODEL_ULTRA = os.getenv("SPARK_MODEL_ULTRA", "4.0Ultra")          # 4.0 Ultra


class SparkClient:
    """讯飞星火 OpenAI 兼容客户端（单例）"""

    _instance: Optional["SparkClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        api_key = os.getenv("SPARK_API_KEY", "")
        base_url = os.getenv("SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/v1")

        if not api_key:
            error("SPARK_API_KEY 未设置，讯飞星火 API 不可用")

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        info(f"讯飞星火客户端初始化完成 (base_url={base_url})")

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
            model: 星火模型 ID
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
            error(f"讯飞星火 API 调用失败 (model={model}): {e}")
            return f"错误: {e}"

    # ── 便捷方法：按任务复杂度选模型 ──────────────────────────
    def simple(self, prompt: str, **kw) -> str:
        """简单任务 — Lite"""
        return self.chat(prompt, model=MODEL_SIMPLE, **kw)

    def standard(self, prompt: str, **kw) -> str:
        """标准任务 — Pro"""
        return self.chat(prompt, model=MODEL_STANDARD, **kw)

    def advanced(self, prompt: str, **kw) -> str:
        """高级任务 — Max"""
        return self.chat(prompt, model=MODEL_ADVANCED, **kw)

    def ultra(self, prompt: str, **kw) -> str:
        """最强推理 — 4.0 Ultra"""
        return self.chat(prompt, model=MODEL_ULTRA, **kw)


# ── 全局单例 ──────────────────────────────────────────────────
spark_client = SparkClient()
