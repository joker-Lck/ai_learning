# 基于多智能体的个性化学习资源生成系统

<p align="center">
  <b>AI-Powered Personalized Learning Resource Generation System</b><br>
  基于 MiMo 大模型 · 6 智能体协同 · 7 种资源类型 · 9 个独立数据库 · RAG 混合检索
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/React_Native-0.76+-61DAFB?logo=react&logoColor=white" alt="React Native">
  <img src="https://img.shields.io/badge/MiMo-v2.5-purple" alt="MiMo">
  <img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 目录

- [项目简介](#项目简介)
- [系统特性](#系统特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [功能模块详解](#功能模块详解)
- [多智能体系统](#多智能体系统)
- [MiMo 大模型集成](#mimo-大模型集成)
- [混合检索系统](#混合检索系统)
- [记忆系统](#记忆系统)
- [数据库设计](#数据库设计)
- [API 接口](#api-接口)
- [移动端 App](#移动端-app)
- [安全机制](#安全机制)
- [部署指南](#部署指南)
- [项目结构](#项目结构)
- [性能指标](#性能指标)
- [版本变更日志](#版本变更日志)
- [文档导航](#文档导航)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 项目简介

本系统是一个面向高等教育场景的**个性化学习资源生成平台**，采用**多智能体协同架构**，基于 **MiMo 大模型** 驱动，为学生提供智能化的学习支持服务。

### 解决的核心问题

| 传统学习痛点 | 本系统解决方案 |
|-------------|---------------|
| 学习资源千篇一律 | 基于 9 维度画像个性化生成 |
| 资源类型单一（仅 PPT/文档） | 7 种资源类型全覆盖 |
| 缺乏个性化学习路径 | AI 分析当前水平，规划最优路径 |
| 答疑依赖教师时间 | 24/7 智能辅导 + 记忆增强 |
| 学习效果难以量化 | 多维度评估报告 + 可视化 |
| AI 回答存在幻觉 | RAG + 事实核查 + 引用溯源三重防护 |

### 核心数据

| 指标 | 数值 |
|------|------|
| 专业智能体 | 6 个 |
| 学习资源类型 | 7 种 |
| 学生画像维度 | 9 个 |
| 独立数据库 | 9 个 |
| 数据库表 | 30+ 张 |
| 检索策略 | 11 种 |
| 消息类型 | 14 种 |
| 敏感词库 | 127 条 |

---

## 系统特性

### MiMo 大模型全能力接入

| 能力 | 模型标识 | 应用场景 |
|------|---------|---------|
| 文本推理 | `mimo-v2.5-pro` | 主力模型：对话、推理、代码生成、数学推导 |
| 视觉理解 | `mimo-v2.5` | 图片识别、OCR 文字提取、图表理解、手写识别 |
| 图片生成 | `mimo-image` | 教学示意图、知识点图解、概念可视化 |
| 语音合成 | `mimo-tts` | 文字转语音、音频讲解生成 |
| 文本向量化 | `mimo-embedding` | 768 维向量嵌入，驱动 RAG 语义检索 |

### 多智能体协同架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Coordinator │    │  消息总线    │    │  消息协议    │
│   协调器     │◄──►│  MessageBus │◄──►│  14种类型    │
└──────┬──────┘    └─────────────┘    └─────────────┘
       │
  ┌────┴────────────────────────────────────────────┐
  │                                                 │
  ▼              ▼              ▼              ▼     ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Profile │  │Resource│  │  Path  │  │ Tutor  │  │Assess- │
│ Agent  │  │ Agent  │  │ Agent  │  │ Agent  │  │  ment  │
│ 画像师 │  │ 讲师   │  │ 导师   │  │ 辅导员 │  │ 评估师 │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

### 7 种学习资源类型

| # | 类型 | 标识 | 说明 |
|---|------|------|------|
| 1 | 文档资料 | `document` | 结构化学习文档，含 Markdown 格式 |
| 2 | 思维导图 | `mindmap` | Mermaid.js 渲染的知识结构图 |
| 3 | 测验题目 | `quiz` | 选择题/填空题/判断题，含解析 |
| 4 | 视频讲解 | `video` | 多场景教学视频脚本 |
| 5 | 动画演示 | `animation` | SVG + CSS 交互动画 |
| 6 | 代码案例 | `code_case` | 带注释的代码示例 |
| 7 | 阅读材料 | `reading` | 扩展阅读与参考资料 |

### 9 维度学生画像

| 维度 | 字段 | 说明 |
|------|------|------|
| 知识基础 | `knowledge_base` | 当前掌握的知识体系 |
| 认知风格 | `cognitive_style` | 视觉型/听觉型/动觉型 |
| 学习目标 | `learning_goals` | 短期与长期学习目标 |
| 技能水平 | `skill_level` | 初级/中级/高级 |
| 学习偏好 | `learning_preferences` | 偏好的学习方式列表 |
| 优势领域 | `strengths` | 擅长的学科/技能 |
| 薄弱环节 | `weaknesses` | 需要加强的领域 |
| 学习动机 | `motivation` | 内在/外在学习驱动力 |
| 专业年级 | `major_and_grade` | 所学专业与当前年级 |

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户层 (User Layer)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Web 前端     │  │  移动端 App   │  │  API 文档     │              │
│  │  Next.js 14   │  │  React Native │  │  Swagger UI   │              │
│  │  TypeScript   │  │  Expo 52      │  │  /docs        │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
├─────────┴──────────────────┴──────────────────┴─────────────────────┤
│                              │ HTTP + SSE                            │
│                              ▼                                       │
├─────────────────────────────────────────────────────────────────────┤
│                         API 层 (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  /api/auth/*   认证授权  │  /api/agent/*  核心业务           │    │
│  │  /api/stream/* 流式输出  │  /api/health   健康检查           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  JWT认证 + Pydantic校验 + 速率限制 + 8种自定义异常 + 安全头          │
├────────────────────────────────────┬────────────────────────────────┤
│                                     │                                │
│                                     ▼                                │
├─────────────────────────────────────────────────────────────────────┤
│                    智能体协作层 (Agent Layer)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ 协调器    │ │ 画像Agent │ │资源Agent │ │ 路径Agent │ │ 辅导Agent │ │
│  │Coordinator│ │ Profile  │ │ Resource │ │  Path    │ │  Tutor   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────────────┐ ┌──────────────────────────────┐│
│  │评估Agent │ │ 事件驱动消息总线  │ │ 协商决策(Propose/Accept/...) ││
│  │Assessment│ │ 14种消息类型      │ │                              ││
│  └──────────┘ └──────────────────┘ └──────────────────────────────┘│
├────────────────────────────────────┬────────────────────────────────┤
│                                     │                                │
│                                     ▼                                │
├─────────────────────────────────────────────────────────────────────┤
│                      AI 能力层 (MiMo AI Layer)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐│
│  │ MiMo-v2.5-pro│ │ MiMo-v2.5    │ │ MiMo-image   │ │ MiMo-tts   ││
│  │ 文本推理      │ │ 视觉理解     │ │ 图片生成      │ │ 语音合成   ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │mimo-embedding│ │ RAG 知识库    │ │ 内容安全服务  │               │
│  │ 768维向量化   │ │ FAISS+FTS5   │ │ AC自动机      │               │
│  └──────────────┘ └──────────────┘ └──────────────┘               │
├────────────────────────────────────┬────────────────────────────────┤
│                                     │                                │
│                                     ▼                                │
├─────────────────────────────────────────────────────────────────────┤
│                   数据层 (Data Layer) — 9 个独立 SQLite               │
│  ┌──────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌────────┐ │
│  │ auth │ │ profiles │ │ resources│ │ paths│ │ tutor│ │ memory │ │
│  └──────┘ └──────────┘ └──────────┘ └──────┘ └──────┘ └────────┘ │
│  ┌──────────────┐ ┌──────────┐ ┌───────────────┐                   │
│  │ assessments  │ │  agents  │ │ rag_knowledge │                   │
│  └──────────────┘ └──────────┘ └───────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 技术栈明细

**前端 (Web)**

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.2+ | Web 前端框架（App Router） |
| React | 18.3+ | UI 组件库 |
| TypeScript | 5.4+ | 静态类型检查 |
| Tailwind CSS | 3.4+ | 原子化 CSS 框架 |
| Framer Motion | 11.0+ | 声明式动画 |
| Zustand | 4.5+ | 轻量级状态管理 |
| Mermaid | 11.15+ | 图表/思维导图渲染 |
| Recharts | 2.12+ | 数据可视化 |
| react-markdown | 9.0+ | Markdown 渲染 |
| KaTeX | 1.0+ | 数学公式渲染 |

**前端 (移动端)**

| 技术 | 版本 | 用途 |
|------|------|------|
| React Native | 0.76+ | 跨平台移动框架 |
| Expo | 52+ | 开发工具链 |
| NativeWind | 4.0+ | Tailwind CSS for RN |
| Victory Native | 41+ | 数据可视化（雷达图） |
| React Native Reanimated | 3.16+ | 高性能动画 |

**后端**

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | 高性能异步 API 框架 |
| Python | 3.14 | 后端运行环境 |
| SQLite | 3.50+ | 嵌入式数据库（9 个独立实例） |
| FAISS | 1.7+ | Facebook 向量相似度检索库 |
| OpenAI SDK | 1.0+ | MiMo API 兼容客户端 |
| SSE | — | Server-Sent Events 流式输出 |
| Pydantic | 2.0+ | 数据校验与序列化 |
| bcrypt | 4.0+ | 密码哈希 |
| slowapi | — | 速率限制中间件 |

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 必需 |
|------|------|------|
| Python | 3.14 | ✅ |
| Node.js | 18+ | ✅ |
| npm | 9+ | ✅ |
| MiMo API Key | — | ✅ |

### 方式一：一键配置（推荐）

```bash
# Windows - 一键配置环境（检查依赖、创建 venv、安装包、初始化数据库）
scripts\setup.bat
```

### 方式二：手动配置

**步骤 1：安装后端依赖**

```bash
pip install -r backend/requirements.txt
```

**步骤 2：安装前端依赖**

```bash
cd frontend
npm install
cd ..
```

**步骤 3：配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要配置（详见 [环境变量配置](#环境变量配置)）。

**步骤 4：初始化数据库**

```bash
python scripts/init_databases_v7.2.py
```

预期输出：
```
✅ 数据库 'ai_auth' 创建成功!
✅ 数据库 'ai_profiles' 创建成功!
✅ 数据库 'ai_resources' 创建成功!
✅ 数据库 'ai_paths' 创建成功!
✅ 数据库 'ai_tutor' 创建成功!
✅ 数据库 'ai_assessments' 创建成功!
✅ 数据库 'ai_agents' 创建成功!
✅ 数据库 'ai_rag_knowledge' 创建成功!
✅ 数据库 'ai_memory' 创建成功!
✅ 所有数据库初始化完成
```

**步骤 5：创建管理员账户**

```bash
python scripts/init_admin.py
```

默认账号：`admin` / `admin123`

**步骤 6：启动服务**

```bash
# 终端 1 — 启动后端
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2 — 启动前端
cd frontend && npm run dev
```

或使用启动脚本：

```bash
scripts\启动.bat          # 启动 Web 端
scripts\启动移动端.bat      # 启动移动端
```

**步骤 7：访问系统**

| 服务 | 地址 |
|------|------|
| Web 前端 | http://localhost:3000 |
| API 文档（Swagger） | http://localhost:8000/docs |
| API 文档（ReDoc） | http://localhost:8000/redoc |
| 默认账号 | `admin` / `admin123` |

---

## 环境变量配置

系统通过 `.env` 文件管理配置，模板位于 `.env.example`。

### 完整配置项

```bash
# ===== 安全配置 =====
JWT_SECRET=your_random_secret_key_here_at_least_32_chars   # JWT 签名密钥（必需，≥32字符）

# ===== 应用配置 =====
DEBUG=false                                                 # 调试模式
APP_VERSION=7.2.0                                           # 应用版本
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001  # CORS 白名单

# ===== MiMo AI 配置 =====
MIMO_API_KEY=your_mimo_api_key_here                         # MiMo API 密钥（必需）
MIMO_BASE_URL=https://api.mimo.ai/v1                        # API 基础地址
MIMO_MODEL=mimo-v2.5-pro                                    # 主力推理模型
MIMO_VISION_MODEL=mimo-v2.5                                 # 视觉理解模型
MIMO_IMAGE_MODEL=mimo-image                                 # 图片生成模型
MIMO_TTS_MODEL=mimo-tts                                     # 语音合成模型

# ===== 数据库配置 =====
SQLITE_DB_DIR=data/databases                                # SQLite 数据库目录

# ===== 其他配置 =====
LOG_LEVEL=INFO                                              # 日志级别
MAX_UPLOAD_SIZE=50                                          # 最大上传文件大小(MB)
RAG_SIMILARITY_THRESHOLD=0.8                                # RAG 相似度阈值
```

### 配置项说明

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `JWT_SECRET` | ✅ | — | JWT 签名密钥，≥32 字符，启动时强制校验 |
| `MIMO_API_KEY` | ✅ | — | MiMo API 密钥，从 [MiMo 开放平台](https://api.mimo.ai/) 获取 |
| `MIMO_BASE_URL` | ❌ | `https://api.mimo.ai/v1` | API 基础地址 |
| `MIMO_MODEL` | ❌ | `mimo-v2.5-pro` | 文本推理模型 |
| `MIMO_VISION_MODEL` | ❌ | `mimo-v2.5` | 视觉理解模型 |
| `MIMO_IMAGE_MODEL` | ❌ | `mimo-image` | 图片生成模型 |
| `MIMO_TTS_MODEL` | ❌ | `mimo-tts` | 语音合成模型 |
| `SQLITE_DB_DIR` | ❌ | `data/databases` | 数据库存储目录 |
| `ALLOWED_ORIGINS` | ❌ | `http://localhost:3000` | CORS 允许的源 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `MAX_UPLOAD_SIZE` | ❌ | `50` | 单文件最大上传大小（MB） |
| `RAG_SIMILARITY_THRESHOLD` | ❌ | `0.8` | RAG 检索相似度阈值 |

---

## 功能模块详解

### 模块总览

```
┌─────────────────────────────────────────────────────────┐
│                    首页工作台 (Dashboard)                 │
│  问候语 │ 统计卡片 │ 继续学习 │ 今日建议 │ 协同动态      │
└─────────────────────────────────────────────────────────┘
                          │
        ┌────────┬────────┼────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼        ▼
    ┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
    │学生   ││资源   ││学习   ││智能   ││效果   ││知识   │
    │画像   ││生成   ││路径   ││辅导   ││评估   ││库     │
    └───────┘└───────┘└───────┘└───────┘└───────┘└───────┘
```

### 1. 首页工作台

登录后的默认页面，所有数据从后端实时获取，与当前用户绑定。

| 区域 | 功能 | API 端点 |
|------|------|---------|
| 顶部问候 | 用户名 + 学习天数/时长 | `GET /api/agent/dashboard/stats` |
| 统计卡片 | 学习记录/兴趣领域/生成资源/薄弱待补 | `GET /api/agent/get-profile` |
| 继续学习 | 最近资源列表，点击预览 | `GET /api/agent/list-resources` |
| 今日建议 | 基于记忆系统的个性化推荐 | `GET /api/agent/learning-recommendations` |
| 协同动态 | 智能体活动日志实时流 | `GET /api/agent/activity-logs` |
| 快速开始 | AI问答/资源生成/学习评估/上传文档 | 模块入口 |

### 2. 学生画像模块

**核心能力**：通过自然语言对话构建 9 维度动态学生画像。

**数据管理**（Tab 切换）：

| 功能 | 说明 |
|------|------|
| 课程表管理 | 手动录入 + 文件导入（PDF/Word/Excel/PPT/图片），MiMo 自动识别 |
| 成绩管理 | 录入 + 文件导入，按学期统计分析 |
| 错题本 | 添加/标记掌握/删除 + 文件导入 |
| 学习计划 | MiMo 生成 + 手动创建（周计划/备考计划/自定义） |

**文件导入特性**：
- MiMo 优先校验内容类型（课表/成绩/错题），不匹配直接报错
- 支持扫描版 PDF（PyMuPDF 转图片后 OCR）
- 图片文件优先 OCR 提取，失败降级到多模态视觉识别
- 识别期间切换 Tab 不中断进程

### 3. 资源生成模块

根据学生画像和选择的参数，MiMo 生成个性化学习资源。

**配置项**：
- 学科选择
- 主题输入
- 资源类型（可多选，7 种）
- 难度级别（初级/中级/高级）

**生成流程**：SSE 流式输出，5 个阶段实时推送进度。

### 4. 学习路径模块

MiMo 分析学生当前知识水平，规划有序的个性化学习路径。

**特性**：
- 知识点前置依赖关系建立
- 学习进度实时跟踪
- 路径可视化展示

### 5. 智能辅导模块

多轮对话答疑，集成记忆增强和 RAG 知识库检索。

**响应模态**：
- 文字分步解释
- Mermaid 图解
- 代码示例
- 知识引用溯源

**记忆增强**：自动检索相关历史记忆，构建增强上下文，实现"越聊越懂你"。

### 6. 效果评估模块

多维度学习效果评估，生成可视化评估报告。

**评估维度**：基于学习历史、资源使用、辅导记录等数据综合分析。

### 7. 知识库模块

文档上传 + 混合检索引擎（KNN + ANN + RRF）。

**支持格式**：TXT / MD / PDF / DOCX / PPTX / XLSX / CSV（单文件最大 20MB）

**检索能力**：
- KNN 关键词路径：SQLite FTS5 精确匹配
- ANN 向量路径：FAISS + mimo-embedding 语义匹配
- RRF 融合排序
- 11 种高级检索策略

---

## 多智能体系统

### 智能体角色

| 智能体 | 角色 | 职责 | 核心输出 |
|--------|------|------|---------|
| **Coordinator** | 指挥官 | 任务分发、结果聚合、异常处理、协商仲裁 | 协作结果 |
| **ProfileAgent** | 画像师 | 8 轮对话采集信息，构建 9 维度画像 | 画像数据 |
| **ResourceAgent** | 讲师 | 生成 7 种类型学习资源 | 学习资源 |
| **PathAgent** | 导师 | 分析知识水平，规划学习路径 | 学习路径 |
| **TutorAgent** | 辅导员 | 多轮对话答疑 + 记忆增强 + RAG 检索 | 多模态回答 |
| **AssessmentAgent** | 评估师 | 多维度学习效果评估 | 评估报告 |

### 协作流程

```
用户请求
    │
    ▼
Coordinator（协调器）
    │
    ├──► ProfileAgent ──┐
    ├──► StudentData   ──┤  并行采集
    ▼                    ▼
协商优化（画像 + 数据综合分析）
    │
    ├───────────────┐
    ▼               ▼
ResourceAgent   PathAgent       并行生成
    │               │
    ▼               ▼
AssessmentAgent ──► 异步评估 ──► 返回用户
```

### 消息总线

事件驱动通信，支持 14 种消息类型：

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| `TASK_REQUEST` | Coordinator → Agent | 任务分发 |
| `TASK_RESULT` | Agent → Coordinator | 任务结果 |
| `PROFILE_UPDATE` | ProfileAgent → All | 画像更新通知 |
| `RESOURCE_READY` | ResourceAgent → All | 资源生成完成 |
| `NEGOTIATION` | Agent ↔ Agent | 协商决策 |
| `STATUS_UPDATE` | Agent → Coordinator | 状态更新 |
| `ERROR_REPORT` | Agent → Coordinator | 错误报告 |
| `DATA_REQUEST` | Agent → DataLayer | 数据查询 |
| `DATA_RESPONSE` | DataLayer → Agent | 数据返回 |
| `AI_REQUEST` | Agent → AILayer | AI 调用 |
| `AI_RESPONSE` | AILayer → Agent | AI 返回 |
| `MEMORY_QUERY` | TutorAgent → MemoryLayer | 记忆查询 |
| `MEMORY_STORE` | TutorAgent → MemoryLayer | 记忆存储 |
| `SAFETY_CHECK` | Any → SafetyService | 安全检查 |

### 协商决策机制

| 决策类型 | 说明 |
|---------|------|
| **Propose** | 提议方案 |
| **Accept** | 接受方案 |
| **Reject** | 拒绝方案 |
| **Counter** | 反提议（提出替代方案） |

---

## MiMo 大模型集成

### 集成架构

```
各 Agent / Service 层
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  spark_client.py  (MiMoClient 单例)                      │
│  基于 OpenAI SDK，通过 OpenAI 兼容接口连接 MiMo API       │
│                                                          │
│  核心方法:                                                │
│  · chat()            — 文本对话                          │
│  · chat_with_image() — 多模态视觉理解                    │
│  · chat_stream()     — 流式文本生成                      │
│  · generate_image()  — 图片生成                          │
│  · text_to_speech()  — 语音合成                          │
│  · ocr_image()       — OCR 文字识别                      │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  embedding_service.py  (EmbeddingService 单例)            │
│  · get_embedding()     — 文本向量化 (768维)               │
│  · cosine_similarity() — 余弦相似度计算                   │
└──────────────────────────────────────────────────────────┘
```

### API 端点

| 功能 | 端点 | 模型 |
|------|------|------|
| 文本对话 | `{base_url}/chat/completions` | `mimo-v2.5-pro` |
| 视觉理解 | `{base_url}/chat/completions` | `mimo-v2.5` |
| 图片生成 | `{base_url}/images/generations` | `mimo-image` |
| 语音合成 | `{base_url}/audio/speech` | `mimo-tts` |
| 文本向量化 | `{base_url}/embeddings` | `mimo-embedding` |

### 复杂度分层调用

MiMoClient 提供按复杂度分层的调用方法，自动选择合适的参数配置：

| 方法 | 适用场景 | 说明 |
|------|---------|------|
| `simple()` | 简单分类/提取 | 低 token，快速响应 |
| `standard()` | 标准对话 | 平衡质量与速度 |
| `advanced()` | 复杂推理 | 高 token，深度思考 |
| `ultra()` | 最复杂任务 | 最大 token，最高质量 |

---

## 混合检索系统

### 算法架构

```
用户查询
   │
   ├── KNN 关键词路径 ──► SQLite FTS5 ──► Top-K 结果
   │   (专业术语精确匹配)
   │
   ├── ANN 向量路径 ──► mimo-embedding(768维) ──► FAISS 检索 ──► Top-K 结果
   │                                                   │
   │                                            三级回退策略
   │                                            ┌──────┴──────┐
   │                                            ▼             ▼
   │                                      索引已就绪     索引未构建
   │                                      FAISS搜索     惰性构建后搜索
   │                                            │
   │                                            ▼ FAISS不可用
   │                                      暴力余弦回退(numpy)
   │
   └──────────────────┬──────────────────────────────────────┐
                      ▼                                      │
         ┌──── RRF 融合排序 ─────┐                           │
         │ RRF(d)=Σ1/(k+rank)   │                           │
         │ 去重 + Top-K 截断     │                           │
         └───────────┬──────────┘                           │
                     ▼                                       │
           混合检索结果（基座）                                │
                     │                                       │
         ┌───────────┼───────────┐                           │
         ▼           ▼           ▼                           │
       HyDE     RAG-Fusion  Graph-Enhanced                  │
       Multi-Query Contextual 策略路由(smart_search)         │
```

### 11 种检索策略

| 策略 | 标识 | 说明 | 适用场景 |
|------|------|------|---------|
| 自动选择 | `auto` | 短查询用 HyDE，长查询用 RAG-Fusion | 默认 |
| KNN 关键词 | `knn` | SQLite FTS5 全文索引 | 专业术语、公式 |
| ANN 向量 | `ann` | FAISS + mimo-embedding | 模糊语义查询 |
| 混合检索 | `hybrid` | KNN + ANN + RRF | 通用推荐 |
| 假设性文档 | `hyde` | HyDE（Gao et al., 2023） | 短查询、概念性问题 |
| 多查询 | `multi_query` | Multi-Query（LangChain, 2023） | 提高召回率 |
| RAG-Fusion | `rag_fusion` | RAG-Fusion + RRF（Raudaschl, 2023） | 通用推荐 |
| 上下文精排 | `contextual` | Contextual Retrieval（Anthropic, 2024） | 高精度场景 |
| 图谱增强 | `graph` | Graph-Enhanced RAG（Microsoft, 2024） | 有图谱数据时 |
| 混合进阶 | `hybrid_advl` | 基座 + HyDE + RAG-Fusion 三路 RRF | 平衡速度与精度 |
| 全策略集成 | `ensemble` | 全部 6 种方法取并集，RRF 融合 | 最全面 |

### 三级回退策略

| 级别 | 触发条件 | 检索方式 | 响应时间 |
|------|---------|---------|---------|
| L1 | FAISS 索引已就绪 | `IndexFlatIP` 内积搜索 | ~5ms |
| L2 | FAISS 可用但索引为空 | 从 DB 加载构建索引后搜索 | ~500ms（首次） |
| L3 | FAISS 不可用 | numpy 暴力余弦相似度 | ~100ms |

### Embedding 技术参数

| 参数 | 值 | 说明 |
|------|------|------|
| API | MiMo Embedding API | `https://api.mimo.ai/v1/embeddings` |
| 向量维度 | 768 | 空文本返回零向量 |
| 文本截断 | 8000 字符 | 超长自动截断 |
| 索引类型 | `faiss.IndexFlatIP` | L2 归一化后内积 ≡ 余弦相似度 |
| 持久化 | `data/faiss_index/` | 二进制索引 + ID 映射 JSON |

---

## 记忆系统

四层记忆架构，集成在 TutorAgent 中，实现"越聊越懂你"的个性化辅导。

### 记忆层次

| 层次 | 类型 | 说明 | 存储方式 |
|------|------|------|---------|
| L1 | 短期记忆 | Token 级上下文窗口 | 对话历史自动保存 |
| L2 | 情景记忆 | 对话事件和学习场景 | 按重要性衰减 |
| L3 | 语义记忆 | SPO 三元组事实知识 | 冲突检测与修正 |
| L4 | 实体记忆 | KV 画像 + 知识图谱 | 实体关系网络 |

### 遗忘机制

基于艾宾浩斯遗忘曲线的智能衰减：

```
R = e^(-t/S)

其中：
  R — 记忆保持力（Retention）
  t — 时间间隔（Time elapsed）
  S — 记忆强度（Strength）
```

### 记忆增强问答流程

```
用户提问
    │
    ▼
提取关键实体
    │
    ▼
检索相关记忆（短期 + 情景 + 语义 + 实体）
    │
    ▼
构建增强上下文
    │
    ▼
MiMo 生成回答（融合记忆上下文）
    │
    ▼
存储新记忆
```

---

## 数据库设计

### 多数据库架构

9 个独立 SQLite 数据库，功能完全隔离，无需外部数据库服务。

| 数据库 | 文件 | 用途 | 核心表 |
|--------|------|------|--------|
| `ai_auth` | `ai_auth.db` | 认证与用户管理 | `users`, `sessions` |
| `ai_profiles` | `ai_profiles.db` | 学生画像 | `student_profiles`, `course_schedules`, `student_grades`, `error_notes`, `study_plans` |
| `ai_resources` | `ai_resources.db` | 学习资源 | `learning_resources`, `resource_safety_logs` |
| `ai_paths` | `ai_paths.db` | 学习路径 | `learning_paths`, `path_progress` |
| `ai_tutor` | `ai_tutor.db` | 智能辅导 | `tutor_sessions`, `tutor_messages`, `tutor_knowledge_refs` |
| `ai_assessments` | `ai_assessments.db` | 效果评估 | `learning_assessments`, `assessment_dimensions`, `learning_activities` |
| `ai_agents` | `ai_agents.db` | 智能体协作 | `agent_collaboration_logs`, `agent_tasks` |
| `ai_rag_knowledge` | `ai_rag_knowledge.db` | RAG 知识库 | `knowledge_documents`, `knowledge_points`, `document_categories` + FTS5 |
| `ai_memory` | `ai_memory.db` | 记忆系统 | 8 张记忆表（见下） |

### 记忆系统表结构

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

-- 情景记忆
CREATE TABLE episodic_memory (...);

-- 语义记忆（SPO 三元组）
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

-- 实体记忆（KV 画像 + 知识图谱）
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

-- 记忆元数据（遗忘机制控制）
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

## API 接口

### 认证 API

| 端点 | 方法 | 功能 | 认证 |
|------|------|------|------|
| `/api/auth/login` | POST | 用户登录 | ❌ |
| `/api/auth/register` | POST | 用户注册 | ❌ |
| `/api/auth/guest` | POST | 游客模式 | ❌ |
| `/api/auth/me` | GET | 获取当前用户 | ✅ |
| `/api/auth/change-password` | POST | 修改密码 | ✅ |

### 学习智能体 API（核心）

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/agent/build-profile` | POST | 构建学生画像 |
| `/api/agent/get-profile` | GET | 获取学生画像 |
| `/api/agent/generate-resources` | POST | 生成学习资源 |
| `/api/agent/plan-path` | POST | 规划学习路径 |
| `/api/agent/tutor` | POST | 智能辅导答疑 |
| `/api/agent/assess` | POST | 学习效果评估 |
| `/api/agent/list-resources` | GET | 获取资源列表 |
| `/api/agent/save-resource` | POST | 保存资源到数据库 |
| `/api/agent/dashboard/stats` | GET | 工作台统计数据 |
| `/api/agent/activity-logs` | GET/POST | 活动日志查询/记录 |
| `/api/agent/learning-recommendations` | GET | 个性化学习推荐 |
| `/api/agent/advanced-search` | POST | 高级检索（11 种策略） |

### 流式输出 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/stream/generate-resource/{type}` | GET | 流式生成资源（SSE） |
| `/api/stream/tutor` | POST | 流式智能辅导（SSE） |
| `/api/stream/progress/{task_id}` | GET | 查询任务进度 |
| `/api/stream/check-content-safety` | POST | 内容安全检查 |
| `/api/stream/verify-fact` | POST | 事实验证 |

### 系统 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查（SQLite/FAISS 状态） |

**交互式 API 文档**：启动后端后访问 http://localhost:8000/docs

---

## 移动端 App

### 技术架构

```
┌─────────────────────────────────────────┐
│  React Native + Expo 52                 │
│  ┌───────────────────────────────────┐  │
│  │  App Router (Expo Router)         │  │
│  │  ┌─────────┐  ┌───────────────┐  │  │
│  │  │ (auth)  │  │    (tabs)     │  │  │
│  │  │ login   │  │ index         │  │  │
│  │  │ register│  │ tutor         │  │  │
│  │  └─────────┘  │ resources     │  │  │
│  │               │ profile       │  │  │
│  │               └───────────────┘  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  components/ ui/ chat/ dashboard/ │  │
│  │  stores/ hooks/ constants/ lib/   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 功能模块

| 模块 | 功能 |
|------|------|
| 工作台 | 统计卡片、最近资源、今日建议、协同动态 |
| 智能辅导 | 聊天界面、SSE 流式输出、学科选择 |
| 资源生成 | 7 种类型选择、难度配置、MiMo 生成 |
| 学生画像 | 9 维度画像、课程表、成绩、错题 |
| 学习路径 | 路径可视化、进度跟踪 |
| 效果评估 | 多维度评分、改进建议 |

### 启动方式

```bash
cd mobile
npm install
npx expo start
```

使用 Expo Go 扫码在真机测试，或使用 Android Studio / Xcode 模拟器运行。

---

## 安全机制

### 认证与授权

| 特性 | 说明 |
|------|------|
| 算法 | HS256 |
| 有效期 | 24 小时 |
| 密钥校验 | 启动时强制校验 `JWT_SECRET` |
| 密码存储 | bcrypt 哈希 |
| 游客模式 | 支持（`user_id=0`, `role=guest`） |

### 速率限制

| 端点 | 限制 | 防护目标 |
|------|------|---------|
| `/api/auth/register` | 5 次/分钟 | 防止批量注册 |
| `/api/auth/login` | 10 次/分钟 | 防止暴力破解 |
| 其他 API | 120 次/分钟 | 全局保护 |
| AI 生成端点 | 独立限流 | 防止资源滥用 |

### 内容安全

**敏感词检测**：AC 自动机（Aho-Corasick），O(n) 一次扫描，127 条敏感词，支持热更新。

| 类别 | 说明 |
|------|------|
| 暴力 | 暴力行为描述 |
| 色情 | 色情内容 |
| 歧视 | 种族/性别歧视 |
| 违法 | 违法指导内容 |
| 虚假信息 | 明显错误知识点 |
| 仇恨言论 | 仇恨煽动 |
| 商业推广 | 广告推销 |
| 学术不端 | 代写/抄袭暗示 |

### 防幻觉机制

```
confidence = rag_similarity × 0.6 + fact_check_score × 0.4
verified = confidence ≥ 0.7
```

三层防护：RAG 优先检索 → 事实核查验证 → 引用标注溯源。

### HTTP 安全头

| 安全头 | 值 | 作用 |
|--------|-----|------|
| X-Content-Type-Options | nosniff | 防 MIME 嗅探 |
| X-Frame-Options | DENY | 防 Clickjacking |
| X-XSS-Protection | 1; mode=block | 防 XSS |
| Referrer-Policy | strict-origin-when-cross-origin | 控制 Referer |
| Strict-Transport-Security | max-age=31536000 | 强制 HTTPS |

### 自定义异常体系

| 异常类 | HTTP 状态码 | 用途 |
|--------|-----------|------|
| `ValidationError` | 400 | 请求参数校验失败 |
| `AuthenticationError` | 401 | 认证失败 |
| `AuthorizationError` | 403 | 权限不足 |
| `RateLimitError` | 429 | 请求过于频繁 |
| `DatabaseError` | 500 | 数据库操作异常 |
| `AIServiceError` | 502 | AI 服务调用失败 |
| `ResourceGenerationError` | 500 | 资源生成异常 |
| `AppException` | 可配置 | 业务基础异常 |

---

## 部署指南

### Docker 部署

```bash
# 一键启动（后端 + 前端 + SQLite）
docker-compose up -d
```

### 打包为 Windows 安装程序

```bash
# PyInstaller 打包
python build.py

# NSIS 编译安装程序
makensis installer.nsi
```

生成文件：
- `AI学习智能体_Setup.exe` — 完整安装程序
- `dist/AI学习智能体/` — 免安装版本

### 手动部署

```bash
# 后端
pip install -r backend/requirements.txt
python scripts/init_databases_v7.2.py
python scripts/init_admin.py
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm install && npm run build && npm start
```

---

## 项目结构

```
├── backend/                        # 后端 API 服务
│   ├── api/
│   │   ├── agent.py                # 多智能体 API 端点
│   │   ├── stream.py               # 流式输出（SSE）
│   │   └── auth.py                 # 认证 API
│   ├── main.py                     # FastAPI 应用入口
│   ├── dependencies.py             # JWT 认证、权限校验
│   ├── exceptions.py               # 8 种自定义异常
│   ├── middleware/                  # 中间件
│   └── schemas/                    # Pydantic 请求/响应模型
│
├── services/                       # 业务逻辑层
│   ├── spark_client.py             # MiMo AI 客户端（OpenAI 兼容）
│   ├── agent_coordinator.py        # 协调器
│   ├── profile_agent.py            # 画像智能体
│   ├── resource_agent.py           # 资源智能体
│   ├── path_agent.py               # 路径智能体
│   ├── tutor_agent.py              # 辅导智能体（集成记忆增强）
│   ├── assessment_agent.py         # 评估智能体
│   ├── memory_service.py           # 记忆系统服务
│   ├── message_bus.py              # 事件驱动消息总线
│   ├── agent_message.py            # 消息协议定义（14 种类型）
│   ├── advanced_retrieval_service.py # 高级检索（11 种策略）
│   ├── content_safety_service.py   # 内容安全（AC 自动机 + 防幻觉）
│   ├── streaming_service.py        # 流式输出服务
│   ├── animation_service.py        # 教学动画生成
│   ├── image_service.py            # 图片/SVG 生成
│   └── video_generation_service.py # 视频脚本生成
│
├── data/                           # 数据访问层
│   ├── rag_knowledge_base.py       # RAG 知识库（FAISS + 混合检索）
│   ├── embedding_service.py        # MiMo Embedding 768 维向量化
│   ├── document_parser.py          # 文档解析（PDF/Word/Excel/PPT）
│   ├── data_manager.py             # 数据管理器
│   ├── db_operations.py            # 数据库操作
│   ├── qa_db_operations.py         # QA 相似问题检索
│   ├── dao.py                      # DAO 层
│   ├── config.py                   # 多数据库配置
│   ├── redis_cache.py              # 缓存层
│   └── databases/                  # 9 个 SQLite 数据库文件
│
├── core/                           # 核心工具
│   ├── logger.py                   # 结构化日志（JSON 格式，日志轮转）
│   ├── json_utils.py               # 容错 JSON 解析
│   ├── prompts.py                  # Prompt 模板
│   ├── utils.py                    # 通用工具函数
│   └── ui_components.py            # UI 组件配置
│
├── frontend/                       # Web 前端（Next.js）
│   ├── app/
│   │   ├── layout.tsx              # 根布局
│   │   ├── page.tsx                # 首页
│   │   ├── dashboard/              # 工作台
│   │   ├── tutor/                  # 智能辅导
│   │   ├── resources/              # 资源生成
│   │   ├── assessment/             # 效果评估
│   │   ├── learning-path/          # 学习路径
│   │   └── profile/                # 学生画像
│   ├── components/
│   │   ├── shared/                 # 共享组件
│   │   └── modules/                # 6 大功能模块组件
│   ├── lib/
│   │   ├── api.ts                  # API 客户端（重试 + 超时）
│   │   ├── hooks.ts                # 防抖/节流 hooks
│   │   └── useVoiceInput.ts        # 语音输入 hook
│   ├── stores/index.ts             # Zustand 状态管理
│   ├── styles/globals.css          # 全局样式
│   └── middleware.ts               # 安全头中间件
│
├── mobile/                         # 移动端（React Native + Expo）
│   ├── app/
│   │   ├── (auth)/                 # 登录/注册
│   │   └── (tabs)/                 # Tab 导航页面
│   ├── components/
│   │   ├── ui/                     # 基础 UI 组件
│   │   ├── chat/                   # 聊天组件
│   │   └── dashboard/              # 工作台组件
│   ├── lib/api.ts                  # API 客户端
│   ├── stores/                     # Zustand 状态管理
│   ├── hooks/                      # 自定义 Hooks
│   ├── constants/                  # 常量配置
│   └── android/                    # Android 原生配置
│
├── docs/                           # 项目文档
├── scripts/                        # 初始化与启动脚本
├── config/                         # 配置文件
│   └── sensitive_words.json        # 敏感词库（127 条）
├── Dockerfile                      # 后端容器化
├── docker-compose.yml              # 多服务编排
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
├── pyproject.toml                  # Python 项目配置
└── LICENSE.txt                     # MIT 许可证
```

---

## 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 画像构建 | <2s | MiMo 单次对话 |
| 资源生成 | 3-90s | 取决于资源类型和复杂度 |
| SSE 延迟 | <200ms | 首字节时间 |
| 内容安全检查 | <100ms | AC 自动机 O(n) |
| API 响应 (P95) | <2s | 不含 AI 生成 |
| RAG 检索 | ~5ms | FAISS 就绪时 |
| 暴力余弦回退 | ~100ms | FAISS 不可用时 |

---

## 版本变更日志

### v7.4.0（2026-07）

**新增**：
- 反思验证器（Reflector）：答案质量评分 + 证据链检查 + 低分自动二次检索重新生成
- 多跳推理检索（Multi-Hop Retriever）：逻辑图构建 + 2-5跳深度推理 + 证据链验证
- 自学习闭环（Self-Learning Loop）：反馈收集 → 经验筛选 → 数据增强 → RAG 增量更新
- 新增 3 张数据库表：knowledge_entity_graph, user_feedback, learning_experiences
- 新增 API 端点：POST /feedback, GET /learning-stats, POST /trigger-learning
- 检索策略新增第12种：multi_hop（多跳推理检索）

### v7.3.0（2026-07）

**新增**：
- 移动端 App（React Native + Expo），覆盖全部 6 大功能模块
- 完整文档体系（docs/ 目录，11 篇文档）

### v7.2.0（2026-06）

**新增**：
- 8 种自定义异常类，分层异常处理
- DAO 层（ResourceDAO + ActivityDAO）
- 12 个 Pydantic 请求模型
- 敏感词外部配置（125 词）

**改进**：
- JWT 密钥缺失时启动失败（不再静默降级）
- 核心端点改用 Pydantic 模型 + DAO 层

### v7.1.0（2026-05）

**新增**：
- 无限长时记忆架构（四层记忆模型）
- 艾宾浩斯遗忘曲线衰减机制
- 记忆增强问答
- 知识图谱实体关系

### v7.0.0（2026-04）

**新增**：
- 多智能体协同架构（6 个专业智能体）
- 事件驱动消息总线（14 种消息类型）
- 7 种学习资源类型
- 9 维度学生画像
- 混合检索系统（KNN + ANN + RRF）
- 11 种高级检索策略
- 防幻觉三重保障
- 流式输出（SSE）
- 多数据库架构（9 个独立 SQLite）
- 单页面导航系统

---

## 文档导航

完整文档位于 [`docs/`](docs/) 目录：

| 文档 | 说明 |
|------|------|
| [文档中心](docs/README.md) | 文档导航首页 |
| [系统架构](docs/architecture.md) | 整体架构、技术选型、设计原则 |
| [API 接口参考](docs/api-reference.md) | 完整 API 端点列表与参数说明 |
| [数据库设计](docs/database.md) | 9 个数据库、30+ 张表结构 |
| [多智能体系统](docs/agents.md) | 6 个智能体、协作流程、消息协议 |
| [检索算法详解](docs/retrieval.md) | 混合检索、11 种策略、三级回退 |
| [记忆系统](docs/memory-system.md) | 四层记忆、遗忘机制、记忆增强 |
| [安全机制](docs/security.md) | JWT、限流、防幻觉、异常体系 |
| [部署指南](docs/deployment.md) | Docker、打包、App 构建 |
| [移动端开发](docs/mobile-app.md) | React Native 开发指南 |
| [版本变更日志](docs/changelog.md) | 版本变更记录 |

---

## 常见问题

### Q1: 如何获取 MiMo API Key？

访问 [MiMo 开放平台](https://api.mimo.ai/) 注册账号，在控制台创建 API Key，填入 `.env` 文件的 `MIMO_API_KEY` 字段。

### Q2: 系统如何体现"多智能体"？

系统有 6 个专业智能体（画像/资源/路径/辅导/评估/协调），通过事件驱动消息总线（14 种消息类型）分工协作，支持协商决策（Propose/Accept/Reject/Counter），不是单一 AI 模型调用。

### Q3: 如何保证 AI 回答的准确性？

三层防幻觉防护：
1. **RAG 优先**：回答前先检索知识库，基于事实生成
2. **事实核查**：交叉验证关键实体，置信度 < 0.7 标记为"可能存在幻觉"
3. **引用溯源**：标注信息来源，支持验证

### Q4: 为什么选择 9 个独立数据库？

- 功能隔离，避免数据耦合
- 性能优化，针对性优化不同数据类型
- 故障隔离，单库故障不影响全局
- RAG 知识库专业化（FTS5 全文索引）
- 无需外部数据库服务，部署简单

### Q5: 流式输出如何实现？

使用 SSE（Server-Sent Events），分 5 个阶段实时推送生成进度，前端通过 EventSource 接收，避免白屏等待。

### Q6: 如何备份数据库？

```bash
# SQLite 数据库文件位于 data/databases/ 目录
# 直接复制 .db 文件即可备份
copy data\databases\*.db backup\
```

### Q7: 如何导入 RAG 知识库数据？

```bash
python scripts/init_rag_db.py
```

支持 TXT/MD/PDF/DOCX/PPTX/XLSX/CSV 格式，单文件最大 20MB。

### Q8: 移动端如何启动？

```bash
cd mobile
npm install
npx expo start
```

使用 Expo Go 扫码在真机测试。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE.txt)。

---

<p align="center">
  <b>技术支持</b><br>
  <a href="http://localhost:8000/docs">API 文档（Swagger UI）</a> ·
  查看 <code>logs/</code> 目录获取运行日志
</p>
