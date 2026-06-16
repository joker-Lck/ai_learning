"""Services 包初始化
封装所有核心业务逻辑，实现前后端解耦
包括多智能体系统
"""
from services.content import QAService, qa_service, ImageService, AnimationService, ContentSafetyService, ProgressTracker, SSEStreamGenerator
from services.auth import AuthService, auth_service
from services.agents import AgentCoordinator, agent_coordinator, AgentMessage, MessageType, AgentRole, CollaborationContext, MessageBus, message_bus, ProfileAgent, ResourceAgent, PathAgent, TutorAgent, AssessmentAgent
from services.retrieval import AdvancedRetrievalService, retrieval_service
