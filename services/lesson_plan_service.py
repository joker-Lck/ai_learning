"""
教案 + PPT 内容生成服务
调用 LLM 生成结构化教案与幻灯片内容，支持多种 PPT 风格
"""
import json

from core.json_utils import safe_parse_json
from core.logger import error, info, warning
from services.spark_client import spark_client


# ── PPT 风格配置 ──
PPT_STYLES = {
    "modern": {
        "name": "现代蓝",
        "primary": "1E40AF",
        "secondary": "3B82F6",
        "accent": "60A5FA",
        "bg_light": "EFF6FF",
        "bg_dark": "1E3A5F",
        "text_dark": "1E293B",
        "text_light": "F8FAFC",
        "gradient_start": "1E40AF",
        "gradient_end": "3B82F6",
    },
    "elegant": {
        "name": "典雅紫",
        "primary": "6D28D9",
        "secondary": "8B5CF6",
        "accent": "A78BFA",
        "bg_light": "F5F3FF",
        "bg_dark": "2E1065",
        "text_dark": "1E1B4B",
        "text_light": "FAF5FF",
        "gradient_start": "5B21B6",
        "gradient_end": "8B5CF6",
    },
    "warm": {
        "name": "暖阳橙",
        "primary": "C2410C",
        "secondary": "EA580C",
        "accent": "FB923C",
        "bg_light": "FFF7ED",
        "bg_dark": "7C2D12",
        "text_dark": "431407",
        "text_light": "FFFBEB",
        "gradient_start": "C2410C",
        "gradient_end": "F97316",
    },
    "tech": {
        "name": "科技深色",
        "primary": "0F172A",
        "secondary": "1E293B",
        "accent": "38BDF8",
        "bg_light": "0F172A",
        "bg_dark": "020617",
        "text_dark": "E2E8F0",
        "text_light": "F8FAFC",
        "gradient_start": "0F172A",
        "gradient_end": "1E293B",
    },
    "nature": {
        "name": "清新绿",
        "primary": "15803D",
        "secondary": "22C55E",
        "accent": "4ADE80",
        "bg_light": "F0FDF4",
        "bg_dark": "14532D",
        "text_dark": "14532D",
        "text_light": "F0FDF4",
        "gradient_start": "166534",
        "gradient_end": "22C55E",
    },
}

# ── 教案结构模板 ──
LESSON_PLAN_PROMPT = """你是资深教学设计师。请根据以下信息生成一份完整、专业的教案。

## 课程信息
- 学科：{subject}
- 主题：{topic}
- 年级/对象：{grade}
- 课时长度：{duration} 分钟
- 教学风格偏好：{style_hint}

## 输出要求
请严格输出 JSON 格式（不要 markdown 代码块），结构如下：
{{
  "lesson_title": "课程标题",
  "subject": "学科",
  "topic": "主题",
  "grade": "年级",
  "duration": 45,
  "teaching_objectives": {{
    "knowledge": ["知识目标1", "知识目标2", "知识目标3"],
    "ability": ["能力目标1", "能力目标2"],
    "emotion": ["情感目标1", "情感目标2"]
  }},
  "key_points": ["重点1", "重点2"],
  "difficult_points": ["难点1", "难点2"],
  "teaching_methods": ["讲授法", "讨论法", "演示法"],
  "teaching_aids": ["PPT课件", "板书", "多媒体"],
  "teaching_process": [
    {{
      "phase": "导入新课",
      "duration": 5,
      "teacher_activity": "教师活动描述",
      "student_activity": "学生活动描述",
      "design_intent": "设计意图"
    }},
    {{
      "phase": "讲授新知",
      "duration": 20,
      "teacher_activity": "教师活动描述",
      "student_activity": "学生活动描述",
      "design_intent": "设计意图"
    }},
    {{
      "phase": "巩固练习",
      "duration": 12,
      "teacher_activity": "教师活动描述",
      "student_activity": "学生活动描述",
      "design_intent": "设计意图"
    }},
    {{
      "phase": "课堂小结",
      "duration": 5,
      "teacher_activity": "教师活动描述",
      "student_activity": "学生活动描述",
      "design_intent": "设计意图"
    }},
    {{
      "phase": "布置作业",
      "duration": 3,
      "teacher_activity": "教师活动描述",
      "student_activity": "学生活动描述",
      "design_intent": "设计意图"
    }}
  ],
  "board_design": "板书设计说明（可用文字描述结构）",
  "homework": "课后作业内容",
  "teaching_reflection": "教学反思要点（供教师课后填写的引导）"
}}

请确保内容专业、具体、可操作，适合实际教学使用。"""

PPT_CONTENT_PROMPT = """你是专业 PPT 设计师。请根据以下教案生成配套的 PPT 幻灯片内容。

## 课程信息
- 学科：{subject}
- 主题：{topic}
- 年级：{grade}

## 教案核心内容
{lesson_summary}

## 输出要求
请严格输出 JSON 格式（不要 markdown 代码块），生成 8-14 张幻灯片：
{{
  "slides": [
    {{
      "type": "title",
      "title": "课程标题",
      "subtitle": "学科 · 年级",
      "notes": "演讲者备注"
    }},
    {{
      "type": "objectives",
      "title": "学习目标",
      "bullets": ["目标1", "目标2", "目标3"],
      "notes": "备注"
    }},
    {{
      "type": "section",
      "title": "第一部分",
      "subtitle": "章节副标题",
      "notes": "备注"
    }},
    {{
      "type": "content",
      "title": "知识要点",
      "bullets": ["要点1", "要点2", "要点3"],
      "notes": "备注"
    }},
    {{
      "type": "two_column",
      "title": "对比分析",
      "left_title": "概念A",
      "left_bullets": ["特点1", "特点2"],
      "right_title": "概念B",
      "right_bullets": ["特点1", "特点2"],
      "notes": "备注"
    }},
    {{
      "type": "activity",
      "title": "课堂活动",
      "description": "活动描述",
      "steps": ["步骤1", "步骤2", "步骤3"],
      "time": "10分钟",
      "notes": "备注"
    }},
    {{
      "type": "summary",
      "title": "课堂小结",
      "bullets": ["要点回顾1", "要点回顾2"],
      "notes": "备注"
    }},
    {{
      "type": "qa",
      "title": "谢谢观看",
      "subtitle": "Q & A",
      "notes": "备注"
    }}
  ]
}}

幻灯片类型可选: title, objectives, section, content, two_column, activity, summary, qa
内容要精炼、适合 PPT 展示（每条要点不超过 30 字）。"""


class LessonPlanService:
    """教案 + PPT 内容生成服务"""

    def generate_lesson_plan(
        self,
        subject: str,
        topic: str,
        grade: str = "大学",
        duration: int = 45,
        style_hint: str = "",
    ) -> dict:
        """生成完整教案"""
        prompt = LESSON_PLAN_PROMPT.format(
            subject=subject,
            topic=topic,
            grade=grade,
            duration=duration,
            style_hint=style_hint or "传统讲授与互动结合",
        )
        try:
            info(f"生成教案: {subject} / {topic}")
            result = spark_client.chat(prompt, max_tokens=4000)
            plan = safe_parse_json(result)
            if not plan:
                warning("教案 JSON 解析失败，使用模板回退")
                return self._fallback_lesson_plan(subject, topic, grade, duration)
            return plan
        except Exception as e:
            error(f"生成教案失败: {e!s}")
            return self._fallback_lesson_plan(subject, topic, grade, duration)

    def generate_ppt_content(
        self,
        subject: str,
        topic: str,
        grade: str,
        lesson_summary: str,
    ) -> dict:
        """根据教案生成 PPT 幻灯片内容"""
        prompt = PPT_CONTENT_PROMPT.format(
            subject=subject,
            topic=topic,
            grade=grade,
            lesson_summary=lesson_summary[:2000],
        )
        try:
            info(f"生成PPT内容: {subject} / {topic}")
            result = spark_client.chat(prompt, max_tokens=4000)
            content = safe_parse_json(result)
            if not content or "slides" not in content:
                warning("PPT JSON 解析失败，使用模板回退")
                return self._fallback_ppt_content(subject, topic, grade)
            return content
        except Exception as e:
            error(f"生成PPT内容失败: {e!s}")
            return self._fallback_ppt_content(subject, topic, grade)

    def generate_full(
        self,
        subject: str,
        topic: str,
        grade: str = "大学",
        duration: int = 45,
        style: str = "modern",
        style_hint: str = "",
    ) -> dict:
        """一次性生成教案 + PPT 内容"""
        plan = self.generate_lesson_plan(subject, topic, grade, duration, style_hint)

        # 构建教案摘要供 PPT 生成
        summary_parts = [
            f"教学目标(知识): {'; '.join(plan.get('teaching_objectives', {}).get('knowledge', []))}",
            f"重点: {'; '.join(plan.get('key_points', []))}",
            f"难点: {'; '.join(plan.get('difficult_points', []))}",
        ]
        for p in plan.get("teaching_process", []):
            summary_parts.append(f"{p.get('phase','')}: {p.get('teacher_activity','')}")
        lesson_summary = "\n".join(summary_parts)

        ppt = self.generate_ppt_content(subject, topic, grade, lesson_summary)

        return {
            "success": True,
            "lesson_plan": plan,
            "ppt_content": ppt,
            "style": style,
            "style_config": PPT_STYLES.get(style, PPT_STYLES["modern"]),
        }

    def _fallback_lesson_plan(self, subject, topic, grade, duration):
        return {
            "lesson_title": f"{subject}——{topic}",
            "subject": subject,
            "topic": topic,
            "grade": grade,
            "duration": duration,
            "teaching_objectives": {
                "knowledge": [f"理解{topic}的核心概念与基本原理", f"掌握{topic}的相关方法与技能", f"了解{topic}的实际应用场景"],
                "ability": ["培养分析问题与解决问题的能力", "提升自主学习与合作探究能力"],
                "emotion": ["激发对学科的兴趣与热爱", "培养严谨求实的科学态度"],
            },
            "key_points": [f"{topic}的核心概念", f"{topic}的基本方法"],
            "difficult_points": [f"{topic}的深层理解与灵活应用"],
            "teaching_methods": ["讲授法", "讨论法", "案例教学法"],
            "teaching_aids": ["PPT课件", "板书", "多媒体设备"],
            "teaching_process": [
                {"phase": "导入新课", "duration": 5, "teacher_activity": f"通过实际案例引入{topic}话题，激发学生兴趣", "student_activity": "思考问题，积极参与讨论", "design_intent": "创设情境，引起学习动机"},
                {"phase": "讲授新知", "duration": 20, "teacher_activity": f"系统讲解{topic}的核心概念、原理与方法", "student_activity": "认真听讲，记录要点，及时提问", "design_intent": "突出重点，突破难点"},
                {"phase": "巩固练习", "duration": 12, "teacher_activity": "设计分层练习题，巡视指导", "student_activity": "独立完成练习，小组讨论交流", "design_intent": "学以致用，深化理解"},
                {"phase": "课堂小结", "duration": 5, "teacher_activity": "引导学生回顾知识框架", "student_activity": "梳理知识要点，完善笔记", "design_intent": "构建知识体系"},
                {"phase": "布置作业", "duration": 3, "teacher_activity": "布置课后作业，提出拓展要求", "student_activity": "记录作业要求", "design_intent": "课后巩固，拓展延伸"},
            ],
            "board_design": f"主板：{topic}核心概念框架图\n副板：关键词与公式",
            "homework": f"完成{topic}相关练习题，预习下一节内容",
            "teaching_reflection": "（课后填写：教学目标达成情况、学生反馈、改进方向）",
        }

    def _fallback_ppt_content(self, subject, topic, grade):
        return {
            "slides": [
                {"type": "title", "title": topic, "subtitle": f"{subject} · {grade}", "notes": ""},
                {"type": "objectives", "title": "学习目标", "bullets": [f"理解{topic}的核心概念", f"掌握{topic}的基本方法", f"学会{topic}的实际应用"], "notes": ""},
                {"type": "section", "title": "知识讲解", "subtitle": "核心内容", "notes": ""},
                {"type": "content", "title": f"{topic}——核心概念", "bullets": ["概念定义与内涵", "基本特征与性质", "重要原理与规律"], "notes": ""},
                {"type": "content", "title": f"{topic}——方法技能", "bullets": ["基本方法介绍", "操作步骤解析", "常见问题与注意事项"], "notes": ""},
                {"type": "two_column", "title": "重点与难点", "left_title": "学习重点", "left_bullets": ["核心概念", "基本方法"], "right_title": "学习难点", "right_bullets": ["深层理解", "灵活应用"], "notes": ""},
                {"type": "section", "title": "课堂实践", "subtitle": "互动练习", "notes": ""},
                {"type": "activity", "title": "课堂练习", "description": f"围绕{topic}进行分组练习", "steps": ["独立思考", "小组讨论", "成果展示"], "time": "10分钟", "notes": ""},
                {"type": "summary", "title": "课堂小结", "bullets": ["核心概念回顾", "方法技能梳理", "知识体系构建"], "notes": ""},
                {"type": "qa", "title": "谢谢观看", "subtitle": "Q & A", "notes": ""},
            ]
        }


# 全局单例
lesson_plan_service = LessonPlanService()
