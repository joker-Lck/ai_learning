"""AI 教学图片生成器 - 基于 Kimi AI 生成 SVG 教学示意图"""

import os
import io
import re
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class ImageService:
    """教学图片生成服务"""
    
    def __init__(self):
        """初始化客户端"""
        api_key = os.getenv('KIMI_API_KEY', '')
        base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        # 确保图片目录存在
        self.images_dir = "generated_images"
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
    
    def generate_image_from_suggestion(self, suggestion, topic, subject, slide_index=0):
        """根据图片建议生成教学示意图"""
        try:
            # 1. 使用 Kimi 生成 SVG 代码
            svg_code = self._generate_svg(suggestion, topic, subject)
            
            if not svg_code:
                return {"success": False, "error": "SVG 生成失败"}
            
            # 2. 转换为 PNG
            png_data = self._svg_to_png(svg_code)
            
            if not png_data:
                return {"success": False, "error": "PNG 转换失败"}
            
            # 3. 保存 PNG 文件
            safe_name = re.sub(r'[^\w\u4e00-\u9fa5]', '_', suggestion)[:30]
            png_filename = f"slide_{slide_index}_{safe_name}_{datetime.now().strftime('%H%M%S')}.png"
            png_path = os.path.join(self.images_dir, png_filename)
            
            with open(png_path, 'wb') as f:
                f.write(png_data)
            
            return {
                "success": True,
                "svg_code": svg_code,
                "png_path": png_path,
                "png_data": png_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_svg(self, suggestion, topic, subject):
        """使用 Kimi 生成 SVG 教学示意图"""
        svg_prompt = f"""你是专业的教学图示设计师。请根据以下信息生成一个清晰、美观的教学示意图（SVG 格式）。

课程主题：{topic}
学科：{subject}
图片描述：{suggestion}

要求：
1. 生成纯 SVG 代码，不要使用外部资源
2. 图片尺寸为 800x400 像素（viewBox="0 0 800 400"）
3. 使用清晰的线条、形状和文字，配色专业美观
4. 文字使用中文，字体大小适中（18-24px）
5. 如果是数据结构图，要展示元素之间的关系（箭头、连线等）
6. 如果是流程图，要清晰展示流程步骤
7. 所有元素必须在 viewBox 范围内，布局合理
8. 使用圆角矩形、箭头、不同颜色区分元素

请严格按照以下格式输出（只输出 SVG 代码，不要有其他文字）：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#ffffff" rx="10"/>
  <!-- 你的图示内容 -->
</svg>
```

现在请生成 "{suggestion}" 的 SVG 图示。"""

        try:
            response = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[{"role": "user", "content": svg_prompt}],
                temperature=0.7,
                max_tokens=3000,
                timeout=60
            )
            
            content = response.choices[0].message.content
            
            # 提取 SVG 代码
            svg_match = re.search(r'```svg\s*(.*?)\s*```', content, re.DOTALL)
            if svg_match:
                return svg_match.group(1).strip()
            
            # 尝试直接查找 SVG 标签
            svg_start = content.find('<svg')
            svg_end = content.find('</svg>')
            if svg_start >= 0 and svg_end > svg_start:
                return content[svg_start:svg_end + 6].strip()
            
            return None
            
        except Exception as e:
            print(f"SVG 生成失败：{str(e)}")
            return None
    
    def _svg_to_png(self, svg_code):
        """将 SVG 代码转换为 PNG 数据"""
        try:
            # 方法1：尝试使用 cairosvg（推荐）
            try:
                import cairosvg
                png_data = cairosvg.svg2png(bytestring=svg_code.encode('utf-8'))
                return png_data
            except ImportError:
                pass
            
            # 方法2：使用 svglib + reportlab
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as f:
                    f.write(svg_code)
                    temp_svg = f.name
                
                drawing = svg2rlg(temp_svg)
                png_data = renderPM.drawToString(drawing, fmt='PNG')
                os.unlink(temp_svg)
                return png_data
            except ImportError:
                pass
            
            # 方法3：降级方案 - 使用 Pillow 创建简单示意图
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                img = Image.new('RGB', (800, 400), color='white')
                draw = ImageDraw.Draw(img)
                
                # 尝试加载字体
                try:
                    font = ImageFont.truetype("msyh.ttc", 24)
                    font_title = ImageFont.truetype("msyh.ttc", 28)
                except:
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
                        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
                    except:
                        font = ImageFont.load_default()
                        font_title = font
                
                # 绘制圆角矩形边框
                draw.rounded_rectangle([(20, 20), (780, 380)], radius=20, outline='#4a90d9', width=3)
                draw.rounded_rectangle([(25, 25), (775, 375)], radius=18, outline='#e0e0e0', width=1)
                
                # 标题
                title = "📊 " + suggestion[:20]
                draw.text((400, 140), title, fill='#333333', font=font_title, anchor="mm")
                
                # 提示文字
                hint = "提示：安装 cairosvg 可生成精美 SVG 示意图"
                draw.text((400, 200), hint, fill='#666666', font=font, anchor="mm")
                
                hint2 = "pip install cairosvg"
                draw.text((400, 240), hint2, fill='#999999', font=font, anchor="mm")
                
                img_data = io.BytesIO()
                img.save(img_data, format='PNG')
                return img_data.getvalue()
            except Exception as e:
                print(f"降级方案失败：{str(e)}")
                return None
            
        except Exception as e:
            print(f"SVG 转 PNG 失败：{str(e)}")
            return None
    
    def generate_batch_images(self, slides, topic, subject, progress_callback=None):
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
                    progress_callback(current, total, f"正在生成第 {i+1} 页配图：{suggestion[:20]}...")
                
                result = self.generate_image_from_suggestion(
                    suggestion=suggestion,
                    topic=topic,
                    subject=subject,
                    slide_index=i + 1
                )
                result['slide_index'] = i + 1
                result['suggestion'] = suggestion
                results[i] = result
                
                if progress_callback:
                    if result['success']:
                        progress_callback(current, total, f"✅ 第 {i+1} 页配图生成成功")
                    else:
                        progress_callback(current, total, f"⚠️ 第 {i+1} 页配图生成失败：{result.get('error', '未知错误')}")
        
        return results
