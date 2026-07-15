# 版本变更日志

## v7.5.0 (2026-07)

### 新增
- 学习能力雷达图（6维度评估）
  - 首页工作台右侧边栏迷你版（200px）
  - 学生画像页面顶部完整版（280px + 分数标签）
  - 6维度：知识基础、学习目标、记忆能力、自控力、专注度、学习深度
  - 基于画像数据动态评估（1-5分，默认3分）
  - 使用 Recharts RadarChart，紫色主题
- 企业级改造
  - 测试覆盖：45个单元测试（core/database/services），全部通过
  - CI/CD：GitHub Actions 流水线（Lint + Test Python 3.10/3.11/3.12 + Type Check）
  - RBAC权限：4级角色（admin>teacher>student>guest），细粒度权限控制
  - 配置管理：pydantic-settings 环境隔离（dev/staging/prod）
  - 代码规范：Ruff linter + pre-commit hooks + coverage 配置
  - 依赖管理：pyproject.toml 主依赖+dev依赖分离

### 改进
- 启动脚本路径修复：所有 .bat 文件正确解析到项目根目录
- setup.bat 更新：MIMO_API_KEY 引用，安装 pydantic-settings

## v7.4.0 (2026-07)

### 新增
- 反思验证器（Reflector）
  - 答案质量评分（0-10分，四维度评估）
  - 证据链完整性检查
  - 低分自动触发二次检索重新生成（最多2次重试）
- 多跳推理检索（Multi-Hop Retriever）
  - 逻辑图构建（实体-关系三元组）
  - 2-5跳深度推理探索
  - 证据链验证与置信度计算
  - 第12种检索策略：`multi_hop`
- 自学习闭环（Self-Learning Loop）
  - 用户反馈收集（点赞/点踩/评分/评论）
  - 高质量经验筛选（评分≥4，置信度≥0.7）
  - 数据增强（QA变体生成）
  - RAG知识库增量更新
- 新增API端点
  - `POST /api/agent/feedback` — 提交反馈
  - `GET /api/agent/learning-stats` — 自学习统计
  - `POST /api/agent/trigger-learning` — 手动触发学习循环
- 新增数据库表
  - `knowledge_entity_graph`（ai_rag_knowledge.db）— 知识实体关系图
  - `user_feedback`（ai_memory.db）— 用户反馈
  - `learning_experiences`（ai_memory.db）— 自学习经验

### 改进
- TutorAgent 集成反思验证器，自动评估答案质量
- 辅导回答返回 interaction_id 用于反馈追踪
- 所有文档统一为 MiMo AI（移除讯飞星火/Spark/Kimi引用）
- 前端框架文档修正为 Next.js 14 App Router + React 18

## v7.3.0 (2026-07)

### 新增
- 移动端 App（React Native + Expo）
  - 工作台仪表盘
  - 学生画像模块（含雷达图）
  - 资源生成模块（7 种类型）
  - 学习路径模块
  - 智能辅导模块（SSE 流式）
  - 效果评估模块
  - 知识库模块
- 完整文档体系（docs/ 目录）
  - 系统架构设计
  - API 接口参考
  - 数据库设计
  - 多智能体系统设计
  - 检索算法详解
  - 记忆系统设计
  - 安全机制说明
  - 部署指南
  - 移动端开发指南

---

## v7.2.0 (2026-06)

### 新增
- 8 种自定义异常类，分层异常处理
- 数据访问对象层（DAO：ResourceDAO + ActivityDAO）
- 12 个 Pydantic 请求模型
- 敏感词外部配置（125 词）

### 改进
- JWT 密钥缺失时启动失败（不再静默降级）
- 核心端点改用 Pydantic 模型 + DAO 层
- 敏感词支持外部 JSON 配置热更新

---

## v7.1.0 (2026-05)

### 新增
- 无限长时记忆架构（四层记忆模型）
- 艾宾浩斯遗忘曲线衰减机制
- 记忆增强问答
- 知识图谱实体关系

### 改进
- 辅导智能体集成记忆增强
- 情景记忆按重要性衰减

---

## v7.0.0 (2026-04)

### 新增
- 多智能体协同架构（6 个专业智能体）
- 事件驱动消息总线（14 种消息类型）
- 协商决策机制
- 7 种学习资源类型
- 9 维度学生画像
- 混合检索系统（KNN + ANN + RRF）
- 11 种高级检索策略（2023-2026 前沿算法）
- 防幻觉三重保障
- 流式输出（SSE）
- 多数据库架构（9 个独立 SQLite）
- 单页面导航系统
