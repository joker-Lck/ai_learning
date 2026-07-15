"""
智能体消息协议
定义智能体间通信的消息格式、类型和路由规则
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════
# 消息类型枚举
# ═══════════════════════════════════════════

class MessageType(str, Enum):
    """消息类型 — 驱动智能体行为的事件分类"""

    # ── 请求/响应 ──
    REQUEST = "request"               # 普通请求
    RESPONSE = "response"             # 普通响应

    # ── 协商 ──
    PROPOSE = "propose"               # 提议（A → B: 我建议你这样做）
    ACCEPT = "accept"                 # 接受提议
    REJECT = "reject"                 # 拒绝提议
    COUNTER = "counter"               # 反提议

    # ── 广播 ──
    BROADCAST = "broadcast"           # 广播（发送给所有订阅者）
    NOTIFY = "notify"                 # 通知（单向，无需响应）

    # ── 协作 ──
    DELEGATE = "delegate"             # 委托任务
    REPORT = "report"                 # 汇报结果
    FEEDBACK = "feedback"             # 反馈（评估→资源: 资源质量不佳）
    QUERY = "query"                   # 查询（路径→画像: 获取学生薄弱点）

    # ── 生命周期 ──
    HEARTBEAT = "heartbeat"           # 心跳
    ERROR = "error"                   # 错误


class AgentRole(str, Enum):
    """智能体角色标识"""
    COORDINATOR = "coordinator"
    PROFILE = "profile"
    RESOURCE = "resource"
    PATH = "path"
    TUTOR = "tutor"
    ASSESSMENT = "assessment"


class TaskPriority(int, Enum):
    """任务优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


# ═══════════════════════════════════════════
# 消息数据结构
# ═══════════════════════════════════════════

@dataclass
class AgentMessage:
    """
    智能体间消息

    所有智能体通信的统一载体，支持：
    - 点对点请求/响应
    - 广播/订阅
    - 协商（提议→接受/拒绝/反提议）
    - 任务委托与结果汇报
    """

    # ── 路由信息 ──
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    msg_type: MessageType = MessageType.REQUEST
    sender: AgentRole = AgentRole.COORDINATOR
    receiver: AgentRole | None = None      # None = 广播
    session_id: str = ""
    correlation_id: str | None = None      # 关联请求的 msg_id（用于响应匹配）

    # ── 业务载荷 ──
    action: str = ""                          # 具体动作（如 "build_profile", "generate_resource"）
    payload: dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL

    # ── 元数据 ──
    timestamp: float = field(default_factory=time.time)
    ttl: float = 30.0                         # 消息存活时间（秒）
    retry_count: int = 0
    max_retries: int = 3

    # ── 结果 ──
    success: bool = True
    error: str | None = None

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def reply(self, sender: AgentRole, payload: dict, success: bool = True,
              error: str | None = None, msg_type: MessageType = MessageType.RESPONSE) -> "AgentMessage":
        """快速构造响应消息"""
        return AgentMessage(
            msg_type=msg_type,
            sender=sender,
            receiver=self.sender,
            session_id=self.session_id,
            correlation_id=self.msg_id,
            action=self.action,
            payload=payload,
            priority=self.priority,
            success=success,
            error=error,
        )

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type.value,
            "sender": self.sender.value,
            "receiver": self.receiver.value if self.receiver else None,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "action": self.action,
            "payload_summary": str(self.payload)[:200],
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "success": self.success,
        }

    def __repr__(self):
        return (f"Msg({self.msg_id[:6]} {self.msg_type.value} "
                f"{self.sender.value}→{self.receiver.value if self.receiver else '*'} "
                f"action={self.action})")


# ═══════════════════════════════════════════
# 协作上下文 — 追踪一次完整协作流程
# ═══════════════════════════════════════════

@dataclass
class CollaborationContext:
    """
    协作上下文 — 记录一次多智能体协作的完整生命周期

    用于：
    - 追踪参与的智能体和各自贡献
    - 支持协商过程（提议/接受/拒绝）
    - 聚合最终结果
    """
    session_id: str
    user_id: int
    task_type: str = ""
    initiated_by: AgentRole = AgentRole.COORDINATOR
    participants: list[AgentRole] = field(default_factory=list)
    message_log: list[AgentMessage] = field(default_factory=list)
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    negotiations: list[dict] = field(default_factory=list)   # 协商记录
    start_time: float = field(default_factory=time.time)
    status: str = "pending"                                   # pending → running → negotiating → completed → failed

    def add_participant(self, role: AgentRole):
        if role not in self.participants:
            self.participants.append(role)

    def log_message(self, msg: AgentMessage):
        self.message_log.append(msg)

    def set_result(self, key: str, value: Any):
        self.intermediate_results[key] = value

    def get_result(self, key: str, default=None):
        return self.intermediate_results.get(key, default)

    def log_negotiation(self, proposer: AgentRole, target: AgentRole,
                        proposal: str, outcome: str, detail: str = ""):
        self.negotiations.append({
            "proposer": proposer.value,
            "target": target.value,
            "proposal": proposal,
            "outcome": outcome,         # accepted / rejected / counter
            "detail": detail,
            "timestamp": time.time()
        })

    @property
    def elapsed_ms(self) -> int:
        return int((time.time() - self.start_time) * 1000)

    @property
    def message_count(self) -> int:
        return len(self.message_log)

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "task_type": self.task_type,
            "participants": [p.value for p in self.participants],
            "message_count": self.message_count,
            "negotiation_count": len(self.negotiations),
            "elapsed_ms": self.elapsed_ms,
            "status": self.status,
        }
