"""学习资源生成智能体 - 生成多模态学习资源
支持7种类型:文档、思维导图、题库、视频、动画、代码案例、拓展阅读
集成内容安全检查和防幻觉机制
"""

import json
from datetime import datetime

from core.json_utils import safe_parse_json
from core.logger import debug, error, info, warning
from services.content_safety_service import anti_hallucination_service, content_safety_service
from services.qa_service import qa_service


def _extract_text_from_resource(resource: dict) -> str:
    """从资源中提取纯文本内容，用于 RAG 存储"""
    rtype = resource.get("type", "")
    data = resource.get("content_data", {})

    if rtype == "document":
        sections = data.get("sections", [])
        return "\n\n".join(
            f"## {s.get('heading', '')}\n{s.get('content', '')}" for s in sections
        )
    elif rtype == "quiz":
        questions = data.get("questions", [])
        parts = []
        for q in questions:
            parts.append(f"题目: {q.get('question', '')}")
            if q.get("options"):
                parts.append("选项: " + " | ".join(q["options"]))
            parts.append(f"答案: {q.get('correct_answer', '')}")
            parts.append(f"解析: {q.get('explanation', '')}")
        return "\n".join(parts)
    elif rtype == "mindmap":
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        text_parts = [f"中心: {data.get('title', '')}"]
        for n in nodes:
            text_parts.append(f"节点: {n.get('label', '')}")
        for e in edges:
            text_parts.append(f"关系: {e.get('source', '')} -> {e.get('target', '')}")
        return "\n".join(text_parts)
    elif rtype == "reading":
        return data.get("content", "") or json.dumps(data, ensure_ascii=False)
    else:
        return json.dumps(data, ensure_ascii=False)[:5000]


def _extract_knowledge_points(resource: dict) -> list[str]:
    """从资源中提取知识点列表"""
    data = resource.get("content_data", {})
    points = []

    # 文档类型的知识点
    if "key_concepts" in data:
        points.extend(data["key_concepts"])
    if "knowledge_points" in data:
        points.extend(data["knowledge_points"])

    # 思维导图的节点
    if resource.get("type") == "mindmap":
        for node in data.get("nodes", []):
            label = node.get("label", "")
            if label and label != data.get("title", ""):
                points.append(label)

    # 去重
    return list(dict.fromkeys(points))[:20]


class ResourceAgent:
    """学习资源生成智能体"""

    RESOURCE_TYPES = {
        "document": "课程讲解文档",
        "mindmap": "知识点思维导图",
        "quiz": "练习题目",
        "video": "教学视频脚本",
        "animation": "动画演示脚本",
        "code_case": "代码实操案例",
        "reading": "拓展阅读材料"
    }

    def __init__(self):
        info("学习资源生成智能体初始化完成")

    def generate_resources(self, user_id: int, input_data: dict) -> dict:
        """
        生成多模态学习资源
        
        Args:
            user_id: 用户ID
            input_data: {
                "subject": 学科,
                "topic": 主题,
                "profile": 学生画像,
                "resource_types": 需要的资源类型列表,
                "difficulty": 难度级别
            }
            
        Returns:
            生成的资源列表
        """
        info(f"开始生成学习资源, 用户: {user_id}, 主题: {input_data.get('topic')}")

        try:
            subject = input_data.get("subject", "综合")
            topic = input_data.get("topic", "")
            profile = input_data.get("profile", {})
            resource_types = input_data.get("resource_types", ["document", "quiz", "mindmap"])
            difficulty = input_data.get("difficulty", "intermediate")

            generated_resources = []

            # 并行或串行生成各类资源
            for resource_type in resource_types:
                try:
                    resource = self._generate_single_resource(
                        user_id, resource_type, subject, topic, profile, difficulty
                    )
                    if resource:
                        # 内容安全检查
                        safety_check = self._check_resource_safety(resource)
                        if safety_check["is_safe"]:
                            generated_resources.append(resource)
                            info(f"成功生成资源: {resource_type}")
                        else:
                            warning(f"资源 {resource_type} 安全检查失败: {safety_check['violations']}")
                except Exception as e:
                    error(f"生成资源 {resource_type} 失败: {e!s}")
                    # 继续生成其他资源

            # 保存到数据库
            resource_ids = self._save_resources(generated_resources, user_id)

            result = {
                "resources": generated_resources,
                "resource_ids": resource_ids,
                "count": len(generated_resources),
                "types": list(set([r["type"] for r in generated_resources]))
            }

            info(f"资源生成完成,共 {len(generated_resources)} 个")
            return result

        except Exception as e:
            error(f"生成学习资源失败: {e!s}")
            return {
                "success": False,
                "message": f"生成失败: {e!s}",
                "resources": []
            }

    def _check_resource_safety(self, resource: dict) -> dict:
        """检查资源内容安全性"""
        try:
            # 提取文本内容进行检查
            content_to_check = ""

            if resource["type"] == "document":
                sections = resource.get("content_data", {}).get("sections", [])
                content_to_check = " ".join([s.get("content", "") for s in sections])
            elif resource["type"] == "quiz":
                questions = resource.get("content_data", {}).get("questions", [])
                content_to_check = " ".join([q.get("question", "") + q.get("explanation", "") for q in questions])
            else:
                # 其他类型转换为JSON字符串检查
                content_to_check = json.dumps(resource.get("content_data", {}), ensure_ascii=False)

            if not content_to_check:
                return {"is_safe": True, "violations": []}

            # 执行安全检查
            safety_result = content_safety_service.check_content_safety(content_to_check)

            return safety_result

        except Exception as e:
            error(f"资源安全检查失败: {e!s}")
            return {"is_safe": True, "violations": []}  # 默认通过,避免阻塞

    def _generate_single_resource(self, user_id: int, resource_type: str,
                                  subject: str, topic: str,
                                  profile: dict, difficulty: str) -> dict | None:
        """生成单个资源"""

        if resource_type == "document":
            return self._generate_document(subject, topic, profile, difficulty)
        elif resource_type == "mindmap":
            return self._generate_mindmap(subject, topic, profile, difficulty)
        elif resource_type == "quiz":
            return self._generate_quiz(subject, topic, profile, difficulty)
        elif resource_type == "video":
            return self._generate_video_script(subject, topic, profile, difficulty)
        elif resource_type == "animation":
            return self._generate_animation_script(subject, topic, profile, difficulty)
        elif resource_type == "code_case":
            return self._generate_code_case(subject, topic, profile, difficulty)
        elif resource_type == "reading":
            return self._generate_reading_material(subject, topic, profile, difficulty)
        else:
            error(f"不支持的资源类型: {resource_type}")
            return None

    def _generate_document(self, subject: str, topic: str,
                          profile: dict, difficulty: str) -> dict:
        """生成课程讲解文档"""

        cognitive_style = profile.get("cognitive_style", "visual")
        weak_points = profile.get("weak_points", [])

        prompt = f"""请为{subject}课程的"{topic}"主题生成一份详细的讲解文档。

学生特征:
- 认知风格: {cognitive_style}
- 薄弱点: {', '.join(weak_points[:3]) if weak_points else '无'}
- 难度级别: {difficulty}

要求:
1. 结构清晰,包含:引言、核心概念、详细讲解、实例分析、总结
2. 针对薄弱点进行重点讲解
3. 使用适合{cognitive_style}型学习者的表达方式
4. 长度适中,约800-1200字
5. 使用Markdown格式
6. 确保内容准确,避免绝对化表述
7. 重要知识点提供引用来源

输出JSON格式:
{{
    "title": "文档标题",
    "sections": [
        {{
            "heading": "章节标题",
            "content": "章节内容(Markdown格式)"
        }}
    ],
    "key_points": ["关键点1", "关键点2"],
    "estimated_reading_time": 15,
    "references": ["参考资料1"]
}}
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            doc_data = safe_parse_json(response)

            # 如果解析失败，返回 None
            if not doc_data:
                warning("AI 返回的文档数据无法解析")
                return None

            # 如果返回的是数组，取第一个元素
            if isinstance(doc_data, list) and len(doc_data) > 0:
                info("AI 返回了数组格式，取第一个元素")
                doc_data = doc_data[0] if isinstance(doc_data[0], dict) else {"title": f"{topic}讲解文档", "sections": doc_data}

            if not isinstance(doc_data, dict):
                warning(f"AI 返回的文档数据类型无效: {type(doc_data)}")
                return None

            # 添加引用标注
            if doc_data.get("references"):
                sources = [{"title": ref} for ref in doc_data["references"]]
                doc_data["content_with_citations"] = anti_hallucination_service.add_citations(
                    json.dumps(doc_data["sections"], ensure_ascii=False),
                    sources
                )

            return {
                "type": "document",
                "title": doc_data.get("title", f"{topic}讲解文档"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": doc_data,
                "duration_minutes": doc_data.get("estimated_reading_time", 15),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            error(f"生成文档失败: {e!s}")
            return None

    def _generate_mindmap(self, subject: str, topic: str,
                         profile: dict, difficulty: str) -> dict:
        """生成知识点思维导图"""

        prompt = f"""请为{subject}课程的"{topic}"主题生成一个结构清晰的知识点思维导图。

难度级别: {difficulty}

【严格结构要求】
1. 树状结构固定为3层：根节点 → 一级分支(3-5个) → 二级叶子(每个分支2-4个)
2. 根节点 name 必须是 "{topic}"
3. 一级分支必须是该主题的核心知识模块，使用【名词短语】命名（如"基本概念"、"核心算法"、"应用场景"）
4. 二级叶子必须是具体的知识点，使用简短词语（不超过8个字）
5. 每个节点 name 必须简洁精炼，不要写成句子
6. 不要出现重复或相似的节点名
7. difficulty_marks 中标注的节点名必须与上面的节点名完全一致

输出JSON格式(只输出JSON,不要其他文字):
{{
    "title": "{topic}知识结构",
    "root": {{
        "name": "{topic}",
        "children": [
            {{
                "name": "一级分支名称",
                "children": [
                    {{"name": "知识点1"}},
                    {{"name": "知识点2"}},
                    {{"name": "知识点3"}}
                ]
            }},
            {{
                "name": "一级分支名称",
                "children": [
                    {{"name": "知识点1"}},
                    {{"name": "知识点2"}}
                ]
            }}
        ]
    }},
    "key_concepts": ["核心概念1", "核心概念2", "核心概念3"],
    "difficulty_marks": {{"知识点名称": "hard"}}
}}

注意: 只输出JSON,严格按上述格式,children数组长度必须符合要求。
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            mindmap_data = safe_parse_json(response)

            # 如果解析失败，返回 None
            if not mindmap_data:
                warning("AI 返回的思维导图数据无法解析")
                return None

            # 如果返回的是数组，取第一个元素
            if isinstance(mindmap_data, list) and len(mindmap_data) > 0:
                info("AI 返回了数组格式，取第一个元素")
                mindmap_data = mindmap_data[0] if isinstance(mindmap_data[0], dict) else {"topic": topic, "children": mindmap_data}

            if not isinstance(mindmap_data, dict):
                warning(f"AI 返回的思维导图数据类型无效: {type(mindmap_data)}")
                return None

            # 生成 SVG 思维导图
            svg_code = self._generate_mindmap_svg(mindmap_data, topic)

            # 保存为 HTML 文件
            if svg_code:
                import hashlib
                from pathlib import Path
                EXPORT_DIR = Path(__file__).parent.parent / "exports"
                EXPORT_DIR.mkdir(exist_ok=True)
                html = self._wrap_svg_html(svg_code, f"{topic} - 思维导图")
                filename = f"mindmap_{hashlib.md5(topic.encode()).hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}.html"
                filepath = EXPORT_DIR / filename
                filepath.write_text(html, encoding="utf-8")
                mindmap_data["media_url"] = f"/exports/{filename}"
                mindmap_data["has_svg"] = True

            return {
                "type": "mindmap",
                "title": mindmap_data.get("title", f"{topic}思维导图"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": mindmap_data,
                "duration_minutes": 10,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            error(f"生成思维导图失败: {e!s}")
            return None

    def _generate_mindmap_svg(self, data: dict, topic: str) -> str:
        """将思维导图 JSON 转换为 SVG"""
        try:
            root = data.get("root", {})
            root_name = root.get("name", topic)
            children = root.get("children", [])

            if not children:
                return ""

            # 计算布局
            branch_count = len(children)
            svg_width = 900
            svg_height = max(400, 100 + branch_count * 80)
            center_x = 150
            center_y = svg_height // 2

            svg_parts = [
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}">',
                '<defs>',
                '<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#0a1628"/><stop offset="100%" style="stop-color:#1a2a4a"/></linearGradient>',
                '<linearGradient id="branch" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#06b6d4"/><stop offset="100%" style="stop-color:#3b82f6"/></linearGradient>',
                '</defs>',
                f'<rect width="{svg_width}" height="{svg_height}" fill="url(#bg)" rx="12"/>',
            ]

            # 根节点
            svg_parts.append(f'<rect x="{center_x - 60}" y="{center_y - 20}" width="120" height="40" rx="20" fill="url(#branch)"/>')
            svg_parts.append(f'<text x="{center_x}" y="{center_y + 5}" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Microsoft YaHei, sans-serif">{root_name}</text>')

            # 分支
            branch_spacing = (svg_height - 100) / max(1, branch_count)
            colors = ['#06b6d4', '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444']

            for i, branch in enumerate(children):
                branch_name = branch.get("name", f"分支{i+1}")
                branch_y = 50 + i * branch_spacing + branch_spacing / 2
                branch_x = 350
                color = colors[i % len(colors)]

                # 连接线
                svg_parts.append(f'<line x1="{center_x + 60}" y1="{center_y}" x2="{branch_x - 10}" y2="{branch_y}" stroke="{color}" stroke-width="2" opacity="0.6"/>')

                # 分支节点
                svg_parts.append(f'<rect x="{branch_x - 10}" y="{branch_y - 18}" width="160" height="36" rx="8" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1"/>')
                svg_parts.append(f'<text x="{branch_x + 70}" y="{branch_y + 5}" text-anchor="middle" fill="{color}" font-size="13" font-weight="bold" font-family="Microsoft YaHei, sans-serif">{branch_name}</text>')

                # 子节点
                sub_children = branch.get("children", [])
                for j, sub in enumerate(sub_children):
                    sub_name = sub.get("name", f"知识点{j+1}")
                    sub_x = 600
                    sub_y = branch_y - (len(sub_children) - 1) * 15 + j * 30

                    svg_parts.append(f'<line x1="{branch_x + 150}" y1="{branch_y}" x2="{sub_x - 5}" y2="{sub_y}" stroke="{color}" stroke-width="1" opacity="0.4"/>')
                    svg_parts.append(f'<rect x="{sub_x - 5}" y="{sub_y - 12}" width="140" height="24" rx="6" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>')
                    svg_parts.append(f'<text x="{sub_x + 65}" y="{sub_y + 4}" text-anchor="middle" fill="rgba(255,255,255,0.7)" font-size="11" font-family="Microsoft YaHei, sans-serif">{sub_name}</text>')

            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)

        except Exception as e:
            error(f"生成思维导图SVG失败: {e}")
            return ""

    def _wrap_svg_html(self, svg_code: str, title: str) -> str:
        """将 SVG 包装为可查看/下载的 HTML"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #060d1f; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; font-family: "Microsoft YaHei", system-ui, sans-serif; }}
.container {{ max-width: 1000px; width: 100%; }}
.toolbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 12px 16px; background: rgba(255,255,255,0.05); border-radius: 8px; }}
.toolbar h2 {{ color: #67e8f9; font-size: 16px; }}
.btn {{ padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; background: linear-gradient(135deg, #06b6d4, #3b82f6); color: white; }}
.btn:hover {{ opacity: 0.9; }}
svg {{ width: 100%; height: auto; border-radius: 12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="toolbar">
    <h2>🧠 {title}</h2>
    <button class="btn" onclick="downloadSVG()">⬇ 下载 SVG</button>
  </div>
  {svg_code}
</div>
<script>
function downloadSVG() {{
  const svg = document.querySelector('svg');
  if (!svg) return;
  const blob = new Blob([svg.outerHTML], {{type: 'image/svg+xml'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '{title}.svg';
  a.click();
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>'''

    def _generate_quiz(self, subject: str, topic: str,
                      profile: dict, difficulty: str) -> dict:
        """生成练习题目"""

        weak_points = profile.get("weak_points", [])

        prompt = f"""请为{subject}课程的"{topic}"主题生成一套练习题。

学生薄弱点: {', '.join(weak_points[:3]) if weak_points else '无'}
难度级别: {difficulty}

要求:
1. 包含选择题(5题)、填空题(3题)、解答题(2题)
2. 针对薄弱点增加相关题目
3. 每道题提供详细解析
4. 标注每题的难度和考察知识点
5. 确保答案准确无误

输出JSON格式:
{{
    "title": "{topic}练习题",
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A",
            "explanation": "详细解析",
            "difficulty": "easy/medium/hard",
            "knowledge_point": "考察知识点"
        }}
    ],
    "total_questions": 10,
    "estimated_time": 20
}}
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            info(f"AI 返回的题库原始响应 (前500字): {response[:500] if response else 'None'}")
            quiz_data = safe_parse_json(response)
            info(f"解析后的题库数据类型: {type(quiz_data)}, 内容: {str(quiz_data)[:300] if quiz_data else 'None'}")

            # 如果解析失败，使用降级方案
            if not quiz_data:
                warning("AI 返回的题库数据无法解析，使用降级方案")
                return self._fallback_quiz(subject, topic, difficulty)

            # 如果返回的是数组，转换为对象格式
            if isinstance(quiz_data, list):
                info("AI 返回了数组格式，转换为对象格式")
                quiz_data = {
                    "title": f"{topic}练习题",
                    "questions": quiz_data,
                    "total_questions": len(quiz_data),
                    "estimated_time": 20
                }

            if not isinstance(quiz_data, dict):
                warning(f"AI 返回的题库数据类型无效: {type(quiz_data)}，使用降级方案")
                return self._fallback_quiz(subject, topic, difficulty)

            return {
                "type": "quiz",
                "title": quiz_data.get("title", f"{topic}练习题"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": quiz_data,
                "duration_minutes": quiz_data.get("estimated_time", 20),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            error(f"生成题库失败: {e!s}")
            return None

    def _generate_video_script(self, subject: str, topic: str,
                              profile: dict, difficulty: str) -> dict:
        """生成教学视频 — spark-x 脚本 + TTI 图片 + TTS 语音"""
        from services.spark_client import spark_client

        cognitive_style = profile.get("cognitive_style", "visual")

        # 1. 使用 spark-x 生成视频脚本
        prompt = f"""请为{subject}课程的"{topic}"主题生成一个教学视频脚本。

学习者认知风格: {cognitive_style}
难度级别: {difficulty}

要求：
1. 生成 4-6 个场景，每个场景讲解一个知识点
2. 每个场景包含：标题、讲解文字（50-100字，口语化）、关键要点
3. 循序渐进，从基础到进阶
4. 最后一个场景做总结

输出严格JSON格式：
{{
    "title": "{topic}教学视频",
    "scenes": [
        {{
            "scene_id": 1,
            "title": "场景标题",
            "narration": "讲解文字（口语化）",
            "key_point": "关键要点",
            "image_prompt": "用于生成配图的英文描述"
        }}
    ],
    "total_scenes": 4
}}

只输出JSON，不要其他文字。"""

        try:
            response = spark_client.chat(prompt, max_tokens=3000)
            script_data = safe_parse_json(response)

            if not script_data or not isinstance(script_data, dict):
                warning("AI 视频脚本生成失败，使用降级方案")
                script_data = self._default_video_script(subject, topic)

            # 2. 为每个场景生成配图（TTI API）
            scenes = script_data.get("scenes", [])
            for scene in scenes:
                img_prompt = scene.get("image_prompt", f"{topic} {scene.get('title', '')}")
                img_b64 = spark_client.generate_image(img_prompt, width=512, height=512)
                if img_b64:
                    scene["image_b64"] = img_b64
                    scene["has_image"] = True
                else:
                    scene["has_image"] = False

            # 3. 生成语音（TTS API）
            full_narration = " ".join([s.get("narration", "") for s in scenes])
            audio_data = spark_client.text_to_speech(full_narration[:500])  # 限制长度
            has_audio = audio_data is not None

            content_data = {
                "title": script_data.get("title", f"{topic}教学视频"),
                "duration_minutes": len(scenes) * 2,
                "scenes": scenes,
                "total_scenes": len(scenes),
                "target_audience": f"{cognitive_style}型学习者",
                "generation_type": "video_with_images",
                "has_audio": has_audio,
                "narration_text": full_narration[:500]
            }

            return {
                "type": "video",
                "title": script_data.get("title", f"{topic}教学视频"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": content_data,
                "duration_minutes": len(scenes) * 2,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            error(f"生成视频失败: {e!s}")
            return self._fallback_video(subject, topic, difficulty)

    def _default_video_script(self, subject: str, topic: str) -> dict:
        """默认视频脚本"""
        return {
            "title": f"{topic}教学视频",
            "scenes": [
                {"scene_id": 1, "title": f"什么是{topic}", "narration": f"同学们好，今天我们来学习{subject}中的{topic}。这是一个非常重要的概念。", "key_point": "基本概念", "image_prompt": f"{topic} concept diagram"},
                {"scene_id": 2, "title": f"{topic}的基本原理", "narration": f"接下来我们来了解{topic}的基本原理。", "key_point": "基本原理", "image_prompt": f"{topic} principle diagram"},
                {"scene_id": 3, "title": f"{topic}的应用", "narration": f"了解了基本原理后，让我们来看{topic}的实际应用。", "key_point": "实际应用", "image_prompt": f"{topic} application example"},
                {"scene_id": 4, "title": "总结", "narration": f"好的，让我们来总结一下今天学习的{topic}。", "key_point": "总结回顾", "image_prompt": f"{topic} summary"}
            ],
            "total_scenes": 4
        }

    def _fallback_video(self, subject: str, topic: str, difficulty: str) -> dict:
        """视频降级方案"""
        script = self._default_video_script(subject, topic)
        return {
            "type": "video",
            "title": f"{topic}教学视频",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": {
                "title": f"{topic}教学视频",
                "duration_minutes": 8,
                "scenes": script["scenes"],
                "total_scenes": 4,
                "generation_type": "fallback"
            },
            "duration_minutes": 8,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _generate_animation_script(self, subject: str, topic: str,
                                  profile: dict, difficulty: str) -> dict:
        """生成教学图片（TTI API）"""
        from services.image_service import image_service

        # 使用 TTI API 生成图片
        result = image_service.generate_image_from_suggestion(
            f"{topic}教学示意图", topic, subject
        )

        content_data = {
            "title": f"{topic}教学图片",
            "duration_minutes": 5,
            "description": f"{topic}的教学示意图，帮助理解核心概念",
            "visual_style": "AI生成图片",
            "generation_type": result.get("type", "tti_image"),
            "media_url": result.get("url"),
        }

        return {
            "type": "animation",
            "title": f"{topic}教学图片",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": content_data,
            "duration_minutes": 5,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _generate_code_case(self, subject: str, topic: str,
                           profile: dict, difficulty: str) -> dict:
        """生成代码实操案例"""

        prompt = f"""请为{subject}课程的"{topic}"主题生成一个代码实操案例。

难度级别: {difficulty}

要求:
1. 完整的可运行代码
2. 详细的代码注释
3. 包含需求说明、实现思路、代码实现、运行结果
4. 提供扩展练习建议
5. 确保代码正确性和最佳实践

输出JSON格式:
{{
    "title": "案例标题",
    "description": "案例说明",
    "requirements": ["需求1", "需求2"],
    "implementation_steps": ["步骤1", "步骤2"],
    "code": {{
        "language": "python/java/cpp",
        "filename": "main.py",
        "source_code": "完整代码"
    }},
    "expected_output": "预期输出",
    "exercises": ["扩展练习1", "扩展练习2"],
    "estimated_time": 30
}}
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=2000)
            code_data = safe_parse_json(response)

            # 如果解析失败，使用降级方案
            if not code_data:
                warning("AI 返回的代码案例数据无法解析，使用降级方案")
                return self._fallback_code(subject, topic, difficulty)

            # 如果返回的是数组，取第一个元素
            if isinstance(code_data, list) and len(code_data) > 0:
                info("AI 返回了数组格式，取第一个元素")
                code_data = code_data[0] if isinstance(code_data[0], dict) else {"title": f"{topic}代码案例", "code": code_data}

            if not isinstance(code_data, dict):
                warning(f"AI 返回的代码案例数据类型无效: {type(code_data)}，使用降级方案")
                return self._fallback_code(subject, topic, difficulty)

            return {
                "type": "code_case",
                "title": code_data.get("title", f"{topic}代码案例"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": code_data,
                "duration_minutes": code_data.get("estimated_time", 30),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            error(f"生成代码案例失败: {e!s}")
            return self._fallback_code(subject, topic, difficulty)

    def _generate_reading_material(self, subject: str, topic: str,
                                  profile: dict, difficulty: str) -> dict:
        """生成拓展阅读材料"""

        interest_areas = profile.get("interest_areas", [])

        prompt = f"""请为{subject}课程的"{topic}"主题生成拓展阅读材料。

学生兴趣领域: {', '.join(interest_areas[:3]) if interest_areas else '通用'}
难度级别: {difficulty}

要求:
1. 介绍相关前沿知识或应用场景
2. 结合实际案例
3. 提供延伸阅读推荐
4. 长度适中,约600-800字
5. 提供可靠的参考来源

输出JSON格式:
{{
    "title": "阅读材料标题",
    "content": "正文内容(Markdown格式)",
    "case_studies": ["案例1", "案例2"],
    "further_reading": [
        {{"title": "文章标题", "url": "链接(可选)"}}
    ],
    "estimated_reading_time": 10,
    "references": ["参考文献1", "参考文献2"]
}}
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=1500)
            reading_data = safe_parse_json(response)

            # 如果解析失败，使用降级方案
            if not reading_data:
                warning("AI 返回的阅读材料数据无法解析，使用降级方案")
                return self._fallback_reading(subject, topic, difficulty)

            # 如果返回的是数组，取第一个元素
            if isinstance(reading_data, list) and len(reading_data) > 0:
                info("AI 返回了数组格式，取第一个元素")
                reading_data = reading_data[0] if isinstance(reading_data[0], dict) else {"title": f"{topic}阅读材料", "content": str(reading_data)}

            if not isinstance(reading_data, dict):
                warning(f"AI 返回的阅读材料数据类型无效: {type(reading_data)}，使用降级方案")
                return self._fallback_reading(subject, topic, difficulty)

            # 添加引用
            if reading_data.get("references"):
                sources = [{"title": ref} for ref in reading_data["references"]]
                reading_data["content_with_citations"] = anti_hallucination_service.add_citations(
                    reading_data.get("content", ""),
                    sources
                )

            return {
                "type": "reading",
                "title": reading_data.get("title", f"{topic}拓展阅读"),
                "subject": subject,
                "difficulty_level": difficulty,
                "content_data": reading_data,
                "duration_minutes": reading_data.get("estimated_reading_time", 10),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            error(f"生成阅读材料失败: {e!s}")
            return self._fallback_reading(subject, topic, difficulty)

    def _save_resources(self, resources: list[dict], user_id: int = None) -> list[int]:
        """保存资源到主数据库 + RAG 知识库"""
        try:
            from data.db_operations import resource_db
            with resource_db:
                resource_ids = []

                for resource in resources:
                    sql = """
                        INSERT INTO learning_resources
                        (user_id, title, resource_type, subject, difficulty_level, content_data, duration_minutes, generated_by_agent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    resource_db.cursor.execute(sql, (
                        user_id,
                        resource["title"],
                        resource["type"],
                        resource["subject"],
                        resource["difficulty_level"],
                        json.dumps(resource["content_data"], ensure_ascii=False),
                        resource["duration_minutes"],
                        f"user_{user_id}" if user_id else "system"
                    ))
                    resource_ids.append(resource_db.cursor.lastrowid)

                resource_db.conn.commit()

                info(f"成功保存 {len(resource_ids)} 个资源到主数据库")

            # 同步写入 RAG 知识库
            self._save_to_rag(resources, user_id)

            return resource_ids

        except Exception as e:
            error(f"保存资源失败: {e!s}")
            return []

    def _save_to_rag(self, resources: list[dict], user_id: int = None) -> None:
        """将生成的资源同步写入 RAG 知识库"""
        try:
            from data.rag_knowledge_base import rag_kb

            saved = 0
            for resource in resources:
                try:
                    content_text = _extract_text_from_resource(resource)
                    knowledge_points = _extract_knowledge_points(resource)

                    doc_id = rag_kb.add_document(
                        title=resource.get("title", "未命名资源"),
                        subject=resource.get("subject", "综合"),
                        file_path=f"generated/{resource.get('type', 'unknown')}",
                        file_type="json",
                        content_text=content_text,
                        knowledge_points=knowledge_points,
                        ai_summary=content_text[:200] if content_text else "",
                        uploaded_by=user_id or 0,
                    )
                    if doc_id:
                        saved += 1
                        debug(f"RAG 入库成功: {resource.get('title')} (doc_id={doc_id})")
                except Exception as e:
                    warning(f"单条资源写入 RAG 失败: {e}")

            if saved:
                info(f"已同步 {saved}/{len(resources)} 条资源到 RAG 知识库")
        except Exception as e:
            warning(f"RAG 知识库写入失败（不影响主流程）: {e}")

    # ──────────────────────────────────────────────
    # 降级方案（AI 生成失败时使用）
    # ──────────────────────────────────────────────

    def _fallback_quiz(self, subject: str, topic: str, difficulty: str) -> dict:
        """题库降级方案"""
        return {
            "type": "quiz",
            "title": f"{topic}练习题",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": {
                "title": f"{topic}练习题",
                "questions": [
                    {"id": 1, "type": "multiple_choice", "question": f"以下关于{topic}的说法，正确的是？",
                     "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
                     "answer": "A", "explanation": f"这是{topic}的基础概念", "difficulty": "easy", "knowledge_point": topic},
                    {"id": 2, "type": "fill_blank", "question": f"{topic}的核心要素包括____",
                     "answer": "核心要素", "explanation": f"考察{topic}的基本定义", "difficulty": "medium", "knowledge_point": topic},
                    {"id": 3, "type": "essay", "question": f"请简述{topic}的基本原理和应用场景",
                     "answer": f"{topic}是{subject}中的重要概念...", "explanation": "综合考察", "difficulty": "hard", "knowledge_point": topic}
                ],
                "total_questions": 3,
                "estimated_time": 15
            },
            "duration_minutes": 15,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _fallback_code(self, subject: str, topic: str, difficulty: str) -> dict:
        """代码案例降级方案"""
        return {
            "type": "code_case",
            "title": f"{topic}代码案例",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": {
                "title": f"{topic}代码案例",
                "description": f"通过代码演示{topic}的核心概念",
                "requirements": [f"理解{topic}的基本原理", "能够运行并理解代码"],
                "implementation_steps": ["导入必要的库", "定义核心函数", "运行示例"],
                "code": {"language": "python", "filename": "demo.py",
                         "source_code": f"# {topic} 示例代码\n# {subject}课程\n\nprint('Hello, {topic}!')\n\n# TODO: 添加{topic}的核心实现"},
                "expected_output": f"Hello, {topic}!",
                "exercises": [f"修改代码实现{topic}的扩展功能"],
                "estimated_time": 30
            },
            "duration_minutes": 30,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _fallback_reading(self, subject: str, topic: str, difficulty: str) -> dict:
        """阅读材料降级方案"""
        return {
            "type": "reading",
            "title": f"{topic}拓展阅读",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": {
                "title": f"{topic}拓展阅读",
                "content": f"# {topic}\n\n{topic}是{subject}中的重要概念。本文将介绍其基本原理和实际应用。\n\n## 基本概念\n\n{topic}的核心思想是...\n\n## 应用场景\n\n在实际应用中，{topic}可以用于...\n\n## 总结\n\n通过学习{topic}，我们可以更好地理解{subject}的核心知识。",
                "case_studies": [f"{topic}在实际项目中的应用"],
                "further_reading": [{"title": f"{topic}深入学习", "url": ""}],
                "estimated_reading_time": 10,
                "references": [f"{subject}教材"]
            },
            "duration_minutes": 10,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _fallback_animation(self, subject: str, topic: str, difficulty: str) -> dict:
        """动画降级方案 — 生成图片"""
        from services.image_service import image_service
        result = image_service.generate_image_from_suggestion(
            f"{topic}教学示意图", topic, subject
        )
        return {
            "type": "animation",
            "title": f"{topic}教学图片",
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": {
                "title": f"{topic}教学图片",
                "description": f"{topic}的教学示意图",
                "media_url": result.get("url"),
                "generation_type": "svg_image"
            },
            "duration_minutes": 5,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def generate_resource(
        self, resource_type: str, subject: str, topic: str,
        difficulty: str = "intermediate", user_id: int = 0
    ) -> dict:
        """单类型资源生成便捷方法（供 stream.py 使用）"""
        try:
            resource = self._generate_single_resource(
                user_id, resource_type, subject, topic, {}, difficulty
            )
            if resource:
                # 同步写入 RAG
                self._save_to_rag([resource])
                return {"success": True, "data": resource}
            return {"success": False, "message": f"生成 {resource_type} 失败"}
        except Exception as e:
            error(f"生成资源异常 [{resource_type}]: {e}")
            return {"success": False, "message": str(e)}


# 模块级单例
resource_agent = ResourceAgent()
