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
from urllib.parse import urlencode, urlparse
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error, warning
import httpx

load_dotenv(override=True)

# ── 模型路由表（讯飞星火）──────────────────────────────────────
def _get_model():
    """动态获取模型名称"""
    return os.getenv("SPARK_MODEL", "spark-x")

# 为了兼容性，保留这些变量名，但使用函数获取
MODEL_SIMPLE = _get_model()
MODEL_STANDARD = _get_model()
MODEL_ADVANCED = _get_model()
MODEL_ULTRA = _get_model()
MODEL_VISION = _get_model()


def _generate_spark_token(api_key: str, api_secret: str) -> str:
    """
    生成讯飞星火 OpenAI 兼容接口的 Bearer Token
    
    讯飞 OpenAI 兼容接口鉴权方式：
    使用 api_key:api_secret 格式作为 Bearer Token
    """
    return f"{api_key}:{api_secret}"


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
            # 强制重新加载环境变量
            load_dotenv(override=True)
            
            api_key = os.getenv("SPARK_API_KEY", "")
            api_secret = os.getenv("SPARK_API_SECRET", "")
            base_url = os.getenv("SPARK_BASE_URL", "https://spark-api-open.xf-yun.com/agent/v1")

            if not api_key:
                raise RuntimeError(
                    "SPARK_API_KEY 未配置，请在 .env 文件中设置。参考 .env.example"
                )

            # 讯飞星火 OpenAI 兼容接口使用 api_key:api_secret 作为 Bearer Token
            token = f"{api_key}:{api_secret}" if api_secret else api_key

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
        """
        多模态调用 — 讯飞星火图片理解 API
        使用 WebSocket 协议: wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image
        """
        try:
            import websocket
            import hashlib
            import hmac
            import base64
            from datetime import datetime, timezone
            from urllib.parse import urlencode, urlparse
            
            images = [image_b64] if isinstance(image_b64, str) else image_b64
            info(f"讯飞图片理解: prompt={prompt[:50]}..., 图片数量={len(images)}")
            
            app_id = os.getenv("SPARK_APPID", "")
            api_key = os.getenv("SPARK_API_KEY", "")
            api_secret = os.getenv("SPARK_API_SECRET", "")
            
            if not app_id or not api_key or not api_secret:
                error("讯飞图片理解 API 配置不完整（需要 APPID/APIKey/APISecret）")
                return f"错误: API 配置不完整"
            
            # 构建鉴权 URL
            ws_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"
            parsed = urlparse(ws_url)
            host = parsed.hostname
            path = parsed.path
            
            now = datetime.now(timezone.utc)
            date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # 构建签名原始字符串
            signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
            
            # HMAC-SHA256 签名
            signature_sha = hmac.new(
                api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
            
            # 构建 authorization_origin
            authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
            
            # 构建完整 URL
            params = {
                "authorization": authorization,
                "date": date,
                "host": host
            }
            full_url = f"{ws_url}?{urlencode(params)}"
            
            # 构建请求消息
            # 将图片转为 URL 格式（data:image/jpeg;base64,...）
            image_urls = []
            for img in images:
                if img.startswith('data:'):
                    image_urls.append(img)
                else:
                    image_urls.append(f"data:image/jpeg;base64,{img}")
            
            # 构建用户消息
            user_content = []
            for img_url in image_urls:
                user_content.append({"role": "user", "content": img_url})
            user_content.append({"role": "user", "content": prompt})
            
            request_data = {
                "header": {
                    "app_id": app_id,
                    "uid": "user_001"
                },
                "parameter": {
                    "chat": {
                        "domain": "image",
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_k": 4,
                        "auditing": "default"
                    }
                },
                "payload": {
                    "message": {
                        "text": user_content
                    }
                }
            }
            
            # WebSocket 调用
            result_text = []
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get("header", {}).get("code") != 0:
                        error(f"讯飞图片理解错误: {data.get('header', {}).get('message', '未知错误')}")
                        ws.close()
                        return
                    
                    text = data.get("payload", {}).get("choices", {}).get("text", [])
                    for item in text:
                        if item.get("content"):
                            result_text.append(item["content"])
                    
                    if data.get("header", {}).get("status") == 2:
                        ws.close()
                except Exception as e:
                    error(f"解析消息失败: {e}")
                    ws.close()
            
            def on_error(ws, error):
                error(f"WebSocket 错误: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                pass
            
            def on_open(ws):
                ws.send(json.dumps(request_data))
            
            ws = websocket.WebSocketApp(
                full_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            ws.run_forever(ping_timeout=30)
            
            result = "".join(result_text)
            if not result:
                warning("讯飞图片理解返回空结果")
                return ""
            
            info(f"讯飞图片理解成功: {len(result)} 字符")
            return result
            
        except ImportError:
            warning("websocket-client 未安装，降级到 HTTP API")
            return self._chat_with_image_http(prompt, image_b64, model, max_tokens, temperature, system_prompt)
        except Exception as e:
            error(f"讯飞图片理解失败: {e}")
            return self._chat_with_image_http(prompt, image_b64, model, max_tokens, temperature, system_prompt)

    def _chat_with_image_http(
        self,
        prompt: str,
        image_b64: str | List[str],
        model: str = MODEL_VISION,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        """HTTP 降级方案 — 使用 OpenAI 兼容接口"""
        try:
            images = [image_b64] if isinstance(image_b64, str) else image_b64
            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            content_parts: List[Dict] = [{"type": "text", "text": prompt}]
            for img in images:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
            messages.append({"role": "user", "content": content_parts})
            
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
            error(f"HTTP 降级调用失败: {e}")
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

    # ── 讯飞图片生成 (TTI) ──────────────────────────────
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[str]:
        """
        使用讯飞 TTI API 生成图片
        WebSocket: wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti
        
        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            
        Returns:
            base64 编码的图片数据，失败返回 None
        """
        try:
            import websocket
            import time
            
            app_id = os.getenv("SPARK_IMAGE_APPID", os.getenv("SPARK_APPID", ""))
            api_key = os.getenv("SPARK_IMAGE_API_KEY", os.getenv("SPARK_API_KEY", ""))
            api_secret = os.getenv("SPARK_IMAGE_API_SECRET", os.getenv("SPARK_API_SECRET", ""))
            
            if not app_id or not api_key or not api_secret:
                error("讯飞图片生成 API 配置不完整")
                return None
            
            # 构建鉴权 URL
            ws_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti"
            parsed = urlparse(ws_url)
            host = parsed.hostname
            path = parsed.path
            
            now = datetime.now(timezone.utc)
            date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # 构建签名
            signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
            signature_sha = hmac.new(
                api_secret.encode('utf-8'),
                signature_origin.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
            
            authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
            authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
            
            params = {"authorization": authorization, "date": date, "host": host}
            full_url = f"{ws_url}?{urlencode(params)}"
            
            # 构建请求
            request_data = {
                "header": {
                    "app_id": app_id,
                    "uid": "user_001"
                },
                "parameter": {
                    "chat": {
                        "domain": "tti",
                        "width": width,
                        "height": height
                    }
                },
                "payload": {
                    "message": {
                        "text": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                }
            }
            
            result_data = []
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    code = data.get("header", {}).get("code", -1)
                    
                    if code != 0:
                        error(f"讯飞图片生成错误: {data.get('header', {}).get('message', '未知错误')}")
                        ws.close()
                        return
                    
                    # 获取图片数据
                    payload = data.get("payload", {})
                    choices = payload.get("choices", {})
                    text_list = choices.get("text", [])
                    
                    for item in text_list:
                        if item.get("content"):
                            result_data.append(item["content"])
                    
                    status = data.get("header", {}).get("status", 0)
                    if status == 2:
                        ws.close()
                except Exception as e:
                    error(f"解析消息失败: {e}")
                    ws.close()
            
            def on_error(ws, err):
                error(f"WebSocket 错误: {err}")
            
            def on_close(ws, close_status_code, close_msg):
                pass
            
            def on_open(ws):
                ws.send(json.dumps(request_data))
            
            info(f"讯飞图片生成: prompt={prompt[:50]}...")
            
            ws = websocket.WebSocketApp(
                full_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            ws.run_forever(ping_timeout=30)
            
            if result_data:
                # 返回 base64 图片数据
                img_data = result_data[0]
                if len(img_data) > 100:  # 有效的 base64 数据
                    info(f"讯飞图片生成成功")
                    return img_data
            
            warning("讯飞图片生成返回空结果")
            return None
            
        except ImportError:
            warning("websocket-client 未安装")
            return None
        except Exception as e:
            error(f"讯飞图片生成失败: {e}")
            return None

    def generate_image_url(self, prompt: str, width: int = 1024, height: int = 1024) -> Optional[str]:
        """
        使用讯飞 TTI API 生成图片，返回 base64 数据（与 generate_image 相同）
        
        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            
        Returns:
            base64 编码的图片数据，失败返回 None
        """
        return self.generate_image(prompt, width, height)

    # ── 讯飞 OCR 文字识别 ──────────────────────────────
    def ocr_handwriting(self, image_b64: str) -> Optional[str]:
        """
        讯飞手写文字识别
        
        Args:
            image_b64: base64 编码的图片数据
            
        Returns:
            识别出的文字，失败返回 None
        """
        import requests
        import time
        
        app_id = os.getenv("SPARK_IMAGE_APPID", os.getenv("SPARK_APPID", ""))
        api_key = os.getenv("SPARK_IMAGE_API_KEY", os.getenv("SPARK_API_KEY", ""))
        
        if not app_id or not api_key:
            error("讯飞 OCR 配置不完整（需要 APPID/APIKey）")
            return None
        
        url = "https://webapi.xfyun.cn/v1/service/v1/ocr/handwriting"
        
        # 构建请求头
        cur_time = str(int(time.time()))
        param = {
            "engine_type": "handwriting",
            "status": 3
        }
        param_base64 = base64.b64encode(json.dumps(param).encode('utf-8')).decode('utf-8')
        
        # 构建签名
        checksum = hashlib.md5((api_key + cur_time + param_base64).encode('utf-8')).hexdigest()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Appid": app_id,
            "X-CurTime": cur_time,
            "X-Param": param_base64,
            "X-CheckSum": checksum
        }
        
        data = {
            "image": image_b64
        }
        
        try:
            info("讯飞手写文字识别...")
            resp = requests.post(url, headers=headers, data=data, timeout=30)
            resp.raise_for_status()
            
            result = resp.json()
            if result.get("code") == "0":
                text = result.get("data", {}).get("region", "")
                if text:
                    info(f"手写识别成功: {len(text)} 字符")
                    return text
            
            warning(f"手写识别返回: {result}")
            return None
            
        except Exception as e:
            error(f"手写识别失败: {e}")
            return None

    def ocr_print(self, image_b64: str) -> Optional[str]:
        """
        讯飞通用文档识别 (OCR大模型)
        https://cbm01.cn-huabei-1.xf-yun.com/v1/private/se75ocrbm
        """
        import requests
        
        # OCR 使用图片生成的凭证
        app_id = os.getenv("SPARK_IMAGE_APPID", os.getenv("SPARK_APPID", ""))
        api_key = os.getenv("SPARK_IMAGE_API_KEY", os.getenv("SPARK_API_KEY", ""))
        api_secret = os.getenv("SPARK_IMAGE_API_SECRET", os.getenv("SPARK_API_SECRET", ""))
        
        if not app_id or not api_key:
            error("讯飞 OCR 配置不完整")
            return None
        
        url = os.getenv("SPARK_OCR_URL", "https://cbm01.cn-huabei-1.xf-yun.com/v1/private/se75ocrbm")
        
        # 生成鉴权 Token
        token = _generate_spark_token(api_key, api_secret)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "appid": app_id
        }
        
        payload = {
            "header": {
                "app_id": app_id,
                "status": 3
            },
            "parameter": {
                "ocr": {
                    "result_option": "normal"
                }
            },
            "payload": {
                "image": {
                    "encoding": "jpg",
                    "image": image_b64,
                    "status": 3
                }
            }
        }
        
        try:
            info("讯飞通用文档识别(OCR大模型)...")
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            
            result = resp.json()
            code = result.get("header", {}).get("code", -1)
            
            if code == 0:
                # 提取识别结果
                pages = result.get("payload", {}).get("result", {}).get("page", [])
                texts = []
                for page in pages:
                    for line in page.get("line", []):
                        for word in line.get("word", []):
                            if word.get("content"):
                                texts.append(word["content"])
                
                text = "\n".join(texts)
                if text:
                    info(f"OCR识别成功: {len(text)} 字符")
                    return text
            
            warning(f"OCR识别返回: {result}")
            return None
            
        except Exception as e:
            error(f"OCR识别失败: {e}")
            return None

    def ocr_image(self, image_b64: str, ocr_type: str = "auto") -> Optional[str]:
        """
        智能 OCR 识别（自动选择手写或印刷）
        
        Args:
            image_b64: base64 编码的图片数据
            ocr_type: "handwriting" | "print" | "auto"
            
        Returns:
            识别出的文字，失败返回 None
        """
        if ocr_type == "handwriting":
            return self.ocr_handwriting(image_b64)
        elif ocr_type == "print":
            return self.ocr_print(image_b64)
        else:
            # 自动模式：先尝试印刷识别，失败再尝试手写
            result = self.ocr_print(image_b64)
            if result:
                return result
            return self.ocr_handwriting(image_b64)


# 全局单例 — 保持变量名兼容，避免改所有 import
spark_client = SparkClient()
