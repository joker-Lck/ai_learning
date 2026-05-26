"""动画生成服务模块 - 使用 SVG + CSS 动画生成教学动画"""

import json
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class AnimationService:
    """教学动画生成服务"""
    
    def __init__(self):
        """初始化客户端"""
        api_key = os.getenv('KIMI_API_KEY', '')
        base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate_animations_for_courseware(self, topic, subject, slides, requirements=""):
        """根据课件内容生成配套动画"""
        try:
            # 构建提示词
            animation_prompt = f"""你是专业的教学设计动画师。请根据以下课件内容，判断是否需要添加教学动画来辅助理解。

课程主题: {topic}
学科: {subject}
用户需求: {requirements if requirements else '无特殊要求'}

课件内容（前 3 页）:
{json.dumps(slides[:3] if len(slides) > 3 else slides, ensure_ascii=False, indent=2)}

要求：
1. 如果课件中有需要动画辅助理解的知识点（如物理过程、数学变化、化学实验等），请生成 1-2 个简单的 SVG 动画
2. 如果课件内容不需要动画（如纯文字理论、历史事件等），请返回空数组
3. 动画应该是简单的 SVG + CSS/SMIL 动画，时长 3-5 秒
4. 动画必须使用纯 SVG 代码，不要使用外部资源
5. 动画应包含文字说明，方便学生理解
6. 动画应该与对应的幻灯片页面关联（related_slide_index）

请严格按照以下 JSON 格式输出：
{{
    "animations": [
        {{
            "title": "动画标题",
            "description": "动画说明（描述这个动画展示什么）",
            "related_slide_index": 关联的幻灯片页码（从 1 开始，0 表示无关联）,
            "svg_code": "完整的 SVG 代码（必须是可以直接在浏览器中播放的完整 SVG，包含<svg>标签）",
            "animation_type": "类型（如：process / diagram / demonstration / experiment）"
        }}
    ]
}}

注意：
- 只输出 JSON，不要有任何其他文字
- SVG 代码必须完整且有效
- SVG 应该使用 viewBox 属性保证自适应大小
- 动画使用 <animate>, <animateTransform>, 或 CSS @keyframes
- 颜色应该鲜明且适合教学场景

现在请生成动画。"""

            response = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[{"role": "user", "content": animation_prompt}],
                temperature=0.7,
                max_tokens=4000,
                timeout=60
            )
            
            # 解析响应
            content = response.choices[0].message.content

            # 尝试提取 JSON（AI 可能添加额外文字）
            from core.json_utils import safe_parse_json
            animation_data = safe_parse_json(content)
            if not animation_data:
                print(f"⚠️ 动画 JSON 解析失败，返回空列表")
                return []
            
            animations = animation_data.get("animations", [])
            
            if animations:
                print(f"✅ 成功生成 {len(animations)} 个教学动画")
            else:
                print("ℹ️ 课件内容不需要动画辅助")
            
            return animations
            
        except Exception as e:
            print(f"❌ 生成动画失败：{str(e)}")
            return []
    
    def generate_html_animation(self, svg_code, title="教学动画", auto_play=False):
        """生成独立的 HTML 动画文件"""
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 30px;
            max-width: 900px;
            width: 100%;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 20px;
        }}
        .svg-container {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background: #fafafa;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 400px;
        }}
        .controls {{
            margin-top: 20px;
            text-align: center;
        }}
        button {{
            background: #1e88e5;
            color: white;
            border: none;
            padding: 10px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s;
        }}
        button:hover {{
            background: #1565c0;
            transform: scale(1.05);
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .info {{
            text-align: center;
            color: #666;
            margin-top: 15px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="svg-container">
            {svg_code}
        </div>
        <div class="controls">
            <button onclick="restartAnimation()" id="playBtn">🔄 重新播放</button>
            <button onclick="togglePause()" id="pauseBtn">⏸️ 暂停</button>
        </div>
        <div class="info">
            💡 提示：动画将循环播放，点击按钮可以控制播放
        </div>
    </div>
    
    <script>
        let isPaused = false;
        
        function restartAnimation() {{
            var svg = document.querySelector('svg');
            if (svg) {{
                // 重新加载 SVG 以重置动画
                var svgHTML = svg.outerHTML;
                svg.outerHTML = svgHTML;
            }}
            isPaused = false;
            document.getElementById('pauseBtn').textContent = '⏸️ 暂停';
        }}
        
        function togglePause() {{
            var svg = document.querySelector('svg');
            if (!svg) return;
            
            isPaused = !isPaused;
            var btn = document.getElementById('pauseBtn');
            
            if (isPaused) {{
                svg.pauseAnimations();
                btn.textContent = '▶️ 继续';
            }} else {{
                svg.unpauseAnimations();
                btn.textContent = '⏸️ 暂停';
            }}
        }}
        
        // 自动播放（如果启用）
        window.onload = function() {{
            {f'restartAnimation();' if auto_play else ''}
        }};
    </script>
</body>
</html>"""
        
        return html_template
    
    def svg_to_gif(self, svg_code, output_path=None, duration=3, fps=10):
        """将 SVG 动画转换为 GIF"""
        try:
            if output_path is None:
                output_path = f"animation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif"
            
            html_content = self.generate_html_animation(svg_code, "Animation", auto_play=True)
            html_output = output_path.replace('.gif', '.html')
            with open(html_output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML 动画文件生成成功：{html_output}")
            return html_output
        except Exception as e:
            print(f"❌ 动画文件生成失败：{str(e)}")
            return None
