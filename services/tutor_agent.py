"""
智能辅导智能体 - 多模态答疑解惑
提供文字解答、图解说明、短视频讲解等多样化形式
"""

from core.json_utils import safe_parse_json

import json
from typing import Dict, List, Optional
from datetime import datetime
from core.logger import info, error
from services.qa_service import qa_service


class TutorAgent:
    """智能辅导智能体"""
    
    def __init__(self):
        info("智能辅导智能体初始化完成")
    
    def answer_query(self, user_id: int, input_data: Dict) -> Dict:
        """
        回答学生问题 - 多模态解答
        
        Args:
            user_id: 用户ID
            input_data: {
                "question": 问题内容,
                "subject": 学科,
                "context": 上下文(可选),
                "preferred_format": 偏好的解答形式(text/diagram/video/all)
            }
            
        Returns:
            多模态解答
        """
        info(f"开始智能辅导答疑, 用户: {user_id}")
        
        try:
            question = input_data.get("question", "")
            subject = input_data.get("subject", "综合")
            context = input_data.get("context", "")
            preferred_format = input_data.get("preferred_format", "all")
            
            # 获取学生画像以个性化解答
            profile = self._get_user_profile(user_id)
            
            # 生成多模态解答
            answer_data = self._generate_multimodal_answer(
                question, subject, context, profile, preferred_format
            )
            
            # 保存问答记录
            self._save_tutor_record(user_id, question, answer_data)
            
            result = {
                "answer": answer_data,
                "message": "智能辅导回答生成完成"
            }
            
            info(f"智能辅导完成, 解答类型: {answer_data.get('formats', [])}")
            return result
            
        except Exception as e:
            error(f"智能辅导失败: {str(e)}")
            return {
                "success": False,
                "message": f"辅导失败: {str(e)}"
            }
    
    def _generate_multimodal_answer(self, question: str, subject: str,
                                   context: str, profile: Dict,
                                   preferred_format: str) -> Dict:
        """生成多模态解答"""
        
        cognitive_style = profile.get("cognitive_style", "visual") if profile else "visual"
        weak_points = profile.get("weak_points", []) if profile else []
        
        # 根据偏好决定生成哪些形式
        formats_to_generate = []
        if preferred_format == "all":
            formats_to_generate = ["text", "diagram", "example"]
        elif preferred_format == "text":
            formats_to_generate = ["text"]
        elif preferred_format == "diagram":
            formats_to_generate = ["text", "diagram"]
        elif preferred_format == "video":
            formats_to_generate = ["text", "example"]
        else:
            formats_to_generate = ["text", "diagram", "example"]
        
        answer_data = {
            "question": question,
            "subject": subject,
            "formats": [],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 1. 文字解答(必选)
        if "text" in formats_to_generate:
            text_answer = self._generate_text_answer(question, subject, context, cognitive_style)
            if text_answer:
                answer_data["text_answer"] = text_answer
                answer_data["formats"].append("text")
        
        # 2. 图解说明
        if "diagram" in formats_to_generate:
            diagram = self._generate_diagram_explanation(question, subject, cognitive_style)
            if diagram:
                answer_data["diagram"] = diagram
                answer_data["formats"].append("diagram")
        
        # 3. 实例讲解/代码示例
        if "example" in formats_to_generate:
            example = self._generate_example(question, subject, weak_points)
            if example:
                answer_data["example"] = example
                answer_data["formats"].append("example")
        
        return answer_data
    
    def _generate_text_answer(self, question: str, subject: str,
                             context: str, cognitive_style: str) -> Dict:
        """生成文字解答"""
        
        prompt = f"""请详细回答以下{subject}课程的问题。

问题: {question}
{f'上下文: {context}' if context else ''}

学习者认知风格: {cognitive_style}

要求:
1. 给出准确、清晰的答案
2. 分步骤解释,逻辑清晰
3. 针对{cognitive_style}型学习者优化表达方式
4. 标注关键概念和公式
5. 长度适中,约300-500字

输出JSON格式:
{{
    "summary": "简要总结(1-2句)",
    "detailed_explanation": "详细解释(Markdown格式)",
    "key_concepts": ["概念1", "概念2"],
    "common_mistakes": ["常见错误1", "常见错误2"],
    "tips": ["学习建议1", "学习建议2"]
}}
"""
        
        try:
            response = qa_service.call_ai(prompt, max_tokens=1500)
            return safe_parse_json(response)
        except Exception as e:
            error(f"生成文字解答失败: {str(e)}")
            return None
    
    def _generate_diagram_explanation(self, question: str, subject: str,
                                     cognitive_style: str) -> Dict:
        """生成图解说明 — 返回 Mermaid 语法"""

        prompt = f"""请为以下{subject}问题生成一个 Mermaid.js 图表代码。

问题: {question}

要求:
1. 选择最合适的图表类型(flowchart/graph/sequenceDiagram/classDiagram等)
2. 用中文标注节点和关系
3. 适合{cognitive_style}型学习者理解
4. 直接输出合法的 Mermaid 语法，不要用代码块包裹

示例输出格式:
graph TD
    A[变量声明] --> B[赋值]
    B --> C[使用变量]
    C --> D{{条件判断}}
    D -->|是| E[执行分支1]
    D -->|否| F[执行分支2]

请直接输出 Mermaid 语法:
"""

        try:
            response = qa_service.call_ai(prompt, max_tokens=800)
            # 清理：去掉可能的代码块包裹
            mermaid_code = response.strip()
            if mermaid_code.startswith("```"):
                lines = mermaid_code.split("\n")
                mermaid_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return {"mermaid": mermaid_code.strip()}
        except Exception as e:
            error(f"生成图解说明失败: {str(e)}")
            return None
    
    def _generate_example(self, question: str, subject: str,
                         weak_points: List[str]) -> Dict:
        """生成实例讲解或代码示例"""
        
        weak_points_str = ', '.join(weak_points[:2]) if weak_points else '无'
        
        prompt = f"""请为以下{subject}问题提供一个具体的实例或代码示例。

问题: {question}
学生薄弱点: {weak_points_str}

要求:
1. 提供与问题相关的具体实例
2. 如果是编程问题,提供完整可运行代码
3. 逐步解释实例的执行过程或解题思路
4. 针对薄弱点进行特别说明
5. 提供变式练习

输出JSON格式:
{{
    "example_title": "实例标题",
    "description": "实例说明",
    "steps": [
        {{
            "step_number": 1,
            "action": "操作步骤",
            "explanation": "原理解释"
        }}
    ],
    "code_example": {{
        "language": "python/java/none",
        "code": "代码内容",
        "output": "预期输出"
    }},
    "practice_variations": ["变式1", "变式2"],
    "key_takeaways": ["要点1", "要点2"]
}}
"""
        
        try:
            response = qa_service.call_ai(prompt, max_tokens=1800)
            return safe_parse_json(response)
        except Exception as e:
            error(f"生成实例讲解失败: {str(e)}")
            return None
    
    def _get_user_profile(self, user_id: int) -> Optional[Dict]:
        """获取用户画像"""
        try:
            from data.db_operations import profile_db
            with profile_db:
                sql = "SELECT profile_data FROM student_profiles WHERE user_id = %s ORDER BY version DESC LIMIT 1"
                profile_db.cursor.execute(sql, (user_id,))
                result = profile_db.cursor.fetchone()

                if result and result.get("profile_data"):
                    return json.loads(result["profile_data"])
                return None

        except Exception as e:
            error(f"获取用户画像失败: {str(e)}")
            return None
    
    def _save_tutor_record(self, user_id: int, question: str, answer_data: Dict):
        """保存辅导记录"""
        try:
            from data.db_operations import assessment_db
            with assessment_db:
                # 保存到learning_activities表
                sql = """
                    INSERT INTO learning_activities
                    (user_id, activity_type, metadata, duration_seconds)
                    VALUES (%s, %s, %s, %s)
                """
                assessment_db.cursor.execute(sql, (
                    user_id,
                    "tutor_query",
                    json.dumps({
                        "question": question,
                        "answer_summary": answer_data.get("text_answer", {}).get("summary", ""),
                        "formats": answer_data.get("formats", [])
                    }, ensure_ascii=False),
                    0  # 即时问答,时长为0
                ))

                assessment_db.conn.commit()

        except Exception as e:
            error(f"保存辅导记录失败: {str(e)}")
