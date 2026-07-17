"""
学习智能体 API - 多智能体系统接口
包括学生画像、资源生成、路径规划、智能辅导、效果评估
"""
import json
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from backend.dependencies import get_current_user, require_auth
from backend.schemas.models import BaseResponse
from backend.schemas.request_models import (
    GenerateResourcesRequest,
    TutorQueryRequest,
)
from core.logger import error, info, warning
from data.dao import get_activity_dao, get_resource_dao
from services.agent_coordinator import agent_coordinator
from services.assessment_agent import AssessmentAgent
from services.document_analysis_service import document_analysis_service
from services.path_agent import PathAgent
from services.profile_agent import ProfileAgent
from services.resource_export_service import resource_export_service

router = APIRouter(prefix="/agent", tags=["学习智能体"])

profile_agent = ProfileAgent()
path_agent = PathAgent()
assessment_agent = AssessmentAgent()


@router.post("/build-profile", response_model=BaseResponse)
async def build_student_profile(
    input_data: dict[str, Any] = Body(...),
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
        error(f"构建学生画像失败: {e!s}")
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
        error(f"获取学生画像失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-profile-field", response_model=BaseResponse)
async def update_profile_field(
    input_data: dict[str, Any] = Body(...),
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


@router.post("/evaluate-profile", response_model=BaseResponse)
async def evaluate_profile_with_ai(user: dict = Depends(require_auth)):
    """AI 评定学生画像 — 基于使用数据动态评估 6 维度分数"""
    try:
        user_id = user["id"]

        # 1. 获取当前画像
        profile_result = profile_agent.get_or_build_profile(user_id)
        profile = profile_result.get("profile", {}) if profile_result.get("success") else {}

        # 2. 获取使用数据
        from data.db_operations import assessment_db, resource_db
        from services.memory_service import memory_service

        # 学习资源数
        with resource_db:
            resource_db.cursor.execute(
                "SELECT COUNT(*) as cnt FROM learning_resources WHERE user_id=?", (user_id,)
            )
            resource_count = resource_db.cursor.fetchone()["cnt"] if resource_db.cursor.rowcount else 0

        # 学习活动数
        with assessment_db:
            assessment_db.cursor.execute(
                "SELECT COUNT(*) as cnt FROM learning_activities WHERE user_id=?", (user_id,)
            )
            activity_count = assessment_db.cursor.fetchone()["cnt"] if assessment_db.cursor.rowcount else 0

        # 记忆统计
        with memory_service as ms:
            mem_stats = ms.get_memory_stats(user_id)

        # 3. 构建 AI 评定 prompt
        prompt = f"""你是一个学习能力评估专家。请根据以下学生画像和使用数据，评估 6 个维度的分数（1-5 分）。

【学生画像】
{json.dumps(profile, ensure_ascii=False, indent=2)}

【使用数据】
- 学习资源数：{resource_count}
- 学习活动数：{activity_count}
- 短期记忆条数：{mem_stats.get('short_term_count', 0)}
- 语义记忆条数：{mem_stats.get('semantic_count', 0)}
- 情景记忆条数：{mem_stats.get('episodic_count', 0)}
- 实体记忆条数：{mem_stats.get('entity_count', 0)}

请输出 JSON 格式：
{{
  "knowledge_base": 分数,
  "learning_goals": 分数,
  "memory_ability": 分数,
  "self_control": 分数,
  "focus": 分数,
  "learning_depth": 分数,
  "reasoning": "评估理由"
}}

只输出 JSON，不要其他内容。"""

        from services.qa_service import qa_service
        ai_result = qa_service.call_simple(prompt, max_tokens=500)

        # 4. 解析结果
        scores = None
        try:
            import re
            match = re.search(r'\{[^{}]*\}', ai_result)
            if match:
                scores = json.loads(match.group())
        except Exception:
            pass

        if not scores:
            scores = {
                "knowledge_base": 3, "learning_goals": 3, "memory_ability": 3,
                "self_control": 3, "focus": 3, "learning_depth": 3,
                "reasoning": "AI 评定失败，使用默认分数",
            }

        # 5. 保存评定记录到数据库
        try:
            import sqlite3

            from data.config import get_memory_db_path
            conn = sqlite3.connect(get_memory_db_path())
            conn.execute("""
                INSERT INTO profile_evaluations
                (user_id, knowledge_base, learning_goals, memory_ability,
                 self_control, focus, learning_depth, reasoning,
                 resource_count, activity_count, evaluation_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ai')
            """, (
                user_id,
                scores.get("knowledge_base", 3),
                scores.get("learning_goals", 3),
                scores.get("memory_ability", 3),
                scores.get("self_control", 3),
                scores.get("focus", 3),
                scores.get("learning_depth", 3),
                scores.get("reasoning", ""),
                resource_count,
                activity_count,
            ))
            conn.commit()
            conn.close()
        except Exception as save_err:
            warning(f"保存画像评定记录失败: {save_err}")

        return BaseResponse(
            success=True,
            message="AI 画像评定完成",
            data={
                "scores": scores,
                "resource_count": resource_count,
                "activity_count": activity_count,
                "memory_stats": mem_stats,
            },
        )

    except Exception as e:
        error(f"AI 画像评定失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-resources", response_model=BaseResponse)
async def generate_learning_resources(
    input_data: GenerateResourcesRequest,
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
        info(f"用户 {user_id} 请求生成学习资源: {input_data.topic}")

        # 获取学生画像
        profile_result = profile_agent.get_or_build_profile(user_id)
        payload = input_data.model_dump()
        payload["profile"] = profile_result.get("profile", {})

        result = agent_coordinator.execute_task(
            task_type="generate_resources",
            user_id=user_id,
            input_data=payload
        )

        # 自动保存生成的资源到数据库
        if result.get("success") and result.get("data"):
            resources_data = result["data"].get("resources", [])
            dao = get_resource_dao()
            saved = 0
            for res in resources_data:
                rid = dao.save(
                    user_id=user_id,
                    title=res.get("title", ""),
                    resource_type=res.get("type", res.get("resource_type", "document")),
                    subject=input_data.subject,
                    topic=input_data.topic,
                    difficulty=input_data.difficulty,
                    content_data=res.get("content_data", res),
                )
                if rid:
                    saved += 1
            if saved:
                info(f"非流式资源自动保存成功: {saved} 条")

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )

    except Exception as e:
        error(f"生成学习资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan-path", response_model=BaseResponse)
async def plan_learning_path(
    input_data: dict[str, Any] = Body(...),
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
        error(f"规划学习路径失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor")
async def tutor_query(
    input_data: TutorQueryRequest,
    user: dict = Depends(get_current_user)
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
        info(f"用户 {user_id} 请求智能辅导, 问题: {input_data.question[:50]}")

        # 验证必填字段
        if not input_data.question:
            return JSONResponse(content={"success": False, "message": "问题内容不能为空", "data": None})

        # 使用辅导服务（已集成记忆增强）
        from services.tutor_agent import tutor_agent
        result = tutor_agent.answer_query(user_id, input_data.model_dump())

        info(f"辅导结果 - success: {result.get('success')}, 数据大小: {len(str(result.get('data', '')))} 字符")

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

        # 记录活动日志
        if resp_content.get("success"):
            try:
                from data.db_operations import assessment_db
                if assessment_db.connect():
                    assessment_db.cursor.execute(
                        "INSERT INTO learning_activities (user_id, activity_type, metadata) VALUES (?, ?, ?)",
                        (user_id, 'tutor_query', json.dumps({
                            "question": input_data.question[:100],
                            "subject": input_data.subject
                        }, ensure_ascii=False))
                    )
                    assessment_db.conn.commit()
                    assessment_db.close()
            except Exception as log_err:
                error(f"辅导活动日志记录失败: {log_err}")

        return JSONResponse(content=resp_content)

    except Exception as e:
        error(f"智能辅导失败: {e!s}")
        import traceback
        error(f"异常堆栈: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"辅导失败: {e!s}", "data": None}
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
        error(f"获取知识图谱失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-recommendations")
async def get_learning_recommendations(
    subject: str | None = Query(None),
    user: dict = Depends(get_current_user)
):
    """获取基于记忆的学习推荐"""
    try:
        from services.tutor_agent import tutor_agent
        recommendations = tutor_agent.get_learning_recommendations(user['id'], subject)
        return {"success": True, "data": {"recommendations": recommendations}}
    except Exception as e:
        error(f"获取学习推荐失败: {e!s}")
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
        error(f"记忆维护失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess", response_model=BaseResponse)
async def assess_learning(
    input_data: dict[str, Any] = Body(...),
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

        # 记录活动日志
        if result.get("success"):
            try:
                from data.db_operations import assessment_db
                if assessment_db.connect():
                    grade = ""
                    if result.get("data") and result["data"].get("assessment"):
                        grade = result["data"]["assessment"].get("grade", "")
                    assessment_db.cursor.execute(
                        "INSERT INTO learning_activities (user_id, activity_type, metadata) VALUES (?, ?, ?)",
                        (user_id, 'assessment', json.dumps({
                            "assessment_type": input_data.get("assessment_type", "comprehensive"),
                            "grade": grade
                        }, ensure_ascii=False))
                    )
                    assessment_db.conn.commit()
                    assessment_db.close()
            except Exception as log_err:
                error(f"评估活动日志记录失败: {log_err}")

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )

    except Exception as e:
        error(f"学习效果评估失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-assessment", response_model=BaseResponse)
async def get_latest_assessment(user: dict = Depends(require_auth)):
    """获取最新一次学习评估结果"""
    try:
        user_id = user["id"]
        from data.db_operations import assessment_db

        if not assessment_db.connect():
            return BaseResponse(success=True, message="暂无评估数据", data=None)

        assessment_db.cursor.execute(
            """SELECT metadata, created_at FROM learning_activities
               WHERE user_id = ? AND activity_type = 'assessment'
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        )
        row = assessment_db.cursor.fetchone()
        assessment_db.close()

        if not row:
            return BaseResponse(success=True, message="暂无评估数据", data=None)

        metadata = {}
        if row.get("metadata"):
            try:
                metadata = json.loads(row["metadata"])
            except Exception:
                pass

        return BaseResponse(
            success=True,
            message="获取成功",
            data={
                "grade": metadata.get("grade", ""),
                "assessment_type": metadata.get("assessment_type", ""),
                "created_at": row.get("created_at", ""),
            }
        )
    except Exception as e:
        error(f"获取最新评估失败: {e}")
        return BaseResponse(success=True, message="暂无评估数据", data=None)


@router.post("/comprehensive-plan", response_model=BaseResponse)
async def comprehensive_learning_plan(
    input_data: dict[str, Any] = Body(...),
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
        error(f"综合学习计划失败: {e!s}")
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
        result = path_agent.update_path_progress(path_id, completed_step, user_id)

        return BaseResponse(
            success=result["success"],
            message=result["message"],
            data=result.get("path_data")
        )

    except Exception as e:
        error(f"更新路径进度失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-profile-from-learning", response_model=BaseResponse)
async def update_profile_from_learning(
    learning_data: dict[str, Any] = Body(...),
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
        error(f"更新画像失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-resource", response_model=BaseResponse)
async def export_resource_file(
    input_data: dict[str, Any] = Body(...),
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
        error(f"导出资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学习资源管理库 ====================

@router.post("/save-resource", response_model=BaseResponse)
async def save_resource(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    保存学习资源到管理库

    输入格式:
    {
        "title": "资源标题",
        "resource_type": "document/quiz/mindmap/video/animation/code/reading",
        "subject": "学科",
        "topic": "主题",
        "difficulty_level": "beginner/intermediate/advanced",
        "content_data": {资源内容},
        "tags": ["标签1", "标签2"]
    }
    """
    try:
        user_id = user["id"]
        info(f"用户 {user_id} 保存学习资源: {input_data.get('title')}")

        from data.db_operations import resource_db

        if not resource_db.connect():
            return BaseResponse(success=False, message="数据库连接失败", data=None)

        sql = """
            INSERT INTO learning_resources
            (user_id, title, resource_type, subject, topic, difficulty_level, content_data, tags, generated_by_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        resource_db.cursor.execute(sql, (
            user_id,
            input_data.get("title", ""),
            input_data.get("resource_type", "document"),
            input_data.get("subject", ""),
            input_data.get("topic", ""),
            input_data.get("difficulty_level", "intermediate"),
            json.dumps(input_data.get("content_data", {}), ensure_ascii=False),
            json.dumps(input_data.get("tags", []), ensure_ascii=False),
            f"user_{user_id}"
        ))
        resource_db.conn.commit()
        resource_id = resource_db.cursor.lastrowid
        resource_db.close()

        info(f"学习资源保存成功: resource_id={resource_id}")
        return BaseResponse(
            success=True,
            message="资源保存成功",
            data={"resource_id": resource_id}
        )

    except Exception as e:
        error(f"保存学习资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-resources", response_model=BaseResponse)
async def list_resources(
    resource_type: str = Query("", description="资源类型筛选"),
    subject: str = Query("", description="学科筛选"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user)
):
    """
    获取学习资源列表
    """
    try:
        user_id = user["id"]

        from data.db_operations import resource_db

        if not resource_db.connect():
            return BaseResponse(success=False, message="数据库连接失败", data=None)

        conditions = ["(user_id = ? OR (user_id IS NULL AND generated_by_agent = ?))"]
        params = [user_id, f"user_{user_id}"]

        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)

        if subject:
            conditions.append("subject LIKE ?")
            params.append(f"%{subject}%")

        where = " AND ".join(conditions)
        sql = f"""
            SELECT id, title, resource_type, subject, topic, difficulty_level,
                   content_data, tags, usage_count, rating, duration_minutes, created_at
            FROM learning_resources
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        resource_db.cursor.execute(sql, params)
        rows = resource_db.cursor.fetchall()

        # 解析 JSON 字段
        for row in rows:
            if row.get("content_data"):
                try:
                    row["content_data"] = json.loads(row["content_data"])
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            if row.get("tags"):
                try:
                    row["tags"] = json.loads(row["tags"])
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
            if row.get("created_at"):
                row["created_at"] = str(row["created_at"])

        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM learning_resources WHERE {where}"
        resource_db.cursor.execute(count_sql, params[:-2])
        total = resource_db.cursor.fetchone()["total"]

        resource_db.close()

        return BaseResponse(
            success=True,
            message="获取成功",
            data={"resources": rows, "total": total}
        )

    except Exception as e:
        error(f"获取学习资源列表失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-resource/{resource_id}", response_model=BaseResponse)
async def delete_resource(
    resource_id: int,
    user: dict = Depends(get_current_user)
):
    """删除学习资源"""
    try:
        user_id = user["id"]

        from data.db_operations import resource_db

        if not resource_db.connect():
            return BaseResponse(success=False, message="数据库连接失败", data=None)

        # 验证资源属于当前用户
        sql = "SELECT id FROM learning_resources WHERE id = ? AND (user_id = ? OR (user_id IS NULL AND generated_by_agent = ?))"
        resource_db.cursor.execute(sql, (resource_id, user_id, f"user_{user_id}"))
        if not resource_db.cursor.fetchone():
            resource_db.close()
            return BaseResponse(success=False, message="资源不存在或无权限删除", data=None)

        # 删除资源
        delete_sql = "DELETE FROM learning_resources WHERE id = ?"
        resource_db.cursor.execute(delete_sql, (resource_id,))
        resource_db.conn.commit()
        resource_db.close()

        info(f"用户 {user_id} 删除资源: resource_id={resource_id}")
        return BaseResponse(success=True, message="删除成功")

    except Exception as e:
        error(f"删除学习资源失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-documents", response_model=BaseResponse)
async def analyze_documents(
    files: list[UploadFile] = File(...),
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
        error(f"文档分析失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== RAG 知识库上传 ==========
@router.post("/upload-to-rag", response_model=BaseResponse)
async def upload_to_rag(
    files: list[UploadFile] = File(...),
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
                from core.json_utils import safe_parse_json
                from services.spark_client import spark_client
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
                uploaded_by=user_id,
                file_size=len(content),
            )

            if doc_id:
                results.append({"filename": f.filename, "success": True, "doc_id": doc_id,
                                "knowledge_points": len(kp_list), "summary": summary})

                # 异步构建知识图谱（不阻塞响应）
                try:
                    from services.multi_hop_retriever import multi_hop_retriever
                    import threading
                    threading.Thread(
                        target=multi_hop_retriever.build_knowledge_graph,
                        args=(doc_id, subject or "综合", text),
                        daemon=True
                    ).start()
                except Exception as kg_err:
                    debug(f"知识图谱构建启动失败: {kg_err}")
            else:
                results.append({"filename": f.filename, "success": False, "message": "写入数据库失败"})

        success_count = sum(1 for r in results if r["success"])
        return BaseResponse(
            success=success_count > 0,
            message=f"成功导入 {success_count}/{len(results)} 个文件到知识库",
            data={"results": results},
        )

    except Exception as e:
        error(f"RAG上传失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-documents", response_model=BaseResponse)
async def list_rag_documents(
    user: dict = Depends(require_auth),
    limit: int = 200,
):
    """获取 RAG 知识库文档列表（仅当前用户）"""
    try:
        from data.rag_knowledge_base import rag_kb
        docs = rag_kb.get_documents_by_user(str(user["id"]), limit=limit)
        return BaseResponse(success=True, message="获取成功", data={"documents": docs})
    except Exception as e:
        error(f"获取RAG文档列表失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学生数据管理 API ====================

from services.student_data_service import student_data_service


@router.post("/save-course-schedule", response_model=BaseResponse)
async def save_course_schedule(
    input_data: dict[str, Any] = Body(...),
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
    input_data: dict[str, Any] = Body(...),
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
    semester: str | None = None,
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
    input_data: dict[str, Any] = Body(...),
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
    subject: str | None = None,
    mastery: int | None = None,
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
    input_data: dict[str, Any] = Body(...),
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
    input_data: dict[str, Any] = Body(...),
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
    input_data: dict[str, Any] = Body(...),
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
    semester: str | None = None,
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


# ==================== 工作台 API ====================


@router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """获取工作台统计数据"""
    try:
        user_id = user["id"]
        stats = {}

        res_dao = get_resource_dao()
        act_dao = get_activity_dao()
        stats["resource_count"] = res_dao.count_by_user(user_id)
        stats["activity_count"] = act_dao.count_by_user(user_id)
        stats["login_days"] = act_dao.get_login_days(user_id)
        stats["total_study_seconds"] = act_dao.get_total_study_seconds(user_id)

        return {"success": True, "data": stats}

    except Exception as e:
        error(f"获取工作台统计失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs")
async def get_activity_logs(
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """获取用户最近活动日志"""
    try:
        user_id = user["id"]
        act_dao = get_activity_dao()
        rows = act_dao.get_recent(user_id, limit)

        return BaseResponse(success=True, data={"logs": rows})

    except Exception as e:
        error(f"获取活动日志失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activity-logs")
async def record_session_time(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user)
):
    """记录会话学习时长"""
    try:
        user_id = user["id"]
        seconds = input_data.get("seconds", 0)
        if seconds < 10:
            return {"success": True, "message": "ignored"}

        act_dao = get_activity_dao()
        act_dao.record(user_id, 'session', {"action": "页面浏览"}, seconds)

        return {"success": True}
    except Exception as e:
        error(f"记录会话时长失败: {e!s}")
        return {"success": False}


# ==================== 高级检索 API ====================


@router.post("/advanced-search", response_model=BaseResponse)
async def advanced_search(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    高级检索 — 支持 11 种检索策略

    输入格式:
    {
        "query": "检索内容",
        "subject": "学科（可选）",
        "strategy": "auto|knn|ann|hybrid|hyde|multi_query|rag_fusion|contextual|graph|hybrid_advl|ensemble",
        "limit": 5
    }

    策略路由:
    - auto: 自动选择（短查询用 HyDE，长查询用 RAG-Fusion）
    - knn: KNN 关键词检索（MySQL FULLTEXT INDEX 精确匹配）
    - ann: ANN 向量检索（FAISS 语义匹配）
    - hybrid: KNN + ANN + RRF 混合检索（基座策略）
    - hyde: 假设性文档嵌入（2023）
    - multi_query: 多查询检索（2023）
    - rag_fusion: RAG-Fusion + RRF 排序（2023，推荐）
    - contextual: 上下文精排（2024）
    - graph: 图谱增强检索（2024）
    - hybrid_advl: HyDE + RAG-Fusion + 基座混合（三路 RRF）
    - ensemble: 全方法集成（6路取并集，最全面）
    """
    try:
        user_id = user["id"]
        query = input_data.get("query", "")
        if not query:
            return BaseResponse(success=False, message="查询内容不能为空", data=None)

        subject = input_data.get("subject")
        strategy = input_data.get("strategy", "auto")
        limit = input_data.get("limit", 5)

        info(f"用户 {user_id} 高级检索: query={query[:50]}, strategy={strategy}")

        from services.advanced_retrieval_service import retrieval_service
        results = retrieval_service.smart_search(
            user_id=user_id,
            query=query,
            subject=subject,
            limit=limit,
            strategy=strategy,
        )

        return BaseResponse(
            success=True,
            message=f"检索完成，返回 {len(results)} 条结果",
            data={
                "results": results,
                "strategy_used": strategy,
                "count": len(results),
            },
        )

    except Exception as e:
        error(f"高级检索失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contextual-upload", response_model=BaseResponse)
async def contextual_upload(
    files: list[UploadFile] = File(...),
    subject: str = Form(""),
    user: dict = Depends(get_current_user),
):
    """
    上下文分块上传到 RAG 知识库
    参考 Anthropic Contextual Retrieval (2024)
    为每个段落添加上下文前缀后再嵌入，显著提升检索精度
    """
    ALLOWED = {'.txt', '.md', '.pdf', '.doc', '.docx', '.ppt', '.pptx'}
    MAX_SIZE = 20 * 1024 * 1024

    try:
        user_id = user["id"]
        from services.advanced_retrieval_service import retrieval_service
        from services.document_analysis_service import document_analysis_service

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
                from core.json_utils import safe_parse_json
                from services.spark_client import spark_client
                kp_resp = spark_client.simple(kp_prompt, max_tokens=500)
                kp_list = safe_parse_json(kp_resp)
                if not isinstance(kp_list, list):
                    kp_list = []
            except Exception:
                kp_list = []

            title = f.filename.rsplit('.', 1)[0]
            doc_id = retrieval_service.add_contextual_document(
                title=title,
                subject=subject or "综合",
                content_text=text,
                file_path=f.filename,
                file_type=ext.lstrip('.'),
                knowledge_points=kp_list,
                uploaded_by=user_id,
            )

            if doc_id:
                results.append({"filename": f.filename, "success": True, "doc_id": doc_id,
                                "knowledge_points": len(kp_list), "method": "contextual_chunking"})
            else:
                results.append({"filename": f.filename, "success": False, "message": "写入失败"})

        success_count = sum(1 for r in results if r.get("success"))
        return BaseResponse(
            success=success_count > 0,
            message=f"上下文分块入库 {success_count}/{len(results)} 个文件",
            data={"results": results},
        )

    except Exception as e:
        error(f"上下文上传失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 单独检索方法 API ====================


@router.post("/hyde-search", response_model=BaseResponse)
async def hyde_search(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    HyDE 检索 — 假设性文档嵌入（Gao et al., 2023）
    LLM 生成假设答案，用答案向量检索

    输入格式:
    {
        "query": "检索内容",
        "subject": "学科（可选）",
        "model": "simple|standard|advanced",
        "limit": 5
    }
    """
    try:
        user_id = user["id"]
        query = input_data.get("query", "")
        if not query:
            return BaseResponse(success=False, message="查询内容不能为空", data=None)

        subject = input_data.get("subject")
        model = input_data.get("model", "simple")
        limit = input_data.get("limit", 5)

        info(f"用户 {user_id} HyDE检索: query={query[:50]}")

        from services.advanced_retrieval_service import retrieval_service
        results = retrieval_service.hyde_search(
            query=query, subject=subject, limit=limit, model=model
        )

        return BaseResponse(
            success=True,
            message=f"HyDE检索完成，返回 {len(results)} 条结果",
            data={"results": results, "method": "hyde", "count": len(results)},
        )

    except Exception as e:
        error(f"HyDE检索失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-query-search", response_model=BaseResponse)
async def multi_query_search(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    Multi-Query 检索 — 多查询检索（LangChain, 2023）
    LLM 生成多个查询变体，分别检索合并

    输入格式:
    {
        "query": "检索内容",
        "subject": "学科（可选）",
        "num_variants": 3,
        "limit": 5
    }
    """
    try:
        user_id = user["id"]
        query = input_data.get("query", "")
        if not query:
            return BaseResponse(success=False, message="查询内容不能为空", data=None)

        subject = input_data.get("subject")
        num_variants = input_data.get("num_variants", 3)
        limit = input_data.get("limit", 5)

        info(f"用户 {user_id} Multi-Query检索: query={query[:50]}")

        from services.advanced_retrieval_service import retrieval_service
        results = retrieval_service.multi_query_search(
            query=query, subject=subject, limit=limit, num_variants=num_variants
        )

        return BaseResponse(
            success=True,
            message=f"Multi-Query检索完成，返回 {len(results)} 条结果",
            data={"results": results, "method": "multi_query", "count": len(results)},
        )

    except Exception as e:
        error(f"Multi-Query检索失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag-fusion-search", response_model=BaseResponse)
async def rag_fusion_search(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    RAG-Fusion 检索 — 查询融合 + RRF 排序（Raudaschl, 2023）
    多查询 + 倒数排名融合排序

    输入格式:
    {
        "query": "检索内容",
        "subject": "学科（可选）",
        "num_variants": 4,
        "rrf_k": 60,
        "limit": 5
    }
    """
    try:
        user_id = user["id"]
        query = input_data.get("query", "")
        if not query:
            return BaseResponse(success=False, message="查询内容不能为空", data=None)

        subject = input_data.get("subject")
        num_variants = input_data.get("num_variants", 4)
        rrf_k = input_data.get("rrf_k", 60)
        limit = input_data.get("limit", 5)

        info(f"用户 {user_id} RAG-Fusion检索: query={query[:50]}")

        from services.advanced_retrieval_service import retrieval_service
        results = retrieval_service.rag_fusion_search(
            query=query, subject=subject, limit=limit,
            num_variants=num_variants, rrf_k=rrf_k
        )

        return BaseResponse(
            success=True,
            message=f"RAG-Fusion检索完成，返回 {len(results)} 条结果",
            data={"results": results, "method": "rag_fusion", "count": len(results)},
        )

    except Exception as e:
        error(f"RAG-Fusion检索失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph-search", response_model=BaseResponse)
async def graph_search(
    input_data: dict[str, Any] = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    图谱增强检索 — Graph-Enhanced RAG（Microsoft GraphRAG, 2024）
    实体识别 → 图谱遍历 → 查询扩展 → 融合检索

    输入格式:
    {
        "query": "检索内容",
        "subject": "学科（可选）",
        "graph_depth": 2,
        "limit": 5
    }
    """
    try:
        user_id = user["id"]
        query = input_data.get("query", "")
        if not query:
            return BaseResponse(success=False, message="查询内容不能为空", data=None)

        subject = input_data.get("subject")
        graph_depth = input_data.get("graph_depth", 2)
        limit = input_data.get("limit", 5)

        info(f"用户 {user_id} 图谱增强检索: query={query[:50]}")

        from services.advanced_retrieval_service import retrieval_service
        results = retrieval_service.graph_enhanced_search(
            user_id=user_id, query=query, subject=subject,
            limit=limit, graph_depth=graph_depth
        )

        return BaseResponse(
            success=True,
            message=f"图谱增强检索完成，返回 {len(results)} 条结果",
            data={"results": results, "method": "graph_enhanced", "count": len(results)},
        )

    except Exception as e:
        error(f"图谱增强检索失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 自学习闭环 API
# ==========================================

@router.post("/feedback")
async def submit_feedback(
    request_data: dict = Body(...),
    user=Depends(get_current_user),
):
    """提交用户反馈（点赞/点踩/评分/评论）"""
    try:
        user_id = user["id"]
        interaction_id = request_data.get("interaction_id", "")
        if not interaction_id:
            return BaseResponse(success=False, message="缺少 interaction_id", data=None)

        feedback = {
            "rating": request_data.get("rating", 3),
            "helpful": request_data.get("helpful", True),
            "comment": request_data.get("comment", ""),
            "interaction_type": request_data.get("interaction_type", "tutor"),
            "original_query": request_data.get("original_query", ""),
            "original_answer": request_data.get("original_answer", ""),
        }

        from services.self_learning_service import self_learning_service
        success = self_learning_service.collect_feedback(user_id, interaction_id, feedback)

        return BaseResponse(
            success=success,
            message="反馈提交成功" if success else "反馈提交失败",
            data={"interaction_id": interaction_id},
        )
    except Exception as e:
        error(f"提交反馈失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-stats")
async def get_learning_stats(user=Depends(require_auth)):
    """获取自学习统计"""
    try:
        from services.self_learning_service import self_learning_service
        stats = self_learning_service.get_learning_stats(user["id"])
        return BaseResponse(success=True, message="获取统计成功", data=stats)
    except Exception as e:
        error(f"获取学习统计失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-learning")
async def trigger_learning_cycle(user=Depends(require_auth)):
    """手动触发自学习循环"""
    try:
        from services.self_learning_service import self_learning_service
        result = self_learning_service.trigger_learning_cycle()
        return BaseResponse(success=True, message="学习循环完成", data=result)
    except Exception as e:
        error(f"触发学习循环失败: {e!s}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# 检索评测 API
# ═══════════════════════════════════════════

@router.get("/eval-retrieval/datasets", response_model=BaseResponse)
async def list_eval_datasets(user: dict = Depends(require_auth)):
    """获取所有检索评测数据集"""
    try:
        from services.retrieval_evaluator import retrieval_evaluator
        datasets = retrieval_evaluator.get_datasets()
        return BaseResponse(success=True, message="获取成功", data=datasets)
    except Exception as e:
        error(f"获取评测数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eval-retrieval/datasets", response_model=BaseResponse)
async def create_eval_dataset(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """创建检索评测数据集"""
    try:
        from services.retrieval_evaluator import retrieval_evaluator
        name = input_data.get("name", "")
        description = input_data.get("description", "")
        if not name:
            raise HTTPException(status_code=400, detail="数据集名称不能为空")
        result = retrieval_evaluator.create_dataset(name, description)
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"创建评测数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eval-retrieval/queries", response_model=BaseResponse)
async def add_eval_query(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """向数据集添加评测查询"""
    try:
        from services.retrieval_evaluator import retrieval_evaluator
        dataset_id = input_data.get("dataset_id")
        query = input_data.get("query", "")
        relevant_doc_ids = input_data.get("relevant_doc_ids", [])
        if not dataset_id or not query:
            raise HTTPException(status_code=400, detail="dataset_id 和 query 不能为空")
        result = retrieval_evaluator.add_query(dataset_id, query, relevant_doc_ids)
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加评测查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eval-retrieval/run", response_model=BaseResponse)
async def run_eval_retrieval(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """
    运行检索评测

    请求体:
    {
        "dataset_id": 1,
        "strategy": "hybrid",
        "k": 5
    }
    """
    try:
        from data.rag_knowledge_base import rag_kb
        from services.retrieval_evaluator import retrieval_evaluator

        dataset_id = input_data.get("dataset_id")
        strategy = input_data.get("strategy", "hybrid")
        k = input_data.get("k", 5)

        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id 不能为空")

        # 构建检索函数
        def retrieval_fn(query: str):
            from data.embedding_service import embedding_service
            embedding = embedding_service.get_embedding(query)
            if strategy == "hybrid":
                return rag_kb.hybrid_search(query, query_embedding=embedding, limit=k)
            elif strategy == "fts5":
                return rag_kb.search_documents_by_fulltext(query, limit=k)
            elif strategy == "vector":
                return rag_kb.search_documents_by_vector(embedding, limit=k)
            else:
                return rag_kb.hybrid_search(query, query_embedding=embedding, limit=k)

        result = retrieval_evaluator.run_evaluation(
            dataset_id=dataset_id,
            retrieval_fn=retrieval_fn,
            strategy_name=strategy,
            k=k
        )
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"运行检索评测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eval-retrieval/history", response_model=BaseResponse)
async def get_eval_history(
    dataset_id: int | None = Query(None),
    user: dict = Depends(require_auth)
):
    """获取评测历史"""
    try:
        from services.retrieval_evaluator import retrieval_evaluator
        history = retrieval_evaluator.get_history(dataset_id)
        return BaseResponse(success=True, message="获取成功", data=history)
    except Exception as e:
        error(f"获取评测历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eval-retrieval/compare", response_model=BaseResponse)
async def compare_eval_strategies(
    dataset_id: int = Query(...),
    k: int = Query(5),
    user: dict = Depends(require_auth)
):
    """对比不同策略的评测结果"""
    try:
        from services.retrieval_evaluator import retrieval_evaluator
        result = retrieval_evaluator.compare_strategies(dataset_id, k)
        return BaseResponse(**result)
    except Exception as e:
        error(f"对比评测策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Multi-Hop 检索可视化 API
# ═══════════════════════════════════════════

@router.post("/multi-hop-search", response_model=BaseResponse)
async def multi_hop_search(
    input_data: dict = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Multi-Hop 多跳推理检索（含可视化数据）

    请求体:
    {
        "query": "问题内容",
        "max_hops": 3,
        "limit": 5
    }

    返回:
    {
        "answer": "综合答案",
        "evidence_chain": [{"hop": 0, "doc_id": ..., "title": ..., "content": ..., "score": ..., "relation": ...}],
        "confidence": 0.85,
        "hops_used": 2,
        "logic_graph": {"nodes": [...], "edges": [...]}
    }
    """
    try:
        from services.multi_hop_retriever import multi_hop_retriever

        query = input_data.get("query", "")
        max_hops = input_data.get("max_hops", 3)
        limit = input_data.get("limit", 5)

        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")

        user_id = user["id"]
        info(f"用户 {user_id} 请求 Multi-Hop 检索: {query[:50]}")

        result = multi_hop_retriever.retrieve(
            query=query, user_id=user_id,
            max_hops=max_hops, limit=limit
        )

        return BaseResponse(
            success=True,
            message="Multi-Hop 检索完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Multi-Hop 检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/react-search", response_model=BaseResponse)
async def react_search(
    input_data: dict = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    ReAct 推理-检索交替检索（适配推导题、多步骤问题）

    请求体:
    {
        "query": "问题内容",
        "max_steps": 3,
        "limit": 5
    }

    返回:
    {
        "answer": "综合答案",
        "evidence_chain": [...],
        "reasoning_steps": [{"step": 0, "thought": "...", "need_info": "...", "is_sufficient": false}],
        "confidence": 0.85,
        "logic_graph": {"nodes": [...], "edges": [...]}
    }
    """
    try:
        from services.multi_hop_retriever import multi_hop_retriever

        query = input_data.get("query", "")
        max_steps = input_data.get("max_steps", 3)
        limit = input_data.get("limit", 5)

        if not query:
            raise HTTPException(status_code=400, detail="查询内容不能为空")

        user_id = user["id"]
        info(f"用户 {user_id} 请求 ReAct 检索: {query[:50]}")

        result = multi_hop_retriever.react_retrieve(
            query=query, user_id=user_id,
            max_steps=max_steps, limit=limit
        )

        return BaseResponse(
            success=True,
            message="ReAct 检索完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"ReAct 检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/faiss-info", response_model=BaseResponse)
async def get_faiss_index_info(user: dict = Depends(require_auth)):
    """获取 FAISS 索引信息（类型、向量数、维度）"""
    try:
        from data.rag_knowledge_base import vector_index
        info_data = vector_index.index_info
        return BaseResponse(success=True, message="获取成功", data=info_data)
    except Exception as e:
        error(f"获取 FAISS 索引信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════
# Agent 协作状态可视化 API
# ═══════════════════════════════════════════

@router.get("/agent-status/{session_id}", response_model=BaseResponse)
async def get_agent_status(session_id: str, user: dict = Depends(require_auth)):
    """获取 Agent 协作状态（用于实时可视化）"""
    try:
        events = agent_coordinator.get_session_status(session_id)
        return BaseResponse(success=True, message="获取成功", data=events)
    except Exception as e:
        error(f"获取 Agent 状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-status-stream/{session_id}")
async def stream_agent_status(session_id: str, user: dict = Depends(get_current_user)):
    """
    SSE 流式推送 Agent 协作状态

    事件格式:
    data: {"type": "task_start|agent_thinking|retrieving|synthesizing|task_complete", "data": {...}}
    """
    import asyncio

    async def event_generator():
        queue = asyncio.Queue()

        def callback(event):
            try:
                queue.put_nowait(event)
            except Exception:
                pass

        agent_coordinator.register_status_callback(callback)
        try:
            # 发送已有事件
            existing = agent_coordinator.get_session_status(session_id)
            for event in existing:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 持续推送新事件
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    if event.get("session_id") == session_id:
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 心跳
                    yield f": heartbeat\n\n"
        finally:
            agent_coordinator.unregister_status_callback(callback)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
