"""
讯飞星火 API 客户端 — OpenAI 兼容接口
所有 API Key 仅存后端 .env

模型分层策略:
  spark-lite      — 简单任务（免费）
  spark-pro       — 标准任务
  spark-max       — 复杂推理
  spark-4.0-ultra — 最强推理
  spark-image     — 图片多模态识别
"""

import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Generator
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error
import httpx

load_dotenv()

# ── 模型路由表（讯飞星火）──────────────────────────────────────
MODEL_SIMPLE   = os.getenv("SPARK_MODEL_SIMPLE", "generalv3.5")      # 简单任务
MODEL_STANDARD = os.getenv("SPARK_MODEL_STANDARD", "generalv3.5")    # 标准任务
MODEL_ADVANCED = os.getenv("SPARK_MODEL_ADVANCED", "4.0Ultra")       # 复杂推理
MODEL_ULTRA    = os.getenv("SPARK_MODEL_ULTRA", "4.0Ultra")          # 最强推理
MODEL_VISION   = os.getenv("SPARK_MODEL_VISION", "generalv3.5")      # 图片多模态


def _generate_spark_token(api_key: str, api_secret: str) -> str:
    """生成讯飞星火 OpenAI 兼容接口的 Bearer Token"""
    # 构建鉴权参数
    now = datetime.now(timezone.utc)
    date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 拼接签名原始字符串
    signature_origin = f"host: spark-api-open.xf-yun.com\ndate: {date}\nGET /v1/chat/completions HTTP/1.1"
    
    # HMAC-SHA256 签名
    signature_sha = hmac.new(
        api_secret.encode('utf-8'),
        signature_origin.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
    
    # 构建 authorization_origin
    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
    
    # Base64 编码
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    return authorization


class SparkClient:
    """讯飞星火 OpenAI 兼容客户端（单例，懒加载）"""

    _instance: Optional["SparkClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    @property
    def client(self):
        if self._client is None:
            api_key = os.getenv("SPARK_API_KEY", "")
            api_secret = os.getenv("SPARK_API_SECRET", "")
            base_url = os.getenv("SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/v1")
            
            if not api_key:
                raise RuntimeError(
                    "SPARK_API_KEY 未配置，请在 .env 文件中设置。参考 .env.example"
                )
            
            # 生成鉴权 Token
            token = _generate_spark_token(api_key, api_secret) if api_secret else api_key
            
            self._client = OpenAI(
                api_key=token,
                base_url=base_url,
                timeout=httpx.Timeout(90.0, connect=15.0),
                max_retries=3,
            )
            info(f"讯飞星火客户端初始化完成 (base_url={base_url})")
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
        标准文本生成调用

        Args:
            prompt: 用户提示词
            model: 模型名称
            max_tokens: 最大 token 数
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

            # 讯飞推理模型只允许 temperature=1
            if "Ultra" in model or "ultra" in model.lower():
                temperature = 1

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            msg = response.choices[0].message
            content = msg.content or ""
            # 讯飞推理模型：content 为空时从 reasoning_content 提取
            if not content and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                reasoning = msg.reasoning_content
                info(f"讯飞推理模型 content 为空，从 reasoning_content 提取 (len={len(reasoning)})")
                import re
                # 尝试从推理过程中提取 JSON
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', reasoning, re.DOTALL)
                if json_matches:
                    content = json_matches[-1]
                else:
                    json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', reasoning)
                    if json_match:
                        content = json_match.group(0)
                    else:
                        lines = [line.strip() for line in reasoning.strip().split('\n') if line.strip()]
                        content = lines[-1] if lines else ""
            if not content:
                error(f"讯飞模型返回空内容 (model={model}, finish_reason={response.choices[0].finish_reason})")
            return content

        except Exception as e:
            error(f"讯飞 API 调用失败 (model={model}): {e}")
            return f"错误: {e}"

    def chat_with_image(
        self,
        prompt: str,
        image_b64: str | List[str],
        *,
        model: str = MODEL_VISION,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        """多模态调用 — 发送图片 + 文本，支持单张或多张图片"""
        try:
            images = [image_b64] if isinstance(image_b64, str) else image_b64
            info(f"多模态调用: model={model}, 图片数量={len(images)}")
            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            content_parts: List[Dict] = [{"type": "text", "text": prompt}]
            for img in images:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
            messages.append({"role": "user", "content": content_parts})
            
            # 讯飞推理模型只允许 temperature=1
            if "Ultra" in model or "ultra" in model.lower():
                temperature = 1
            
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
                info(f"讯飞推理模型 content 为空，从 reasoning_content 提取 (len={len(reasoning)})")
                import re
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', reasoning, re.DOTALL)
                if json_matches:
                    content = json_matches[-1]
                else:
                    json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', reasoning)
                    if json_match:
                        content = json_match.group(0)
                    else:
                        lines = [line.strip() for line in reasoning.strip().split('\n') if line.strip()]
                        content = lines[-1] if lines else ""
            return content
        except Exception as e:
            error(f"讯飞多模态调用失败 (model={model}): {type(e).__name__}: {e}")
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

            # 讯飞推理模型只允许 temperature=1
            if "Ultra" in model or "ultra" in model.lower():
                temperature = 1

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
            error(f"讯飞流式调用失败 (model={model}): {e}")
            yield f"错误: {e}"

    # ── 新接口：按任务复杂度调用 ──────────────────────────────
    def simple(self, prompt: str, max_tokens: int = 1500, system_prompt: str = None) -> str:
        """简单任务 — spark-lite（免费）"""
        return self.chat(prompt, model=MODEL_SIMPLE, max_tokens=max_tokens, system_prompt=system_prompt)

    def standard(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """标准任务 — spark-pro"""
        return self.chat(prompt, model=MODEL_STANDARD, max_tokens=max_tokens, system_prompt=system_prompt)

    def advanced(self, prompt: str, max_tokens: int = 3000, system_prompt: str = None) -> str:
        """高级任务 — spark-max"""
        return self.chat(prompt, model=MODEL_ADVANCED, max_tokens=max_tokens, system_prompt=system_prompt)

    def ultra(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """最强推理 — spark-4.0-ultra"""
        return self.chat(prompt, model=MODEL_ULTRA, max_tokens=max_tokens, system_prompt=system_prompt)

    # ── SparkChain 图片生成 ──────────────────────────────
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[str]:
        """
        使用讯飞 SparkChain 生成图片
        
        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            
        Returns:
            base64 编码的图片数据，失败返回 None
        """
        import requests
        
        api_key = os.getenv("SPARK_API_KEY", "")
        api_secret = os.getenv("SPARK_API_SECRET", "")
        app_id = os.getenv("SPARK_APPID", "")
        
        if not api_key or not api_secret:
            error("SparkChain API 配置不完整")
            return None
        
        # 生成鉴权 Token
        token = _generate_spark_token(api_key, api_secret)
        
        # SparkChain 图片生成 API
        url = "https://spark-api-open.xf-yun.com/v1/images/generations"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "model": "generalv3",  # 使用通用模型生成图片
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json"
        }
        
        try:
            info(f"SparkChain 图片生成: prompt={prompt[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            
            result = resp.json()
            if result.get("data") and len(result["data"]) > 0:
                b64_data = result["data"][0].get("b64_json")
                if b64_data:
                    info(f"SparkChain 图片生成成功")
                    return b64_data
            
            warning(f"SparkChain 返回无图片数据: {result}")
            return None
            
        except Exception as e:
            error(f"SparkChain 图片生成失败: {e}")
            return None

    def generate_image_url(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[str]:
        """
        使用讯飞 SparkChain 生成图片，返回 URL
        
        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            
        Returns:
            图片 URL，失败返回 None
        """
        import requests
        
        api_key = os.getenv("SPARK_API_KEY", "")
        api_secret = os.getenv("SPARK_API_SECRET", "")
        
        if not api_key or not api_secret:
            error("SparkChain API 配置不完整")
            return None
        
        # 生成鉴权 Token
        token = _generate_spark_token(api_key, api_secret)
        
        # SparkChain 图片生成 API
        url = "https://spark-api-open.xf-yun.com/v1/images/generations"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "model": "generalv3",
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "url"
        }
        
        try:
            info(f"SparkChain 图片生成(URL): prompt={prompt[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            
            result = resp.json()
            if result.get("data") and len(result["data"]) > 0:
                img_url = result["data"][0].get("url")
                if img_url:
                    info(f"SparkChain 图片生成成功: {img_url[:50]}...")
                    return img_url
            
            warning(f"SparkChain 返回无图片数据: {result}")
            return None
            
        except Exception as e:
            error(f"SparkChain 图片生成失败: {e}")
            return None


# 全局单例 — 保持变量名兼容，避免改所有 import
spark_client = SparkClient()
