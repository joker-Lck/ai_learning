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
            # 讯飞推理模型：content 为空或过短时从 reasoning_content 提取
            if (not content or len(content) < 20) and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                reasoning = msg.reasoning_content
                info(f"讯飞推理模型 content 为空，从 reasoning_content 提取 (len={len(reasoning)})")
                from core.json_utils import safe_parse_json
                parsed = safe_parse_json(reasoning)
                if parsed is not None:
                    import json
                    content = json.dumps(parsed, ensure_ascii=False)
                else:
                    # 尝试提取最后一个完整的 JSON 对象
                    import re
                    # 用括号深度匹配提取 JSON（支持任意嵌套）
                    def _extract_last_json(text):
                        candidates = []
                        for start_ch, end_ch in [('{', '}'), ('[', ']')]:
                            i = 0
                            while i < len(text):
                                start = text.find(start_ch, i)
                                if start == -1:
                                    break
                                depth = 0
                                in_str = False
                                esc = False
                                for j in range(start, len(text)):
                                    c = text[j]
                                    if esc:
                                        esc = False
                                        continue
                                    if c == '\\' and in_str:
                                        esc = True
                                        continue
                                    if c == '"' and not esc:
                                        in_str = not in_str
                                        continue
                                    if not in_str:
                                        if c == start_ch:
                                            depth += 1
                                        elif c == end_ch:
                                            depth -= 1
                                            if depth == 0:
                                                candidates.append(text[start:j + 1])
                                                i = j + 1
                                                break
                                else:
                                    i += 1
                                    continue
                        # 返回最长的 JSON 候选
                        return max(candidates, key=len) if candidates else None

                    json_str = _extract_last_json(reasoning)
                    if json_str:
                        content = json_str
                    else:
                        # 降级：提取关键句子
                        import re as re2
                        sentences = re2.split(r'[。！？\n]', reasoning)
                        definition_keywords = ['是', '指', '用于', '属于', '一种', '方法', '技术', '算法']
                        definition_sentences = [s.strip() for s in sentences if any(kw in s for kw in definition_keywords) and len(s.strip()) > 15]
                        if definition_sentences:
                            content = definition_sentences[0]
                        else:
                            lines = [line.strip() for line in reasoning.strip().split('\n') if line.strip()]
                            reasoning_starters = ('嗯，', '首先', '其次', '接下来', '我需要', '让我', '现在', '用户让', '然后', '可能', '还要', '另外', '最后')
                            answer_lines = [l for l in lines if not any(l.startswith(s) for s in reasoning_starters) and len(l) > 15]
                            content = answer_lines[-1] if answer_lines else (lines[-1] if lines else "")
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
            
            app_id = os.getenv("SPARK_IMAGE_APPID") or os.getenv("SPARK_APPID", "")
            api_key = os.getenv("SPARK_IMAGE_API_KEY") or os.getenv("SPARK_API_KEY", "")
            api_secret = os.getenv("SPARK_IMAGE_API_SECRET") or os.getenv("SPARK_API_SECRET", "")
            
            info(f"讯飞图片理解凭证: APPID={app_id[:8]}..., APIKey={api_key[:8]}..., APISecret={api_secret[:8]}...")
            
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
                        error_code = data.get("header", {}).get("code", "")
                        error_msg = data.get("header", {}).get("message", "未知错误")
                        error(f"讯飞图片理解错误: code={error_code}, message={error_msg}")
                        if "AppIdNoAuthError" in str(error_msg):
                            error(f"APPID 无权限访问图片理解服务，请检查：1. 讯飞控制台是否开通图片理解服务 2. API 配额是否充足")
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
            
            def on_error(ws, err):
                error(f"WebSocket 错误: {err}")
            
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
            error(f"图片理解失败: {e}")
            return self._chat_with_image_mimo(prompt, image_b64, max_tokens, system_prompt)

    def _chat_with_image_http(
        self,
        prompt: str,
        image_b64: str | List[str],
        model: str = MODEL_VISION,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ) -> str:
        """HTTP 降级方案 — 使用 MiMo 图片理解"""
        return self._chat_with_image_mimo(prompt, image_b64 if isinstance(image_b64, str) else image_b64[0], max_tokens, system_prompt)

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
    def generate_image(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """
        使用讯飞 TTI API 生成图片
        HTTP: https://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti
        
        Args:
            prompt: 图片描述
            width: 图片宽度 (支持: 512, 768, 1024)
            height: 图片高度 (支持: 512, 768, 1024)
            
        Returns:
            base64 编码的图片数据，失败返回 None
        """
        import requests
        
        app_id = os.getenv("SPARK_IMAGE_APPID", os.getenv("SPARK_APPID", ""))
        api_key = os.getenv("SPARK_IMAGE_API_KEY", os.getenv("SPARK_API_KEY", ""))
        api_secret = os.getenv("SPARK_IMAGE_API_SECRET", os.getenv("SPARK_API_SECRET", ""))
        
        if not app_id or not api_key:
            error("讯飞图片生成 API 配置不完整")
            return None
        
        url = os.getenv("SPARK_IMAGE_URL", "https://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti")
        
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
        
        try:
            info(f"讯飞图片生成: prompt={prompt[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            
            result = resp.json()
            code = result.get("header", {}).get("code", -1)
            
            if code == 0:
                # 获取图片数据
                payload_data = result.get("payload", {})
                choices = payload_data.get("choices", {})
                text_list = choices.get("text", [])
                
                for item in text_list:
                    if item.get("content"):
                        img_data = item["content"]
                        if len(img_data) > 100:
                            info(f"讯飞图片生成成功")
                            return img_data
            
            warning(f"讯飞图片生成返回: {result}")
            return None
            
        except Exception as e:
            error(f"讯飞图片生成失败: {e}")
            return None

    def generate_image_url(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
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
        
        # OCR 使用独立凭证
        app_id = os.getenv("SPARK_OCR_APPID", os.getenv("SPARK_APPID", ""))
        api_key = os.getenv("SPARK_OCR_API_KEY", os.getenv("SPARK_API_KEY", ""))
        api_secret = os.getenv("SPARK_OCR_API_SECRET", os.getenv("SPARK_API_SECRET", ""))
        
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
            message = result.get("header", {}).get("message", "")
            
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
                else:
                    warning("OCR识别返回空结果")
                    return None
            
            warning(f"OCR识别失败 (code={code}): {message}")
            return None
            
        except Exception as e:
            error(f"OCR识别异常: {e}")
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

    # ── MiMo 图片理解 (临时替代讯飞) ──────────────────────
    def _chat_with_image_mimo(
        self,
        prompt: str,
        image_b64: str,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> str:
        """使用 MiMo-V2.5 进行图片理解"""
        try:
            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")
            model = os.getenv("MIMO_MODEL", "MiMo-V2.5")
            
            if not api_key:
                error("MiMo API Key 未配置")
                return ""
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 构建带图片的消息
            image_url = f"data:image/jpeg;base64,{image_b64}" if not image_b64.startswith("data:") else image_b64
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            })
            
            info(f"MiMo 图片理解: model={model}, prompt={prompt[:50]}...")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            
            result = response.choices[0].message.content or ""
            info(f"MiMo 图片理解成功: {len(result)} 字符")
            return result
            
        except Exception as e:
            error(f"MiMo 图片理解失败: {e}")
            return ""

    # ── 讯飞语音合成 (TTS) ──────────────────────────────
    def text_to_speech(self, text: str, voice: str = "xiaoyan") -> Optional[bytes]:
        """
        讯飞长文本语音合成
        https://api-dx.xf-yun.com/v1/private/dts_create
        
        Args:
            text: 要合成的文字
            voice: 发音人（xiaoyan, xiaoyu, vixy 等）
            
        Returns:
            音频数据（PCM格式），失败返回 None
        """
        import requests
        import time
        
        app_id = os.getenv("SPARK_TTS_APPID", os.getenv("SPARK_APPID", ""))
        api_key = os.getenv("SPARK_TTS_API_KEY", os.getenv("SPARK_API_KEY", ""))
        api_secret = os.getenv("SPARK_TTS_API_SECRET", os.getenv("SPARK_API_SECRET", ""))
        
        if not app_id or not api_key:
            error("讯飞语音合成配置不完整")
            return None
        
        url = os.getenv("SPARK_TTS_URL", "https://api-dx.xf-yun.com/v1/private/dts_create")
        
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
                "uid": "user_001",
                "status": 3
            },
            "parameter": {
                "tts": {
                    "vcn": voice,  # 发音人
                    "speed": 50,   # 语速 (0-100)
                    "volume": 50,  # 音量 (0-100)
                    "pitch": 50,   # 音高 (0-100)
                    "bgs": 0,      # 背景音
                    "tte": "UTF8",  # 文本编码
                    "rdn": "0"     # 数字发音方式
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "text": base64.b64encode(text.encode('utf-8')).decode('utf-8'),
                    "status": 3
                }
            }
        }
        
        try:
            info(f"讯飞语音合成: text={text[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            
            result = resp.json()
            code = result.get("header", {}).get("code", -1)
            
            if code == 0:
                # 获取音频数据
                audio_data = result.get("payload", {}).get("audio", {})
                audio_bytes = audio_data.get("audio", "")
                
                if audio_bytes:
                    audio_pcm = base64.b64decode(audio_bytes)
                    info(f"语音合成成功: {len(audio_pcm)} 字节")
                    return audio_pcm
            
            warning(f"语音合成返回: {result}")
            return None
            
        except Exception as e:
            error(f"语音合成失败: {e}")
            return None

    def text_to_speech_file(self, text: str, output_path: str, voice: str = "xiaoyan") -> bool:
        """
        语音合成并保存为文件
        
        Args:
            text: 要合成的文字
            output_path: 输出文件路径（.pcm 或 .wav）
            voice: 发音人
            
        Returns:
            是否成功
        """
        audio_data = self.text_to_speech(text, voice)
        if audio_data:
            try:
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                info(f"语音文件保存成功: {output_path}")
                return True
            except Exception as e:
                error(f"保存语音文件失败: {e}")
                return False
        return False


# 全局单例 — 保持变量名兼容，避免改所有 import
spark_client = SparkClient()
