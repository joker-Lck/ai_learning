"""
Kimi (Moonshot) API 客户端 — OpenAI 兼容 HTTP 接口
所有 API Key 仅存后端 .env

模型分层策略:
  kimi-k2.5                      — 简单/标准任务（推理模型）
  kimi-k2.6                      — 复杂/高级推理任务
  moonshot-v1-8k-vision-preview  — 图片多模态识别
"""

import os
from typing import Optional, List, Dict, Generator
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error
import httpx

load_dotenv()

# ── 模型路由表 ──────────────────────────────────────────────
MODEL_SIMPLE = os.getenv("KIMI_MODEL_SIMPLE", "kimi-k2.5")
MODEL_STANDARD = os.getenv("KIMI_MODEL_STANDARD", "kimi-k2.5")
MODEL_ADVANCED = os.getenv("KIMI_MODEL_ADVANCED", "kimi-k2.6")
MODEL_ULTRA = os.getenv("KIMI_MODEL_ULTRA", "kimi-k2.6")
MODEL_VISION = os.getenv("KIMI_MODEL_VISION", "moonshot-v1-8k-vision-preview")


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
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(60.0, connect=5.0),
                max_retries=1,
            )
            info(f"Kimi 客户端初始化完成 (base_url={base_url})")
        return self._client

    # ── 核心调用 ──────────────────────────────────────────────
    def chat(
        self,
        prompt: str,
        *,
        model: str = MODEL_STANDARD,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        通用文本生成（兼容 k2.x 推理模型）

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

            msg = response.choices[0].message
            content = msg.content or ""
            # k2.x 推理模型：content 为空时从 reasoning_content 提取
            if not content and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                reasoning = msg.reasoning_content
                # 尝试从推理过程中提取 JSON 或最后一段
                import re
                json_match = re.search(r'\[.*\]|\{.*\}', reasoning, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    content = reasoning.strip().split('\n')[-1]
            return content

        except Exception as e:
            error(f"Kimi API 调用失败 (model={model}): {e}")
            return f"错误: {e}"

    def chat_with_image(
        self,
        prompt: str,
        image_b64: str,
        *,
        model: str = MODEL_VISION,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        """多模态调用 — 发送图片 + 文本"""
        try:
            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            })
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            msg = response.choices[0].message
            content = msg.content or ""
            if not content and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                reasoning = msg.reasoning_content
                import re
                json_match = re.search(r'\[.*\]|\{.*\}', reasoning, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
                else:
                    content = reasoning.strip().split('\n')[-1]
            return content
        except Exception as e:
            error(f"Kimi 多模态调用失败 (model={model}): {e}")
            return f"错误: {e}"

    def chat_stream(
        self,
        prompt: str,
        *,
        model: str = MODEL_STANDARD,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """流式文本生成，逐 chunk 返回"""
        try:
            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            error(f"Kimi 流式调用失败 (model={model}): {e}")
            yield f"错误: {e}"

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
