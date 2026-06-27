"""
自定义异常类 - 分层异常处理
"""
from fastapi import HTTPException, status


class AppException(Exception):
    """应用基础异常"""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class DatabaseError(AppException):
    """数据库操作异常"""

    def __init__(self, message: str = "数据库操作失败", detail: str = ""):
        super().__init__(message=message, code="DB_ERROR", status_code=500)
        self.detail = detail


class AIServiceError(AppException):
    """AI 服务调用异常"""

    def __init__(self, message: str = "AI 服务调用失败", provider: str = "spark"):
        super().__init__(message=message, code="AI_SERVICE_ERROR", status_code=502)
        self.provider = provider


class ResourceGenerationError(AppException):
    """资源生成异常"""

    def __init__(self, resource_type: str, message: str = "资源生成失败"):
        super().__init__(
            message=f"{resource_type}: {message}",
            code="RESOURCE_GEN_ERROR",
            status_code=500,
        )
        self.resource_type = resource_type


class ValidationError(AppException):
    """业务验证异常"""

    def __init__(self, message: str, field: str = ""):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400)
        self.field = field


class AuthenticationError(AppException):
    """认证异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, code="AUTH_ERROR", status_code=401)


class AuthorizationError(AppException):
    """授权异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class RateLimitError(AppException):
    """频率限制异常"""

    def __init__(self, message: str = "请求过于频繁，请稍后重试"):
        super().__init__(message=message, code="RATE_LIMIT", status_code=429)

