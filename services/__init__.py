"""Services 包初始化
封装所有核心业务逻辑，实现前后端解耦
包括多智能体系统
"""
from services.agents import (
    AgentCoordinator,
    AgentMessage,
    AgentRole,
    AssessmentAgent,
    CollaborationContext,
    MessageBus,
    MessageType,
    PathAgent,
    ProfileAgent,
    ResourceAgent,
    TutorAgent,
    agent_coordinator,
    message_bus,
)
from services.auth import AuthService, auth_service
from services.content import (
    AnimationService,
    ContentSafetyService,
    ImageService,
    ProgressTracker,
    QAService,
    SSEStreamGenerator,
    qa_service,
)
from services.retrieval import AdvancedRetrievalService, retrieval_service
