"""
Pydantic 数据模型 - 请求/响应结构定义
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ==================== 通用模型 ====================

class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"
    GUEST = "guest"


class BaseResponse(BaseModel):
    """通用响应模型"""
    success: bool = True
    message: str = ""
    error: str | None = None
    data: Any | None = None


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    total: int = 0
    page: int = 1
    page_size: int = 20


# ==================== 认证相关 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=20, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: str | None = Field(None, description="邮箱")


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    role: str
    email: str | None = None


class AuthResponse(BaseResponse):
    """认证响应"""
    user: UserInfo | None = None
    token: str | None = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# ==================== 智能答疑相关 ====================

class QARequest(BaseModel):
    """问答请求"""
    question: str = Field(..., min_length=1, description="问题内容")
    scenario: str = Field("智能答疑", description="场景类型")


class QAHistoryItem(BaseModel):
    """问答历史条目"""
    question: str
    answer: str
    scenario: str = ""
    time: str = ""
    source: str = ""
    tokens_used: int | None = None
    response_time_ms: float | None = None
    rag_docs_count: int = 0


class QAResponse(BaseResponse):
    """问答响应"""
    answer: str = ""
    source_info: str = ""
    tokens_used: int | None = None
    response_time_ms: float | None = None
    rag_docs_found: list[dict[str, Any]] = []


# ==================== 知识库相关 ====================

class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    subject: str | None = Field(None, description="限定学科")
    limit: int = Field(10, ge=1, le=50, description="返回数量")


class KnowledgeDocument(BaseModel):
    """知识库文档"""
    id: int
    title: str
    subject: str = ""
    file_type: str = ""
    file_size: int = 0
    content_text: str = ""
    upload_time: str = ""


class KnowledgeStatsResponse(BaseResponse):
    """知识库统计响应"""
    total_documents: int = 0
    total_knowledge_points: int = 0
    average_usage: float = 0.0
    subject_distribution: list[dict[str, Any]] = Field(default_factory=list)


# ==================== 学情分析相关 ====================

class AnalysisRequest(BaseModel):
    """学情分析请求"""
    analysis_mode: str = Field("全班评估", description="分析模式: 单个学生/全班评估")
    student_name: str | None = Field(None, description="学生姓名 (单个学生模式)")
    class_name: str | None = Field(None, description="班级名称 (全班评估模式)")
    total_students: int = Field(45, description="班级总人数")


class AnalysisReportResponse(BaseResponse):
    """学情分析报告响应"""
    report: str = ""
    charts: dict[str, Any] = Field(default_factory=dict)


class DataManageRequest(BaseModel):
    """数据管理请求"""
    action: str = Field(..., description="操作类型: backup/restore/export/clear/search")
    keyword: str | None = Field(None, description="搜索关键词 (search 操作)")
    format: str | None = Field(None, description="导出格式: json/txt (export 操作)")
