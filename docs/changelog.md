# 版本变更日志

## v8.0.0 (2026-07-17) — 检索系统全面升级 + 协同学习

### 新增 — P0 高收益优化
- **语义缓存** (`SemanticCache`)
  - 基于向量相似度的缓存匹配（阈值 0.92）
  - 相似问题直接复用缓存结果，减少 API 调用
  - 集成到 `hybrid_search()` 方法
- **检索评测指标** (`services/retrieval_evaluator.py`)
  - NDCG@k、MRR、Recall@k 三个标准指标
  - 支持创建评测数据集、标注查询、运行评测、策略对比
  - SQLite 持久化评测结果
- **Multi-Hop 可视化**
  - 推理链路展示（跳数标签 + 关系 + 置信度）
  - Mermaid 知识关联图谱渲染
  - 新增 `POST /api/agent/multi-hop-search` 端点
- **FAISS 索引升级**
  - 按文档量自动选择：<10K → FlatIP，10K-100K → IVFFlat，>100K → HNSW
  - `_maybe_upgrade_index()` 自动升级
  - `index_type` / `index_info` 属性监控

### 新增 — P1 体验提升
- **Self-RAG 检索决策** (`services/self_rag.py`)
  - `retrieval_gate()`: 前置判断是否需要检索
  - `strategy_router()`: 按题型自动选择策略
  - `result_verifier()`: 后置校验检索质量
- **ReAct 推理-检索交替** (`multi_hop_retriever.react_retrieve()`)
  - 推理→检索→推理 交替执行
  - LLM 判断信息充分性，精准检索
  - 适配推导题、多步骤答疑
- **智能路由**（按题型自动分发）
  - 代码题 → hybrid，概念题 → HyDE，推导题 → ReAct，应用题 → Graph
- **Agent 协作实时可视化**
  - 状态追踪器 + SSE 推送
  - 事件类型：task_start / agent_thinking / task_complete
  - `GET /api/agent/agent-status/{session_id}` 轮询
  - `GET /api/agent/agent-status-stream/{session_id}` SSE 流

### 新增 — P2 锦上添花
- **命题级分块** (`document_parser.split_into_propositions()`)
  - LLM 将段落拆解为独立事实命题
  - 原子事实独立向量化，检索精度更高
- **知识图谱自动构建** (`multi_hop_retriever.build_knowledge_graph()`)
  - LLM-based NER + 关系抽取
  - 规则 + LLM 结果合并去重
  - 文档上传时异步构建
- **Reflector 增强**
  - `pairwise_compare()`: 多候选答案两两比较
  - `generate_and_select_best()`: 生成 2-4 条候选 + 选最优
- **协同学习小组** (`services/collaboration_service.py`)
  - 5 张新表：study_groups, group_members, shared_resources, learning_activities_feed, peer_reviews
  - 12 个 API 端点：小组管理、资源共享、学习动态、互评、进度对比
- **增强视觉识别** (`services/enhanced_vision_service.py`)
  - 图像预处理（自动旋转/放大/对比度/锐度/去噪）
  - 多策略 OCR 融合（通用 OCR + 结构化提取 + 专用 prompt）
  - 课表/错题/成绩单专用识别接口
  - 置信度评估 + 自动降级

### 变更
- `services/tutor_agent.py` — 集成 Self-RAG 三层决策
- `services/advanced_retrieval_service.py` — 新增 `react` 策略
- `services/agent_coordinator.py` — 新增状态追踪和 SSE 推送
- `services/student_data_service.py` — 图像识别升级为增强视觉服务
- `backend/main.py` — 注册 collaboration_router

### 新增文件
- `services/self_rag.py` — Self-RAG 检索决策器
- `services/retrieval_evaluator.py` — 检索评测模块
- `services/enhanced_vision_service.py` — 增强视觉识别服务
- `services/collaboration_service.py` — 协同学习小组服务
- `data/collaboration_db.py` — 协同学习数据库操作
- `backend/api/collaboration.py` — 协同学习 API

## v7.5.1 (2026-07-16)

### 变更
- **Embedding 服务改造**：从 MiMo Embedding API 改为本地 TF-IDF + SVD 方案
  - 移除 `sentence-transformers` 依赖，新增 `jieba`、`scikit-learn` 依赖
  - 向量维度从固定 768 维改为动态计算（50-200 维）
  - 启动时自动加载教育领域语料库训练模型
  - 纯本地实现，无需外部 API 和网络下载
- **API Key 更新**：MiMo API Key 已更新
- **文档更新**：更新所有技术文档中的向量化说明

### 新增
- `data/corpus/education_corpus.txt` — 教育领域语料库（82条）
- `backend/main.py` — 启动时自动训练 embedding 模型

## v7.5.0 (2026-07)

### 新增
- 学习能力雷达图（6维度评估）
  - 首页工作台右侧边栏迷你版（200px）+ 「AI 评定」按钮
  - 学生画像页面顶部完整版（280px + 分数标签），自动同步 AI 评分
  - 6维度：知识基础、学习目标、记忆能力、自控力、专注度、学习深度
  - 两种评估模式：规则评估（默认）+ AI 评定（MiMo 综合分析）
  - 评分缓存：localStorage 24小时有效，两页面共享
  - 使用 Recharts RadarChart，紫色主题，domain [0,5]
- AI 画像评定
  - `POST /api/agent/evaluate-profile`：MiMo 综合分析画像+使用数据
  - 评定记录持久化到 `profile_evaluations` 表
  - 参考数据：资源数、活动数、记忆统计
- 新增数据库表：`profile_evaluations`（ai_memory.db）
  - 字段：user_id, 6维度分数, reasoning, resource_count, activity_count
  - 按用户和时间索引
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
- 工作台背景：使用 DashboardBackground 线条装饰（与 Hero 页一致）
- 雷达图统一：共享计算函数 `lib/radar.ts`，消除两页面评分不一致

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
