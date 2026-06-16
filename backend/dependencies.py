"""
FastAPI 依赖注入 — 企业级安全配置
JWT 认证、请求上下文注入、权限校验
"""
import os
import jwt
import secrets
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Header, Request
from typing import Optional

from data.data_manager import CacheManager

# ── JWT 配置 ──
_jwt_env = os.getenv("JWT_SECRET")
if _jwt_env:
    JWT_SECRET = _jwt_env
else:
    JWT_SECRET = secrets.token_urlsafe(48)
    import warnings
    warnings.warn(
        "JWT_SECRET 未设置，已生成随机密钥（重启后所有 Token 失效）。"
        "请在 .env 中配置 JWT_SECRET。",
        stacklevel=2,
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))


def get_api_config() -> dict:
    config = CacheManager.load_env_config()
    return {
        "api_key": config.get("api_key", ""),
        "base_url": config.get("base_url", "https://spark-api-open.xf-yun.com/v1"),
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


async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> dict:
    """获取当前认证用户

    支持两种认证方式:
    1. Bearer Token: Authorization: Bearer <token>
    2. 无 Token 时返回游客用户
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
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
