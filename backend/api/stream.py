"""
流式输出 API - SSE实时推送生成进度
"""

import asyncio
import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.dependencies import get_current_user, require_auth
from core.logger import error, info
from services.content_safety_service import anti_hallucination_service, content_safety_service
from services.qa_service import qa_service
from services.resource_agent import resource_agent
from services.streaming_service import progress_tracker, sse_generator
from services.tutor_agent import tutor_agent

router = APIRouter(tags=["流式输出"])
_rate_limiter = Limiter(key_func=get_remote_address)


@router.get("/generate-resource/{resource_type}")
async def stream_generate_resource(
    resource_type: str,
    subject: str,
    topic: str,
    user: dict = Depends(require_auth)
):
    """
    流式生成学习资源 - SSE实时推送进度

    参数:
    - resource_type: 资源类型 (document/quiz/mindmap/video等)
    - subject: 学科
    - topic: 主题
    """
    try:
        user_id = user["id"]
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        info(f"开始流式生成资源: {resource_type}, 任务ID: {task_id}")

        # 获取用户画像
        profile = {"user_id": user_id}

        async def event_generator():
            source = sse_generator.generate_resource_stream(
                task_id=task_id, resource_type=resource_type,
                subject=subject, topic=topic, profile=profile
            )
            async for event in sse_generator.wrap_with_heartbeat(source):
                yield event

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Encoding": "identity",
            }
        )

    except Exception as e:
        error(f"流式生成资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate-resources-real")
async def stream_generate_resources_real(
    subject: str,
    topic: str,
    resource_types: str,
    difficulty: str = "intermediate",
    user: dict = Depends(require_auth)
):
    """
    真实流式生成多种学习资源 - SSE实时推送进度

    参数:
    - subject: 学科
    - topic: 主题
    - resource_types: 逗号分隔的资源类型 (如 "document,quiz,mindmap")
    - difficulty: 难度 (beginner/intermediate/advanced)
    """
    try:
        user_id = user["id"]
        types_list = [t.strip() for t in resource_types.split(",") if t.strip()]
        total = len(types_list)

        if total == 0:
            raise HTTPException(status_code=400, detail="resource_types 不能为空")

        info(f"用户 {user_id} 请求流式生成 {total} 种资源: {types_list}")

        def _sse(data: dict) -> str:
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        def _do_generate(rtype, subject, topic, difficulty, user_id):
            return resource_agent.generate_resource(
                resource_type=rtype, subject=subject, topic=topic,
                difficulty=difficulty, user_id=user_id
            )

        def _save_resource(user_id, title, rtype, subject, topic, difficulty, content_data, duration_minutes):
            from data.db_operations import resource_db
            if resource_db.connect():
                resource_db.cursor.execute("""
                    INSERT INTO learning_resources
                    (user_id, title, resource_type, subject, topic, difficulty_level, content_data, generated_by_agent, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, title, rtype, subject, topic, difficulty,
                    json.dumps(content_data, ensure_ascii=False),
                    f"user_{user_id}", duration_minutes
                ))
                resource_db.conn.commit()
                resource_db.close()

        def _log_activity(user_id, rtype, subject, topic, title):
            from data.db_operations import assessment_db
            if assessment_db.connect():
                assessment_db.cursor.execute("""
                    INSERT INTO learning_activities (user_id, activity_type, metadata)
                    VALUES (?, ?, ?)
                """, (
                    user_id, 'resource_generate',
                    json.dumps({"resource_type": rtype, "subject": subject, "topic": topic, "title": title}, ensure_ascii=False)
                ))
                assessment_db.conn.commit()
                assessment_db.close()

        async def event_generator():
            for idx, rtype in enumerate(types_list):
                # 检测客户端断开连接
                try:
                    pass
                except Exception:
                    pass

                type_label = {
                    "document": "课程文档", "mindmap": "思维导图", "quiz": "练习题目",
                    "video": "视频脚本", "animation": "动画脚本", "code_case": "代码案例",
                    "reading": "拓展阅读"
                }.get(rtype, rtype)

                yield _sse({
                    "type": "progress",
                    "step": "generating",
                    "resource_type": rtype,
                    "current": idx + 1,
                    "total": total,
                    "progress": round(idx / total * 100),
                    "message": f"[{idx + 1}/{total}] 🤖 {type_label} 生成中..."
                })

                t0 = time.time()
                try:
                    result = await asyncio.to_thread(
                        _do_generate, rtype, subject, topic, difficulty, user_id
                    )
                    elapsed = round(time.time() - t0, 1)

                    if result.get("success"):
                        res_data = result.get("data", {})
                        title = res_data.get("title", f"{topic} - {type_label}")
                        content_data = res_data.get("content_data", res_data)

                        try:
                            await asyncio.to_thread(
                                _save_resource, user_id, title, rtype, subject, topic,
                                difficulty, content_data, res_data.get("duration_minutes")
                            )
                            info(f"资源自动保存成功: {title}")
                        except Exception as save_err:
                            error(f"资源自动保存失败: {save_err}")

                        try:
                            await asyncio.to_thread(
                                _log_activity, user_id, rtype, subject, topic, title
                            )
                        except Exception as log_err:
                            error(f"活动日志记录失败: {log_err}")

                        yield _sse({
                            "type": "resource",
                            "resource_type": rtype,
                            "title": title,
                            "content_data": content_data,
                            "duration_minutes": res_data.get("duration_minutes"),
                            "elapsed_seconds": elapsed,
                            "message": f"✅ {type_label} 生成完成 ({elapsed}s)"
                        })
                    else:
                        yield _sse({
                            "type": "resource_error",
                            "resource_type": rtype,
                            "error": result.get("message", "生成失败"),
                            "elapsed_seconds": elapsed
                        })

                except Exception as e:
                    elapsed = round(time.time() - t0, 1)
                    error(f"学习资源生成异常 [{rtype}]: {e}")
                    yield _sse({
                        "type": "resource_error",
                        "resource_type": rtype,
                        "error": str(e),
                        "elapsed_seconds": elapsed
                    })

            yield _sse({
                "type": "complete",
                "progress": 100,
                "message": f"✅ 全部 {total} 种学习资源生成完成!"
            })

        async def wrapped_generator():
            async for event in sse_generator.wrap_with_heartbeat(event_generator()):
                yield event

        return StreamingResponse(
            wrapped_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Encoding": "identity",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error(f"流式生成资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{task_id}")
async def get_task_progress(
    task_id: str,
    user: dict = Depends(require_auth)
):
    """获取任务进度"""
    task = progress_tracker.get_task_status(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    return {
        "success": True,
        "data": task
    }


@router.get("/my-tasks")
async def get_user_tasks(
    limit: int = 10,
    user: dict = Depends(require_auth)
):
    """获取用户的任务列表"""
    tasks = progress_tracker.get_user_tasks(user["id"], limit)

    return {
        "success": True,
        "data": tasks,
        "count": len(tasks)
    }


@router.post("/check-content-safety")
async def check_content_safety_api(
    content_data: dict[str, Any],
    user: dict = Depends(require_auth)
):
    """
    检查内容安全性

    请求体:
    {
        "content": "待检查的文本"
    }
    """
    try:
        content = content_data.get("content", "")

        if not content:
            raise HTTPException(status_code=400, detail="内容为空")

        # 安全检查
        safety_result = content_safety_service.check_content_safety(content)

        # 如果不安全,提供过滤后的版本
        filtered = None
        if not safety_result["is_safe"]:
            filtered_result = content_safety_service.filter_and_clean(content)
            filtered = filtered_result["filtered_content"]

        return {
            "success": True,
            "data": {
                "safety_check": safety_result,
                "filtered_content": filtered
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error(f"内容安全检查失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-fact")
async def verify_fact_api(
    fact_data: dict[str, Any],
    user: dict = Depends(require_auth)
):
    """
    验证事实准确性

    请求体:
    {
        "claim": "需要验证的陈述",
        "knowledge_context": "相关知识库上下文(可选)"
    }
    """
    try:
        claim = fact_data.get("claim", "")
        knowledge_context = fact_data.get("knowledge_context", "")

        if not claim:
            raise HTTPException(status_code=400, detail="陈述内容为空")

        # 事实验证
        verification_result = anti_hallucination_service.verify_with_rag(
            claim=claim,
            knowledge_context=knowledge_context
        )

        # 检测不确定性标记
        uncertainty_markers = anti_hallucination_service.detect_uncertainty_markers(claim)

        return {
            "success": True,
            "data": {
                "verification": verification_result,
                "uncertainty_markers": uncertainty_markers
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error(f"事实验证失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-citations")
async def add_citations_api(
    citation_data: dict[str, Any],
    user: dict = Depends(require_auth)
):
    """
    为内容添加引用标注

    请求体:
    {
        "content": "原始内容",
        "sources": [
            {"title": "标题", "author": "作者", "year": 2024}
        ]
    }
    """
    try:
        content = citation_data.get("content", "")
        sources = citation_data.get("sources", [])

        if not content:
            raise HTTPException(status_code=400, detail="内容为空")

        # 添加引用
        cited_content = anti_hallucination_service.add_citations(content, sources)

        return {
            "success": True,
            "data": {
                "cited_content": cited_content,
                "sources_count": len(sources)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error(f"添加引用失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross-validate")
async def cross_validate_api(
    validation_data: dict[str, Any],
    user: dict = Depends(require_auth)
):
    """
    交叉验证内容一致性

    请求体:
    {
        "primary_answer": "主要答案",
        "alternative_sources": ["来源1", "来源2"]
    }
    """
    try:
        primary_answer = validation_data.get("primary_answer", "")
        alternative_sources = validation_data.get("alternative_sources", [])

        if not primary_answer or not alternative_sources:
            raise HTTPException(status_code=400, detail="参数不完整")

        # 交叉验证
        consistency_result = anti_hallucination_service.cross_validate(
            primary_answer=primary_answer,
            alternative_sources=alternative_sources
        )

        return {
            "success": True,
            "data": consistency_result
        }

    except HTTPException:
        raise
    except Exception as e:
        error(f"交叉验证失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor")
async def stream_tutor_query(
    input_data: dict[str, Any],
    user: dict = Depends(get_current_user),
):
    """
    流式智能辅导 — SSE 逐字推送解答

    请求体: { "question": "...", "subject": "..." }
    SSE 事件:
      data: {"type": "text_delta", "content": "增量文本"}
      data: {"type": "diagram", "data": {...}}
      data: {"type": "example", "data": {...}}
      data: {"type": "complete"}
      data: {"type": "error", "message": "..."}
    """
    question = input_data.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    subject = input_data.get("subject", "通用")
    user_id = user.get("id", 0)
    cognitive_style = user.get("learning_style", "visual")

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_generator():
        info(f"用户 {user_id} 流式辅导: {question[:50]}")

        prompt = f"""请回答以下学习问题，给出清晰、分步骤的解答。

问题: {question}
学科: {subject}
认知风格: {cognitive_style}

要求:
1. 准确清晰，分步骤解释
2. 标注关键概念
3. 约200-400字
直接输出解答内容，不要输出JSON格式。"""

        try:
            for chunk in qa_service.call_ai_stream(prompt, max_tokens=1500):
                yield _sse({"type": "text_delta", "content": chunk})
        except Exception as e:
            yield _sse({"type": "error", "message": f"文字解答生成失败: {e}"})
            return

        try:
            diagram = tutor_agent._generate_diagram_explanation(question, subject, cognitive_style)
            if diagram:
                yield _sse({"type": "diagram", "data": diagram})
        except Exception as e:
            error(f"图解生成失败: {e}")

        try:
            example = tutor_agent._generate_example(question, subject, [])
            if example:
                yield _sse({"type": "example", "data": example})
        except Exception as e:
            error(f"示例生成失败: {e}")

        yield _sse({"type": "complete"})

    async def wrapped_generator():
        async for event in sse_generator.wrap_with_heartbeat(event_generator()):
            yield event

    return StreamingResponse(
        wrapped_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


# ── 流式自适应出题 ──

@router.post("/quiz/adaptive")
async def stream_quiz_adaptive(
    input_data: dict[str, Any],
    user: dict = Depends(require_auth),
):
    """
    流式自适应出题 — 先从题库取，不足时AI流式生成

    请求体: { "subject": "数学", "count": 10 }
    SSE 事件:
      data: {"type": "progress", "message": "正在从题库查找..."}
      data: {"type": "questions", "questions": [...], "source": "bank"}
      data: {"type": "complete", "questions": [...], "source": "mixed"}
      data: {"type": "error", "message": "..."}
    """
    from data.dao import get_quiz_dao
    from core.json_utils import safe_parse_json

    subject = input_data.get("subject") or "综合"
    count = input_data.get("count", 10)
    user_id = user.get("id", 0)

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_generator():
        quiz_dao = get_quiz_dao()

        # 1. 从题库取题（最多占60%，确保用户总能遇到新题）
        yield _sse({"type": "progress", "message": "正在从题库查找..."})
        bank_cap = max(1, int(count * 0.6))
        bank_questions = quiz_dao.get_from_bank(subject=subject, count=bank_cap)
        bank_take = min(len(bank_questions), bank_cap)

        # 2. 剩余由AI流式生成
        need = count - bank_take
        if bank_take > 0:
            yield _sse({"type": "progress", "message": f"题库复用 {bank_take} 题，AI 补充生成 {need} 题..."})
        else:
            yield _sse({"type": "progress", "message": f"AI 生成 {need} 道新题..."})

        weak_topics = quiz_dao.get_weak_topics(user_id, limit=5)
        weak_info = ""
        if weak_topics:
            weak_info = "学生薄弱知识点：\n"
            for t in weak_topics:
                weak_info += f"- {t['knowledge_point']}：正确率 {t['accuracy']}%\n"

        prompt = f"""请为{subject}学科生成 {need} 道练习题。
{weak_info}
要求：题型包含选择题(type="multiple_choice")、判断题(type="judge")、填空题(type="fill_blank")。
选择题options格式：["A. xxx", "B. xxx", "C. xxx", "D. xxx"]，answer填字母如"A"。
判断题options留空数组，answer填"true"或"false"。
填空题options留空数组，answer填答案文本。

只输出JSON，不要输出其他内容：
{{"questions":[{{"id":1,"type":"multiple_choice","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"A","explanation":"...","difficulty":"easy","knowledge_point":"..."}}]}}"""

        try:
            full_text = ""
            for chunk in qa_service.call_ai_stream(prompt, max_tokens=2500):
                full_text += chunk
                yield _sse({"type": "delta", "content": chunk})

            # 解析AI返回的JSON
            quiz_data = safe_parse_json(full_text)
            ai_questions = []
            if quiz_data and isinstance(quiz_data, dict):
                ai_questions = quiz_data.get("questions", [])

            if ai_questions:
                saved = quiz_dao.save_to_bank(subject, ai_questions)
                info(f"流式出题存入题库 {saved} 题")

            all_questions = bank_questions[:bank_take] + ai_questions
            yield _sse({"type": "questions", "questions": all_questions[:count], "source": "mixed" if bank_take else "ai"})
            yield _sse({"type": "complete"})
        except Exception as e:
            error(f"流式出题失败: {e}")
            if bank_take:
                yield _sse({"type": "questions", "questions": bank_questions[:bank_take], "source": "bank"})
                yield _sse({"type": "complete"})
            else:
                yield _sse({"type": "error", "message": f"出题失败: {e}"})

    async def wrapped_generator():
        async for event in sse_generator.wrap_with_heartbeat(event_generator()):
            yield event

    return StreamingResponse(
        wrapped_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no", "Content-Encoding": "identity"},
    )


# ── 流式学习路径生成 ──

@router.post("/plan-path")
async def stream_plan_path(
    input_data: dict[str, Any],
    user: dict = Depends(get_current_user),
):
    """
    流式学习路径生成 — SSE逐字推送

    请求体: { "learning_goal": "掌握Python数据分析" }
    SSE 事件:
      data: {"type": "delta", "content": "增量文本"}
      data: {"type": "complete", "path": {...}}
      data: {"type": "error", "message": "..."}
    """
    learning_goal = input_data.get("learning_goal", "").strip()
    if not learning_goal:
        raise HTTPException(status_code=400, detail="学习目标不能为空")

    user_id = user.get("id", 0)

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_generator():
        from services.profile_agent import ProfileAgent
        from core.json_utils import safe_parse_json

        profile_agent = ProfileAgent()
        profile_result = profile_agent.get_or_build_profile(user_id)
        profile = profile_result.get("profile", {})

        cognitive_style = profile.get("cognitive_style", "visual")
        weak_points = profile.get("weak_points", [])
        preferred_resources = profile.get("preferred_resources", ["document"])

        prompt = f"""你是一个专业的学习规划师。请为学生规划一个个性化的学习路径。

学习目标: {learning_goal}
学生特征:
- 认知风格: {cognitive_style}
- 薄弱点: {', '.join(weak_points[:3]) if weak_points else '无'}
- 资源偏好: {', '.join(preferred_resources[:3])}

请严格按照以下JSON格式输出学习路径：
{{
  "path_name": "路径名称",
  "estimated_hours": 总时长数字,
  "total_steps": 步骤数,
  "steps": [
    {{
      "step_id": 1,
      "title": "步骤标题",
      "description": "详细描述",
      "learning_objective": "学习目标",
      "estimated_time": 预计分钟数,
      "resource_type": "document/mindmap/quiz/video/animation/code_case",
      "prerequisites": []
    }}
  ]
}}

要求: 生成4-8个具体的学习步骤，每个步骤20-60分钟，总时长2-6小时。只输出JSON。"""

        try:
            full_text = ""
            for chunk in qa_service.call_ai_stream(prompt, max_tokens=2500):
                full_text += chunk
                yield _sse({"type": "delta", "content": chunk})

            # 解析路径JSON
            path_data = safe_parse_json(full_text)
            if path_data and isinstance(path_data, dict):
                steps = path_data.get("steps", [])
                result_path = {
                    "goal": learning_goal,
                    "total_steps": path_data.get("total_steps", len(steps)),
                    "estimated_duration": f"{path_data.get('estimated_hours', 0)}小时",
                    "steps": [
                        {
                            "step_number": s.get("step_id", i + 1),
                            "title": s.get("title", f"步骤 {i + 1}"),
                            "description": s.get("description", s.get("learning_objective", "")),
                            "estimated_time": f"{s.get('estimated_time', 30)}分钟",
                            "prerequisites": s.get("prerequisites", []),
                            "resources": [s.get("resource_type", "")] if s.get("resource_type") else [],
                        }
                        for i, s in enumerate(steps)
                    ],
                }
                yield _sse({"type": "complete", "path": result_path})
            else:
                yield _sse({"type": "complete", "path": {"goal": learning_goal, "total_steps": 0, "estimated_duration": "0小时", "steps": []}})
        except Exception as e:
            error(f"流式路径生成失败: {e}")
            yield _sse({"type": "error", "message": f"路径生成失败: {e}"})

    async def wrapped_generator():
        async for event in sse_generator.wrap_with_heartbeat(event_generator()):
            yield event

    return StreamingResponse(
        wrapped_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no", "Content-Encoding": "identity"},
    )
