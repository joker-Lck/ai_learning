"""
自定义异常类 - 分层异常处理
"""


class AppException(Exception):
    """应用基础异常"""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AppException):
    """业务验证异常"""

    def __init__(self, message: str, field: str = ""):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400)
        self.field = field


class AuthenticationError(AppException):
    """认证异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, code="AUTH_ERROR", status_code=401)


class RateLimitError(AppException):
    """频率限制异常"""

    def __init__(self, message: str = "请求过于频繁，请稍后重试"):
        super().__init__(message=message, code="RATE_LIMIT", status_code=429)

