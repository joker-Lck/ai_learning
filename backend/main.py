"""
FastAPI 应用入口 — 企业级配置
多模态 AI 教学智能体 - 后端 API 服务
"""
import sys
import os
import uuid
import time
import signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.api.auth import router as auth_router
from backend.api.agent import router as agent_router
from backend.api.stream import router as stream_router

from core.logger import (
    info, error as log_error, warning,
    set_request_context, clear_request_context,
)

# ── 配置 ──
APP_VERSION = os.getenv("APP_VERSION", "7.2.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

# 速率限制器
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


# ── 生命周期管理 ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    info(f"应用启动 v{APP_VERSION}")
    yield
    info("应用关闭")


# ── FastAPI 实例 ──
app = FastAPI(
    title="基于多智能体的个性化学习资源生成系统",
    description="多智能体协同架构，为学生提供个性化学习资源生成服务",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── 中间件 ──
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """请求中间件：ID注入 + 安全头 + 耗时统计 + 日志上下文"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    # 设置日志上下文
    set_request_context(request_id=request_id)

    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        log_error(f"未捕获异常: {exc}")
        response = JSONResponse(
            status_code=500,
            content={"success": False, "error": "服务器内部错误", "request_id": request_id},
        )
    finally:
        clear_request_context()

    # 响应头
    elapsed_ms = round((time.time() - start_time) * 1000, 1)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # 请求日志（排除健康检查和静态文件）
    path = request.url.path
    if not path.startswith("/api/health") and not path.startswith("/exports"):
        info(f"{request.method} {path} {response.status_code} {elapsed_ms}ms")

    return response


# ── 全局异常处理 ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    log_error(f"未捕获异常 [{request_id}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "request_id": request_id,
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "资源不存在"},
    )


@app.exception_handler(422)
async def validation_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "请求参数校验失败", "detail": str(exc)},
    )


# ── 路由注册 ──
app.include_router(agent_router, prefix="/api", tags=["学习智能体"])
app.include_router(stream_router, prefix="/api/stream", tags=["流式输出"])
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])

# 静态文件
exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


# ── 健康检查 ──
@app.get("/api/health", tags=["系统"])
async def health_check():
    """详细健康检查，包含依赖状态"""
    checks = {"api": "ok"}

    # MySQL 检查
    try:
        from data.db_operations import profile_db
        if profile_db.connect():
            profile_db.cursor.execute("SELECT 1")
            profile_db.cursor.fetchone()
            profile_db.close()
            checks["mysql"] = "ok"
        else:
            checks["mysql"] = "error"
    except Exception:
        checks["mysql"] = "error"

    # FAISS 检查
    try:
        from data.rag_knowledge_base import vector_index
        checks["faiss"] = "ok" if vector_index._faiss_available else "unavailable"
    except Exception:
        checks["faiss"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
    }


# ── 系统信息 ──
@app.get("/api/info", tags=["系统"])
async def system_info():
    return {
        "name": "基于多智能体的个性化学习资源生成系统",
        "version": APP_VERSION,
        "features": [
            "对话式学生画像构建 (8维度)",
            "多智能体协同资源生成 (7种类型)",
            "个性化学习路径规划",
            "智能辅导 (多模态答疑)",
            "学习效果评估",
            "防幻觉与内容安全",
            "流式输出进度追踪",
            "5种2023-2026前沿检索算法",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level="debug" if DEBUG else "info",
        access_log=False,  # 由中间件处理
    )
