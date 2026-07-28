"""Services 包初始化
封装所有核心业务逻辑，实现前后端解耦
包括多智能体系统
"""
from services.agent_coordinator import AgentCoordinator, agent_coordinator
from services.agent_message import AgentMessage, AgentRole, CollaborationContext, MessageType
from services.assessment_agent import AssessmentAgent
from services.auth_service import AuthService, auth_service
from services.content_safety_service import ContentSafetyService
from services.image_service import ImageService
from services.message_bus import MessageBus, message_bus
from services.path_agent import PathAgent
from services.profile_agent import ProfileAgent
from services.qa_service import QAService, qa_service
from services.resource_agent import ResourceAgent
from services.advanced_retrieval_service import AdvancedRetrievalService, retrieval_service
from services.streaming_service import ProgressTracker, SSEStreamGenerator
from services.animation_service import AnimationService
from services.tutor_agent import TutorAgent
