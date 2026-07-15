"""
多智能体协调器 — 事件驱动架构
负责任务分发、智能体调度、结果整合、协商决策

架构升级：
- 消息总线驱动：智能体通过 MessageBus 发布/订阅消息，而非直接函数调用
- 并发编排：独立任务通过线程池并行执行
- 协商机制：资源生成前与画像智能体协商最优策略
- 协作上下文：完整追踪多智能体协作生命周期
"""

import json
import time
from datetime import datetime
from typing import Any

from core.logger import debug, error, info
from services.agent_message import (
    AgentMessage,
    AgentRole,
    CollaborationContext,
    MessageType,
    TaskPriority,
)
from services.assessment_agent import AssessmentAgent
from services.message_bus import message_bus
from services.path_agent import PathAgent
from services.profile_agent import ProfileAgent
from services.resource_agent import ResourceAgent
from services.tutor_agent import TutorAgent


class AgentCoordinator:
    """智能体协调器 — 多智能体系统的核心控制器"""

    def __init__(self):
        # ── 初始化各专业智能体 ──
        self.profile_agent = ProfileAgent()
        self.resource_agent = ResourceAgent()
        self.path_agent = PathAgent()
        self.tutor_agent = TutorAgent()
        self.assessment_agent = AssessmentAgent()

        # ── 注册到消息总线 ──
        self._register_handlers()

        info("多智能体协调器初始化完成（事件驱动架构）")

    # ═══════════════════════════════════════
    # 消息总线注册
    # ═══════════════════════════════════════

    def _register_handlers(self):
        """将各智能体注册为消息总线的处理器"""
        message_bus.subscribe(AgentRole.PROFILE, self._handle_profile_message)
        message_bus.subscribe(AgentRole.RESOURCE, self._handle_resource_message)
        message_bus.subscribe(AgentRole.PATH, self._handle_path_message)
        message_bus.subscribe(AgentRole.TUTOR, self._handle_tutor_message)
        message_bus.subscribe(AgentRole.ASSESSMENT, self._handle_assessment_message)

    def _handle_profile_message(self, msg: AgentMessage) -> AgentMessage | None:
        """画像智能体消息处理器"""
        if msg.msg_type in (MessageType.REQUEST, MessageType.QUERY):
            result = self.profile_agent.build_profile(
                msg.payload.get("user_id", 0), msg.payload
            )
            return msg.reply(AgentRole.PROFILE, result)

        if msg.msg_type == MessageType.PROPOSE:
            # 画像智能体接受资源生成策略的协商
            return msg.reply(
                AgentRole.PROFILE,
                {"accepted": True, "profile_suggestion": "基于学生画像推荐个性化资源"},
                msg_type=MessageType.ACCEPT,
            )
        return None

    def _handle_resource_message(self, msg: AgentMessage) -> AgentMessage | None:
        """资源智能体消息处理器"""
        if msg.msg_type in (MessageType.REQUEST, MessageType.DELEGATE):
            result = self.resource_agent.generate_resources(
                msg.payload.get("user_id", 0), msg.payload
            )
            return msg.reply(AgentRole.RESOURCE, result)

        if msg.msg_type == MessageType.FEEDBACK:
            # 收到评估智能体的反馈，记录质量问题
            debug(f"资源智能体收到反馈: {msg.payload}")
            return msg.reply(AgentRole.RESOURCE, {"acknowledged": True})
        return None

    def _handle_path_message(self, msg: AgentMessage) -> AgentMessage | None:
        """路径智能体消息处理器"""
        if msg.msg_type in (MessageType.REQUEST, MessageType.DELEGATE):
            result = self.path_agent.plan_path(
                msg.payload.get("user_id", 0), msg.payload
            )
            return msg.reply(AgentRole.PATH, result)
        return None

    def _handle_tutor_message(self, msg: AgentMessage) -> AgentMessage | None:
        """辅导智能体消息处理器"""
        if msg.msg_type == MessageType.REQUEST:
            result = self.tutor_agent.answer_query(
                msg.payload.get("user_id", 0), msg.payload
            )
            return msg.reply(AgentRole.TUTOR, result)
        return None

    def _handle_assessment_message(self, msg: AgentMessage) -> AgentMessage | None:
        """评估智能体消息处理器"""
        if msg.msg_type == MessageType.REQUEST:
            result = self.assessment_agent.assess(
                msg.payload.get("user_id", 0), msg.payload
            )
            return msg.reply(AgentRole.ASSESSMENT, result)
        return None

    # ═══════════════════════════════════════
    # 任务执行入口（保持向后兼容）
    # ═══════════════════════════════════════

    def execute_task(self,
                    task_type: str,
                    user_id: int,
                    input_data: dict[str, Any],
                    session_id: str | None = None) -> dict[str, Any]:
        """
        执行任务 — 通过消息总线调度智能体

        Args:
            task_type: 任务类型
            user_id: 用户ID
            input_data: 输入数据
            session_id: 会话ID

        Returns:
            执行结果（与旧版 API 完全兼容）
        """
        start_time = time.time()

        if not session_id:
            session_id = f"session_{int(time.time())}_{user_id}"

        # 创建协作上下文
        ctx = message_bus.create_context(session_id, user_id, task_type)
        ctx.status = "running"

        result = {
            "success": False,
            "session_id": session_id,
            "task_type": task_type,
            "data": None,
            "message": "",
            "execution_time_ms": 0,
            "collaboration": None,
        }

        try:
            info(f"开始执行任务: {task_type}, 用户: {user_id}, 会话: {session_id}")

            # ── 路由到对应处理流程 ──
            task_map = {
                "build_profile":           self._msg_build_profile,
                "generate_resources":      self._msg_generate_resources,
                "plan_learning_path":      self._msg_plan_path,
                "tutor_query":             self._msg_tutor_query,
                "assess_learning":         self._msg_assess_learning,
                "comprehensive_learning_plan": self._msg_comprehensive_plan,
            }

            handler = task_map.get(task_type)
            if handler:
                result["data"] = handler(user_id, input_data, ctx)
                result["success"] = True
                result["message"] = self._success_message(task_type, result["data"])
            else:
                result["message"] = f"未知任务类型: {task_type}"
                error(f"未知任务类型: {task_type}")

        except Exception as e:
            result["message"] = f"任务执行失败: {e!s}"
            ctx.status = "failed"
            error(f"任务执行失败 [{task_type}]: {e!s}")

        finally:
            execution_time = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time
            result["collaboration"] = ctx.summary()

            ctx.status = "completed" if result["success"] else "failed"
            self._log_collaboration(ctx, result)

            # 清理上下文（保留最近 100 个）
            if len(message_bus._contexts) > 100:
                oldest = sorted(message_bus._contexts.items(),
                               key=lambda x: x[1].start_time)[:50]
                for sid, _ in oldest:
                    message_bus.remove_context(sid)

            info(f"任务完成: {task_type}, 耗时: {execution_time}ms, "
                 f"消息数: {ctx.message_count}")

        return result

    # ═══════════════════════════════════════
    # 消息驱动的任务处理
    # ═══════════════════════════════════════

    def _msg_build_profile(self, user_id: int, input_data: dict,
                           ctx: CollaborationContext) -> dict:
        """通过消息总线构建学生画像"""
        msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.PROFILE,
            session_id=ctx.session_id,
            action="build_profile",
            payload={"user_id": user_id, **input_data},
        )
        ctx.add_participant(AgentRole.PROFILE)
        ctx.log_message(msg)

        response = message_bus.request(msg, timeout=30)
        if response:
            ctx.log_message(response)
            ctx.set_result("profile", response.payload)
            return response.payload

        return {"error": "画像构建超时"}

    def _msg_generate_resources(self, user_id: int, input_data: dict,
                                ctx: CollaborationContext) -> dict:
        """通过消息总线生成学习资源"""
        msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.RESOURCE,
            session_id=ctx.session_id,
            action="generate_resources",
            payload={"user_id": user_id, **input_data},
        )
        ctx.add_participant(AgentRole.RESOURCE)
        ctx.log_message(msg)

        response = message_bus.request(msg, timeout=60)
        if response:
            ctx.log_message(response)
            ctx.set_result("resources", response.payload)
            return response.payload

        return {"error": "资源生成超时"}

    def _msg_plan_path(self, user_id: int, input_data: dict,
                       ctx: CollaborationContext) -> dict:
        """通过消息总线规划学习路径"""
        msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.PATH,
            session_id=ctx.session_id,
            action="plan_path",
            payload={"user_id": user_id, **input_data},
        )
        ctx.add_participant(AgentRole.PATH)
        ctx.log_message(msg)

        response = message_bus.request(msg, timeout=90)
        if response:
            ctx.log_message(response)
            ctx.set_result("path", response.payload)
            return response.payload

        return {"error": "路径规划超时"}

    def _msg_tutor_query(self, user_id: int, input_data: dict,
                         ctx: CollaborationContext) -> dict:
        """通过消息总线进行智能辅导"""
        msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.TUTOR,
            session_id=ctx.session_id,
            action="tutor_query",
            payload={"user_id": user_id, **input_data},
        )
        ctx.add_participant(AgentRole.TUTOR)
        ctx.log_message(msg)

        response = message_bus.request(msg, timeout=90)
        if response:
            ctx.log_message(response)
            ctx.set_result("tutor_answer", response.payload)
            return response.payload

        return {"error": "辅导响应超时"}

    def _msg_assess_learning(self, user_id: int, input_data: dict,
                             ctx: CollaborationContext) -> dict:
        """通过消息总线评估学习效果"""
        msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.ASSESSMENT,
            session_id=ctx.session_id,
            action="assess",
            payload={"user_id": user_id, **input_data},
        )
        ctx.add_participant(AgentRole.ASSESSMENT)
        ctx.log_message(msg)

        response = message_bus.request(msg, timeout=30)
        if response:
            ctx.log_message(response)
            ctx.set_result("assessment", response.payload)
            return response.payload

        return {"error": "评估响应超时"}

    # ═══════════════════════════════════════
    # 综合学习计划 — 多智能体协同 + 协商
    # ═══════════════════════════════════════

    def _msg_comprehensive_plan(self, user_id: int, input_data: dict,
                                ctx: CollaborationContext) -> dict:
        """
        综合学习计划 — 展示真正的多智能体协同

        流程:
        1. [并发] 画像查询 + 学科知识检索
        2. [协商] 协调器→画像智能体: 基于画像推荐资源策略
        3. [并发] 资源生成 + 路径规划（可并行）
        4. [反馈] 评估智能体→资源智能体: 资源质量反馈
        5. [聚合] 整合所有结果
        """
        info(f"综合学习计划启动, 用户: {user_id}, 会话: {ctx.session_id}")
        ctx.status = "running"

        profile_data = input_data.get("profile")
        subject = input_data.get("subject", "")
        topic = input_data.get("topic", "")

        # ── Step 1: 并发获取画像 + 上下文 ──
        profile_msg = AgentMessage(
            msg_type=MessageType.REQUEST,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.PROFILE,
            session_id=ctx.session_id,
            action="get_or_build_profile",
            payload={"user_id": user_id},
        )
        ctx.add_participant(AgentRole.PROFILE)
        ctx.log_message(profile_msg)

        if not profile_data:
            profile_resp = message_bus.request(profile_msg, timeout=20)
            if profile_resp:
                ctx.log_message(profile_resp)
                profile_data = profile_resp.payload.get("profile", {})
                ctx.set_result("profile", profile_data)

        # ── Step 2: 协商 — 协调器向画像智能体提议资源策略 ──
        ctx.status = "negotiating"
        strategy = self._negotiate_resource_strategy(
            user_id, profile_data, subject, topic, ctx
        )
        ctx.status = "running"

        # ── Step 3: 并发执行资源生成 + 路径规划 ──
        resource_types = strategy.get("resource_types",
                                      input_data.get("resource_types",
                                                     ["document", "quiz", "mindmap"]))

        resource_msg = AgentMessage(
            msg_type=MessageType.DELEGATE,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.RESOURCE,
            session_id=ctx.session_id,
            action="generate_resources",
            payload={
                "user_id": user_id,
                "subject": subject,
                "topic": topic,
                "profile": profile_data,
                "resource_types": resource_types,
                "strategy": strategy,
            },
            priority=TaskPriority.HIGH,
        )
        ctx.add_participant(AgentRole.RESOURCE)
        ctx.log_message(resource_msg)

        path_msg = AgentMessage(
            msg_type=MessageType.DELEGATE,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.PATH,
            session_id=ctx.session_id,
            action="plan_path",
            payload={
                "user_id": user_id,
                "profile": profile_data,
                "learning_goal": input_data.get("learning_goal", ""),
            },
        )
        ctx.add_participant(AgentRole.PATH)
        ctx.log_message(path_msg)

        # 并发发送，等待两者完成
        responses = message_bus.parallel_requests(
            [resource_msg, path_msg], timeout=60
        )

        resources_result = responses[0].payload if responses[0] else {"resources": []}
        path_result = responses[1].payload if responses[1] else {"path": {}}

        ctx.set_result("resources", resources_result)
        ctx.set_result("path", path_result)

        # 记录响应消息
        for resp in responses:
            if resp:
                ctx.log_message(resp)

        # ── Step 4: 评估反馈（异步，不阻塞主流程）──
        self._async_assessment_feedback(user_id, resources_result, ctx)

        # ── Step 5: 聚合结果 ──
        recommendations = self._generate_recommendations(
            profile_data, resources_result, path_result
        )

        comprehensive_result = {
            "profile": profile_data,
            "resources": resources_result.get("resources", []),
            "learning_path": path_result.get("path"),
            "strategy": strategy,
            "recommendations": recommendations,
            "collaboration_summary": ctx.summary(),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        info(f"综合学习计划完成, 资源: {len(comprehensive_result['resources'])} 个, "
             f"消息: {ctx.message_count} 条, 协商: {len(ctx.negotiations)} 次")
        return comprehensive_result

    def _negotiate_resource_strategy(self, user_id: int, profile: dict,
                                     subject: str, topic: str,
                                     ctx: CollaborationContext) -> dict:
        """
        协商资源生成策略

        协调器向画像智能体提议资源策略，画像智能体基于学生画像
        给出建议（接受/拒绝/反提议）
        """
        # 构建提议
        cognitive_style = profile.get("cognitive_style", "") if profile else ""
        weak_points = profile.get("weak_points", []) if profile else []

        proposed_types = ["document", "quiz", "mindmap"]
        if "视觉" in cognitive_style:
            proposed_types.append("video")
        if "动觉" in cognitive_style:
            proposed_types.append("exercise")

        proposal = AgentMessage(
            msg_type=MessageType.PROPOSE,
            sender=AgentRole.COORDINATOR,
            receiver=AgentRole.PROFILE,
            session_id=ctx.session_id,
            action="negotiate_resource_strategy",
            payload={
                "user_id": user_id,
                "subject": subject,
                "topic": topic,
                "proposed_resource_types": proposed_types,
                "cognitive_style": cognitive_style,
                "weak_points": weak_points,
            },
        )
        ctx.log_message(proposal)

        response = message_bus.negotiate(proposal, timeout=10)

        if response and response.msg_type == MessageType.ACCEPT:
            # 画像智能体接受提议
            ctx.log_negotiation(
                AgentRole.COORDINATOR, AgentRole.PROFILE,
                f"资源策略: {proposed_types}", "accepted",
                response.payload.get("profile_suggestion", "")
            )
            ctx.log_message(response)
            return {
                "resource_types": proposed_types,
                "source": "negotiated",
                "profile_suggestion": response.payload.get("profile_suggestion", ""),
            }

        elif response and response.msg_type == MessageType.COUNTER:
            # 画像智能体反提议
            counter_types = response.payload.get("resource_types", proposed_types)
            ctx.log_negotiation(
                AgentRole.COORDINATOR, AgentRole.PROFILE,
                f"资源策略: {proposed_types}", "counter",
                f"反提议: {counter_types}"
            )
            ctx.log_message(response)
            return {
                "resource_types": counter_types,
                "source": "counter_proposal",
                "profile_suggestion": response.payload.get("profile_suggestion", ""),
            }

        else:
            # 超时或拒绝 — 使用默认策略
            ctx.log_negotiation(
                AgentRole.COORDINATOR, AgentRole.PROFILE,
                f"资源策略: {proposed_types}", "timeout",
                "使用默认策略"
            )
            return {
                "resource_types": proposed_types,
                "source": "default",
            }

    def _async_assessment_feedback(self, user_id: int, resources_result: dict,
                                   ctx: CollaborationContext):
        """异步发送评估反馈（不阻塞主流程）"""
        resources = resources_result.get("resources", [])
        if not resources:
            return

        feedback_msg = AgentMessage(
            msg_type=MessageType.FEEDBACK,
            sender=AgentRole.ASSESSMENT,
            receiver=AgentRole.RESOURCE,
            session_id=ctx.session_id,
            action="quality_feedback",
            payload={
                "user_id": user_id,
                "resource_count": len(resources),
                "resource_types": [r.get("type", "") for r in resources[:5]],
            },
        )
        ctx.add_participant(AgentRole.ASSESSMENT)
        ctx.log_message(feedback_msg)

        # 异步投递，不等待响应
        message_bus.publish(feedback_msg)

    # ═══════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════

    def _success_message(self, task_type: str, data: dict) -> str:
        """生成成功消息"""
        msg_map = {
            "build_profile": "学生画像构建成功",
            "generate_resources": f"成功生成 {len(data.get('resources', []))} 个学习资源",
            "plan_learning_path": "个性化学习路径规划完成",
            "tutor_query": "智能辅导回答生成完成",
            "assess_learning": "学习效果评估完成",
            "comprehensive_learning_plan": "综合学习计划生成完成",
        }
        return msg_map.get(task_type, "任务执行完成")

    def _generate_recommendations(self, profile, resources_result, path_result) -> list[str]:
        """基于画像、资源和路径生成学习建议"""
        recommendations = []

        if not profile:
            return ["暂无画像数据，建议先完成学生画像构建"]

        # 基于认知风格推荐
        cognitive_style = profile.get("cognitive_style", "")
        if "视觉" in cognitive_style:
            recommendations.append("建议优先观看视频资源，配合图表学习")
        elif "听觉" in cognitive_style:
            recommendations.append("建议通过讲解音频和讨论加深理解")
        elif "动觉" in cognitive_style:
            recommendations.append("建议多做实操练习和项目实践")

        # 基于薄弱点推荐
        weak_points = profile.get("weak_points", [])
        if weak_points:
            recommendations.append(f"重点关注薄弱环节: {', '.join(weak_points[:3])}")

        # 基于学习路径推荐
        if path_result and path_result.get("path"):
            total_steps = path_result["path"].get("total_steps", 0)
            estimated_hours = path_result["path"].get("estimated_hours", 0)
            if total_steps:
                recommendations.append(
                    f"学习路径包含 {total_steps} 个步骤，预计需要 {estimated_hours} 小时"
                )

        # 基于策略推荐
        if isinstance(resources_result, dict):
            strategy = resources_result.get("strategy", {})
            if strategy.get("source") == "negotiated":
                recommendations.append("资源策略已根据学生画像个性化调整")

        return recommendations if recommendations else ["建议按学习路径逐步推进"]

    def _log_collaboration(self, ctx: CollaborationContext, result: dict):
        """记录协作日志"""
        try:
            log_summary = {
                "session_id": ctx.session_id,
                "user_id": ctx.user_id,
                "task_type": ctx.task_type,
                "participants": [p.value for p in ctx.participants],
                "message_count": ctx.message_count,
                "negotiations": len(ctx.negotiations),
                "status": ctx.status,
                "elapsed_ms": ctx.elapsed_ms,
                "success": result.get("success", False),
            }
            debug(f"协作日志: {json.dumps(log_summary, ensure_ascii=False)}")

        except Exception as e:
            error(f"记录协作日志失败: {e!s}")

    def get_bus_stats(self) -> dict:
        """获取消息总线统计（供 API 查询）"""
        return message_bus.get_stats()


# 全局协调器实例
agent_coordinator = AgentCoordinator()
