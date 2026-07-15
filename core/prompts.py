"""AI 提示词模块
包含学生画像构建等提示词
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


class VoiceQAPrompts:
    """语音问答相关提示词"""

    @staticmethod
    def get_voice_qa_prompt(transcribed_text, rag_context=None):
        """获取语音问答提示词"""
        if rag_context:
            return f"用户通过语音提问：{transcribed_text}\n\n{rag_context}\n\n请根据参考资料和语音提问提供详细的回答。"
        else:
            return f"用户通过语音提问：{transcribed_text}\n\n请根据这个问题提供详细的回答。"
