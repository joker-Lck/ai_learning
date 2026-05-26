"""
流式输出 API - SSE实时推送生成进度
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from backend.dependencies import require_auth
from services.streaming_service import sse_generator, progress_tracker
from services.content_safety_service import content_safety_service, anti_hallucination_service
from core.logger import info, error

router = APIRouter(prefix="/stream", tags=["流式输出"])


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
            async for event in sse_generator.generate_resource_stream(
                task_id=task_id,
                resource_type=resource_type,
                subject=subject,
                topic=topic,
                profile=profile
            ):
                yield event
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
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
