"""
增强版 AI 提示词模块 v6.0
- 增加 few-shot 示例提升准确性
- 增加输出格式约束
- 增加学科特化策略
- 增加多样性控制
"""


class EnhancedCoursewarePrompts:
    """增强版课件生成提示词"""

    # 学科特化策略
    SUBJECT_STRATEGIES = {
        "数学": {
            "focus": "公式推导、定理证明、解题步骤、图形演示",
            "style": "逻辑严谨、步骤清晰、注重推导过程",
            "animation": "函数图像变化、几何变换、概率模拟",
            "decorations": "几何图形、坐标系、公式框",
        },
        "物理": {
            "focus": "实验演示、物理过程、公式应用、现象解释",
            "style": "图文并茂、实验导向、注重因果关系",
            "animation": "力学分析、电路演示、波动传播、光学实验",
            "decorations": "实验装置图、力的示意图、电路图",
        },
        "化学": {
            "focus": "化学反应、分子结构、实验操作、方程式",
            "style": "实验为主、安全提示、步骤详细",
            "animation": "分子运动、化学反应过程、溶液配制",
            "decorations": "分子模型、反应方程式、实验器材",
        },
        "语文": {
            "focus": "文本赏析、写作技巧、语言表达、文化传承",
            "style": "文学性强、情感丰富、注重意境",
            "animation": "古诗词意境、写作结构图、思维导图",
            "decorations": "书卷元素、毛笔装饰、古典纹样",
        },
        "英语": {
            "focus": "词汇拓展、语法讲解、口语练习、文化背景",
            "style": "中英结合、互动性强、注重应用",
            "animation": "对话场景、语法结构图、发音口型",
            "decorations": "气泡对话框、国旗元素、世界地图",
        },
        "历史": {
            "focus": "时间线、因果分析、人物评价、史料分析",
            "style": "叙事性强、时间线清晰、多角度分析",
            "animation": "历史事件时间线、地图变迁、战争形势",
            "decorations": "卷轴、时间轴、古建筑剪影",
        },
        "地理": {
            "focus": "地图分析、气候特征、人文地理、区域比较",
            "style": "图表为主、数据支撑、空间思维",
            "animation": "板块运动、气候形成、洋流分布",
            "decorations": "地球仪、指南针、等高线",
        },
        "生物": {
            "focus": "生命过程、生态系统、遗传变异、人体结构",
            "style": "图文结合、过程清晰、注重微观",
            "animation": "细胞分裂、DNA 复制、生态系统循环",
            "decorations": "细胞模型、DNA 双螺旋、叶绿体",
        },
        "信息技术": {
            "focus": "编程逻辑、算法演示、网络原理、信息安全",
            "style": "代码展示、流程图、动手实践",
            "animation": "算法执行过程、数据结构变化、网络拓扑",
            "decorations": "代码块、流程图、二进制装饰",
        },
    }

    @staticmethod
    def get_enhanced_ppt_prompt(subject, topic, requirements_text, fast_mode=True):
        """增强版 PPT 生成提示词"""
        strategy = EnhancedCoursewarePrompts.SUBJECT_STRATEGIES.get(
            subject,
            EnhancedCoursewarePrompts.SUBJECT_STRATEGIES.get("数学")
        )

        mode_config = {
            "fast": {
                "pages": "8-10",
                "points": "2-4",
                "time": "15-25 秒",
                "decorations": "简洁几何装饰",
                "images": "无配图",
            },
            "standard": {
                "pages": "10-15",
                "points": "3-5",
                "time": "45-90 秒",
                "decorations": "精美装饰元素",
                "images": "含配图建议",
            },
        }

        config = mode_config["fast" if fast_mode else "standard"]

        return f"""你是一位专业的 PPT 课件设计师，擅长{subject}学科的教学课件设计。

## 任务
为{subject}课程「{topic}」设计一个专业、美观的 PPT 课件。

## 学科特点
- 教学重点: {strategy['focus']}
- 设计风格: {strategy['style']}
- 装饰元素: {strategy['decorations']}

## 设计要求
1. 总共 {config['pages']} 页幻灯片
2. 包含: 封面、目录、教学目标、知识点讲解、典型例题、课堂小结
3. 每页 {config['points']} 个要点
4. 结合用户需求: {requirements_text}

## 质量要求
- 每个要点必须是完整的句子，不能是空字符串
- 知识点要准确、专业、有深度
- 内容要具体，不能是泛泛的描述
- 例题要有完整的题目和解答过程
- 教学目标要具体可测量

## 模板选择
根据学科自动选择最合适的模板风格:
- tech: 科技蓝 (#0a192f/#64ffda/#00d4ff) - 适合数学/信息技术
- edu: 教育紫 (#5b2c6f/#f39c12/#e74c3c) - 适合语文/英语/历史
- nature: 自然绿 (#27ae60/#2ecc71/#f1c40f) - 适合生物/地理
- minimal: 简约灰 (#2c3e50/#95a5a6/#e74c3c) - 适合物理/化学
- business: 商务金 (#1a1a2e/#c9a227/#d4af37) - 适合经济学

## 输出格式
严格按照以下 JSON 格式输出，不要有任何其他文字:

{{
    "template_style": "模板风格",
    "theme": {{
        "primary_color": "#主色调",
        "secondary_color": "#辅助色",
        "accent_color": "#强调色",
        "bg_color": "#背景色",
        "text_color": "#文字色"
    }},
    "slides": [
        {{
            "title": "页面标题（不能为空）",
            "subtitle": "副标题（可选）",
            "content": ["要点1（必须是完整的有意义的句子）", "要点2", "要点3"],
            "layout": "title_only / title_content / two_column / section_divider",
            "background": {{"type": "gradient / solid", "colors": ["#颜色1", "#颜色2"]}},
            "decorations": [],
            "image_suggestion": "图片建议（标准模式下填写）",
            "notes": "演讲者备注（可选）"
        }}
    ]
}}

## 示例输出
以下是一个高质量课件的示例（仅作参考，请根据实际主题生成）:

{{
    "template_style": "minimal",
    "theme": {{
        "primary_color": "#2c3e50",
        "secondary_color": "#95a5a6",
        "accent_color": "#e74c3c",
        "bg_color": "#ffffff",
        "text_color": "#333333"
    }},
    "slides": [
        {{
            "title": "函数的单调性",
            "subtitle": "高中数学 · 必修一",
            "content": [""],
            "layout": "title_only",
            "background": {{"type": "gradient", "colors": ["#2c3e50", "#34495e"]}},
            "decorations": [],
            "image_suggestion": "",
            "notes": ""
        }},
        {{
            "title": "教学目标",
            "subtitle": "",
            "content": [
                "理解函数单调性的定义和几何意义",
                "掌握判断函数单调性的方法（定义法、导数法）",
                "能够运用单调性解决实际问题"
            ],
            "layout": "title_content",
            "background": {{"type": "solid", "colors": ["#ffffff"]}},
            "decorations": [],
            "image_suggestion": "",
            "notes": ""
        }}
    ]
}}

注意: 只输出 JSON，不要有任何其他文字。"""
