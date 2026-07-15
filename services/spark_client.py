"""
MiMo API 客户端 — OpenAI 兼容接口
所有 API Key 仅存后端 .env

模型分层策略:
  mimo-v2.5-pro  — 文本对话/推理（主力模型）
  mimo-v2.5      — 视觉理解（图片多模态）
  mimo-image     — 图片生成
  mimo-ocr       — 文字识别
  mimo-tts       — 语音合成
"""

import os
import json
import base64
from typing import Optional, List, Dict, Generator
from openai import OpenAI
from dotenv import load_dotenv
from core.logger import info, error, warning
import httpx

load_dotenv(override=True)

# ── 模型路由表（MiMo）──────────────────────────────────────
def _get_model():
    """动态获取模型名称"""
    return os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

# 为了兼容性，保留这些变量名，但使用函数获取
MODEL_SIMPLE = _get_model()
MODEL_STANDARD = _get_model()
MODEL_ADVANCED = _get_model()
MODEL_ULTRA = _get_model()
MODEL_VISION = os.getenv("MIMO_VISION_MODEL", "mimo-v2.5")


class MiMoClient:
    """MiMo API OpenAI 兼容客户端（单例，懒加载）"""

    _instance: Optional["MiMoClient"] = None

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

            api_key = os.getenv("MIMO_API_KEY", "")
            base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")

            if not api_key:
                raise RuntimeError(
                    "MIMO_API_KEY 未配置，请在 .env 文件中设置。参考 .env.example"
                )

            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(90.0, connect=15.0),
                max_retries=3,
            )
            info(f"MiMo 客户端初始化完成 (base_url={base_url})")
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

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            msg = response.choices[0].message
            content = msg.content or ""
            # 推理模型：content 为空或过短时从 reasoning_content 提取
            if (not content or len(content) < 20) and hasattr(msg, 'reasoning_content') and msg.reasoning_content:
                reasoning = msg.reasoning_content
                info(f"MiMo 推理模型 content 为空，从 reasoning_content 提取 (len={len(reasoning)})")
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
                error(f"MiMo 模型返回空内容 (model={model}, finish_reason={response.choices[0].finish_reason})")
            return content

        except Exception as e:
            error(f"MiMo API 调用失败 (model={model}): {e}")
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
        多模态调用 — MiMo 图片理解 API
        使用 OpenAI 兼容接口（vision 模型）
        """
        try:
            images = [image_b64] if isinstance(image_b64, str) else image_b64
            info(f"MiMo 图片理解: prompt={prompt[:50]}..., 图片数量={len(images)}")

            messages: List[Dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            content_parts: List[Dict] = [{"type": "text", "text": prompt}]
            for img in images:
                if img.startswith('data:'):
                    content_parts.append({"type": "image_url", "image_url": {"url": img}})
                else:
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

            if content:
                info(f"MiMo 图片理解成功: {len(content)} 字符")
            else:
                warning("MiMo 图片理解返回空结果")
            return content

        except Exception as e:
            error(f"MiMo 图片理解失败: {e}")
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
            error(f"MiMo 流式调用失败 (model={model}): {e}")
            yield f"错误: {e}"

    # ── 新接口：按任务复杂度调用 ──────────────────────────────
    def simple(self, prompt: str, max_tokens: int = 1500, system_prompt: str = None) -> str:
        """简单任务"""
        return self.chat(prompt, model=MODEL_SIMPLE, max_tokens=max_tokens, system_prompt=system_prompt)

    def standard(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """标准任务"""
        return self.chat(prompt, model=MODEL_STANDARD, max_tokens=max_tokens, system_prompt=system_prompt)

    def advanced(self, prompt: str, max_tokens: int = 3000, system_prompt: str = None) -> str:
        """高级任务"""
        return self.chat(prompt, model=MODEL_ADVANCED, max_tokens=max_tokens, system_prompt=system_prompt)

    def ultra(self, prompt: str, max_tokens: int = 2000, system_prompt: str = None) -> str:
        """最强推理"""
        return self.chat(prompt, model=MODEL_ULTRA, max_tokens=max_tokens, system_prompt=system_prompt)

    # ── 图片生成 ──────────────────────────────────────────────
    def generate_image(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """
        使用 MiMo 图片生成 API

        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度

        Returns:
            base64 编码的图片数据，失败返回 None
        """
        import requests

        api_key = os.getenv("MIMO_API_KEY", "")
        base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")

        if not api_key:
            error("MiMo 图片生成 API 配置不完整")
            return None

        url = f"{base_url}/images/generations"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": os.getenv("MIMO_IMAGE_MODEL", "mimo-image"),
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json",
        }

        try:
            info(f"MiMo 图片生成: prompt={prompt[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()

            result = resp.json()
            if "data" in result and len(result["data"]) > 0:
                img_data = result["data"][0].get("b64_json") or result["data"][0].get("url")
                if img_data:
                    info("MiMo 图片生成成功")
                    return img_data

            warning(f"MiMo 图片生成返回: {result}")
            return None

        except Exception as e:
            error(f"MiMo 图片生成失败: {e}")
            return None

    def generate_image_url(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """图片生成，返回 base64 数据"""
        return self.generate_image(prompt, width, height)

    # ── OCR 文字识别 ──────────────────────────────────────────
    def ocr_image(self, image_b64: str, ocr_type: str = "auto") -> Optional[str]:
        """
        智能 OCR 识别 — 使用 MiMo 视觉模型

        Args:
            image_b64: base64 编码的图片数据
            ocr_type: "handwriting" | "print" | "auto" (均使用视觉模型)

        Returns:
            识别出的文字，失败返回 None
        """
        try:
            info("MiMo OCR 文字识别...")
            prompt = "请识别这张图片中的所有文字内容，保持原始格式和排版。只输出识别到的文字，不要添加任何解释。"
            result = self.chat_with_image(prompt, image_b64, max_tokens=4000)
            if result and not result.startswith("错误"):
                info(f"OCR 识别成功: {len(result)} 字符")
                return result
            return None
        except Exception as e:
            error(f"OCR 识别失败: {e}")
            return None

    def ocr_handwriting(self, image_b64: str) -> Optional[str]:
        """手写文字识别（使用视觉模型）"""
        return self.ocr_image(image_b64, "handwriting")

    def ocr_print(self, image_b64: str) -> Optional[str]:
        """印刷文字识别（使用视觉模型）"""
        return self.ocr_image(image_b64, "print")

    # ── 语音合成 (TTS) ────────────────────────────────────────
    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """
        语音合成 — 使用 MiMo TTS API

        Args:
            text: 要合成的文字
            voice: 发音人

        Returns:
            音频数据，失败返回 None
        """
        import requests

        api_key = os.getenv("MIMO_API_KEY", "")
        base_url = os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")

        if not api_key:
            error("MiMo TTS API 配置不完整")
            return None

        url = f"{base_url}/audio/speech"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": os.getenv("MIMO_TTS_MODEL", "mimo-tts"),
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }

        try:
            info(f"MiMo 语音合成: text={text[:50]}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()

            if resp.content and len(resp.content) > 100:
                info(f"语音合成成功: {len(resp.content)} 字节")
                return resp.content

            warning("语音合成返回空结果")
            return None

        except Exception as e:
            error(f"语音合成失败: {e}")
            return None

    def text_to_speech_file(self, text: str, output_path: str, voice: str = "alloy") -> bool:
        """
        语音合成并保存为文件

        Args:
            text: 要合成的文字
            output_path: 输出文件路径
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
# 注意：变量名仍叫 spark_client 以兼容现有 import
spark_client = MiMoClient()
