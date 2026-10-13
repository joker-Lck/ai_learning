"""
老师端 API — 班级管理 + 学生学情代查
全部端点要求 role ∈ {teacher, admin}
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import require_role
from backend.schemas.models import (
    BaseResponse,
    ClassCreateRequest,
    ClassUpdateRequest,
)
from services.class_service import class_service, student_monitor_service

router = APIRouter()

# 老师/管理员才能访问
require_teacher = require_role("teacher")


# ── 辅助：校验学生在老师班级内 ──
def _assert_student(teacher_id: int, student_id: int):
    if not class_service.assert_student_in_teacher_class(teacher_id, student_id):
        raise HTTPException(status_code=403, detail="该学生不在您的班级内")


# ==================== A. 班级管理 ====================

@router.post("/classes", response_model=BaseResponse)
async def create_class(req: ClassCreateRequest, user: dict = Depends(require_teacher)):
    """创建班级"""
    result = class_service.create_class(
        teacher_id=user["id"],
        name=req.name,
        subject=req.subject,
        grade_level=req.grade_level,
        semester=req.semester,
        description=req.description,
        max_students=req.max_students,
    )
    return BaseResponse(
        success=result["success"],
        message=result.get("message", "创建成功"),
        data=result,
    )


@router.get("/classes", response_model=BaseResponse)
async def list_classes(user: dict = Depends(require_teacher)):
    """我的班级列表"""
    classes = class_service.list_classes(user["id"])
    return BaseResponse(success=True, data=classes)


@router.get("/classes/{class_id}", response_model=BaseResponse)
async def get_class(class_id: int, user: dict = Depends(require_teacher)):
    """班级详情"""
    cls = class_service.get_class(class_id, teacher_id=user["id"])
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    return BaseResponse(success=True, data=cls)


@router.put("/classes/{class_id}", response_model=BaseResponse)
async def update_class(
    class_id: int,
    req: ClassUpdateRequest,
    user: dict = Depends(require_teacher),
):
    """更新班级信息"""
    fields = req.model_dump(exclude_none=True)
    result = class_service.update_class(class_id, user["id"], **fields)
    return BaseResponse(
        success=result["success"],
        message=result.get("message", ""),
        data=result,
    )


@router.post("/classes/{class_id}/reset-code", response_model=BaseResponse)
async def reset_invite_code(class_id: int, user: dict = Depends(require_teacher)):
    """重置邀请码"""
    result = class_service.reset_invite_code(class_id, user["id"])
    return BaseResponse(
        success=result["success"],
        message="邀请码已重置" if result["success"] else "重置失败",
        data=result,
    )


@router.post("/classes/{class_id}/close", response_model=BaseResponse)
async def close_class(class_id: int, user: dict = Depends(require_teacher)):
    """关闭入班"""
    result = class_service.set_class_open(class_id, user["id"], is_open=False)
    return BaseResponse(success=result["success"], message="已关闭入班")


@router.post("/classes/{class_id}/open", response_model=BaseResponse)
async def open_class(class_id: int, user: dict = Depends(require_teacher)):
    """开启入班"""
    result = class_service.set_class_open(class_id, user["id"], is_open=True)
    return BaseResponse(success=result["success"], message="已开启入班")


@router.get("/classes/{class_id}/students", response_model=BaseResponse)
async def list_class_students(class_id: int, user: dict = Depends(require_teacher)):
    """学生名单"""
    cls = class_service.get_class(class_id, teacher_id=user["id"])
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    students = class_service.list_students(class_id)
    return BaseResponse(success=True, data=students)


@router.delete("/classes/{class_id}/students/{sid}", response_model=BaseResponse)
async def remove_student(
    class_id: int, sid: int, user: dict = Depends(require_teacher)
):
    """移除学生"""
    result = class_service.remove_student(class_id, sid, user["id"])
    return BaseResponse(
        success=result["success"],
        message=result.get("message", ""),
    )


@router.get("/classes/{class_id}/overview", response_model=BaseResponse)
async def class_overview(class_id: int, user: dict = Depends(require_teacher)):
    """班级概览"""
    cls = class_service.get_class(class_id, teacher_id=user["id"])
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    overview = class_service.get_overview(class_id)
    return BaseResponse(success=True, data=overview)


# ==================== B. 学生学情代查 ====================

@router.get("/students", response_model=BaseResponse)
async def list_all_students(user: dict = Depends(require_teacher)):
    """我的全部学生（跨班）"""
    students = class_service.list_all_students(user["id"])
    return BaseResponse(success=True, data=students)


@router.get("/students/{sid}/brief", response_model=BaseResponse)
async def student_brief(sid: int, user: dict = Depends(require_teacher)):
    """学生摘要"""
    _assert_student(user["id"], sid)
    brief = student_monitor_service.get_student_brief(sid)
    return BaseResponse(success=True, data=brief)


@router.get("/students/{sid}/profile", response_model=BaseResponse)
async def student_profile(sid: int, user: dict = Depends(require_teacher)):
    """学生画像"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_profile(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/course-schedule", response_model=BaseResponse)
async def student_course_schedule(sid: int, user: dict = Depends(require_teacher)):
    """学生课程表"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_course_schedule(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/resources", response_model=BaseResponse)
async def student_resources(sid: int, user: dict = Depends(require_teacher)):
    """学生学习资源"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_resources(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/learning-path", response_model=BaseResponse)
async def student_learning_path(sid: int, user: dict = Depends(require_teacher)):
    """学生学习路径"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_learning_paths(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/quiz", response_model=BaseResponse)
async def student_quiz(sid: int, user: dict = Depends(require_teacher)):
    """学生做题数据"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_quiz_data(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/assessment", response_model=BaseResponse)
async def student_assessment(sid: int, user: dict = Depends(require_teacher)):
    """学生评估报告"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_assessments(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/analytics/{metric}", response_model=BaseResponse)
async def student_analytics(
    sid: int, metric: str, user: dict = Depends(require_teacher)
):
    """学生学情分析指标"""
    _assert_student(user["id"], sid)
    valid_metrics = {
        "overview", "subject-breakdown", "quiz-trend",
        "study-trend", "knowledge-mastery", "weekly-report",
    }
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"无效指标: {metric}")
    data = student_monitor_service.get_analytics(sid, metric)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/activities", response_model=BaseResponse)
async def student_activities(sid: int, user: dict = Depends(require_teacher)):
    """学生活跃度"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_activities(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/errors", response_model=BaseResponse)
async def student_errors(sid: int, user: dict = Depends(require_teacher)):
    """学生错题本"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_error_notes(sid)
    return BaseResponse(success=True, data=data)


@router.get("/students/{sid}/grades", response_model=BaseResponse)
async def student_grades(sid: int, user: dict = Depends(require_teacher)):
    """学生成绩"""
    _assert_student(user["id"], sid)
    data = student_monitor_service.get_grades(sid)
    return BaseResponse(success=True, data=data)
