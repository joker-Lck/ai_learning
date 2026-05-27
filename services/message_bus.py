"""
事件驱动消息总线
智能体间通信的核心基础设施，提供：
- Pub/Sub 发布订阅
- 点对点消息路由
- 同步请求/响应（带超时）
- 广播分发
- 并发任务编排
- 消息追踪与统计
"""

import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict
from core.logger import info, error, debug, warning
from services.agent_message import (
    AgentMessage, MessageType, AgentRole, TaskPriority,
    CollaborationContext,
)

# 消息处理器类型: (msg: AgentMessage) -> Optional[AgentMessage]
MessageHandler = Callable[[AgentMessage], Optional[AgentMessage]]


class MessageBus:
    """
    事件驱动消息总线

    核心能力:
    1. publish(msg)       — 发布消息，总线路由到目标智能体
    2. subscribe(role, h) — 订阅某角色的消息
    3. request(msg, timeout) — 同步请求/响应（阻塞等待）
    4. broadcast(msg)     — 广播给所有订阅者
    5. submit_task(fn)    — 提交并发任务，返回 Future
    6. negotiate(msg)     — 发起协商（propose → accept/reject/counter）

    架构:
    ┌─────────┐    publish     ┌──────────┐    dispatch    ┌──────────┐
    │ Agent A  │ ──────────→  │ Message  │ ────────────→  │ Agent B  │
    └─────────┘               │   Bus    │               └──────────┘
    ┌─────────┐    subscribe  │          │    broadcast   ┌──────────┐
    │ Agent C  │ ←────────── │          │ ────────────→  │ Agent D  │
    └─────────┘               └──────────┘               └──────────┘
    """

    def __init__(self, max_workers: int = 4):
        # ── 订阅表: role → [handler, ...] ──
        self._subscribers: Dict[AgentRole, List[MessageHandler]] = defaultdict(list)

        # ── 待响应消息: correlation_id → Event+Queue ──
        self._pending_responses: Dict[str, Dict] = {}

        # ── 消息队列（按优先级排序）──
        self._message_queue = queue.PriorityQueue()

        # ── 线程池（并发调度）──
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="agent_bus"
        )

        # ── 统计 ──
        self._stats = {
            "total_published": 0,
            "total_delivered": 0,
            "total_errors": 0,
            "avg_latency_ms": 0,
        }
        self._latency_samples: List[float] = []

        # ── 协作上下文缓存 ──
        self._contexts: Dict[str, CollaborationContext] = {}

        # ── 锁 ──
        self._lock = threading.Lock()

        info("消息总线初始化完成")

    # ═══════════════════════════════════════
    # Pub/Sub 发布订阅
    # ═══════════════════════════════════════

    def subscribe(self, role: AgentRole, handler: MessageHandler):
        """注册消息处理器（每个角色可注册多个处理器）"""
        with self._lock:
            self._subscribers[role].append(handler)
        debug(f"消息总线: {role.value} 注册处理器")

    def unsubscribe(self, role: AgentRole, handler: MessageHandler):
        """移除消息处理器"""
        with self._lock:
            handlers = self._subscribers.get(role, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, msg: AgentMessage) -> Optional[AgentMessage]:
        """
        发布消息 — 总线路由到目标智能体

        - 点对点: msg.receiver 有值 → 直接分发
        - 广播:   msg.receiver 为 None → 分发给所有订阅者
        - 请求/响应: 同步阻塞等待响应

        返回:
        - REQUEST 类型: 返回响应消息（阻塞）
        - 其他类型: 返回 None（异步投递）
        """
        if msg.is_expired():
            warning(f"消息已过期: {msg}")
            return None

        self._stats["total_published"] += 1
        start = time.time()

        # 如果是请求类型，走同步等待路径
        if msg.msg_type == MessageType.REQUEST:
            return self._request_response(msg)

        # 如果是广播
        if msg.receiver is None or msg.msg_type == MessageType.BROADCAST:
            self._dispatch_broadcast(msg)
            return None

        # 点对点异步投递
        self._dispatch_to_target(msg)

        latency = (time.time() - start) * 1000
        self._record_latency(latency)
        return None

    # ═══════════════════════════════════════
    # 同步请求/响应
    # ═══════════════════════════════════════

    def request(self, msg: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        同步请求 — 发送消息并阻塞等待响应

        Args:
            msg: 请求消息（自动设为 REQUEST 类型）
            timeout: 超时秒数

        Returns:
            响应消息，超时返回 None
        """
        msg.msg_type = MessageType.REQUEST
        return self._request_response(msg, timeout)

    def _request_response(self, msg: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """内部: 发送请求并等待响应"""
        event = threading.Event()
        response_holder = {"msg": None}

        with self._lock:
            self._pending_responses[msg.msg_id] = {
                "event": event,
                "response": response_holder,
            }

        # 投递消息
        self._dispatch_to_target(msg)

        # 等待响应
        if event.wait(timeout=timeout):
            with self._lock:
                self._pending_responses.pop(msg.msg_id, None)
            return response_holder["msg"]
        else:
            # 超时
            with self._lock:
                self._pending_responses.pop(msg.msg_id, None)
            warning(f"消息响应超时: {msg}")
            return None

    # ═══════════════════════════════════════
    # 协商机制
    # ═══════════════════════════════════════

    def negotiate(self, proposal: AgentMessage, timeout: float = 15.0) -> AgentMessage:
        """
        发起协商 — 提议→等待接受/拒绝/反提议

        Args:
            proposal: 提议消息（自动设为 PROPOSE 类型）
            timeout: 等待超时

        Returns:
            响应（ACCEPT / REJECT / COUNTER）
        """
        proposal.msg_type = MessageType.PROPOSE
        response = self._request_response(proposal, timeout)

        if response is None:
            # 超时视为拒绝
            return proposal.reply(
                sender=proposal.receiver or AgentRole.COORDINATOR,
                payload={"reason": "协商超时"},
                success=False,
                msg_type=MessageType.REJECT,
            )
        return response

    # ═══════════════════════════════════════
    # 并发任务编排
    # ═══════════════════════════════════════

    def submit_task(self, fn: Callable, *args, **kwargs) -> Future:
        """提交并发任务到线程池"""
        return self._executor.submit(fn, *args, **kwargs)

    def parallel_requests(self, messages: List[AgentMessage],
                          timeout: float = 30.0) -> List[Optional[AgentMessage]]:
        """
        并发发送多个请求，等待全部完成

        Args:
            messages: 请求消息列表
            timeout: 总超时

        Returns:
            响应列表（与输入一一对应，超时为 None）
        """
        futures: List[Future] = []
        for msg in messages:
            msg.msg_type = MessageType.REQUEST
            future = self._executor.submit(self._request_response, msg, timeout)
            futures.append(future)

        results = []
        for future in futures:
            try:
                results.append(future.result(timeout=timeout))
            except Exception as e:
                warning(f"并发请求异常: {e}")
                results.append(None)
        return results

    # ═══════════════════════════════════════
    # 上下文管理
    # ═══════════════════════════════════════

    def create_context(self, session_id: str, user_id: int,
                       task_type: str = "") -> CollaborationContext:
        """创建协作上下文"""
        ctx = CollaborationContext(
            session_id=session_id,
            user_id=user_id,
            task_type=task_type,
        )
        self._contexts[session_id] = ctx
        return ctx

    def get_context(self, session_id: str) -> Optional[CollaborationContext]:
        """获取协作上下文"""
        return self._contexts.get(session_id)

    def remove_context(self, session_id: str):
        """清理协作上下文"""
        self._contexts.pop(session_id, None)

    # ═══════════════════════════════════════
    # 统计
    # ═══════════════════════════════════════

    def get_stats(self) -> Dict:
        """获取消息总线统计"""
        with self._lock:
            avg_latency = (
                sum(self._latency_samples[-100:]) / len(self._latency_samples[-100:])
                if self._latency_samples else 0
            )
            return {
                **self._stats,
                "avg_latency_ms": round(avg_latency, 2),
                "pending_responses": len(self._pending_responses),
                "active_contexts": len(self._contexts),
                "subscribers": {
                    role.value: len(handlers)
                    for role, handlers in self._subscribers.items()
                    if handlers
                },
            }

    # ═══════════════════════════════════════
    # 内部分发
    # ═══════════════════════════════════════

    def _dispatch_to_target(self, msg: AgentMessage):
        """分发消息到目标智能体"""
        target = msg.receiver
        if target is None:
            self._dispatch_broadcast(msg)
            return

        handlers = self._subscribers.get(target, [])
        if not handlers:
            warning(f"消息总线: {target.value} 无处理器, 消息丢弃 {msg}")
            self._stats["total_errors"] += 1
            return

        for handler in handlers:
            try:
                response = handler(msg)
                self._stats["total_delivered"] += 1

                # 如果处理器返回了响应消息，投递回去
                if response is not None and msg.msg_type == MessageType.REQUEST:
                    self._deliver_response(msg.msg_id, response)

            except Exception as e:
                error(f"消息处理异常 [{target.value}]: {e}")
                self._stats["total_errors"] += 1

    def _dispatch_broadcast(self, msg: AgentMessage):
        """广播消息到所有订阅者"""
        for role, handlers in self._subscribers.items():
            # 不回发给发送者
            if role == msg.sender:
                continue
            for handler in handlers:
                try:
                    handler(msg)
                    self._stats["total_delivered"] += 1
                except Exception as e:
                    error(f"广播处理异常 [{role.value}]: {e}")
                    self._stats["total_errors"] += 1

    def _deliver_response(self, correlation_id: str, response: AgentMessage):
        """投递响应到等待中的请求"""
        with self._lock:
            pending = self._pending_responses.get(correlation_id)
            if pending:
                pending["response"]["msg"] = response
                pending["event"].set()

    def _record_latency(self, latency_ms: float):
        """记录延迟样本"""
        with self._lock:
            self._latency_samples.append(latency_ms)
            if len(self._latency_samples) > 500:
                self._latency_samples = self._latency_samples[-200:]

    # ═══════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════

    def shutdown(self):
        """关闭消息总线"""
        self._executor.shutdown(wait=False)
        info("消息总线已关闭")


# 全局单例
message_bus = MessageBus()
