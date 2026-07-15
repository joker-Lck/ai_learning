"""
AI 教学图片生成器
优先使用 MiMo API 生成真实图片，降级为 SVG
"""

import re
from datetime import datetime
from pathlib import Path

from core.logger import error, info, warning

# 导出目录
EXPORT_DIR = Path(__file__).parent.parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


class ImageService:
    """教学图片生成服务 — 优先 SparkChain，降级 SVG"""

    def __init__(self):
        info("图片生成服务初始化完成")

    def generate_image_from_suggestion(self, suggestion: str, topic: str,
                                       subject: str, slide_index: int = 0) -> dict:
        """根据图片建议生成教学示意图"""
        try:
            # 1. 优先使用 SparkChain 生成真实图片
            spark_result = self._generate_with_sparkchain(suggestion, topic, subject)
            if spark_result:
                return spark_result

            # 2. 降级：使用 AI 生成 SVG
            svg_code = self._generate_svg(suggestion, topic, subject)

            # 3. 如果 AI 生成失败，使用模板生成
            if not svg_code:
                svg_code = self._generate_template_svg(suggestion, topic, subject)

            # 4. 包装为 HTML 并保存
            html = self._wrap_svg_html(svg_code, f"{subject} - {suggestion}")
            safe_name = re.sub(r'[^\w]', '_', suggestion)[:30]
            filename = f"img_{slide_index}_{safe_name}_{datetime.now().strftime('%H%M%S')}.html"
            filepath = EXPORT_DIR / filename
            filepath.write_text(html, encoding="utf-8")

            url = f"/exports/{filename}"
            info(f"教学图片生成成功(SVG): {filename}")

            return {
                "success": True,
                "svg_code": svg_code,
                "url": url,
                "html_path": str(filepath),
                "type": "svg_image"
            }

        except Exception as e:
            error(f"图片生成失败: {e!s}")
            return self._generate_placeholder(suggestion, topic, subject, slide_index)

    def _generate_with_sparkchain(self, suggestion: str, topic: str, subject: str) -> dict | None:
        """使用 MiMo API 生成真实图片"""
        try:
            from services.spark_client import spark_client

            # 构建图片生成提示词
            prompt = f"{subject}课程{topic}的教学示意图，{suggestion}，清晰美观，教育风格，专业图表"

            # 生成图片
            b64_data = spark_client.generate_image(prompt, width=512, height=512)

            if not b64_data:
                return None

            # 保存为 HTML 文件（包含 base64 图片）
            html = self._wrap_image_html(b64_data, f"{subject} - {suggestion}")
            safe_name = re.sub(r'[^\w]', '_', suggestion)[:30]
            filename = f"img_{safe_name}_{datetime.now().strftime('%H%M%S')}.html"
            filepath = EXPORT_DIR / filename
            filepath.write_text(html, encoding="utf-8")

            url = f"/exports/{filename}"
            info(f"SparkChain 图片生成成功: {filename}")

            return {
                "success": True,
                "url": url,
                "html_path": str(filepath),
                "type": "sparkchain_image"
            }

        except Exception as e:
            warning(f"SparkChain 图片生成失败，降级到 SVG: {e}")
            return None

    def _wrap_image_html(self, b64_data: str, title: str) -> str:
        """将 base64 图片包装为可查看/下载的 HTML 页面"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #060d1f;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
  padding: 20px;
}}
.container {{
  max-width: 1000px;
  width: 100%;
}}
.toolbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
}}
.toolbar h2 {{
  color: #67e8f9;
  font-size: 16px;
}}
.btn {{
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}}
.btn-primary {{
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: white;
}}
.btn-primary:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.image-wrapper {{
  background: rgba(255,255,255,0.02);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 16px;
  text-align: center;
}}
img {{
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}}
</style>
</head>
<body>
<div class="container">
  <div class="toolbar">
    <h2>🖼️ {title}</h2>
    <button class="btn btn-primary" onclick="downloadImage()">⬇ 下载图片</button>
  </div>
  <div class="image-wrapper">
    <img src="data:image/png;base64,{b64_data}" alt="{title}" />
  </div>
</div>
<script>
function downloadImage() {{
  const img = document.querySelector('img');
  const a = document.createElement('a');
  a.href = img.src;
  a.download = '{title.replace(" ", "_")}.png';
  a.click();
}}
</script>
</body>
</html>'''

    def _generate_svg(self, suggestion: str, topic: str, subject: str) -> str | None:
        """使用 AI 生成 SVG 教学示意图"""
        from services.qa_service import qa_service

        prompt = f"""请为{subject}课程的"{topic}"主题生成一个教学示意图的 SVG 代码。

图片描述: {suggestion}

要求:
1. 生成纯 SVG 代码，viewBox="0 0 800 450"
2. 使用清晰的线条、形状和中文文字标注
3. 配色专业美观（蓝色、绿色、橙色等教学风格）
4. 包含标题、关键元素和它们之间的关系
5. 使用圆角矩形、箭头、不同颜色区分元素
6. 所有元素必须在 viewBox 范围内

只输出 SVG 代码（以 <svg 开头，以 </svg> 结尾），不要有其他文字。"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=3000)
            return self._extract_svg(response)
        except Exception as e:
            warning(f"AI SVG 生成失败: {e}")
            return None

    def _extract_svg(self, text: str) -> str | None:
        """从 AI 响应中提取 SVG 代码"""
        if not text:
            return None
        # 匹配 <svg ... </svg>
        match = re.search(r'<svg[\s\S]*?</svg>', text, re.IGNORECASE)
        if match:
            return match.group(0)
        # 匹配代码块中的 SVG
        match = re.search(r'```(?:svg|xml|html)?\s*(<svg[\s\S]*?</svg>)\s*```', text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _generate_template_svg(self, suggestion: str, topic: str, subject: str) -> str:
        """模板生成 SVG（AI 失败时的降级方案）"""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0a1628"/>
      <stop offset="100%" style="stop-color:#1a2a4a"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#06b6d4"/>
      <stop offset="100%" style="stop-color:#3b82f6"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="800" height="450" fill="url(#bg)" rx="12"/>
  
  <!-- 标题区域 -->
  <rect x="200" y="30" width="400" height="50" rx="25" fill="url(#accent)" opacity="0.9"/>
  <text x="400" y="62" text-anchor="middle" fill="white" font-size="20" font-weight="bold" font-family="Microsoft YaHei, sans-serif">{subject} - {topic}</text>
  
  <!-- 主内容区 -->
  <rect x="50" y="100" width="700" height="300" rx="12" fill="white" opacity="0.05" stroke="rgba(6,182,212,0.3)" stroke-width="1"/>
  
  <!-- 核心概念 -->
  <rect x="280" y="130" width="240" height="50" rx="10" fill="url(#accent)" filter="url(#glow)"/>
  <text x="400" y="162" text-anchor="middle" fill="white" font-size="16" font-weight="bold" font-family="Microsoft YaHei, sans-serif">核心概念</text>
  
  <!-- 分支1 -->
  <line x1="340" y1="180" x2="200" y2="230" stroke="#06b6d4" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="100" y="230" width="200" height="45" rx="8" fill="rgba(6,182,212,0.15)" stroke="#06b6d4" stroke-width="1"/>
  <text x="200" y="258" text-anchor="middle" fill="#67e8f9" font-size="14" font-family="Microsoft YaHei, sans-serif">基础知识</text>
  
  <!-- 分支2 -->
  <line x1="400" y1="180" x2="400" y2="230" stroke="#3b82f6" stroke-width="2"/>
  <rect x="300" y="230" width="200" height="45" rx="8" fill="rgba(59,130,246,0.15)" stroke="#3b82f6" stroke-width="1"/>
  <text x="400" y="258" text-anchor="middle" fill="#93c5fd" font-size="14" font-family="Microsoft YaHei, sans-serif">核心原理</text>
  
  <!-- 分支3 -->
  <line x1="460" y1="180" x2="600" y2="230" stroke="#f59e0b" stroke-width="2"/>
  <rect x="500" y="230" width="200" height="45" rx="8" fill="rgba(245,158,11,0.15)" stroke="#f59e0b" stroke-width="1"/>
  <text x="600" y="258" text-anchor="middle" fill="#fcd34d" font-size="14" font-family="Microsoft YaHei, sans-serif">实际应用</text>
  
  <!-- 底部说明 -->
  <rect x="150" y="310" width="500" height="60" rx="8" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
  <text x="400" y="335" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="12" font-family="Microsoft YaHei, sans-serif">{suggestion[:50]}</text>
  <text x="400" y="355" text-anchor="middle" fill="rgba(255,255,255,0.3)" font-size="10" font-family="Microsoft YaHei, sans-serif">AI 教学示意图</text>
  
  <!-- 装饰元素 -->
  <circle cx="70" cy="70" r="20" fill="rgba(6,182,212,0.1)"/>
  <circle cx="730" cy="380" r="15" fill="rgba(59,130,246,0.1)"/>
  <circle cx="750" cy="80" r="10" fill="rgba(245,158,11,0.1)"/>
</svg>'''

    def _generate_placeholder(self, suggestion: str, topic: str,
                              subject: str, slide_index: int) -> dict:
        """生成占位图（最终降级方案）"""
        svg = self._generate_template_svg(suggestion, topic, subject)
        html = self._wrap_svg_html(svg, f"{subject} - {suggestion}")
        filename = f"img_{slide_index}_placeholder_{datetime.now().strftime('%H%M%S')}.html"
        filepath = EXPORT_DIR / filename
        filepath.write_text(html, encoding="utf-8")

        return {
            "success": True,
            "svg_code": svg,
            "url": f"/exports/{filename}",
            "html_path": str(filepath),
            "type": "svg_image",
            "is_placeholder": True
        }

    def _wrap_svg_html(self, svg_code: str, title: str) -> str:
        """将 SVG 包装为可查看/下载的 HTML 页面"""
        return f'''<!DOCTYPE html>
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
  padding: 20px;
}}
.container {{
  max-width: 900px;
  width: 100%;
}}
.toolbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
}}
.toolbar h2 {{
  color: #67e8f9;
  font-size: 16px;
}}
.btn {{
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}}
.btn-primary {{
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: white;
}}
.btn-primary:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.svg-wrapper {{
  background: rgba(255,255,255,0.02);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 16px;
  text-align: center;
}}
svg {{
  width: 100%;
  height: auto;
  border-radius: 8px;
}}
</style>
</head>
<body>
<div class="container">
  <div class="toolbar">
    <h2>📊 {title}</h2>
    <button class="btn btn-primary" onclick="downloadSVG()">⬇ 下载 SVG</button>
  </div>
  <div class="svg-wrapper" id="svgContainer">
    {svg_code}
  </div>
</div>
<script>
function downloadSVG() {{
  const svg = document.querySelector('#svgContainer svg');
  if (!svg) return;
  const blob = new Blob([svg.outerHTML], {{type: 'image/svg+xml'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '{title.replace(" ", "_")}.svg';
  a.click();
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>'''

    def generate_batch_images(self, slides: list, topic: str, subject: str,
                              progress_callback=None) -> dict:
        """批量生成所有幻灯片的配图"""
        results = {}
        total = sum(1 for s in slides if s.get('image_suggestion', '').strip())

        if total == 0:
            return results

        current = 0
        for i, slide in enumerate(slides):
            suggestion = slide.get('image_suggestion', '').strip()
            if suggestion:
                current += 1
                if progress_callback:
                    progress_callback(current, total, f"正在生成第 {i+1} 页配图...")

                result = self.generate_image_from_suggestion(
                    suggestion=suggestion, topic=topic,
                    subject=subject, slide_index=i + 1
                )
                result['slide_index'] = i + 1
                result['suggestion'] = suggestion
                results[i] = result

                if progress_callback:
                    status = "✅" if result['success'] else "⚠️"
                    progress_callback(current, total, f"{status} 第 {i+1} 页配图")

        return results


# 全局单例
image_service = ImageService()
