"""
Pydantic 请求模型 - 学习智能体 API
"""
from pydantic import BaseModel, Field


class GenerateResourcesRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    resource_types: list[str] = Field(default=["document", "quiz", "mindmap"])
    difficulty: str = Field("intermediate")


class TutorQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    subject: str = Field("通用")
    preferred_format: str = Field("all")
    session_id: str | None = Field(None)
