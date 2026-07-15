"""
Pydantic 请求模型 - 学习智能体 API
"""
from typing import Any

from pydantic import BaseModel, Field


class BuildProfileRequest(BaseModel):
    conversation_log: list[dict[str, str]] = Field(default_factory=list)
    basic_info: dict[str, Any] | None = Field(None)


class GenerateResourcesRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    resource_types: list[str] = Field(default=["document", "quiz", "mindmap"])
    difficulty: str = Field("intermediate")


class PlanPathRequest(BaseModel):
    learning_goal: str = Field(..., min_length=1)
    resources: list[dict[str, Any]] | None = Field(None)


class TutorQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    subject: str = Field("通用")
    preferred_format: str = Field("all")
    session_id: str | None = Field(None)


class AssessRequest(BaseModel):
    assessment_type: str = Field("comprehensive")
    period_start: str | None = Field(None)
    period_end: str | None = Field(None)


class ComprehensivePlanRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    learning_goal: str = Field("")
    resource_types: list[str] = Field(default=["document", "quiz", "mindmap"])


class UpdatePathProgressRequest(BaseModel):
    path_id: int = Field(...)
    completed_step: int = Field(...)


class ExportResourceRequest(BaseModel):
    resource: dict[str, Any] = Field(...)


class SaveResourceRequest(BaseModel):
    title: str = Field(..., min_length=1)
    resource_type: str = Field(...)
    subject: str = Field("")
    topic: str = Field("")
    difficulty_level: str = Field("intermediate")
    content_data: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] | None = Field(None)


class AdvancedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    subject: str | None = Field(None)
    strategy: str = Field("auto")
    limit: int = Field(5, ge=1, le=50)


class RecordSessionRequest(BaseModel):
    seconds: int = Field(0, ge=0)

