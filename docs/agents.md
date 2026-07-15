# 多智能体系统设计

## 智能体角色

系统包含 **6 个专业智能体**，通过事件驱动消息总线分工协作。

| Agent | 角色 | 职责 | 模型 |
|-------|------|------|------|
| **ProfileAgent** | 画像师 | 9 维度对话式画像构建 | mimo-v2.5-pro |
| **ResourceAgent** | 讲师 | 7 种类型资源生成 | mimo-v2.5-pro |
| **PathAgent** | 导师 | 学习路径规划 | mimo-v2.5-pro |
| **TutorAgent** | 辅导员 | 多轮对话答疑 + 记忆增强 | mimo-v2.5-pro |
| **AssessmentAgent** | 评估师 | 多维度学习效果评估 | mimo-v2.5-pro |
| **Coordinator** | 指挥官 | 任务分发、结果聚合 | — |

## 协作流程

```
用户请求 ──► Coordinator
                │
                ├──► ProfileAgent  ──┐
                ├──► StudentData    ──┤ 并行采集
                ▼                    ▼
            协商优化 (画像 + 数据综合分析)
                │
        ┌───────┴───────┐
        ▼               ▼
  ResourceAgent    PathAgent       并行生成
        │               │
        ▼               ▼
  AssessmentAgent ──► 异步评估   ──► 返回用户
```

## 消息总线

系统使用事件驱动消息总线进行智能体间通信，支持 **14 种消息类型**。

### 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| TASK_REQUEST | Coordinator → Agent | 任务分发 |
| TASK_RESULT | Agent → Coordinator | 任务结果 |
| PROFILE_UPDATE | ProfileAgent → All | 画像更新通知 |
| RESOURCE_READY | ResourceAgent → All | 资源生成完成 |
| NEGOTIATION | Agent ↔ Agent | 协商决策 |
| STATUS_UPDATE | Agent → Coordinator | 状态更新 |
| ERROR_REPORT | Agent → Coordinator | 错误报告 |
| DATA_REQUEST | Agent → DataLayer | 数据查询 |
| DATA_RESPONSE | DataLayer → Agent | 数据返回 |
| AI_REQUEST | Agent → AILayer | AI 调用 |
| AI_RESPONSE | AILayer → Agent | AI 返回 |
| MEMORY_QUERY | TutorAgent → MemoryLayer | 记忆查询 |
| MEMORY_STORE | TutorAgent → MemoryLayer | 记忆存储 |
| SAFETY_CHECK | Any → SafetyService | 安全检查 |

### 协商决策机制

智能体之间支持三种协商决策：

| 决策 | 说明 |
|------|------|
| **Propose** | 提议方案 |
| **Accept** | 接受方案 |
| **Reject** | 拒绝方案 |
| **Counter** | 反提议 |

## 智能体职责详解

### ProfileAgent（画像师）

- 通过 8 轮对话采集学生信息
- 构建 9 维度动态画像
- 从课程表/成绩/错题中自动提取特征
- 支持手动编辑画像字段

### ResourceAgent（讲师）

- 根据画像生成 7 种类型资源
- 独立参数配置（难度/学科/主题）
- 内容安全检查
- 流式输出进度推送

### PathAgent（导师）

- 分析当前知识水平
- 规划有序学习路径
- 建立前置依赖关系
- 跟踪学习进度

### TutorAgent（辅导员）

- 多轮对话答疑
- 多模态回答（文字 + 图解 + 代码）
- 记忆增强上下文
- RAG 知识库检索

### AssessmentAgent（评估师）

- 多维度学习效果评估
- 基于真实数据的评估报告
- 可视化图表展示
- AI 不可用时降级到数据驱动评估

### Coordinator（指挥官）

- 任务分发与调度
- 结果聚合与合并
- 异常处理与降级
- 协商决策仲裁

## 辅助服务

### Reflector（反思验证器）

集成在 TutorAgent 中，对生成的答案进行质量评估和验证：

- **答案质量评分**（0-10）：准确性、完整性、相关性、逻辑性
- **证据链检查**：关键声明是否有上下文支撑
- **自动改进**：低分触发二次检索 + 重新生成，最多重试 2 次

### Multi-Hop Retriever（多跳推理检索）

作为第 12 种检索策略集成在 AdvancedRetrievalService 中：

- **逻辑图构建**：从种子文档提取实体-关系三元组
- **多跳探索**：2-5 跳深度推理，逐跳扩展证据链
- **证据链验证**：逻辑连贯性检查 + 置信度计算 + 剪枝

### Self-Learning Service（自学习闭环）

通过 API 端点收集用户反馈，驱动知识库增量更新：

- **反馈收集**：点赞/点踩/评分/评论
- **经验筛选**：置信度 ≥ 0.7 且评分 ≥ 4
- **数据增强**：基于高质量 QA 对生成变体
- **增量更新**：自动写入 RAG 知识库

## 源文件

| 文件 | 说明 |
|------|------|
| `services/agent_coordinator.py` | 协调器实现 |
| `services/message_bus.py` | 消息总线 |
| `services/agent_message.py` | 消息协议定义 |
| `services/profile_agent.py` | 画像智能体 |
| `services/resource_agent.py` | 资源智能体 |
| `services/path_agent.py` | 路径智能体 |
| `services/tutor_agent.py` | 辅导智能体 |
| `services/assessment_agent.py` | 评估智能体 |
| `services/reflector.py` | 反思验证器 |
| `services/multi_hop_retriever.py` | 多跳推理检索 |
| `services/self_learning_service.py` | 自学习闭环 |
