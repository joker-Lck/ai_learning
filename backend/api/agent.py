"""
学习智能体 API - 多智能体系统接口
包括学生画像、资源生成、路径规划、智能辅导、效果评估
"""
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from backend.schemas.models import BaseResponse
from backend.dependencies import require_auth, get_current_user
from services.agent_coordinator import agent_coordinator
from services.profile_agent import ProfileAgent
from services.path_agent import PathAgent
from services.assessment_agent import AssessmentAgent
from services.resource_export_service import resource_export_service
from services.document_analysis_service import document_analysis_service
from core.logger import info, error

router = APIRouter(prefix="/agent", tags=["学习智能体"])

profile_agent = ProfileAgent()
path_agent = PathAgent()
assessment_agent = AssessmentAgent()


@router.post("/build-profile", response_model=BaseResponse)
async def build_student_profile(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    构建学生画像 - 对话式构建≥6维度的动态画像
    
    输入格式:
    {
        "conversation_log": [{"role": "user", "content": "..."}],
        "basic_info": {"major": "...", "grade_level": "..."}
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求构建学生画像")
        
        result = agent_coordinator.execute_task(
            task_type="build_profile",
            user_id=user_id,
            input_data=input_data
        )
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except Exception as e:
        error(f"构建学生画像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-profile", response_model=BaseResponse)
async def get_student_profile(user: dict = Depends(require_auth)):
    """获取当前用户的学生画像"""
    try:
        user_id = user["id"]
        result = profile_agent.get_or_build_profile(user_id)
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("profile")
        )
        
    except Exception as e:
        error(f"获取学生画像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-resources", response_model=BaseResponse)
async def generate_learning_resources(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    生成多模态学习资源 - 支持7种类型
    
    输入格式:
    {
        "subject": "学科",
        "topic": "主题",
        "resource_types": ["document", "quiz", "mindmap", "video", "animation", "code_case", "reading"],
        "difficulty": "beginner/intermediate/advanced"
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求生成学习资源: {input_data.get('topic')}")
        
        # 获取学生画像
        profile_result = profile_agent.get_or_build_profile(user_id)
        input_data["profile"] = profile_result.get("profile", {})
        
        result = agent_coordinator.execute_task(
            task_type="generate_resources",
            user_id=user_id,
            input_data=input_data
        )
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except Exception as e:
        error(f"生成学习资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan-path", response_model=BaseResponse)
async def plan_learning_path(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    规划个性化学习路径
    
    输入格式:
    {
        "learning_goal": "学习目标",
        "resources": [可选的资源列表]
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求规划学习路径")
        
        # 获取学生画像
        profile_result = profile_agent.get_or_build_profile(user_id)
        input_data["profile"] = profile_result.get("profile", {})
        
        result = agent_coordinator.execute_task(
            task_type="plan_learning_path",
            user_id=user_id,
            input_data=input_data
        )
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except Exception as e:
        error(f"规划学习路径失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor")
async def tutor_query(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    智能辅导答疑 - 多模态解答

    输入格式:
    {
        "question": "问题内容",
        "subject": "学科",
        "preferred_format": "text/diagram/video/all"
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求智能辅导, 问题: {input_data.get('question', '')[:50]}")

        # 验证必填字段
        if not input_data.get("question"):
            return JSONResponse(content={"success": False, "message": "问题内容不能为空", "data": None})

        result = agent_coordinator.execute_task(
            task_type="tutor_query",
            user_id=user_id,
            input_data=input_data
        )

        info(f"辅导结果 - success: {result.get('success')}, 数据大小: {len(str(result.get('data', '')))} 字符")

        import json
        resp_content = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": result.get("data"),
        }
        # 确保可序列化
        try:
            json.dumps(resp_content, ensure_ascii=False)
        except (TypeError, ValueError) as ser_err:
            error(f"JSON 序列化失败，降级处理: {ser_err}")
            resp_content["data"] = str(result.get("data", ""))

        return JSONResponse(content=resp_content)

    except Exception as e:
        error(f"智能辅导失败: {str(e)}")
        import traceback
        error(f"异常堆栈: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"辅导失败: {str(e)}", "data": None}
        )


@router.post("/assess", response_model=BaseResponse)
async def assess_learning(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    学习效果评估
    
    输入格式:
    {
        "assessment_type": "weekly/monthly/custom",
        "period_start": "2024-01-01",  # 可选
        "period_end": "2024-01-07"      # 可选
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求学习效果评估")
        
        result = agent_coordinator.execute_task(
            task_type="assess_learning",
            user_id=user_id,
            input_data=input_data
        )
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except Exception as e:
        error(f"学习效果评估失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive-plan", response_model=BaseResponse)
async def comprehensive_learning_plan(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """
    综合学习计划 - 多智能体协同
    
    输入格式:
    {
        "subject": "学科",
        "topic": "主题",
        "learning_goal": "学习目标",
        "resource_types": ["document", "quiz", "mindmap"]
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求综合学习计划")
        
        result = agent_coordinator.execute_task(
            task_type="comprehensive_learning_plan",
            user_id=user_id,
            input_data=input_data
        )
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except Exception as e:
        error(f"综合学习计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-path-progress", response_model=BaseResponse)
async def update_path_progress(
    path_id: int = Body(...),
    completed_step: int = Body(...),
    user: dict = Depends(require_auth)
):
    """更新学习路径进度"""
    try:
        user_id = user["id"]
        result = path_agent.update_path_progress(path_id, completed_step)
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("path_data")
        )
        
    except Exception as e:
        error(f"更新路径进度失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-profile-from-learning", response_model=BaseResponse)
async def update_profile_from_learning(
    learning_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth)
):
    """根据学习行为动态更新画像"""
    try:
        user_id = user["id"]
        result = profile_agent.update_profile_from_learning(user_id, learning_data)
        
        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("profile")
        )
        
    except Exception as e:
        error(f"更新画像失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-resource", response_model=BaseResponse)
async def export_resource_file(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)  # 允许guest用户
):
    """
    导出学习资源为文件
    
    输入格式:
    {
        "resource": 完整的资源数据对象
    }
    
    输出格式:
    - document/quiz → Word文档 (.docx)
    - mindmap → JPG图片 (.jpg)
    - video/animation → 文本脚本 (.txt)
    - code_case/reading → Markdown文件 (.md)
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求导出资源: {input_data.get('resource', {}).get('title')}")
        
        resource = input_data.get("resource", {})
        if not resource:
            return BaseResponse(
                success=False,
                message="资源数据不能为空",
                data=None
            )
        
        # 调用导出服务
        result = resource_export_service.export_resource(resource)
        
        if result.get("success"):
            info(f"资源导出成功: {result.get('file_path')}")
            return BaseResponse(
                success=True,
                message=result.get("message", "导出成功"),
                data={
                    "file_path": result.get("file_path"),
                    "filename": result.get("filename"),
                    "file_type": result.get("file_type")
                }
            )
        else:
            return BaseResponse(
                success=False,
                message=result.get("message", "导出失败"),
                data=None
            )
        
    except Exception as e:
        error(f"导出资源失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-documents", response_model=BaseResponse)
async def analyze_documents(
    files: List[UploadFile] = File(...),
    subject: str = Form(""),
    topic: str = Form(""),
    difficulty: str = Form(""),
    user: dict = Depends(get_current_user),
):
    """
    上传学习资料并进行AI分析

    支持格式: txt, md, pdf, doc, docx, ppt, pptx, jpg, jpeg, png
    最大单文件: 10MB, 最大总大小: 30MB, 最多10个文件
    """
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png'}
    MAX_SINGLE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TOTAL_SIZE = 30 * 1024 * 1024   # 30MB
    MAX_FILES = 10

    try:
        user_id = user["id"]

        if len(files) > MAX_FILES:
            return BaseResponse(success=False, message=f"最多上传 {MAX_FILES} 个文件", data=None)

        total_size = 0
        file_data = []
        for f in files:
            # 校验扩展名
            ext = ''
            if f.filename:
                ext = '.' + f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
            if ext not in ALLOWED_EXTENSIONS:
                return BaseResponse(
                    success=False,
                    message=f"不支持的文件格式: {ext}。允许: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                    data=None,
                )

            content = await f.read()

            if len(content) > MAX_SINGLE_SIZE:
                return BaseResponse(success=False, message=f"文件 {f.filename} 超过 10MB 限制", data=None)

            total_size += len(content)
            if total_size > MAX_TOTAL_SIZE:
                return BaseResponse(success=False, message="总文件大小超过 30MB 限制", data=None)

            file_data.append({
                "filename": f.filename,
                "content": content,
                "size": len(content),
            })

        info(f"用户 {user_id} 上传 {len(file_data)} 个文件进行分析")

        result = document_analysis_service.analyze_documents(
            files=file_data,
            user_context={"subject": subject, "topic": topic, "difficulty": difficulty},
        )

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data"),
        )

    except Exception as e:
        error(f"文档分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
