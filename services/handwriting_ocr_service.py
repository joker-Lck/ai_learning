"""
手写答案识别服务 — 专用 OCR（RapidOCR / PP-OCRv6）主力 + 视觉模型兜底

流程：手写增强预处理 → RapidOCR 识别
      → 置信度达标直接返回；否则切 MiMo 视觉模型手写专用 prompt 二次识别
      → 择优返回（附置信度、引擎标识、逐行明细）
"""

import base64
import io

from core.logger import error, info

# RapidOCR 平均置信度低于该阈值时触发视觉模型兜底
RAPIDOCR_CONF_THRESHOLD = 0.55

HANDWRITING_VISION_PROMPT = (
    "这是一张学生手写作答的图片。请逐字识别其中所有手写与印刷文字，"
    "保持原有排版顺序（先题目后作答）。尽量准确还原每个字，"
    "无法辨认的字用〔?〕代替。只输出识别到的文字，不要添加任何解释、评分或翻译。"
)


def _image_to_base64(image_bytes: bytes, max_size: int = 4096, quality: int = 90) -> str:
    """压缩图片并返回 base64 — 与 student_data_service._compress_image 同策略"""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        error(f"图片压缩失败，使用原图: {e}")
        return base64.b64encode(image_bytes).decode("utf-8")


class HandwritingOCRService:
    """手写识别：RapidOCR 主力 + 视觉模型兜底"""

    def __init__(self):
        self._rapid_engine = None
        self._rapid_unavailable = False

    # ── 引擎惰性加载 ──

    def _get_rapidocr(self):
        if self._rapid_unavailable:
            return None
        if self._rapid_engine is None:
            try:
                from rapidocr import RapidOCR

                self._rapid_engine = RapidOCR()
                info("RapidOCR 手写识别引擎已加载")
            except Exception as e:
                self._rapid_unavailable = True
                error(f"RapidOCR 不可用，手写识别降级为视觉模型: {e}")
                return None
        return self._rapid_engine

    # ── 预处理 ──

    @staticmethod
    def _preprocess(image_bytes: bytes) -> bytes:
        try:
            from services.enhanced_vision_service import enhanced_vision

            return enhanced_vision.preprocess_image(image_bytes, enhance_type="handwriting")
        except Exception as e:
            error(f"手写图像预处理失败，使用原图: {e}")
            return image_bytes

    # ── 两路识别 ──

    def _rapid_ocr(self, image_bytes: bytes) -> dict | None:
        """专用 OCR 引擎识别，返回 {text, confidence, segments}"""
        engine = self._get_rapidocr()
        if engine is None:
            return None
        try:
            import numpy as np
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            result = engine(np.array(img))
            txts = list(getattr(result, "txts", None) or [])
            scores = list(getattr(result, "scores", None) or [])
            if not txts:
                return None
            segments = [
                {"text": t, "score": round(float(s), 4)} for t, s in zip(txts, scores or [0.0] * len(txts))
            ]
            confidence = round(sum(s["score"] for s in segments) / len(segments), 4)
            text = "\n".join(t.strip() for t in txts if t and t.strip())
            info(f"RapidOCR 识别: {len(txts)} 行, 置信度 {confidence}")
            return {"text": text, "confidence": confidence, "segments": segments}
        except Exception as e:
            error(f"RapidOCR 识别失败: {e}")
            return None

    def _vision_ocr(self, image_bytes: bytes) -> dict | None:
        """视觉模型兜底识别（手写专用 prompt）"""
        try:
            from services.spark_client import spark_client

            image_b64 = _image_to_base64(image_bytes)
            text = spark_client.chat_with_image(
                HANDWRITING_VISION_PROMPT, image_b64, max_tokens=4000, temperature=0.1
            )
            if not text or text.startswith("错误"):
                error(f"视觉模型手写识别失败: {text}")
                return None
            text = text.strip()
            if not text:
                return None
            # 视觉模型无逐字置信度，按结果完整度给启发式置信度
            confidence = 0.75 if len(text) > 20 else 0.6
            info(f"视觉模型手写识别: {len(text)} 字符")
            return {"text": text, "confidence": confidence, "segments": [{"text": text, "score": confidence}]}
        except Exception as e:
            error(f"视觉模型手写识别异常: {e}")
            return None

    # ── 对外入口 ──

    def recognize(self, image_bytes: bytes, *, use_vision_fallback: bool = True) -> dict:
        """
        手写答案识别。

        Returns:
            {success, text, confidence, engine, segments, low_confidence, all_results}
        """
        if not image_bytes:
            return {"success": False, "text": "", "confidence": 0.0, "engine": "none",
                    "segments": [], "low_confidence": True, "all_results": {}}

        preprocessed = self._preprocess(image_bytes)
        rapid = self._rapid_ocr(preprocessed)
        if rapid is None and preprocessed != image_bytes:
            rapid = self._rapid_ocr(image_bytes)

        all_results: dict = {}
        if rapid:
            all_results["rapidocr"] = rapid

        # RapidOCR 成功且置信度达标 → 主力直接返回
        if rapid and rapid["confidence"] >= RAPIDOCR_CONF_THRESHOLD and rapid["text"].strip():
            return {
                "success": True,
                "text": rapid["text"],
                "confidence": rapid["confidence"],
                "engine": "rapidocr",
                "segments": rapid["segments"],
                "low_confidence": False,
                "all_results": all_results,
            }

        vision = self._vision_ocr(image_bytes) if use_vision_fallback else None
        if vision:
            all_results["vision"] = vision

        # 择优：视觉结果更长且 RapidOCR 不达标时取视觉；否则取已有结果
        best = rapid
        engine = "rapidocr" if rapid else "none"
        if vision and (not rapid or rapid["confidence"] < RAPIDOCR_CONF_THRESHOLD):
            if not rapid or len(vision["text"]) >= len(rapid["text"]) * 0.8:
                best = vision
                engine = "vision"

        if not best or not best["text"].strip():
            return {"success": False, "text": "", "confidence": 0.0, "engine": engine,
                    "segments": [], "low_confidence": True, "all_results": all_results}

        low_conf = best["confidence"] < RAPIDOCR_CONF_THRESHOLD
        return {
            "success": True,
            "text": best["text"],
            "confidence": best["confidence"],
            "engine": engine,
            "segments": best["segments"],
            "low_confidence": low_conf,
            "all_results": all_results,
        }


handwriting_ocr = HandwritingOCRService()
