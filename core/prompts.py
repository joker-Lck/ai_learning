"""AI 提示词模块
包含课件生成、学生画像构建等提示词
"""


class ProfilePrompts:
    """学生画像构建相关提示词"""
    
    @staticmethod
    def build_extraction_prompt(conversation_log, basic_info, existing_profile):
        """构建从对话中提取画像特征的提示词"""
        
        conversation_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation_log[-10:]])
        
        return f"""请基于以下对话和基本信息,提取学生的多维度学习画像特征。

对话历史:
{conversation_text}

基本信息:
{basic_info}

已有画像(如有):
{existing_profile}

请提取以下维度的特征:
1. knowledge_base: 知识基础水平(beginner/intermediate/advanced)和已掌握的主题列表
2. cognitive_style: 认知风格(visual视觉型/auditory听觉型/kinesthetic动觉型)
3. learning_goals: 学习目标列表(如"通过考试"、"提升技能"等)
4. weak_points: 薄弱知识点或易错点列表
5. interest_areas: 兴趣领域列表
6. preferred_resources: 偏好的学习资源类型(document/video/quiz/code_case等)
7. major: 专业(如有)
8. grade_level: 年级(如有)

输出JSON格式(只输出JSON,不要其他文字):
{{
    "knowledge_base": {{
        "level": "beginner/intermediate/advanced",
        "topics": ["主题1", "主题2"]
    }},
    "cognitive_style": "visual/auditory/kinesthetic",
    "learning_goals": ["目标1", "目标2"],
    "weak_points": ["薄弱点1", "薄弱点2"],
    "interest_areas": ["兴趣1", "兴趣2"],
    "preferred_resources": ["document", "video"],
    "major": "专业名称",
    "grade_level": "年级",
    "summary": "用Markdown格式撰写的学生画像综合分析报告。包含：## 学生概况（基本信息一句话总结）、## 学习特征分析（认知风格与学习偏好）、## 知识掌握评估（基础水平与薄弱环节）、## 个性化建议（针对该学生的3-5条具体学习建议）。内容要专业、有温度、有针对性，约300-500字。"
}}

注意:
- 如果某个维度无法从对话中提取,使用空字符串或空数组
- 确保输出是有效的JSON格式
- 只输出JSON,不要有任何解释性文字
"""


class CoursewarePrompts:
    """课件生成相关提示词"""
    
    @staticmethod
    def get_identify_prompt(topic, requirements_text, rag_context=None):
        """获取学科识别和大纲生成提示词"""
        if rag_context:
            return f"""请根据主题'{topic}'，自动识别该课程所属的学科（如：数学、物理、语文、英语、历史、地理、化学、生物、政治等）。

以下是从知识库中检索到的相关教学资料，请优先参考这些内容：
{rag_context}

具体要求：
{requirements_text}

请严格按照以下 JSON 格式输出（不要添加任何其他说明）：
{{
    "subject": "学科名称",
    "outline": "简要教案：1.教学目标 2.教学过程 3.教学方法 4.课堂活动 5.课后作业"
}}

注意：只输出 JSON，不要有任何其他文字。"""
        else:
            return f"""请根据主题'{topic}'，自动识别该课程所属的学科（如：数学、物理、语文、英语、历史、地理、化学、生物、政治等）。

具体要求：
{requirements_text}

请严格按照以下 JSON 格式输出（不要添加任何其他说明）：
{{
    "subject": "学科名称",
    "outline": "简要教案：1.教学目标 2.教学过程 3.教学方法 4.课堂活动 5.课后作业"
}}

注意：只输出 JSON，不要有任何其他文字。"""
    
    @staticmethod
    def get_ppt_prompt(subject, topic, requirements_text, fast_mode=True):
        """获取 PPT 课件结构生成提示词
        
        参数：
        - subject: 学科
        - topic: 主题
        - requirements_text: 需求描述
        - fast_mode: 是否快速模式（默认 True）
        """
        if fast_mode:
            # 快速模式：精简版课件
            return f"""你是一位专业的 PPT 课件设计师。请为{subject}课程'{topic}'设计一个简洁、专业的 PPT 课件。

要求：
1. 总共 8-10 页幻灯片（精简版，提高生成速度）
2. 包含：封面、目录、教学目标、知识点讲解（3-4页）、典型例题、课堂小结
3. 每页包含明确的标题和 2-4 个要点（精简内容）
4. 结合以下用户需求：{requirements_text}

【模板设计】
根据学科和主题，自主选择以下一种模板风格：
- tech: 科技风格（深蓝渐变背景、发光装饰、现代感强，适合计算机/AI/数学等）
- edu: 教育风格（暖色调、书本元素、温馨感，适合语文/英语/历史等）
- nature: 自然风格（绿色系、植物元素、清新感，适合生物/地理/环境等）
- minimal: 简约风格（黑白灰、极简线条、高级感，适合物理/化学等理科）
- business: 商务风格（金色点缀、专业严谨，适合经济学/管理学等）

【颜色方案】
为每个模板风格选择合适的配色：
- tech: 主色#0a192f 辅色#64ffda 强调色#00d4ff
- edu: 主色#5b2c6f 辅色#f39c12 强调色#e74c3c
- nature: 主色#27ae60 辅色#2ecc71 强调色#f1c40f
- minimal: 主色#2c3e50 辅色#95a5a6 强调色#e74c3c
- business: 主色#1a1a2e 辅色#c9a227 强调色#d4af37

【装饰元素】
为每页添加简单的装饰元素（根据模板风格选择）：
- 封面：添加简单几何图形
- 目录页：使用编号列表
- 内容页：添加页眉装饰条
- 结尾页：简洁结束页面

请严格按照以下 JSON 格式输出（不要添加任何其他说明）：
{{
    "template_style": "模板风格（tech/edu/nature/minimal/business）",
    "theme": {{
        "primary_color": "主色调（十六进制颜色码）",
        "secondary_color": "辅助色（十六进制颜色码）",
        "accent_color": "强调色（十六进制颜色码）",
        "bg_color": "背景色（十六进制颜色码）",
        "text_color": "正文文字颜色（十六进制颜色码）"
    }},
    "slides": [
        {{
            "title": "页面标题",
            "subtitle": "副标题或说明",
            "content": ["要点 1", "要点 2", "要点 3"],
            "layout": "布局类型（title_only / title_content / two_column / title_image / section_divider）",
            "background": {{
                "type": "背景类型（gradient / solid / dark_gradient）",
                "colors": ["#颜色 1", "#颜色 2"]
            }},
            "decorations": [],
            "image_suggestion": "",
            "notes": "演讲者备注（可选）"
        }}
    ]
}}

注意：
1. 只输出 JSON，不要有任何其他文字
2. decorations 设为空数组 [] 以简化装饰
3. image_suggestion 设为空字符串 "" 跳过图片生成
4. content 控制在 2-4 个要点

现在请生成精简版课件。"""
        else:
            # 标准模式：完整版课件
            return f"""你是一位专业的 PPT 课件设计师。请为{subject}课程'{topic}'设计一个美观、专业的 PPT 课件。

要求：
1. 总共 10-15 页幻灯片
2. 包含：封面、目录、教学目标、重点难点、知识点讲解（分多页）、典型例题、课堂小结、课后作业
3. 每页包含明确的标题和 3-5 个要点
4. 结合以下用户需求：{requirements_text}

【模板设计】
根据学科和主题，自主选择以下一种模板风格：
- tech: 科技风格（深蓝渐变背景、发光装饰、现代感强，适合计算机/AI/数学等）
- edu: 教育风格（暖色调、书本元素、温馨感，适合语文/英语/历史等）
- nature: 自然风格（绿色系、植物元素、清新感，适合生物/地理/环境等）
- minimal: 简约风格（黑白灰、极简线条、高级感，适合物理/化学等理科）
- business: 商务风格（金色点缀、专业严谨，适合经济学/管理学等）

【颜色方案】
为每个模板风格选择合适的配色：
- tech: 主色#0a192f 辅色#64ffda 强调色#00d4ff
- edu: 主色#5b2c6f 辅色#f39c12 强调色#e74c3c
- nature: 主色#27ae60 辅色#2ecc71 强调色#f1c40f
- minimal: 主色#2c3e50 辅色#95a5a6 强调色#e74c3c
- business: 主色#1a1a2e 辅色#c9a227 强调色#d4af37

【装饰元素】
为每页添加以下装饰元素（根据模板风格选择）：
- 封面：添加装饰性几何图形（圆形、三角形、线条等），营造氛围感
- 目录页：使用编号卡片式设计
- 内容页：添加页眉装饰条、侧边装饰线、圆点装饰
- 过渡页：使用全背景色+居中大文字
- 结尾页：简洁有力的结束页面

请严格按照以下 JSON 格式输出（不要添加任何其他说明）：
{{
    "template_style": "模板风格（tech/edu/nature/minimal/business）",
    "theme": {{
        "primary_color": "主色调（十六进制颜色码）",
        "secondary_color": "辅助色（十六进制颜色码）",
        "accent_color": "强调色（十六进制颜色码）",
        "bg_color": "背景色（十六进制颜色码）",
        "text_color": "正文文字颜色（十六进制颜色码）"
    }},
    "slides": [
        {{
            "title": "页面标题",
            "subtitle": "副标题或说明",
            "content": ["要点 1", "要点 2", "要点 3"],
            "layout": "布局类型（title_only / title_content / two_column / title_image / section_divider）",
            "background": {{
                "type": "背景类型（gradient / solid / dark_gradient）",
                "colors": ["#颜色 1", "#颜色 2"]
            }},
            "decorations": [
                {{"type": "circle", "position": "top-right", "size": "large"}},
                {{"type": "line", "position": "bottom", "width": "full"}}
            ],
            "image_suggestion": "图片建议描述（要具体详细。如果没有则为空字符串）",
            "notes": "演讲者备注（可选）"
        }}
    ]
}}

注意：只输出 JSON，不要有任何其他文字。"""
    
    @staticmethod
    def get_refine_prompt(topic, subject, slides_json, feedback):
        """获取基于反馈调整课件的提示词"""
        return f"""你是专业的课件设计师。请根据以下反馈重新调整课件。

原始主题：{topic}
学科：{subject}

原始课件内容：
{slides_json}

用户反馈：
{feedback}

请生成调整后的 JSON 格式课件（格式与之前相同）。

注意：只输出 JSON，不要有其他文字。"""


class AnalysisPrompts:
    """学情分析相关提示词"""
    
    @staticmethod
    def get_analysis_prompt(target_info, data_summary, file_info=""):
        """获取学情分析报告生成提示词"""
        return f"""你是一位专业的教育数据分析师。请根据以下数据和信息，生成一份详细的学情分析报告。

{target_info}

{data_summary}
{file_info}

请生成包含以下内容的报告：
1. 📊 **整体情况概览**（包括平均分、优秀率、及格率等关键指标）
2. 📈 **成绩分布分析**（分数段统计、正态分布分析）
3. 🎯 **知识点掌握情况**（优势知识点、薄弱知识点 TOP5）
4. 👥 **学生分层分析**（学优生、中等生、学困生比例及特点）
5. 📉 **典型问题分析**（错误率高的题目类型和原因）
6. 💡 **个性化教学建议**（针对不同层次学生的具体建议）
7. 📋 **后续教学计划**（重点讲解内容、练习安排）

要求：数据可视化呈现，使用图表、表格等形式，语言简洁专业。"""


class DocumentAnalysisPrompts:
    """文档分析相关提示词"""
    
    @staticmethod
    def get_courseware_analysis_prompt(file_list):
        """获取课件解析提示词"""
        return f"""你是一位专业的教学内容分析师。请分析以下上传的教学资料，提取关键信息。

上传的文件列表：
{file_list}

请完成以下任务：
1. 📚 **知识点提炼**（列出核心概念、重点难点）
2. 🎯 **教学目标**（知识目标、能力目标、素养目标）
3. 📝 **典型例题**（提供 3-5 道代表性题目及解析）
4. 💡 **教学建议**（推荐的教学方法、活动设计）
5. ⏰ **课时安排**（建议学习时长、进度规划）
6. 🔗 **拓展资源**（相关知识点链接、延伸阅读材料）

要求：结构清晰，语言专业，适合教师直接使用。"""
    
    @staticmethod
    def get_knowledge_base_analysis_prompt(doc_list):
        """获取知识库文档分析提示词"""
        return f"""你是一位专业的知识管理专家。请分析以下上传到知识库的文档，完成以下任务：

文档列表：
{doc_list}

请提供：
1. 📋 **文档分类建议**（按学科、难度、用途等维度）
2. 🎯 **核心知识点提取**（从所有文档中提取关键知识点）
3. 🔗 **知识关联分析**（文档之间的关联性和互补性）
4. 💡 **使用建议**（如何在教学中有效利用这些资源）
5. 📊 **知识结构图**（建议的知识组织方式）

要求：结构清晰，便于教师快速定位和使用。"""


class ClarificationPrompts:
    """需求澄清对话相关提示词"""
    
    @staticmethod
    def get_initial_clarification_prompt(topic):
        """获取初始澄清问题生成提示词"""
        return f"""你是一位专业的教学设计顾问。用户想要为主题“{topic}”生成课件。

为了生成最合适的课件，你需要向用户询问一些关键信息。请提出 3-5 个简短的问题，了解：
1. 教学目标（知识目标、能力目标）
2. 重点难点
3. 授课时长
4. 产出风格（正式/活泼/互动性强）
5. 特殊要求

请以友好的语气提问，每个问题简短明了。

输出格式：
【智能助手】您好！为了帮您生成最合适的课件，我想了解几个关键信息：
1. xxx？
2. xxx？
...

期待您的回复！"""
    
    @staticmethod
    def get_clarification_continue_prompt(topic, conversation_history):
        """获取继续澄清或总结需求的提示词"""
        return f"""根据用户的回复，请判断：
1. 如果信息还不够，继续提出 1-2 个关键问题
2. 如果信息已足够，请总结最终需求并输出格式化的需求清单

总结格式：
【需求确认】
- 主题：{topic}
- 教学目标：xxx
- 重点难点：xxx
- 授课时长：xxx
- 风格要求：xxx
- 其他要求：xxx

✅ 需求已确认，可以开始生成课件！"""


class VoiceQAPrompts:
    """语音问答相关提示词"""
    
    @staticmethod
    def get_voice_qa_prompt(transcribed_text, rag_context=None):
        """获取语音问答提示词"""
        if rag_context:
            return f"用户通过语音提问：{transcribed_text}\n\n{rag_context}\n\n请根据参考资料和语音提问提供详细的回答。"
        else:
            return f"用户通过语音提问：{transcribed_text}\n\n请根据这个问题提供详细的回答。"
