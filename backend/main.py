"""
FastAPI 应用入口
多模态 AI 教学智能体 - 后端 API 服务
"""
import sys
import os

# 将项目根目录添加到 Python 路径, 以便复用现有 services/data/core 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
from backend.api.memory import router as memory_router

from core.logger import info, error as log_error

# 速率限制器 — 基于客户端 IP
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    info("🚀 AI 教学智能体 API 服务启动")
    yield
    info("👋 AI 教学智能体 API 服务关闭")


app = FastAPI(
    title="基于多智能体的个性化学习资源生成系统",
    description="""
    ## 核心功能

    本系统采用多智能体协同架构,为学生提供个性化学习资源生成服务。

    ### 主要特性
    - 🎯 **对话式学生画像**: 自然语言构建8维度动态画像
    - 🤖 **多智能体协同**: 6个专业智能体分工协作
    - 📚 **7种资源类型**: 文档/思维导图/题库/视频/动画/代码/阅读
    - 🛡️ **防幻觉机制**: RAG验证+事实核查+引用标注
    - ⚡ **流式输出**: SSE实时推送生成进度
    - 🔒 **内容安全**: 敏感词过滤+学术规范检查

    ### API分类
    - **学习智能体** (核心): 画像构建、资源生成、路径规划、智能辅导、效果评估
    - **流式输出与安全** (核心): SSE进度推送、内容安全检查、事实验证
    - **认证**: 用户登录注册
    """,
    version="7.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 速率限制
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置 - 允许 Next.js 前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 只保留核心功能
# 核心功能 - 多智能体系统
app.include_router(agent_router, prefix="/api", tags=["🎯 学习智能体 (核心)"])
app.include_router(stream_router, prefix="/api/stream", tags=["⚡ 流式输出与安全 (核心)"])
app.include_router(memory_router, prefix="/api", tags=["🧠 记忆系统 (核心)"])

# 基础功能
app.include_router(auth_router, prefix="/api/auth", tags=["🔐 认证"])

# 静态文件服务 - 用于导出资源文件
exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
os.makedirs(exports_dir, exist_ok=True)
app.mount("/exports", StaticFiles(directory=exports_dir), name="exports")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log_error(f"未捕获的异常: {str(exc)}")
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "detail": str(exc),
        },
    )


# 健康检查
@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "7.2.0",
        "timestamp": datetime.now().isoformat(),
    }


# 系统信息
@app.get("/api/info", tags=["系统"])
async def system_info():
    """系统信息"""
    from data.data_manager import CacheManager

    config = CacheManager.load_env_config()
    return {
        "name": "基于多智能体的个性化学习资源生成系统",
        "version": "7.2.0",
        "api_base": config.get("base_url", ""),
        "features": [
            "对话式学生画像构建 (8维度)",
            "多智能体协同资源生成 (7种类型)",
            "个性化学习路径规划",
            "智能辅导 (多模态答疑)",
            "学习效果评估",
            "防幻觉与内容安全",
            "流式输出进度追踪",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
