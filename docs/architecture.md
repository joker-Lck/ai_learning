# 系统架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层 (User Layer)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Web 前端  │ │ 移动 App  │ │ API 文档  │ │ 管理后台  │           │
│  │ Next.js   │ │ React     │ │ Swagger   │ │ —        │           │
│  └────┬─────┘ │ Native    │ └────┬─────┘ └────┬─────┘           │
│       │       └────┬─────┘      │             │                 │
├───────┴────────────┴────────────┴─────────────┴─────────────────┤
│                    ▼            ▼            ▼                   │
│              ┌─────────────────────────────┐                    │
│              │   FastAPI 后端 (REST + SSE)  │                    │
│              │   JWT 认证 + 限流 + 校验      │                    │
│              └──────────────┬──────────────┘                    │
├─────────────────────────────┼───────────────────────────────────┤
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              智能体协作层 (Agent Layer) — 6 个专业智能体     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ 协调器    │  │ 消息总线  │  │ 消息协议  │               │  │
│  │  └────┬─────┘  └────┬─────┘  └──────────┘               │  │
│  │  ┌────┴───┐   ┌─────┴────┐   ┌─────────┐   ┌─────────┐ │  │
│  │  │画像Agent│   │资源Agent │   │路径Agent │   │辅导Agent│ │  │
│  │  └────────┘   └──────────┘   └─────────┘   └─────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI 能力层 (AI Layer)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │  │
│  │  │ MiMo LLM      │  │ RAG 知识库    │  │ 内容安全服务   │  │  │
│  │  │ mimo-v2.5-pro  │  │ FAISS + FTS5 │  │ AC自动机+防幻觉│  │  │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              数据层 (Data Layer) — 9 个独立 SQLite 数据库   │  │
│  │  auth │ profiles │ resources │ paths │ tutor │ memory    │  │
│  │  assessments │ agents │ rag_knowledge                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 设计原则

| 原则 | 说明 |
|------|------|
| **分层解耦** | 四层分离，标准接口通信 |
| **智能体自治** | 每个 Agent 独立负责一个业务领域 |
| **事件驱动** | 消息总线异步通信，支持并行执行 |
| **降级容错** | 每层都有降级方案 |
| **数据访问层** | DAO 模式封装数据库操作，统一连接管理 |

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.2+ | Web 前端框架（App Router） |
| React | 18.3+ | UI 库 |
| TypeScript | 5.4+ | 类型安全 |
| Tailwind CSS | 3.4+ | 原子化 CSS |
| Framer Motion | 11.0+ | 动画 |
| Zustand | 4.5+ | 状态管理 |
| Mermaid | 11.15+ | 图表渲染 |
| Recharts | 2.12+ | 数据可视化 |

### 移动端

| 技术 | 版本 | 用途 |
|------|------|------|
| React Native | 0.76+ | 跨平台移动框架 |
| Expo | 52+ | 开发工具链 |
| NativeWind | 4.0+ | Tailwind CSS for RN |
| Victory Native | 41+ | 数据可视化 |
| React Native Reanimated | 3.16+ | 动画 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | 高性能 API 框架 |
| Python | 3.8+ | 后端运行环境 |
| SQLite | 3.50+ | 9 个独立数据库 |
| FAISS | 1.7+ | 向量检索 |
| MiMo AI | mimo-v2.5-pro | 大语言模型（文本推理、视觉理解、图片生成、语音合成） |
| TF-IDF + SVD | 本地实现 | 文本向量化（jieba分词 + TF-IDF + SVD降维，维度动态计算） |

## 扩展服务

| 服务 | 文件 | 说明 |
|------|------|------|
| Reflector | `services/reflector.py` | 反思验证器：答案质量评分 + 证据链检查 + 低分自动重生成 |
| Multi-Hop Retriever | `services/multi_hop_retriever.py` | 多跳推理检索：逻辑图 + 2-5跳探索 + 证据链验证 |
| Self-Learning | `services/self_learning_service.py` | 自学习闭环：反馈收集 → 经验筛选 → 数据增强 → RAG更新 |

## 前端可视化

### 学习能力雷达图

| 位置 | 组件 | 尺寸 | 说明 |
|------|------|------|------|
| 首页工作台右侧边栏 | `DashboardRadarChart` | 200px | 迷你版，3x2分数网格，带「AI 评定」按钮 |
| 学生画像页面顶部 | `ProfileRadarChart` | 280px | 完整版，带详细分数标签，自动同步 AI 评分 |

#### 两种评估模式

| 模式 | 触发 | 数据来源 | API |
|------|------|---------|-----|
| 规则评估 | 自动（默认） | 画像字段规则映射 | 无（前端计算） |
| AI 评定 | 用户点击按钮 | MiMo 综合分析画像+使用数据 | `POST /api/agent/evaluate-profile` |

#### 6 维度评分标准（1-5分）

| 维度 | 规则评估 | AI 评定 |
|------|---------|---------|
| 知识基础 | `knowledge_base.level` 映射 | 综合知识掌握程度+学习历史深度 |
| 学习目标 | `learning_goals` 数组长度 | 目标明确度+可执行性+匹配度 |
| 记忆能力 | `learning_history` 长度 | 记忆条数+保持率+遗忘曲线状态 |
| 自控力 | 偏好中含计划类关键词 | 学习频率+计划执行率+规律性 |
| 专注度 | `cognitive_style` 关键词 | 学习时长分布+单次深度 |
| 学习深度 | `interest_areas` 广度 | 兴趣广度+薄弱环节改善率 |

#### AI 评定数据流

```
用户点击「AI 评定」→ POST /api/agent/evaluate-profile
→ 后端收集画像+资源数+活动数+记忆统计
→ MiMo 综合评估 → 返回 6 维度分数+理由
→ 前端缓存 localStorage（24h）→ 保存 profile_evaluations 表
→ 画像页面自动同步（storage 事件监听）
```

#### 评判标准

- 1分：几乎无数据，初始状态
- 2分：少量数据，表现较弱
- 3分：中等水平（默认值）
- 4分：良好，数据充分
- 5分：优秀，数据丰富且稳定

技术栈：共享函数 `lib/radar.ts` + Recharts RadarChart + localStorage 缓存 + `profile_evaluations` 数据库表

## 企业级特性

| 特性 | 实现 |
|------|------|
| 测试 | 45个单元测试（pytest），覆盖 core/database/services |
| CI/CD | GitHub Actions（Lint + Test 3版本 + Type Check） |
| RBAC | 4级角色权限（admin>teacher>student>guest） |
| 配置 | pydantic-settings 环境隔离（dev/staging/prod） |
| 代码规范 | Ruff linter + pre-commit hooks |
| 依赖 | pyproject.toml（主依赖+dev依赖分离） |

## 多数据库架构

| 数据库 | 用途 | 核心表 |
|--------|------|--------|
| ai_auth | 认证 | users, sessions |
| ai_profiles | 画像 | student_profiles, course_schedules, grades, error_notes, study_plans |
| ai_resources | 资源 | learning_resources, safety_logs |
| ai_paths | 路径 | learning_paths, path_progress |
| ai_tutor | 辅导 | tutor_sessions, messages, knowledge_refs |
| ai_assessments | 评估 | assessments, dimensions, activities |
| ai_agents | 协作 | collaboration_logs, tasks |
| ai_rag_knowledge | 知识库 | documents, points, categories（FTS5） |
| ai_memory | 记忆 | 8 张记忆表 |
