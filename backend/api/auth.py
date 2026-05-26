"""
认证 API - 登录/注册/用户信息
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.models import (
    LoginRequest, RegisterRequest, ChangePasswordRequest,
    AuthResponse, UserInfo, BaseResponse,
)
from backend.dependencies import (
    create_token, get_current_user, require_auth,
)
from services.auth_service import auth_service
from core.logger import info, user_login

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """用户登录"""
    result = auth_service.login_user(req.username, req.password)

    if not result["success"]:
        return AuthResponse(success=False, message=result["message"], error=result["message"])

    user = result["user"]
    token = create_token(user["id"], user["username"], user.get("role", "user"))

    user_login(req.username, True)

    return AuthResponse(
        success=True,
        message=result["message"],
        user=UserInfo(
            id=user["id"],
            username=user["username"],
            role=user.get("role", "user"),
            email=user.get("email"),
        ),
        token=token,
    )


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    result = auth_service.register_user(
        req.username, req.password, req.email
    )

    if not result["success"]:
        return AuthResponse(success=False, message=result["message"], error=result["message"])

    return AuthResponse(success=True, message=result["message"])


@router.get("/me", response_model=AuthResponse)
async def get_me(user: dict = Depends(require_auth)):
    """获取当前用户信息"""
    return AuthResponse(
        success=True,
        user=UserInfo(
            id=user["id"],
            username=user["username"],
            role=user["role"],
        ),
    )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    req: ChangePasswordRequest,
    user: dict = Depends(require_auth),
):
    """修改密码"""
    result = auth_service.change_password(
        user["username"], req.old_password, req.new_password
    )
    return BaseResponse(
        success=result["success"],
        message=result.get("message", ""),
        error=result.get("message") if not result["success"] else None,
    )


@router.post("/guest", response_model=AuthResponse)
async def guest_login():
    """游客模式登录"""
    token = create_token(0, "游客", "guest")
    return AuthResponse(
        success=True,
        message="已进入游客模式",
        user=UserInfo(id=0, username="游客", role="guest"),
        token=token,
    )
