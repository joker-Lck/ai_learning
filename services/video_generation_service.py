"""
AI 教学视频生成服务
生成带讲解的交互式教学视频（HTML 格式）
支持：自动播放、语音朗读、进度条、下载
"""

import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from core.logger import info, error, warning

EXPORT_DIR = Path(__file__).parent.parent / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


class VideoGenerationService:
    """教学视频生成服务 — 生成带讲解的 HTML 教学视频"""

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
        """生成教学视频 — 始终返回可用结果"""
        try:
            # 1. 使用 AI 生成教学脚本（多个场景）
            scenes = self._generate_script(subject, topic, description)

            # 2. 生成 HTML 视频
            html = self._build_video_html(subject, topic, scenes)

            # 3. 保存文件
            filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(topic.encode()).hexdigest()[:6]}.html"
            filepath = EXPORT_DIR / filename
            filepath.write_text(html, encoding="utf-8")

            url = f"/exports/{filename}"
            info(f"教学视频生成成功: {filename}")

            return {
                "type": "html_video",
                "url": url,
                "title": f"{topic}教学视频",
                "scenes_count": len(scenes),
                "duration_minutes": max(1, len(scenes) * 1)
            }

        except Exception as e:
            error(f"视频生成失败: {e}")
            return self._generate_fallback_video(subject, topic, description)

    def generate_animation(self, subject: str, topic: str, description: str,
                           duration: int = 4) -> Dict:
        """生成教学动画"""
        return self.generate_video(subject, topic, description, duration)

    # ──────────────────────────────────────────────
    # AI 生成教学脚本
    # ──────────────────────────────────────────────

    def _generate_script(self, subject: str, topic: str, description: str) -> List[Dict]:
        """使用 AI 生成多场景教学脚本"""
        from services.qa_service import qa_service
        from core.json_utils import safe_parse_json

        prompt = f"""请为{subject}课程的"{topic}"主题生成一个教学视频脚本，包含多个讲解场景。

主题描述: {description}

要求：
1. 生成 4-6 个场景，每个场景讲解一个知识点
2. 每个场景包含：标题、讲解文字、可视化描述
3. 讲解文字要口语化，适合朗读（每段 50-100 字）
4. 循序渐进，从基础到进阶
5. 最后一个场景做总结

输出严格JSON数组格式：
[
  {{
    "scene_id": 1,
    "title": "场景标题",
    "narration": "讲解文字（口语化，适合朗读）",
    "visual_type": "text|diagram|formula|code|summary",
    "visual_content": "可视化内容（文字/公式/代码片段）",
    "highlight": "重点关键词"
  }}
]

只输出JSON数组，不要其他文字。"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=3000)
            scenes = safe_parse_json(response)

            if scenes and isinstance(scenes, list) and len(scenes) >= 3:
                return scenes
        except Exception as e:
            warning(f"AI 脚本生成失败: {e}")

        # 降级：生成默认脚本
        return self._default_scenes(subject, topic, description)

    def _default_scenes(self, subject: str, topic: str, description: str) -> List[Dict]:
        """默认教学场景（AI 失败时）"""
        return [
            {
                "scene_id": 1,
                "title": f"什么是{topic}",
                "narration": f"同学们好，今天我们来学习{subject}中的{topic}。这是一个非常重要的概念，在实际应用中有广泛的用途。让我们从最基本的概念开始了解。",
                "visual_type": "text",
                "visual_content": f"{topic}\n核心概念介绍",
                "highlight": topic
            },
            {
                "scene_id": 2,
                "title": f"{topic}的基本原理",
                "narration": f"接下来我们来了解{topic}的基本原理。理解这些原理是掌握这个知识点的关键。我们通过图示来帮助大家理解。",
                "visual_type": "diagram",
                "visual_content": f"原理图示\n输入 → 处理 → 输出",
                "highlight": "基本原理"
            },
            {
                "scene_id": 3,
                "title": f"{topic}的应用实例",
                "narration": f"了解了基本原理后，让我们来看一个具体的应用实例。通过实例，我们可以更好地理解{topic}是如何在实际中发挥作用的。",
                "visual_type": "text",
                "visual_content": f"应用实例\n实际场景演示",
                "highlight": "应用实例"
            },
            {
                "scene_id": 4,
                "title": "总结与回顾",
                "narration": f"好的，让我们来总结一下今天学习的内容。{topic}是{subject}中非常重要的知识点，希望大家能够掌握并应用到实际中。",
                "visual_type": "summary",
                "visual_content": f"总结\n1. 基本概念\n2. 核心原理\n3. 实际应用",
                "highlight": "总结"
            }
        ]

    # ──────────────────────────────────────────────
    # 构建 HTML 视频
    # ──────────────────────────────────────────────

    def _build_video_html(self, subject: str, topic: str, scenes: List[Dict]) -> str:
        """构建完整的 HTML 教学视频"""
        scenes_json = json.dumps(scenes, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject} - {topic} 教学视频</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #060d1f;
  color: white;
  font-family: "Microsoft YaHei", system-ui, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}}
.video-container {{
  max-width: 900px;
  width: 100%;
}}
.header {{
  text-align: center;
  margin-bottom: 24px;
}}
.header h1 {{
  font-size: 24px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}}
.header p {{
  color: rgba(255,255,255,0.5);
  font-size: 14px;
}}
.player {{
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  overflow: hidden;
}}
.screen {{
  aspect-ratio: 16/9;
  background: linear-gradient(135deg, #0a1628, #1a2a4a);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}}
.scene-title {{
  font-size: 28px;
  font-weight: bold;
  color: #67e8f9;
  margin-bottom: 16px;
  text-align: center;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.6s ease;
}}
.scene-visual {{
  font-size: 18px;
  color: rgba(255,255,255,0.8);
  text-align: center;
  line-height: 1.8;
  max-width: 600px;
  padding: 20px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.6s ease 0.2s;
}}
.scene-highlight {{
  display: inline-block;
  background: linear-gradient(135deg, rgba(6,182,212,0.2), rgba(59,130,246,0.2));
  border: 1px solid rgba(6,182,212,0.3);
  padding: 4px 12px;
  border-radius: 6px;
  color: #67e8f9;
  font-size: 14px;
  margin-top: 16px;
  opacity: 0;
  transition: all 0.6s ease 0.4s;
}}
.narration-bar {{
  background: rgba(255,255,255,0.03);
  border-top: 1px solid rgba(255,255,255,0.08);
  padding: 16px 20px;
}}
.narration-text {{
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  line-height: 1.6;
  min-height: 48px;
}}
.controls {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(255,255,255,0.02);
  border-top: 1px solid rgba(255,255,255,0.06);
}}
.btn {{
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}}
.btn-play {{
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: white;
}}
.btn-play:hover {{ transform: scale(1.1); }}
.btn-secondary {{
  background: rgba(255,255,255,0.1);
  color: white;
}}
.btn-secondary:hover {{ background: rgba(255,255,255,0.15); }}
.progress-bar {{
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
}}
.progress-fill {{
  height: 100%;
  background: linear-gradient(90deg, #06b6d4, #3b82f6);
  border-radius: 2px;
  transition: width 0.3s;
}}
.time-display {{
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  min-width: 80px;
  text-align: center;
}}
.scene-dots {{
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}}
.dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  cursor: pointer;
  transition: all 0.3s;
}}
.dot.active {{
  background: #06b6d4;
  transform: scale(1.3);
}}
.toolbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}}
.btn-download {{
  padding: 10px 20px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}}
.btn-download:hover {{ opacity: 0.9; transform: translateY(-1px); }}
.visible .scene-title,
.visible .scene-visual,
.visible .scene-highlight {{
  opacity: 1;
  transform: translateY(0);
}}
</style>
</head>
<body>

<div class="video-container">
  <div class="header">
    <h1>🎬 {subject} - {topic}</h1>
    <p id="sceneCount"></p>
  </div>

  <div class="player">
    <div class="screen" id="screen">
      <div class="scene-title" id="sceneTitle"></div>
      <div class="scene-visual" id="sceneVisual"></div>
      <div class="scene-highlight" id="sceneHighlight"></div>
    </div>

    <div class="narration-bar">
      <div class="narration-text" id="narrationText">点击播放按钮开始学习...</div>
    </div>

    <div class="controls">
      <button class="btn btn-secondary" id="btnPrev" onclick="prevScene()">⏮</button>
      <button class="btn btn-play" id="btnPlay" onclick="togglePlay()">▶</button>
      <button class="btn btn-secondary" id="btnNext" onclick="nextScene()">⏭</button>
      <div class="progress-bar" id="progressBar" onclick="seekTo(event)">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <div class="time-display" id="timeDisplay">0:00 / 0:00</div>
      <button class="btn btn-secondary" id="btnVoice" onclick="toggleVoice()">🔊</button>
    </div>
  </div>

  <div class="scene-dots" id="sceneDots"></div>

  <div class="toolbar">
    <div style="color:rgba(255,255,255,0.4);font-size:13px;">
      💡 提示：点击播放按钮自动讲解，支持语音朗读
    </div>
    <button class="btn-download" onclick="downloadVideo()">⬇ 下载视频</button>
  </div>
</div>

<script>
const scenes = {scenes_json};
let currentScene = 0;
let isPlaying = false;
let voiceEnabled = true;
let speechSynth = window.speechSynthesis;
let currentUtterance = null;

// 初始化
function init() {{
  document.getElementById('sceneCount').textContent = `共 ${{scenes.length}} 个知识点 · 预计 ${{scenes.length}} 分钟`;
  
  // 创建场景指示点
  const dotsContainer = document.getElementById('sceneDots');
  scenes.forEach((_, i) => {{
    const dot = document.createElement('div');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.onclick = () => goToScene(i);
    dotsContainer.appendChild(dot);
  }});
  
  showScene(0);
}}

// 显示场景
function showScene(index) {{
  if (index < 0 || index >= scenes.length) return;
  
  currentScene = index;
  const scene = scenes[index];
  const screen = document.getElementById('screen');
  
  // 移除动画类
  screen.classList.remove('visible');
  
  setTimeout(() => {{
    document.getElementById('sceneTitle').textContent = scene.title;
    document.getElementById('sceneVisual').innerHTML = (scene.visual_content || '').replace(/\\n/g, '<br>');
    document.getElementById('sceneHighlight').textContent = scene.highlight || '';
    document.getElementById('narrationText').textContent = scene.narration || '';
    
    // 触发动画
    screen.classList.add('visible');
    
    // 更新进度
    updateProgress();
    
    // 更新指示点
    document.querySelectorAll('.dot').forEach((dot, i) => {{
      dot.className = 'dot' + (i === index ? ' active' : '');
    }});
    
    // 语音朗读
    if (isPlaying && voiceEnabled) {{
      speak(scene.narration);
    }}
  }}, 100);
}}

// 语音朗读
function speak(text) {{
  if (!speechSynth || !text) return;
  speechSynth.cancel();
  
  currentUtterance = new SpeechSynthesisUtterance(text);
  currentUtterance.lang = 'zh-CN';
  currentUtterance.rate = 0.9;
  currentUtterance.pitch = 1;
  
  currentUtterance.onend = () => {{
    if (isPlaying) {{
      setTimeout(() => {{
        if (currentScene < scenes.length - 1) {{
          nextScene();
        }} else {{
          stopPlay();
        }}
      }}, 1000);
    }}
  }};
  
  speechSynth.speak(currentUtterance);
}}

// 播放控制
function togglePlay() {{
  if (isPlaying) {{
    stopPlay();
  }} else {{
    startPlay();
  }}
}}

function startPlay() {{
  isPlaying = true;
  document.getElementById('btnPlay').textContent = '⏸';
  showScene(currentScene);
}}

function stopPlay() {{
  isPlaying = false;
  document.getElementById('btnPlay').textContent = '▶';
  if (speechSynth) speechSynth.cancel();
}}

function prevScene() {{
  if (currentScene > 0) {{
    showScene(currentScene - 1);
  }}
}}

function nextScene() {{
  if (currentScene < scenes.length - 1) {{
    showScene(currentScene + 1);
  }} else {{
    stopPlay();
  }}
}}

function goToScene(index) {{
  showScene(index);
  if (isPlaying) {{
    showScene(index);
  }}
}}

function toggleVoice() {{
  voiceEnabled = !voiceEnabled;
  document.getElementById('btnVoice').textContent = voiceEnabled ? '🔊' : '🔇';
  if (!voiceEnabled && speechSynth) {{
    speechSynth.cancel();
  }}
}}

function seekTo(event) {{
  const bar = document.getElementById('progressBar');
  const rect = bar.getBoundingClientRect();
  const percent = (event.clientX - rect.left) / rect.width;
  const sceneIndex = Math.floor(percent * scenes.length);
  goToScene(Math.max(0, Math.min(sceneIndex, scenes.length - 1)));
}}

function updateProgress() {{
  const percent = ((currentScene + 1) / scenes.length) * 100;
  document.getElementById('progressFill').style.width = percent + '%';
  document.getElementById('timeDisplay').textContent = 
    `${{currentScene + 1}}:${{String(0).padStart(2,'0')}} / ${{scenes.length}}:${{String(0).padStart(2,'0')}}`;
}}

function downloadVideo() {{
  const html = document.documentElement.outerHTML;
  const blob = new Blob(['<!DOCTYPE html>\\n' + html], {{type: 'text/html'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '{topic}_教学视频.html';
  a.click();
  URL.revokeObjectURL(url);
}}

// 键盘控制
document.addEventListener('keydown', (e) => {{
  if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
  if (e.key === 'ArrowLeft') {{ prevScene(); }}
  if (e.key === 'ArrowRight') {{ nextScene(); }}
}});

init();
</script>
</body>
</html>'''

    def _generate_fallback_video(self, subject: str, topic: str, description: str) -> Dict:
        """降级视频生成"""
        scenes = self._default_scenes(subject, topic, description)
        html = self._build_video_html(subject, topic, scenes)
        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_fallback.html"
        filepath = EXPORT_DIR / filename
        filepath.write_text(html, encoding="utf-8")

        return {
            "type": "html_video",
            "url": f"/exports/{filename}",
            "title": f"{topic}教学视频",
            "scenes_count": len(scenes),
            "duration_minutes": len(scenes)
        }


# 全局单例
video_generation_service = VideoGenerationService()
