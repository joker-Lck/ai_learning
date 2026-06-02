"""学习资源生成智能体 - 生成多模态学习资源
支持7种类型:文档、思维导图、题库、视频、动画、代码案例、拓展阅读
集成内容安全检查和防幻觉机制
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from core.logger import info, error, warning, debug
from core.json_utils import safe_parse_json
from services.qa_service import qa_service
from services.content_safety_service import content_safety_service, anti_hallucination_service


def _extract_text_from_resource(resource: Dict) -> str:
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


def _extract_knowledge_points(resource: Dict) -> List[str]:
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
    
    def generate_resources(self, user_id: int, input_data: Dict) -> Dict:
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
                    error(f"生成资源 {resource_type} 失败: {str(e)}")
                    # 继续生成其他资源
            
            # 保存到数据库
            resource_ids = self._save_resources(generated_resources)
            
            result = {
                "resources": generated_resources,
                "resource_ids": resource_ids,
                "count": len(generated_resources),
                "types": list(set([r["type"] for r in generated_resources]))
            }
            
            info(f"资源生成完成,共 {len(generated_resources)} 个")
            return result
            
        except Exception as e:
            error(f"生成学习资源失败: {str(e)}")
            return {
                "success": False,
                "message": f"生成失败: {str(e)}",
                "resources": []
            }
    
    def _check_resource_safety(self, resource: Dict) -> Dict:
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
            error(f"资源安全检查失败: {str(e)}")
            return {"is_safe": True, "violations": []}  # 默认通过,避免阻塞
    
    def _generate_single_resource(self, user_id: int, resource_type: str,
                                  subject: str, topic: str, 
                                  profile: Dict, difficulty: str) -> Optional[Dict]:
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
                          profile: Dict, difficulty: str) -> Dict:
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
            error(f"生成文档失败: {str(e)}")
            return None
    
    def _generate_mindmap(self, subject: str, topic: str,
                         profile: Dict, difficulty: str) -> Dict:
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
            error(f"生成思维导图失败: {str(e)}")
            return None
    
    def _generate_quiz(self, subject: str, topic: str,
                      profile: Dict, difficulty: str) -> Dict:
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
            response = qa_service.call_ai(prompt, max_tokens=2500)
            quiz_data = safe_parse_json(response)
            
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
            error(f"生成题库失败: {str(e)}")
            return None
    
    def _generate_video_script(self, subject: str, topic: str,
                              profile: Dict, difficulty: str) -> Dict:
        """生成教学视频 — 优先调用视频 API 生成真实视频，降级为 SVG 动画"""
        from services.video_generation_service import video_generation_service

        cognitive_style = profile.get("cognitive_style", "visual")

        # 先生成脚本文本
        prompt = f"""请为{subject}课程的"{topic}"主题生成一个简短的教学视频脚本描述（2-3句话），用于视频AI生成的提示词。

学习者认知风格: {cognitive_style}
难度级别: {difficulty}

要求:
1. 描述视频的核心内容和视觉风格
2. 突出关键知识点的可视化展示方式
3. 100字以内

只输出描述文本，不要JSON。
"""
        try:
            description = qa_service.call_ai(prompt, max_tokens=300)
        except Exception:
            description = f"{subject}课程{topic}的教学视频"

        # 调用视频生成服务
        result = video_generation_service.generate_video(
            subject=subject, topic=topic,
            description=description, duration=10
        )

        content_data = {
            "title": f"{topic}教学视频",
            "duration_minutes": 10,
            "scenes": [],
            "key_visuals": [],
            "target_audience": f"{cognitive_style}型学习者",
            "generation_type": result.get("type", "failed"),
            "media_url": result.get("url"),
        }

        return {
            "type": "video",
            "title": result.get("title", f"{topic}教学视频"),
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": content_data,
            "duration_minutes": 10,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _generate_animation_script(self, subject: str, topic: str,
                                  profile: Dict, difficulty: str) -> Dict:
        """生成教学动画 — AI 生成 SVG 交互动画"""
        from services.video_generation_service import video_generation_service

        description = f"{subject}课程{topic}的交互动画演示，难度{difficulty}"
        result = video_generation_service.generate_animation(
            subject=subject, topic=topic,
            description=description, duration=4
        )

        content_data = {
            "title": f"{topic}动画演示",
            "duration_minutes": 4,
            "frames": [],
            "narration_script": "",
            "visual_style": "SVG交互动画",
            "generation_type": result.get("type", "failed"),
            "media_url": result.get("url"),
        }

        return {
            "type": "animation",
            "title": result.get("title", f"{topic}动画演示"),
            "subject": subject,
            "difficulty_level": difficulty,
            "content_data": content_data,
            "duration_minutes": 4,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _generate_code_case(self, subject: str, topic: str,
                           profile: Dict, difficulty: str) -> Dict:
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
            response = qa_service.call_ai(prompt, max_tokens=2500)
            code_data = safe_parse_json(response)
            
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
            error(f"生成代码案例失败: {str(e)}")
            return None
    
    def _generate_reading_material(self, subject: str, topic: str,
                                  profile: Dict, difficulty: str) -> Dict:
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
            response = qa_service.call_ai(prompt, max_tokens=1800)
            reading_data = safe_parse_json(response)
            
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
            error(f"生成阅读材料失败: {str(e)}")
            return None
    
    def _save_resources(self, resources: List[Dict]) -> List[int]:
        """保存资源到主数据库 + RAG 知识库"""
        try:
            from data.db_operations import resource_db
            with resource_db:
                resource_ids = []

                for resource in resources:
                    sql = """
                        INSERT INTO learning_resources
                        (title, resource_type, subject, difficulty_level, content_data, duration_minutes)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    resource_db.cursor.execute(sql, (
                        resource["title"],
                        resource["type"],
                        resource["subject"],
                        resource["difficulty_level"],
                        json.dumps(resource["content_data"], ensure_ascii=False),
                        resource["duration_minutes"]
                    ))
                    resource_ids.append(resource_db.cursor.lastrowid)

                resource_db.conn.commit()

                info(f"成功保存 {len(resource_ids)} 个资源到主数据库")

            # 同步写入 RAG 知识库
            self._save_to_rag(resources)

            return resource_ids

        except Exception as e:
            error(f"保存资源失败: {str(e)}")
            return []

    def _save_to_rag(self, resources: List[Dict]) -> None:
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
                        uploaded_by="ai_agent",
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

    def generate_resource(
        self, resource_type: str, subject: str, topic: str,
        difficulty: str = "intermediate", user_id: int = 0
    ) -> Dict:
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
