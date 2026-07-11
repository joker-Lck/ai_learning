# 基于多智能体的个性化学习资源生成系统

> **基于多智能体协同架构的个性化学习资源生成系统**  
> 比赛精简版 — 聚焦核心赛事，突出技术创新

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://www.sqlite.org/)

---

## 目录

- [系统概述](#系统概述)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [技术架构](#技术架构)
- [数据库设计](#数据库设计)
- [功能模块](#功能模块)
- [API接口](#api接口)
- [创新亮点](#创新亮点)
- [核心算法：混合检索系统（KNN + ANN）](#核心算法混合检索系统knn--ann)
- [性能指标](#性能指标)
- [常见问题](#常见问题)

---

## 系统概述

本系统采用**多智能体协同架构**和**多数据库设计**，为高等教育学生提供**个性化学习资源生成**服务。

### 核心优势

- **对话式学生画像** — 自然语言构建 9 维度动态画像
- **多智能体协同** — 6 个专业智能体分工协作
- **7 种资源类型** — 文档/思维导图/题库/视频/动画/代码/阅读
- **多数据库架构** — 9 个独立 SQLite 数据库，功能隔离
- **防幻觉机制** — RAG 验证+事实核查+引用标注
- **流式输出** — SSE 实时推送生成进度
- **内容安全** — 敏感词过滤+学术规范检查

---

## 核心特性

### 1. 多智能体系统（6 个专业智能体）

| 智能体 | 职责 | 输出 |
|--------|------|------|
| **Profile Agent** | 学生画像构建 | 9 维度画像数据 |
| **Resource Agent** | 学习资源生成 | 7 种类型资源 |
| **Path Agent** | 学习路径规划 | 个性化学习路径 |
| **Tutor Agent** | 智能辅导答疑 | 多模态回答+记忆增强 |
| **Assessment Agent** | 学习效果评估 | 多维度评估报告 |
| **Coordinator Agent** | 协调器 | 任务分发与结果合并 |

### 2. 多数据库架构（9 个独立数据库）

| 数据库 | 用途 | 核心表 |
|--------|------|--------|
| **ai_auth** | 认证与用户管理 | users, sessions |
| **ai_profiles** | 学生画像存储 | student_profiles, course_schedules, student_grades, error_notes, study_plans |
| **ai_resources** | 学习资源管理 | learning_resources, resource_safety_logs |
| **ai_paths** | 学习路径规划 | learning_paths, path_progress |
| **ai_tutor** | 智能辅导对话 | tutor_sessions, tutor_messages, tutor_knowledge_refs |
| **ai_assessments** | 学习效果评估 | learning_assessments, assessment_dimensions, learning_activities |
| **ai_agents** | 智能体协作日志 | agent_collaboration_logs, agent_tasks |
| **ai_rag_knowledge** | RAG 知识库 | knowledge_documents, knowledge_points, document_categories |
| **ai_memory** | 记忆系统 | short_term_memory, episodic_memory, semantic_memory, entity_memory, entity_relations, memory_metadata, memory_conflicts, memory_access_log |

**总计**: 9 个数据库，30+ 张表

### 3. 7 种学习资源类型

1. **Document** — 文档资料
2. **Mindmap** — 思维导图
3. **Quiz** — 测验题目
4. **Video** — 视频讲解
5. **Animation** — 动画演示
6. **Code Case** — 代码案例
7. **Reading** — 阅读材料

### 4. 首页工作台

系统首页为**动态工作台**，所有数据从后端实时获取，与登录用户绑定：

| 区域 | 功能 | 数据来源 |
|------|------|---------|
| **顶部问候** | 显示用户名 + 累计学习天数/时长 | `GET /api/agent/dashboard/stats` |
| **统计卡片** | 学习记录/兴趣领域/生成资源/薄弱待补 | `GET /api/agent/get-profile` |
| **继续学习** | 最近生成的资源列表，点击直接预览 | `GET /api/agent/list-resources` |
| **最近生成** | 所有 AI 生成资源，支持弹窗预览 | `GET /api/agent/list-resources` |
| **今日建议** | 基于记忆系统的个性化推荐 | `GET /api/agent/learning-recommendations` |
| **快速开始** | AI问答/资源生成/学习评估/上传文档 | 模块入口 |
| **协同动态** | 智能体活动日志实时流 | `GET /api/agent/activity-logs` |

### 5. 9 维度学生画像

- **knowledge_base** — 知识基础
- **cognitive_style** — 认知风格（视觉/听觉/动觉）
- **learning_goals** — 学习目标
- **skill_level** — 技能水平（初级/中级/高级）
- **learning_preferences** — 学习偏好列表
- **strengths** — 优势列表
- **weaknesses** — 劣势列表
- **motivation** — 学习动机
- **major_and_grade** — 专业与年级

### 6. 无限长时记忆架构（集成在辅导智能体）

- **短期记忆** — Token 级上下文窗口，自动保存对话历史
- **情景记忆** — 对话事件和学习场景，按重要性衰减
- **语义记忆** — SPO 三元组事实知识，支持冲突检测与修正
- **实体记忆** — KV 画像存储 + 知识图谱关系
- **遗忘机制** — 基于艾宾浩斯遗忘曲线的智能衰减（R = e^(-t/S)）
- **冲突修正** — 自动检测事实矛盾，三种解决策略
- **记忆增强问答** — 自动检索相关记忆，构建增强上下文
- **集成架构** — 记忆功能直接集成在 TutorAgent 中，无需独立服务

### 7. 混合检索系统（ANN + KNN + RRF）

- **KNN 关键词检索** — SQLite FTS5 全文索引精确匹配专业术语
- **ANN 向量检索** — FAISS 余弦相似度语义匹配
- **RRF 融合排序** — Reciprocal Rank Fusion 统一排序
- **防幻觉机制** — RAG 优先检索 + 事实核查 + 引用标注

---

## 快速开始

### 环境要求

- Python 3.14
- Node.js 18+

### 快速配置（推荐）

```bash
# 一键配置环境（检查依赖、创建venv、安装包、初始化数据库）
setup.bat
```

### 手动配置

#### 步骤1: 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

### 步骤2: 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env，填写以下配置：
# - SPARK_APPID（必需，讯飞星火 APPID）
# - SPARK_API_KEY（必需，讯飞星火 API Key）
# - SPARK_API_SECRET（必需，讯飞星火 API Secret）
```

### 步骤3: 初始化数据库

```bash
# 多数据库架构 - 创建 9 个独立 SQLite 数据库
python scripts/init_databases_v7.2.py
```

**预期输出**:
```
✅ 数据库 'ai_auth' 创建成功!
✅ 数据库 'ai_profiles' 创建成功!
... (共 9 个数据库)
✅ 所有数据库初始化完成
```

### 步骤4: 创建管理员账户

```bash
python scripts/init_admin.py
```

默认账号: `admin / admin123`

### 步骤5: 启动服务

```bash
# 方式1: 使用启动脚本 (Windows)
启动.bat

# 方式2: 手动启动
# 终端1 - 后端
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 终端2 - 前端
cd frontend && npm run dev
```

### 步骤6: 访问系统

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

---

## 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 (Next.js 12)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pages Router + Tailwind CSS + Zustand + Framer Motion 6     │  │
│  │  单页应用 (SPA) · URL参数控制模块切换 · 无页面跳转        │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────────┤
│                    ▼  HTTP + SSE                                │
├─────────────────────────────┼───────────────────────────────────┤
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │              API层 (FastAPI)                              │  │
│  │  /api/auth/* (认证) · /api/agent/* (核心) · /api/stream/* │  │
│  │  JWT认证 + Pydantic校验 + 速率限制 + 自定义异常体系       │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────────┤
│                    ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         智能体协作层 (Agent Layer)                         │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ 协调器    │ │ 消息总线  │ │ 消息协议  │ │ 画像Agent │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │资源Agent │ │ 路径Agent │ │ 辅导Agent │ │评估Agent │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────────┤
│                    ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              AI 能力层 (AI Layer)                          │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐    │  │
│  │  │ 讯飞星火 LLM  │ │ RAG 知识库    │ │ 内容安全服务   │    │  │
│  │  │ spark-x 模型  │ │ FAISS+FTS5   │ │ AC自动机+防幻觉│    │  │
│  │  └──────────────┘ └──────────────┘ └───────────────┘    │  │
│  └──────────────────────────┬───────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────────┤
│                    ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           数据层 (SQLite) — 9个独立数据库                   │  │
│  │  auth │ profiles │ resources │ paths │ tutor │ memory    │  │
│  │  assessments │ agents │ rag_knowledge                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

**前端**:
- Next.js 12 (Pages Router + React 17)
- TypeScript (类型安全)
- Tailwind CSS (样式)
- Framer Motion 6 (动画)
- Zustand (状态管理)
- Mermaid (图表渲染)
- Recharts (数据可视化)
- react-markdown + KaTeX (Markdown + 数学公式)

**后端**:
- FastAPI (高性能API)
- Python 3.14
- SQLite (9 个独立数据库)
- 讯飞星火 API (大模型 spark-x)
- FAISS (向量检索)
- SSE (流式输出)

**AI 能力**:
- 多智能体协同（事件驱动消息总线 + 14 种消息类型）
- RAG 检索增强（11 种策略路由）
- 向量相似度检索（FAISS IndexFlatIP）
- 防幻觉机制（RAG 验证 + 事实核查 + 引用标注 + 交叉验证）
- Spark-X 推理模型
- 图片生成 (TTI API)
- OCR 文字识别（手写识别 + 通用文档识别）
- 语音合成 (TTS API)
- 图片理解 (Vision API)

---

## 数据库设计

### 多数据库架构理念

**为什么需要多数据库？**
- 功能隔离：避免数据耦合
- 性能优化：针对性优化不同数据类型
- 易于维护：模块化设计
- 高可用性：故障隔离
- 灵活扩展：新增功能不影响现有系统

### 数据库关系图

```
ai_rag_knowledge (核心知识库)
  ↕ 被各模块依赖

ai_profiles (学生画像)
  ↕ 被各模块依赖

ai_auth (认证) → 基础服务

ai_resources, ai_paths, ai_tutor, ai_assessments
  → 核心功能模块

ai_agents (协作日志) → 记录层

ai_memory (记忆系统) → 辅导增强
```

### 核心表结构

#### 1. ai_profiles.student_profiles (学生画像)

```sql
CREATE TABLE student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    profile_data TEXT NOT NULL,    -- JSON: 9维度画像
    conversation_log TEXT,         -- JSON: 对话历史
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. ai_resources.learning_resources (学习资源)

```sql
CREATE TABLE learning_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    resource_type TEXT NOT NULL,   -- document/mindmap/quiz/video/animation/code_case/reading
    subject TEXT,
    topic TEXT,
    difficulty_level TEXT,         -- beginner/intermediate/advanced
    content_data TEXT NOT NULL,    -- JSON
    generated_by_agent TEXT,
    tags TEXT,                     -- JSON
    usage_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0,
    duration_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. ai_rag_knowledge.knowledge_documents (RAG 知识库)

```sql
CREATE TABLE knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    document_data TEXT,            -- JSON: 文档数据+embedding(768维)
    embedding TEXT,                -- JSON: 向量嵌入
    uploaded_by INTEGER,
    usage_count INTEGER DEFAULT 0,
    is_public INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 全文检索虚拟表
CREATE VIRTUAL TABLE knowledge_documents_fts USING fts5(title, subject);
```

#### 4. ai_memory (记忆系统)

```sql
-- 短期记忆
CREATE TABLE short_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,            -- user/assistant/system
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0
);

-- 语义记忆：SPO 三元组事实知识
CREATE TABLE semantic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fact_type TEXT,                -- preference/knowledge/skill/habit/goal
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL DEFAULT 0.8,
    UNIQUE(user_id, subject, predicate, object)
);

-- 实体记忆：KV 画像 + 知识图谱
CREATE TABLE entity_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entity_type TEXT,              -- person/concept/skill/course/tool/organization
    entity_name TEXT NOT NULL,
    entity_alias TEXT,
    attributes TEXT,               -- JSON
    description TEXT,
    importance REAL DEFAULT 0.5,
    UNIQUE(user_id, entity_type, entity_name)
);

-- 记忆元数据：遗忘机制控制
CREATE TABLE memory_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_type TEXT,              -- short_term/episodic/semantic/entity/relation
    memory_id INTEGER NOT NULL,
    importance REAL DEFAULT 0.5,
    decay_rate REAL DEFAULT 0.1,
    access_count INTEGER DEFAULT 0,
    is_forgotten INTEGER DEFAULT 0
);
```

---

## 功能模块

### 单页面导航系统

**设计理念**：三屏滑动切换，无页面跳转，通过 scroll-snap 实现全屏页面切换。

#### 三屏布局

```
Section 0: Hero 首页         → 品牌展示 + 统计概览
Section 1: 工作台            → 用户数据仪表盘（内部可滚动）
Section 2: 功能选择/模块内容  → 6大模块入口或具体模块内容
```

#### 工作台页面

工作台是登录后的默认首页，所有数据动态获取：
- 顶部：问候语 + 用户名 + 学习天数/时长统计
- 统计卡片：学习记录/兴趣领域/生成资源/薄弱待补
- 继续学习：最近资源列表，点击弹窗预览
- 今日建议：基于记忆系统的个性化推荐
- 协同动态：智能体活动日志

#### 模块导航

```
学生画像   → URL参数 ?module=profile
资源生成   → URL参数 ?module=resources
学习路径   → URL参数 ?module=path
智能辅导   → URL参数 ?module=tutor
效果评估   → URL参数 ?module=assessment
知识库     → URL参数 ?module=rag
```

---

### 1. 学生画像模块

**功能**：对话式构建 9 维度学生画像

**使用流程**：
1. 点击侧边栏"学生画像"
2. 在对话框中输入个人信息
3. AI 分析并构建画像
4. 查看 9 维度画像结果

**数据管理**（画像模块内 Tab 切换）：
- **课程表**：手动录入/编辑/删除 + 文件导入（PDF/Word/Excel/PPT/图片），AI 自动识别
- **成绩管理**：录入 + 文件导入，按学期统计
- **错题本**：添加/标记掌握/删除 + 文件导入
- **学习计划**：AI 生成 + 手动创建

文件导入特性：
- AI 优先校验内容类型（课表/成绩/错题），不匹配直接报错
- AI 识别期间切换 Tab 不中断识别进程
- 识别失败自动展开手动添加表单
- 支持扫描版 PDF 识别（通过 PyMuPDF 转图片后 OCR）
- 图片文件优先使用 OCR 提取文字，失败则降级到多模态视觉识别

---

### 2. 资源生成模块

**功能**：根据学生画像生成个性化学习资源

**使用流程**：
1. 选择学科和主题
2. 选择资源类型（可多选）
3. 设置难度级别
4. 点击生成，等待 AI 生成

---

### 3. 学习路径模块

**功能**：规划个性化学习路径

**使用流程**：
1. 输入学习目标
2. AI 分析当前水平
3. 生成学习路径（含多个步骤）
4. 跟踪学习进度

---

### 4. 智能辅导模块

**功能**：智能问答，多模态响应，记忆增强

**使用流程**：
1. 进入辅导模块，AI 自动发送欢迎引导消息
2. 选择学科
3. 输入问题
4. AI 检索 RAG 知识库 + 用户记忆上下文
5. 生成回答（含图解、示例）

**响应特点**：
- 文字解释
- Mermaid 图解
- 代码示例
- 知识引用溯源

---

### 5. 效果评估模块

**功能**：多维度学习效果评估

**使用流程**：
1. 点击"生成评估报告"
2. AI 分析学习历史
3. 生成多维度评估
4. 查看改进建议

---

### 6. 知识库模块

**功能**：文档上传 + KNN+ANN+RRF 混合检索

**使用流程**：
1. 点击侧边栏"知识库"
2. 拖拽或选择文件上传（支持 TXT/MD/PDF/DOCX/PPTX/XLSX/CSV，单文件最大 20MB）
3. 可选填写学科标签
4. AI 自动解析文档、提取知识点、生成摘要
5. 文档入库后通过混合检索引擎检索

**检索能力**：
- **KNN 关键词路径**：SQLite FTS5 全文索引精确匹配专业术语
- **ANN 向量路径**：FAISS 语义匹配相近表达
- **RRF 融合排序**：两条路径结果统一排序
- **高级策略**：HyDE / Multi-Query / RAG-Fusion / Contextual / Graph-Enhanced

---

## API接口

### 学习智能体API（核心）

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/agent/build-profile` | POST | 构建学生画像 |
| `/api/agent/generate-resources` | POST | 生成学习资源 |
| `/api/agent/plan-path` | POST | 规划学习路径 |
| `/api/agent/tutor` | POST | 智能辅导答疑 |
| `/api/agent/assess` | POST | 学习效果评估 |
| `/api/agent/list-resources` | GET | 获取资源列表（按用户过滤） |
| `/api/agent/save-resource` | POST | 保存资源到数据库 |
| `/api/agent/dashboard/stats` | GET | 工作台统计数据 |
| `/api/agent/activity-logs` | GET/POST | 活动日志查询/记录 |
| `/api/agent/learning-recommendations` | GET | 个性化学习推荐 |
| `/api/agent/advanced-search` | POST | 高级检索（11 种策略） |

### 流式输出与安全API（核心）

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/stream/generate-resource/{type}` | GET | 流式生成资源(SSE) |
| `/api/stream/progress/{task_id}` | GET | 查询任务进度 |
| `/api/stream/check-content-safety` | POST | 内容安全检查 |
| `/api/stream/verify-fact` | POST | 事实验证 |
| `/api/stream/tutor` | POST | 流式智能辅导(SSE) |

### 认证API

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/guest` | POST | 游客模式 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/auth/change-password` | POST | 修改密码 |

**完整API文档**: http://localhost:8000/docs

---

## 创新亮点

### 1. 真正的多智能体架构

- 6 个专业智能体分工协作
- 事件驱动消息总线（14 种消息类型）
- 协商决策机制（Propose/Accept/Reject/Counter）
- 非单一 AI 模型调用

### 2. 7 种资源类型全覆盖

- 超出比赛要求的 4 种
- 满足全方位学习需求
- 个性化生成

### 3. 防幻觉三重保障

- RAG 优先策略
- 事实核查机制
- 引用标注溯源

### 4. 流式输出体验优化

- SSE 实时进度推送
- 5 阶段可视化
- 避免白屏等待

### 5. 内容安全保障

- 敏感词检测拦截（AC 自动机，127 条敏感词）
- 学术规范检查
- 符合教育场景要求

### 6. 多数据库架构创新

- 9 个独立 SQLite 数据库
- 功能完全隔离
- RAG 知识库专业化
- 无需外部数据库服务

### 7. 单页面导航系统

- 保留导航菜单
- 无页面跳转
- URL 参数控制
- 状态保持

### 8. 2023-2026 前沿检索算法

- HyDE 假设性文档嵌入（Gao et al., 2023）
- Multi-Query 多查询检索（LangChain, 2023）
- RAG-Fusion + RRF 查询融合（Raudaschl, 2023）
- Contextual Retrieval 上下文检索（Anthropic, 2024）
- Graph-Enhanced RAG 图谱增强检索（Microsoft, 2024）

### 9. 全链路性能优化

- 后端：numpy 向量化计算、AC 自动机敏感词匹配、LRU 缓存
- 前端：React.memo、代码分割、CSS contain、will-change
- 检索：向量语义检索降级策略

---

## 核心算法：混合检索系统（KNN + ANN）

本系统在 RAG 知识库检索中设计了一套**混合检索引擎**，融合向量语义检索（ANN）与关键词精确匹配（KNN），配合三级回退策略，实现了高可用、高精度的知识检索能力。

**涉及源文件**：

| 文件 | 核心类/函数 | 说明 |
|------|-----------|------|
| `data/rag_knowledge_base.py` | `VectorIndexManager`, `RAGKnowledgeBase` | FAISS 向量索引 + 混合检索 |
| `data/embedding_service.py` | `EmbeddingService` | Kimi Moonshot Embedding API（768 维） |
| `data/qa_db_operations.py` | `QADatabase.search_similar_questions` | QA 相似问题检索 |
| `services/content_safety_service.py` | `AntiHallucinationService` | 防幻觉验证 |
| `services/advanced_retrieval_service.py` | `AdvancedRetrievalService` | 11 种高级检索策略 |

### 算法架构总览

```
用户查询
   │
   ├── KNN 关键词路径 ──→ SQLite FTS5 ──→ FTS5 查询 ──→ Top-K 结果
   │                       (专业术语精确匹配)
   │
   ├── ANN 向量路径 ──→ Embedding(768维) ──→ FAISS ANN 检索 ──→ Top-K 结果
   │                                          │
   │                                   三级回退策略
   │                                   ┌──────────────┐
   │                                   │              │
   │                             索引已就绪    索引未构建
   │                                   │       自动构建
   │                                   │              │
   │                                   ▼              ▼
   │                             FAISS 搜索    惰性构建后搜索
   │                                   │
   │                                   │ FAISS 不可用
   │                                   ▼
   │                             暴力余弦回退
   │                             (numpy 向量化)
   │
   └───────────────────────┬───────────────────────────────┐
                           │                               │
                           ▼                               │
              ┌───── RRF 融合排序 ─────────────────────┐   │
              │ RRF(d)=Σ1/(k+rank)                     │   │
              │ 去重 + Top-K 截断                       │   │
              └───────────────────────────────────────┘   │
                           │                               │
                           ▼                               │
                 混合检索结果（基座）                       │
                           │                               │
              ┌────────────┼────────────┐                 │
              ▼            ▼            ▼                 │
           HyDE       RAG-Fusion   Graph-Enhanced         │
           Multi-Query Contextual  策略路由(smart_search)  │
```

### 1. 文本向量化（Embedding Service）

**源文件**: `data/embedding_service.py` → `EmbeddingService` 类

#### 技术参数

| 参数 | 值 | 说明 |
|------|------|------|
| **API** | Kimi Moonshot Embedding API | `base_url: https://api.moonshot.cn/v1` |
| **向量维度** | `768` 维 | 空文本返回 `[0.0] * 768` 零向量 |
| **文本截断** | `8000` 字符 | 超长文本自动截断，防止 API 超时 |
| **鉴权方式** | API Key | Kimi Moonshot API Key |

### 2. ANN 近似最近邻检索（FAISS 向量索引）

**源文件**: `data/rag_knowledge_base.py` → `VectorIndexManager` 类

#### 技术方案

| 项目 | 实现 |
|------|------|
| **索引类型** | `faiss.IndexFlatIP`（Flat Inner Product） |
| **相似度原理** | L2 归一化后内积 **等价于** 余弦相似度 |
| **搜索复杂度** | O(n·d) 精确线性扫描 |
| **持久化路径** | `data/faiss_index/knowledge.index`（FAISS 二进制）+ `data/faiss_index/doc_ids.json`（ID 映射） |
| **并发安全** | `threading.Lock` 保护所有索引读写操作 |
| **向量维度** | 768（与Kimi Embedding 对齐） |

### 3. 三级回退检索策略

**源文件**: `data/rag_knowledge_base.py` → `search_documents_by_vector`

| 回退级别 | 触发条件 | 检索方式 | 响应时间 |
|---------|---------|---------|---------|
| **L1** | `vector_index.is_ready == True` | FAISS `IndexFlatIP` 内积搜索 | ~5ms |
| **L2** | `_faiss_available == True` 但索引为空 | `_build_faiss_index()` 从 DB 加载 → FAISS 搜索 | ~500ms（首次），后续 ~5ms |
| **L3** | `_faiss_available == False` 或构建失败 | `_brute_force_vector_search` 遍历计算余弦相似度 | ~100ms |

### 4. 高级检索方法（2023-2026 新型算法）

**源文件**: `services/advanced_retrieval_service.py`

系统实现了 11 种检索策略，通过 `smart_search()` 统一入口按策略路由：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `auto` | 自动选择（短查询用 HyDE，长查询用 RAG-Fusion） | 默认 |
| `knn` | KNN 关键词检索（SQLite FTS5） | 专业术语、公式 |
| `ann` | ANN 向量检索（FAISS 语义匹配） | 模糊语义查询 |
| `hybrid` | KNN + ANN + RRF 混合（基座策略） | 通用推荐 |
| `hyde` | 假设性文档嵌入（2023） | 短查询、概念性问题 |
| `multi_query` | 多查询检索（2023） | 提高召回率 |
| `rag_fusion` | RAG-Fusion + RRF（2023） | 通用推荐 |
| `contextual` | 上下文精排（2024） | 高精度场景 |
| `graph` | 图谱增强检索（2024） | 有图谱数据时 |
| `hybrid_advl` | 基座 + HyDE + RAG-Fusion 三路 RRF | 平衡速度与精度 |
| `ensemble` | 全部 6 种方法取并集，RRF 融合 | 最全面 |

### 5. 防幻觉 RAG 交叉验证

**源文件**: `services/content_safety_service.py` → `AntiHallucinationService`

- **关键实体提取 + RAG 验证**：提取声明中的关键实体，在知识库上下文中逐一查找，计算置信度
- **交叉验证 + 文本相似度**：将主回答与多个替代来源逐一比较，使用 Jaccard 文本相似度计算一致性
- **可信度阈值**: 0.7（置信度 < 0.7 标记为"可能存在幻觉"）
- **一致性阈值**: 0.6（一致性 < 0.6 标记为不一致）

### 6. 问答历史相似度检索

**源文件**: `data/qa_db_operations.py` → `search_similar_questions`

在智能辅导场景中，系统会先用 KNN 检索历史相似问题，命中则直接返回已有回答，避免重复调用大模型。

---

## 性能指标

| 指标 | 数值 |
|-----|------|
| 画像构建 | <2秒 |
| 资源生成 | 3-90秒 |
| SSE延迟 | <200ms |
| 内容安全检查 | <100ms |
| API响应(P95) | <2秒 |
| RAG检索响应 | ~5ms（FAISS 就绪时） |

---

## 企业级特性

### 安全

| 特性 | 说明 |
|------|------|
| JWT 认证 | HS256 签名，24h 有效期，启动时强制校验密钥 |
| 速率限制 | 全局 120次/分钟，登录 10次/分钟，注册 5次/分钟 |
| 安全头 | X-Content-Type-Options, X-Frame-Options, HSTS, CSP |
| CORS | 环境变量配置白名单 |
| 输入校验 | Pydantic 模型自动校验 |
| SQL 注入防护 | 全部使用参数化查询 |
| 自定义异常 | 8 种业务异常类，分层异常处理 |

### 可观测性

| 特性 | 说明 |
|------|------|
| 结构化日志 | JSON 格式，支持日志轮转（10MB/文件，保留 30 天） |
| 请求追踪 | 每个请求唯一 ID（X-Request-ID），全链路追踪 |
| 耗时统计 | X-Response-Time 响应头 |
| 健康检查 | `/api/health` 返回各依赖状态（SQLite/FAISS） |

### 容器化

| 特性 | 说明 |
|------|------|
| Docker | 前后端独立镜像，非 root 用户运行 |
| docker-compose | 一键启动（后端 + 前端 + SQLite） |
| 健康检查 | 容器级别健康检查，自动重启 |

### 打包与分发

系统支持使用 PyInstaller + NSIS 打包为 Windows 安装程序：

```bash
# 一键构建
python build.py

# 编译 NSIS 安装程序
makensis installer.nsi
```

生成文件：
- `AI学习智能体_Setup.exe` — 完整安装程序
- `dist/AI学习智能体/` — 免安装版本

---

## 项目结构

```
项目根目录
├── backend/                  # 后端API
│   ├── api/
│   │   ├── agent.py          # 多智能体API
│   │   ├── stream.py         # 流式输出
│   │   └── auth.py           # 认证API
│   ├── main.py               # 应用入口
│   ├── dependencies.py       # JWT认证、权限校验
│   ├── exceptions.py         # 自定义异常体系
│   └── schemas/              # Pydantic 模型
│
├── services/                 # 业务逻辑
│   ├── agent_coordinator.py  # 协调智能体
│   ├── profile_agent.py      # 画像智能体
│   ├── resource_agent.py     # 资源智能体
│   ├── path_agent.py         # 路径智能体
│   ├── tutor_agent.py        # 辅导智能体（集成记忆增强）
│   ├── assessment_agent.py   # 评估智能体
│   ├── memory_service.py     # 无限长时记忆架构
│   ├── advanced_retrieval_service.py  # 高级检索（11种策略）
│   ├── content_safety_service.py      # 内容安全（AC自动机）
│   └── streaming_service.py  # 流式输出
│
├── data/                     # 数据访问
│   ├── rag_knowledge_base.py # RAG知识库（FAISS+LRU缓存）
│   ├── embedding_service.py  # 向量化服务（Kimi 768维）
│   ├── db_operations.py      # 数据库操作
│   ├── dao.py                # DAO层
│   ├── config.py             # 多数据库配置
│   └── databases/            # 9个 SQLite 数据库文件
│
├── core/                     # 核心工具
│   ├── logger.py             # 结构化日志
│   ├── json_utils.py         # 容错JSON解析
│   └── prompts.py            # Prompt模板
│
├── frontend/                 # 前端应用
│   ├── components/
│   │   ├── shared/           # 共享组件
│   │   └── modules/          # 6大功能模块
│   ├── lib/
│   │   ├── api.ts            # API客户端（重试+超时）
│   │   └── hooks.ts          # 防抖/节流hooks
│   ├── middleware.ts          # 安全头
│   └── stores/index.ts       # Zustand状态管理
│
├── scripts/                  # 初始化脚本
├── config/                   # 配置文件
│   └── sensitive_words.json  # 敏感词库（127条）
├── Dockerfile                # 后端容器化
├── docker-compose.yml        # 多服务编排
├── .env.example              # 环境变量模板
└── README.md
```

---

## 常见问题

### Q1: 如何体现"多智能体"？

**A**: 系统有 6 个专业智能体（画像/资源/路径/辅导/评估/协调），通过事件驱动消息总线分工协作，不是单一 AI 调用。

### Q2: 如何保证内容准确性？

**A**: 三层防护: RAG优先检索 → 事实核查验证 → 引用标注溯源。

### Q3: 流式输出如何实现？

**A**: 使用 SSE (Server-Sent Events)，5 个阶段实时推送进度，前端 EventSource 接收。

### Q4: 与传统课件生成有什么区别？

**A**: 传统课件是固定 PPT，我们基于画像个性化生成 7 种资源类型，动态调整难度。

### Q5: 为什么需要多数据库？

**A**: 
- 功能隔离，避免数据耦合
- 性能优化，针对性优化不同数据类型
- 易于维护，模块化设计
- 高可用，故障隔离
- RAG 知识库专业化

### Q6: 导航为什么跳转页面？

**A**: 
- 用户体验更流畅
- 状态保持不变
- 加载速度更快
- 通过 URL 参数实现模块切换

### Q7: 如何备份数据库？

**A**: 
```bash
# SQLite 数据库文件位于 data/databases/ 目录
# 直接复制 .db 文件即可备份
copy data\databases\*.db backup\

# 单独备份 RAG 知识库
copy data\databases\ai_rag_knowledge.db backup\
```

### Q8: 如何导入 RAG 知识库数据？

**A**:
```bash
python scripts/init_rag_db.py
```

---

## 技术支持

- **API文档**: http://localhost:8000/docs
- **问题反馈**: 查看 `logs/` 目录日志
