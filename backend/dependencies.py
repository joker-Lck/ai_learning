"""
FastAPI 依赖注入 — 企业级安全配置
JWT 认证、请求上下文注入、权限校验
"""
import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, Header, HTTPException, Request

from data.data_manager import CacheManager

# ── JWT 配置 ──
_jwt_env = os.getenv("JWT_SECRET")
_jwt_env = os.getenv("JWT_SECRET")
if not _jwt_env or _jwt_env == "your_random_secret_key_here_at_least_32_chars":
    raise RuntimeError(
        "JWT_SECRET 未配置或使用了默认值，请在 .env 中设置一个随机密钥（至少32字符）。"
    )
JWT_SECRET = _jwt_env

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))


def get_api_config() -> dict:
    config = CacheManager.load_env_config()
    return {
        "api_key": config.get("api_key", ""),
        "base_url": config.get("base_url", "https://api.mimo.ai/v1"),
    }


def create_token(user_id: int, username: str, role: str) -> str:
    """创建 JWT Token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """创建刷新 Token（长期有效）"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


async def get_current_user(request: Request, authorization: str | None = Header(None)) -> dict:
    """获取当前认证用户

    支持三种认证方式:
    1. Bearer Token: Authorization: Bearer <token>
    2. Query 参数: ?token=<token> (用于 SSE/EventSource)
    3. 无 Token 时返回游客用户
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif request.query_params.get("token"):
        token = request.query_params.get("token")

    if token:
        payload = decode_token(token)

        # 拒绝 refresh token 用于接口访问
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="请使用 access token")

        user = {
            "id": payload.get("user_id", 0),
            "username": payload.get("username", "未知"),
            "role": payload.get("role", "guest"),
        }
        # 注入到请求状态，供日志中间件使用
        request.state.user_id = user["id"]
        return user

    return {"id": 0, "username": "游客", "role": "guest"}


async def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """要求用户已认证（非游客）"""
    if user["role"] == "guest":
        raise HTTPException(status_code=401, detail="请先登录")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求管理员角色"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ── RBAC 角色权限控制 ──

ROLE_HIERARCHY = {
    "admin": 100,
    "teacher": 50,
    "student": 10,
    "guest": 0,
}

ROLE_PERMISSIONS = {
    "admin": {"*"},
    "teacher": {
        "profile:read", "profile:write",
        "resource:read", "resource:write", "resource:delete",
        "path:read", "path:write",
        "tutor:read", "tutor:write",
        "assessment:read", "assessment:write",
        "rag:read", "rag:write",
        "feedback:read", "feedback:write",
    },
    "student": {
        "profile:read", "profile:write:own",
        "resource:read", "resource:write:own",
        "path:read", "path:write:own",
        "tutor:read", "tutor:write",
        "assessment:read", "assessment:write:own",
        "rag:read",
        "feedback:write",
    },
    "guest": {
        "profile:read",
        "resource:read",
        "tutor:read",
    },
}


def require_permission(permission: str):
    """RBAC 权限检查装饰器"""
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        role = user.get("role", "guest")
        perms = ROLE_PERMISSIONS.get(role, set())

        if "*" in perms:
            return user
        if permission in perms:
            return user
        # 检查通配符权限（如 "profile:write:own" 匹配 "profile:write"）
        base_perm = ":".join(permission.split(":")[:2])
        if base_perm in perms or f"{base_perm}:own" in perms:
            return user

        raise HTTPException(
            status_code=403,
            detail=f"权限不足: 需要 {permission}，当前角色 {role}"
        )
    return checker


def require_role(min_role: str):
    """要求最低角色等级"""
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        user_level = ROLE_HIERARCHY.get(user.get("role", "guest"), 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足: 需要 {min_role} 及以上角色"
            )
        return user
    return checker
