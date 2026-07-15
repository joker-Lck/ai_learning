"""
应用配置管理 — 基于 pydantic-settings 的环境隔离配置
支持 .env 文件 + 环境变量覆盖
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，优先级：环境变量 > .env 文件 > 默认值"""

    # ── 应用 ──
    app_name: str = "AI Learning Agent"
    app_version: str = "7.4.0"
    debug: bool = False
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # ── 安全 ──
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    jwt_refresh_days: int = 7

    # ── CORS ──
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    # ── MiMo AI ──
    mimo_api_key: str = Field(..., alias="MIMO_API_KEY")
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5-pro"
    mimo_vision_model: str = "mimo-v2.5"
    mimo_image_model: str = "mimo-image"
    mimo_tts_model: str = "mimo-tts"

    # ── 数据库 ──
    sqlite_db_dir: str = "data/databases"

    # ── 限流 ──
    rate_limit_global: str = "120/minute"
    rate_limit_login: str = "10/minute"
    rate_limit_register: str = "5/minute"

    # ── 日志 ──
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "console"

    # ── 上传 ──
    max_upload_size_mb: int = 50

    # ── RAG ──
    rag_similarity_threshold: float = 0.8

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（缓存）"""
    return Settings()
