"""
教案 + PPT 生成 API — 教师端功能
"""
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from backend.dependencies import get_current_user
from backend.schemas.models import BaseResponse
from core.logger import error, info
from services.docx_lesson_service import docx_lesson_service
from services.lesson_plan_service import PPT_STYLES, lesson_plan_service
from services.pptx_export_service import pptx_export_service

router = APIRouter(tags=["教案PPT"])


@router.get("/styles")
async def list_ppt_styles():
    """获取可用 PPT 风格列表"""
    return BaseResponse(
        success=True,
        data=[
            {"key": k, "name": v["name"], "primary": v["primary"]}
            for k, v in PPT_STYLES.items()
        ],
    )


@router.post("/generate", response_model=BaseResponse)
async def generate_lesson_and_ppt(
    input_data: dict,
    user: dict = Depends(get_current_user),
):
    """
    一键生成教案 + PPT 内容

    请求体:
    {
        "subject": "数学",
        "topic": "函数的概念",
        "grade": "高一",
        "duration": 45,
        "style": "modern",
        "style_hint": "互动探究"       // 可选
    }
    """
    subject = input_data.get("subject", "").strip()
    topic = input_data.get("topic", "").strip()
    if not subject or not topic:
        return BaseResponse(success=False, message="学科和主题不能为空")

    grade = input_data.get("grade", "大学")
    duration = int(input_data.get("duration", 45))
    style = input_data.get("style", "modern")
    style_hint = input_data.get("style_hint", "")

    info(f"用户 {user['id']} 请求生成教案+PPT: {subject}/{topic}")
    result = lesson_plan_service.generate_full(
        subject=subject,
        topic=topic,
        grade=grade,
        duration=duration,
        style=style,
        style_hint=style_hint,
    )
    return BaseResponse(
        success=result.get("success", False),
        message="生成成功" if result.get("success") else "生成失败",
        data=result,
    )


@router.post("/export/pptx", response_model=BaseResponse)
async def export_pptx(input_data: dict):
    """
    导出 PPTX 文件

    请求体:
    {
        "ppt_content": { "slides": [...] },
        "style": "modern"
    }
    """
    ppt_content = input_data.get("ppt_content", {})
    style = input_data.get("style", "modern")
    result = pptx_export_service.export(ppt_content, style=style)
    return BaseResponse(
        success=result["success"],
        message=result.get("message", ""),
        data=result,
    )


@router.post("/export/docx", response_model=BaseResponse)
async def export_docx(input_data: dict):
    """
    导出教案 DOCX 文件

    请求体:
    {
        "lesson_plan": { ... }
    }
    """
    lesson_plan = input_data.get("lesson_plan", {})
    result = docx_lesson_service.export(lesson_plan)
    return BaseResponse(
        success=result["success"],
        message=result.get("message", ""),
        data=result,
    )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """下载导出的文件"""
    file_path = Path("exports") / filename
    if not file_path.exists():
        return BaseResponse(success=False, message="文件不存在")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )
