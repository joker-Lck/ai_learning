"""
Pydantic 数据模型 - 请求/响应结构定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


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
    error: Optional[str] = None
    data: Optional[Any] = None


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
    email: Optional[str] = Field(None, description="邮箱")


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    role: str
    email: Optional[str] = None


class AuthResponse(BaseResponse):
    """认证响应"""
    user: Optional[UserInfo] = None
    token: Optional[str] = None


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
    tokens_used: Optional[int] = None
    response_time_ms: Optional[float] = None
    rag_docs_count: int = 0


class QAResponse(BaseResponse):
    """问答响应"""
    answer: str = ""
    source_info: str = ""
    tokens_used: Optional[int] = None
    response_time_ms: Optional[float] = None
    rag_docs_found: List[Dict[str, Any]] = []


# ==================== 课件生成相关 ====================

class CoursewareGenerateRequest(BaseModel):
    """课件生成请求"""
    topic: str = Field(..., min_length=1, description="课件主题")
    requirements: str = Field("", description="需求描述")
    fast_mode: bool = Field(True, description="快速模式")
    grade_level: str = Field("", description="年级")


class ClarificationRequest(BaseModel):
    """需求澄清请求"""
    topic: str = Field(..., description="课件主题")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="对话历史")


class ClarificationReplyRequest(BaseModel):
    """需求澄清回复"""
    topic: str = Field(..., description="课件主题")
    conversation_history: List[Dict[str, str]] = Field(..., description="对话历史")


class RefineRequest(BaseModel):
    """课件调整请求"""
    feedback: str = Field(..., description="修改意见")
    topic: str = Field("", description="课件主题")
    subject: str = Field("", description="学科")
    slides: List[Dict[str, Any]] = Field(default_factory=list, description="当前幻灯片")


class SlideData(BaseModel):
    """单页幻灯片数据"""
    title: str = "无标题"
    subtitle: str = ""
    content: List[str] = Field(default_factory=list)
    layout: str = "title_content"
    background: Dict[str, Any] = Field(default_factory=lambda: {"type": "solid", "colors": ["#ffffff"]})
    decorations: List[Dict[str, Any]] = Field(default_factory=list)
    image_suggestion: str = ""
    notes: str = ""


class CoursewareTheme(BaseModel):
    """课件主题样式"""
    primary_color: str = "#0a192f"
    secondary_color: str = "#64ffda"
    accent_color: str = "#00d4ff"
    bg_color: str = "#ffffff"
    text_color: str = "#333333"
    template_style: str = "tech"


class CoursewareResponse(BaseResponse):
    """课件生成响应"""
    subject: str = ""
    outline: str = ""
    slides: List[Dict[str, Any]] = Field(default_factory=list)
    theme: Dict[str, Any] = Field(default_factory=dict)
    courseware_id: Optional[int] = None
    generated_images: Dict[str, Any] = Field(default_factory=dict)


class CoursewareListItem(BaseModel):
    """课件列表条目"""
    id: int
    title: str
    subject: str = ""
    grade_level: str = ""
    created_at: Optional[str] = None


# ==================== 知识库相关 ====================

class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    subject: Optional[str] = Field(None, description="限定学科")
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
    subject_distribution: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== 学情分析相关 ====================

class AnalysisRequest(BaseModel):
    """学情分析请求"""
    analysis_mode: str = Field("全班评估", description="分析模式: 单个学生/全班评估")
    student_name: Optional[str] = Field(None, description="学生姓名 (单个学生模式)")
    class_name: Optional[str] = Field(None, description="班级名称 (全班评估模式)")
    total_students: int = Field(45, description="班级总人数")


class AnalysisReportResponse(BaseResponse):
    """学情分析报告响应"""
    report: str = ""
    charts: Dict[str, Any] = Field(default_factory=dict)


class DataManageRequest(BaseModel):
    """数据管理请求"""
    action: str = Field(..., description="操作类型: backup/restore/export/clear/search")
    keyword: Optional[str] = Field(None, description="搜索关键词 (search 操作)")
    format: Optional[str] = Field(None, description="导出格式: json/txt (export 操作)")
