"""
AI 视频/动画生成服务
- 优先: 调用视频生成 API 生成真实 mp4
- 降级: AI 生成 SVG + CSS 交互动画（浏览器直接渲染）
生成的文件保存到 exports/ 目录
"""

import os
import re
import json
import hashlib
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from core.logger import info, error, warning

# 导出目录
EXPORT_DIR = Path(__file__).parent.parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


class VideoGenerationService:
    """视频/动画生成服务"""

    _instance: Optional["VideoGenerationService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ──────────────────────────────────────────────
    # 公开接口
    # ──────────────────────────────────────────────

    def generate_video(self, subject: str, topic: str, description: str,
                       duration: int = 10) -> Dict:
        """
        生成教学视频。
        1. 尝试调用视频生成 API → mp4
        2. 降级: AI 生成 SVG 交互动画 → html
        返回: {"type": "video"|"svg_animation", "url": "/exports/xxx", "title": "..."}
        """
        # 优先尝试视频 API
        video_url = self._try_video_api(subject, topic, description, duration)
        if video_url:
            return {"type": "video", "url": video_url, "title": f"{topic}教学视频"}

        # 降级: SVG 动画
        svg_url = self._generate_svg_animation(subject, topic, description, "video")
        if svg_url:
            return {"type": "svg_animation", "url": svg_url, "title": f"{topic}教学动画"}

        return {"type": "failed", "url": None, "title": f"{topic}视频"}

    def generate_animation(self, subject: str, topic: str, description: str,
                           duration: int = 4) -> Dict:
        """
        生成教学动画 (SVG)。
        返回: {"type": "svg_animation", "url": "/exports/xxx", "title": "..."}
        """
        svg_url = self._generate_svg_animation(subject, topic, description, "animation")
        if svg_url:
            return {"type": "svg_animation", "url": svg_url, "title": f"{topic}动画演示"}
        return {"type": "failed", "url": None, "title": f"{topic}动画"}

    # ──────────────────────────────────────────────
    # 视频生成 API（可灵 / Runway / Pika 等）
    # ──────────────────────────────────────────────

    def _try_video_api(self, subject: str, topic: str, description: str,
                       duration: int) -> Optional[str]:
        """尝试调用视频生成 API，返回文件 URL 或 None"""
        api_key = os.getenv("VIDEO_API_KEY", "")
        api_provider = os.getenv("VIDEO_API_PROVIDER", "").lower()

        if not api_key or not api_provider:
            return None

        prompt = f"教育动画: {subject}课程, {topic}. {description}. 清晰的教学风格, 带文字标注."

        try:
            if api_provider == "kling":
                return self._call_kling_api(api_key, prompt, duration)
            elif api_provider == "zhipu":
                return self._call_zhipu_api(api_key, prompt, duration)
            else:
                warning(f"不支持的视频 API: {api_provider}")
                return None
        except Exception as e:
            error(f"视频 API 调用失败: {e}")
            return None

    def _call_kling_api(self, api_key: str, prompt: str, duration: int) -> Optional[str]:
        """可灵 (Kling) 文生视频 API"""
        # 提交任务
        resp = requests.post(
            "https://api.klingai.com/v1/videos/text2video",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": min(duration, 10),
                "aspect_ratio": "16:9",
                "model": "kling-v1",
            },
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json().get("data", {}).get("task_id")
        if not task_id:
            return None

        # 轮询等待完成 (最多 5 分钟)
        for _ in range(60):
            time.sleep(5)
            status_resp = requests.get(
                f"https://api.klingai.com/v1/videos/text2video/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            status_data = status_resp.json().get("data", {})
            if status_data.get("task_status") == "succeed":
                video_url = status_data.get("task_result", {}).get("videos", [{}])[0].get("url")
                if video_url:
                    return self._download_file(video_url, "mp4")
            elif status_data.get("task_status") == "failed":
                warning(f"可灵视频生成失败: {status_data.get('task_status_msg', '')}")
                return None

        return None

    def _call_zhipu_api(self, api_key: str, prompt: str, duration: int) -> Optional[str]:
        """智谱 CogVideoX 文生视频 API"""
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/videos/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": "cogvideox", "prompt": prompt},
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json().get("id")
        if not task_id:
            return None

        for _ in range(60):
            time.sleep(5)
            status_resp = requests.get(
                f"https://open.bigmodel.cn/api/paas/v4/videos/generations/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            result = status_resp.json()
            if result.get("status") == "success":
                video_url = result.get("video_result", [{}])[0].get("url")
                if video_url:
                    return self._download_file(video_url, "mp4")
            elif result.get("status") == "fail":
                return None

        return None

    # ──────────────────────────────────────────────
    # SVG 动画生成（AI 生成 SVG 代码）
    # ──────────────────────────────────────────────

    def _generate_svg_animation(self, subject: str, topic: str,
                                description: str, anim_type: str) -> Optional[str]:
        """用 AI 生成 SVG+CSS 动画，保存为 HTML 文件"""
        from services.qa_service import qa_service

        type_hint = "教学视频动画" if anim_type == "video" else "交互动画演示"

        prompt = f"""请为{subject}课程的"{topic}"主题生成一个{type_hint}的 SVG 动画代码。

主题描述: {description}

要求:
1. 生成完整的 SVG 代码，包含内联 CSS 动画
2. 使用 <animate>, <animateTransform> 或 CSS @keyframes 实现动画效果
3. 动画应该循环播放，时长 5-10 秒一个周期
4. 包含中文文字标注说明关键概念
5. 颜色鲜明，适合教学（使用蓝色、绿色、橙色等）
6. 使用 viewBox="0 0 800 500" 保证自适应
7. 动画应展示概念的变化过程，不要只是静态图
8. 如果是数学/物理主题，包含公式或图表动画
9. 如果是编程主题，展示代码执行流程动画

只输出 SVG 代码（以 <svg 开头，以 </svg> 结尾），不要有任何其他文字。
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=4000)
            svg_code = self._extract_svg(response)

            if not svg_code:
                warning("AI 未生成有效 SVG 代码")
                return None

            # 包装为 HTML 文件
            html = self._wrap_svg_html(svg_code, f"{topic} - {type_hint}")
            filename = f"animation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(topic.encode()).hexdigest()[:6]}.html"
            filepath = EXPORT_DIR / filename
            filepath.write_text(html, encoding="utf-8")

            info(f"SVG 动画生成成功: {filename}")
            return f"/exports/{filename}"

        except Exception as e:
            error(f"SVG 动画生成失败: {e}")
            return None

    def _extract_svg(self, text: str) -> Optional[str]:
        """从 AI 响应中提取 SVG 代码"""
        # 尝试匹配 <svg ... </svg>
        match = re.search(r'<svg[\s\S]*?</svg>', text, re.IGNORECASE)
        if match:
            return match.group(0)
        # 尝试匹配代码块中的 SVG
        match = re.search(r'```(?:svg|xml|html)?\s*(<svg[\s\S]*?</svg>)\s*```', text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _wrap_svg_html(self, svg_code: str, title: str) -> str:
        """将 SVG 代码包装为独立 HTML 页面"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #0a0f1e;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  font-family: system-ui, -apple-system, sans-serif;
  overflow: hidden;
}}
.svg-wrapper {{
  width: 100%;
  max-width: 900px;
  padding: 20px;
}}
svg {{
  width: 100%;
  height: auto;
  border-radius: 12px;
}}
</style>
</head>
<body>
<div class="svg-wrapper">
{svg_code}
</div>
</body>
</html>"""

    # ──────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────

    def _download_file(self, url: str, ext: str) -> Optional[str]:
        """下载远程文件到 exports/，返回本地 URL"""
        try:
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            filepath = EXPORT_DIR / filename
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            info(f"视频下载成功: {filename}")
            return f"/exports/{filename}"
        except Exception as e:
            error(f"视频下载失败: {e}")
            return None


# 全局单例
video_generation_service = VideoGenerationService()
