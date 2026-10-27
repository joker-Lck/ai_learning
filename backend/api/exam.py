"""
教师端 AI 出题/组卷 + 主观题批改 API
- 老师：组卷、试卷管理、导出、发布到班级、上传手写答案、AI 批改、复核、班级报告
- 学生：查看作业、提交作答（文本 + 手写图）
"""

from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from backend.dependencies import require_auth, require_role
from backend.schemas.models import BaseResponse
from services.exam_docx_service import exam_docx_service
from services.exam_paper_service import exam_paper_service
from services.grading_service import grading_service

router = APIRouter()

require_teacher = require_role("teacher")

MAX_IMAGE_SIZE = 15 * 1024 * 1024
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _resp(result: dict) -> BaseResponse:
    """服务层结果 → BaseResponse（额外字段并入 data，防丢失）"""
    extra = {k: v for k, v in result.items() if k not in ("success", "message", "error", "data")}
    data = result.get("data")
    if extra:
        data = {**(data or {}), **extra}
    return BaseResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        error=result.get("error"),
        data=data,
    )


def _assert_paper_owner(paper_id: int, teacher_id: int) -> dict:
    paper = exam_paper_service.get_paper(paper_id, teacher_id)
    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在或无权限")
    return paper


def _assert_assignment_owner(assignment_id: int, teacher_id: int) -> dict:
    a = exam_paper_service.get_assignment(assignment_id, teacher_id)
    if not a:
        raise HTTPException(status_code=404, detail="发布记录不存在或无权限")
    return a


def _get_submission_or_404(submission_id: int) -> dict:
    sub = grading_service.get_submission_detail(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    return sub


def _check_submission_access(sub: dict, user: dict, need_teacher: bool = False) -> None:
    role = user.get("role", "")
    if role in ("teacher", "admin"):
        a = exam_paper_service.get_assignment(sub["assignment_id"])
        if not a or (a["assigned_by"] != user["id"] and role != "admin"):
            raise HTTPException(status_code=403, detail="无权限操作该提交")
    elif need_teacher:
        raise HTTPException(status_code=403, detail="仅教师可执行此操作")
    else:
        if sub.get("student_id") != user["id"]:
            raise HTTPException(status_code=403, detail="只能操作自己的作答")


async def _read_image(file: UploadFile) -> bytes:
    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/bmp/webp 图片")
    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 15MB")
    if not data:
        raise HTTPException(status_code=400, detail="图片内容为空")
    return data


# ==================== A. 试卷生成与管理（教师） ====================

@router.post("/papers/generate", response_model=BaseResponse)
async def generate_paper(input_data: dict = Body(...), user: dict = Depends(require_teacher)):
    """AI 组卷（预览用，不自动落库）"""
    params = dict(input_data)
    params["teacher_id"] = user["id"]
    result = exam_paper_service.generate_paper(params)
    return BaseResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        data=result.get("data"),
        error=result.get("error"),
    )


@router.post("/papers", response_model=BaseResponse)
async def save_paper(input_data: dict = Body(...), user: dict = Depends(require_teacher)):
    """保存试卷（新建）"""
    paper = dict(input_data)
    paper["teacher_id"] = user["id"]
    result = exam_paper_service.save_paper(paper)
    return _resp(result)


@router.get("/papers", response_model=BaseResponse)
async def list_papers(
    subject: str | None = Query(None),
    paper_type: str | None = Query(None),
    user: dict = Depends(require_teacher),
):
    """我的试卷列表"""
    papers = exam_paper_service.list_papers(user["id"], subject=subject, paper_type=paper_type)
    return BaseResponse(success=True, data=papers)


@router.get("/papers/{paper_id}", response_model=BaseResponse)
async def get_paper(paper_id: int, user: dict = Depends(require_teacher)):
    """试卷详情（含题目）"""
    paper = _assert_paper_owner(paper_id, user["id"])
    return BaseResponse(success=True, data=paper)


@router.put("/papers/{paper_id}", response_model=BaseResponse)
async def update_paper(
    paper_id: int,
    input_data: dict = Body(...),
    user: dict = Depends(require_teacher),
):
    """更新试卷（含题目整体替换）"""
    _assert_paper_owner(paper_id, user["id"])
    result = exam_paper_service.update_paper(paper_id, user["id"], input_data)
    return _resp(result)


@router.delete("/papers/{paper_id}", response_model=BaseResponse)
async def delete_paper(paper_id: int, user: dict = Depends(require_teacher)):
    """删除试卷"""
    result = exam_paper_service.delete_paper(paper_id, user["id"])
    return _resp(result)


@router.post("/papers/{paper_id}/export", response_model=BaseResponse)
async def export_paper(paper_id: int, user: dict = Depends(require_teacher)):
    """导出可打印 DOCX 试卷（含答案解析）"""
    paper = _assert_paper_owner(paper_id, user["id"])
    result = exam_docx_service.export(paper, with_answers=True)
    return _resp(result)


@router.get("/download/{filename}")
async def download_file(filename: str, user: dict = Depends(require_auth)):
    """下载导出文件（防目录穿越）"""
    safe_name = Path(filename).name
    file_path = Path("exports") / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(file_path), filename=safe_name,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ==================== B. 发布到班级（教师） ====================

@router.post("/papers/{paper_id}/assign", response_model=BaseResponse)
async def assign_paper(
    paper_id: int,
    input_data: dict = Body(...),
    user: dict = Depends(require_teacher),
):
    """发布试卷到班级"""
    _assert_paper_owner(paper_id, user["id"])
    result = exam_paper_service.assign_paper(
        paper_id, user["id"],
        class_id=int(input_data.get("class_id") or 0),
        due_at=input_data.get("due_at"),
        title=input_data.get("title"),
        allow_late=bool(input_data.get("allow_late", True)),
    )
    return _resp(result)


@router.get("/assignments", response_model=BaseResponse)
async def list_assignments(user: dict = Depends(require_teacher)):
    """我发布的作业/考试列表"""
    rows = exam_paper_service.list_assignments(user["id"])
    return BaseResponse(success=True, data=rows)


@router.get("/assignments/{assignment_id}", response_model=BaseResponse)
async def get_assignment(assignment_id: int, user: dict = Depends(require_teacher)):
    """发布详情（含试卷题目）"""
    a = _assert_assignment_owner(assignment_id, user["id"])
    paper = exam_paper_service.get_paper(a["paper_id"])
    a["paper"] = paper
    return BaseResponse(success=True, data=a)


@router.post("/assignments/{assignment_id}/close", response_model=BaseResponse)
async def close_assignment(assignment_id: int, user: dict = Depends(require_teacher)):
    """截止收卷"""
    result = exam_paper_service.close_assignment(assignment_id, user["id"])
    return _resp(result)


# ==================== C. 提交与批改（教师为主） ====================

@router.post("/submissions", response_model=BaseResponse)
async def create_submission(input_data: dict = Body(...), user: dict = Depends(require_auth)):
    """创建/获取作答记录：教师可代建；学生只能建自己的"""
    assignment_id = int(input_data.get("assignment_id") or 0)
    a = exam_paper_service.get_assignment(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    if user.get("role") in ("teacher", "admin"):
        if a["assigned_by"] != user["id"] and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="无权限操作该作业")
        student_id = int(input_data.get("student_id") or 0)
        if not student_id:
            raise HTTPException(status_code=400, detail="缺少 student_id")
    else:
        student_id = user["id"]
    result = grading_service.get_or_create_submission(assignment_id, a["paper_id"], student_id)
    return _resp(result)


@router.get("/assignments/{assignment_id}/submissions", response_model=BaseResponse)
async def list_submissions(assignment_id: int, user: dict = Depends(require_teacher)):
    """提交列表（批改进度一览）"""
    _assert_assignment_owner(assignment_id, user["id"])
    rows = grading_service.list_submissions(assignment_id)
    return BaseResponse(success=True, data=rows)


@router.get("/submissions/{submission_id}", response_model=BaseResponse)
async def get_submission(submission_id: int, user: dict = Depends(require_auth)):
    """提交详情（逐题作答 + 批改结果）"""
    sub = _get_submission_or_404(submission_id)
    _check_submission_access(sub, user)
    return BaseResponse(success=True, data=sub)


@router.post("/submissions/{submission_id}/answers/{question_id}/image", response_model=BaseResponse)
async def upload_answer_image(
    submission_id: int,
    question_id: int,
    file: UploadFile = File(...),
    ocr: bool = Query(True, description="上传后自动手写识别"),
    user: dict = Depends(require_auth),
):
    """上传手写答案图片（自动 OCR 识别）"""
    sub = _get_submission_or_404(submission_id)
    _check_submission_access(sub, user)
    data = await _read_image(file)
    result = grading_service.save_answer_image(submission_id, question_id, data, file.filename or "")
    if not result.get("success"):
        return _resp(result)
    if ocr:
        ocr_result = grading_service.ocr_answer(result["answer_id"])
        result["ocr"] = ocr_result
    return BaseResponse(success=True, message="图片已保存", data=result)


@router.get("/answers/{answer_id}/image")
async def get_answer_image(answer_id: int, user: dict = Depends(require_auth)):
    """查看手写答案图片（带权限校验）"""
    from data.config import get_assessments_db_path
    from services.exam_paper_service import _conn, _row

    c = _conn(get_assessments_db_path())
    try:
        row = _row(c.execute(
            "SELECT submission_id, answer_image_path FROM exam_answers WHERE id = ?", (answer_id,)
        ))
    finally:
        c.close()
    if not row or not row.get("answer_image_path"):
        raise HTTPException(status_code=404, detail="图片不存在")
    sub = _get_submission_or_404(row["submission_id"])
    _check_submission_access(sub, user)
    img_path = Path(row["answer_image_path"])
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="图片文件缺失")
    media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
             ".bmp": "image/bmp", ".webp": "image/webp"}.get(img_path.suffix.lower(), "image/jpeg")
    return FileResponse(str(img_path), media_type=media)


@router.post("/answers/{answer_id}/ocr", response_model=BaseResponse)
async def ocr_answer(answer_id: int, user: dict = Depends(require_auth)):
    """对已上传手写图执行/重跑手写识别"""
    from data.config import get_assessments_db_path
    from services.exam_paper_service import _conn, _row

    c = _conn(get_assessments_db_path())
    try:
        row = _row(c.execute("SELECT submission_id FROM exam_answers WHERE id = ?", (answer_id,)))
    finally:
        c.close()
    if not row:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    sub = _get_submission_or_404(row["submission_id"])
    _check_submission_access(sub, user)
    result = grading_service.ocr_answer(answer_id)
    return _resp(result)


@router.put("/answers/{answer_id}", response_model=BaseResponse)
async def update_answer(
    answer_id: int,
    input_data: dict = Body(...),
    user: dict = Depends(require_auth),
):
    """修改作答文本（OCR 识别修正）"""
    from data.config import get_assessments_db_path
    from services.exam_paper_service import _conn, _row

    c = _conn(get_assessments_db_path())
    try:
        row = _row(c.execute("SELECT submission_id FROM exam_answers WHERE id = ?", (answer_id,)))
    finally:
        c.close()
    if not row:
        raise HTTPException(status_code=404, detail="作答记录不存在")
    sub = _get_submission_or_404(row["submission_id"])
    _check_submission_access(sub, user)
    c = _conn(get_assessments_db_path())
    try:
        c.execute("UPDATE exam_answers SET answer_text = ? WHERE id = ?",
                  (input_data.get("answer_text") or "", answer_id))
        c.commit()
    finally:
        c.close()
    return BaseResponse(success=True, message="已更新")


@router.post("/answers/{answer_id}/grade", response_model=BaseResponse)
async def grade_answer(answer_id: int, user: dict = Depends(require_teacher)):
    """AI 批改单题（客观题自动判分；主观题 RAG + AI 评分）"""
    result = grading_service.grade_answer(answer_id)
    return BaseResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        data=result,
    )


@router.post("/submissions/{submission_id}/grade", response_model=BaseResponse)
async def grade_submission(submission_id: int, user: dict = Depends(require_teacher)):
    """AI 批改整卷"""
    _get_submission_or_404(submission_id)
    result = grading_service.grade_submission(submission_id)
    return _resp(result)


@router.put("/answers/{answer_id}/review", response_model=BaseResponse)
async def review_answer(
    answer_id: int,
    input_data: dict = Body(...),
    user: dict = Depends(require_teacher),
):
    """教师复核改分（最终成绩以教师为准）"""
    score = input_data.get("teacher_score")
    result = grading_service.review_answer(
        answer_id,
        float(score) if score is not None else None,
        input_data.get("teacher_feedback"),
    )
    return _resp(result)


@router.get("/assignments/{assignment_id}/report", response_model=BaseResponse)
async def class_report(assignment_id: int, user: dict = Depends(require_teacher)):
    """班级批改报告（得分分布 / 逐题统计 / 薄弱知识点）"""
    _assert_assignment_owner(assignment_id, user["id"])
    result = grading_service.class_report(assignment_id)
    return BaseResponse(success=result.get("success", False),
                        message=result.get("message", ""), data=result.get("data"))


# ==================== D. 学生端（最小闭环） ====================

@router.get("/my-assignments", response_model=BaseResponse)
async def my_assignments(user: dict = Depends(require_auth)):
    """我的班级作业列表"""
    from data.config import get_assessments_db_path, get_auth_db_path
    from services.exam_paper_service import _conn, _rows

    try:
        ac = _conn(get_auth_db_path())
        try:
            classes = _rows(ac.execute(
                "SELECT class_id FROM class_students WHERE student_id = ?", (user["id"],)
            ))
        finally:
            ac.close()
        class_ids = [c["class_id"] for c in classes]
        if not class_ids:
            return BaseResponse(success=True, data=[])
        placeholders = ",".join(["?"] * len(class_ids))
        c = _conn(get_assessments_db_path())
        try:
            rows = _rows(c.execute(
                f"""SELECT a.*, p.title, p.subject, p.total_score, p.paper_type,
                           p.duration_minutes,
                           (SELECT status FROM exam_submissions s
                            WHERE s.assignment_id = a.id AND s.student_id = ?) AS my_status
                    FROM exam_assignments a
                    JOIN exam_papers p ON p.id = a.paper_id
                    WHERE a.class_id IN ({placeholders}) AND a.status = 'active'
                    ORDER BY a.created_at DESC""",
                [user["id"]] + class_ids,
            ))
            return BaseResponse(success=True, data=rows)
        finally:
            c.close()
    except Exception as e:
        return BaseResponse(success=False, message=f"查询失败: {e}")


@router.get("/assignments/{assignment_id}/paper", response_model=BaseResponse)
async def student_get_paper(assignment_id: int, user: dict = Depends(require_auth)):
    """学生获取作业题目（不含答案）"""
    from data.config import get_assessments_db_path, get_auth_db_path
    from services.exam_paper_service import _conn, _row

    a = exam_paper_service.get_assignment(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="作业不存在")
    c = _conn(get_auth_db_path())
    try:
        in_class = _row(c.execute(
            "SELECT 1 AS x FROM class_students WHERE class_id = ? AND student_id = ?",
            (a["class_id"], user["id"]),
        ))
    finally:
        c.close()
    if not in_class and user.get("role") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="不在该班级内")
    paper = exam_paper_service.get_paper(a["paper_id"])
    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在")
    # 脱敏：去掉答案与解析
    for q in paper.get("questions") or []:
        q.pop("correct_answer", None)
        q.pop("answer", None)
        q.pop("reference_answer", None)
        q.pop("scoring_points", None)
        q.pop("explanation", None)
    data = {**a, "paper": paper}
    return BaseResponse(success=True, data=data)


@router.post("/assignments/{assignment_id}/submit", response_model=BaseResponse)
async def student_submit(
    assignment_id: int,
    input_data: dict = Body(...),
    user: dict = Depends(require_auth),
):
    """学生提交作答（文本答案）"""
    a = exam_paper_service.get_assignment(assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="作业不存在")
    result = grading_service.get_or_create_submission(assignment_id, a["paper_id"], user["id"])
    if not result.get("success"):
        return _resp(result)
    sub_id = result["data"]["id"]
    for item in (input_data.get("answers") or []):
        if not isinstance(item, dict):
            continue
        qid = item.get("question_id")
        if not qid:
            continue
        grading_service.save_answer(sub_id, int(qid), answer_text=str(item.get("answer_text") or ""))
    done = grading_service.submit(sub_id)
    return BaseResponse(success=done.get("success", False),
                        message=done.get("message", ""), data={"submission_id": sub_id})
