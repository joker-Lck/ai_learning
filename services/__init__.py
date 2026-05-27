"""Services 包初始化
封装所有核心业务逻辑，实现前后端解耦
包括多智能体系统
"""
from services.qa_service import QAService, qa_service
from services.image_service import ImageService
from services.animation_service import AnimationService
from services.auth_service import AuthService, auth_service
from services.content_safety_service import ContentSafetyService
from services.streaming_service import ProgressTracker, SSEStreamGenerator

# 多智能体系统
from services.agent_coordinator import AgentCoordinator, agent_coordinator
from services.agent_message import AgentMessage, MessageType, AgentRole, CollaborationContext
from services.message_bus import MessageBus, message_bus
from services.profile_agent import ProfileAgent
from services.resource_agent import ResourceAgent
from services.path_agent import PathAgent
from services.tutor_agent import TutorAgent
from services.assessment_agent import AssessmentAgent
