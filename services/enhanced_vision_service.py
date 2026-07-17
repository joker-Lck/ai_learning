"""
增强视觉识别服务 — 课表/错题/成绩单专用识别
升级点：
1. 图像预处理（增强对比度、去噪、倾斜校正）
2. 多策略 OCR 融合（通用 OCR + 结构化提取）
3. 专用 prompt（课表/错题/成绩单分别优化）
4. 置信度评估 + 后处理验证
"""

import base64
import io
import json
import re

from core.logger import debug, error, info, warning


class EnhancedVisionService:
    """增强视觉识别服务"""

    def __init__(self):
        self._spark_client = None

    @property
    def spark_client(self):
        if self._spark_client is None:
            from services.spark_client import spark_client
            self._spark_client = spark_client
        return self._spark_client

    # ═══════════════════════════════════════
    # 图像预处理
    # ═══════════════════════════════════════

    def preprocess_image(self, image_bytes: bytes, enhance_type: str = "auto") -> bytes:
        """
        图像预处理 — 提升 OCR 识别率

        Args:
            image_bytes: 原始图片字节
            enhance_type: "auto" | "schedule" | "handwriting" | "document"

        Returns:
            处理后的图片字节
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter

            img = Image.open(io.BytesIO(image_bytes))

            # 转为 RGB（处理 RGBA/P 等模式）
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # 1. 自动旋转（基于 EXIF）
            img = self._auto_rotate(img)

            # 2. 根据类型选择处理策略
            if enhance_type == "schedule":
                img = self._enhance_for_schedule(img)
            elif enhance_type == "handwriting":
                img = self._enhance_for_handwriting(img)
            elif enhance_type == "document":
                img = self._enhance_for_document(img)
            else:
                img = self._enhance_auto(img)

            # 3. 转回 bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()

        except ImportError:
            debug("Pillow 未安装，跳过图像预处理")
            return image_bytes
        except Exception as e:
            debug(f"图像预处理失败: {e}")
            return image_bytes

    def _auto_rotate(self, img):
        """基于 EXIF 自动旋转"""
        try:
            from PIL import ImageOps
            return ImageOps.exif_transpose(img) or img
        except Exception:
            return img

    def _enhance_auto(self, img):
        """自动增强（通用）"""
        from PIL import ImageEnhance

        # 如果图片太小，放大到至少 1500px 宽
        if img.width < 1500:
            scale = 1500 / img.width
            img = img.resize((int(img.width * scale), int(img.height * scale)),
                           Image.Resampling.LANCZOS)

        # 适度增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)

        # 适度增强锐度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)

        return img

    def _enhance_for_schedule(self, img):
        """课表专用增强 — 表格线条清晰化"""
        from PIL import ImageEnhance, ImageFilter

        # 放大
        if img.width < 2000:
            scale = 2000 / img.width
            img = img.resize((int(img.width * scale), int(img.height * scale)),
                           Image.Resampling.LANCZOS)

        # 高对比度（表格需要）
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # 锐化（线条清晰）
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)

        # 轻微去噪
        img = img.filter(ImageFilter.MedianFilter(size=3))

        return img

    def _enhance_for_handwriting(self, img):
        """手写专用增强 — 笔迹强化"""
        from PIL import ImageEnhance, ImageFilter

        # 放大
        if img.width < 1500:
            scale = 1500 / img.width
            img = img.resize((int(img.width * scale), int(img.height * scale)),
                           Image.Resampling.LANCZOS)

        # 中等对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)

        # 轻微锐化
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)

        # 去噪（手写容易有噪点）
        img = img.filter(ImageFilter.MedianFilter(size=5))

        return img

    def _enhance_for_document(self, img):
        """文档专用增强 — 打印文字清晰化"""
        from PIL import ImageEnhance, ImageFilter

        # 放大
        if img.width < 1500:
            scale = 1500 / img.width
            img = img.resize((int(img.width * scale), int(img.height * scale)),
                           Image.Resampling.LANCZOS)

        # 高对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)

        # 高锐度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.6)

        return img

    # ═══════════════════════════════════════
    # 多策略 OCR
    # ═══════════════════════════════════════

    def multi_strategy_ocr(self, image_b64: str, doc_type: str = "auto") -> dict:
        """
        多策略 OCR — 融合通用 OCR + 结构化提取

        Args:
            image_b64: base64 图片
            doc_type: "schedule" | "error_note" | "grade" | "auto"

        Returns:
            {
                "text": str,           # 识别文本
                "confidence": float,   # 置信度 0-1
                "structured": dict,    # 结构化数据（如果有）
                "strategy": str,       # 使用的策略
            }
        """
        results = []

        # 策略 1: 通用 OCR
        ocr_text = self.spark_client.ocr_image(image_b64)
        if ocr_text and len(ocr_text) > 10:
            results.append({
                "text": ocr_text,
                "strategy": "general_ocr",
                "length": len(ocr_text),
            })

        # 策略 2: 结构化提取（直接用视觉模型提取结构化数据）
        if doc_type != "auto":
            structured = self._structured_extraction(image_b64, doc_type)
            if structured:
                results.append({
                    "text": json.dumps(structured, ensure_ascii=False),
                    "strategy": "structured_extraction",
                    "structured": structured,
                    "length": len(json.dumps(structured, ensure_ascii=False)),
                })

        # 策略 3: 专用 prompt OCR（针对特定文档类型优化）
        specialized_text = self._specialized_ocr(image_b64, doc_type)
        if specialized_text and len(specialized_text) > 10:
            results.append({
                "text": specialized_text,
                "strategy": "specialized_ocr",
                "length": len(specialized_text),
            })

        if not results:
            return {"text": "", "confidence": 0.0, "structured": None, "strategy": "none"}

        # 选择最佳结果（最长的通常最完整）
        best = max(results, key=lambda r: r["length"])

        # 计算置信度
        confidence = self._calculate_confidence(results, best)

        return {
            "text": best.get("text", ""),
            "confidence": confidence,
            "structured": best.get("structured"),
            "strategy": best["strategy"],
            "all_results": len(results),
        }

    def _structured_extraction(self, image_b64: str, doc_type: str) -> dict | None:
        """直接用视觉模型提取结构化数据"""
        prompts = {
            "schedule": """请识别这张课程表图片，直接输出 JSON 格式的课程数据。
输出格式：
[
  {"course_name": "课程名", "day": "周一", "start_time": "08:00", "end_time": "09:40", "location": "教室", "teacher": "老师"}
]
要求：
1. day 用周一~周日表示
2. time 用 HH:MM 格式
3. 如果看不清某个字段，用空字符串
4. 只输出 JSON 数组，不要其他内容""",

            "error_note": """请识别这张错题图片，直接输出 JSON 格式的错题数据。
输出格式：
{
  "subject": "学科",
  "question": "题目内容",
  "my_answer": "我的答案",
  "correct_answer": "正确答案",
  "error_reason": "错误原因分析",
  "knowledge_point": "涉及知识点"
}
要求：
1. 尽量完整提取题目内容
2. 如果看不清某个字段，用空字符串
3. 只输出 JSON，不要其他内容""",

            "grade": """请识别这张成绩单图片，直接输出 JSON 格式的数据。
输出格式：
[
  {"course_name": "课程名", "score": 分数, "semester": "学期"}
]
要求：
1. score 用数字表示
2. 如果看不清某个字段，用空字符串
3. 只输出 JSON 数组，不要其他内容""",
        }

        prompt = prompts.get(doc_type)
        if not prompt:
            return None

        try:
            result = self.spark_client.chat_with_image(prompt, image_b64, max_tokens=4000)
            if result and not result.startswith("错误"):
                # 提取 JSON
                match = re.search(r'[\[\{].*[\]\}]', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            debug(f"结构化提取失败: {e}")

        return None

    def _specialized_ocr(self, image_b64: str, doc_type: str) -> str | None:
        """专用 prompt OCR"""
        prompts = {
            "schedule": """这是一张课程表图片。请仔细识别所有课程信息，包括：
- 课程名称
- 上课时间（星期几、第几节）
- 上课教室
- 任课老师

请按时间顺序列出所有课程，保持表格结构。如果某个信息看不清，请标注[?]。""",

            "error_note": """这是一张错题图片。请仔细识别：
- 题目内容（完整）
- 我写的答案
- 正确答案
- 错误原因

请尽量保持原格式，数学公式用 LaTeX 表示。""",

            "grade": """这是一张成绩单图片。请识别所有课程的成绩信息，包括：
- 课程名称
- 成绩/分数
- 学期

请按顺序列出所有课程成绩。""",
        }

        prompt = prompts.get(doc_type, "请识别这张图片中的所有文字内容，保持原始格式。")

        try:
            result = self.spark_client.chat_with_image(prompt, image_b64, max_tokens=4000)
            if result and not result.startswith("错误"):
                return result
        except Exception as e:
            debug(f"专用 OCR 失败: {e}")

        return None

    def _calculate_confidence(self, results: list, best: dict) -> float:
        """计算识别置信度"""
        confidence = 0.5  # 基础分

        # 多策略一致 → 更可信
        if len(results) >= 2:
            confidence += 0.2

        # 文本长度合理 → 更可信
        text_len = best.get("length", 0)
        if text_len > 100:
            confidence += 0.15
        elif text_len > 50:
            confidence += 0.1

        # 结构化提取成功 → 更可信
        if best.get("structured"):
            confidence += 0.15

        return min(confidence, 1.0)

    # ═══════════════════════════════════════
    # 高级识别接口
    # ═══════════════════════════════════════

    def recognize_schedule(self, image_bytes: bytes) -> dict:
        """
        课表专用识别 — 预处理 + 多策略 + 验证

        Returns:
            {
                "success": bool,
                "courses": list,      # 课程列表
                "confidence": float,
                "raw_text": str,
                "message": str,
            }
        """
        # 1. 预处理
        processed = self.preprocess_image(image_bytes, "schedule")
        image_b64 = base64.b64encode(processed).decode('utf-8')

        # 2. 多策略识别
        result = self.multi_strategy_ocr(image_b64, "schedule")

        if result["confidence"] < 0.3:
            return {
                "success": False,
                "courses": [],
                "confidence": result["confidence"],
                "raw_text": result["text"],
                "message": "识别置信度过低，建议重新拍照或手动录入",
            }

        # 3. 解析课程数据
        courses = []
        if result.get("structured"):
            courses = result["structured"] if isinstance(result["structured"], list) else []
        elif result["text"]:
            courses = self._parse_schedule_text(result["text"])

        # 4. 验证
        courses = self._validate_courses(courses)

        if not courses:
            return {
                "success": False,
                "courses": [],
                "confidence": result["confidence"],
                "raw_text": result["text"],
                "message": "未能识别出有效课程，请确认图片是否为课程表",
            }

        return {
            "success": True,
            "courses": courses,
            "confidence": result["confidence"],
            "raw_text": result["text"],
            "message": f"成功识别 {len(courses)} 门课程",
        }

    def recognize_error_note(self, image_bytes: bytes) -> dict:
        """
        错题专用识别

        Returns:
            {
                "success": bool,
                "error_note": dict,
                "confidence": float,
                "raw_text": str,
            }
        """
        # 1. 预处理
        processed = self.preprocess_image(image_bytes, "handwriting")
        image_b64 = base64.b64encode(processed).decode('utf-8')

        # 2. 多策略识别
        result = self.multi_strategy_ocr(image_b64, "error_note")

        # 3. 解析
        error_note = None
        if result.get("structured"):
            error_note = result["structured"]
        elif result["text"]:
            error_note = self._parse_error_note_text(result["text"])

        return {
            "success": error_note is not None,
            "error_note": error_note or {},
            "confidence": result["confidence"],
            "raw_text": result["text"],
        }

    def recognize_grade(self, image_bytes: bytes) -> dict:
        """
        成绩单专用识别

        Returns:
            {
                "success": bool,
                "grades": list,
                "confidence": float,
                "raw_text": str,
            }
        """
        # 1. 预处理
        processed = self.preprocess_image(image_bytes, "document")
        image_b64 = base64.b64encode(processed).decode('utf-8')

        # 2. 多策略识别
        result = self.multi_strategy_ocr(image_b64, "grade")

        # 3. 解析
        grades = []
        if result.get("structured"):
            grades = result["structured"] if isinstance(result["structured"], list) else []
        elif result["text"]:
            grades = self._parse_grade_text(result["text"])

        return {
            "success": len(grades) > 0,
            "grades": grades,
            "confidence": result["confidence"],
            "raw_text": result["text"],
        }

    # ═══════════════════════════════════════
    # 文本解析
    # ═══════════════════════════════════════

    def _parse_schedule_text(self, text: str) -> list:
        """从 OCR 文本解析课程"""
        try:
            # 尝试直接解析 JSON
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                courses = json.loads(match.group())
                if isinstance(courses, list):
                    return courses
        except json.JSONDecodeError:
            pass

        # 降级：用 AI 解析
        try:
            prompt = f"""请从以下 OCR 文本中提取课程信息，输出 JSON 数列。

OCR 文本：
{text[:6000]}

输出格式：
[{{"course_name": "课程名", "day": "周一", "start_time": "08:00", "end_time": "09:40", "location": "教室", "teacher": "老师"}}]

只输出 JSON 数组，不要其他内容。"""

            result = self.spark_client.simple(prompt, max_tokens=4000)
            if result and not result.startswith("错误"):
                match = re.search(r'\[.*\]', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception:
            pass

        return []

    def _parse_error_note_text(self, text: str) -> dict | None:
        """从 OCR 文本解析错题"""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass

        # 降级：用 AI 解析
        try:
            prompt = f"""请从以下 OCR 文本中提取错题信息。

OCR 文本：
{text[:4000]}

输出 JSON 格式：
{{"subject": "学科", "question": "题目", "my_answer": "我的答案", "correct_answer": "正确答案", "error_reason": "错误原因", "knowledge_point": "知识点"}}

只输出 JSON，不要其他内容。"""

            result = self.spark_client.simple(prompt, max_tokens=2000)
            if result and not result.startswith("错误"):
                match = re.search(r'\{.*\}', result, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception:
            pass

        return None

    def _parse_grade_text(self, text: str) -> list:
        """从 OCR 文本解析成绩"""
        try:
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass
        return []

    def _validate_courses(self, courses: list) -> list:
        """验证课程数据格式"""
        valid = []
        days = {'周一', '周二', '周三', '周四', '周五', '周六', '周日',
                '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'}

        for c in courses:
            if not isinstance(c, dict):
                continue
            name = c.get('course_name', '').strip()
            if not name:
                continue

            # 校验日期
            day = c.get('day', '')
            if day and day not in days:
                # 尝试转换
                day_map = {'1': '周一', '2': '周二', '3': '周三', '4': '周四',
                          '5': '周五', '6': '周六', '7': '周日', '0': '周日'}
                day = day_map.get(str(day), day)

            valid.append({
                'course_name': name,
                'day': day,
                'start_time': c.get('start_time', ''),
                'end_time': c.get('end_time', ''),
                'location': c.get('location', ''),
                'teacher': c.get('teacher', ''),
            })

        return valid


# 全局单例
enhanced_vision = EnhancedVisionService()
