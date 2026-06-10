"""
学习智能体 API - 多智能体系统接口
包括学生画像、资源生成、路径规划、智能辅导、效果评估
"""
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form, Query
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


@router.post("/update-profile-field", response_model=BaseResponse)
async def update_profile_field(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """更新画像单个字段"""
    try:
        field = input_data.get("field", "")
        value = input_data.get("value")
        result = profile_agent.update_profile_field(user["id"], field, value)
        return BaseResponse(**result)
    except Exception as e:
        error(f"update-profile-field 失败: {e}")
        return BaseResponse(success=False, message=str(e))


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
    智能辅导答疑 - 多模态解答（记忆增强版）

    输入格式:
    {
        "question": "问题内容",
        "subject": "学科",
        "preferred_format": "text/diagram/video/all",
        "session_id": "会话ID（可选）"
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 请求智能辅导, 问题: {input_data.get('question', '')[:50]}")

        # 验证必填字段
        if not input_data.get("question"):
            return JSONResponse(content={"success": False, "message": "问题内容不能为空", "data": None})

        # 使用辅导服务（已集成记忆增强）
        from services.tutor_agent import tutor_agent
        result = tutor_agent.answer_query(user_id, input_data)

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


@router.get("/knowledge-map")
async def get_knowledge_map(
    user: dict = Depends(get_current_user)
):
    """获取用户知识图谱"""
    try:
        from services.tutor_agent import tutor_agent
        knowledge_map = tutor_agent.get_user_knowledge_map(user['id'])
        return {"success": True, "data": knowledge_map}
    except Exception as e:
        error(f"获取知识图谱失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-recommendations")
async def get_learning_recommendations(
    subject: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    """获取基于记忆的学习推荐"""
    try:
        from services.tutor_agent import tutor_agent
        recommendations = tutor_agent.get_learning_recommendations(user['id'], subject)
        return {"success": True, "data": {"recommendations": recommendations}}
    except Exception as e:
        error(f"获取学习推荐失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/maintenance")
async def apply_memory_maintenance(
    user: dict = Depends(require_auth)
):
    """应用记忆维护（遗忘曲线、清理等）"""
    try:
        from services.tutor_agent import tutor_agent
        result = tutor_agent.apply_memory_maintenance(user['id'])
        return {"success": True, "data": result}
    except Exception as e:
        error(f"记忆维护失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


# ========== RAG 知识库上传 ==========
@router.post("/upload-to-rag", response_model=BaseResponse)
async def upload_to_rag(
    files: List[UploadFile] = File(...),
    subject: str = Form(""),
    user: dict = Depends(get_current_user),
):
    """
    上传学习资料到 RAG 知识库
    支持格式: txt, md, pdf, doc, docx, ppt, pptx
    """
    ALLOWED = {'.txt', '.md', '.pdf', '.doc', '.docx', '.ppt', '.pptx'}
    MAX_SIZE = 20 * 1024 * 1024

    try:
        user_id = user["id"]
        from data.rag_knowledge_base import rag_kb

        results = []
        for f in files:
            ext = '.' + f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
            if ext not in ALLOWED:
                results.append({"filename": f.filename, "success": False, "message": f"不支持格式 {ext}"})
                continue

            content = await f.read()
            if len(content) > MAX_SIZE:
                results.append({"filename": f.filename, "success": False, "message": "文件超过 20MB"})
                continue

            text = document_analysis_service._parse_file(f.filename, content)
            if not text or text.startswith("["):
                results.append({"filename": f.filename, "success": False, "message": "文件解析失败"})
                continue

            # AI 提取知识点
            kp_prompt = f"从以下文本中提取5-15个关键知识点名称，用JSON数组返回（只输出JSON数组）:\n{text[:4000]}"
            try:
                from services.spark_client import spark_client
                from core.json_utils import safe_parse_json
                kp_resp = spark_client.simple(kp_prompt, max_tokens=500)
                kp_list = safe_parse_json(kp_resp)
                if not isinstance(kp_list, list):
                    kp_list = []
            except Exception:
                kp_list = []

            # AI 生成摘要
            summary_prompt = f"用100字以内概括以下教材内容（只输出摘要文字）:\n{text[:3000]}"
            try:
                summary = spark_client.simple(summary_prompt, max_tokens=200)
            except Exception:
                summary = text[:200]

            title = f.filename.rsplit('.', 1)[0]
            doc_id = rag_kb.add_document(
                title=title,
                subject=subject or "综合",
                file_path=f.filename,
                file_type=ext.lstrip('.'),
                content_text=text,
                knowledge_points=kp_list,
                ai_summary=summary,
                uploaded_by=str(user_id),
                file_size=len(content),
            )

            if doc_id:
                results.append({"filename": f.filename, "success": True, "doc_id": doc_id,
                                "knowledge_points": len(kp_list), "summary": summary})
            else:
                results.append({"filename": f.filename, "success": False, "message": "写入数据库失败"})

        success_count = sum(1 for r in results if r["success"])
        return BaseResponse(
            success=success_count > 0,
            message=f"成功导入 {success_count}/{len(results)} 个文件到知识库",
            data={"results": results},
        )

    except Exception as e:
        error(f"RAG上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-documents", response_model=BaseResponse)
async def list_rag_documents(
    user: dict = Depends(get_current_user),
    limit: int = 200,
):
    """获取 RAG 知识库文档列表"""
    try:
        from data.rag_knowledge_base import rag_kb
        docs = rag_kb.get_all_documents(limit=limit)
        return BaseResponse(success=True, message="获取成功", data={"documents": docs})
    except Exception as e:
        error(f"获取RAG文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学生数据管理 API ====================

from services.student_data_service import student_data_service


@router.post("/save-course-schedule", response_model=BaseResponse)
async def save_course_schedule(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """保存学期课程表"""
    try:
        result = student_data_service.save_course_schedule(
            user["id"], input_data["semester"], input_data["courses"]
        )
        return BaseResponse(**result)
    except KeyError as e:
        return BaseResponse(success=False, message=f"缺少参数: {e}")
    except Exception as e:
        error(f"save-course-schedule 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.get("/get-course-schedule", response_model=BaseResponse)
async def get_course_schedule(
    semester: str = "",
    user: dict = Depends(require_auth),
):
    """获取学期课程表"""
    try:
        result = student_data_service.get_course_schedule(user["id"], semester)
        return BaseResponse(**result)
    except Exception as e:
        error(f"get-course-schedule 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.get("/list-semesters", response_model=BaseResponse)
async def list_semesters(user: dict = Depends(require_auth)):
    """列出用户所有学期"""
    try:
        result = student_data_service.list_semesters(user["id"])
        return BaseResponse(**result)
    except Exception as e:
        error(f"list-semesters 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/save-grades", response_model=BaseResponse)
async def save_grades(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """保存学习成绩"""
    try:
        result = student_data_service.save_grades(
            user["id"], input_data["semester"], input_data["grades"]
        )
        return BaseResponse(**result)
    except KeyError as e:
        return BaseResponse(success=False, message=f"缺少参数: {e}")
    except Exception as e:
        error(f"save-grades 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.get("/get-grades", response_model=BaseResponse)
async def get_grades(
    semester: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """获取学习成绩"""
    try:
        result = student_data_service.get_grades(user["id"], semester)
        return BaseResponse(**result)
    except Exception as e:
        error(f"get-grades 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/save-error-note", response_model=BaseResponse)
async def save_error_note(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """添加错题"""
    try:
        result = student_data_service.save_error_note(user["id"], input_data)
        return BaseResponse(**result)
    except Exception as e:
        error(f"save-error-note 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.get("/get-error-notes", response_model=BaseResponse)
async def get_error_notes(
    subject: Optional[str] = None,
    mastery: Optional[int] = None,
    user: dict = Depends(require_auth),
):
    """获取错题列表"""
    try:
        result = student_data_service.get_error_notes(user["id"], subject, mastery)
        return BaseResponse(**result)
    except Exception as e:
        error(f"get-error-notes 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/update-error-mastery", response_model=BaseResponse)
async def update_error_mastery(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """更新错题掌握状态"""
    try:
        result = student_data_service.update_error_note_mastery(
            user["id"], input_data["note_id"], input_data["mastery"]
        )
        return BaseResponse(**result)
    except KeyError as e:
        return BaseResponse(success=False, message=f"缺少参数: {e}")
    except Exception as e:
        error(f"update-error-mastery 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/delete-error-note", response_model=BaseResponse)
async def delete_error_note(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """删除错题"""
    try:
        result = student_data_service.delete_error_note(user["id"], input_data["note_id"])
        return BaseResponse(**result)
    except KeyError as e:
        return BaseResponse(success=False, message=f"缺少参数: {e}")
    except Exception as e:
        error(f"delete-error-note 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.post("/generate-study-plan", response_model=BaseResponse)
async def generate_study_plan(
    input_data: Dict[str, Any] = Body(...),
    user: dict = Depends(require_auth),
):
    """AI 生成学习计划"""
    try:
        result = student_data_service.generate_study_plan(user["id"], input_data)
        return BaseResponse(**result)
    except Exception as e:
        error(f"generate-study-plan 失败: {e}")
        return BaseResponse(success=False, message=str(e))


@router.get("/get-study-plans", response_model=BaseResponse)
async def get_study_plans(
    semester: Optional[str] = None,
    user: dict = Depends(require_auth),
):
    """获取学习计划列表"""
    try:
        result = student_data_service.get_study_plans(user["id"], semester)
        return BaseResponse(**result)
    except Exception as e:
        error(f"get-study-plans 失败: {e}")
        return BaseResponse(success=False, message=str(e))


# ==================== 文件导入（AI 识别）====================

@router.post("/import-courses-from-file", response_model=BaseResponse)
async def import_courses_from_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_auth),
):
    """从文件中 AI 识别课程表并预览"""
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            return BaseResponse(success=False, message="文件超过 10MB 限制", data=None)
        result = student_data_service.import_courses_from_file(user["id"], file.filename, content)
        return BaseResponse(**result)
    except Exception as e:
        error(f"导入课程表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-grades-from-file", response_model=BaseResponse)
async def import_grades_from_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_auth),
):
    """从文件中 AI 识别成绩并预览"""
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            return BaseResponse(success=False, message="文件超过 10MB 限制", data=None)
        result = student_data_service.import_grades_from_file(user["id"], file.filename, content)
        return BaseResponse(**result)
    except Exception as e:
        error(f"导入成绩失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-errors-from-file", response_model=BaseResponse)
async def import_errors_from_file(
    file: UploadFile = File(...),
    user: dict = Depends(require_auth),
):
    """从文件中 AI 识别错题并预览"""
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            return BaseResponse(success=False, message="文件超过 10MB 限制", data=None)
        result = student_data_service.import_errors_from_file(user["id"], file.filename, content)
        return BaseResponse(**result)
    except Exception as e:
        error(f"导入错题失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
