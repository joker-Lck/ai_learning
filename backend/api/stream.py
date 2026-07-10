"""
流式输出 API - SSE实时推送生成进度
"""

import uuid
import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from backend.dependencies import require_auth, get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.streaming_service import sse_generator, progress_tracker
from services.resource_agent import resource_agent
from services.content_safety_service import content_safety_service, anti_hallucination_service
from services.tutor_agent import tutor_agent
from services.qa_service import qa_service
from core.logger import info, error

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
        error(f"流式生成资源失败: {str(e)}")
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
                    from starlette.requests import Request as _Req
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
                    error(f"资源生成异常 [{rtype}]: {e}")
                    yield _sse({
                        "type": "resource_error",
                        "resource_type": rtype,
                        "error": str(e),
                        "elapsed_seconds": elapsed
                    })

            yield _sse({
                "type": "complete",
                "progress": 100,
                "message": f"✅ 全部 {total} 种资源生成完成!"
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
        error(f"流式生成资源失败: {str(e)}")
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
    content_data: Dict[str, Any],
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
        error(f"内容安全检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-fact")
async def verify_fact_api(
    fact_data: Dict[str, Any],
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
        error(f"事实验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-citations")
async def add_citations_api(
    citation_data: Dict[str, Any],
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
        error(f"添加引用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cross-validate")
async def cross_validate_api(
    validation_data: Dict[str, Any],
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
        error(f"交叉验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor")
async def stream_tutor_query(
    input_data: Dict[str, Any],
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
