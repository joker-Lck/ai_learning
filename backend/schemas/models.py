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
    role: UserRole = Field(UserRole.STUDENT, description="角色: teacher/student")


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


# ==================== 班级管理相关 ====================

class ClassCreateRequest(BaseModel):
    """创建班级请求"""
    name: str = Field(..., min_length=1, max_length=50, description="班级名称")
    subject: str = Field("", max_length=30, description="学科")
    grade_level: str = Field("", max_length=20, description="年级")
    semester: str = Field("", max_length=20, description="学期")
    description: str = Field("", max_length=200, description="备注")
    max_students: int | None = Field(None, ge=1, le=500, description="人数上限（可选）")


class ClassUpdateRequest(BaseModel):
    """更新班级信息请求"""
    name: str | None = Field(None, min_length=1, max_length=50, description="班级名称")
    subject: str | None = Field(None, max_length=30, description="学科")
    grade_level: str | None = Field(None, max_length=20, description="年级")
    semester: str | None = Field(None, max_length=20, description="学期")
    description: str | None = Field(None, max_length=200, description="备注")
    max_students: int | None = Field(None, ge=1, le=500, description="人数上限")


class ClassJoinRequest(BaseModel):
    """加入班级请求"""
    invite_code: str = Field(..., min_length=6, max_length=6, description="6位邀请码")
