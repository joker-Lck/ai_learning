"""多智能体系统模块"""
from services.agent_coordinator import AgentCoordinator, agent_coordinator
from services.agent_message import AgentMessage, MessageType, AgentRole, CollaborationContext
from services.message_bus import MessageBus, message_bus
from services.profile_agent import ProfileAgent
from services.resource_agent import ResourceAgent
from services.path_agent import PathAgent
from services.tutor_agent import TutorAgent
from services.assessment_agent import AssessmentAgent