"""
协同学习小组 API
"""

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.dependencies import get_current_user, require_auth
from backend.schemas.models import BaseResponse
from core.logger import error, info

router = APIRouter(prefix="/collaboration", tags=["协同学习"])


# ═══════════════════════════════════════
# 小组管理
# ═══════════════════════════════════════

@router.post("/create-group", response_model=BaseResponse)
async def create_group(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """创建学习小组"""
    try:
        from services.collaboration_service import collaboration_service
        name = input_data.get("name", "")
        if not name:
            raise HTTPException(status_code=400, detail="小组名称不能为空")

        result = collaboration_service.create_group(
            user_id=user["id"],
            name=name,
            description=input_data.get("description", ""),
            subject=input_data.get("subject", "综合"),
        )
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"创建小组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/join-group", response_model=BaseResponse)
async def join_group(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """通过邀请码加入小组"""
    try:
        from services.collaboration_service import collaboration_service
        invite_code = input_data.get("invite_code", "")
        if not invite_code:
            raise HTTPException(status_code=400, detail="邀请码不能为空")

        result = collaboration_service.join_group(user["id"], invite_code.upper())
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"加入小组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leave-group", response_model=BaseResponse)
async def leave_group(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """退出小组"""
    try:
        from services.collaboration_service import collaboration_service
        group_id = input_data.get("group_id")
        if not group_id:
            raise HTTPException(status_code=400, detail="group_id 不能为空")

        result = collaboration_service.leave_group(user["id"], group_id)
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"退出小组失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-groups", response_model=BaseResponse)
async def get_my_groups(user: dict = Depends(require_auth)):
    """获取我的小组列表"""
    try:
        from services.collaboration_service import collaboration_service
        groups = collaboration_service.get_user_groups(user["id"])
        return BaseResponse(success=True, message="获取成功", data=groups)
    except Exception as e:
        error(f"获取小组列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/group/{group_id}", response_model=BaseResponse)
async def get_group_detail(group_id: int, user: dict = Depends(require_auth)):
    """获取小组详情"""
    try:
        from services.collaboration_service import collaboration_service
        detail = collaboration_service.get_group_detail(group_id, user["id"])
        if not detail:
            raise HTTPException(status_code=404, detail="小组不存在")
        return BaseResponse(success=True, message="获取成功", data=detail)
    except HTTPException:
        raise
    except Exception as e:
        error(f"获取小组详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════
# 资源共享
# ═══════════════════════════════════════

@router.post("/share-resource", response_model=BaseResponse)
async def share_resource(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """共享资源到小组"""
    try:
        from services.collaboration_service import collaboration_service
        group_id = input_data.get("group_id")
        resource_id = input_data.get("resource_id")
        if not group_id or not resource_id:
            raise HTTPException(status_code=400, detail="group_id 和 resource_id 不能为空")

        result = collaboration_service.share_resource(
            user_id=user["id"],
            group_id=group_id,
            resource_id=resource_id,
            resource_type=input_data.get("resource_type", "document"),
        )
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"共享资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shared-resources/{group_id}", response_model=BaseResponse)
async def get_shared_resources(group_id: int, user: dict = Depends(require_auth)):
    """获取小组共享资源"""
    try:
        from services.collaboration_service import collaboration_service
        resources = collaboration_service.get_shared_resources(group_id)
        return BaseResponse(success=True, message="获取成功", data=resources)
    except Exception as e:
        error(f"获取共享资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════
# 学习动态
# ═══════════════════════════════════════

@router.get("/activities/{group_id}", response_model=BaseResponse)
async def get_group_activities(group_id: int, user: dict = Depends(require_auth)):
    """获取小组学习动态"""
    try:
        from services.collaboration_service import collaboration_service
        activities = collaboration_service.get_group_activities(group_id)
        return BaseResponse(success=True, message="获取成功", data=activities)
    except Exception as e:
        error(f"获取小组动态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════
# 互评
# ═══════════════════════════════════════

@router.post("/review", response_model=BaseResponse)
async def add_review(
    input_data: dict = Body(...),
    user: dict = Depends(require_auth)
):
    """添加互评"""
    try:
        from services.collaboration_service import collaboration_service
        group_id = input_data.get("group_id")
        resource_id = input_data.get("resource_id")
        rating = input_data.get("rating", 3)
        if not group_id or not resource_id:
            raise HTTPException(status_code=400, detail="group_id 和 resource_id 不能为空")

        result = collaboration_service.add_review(
            user_id=user["id"],
            group_id=group_id,
            resource_id=resource_id,
            rating=rating,
            comment=input_data.get("comment", ""),
        )
        return BaseResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        error(f"添加互评失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════
# 学习进度对比
# ═══════════════════════════════════════

@router.get("/learning-stats/{group_id}", response_model=BaseResponse)
async def get_group_learning_stats(group_id: int, user: dict = Depends(require_auth)):
    """获取小组学习统计（进度对比）"""
    try:
        from services.collaboration_service import collaboration_service
        stats = collaboration_service.get_group_learning_stats(group_id)
        return BaseResponse(success=True, message="获取成功", data=stats)
    except Exception as e:
        error(f"获取学习统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
