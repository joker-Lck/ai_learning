# 数据库设计

## 多数据库架构

系统采用 **9 个独立 SQLite 数据库**，实现功能隔离、性能优化和故障隔离。

所有数据库文件存放在 `data/databases/` 目录，使用 `PRAGMA journal_mode=WAL` + `PRAGMA foreign_keys=ON`。

## 数据库清单

| 数据库文件 | 用途 | 核心表 |
|-----------|------|--------|
| **ai_auth.db** | 认证与用户管理 | users, sessions |
| **ai_profiles.db** | 学生画像存储 | student_profiles, course_schedules, student_grades, error_notes, study_plans |
| **ai_resources.db** | 学习资源管理 | learning_resources, resource_safety_logs |
| **ai_paths.db** | 学习路径规划 | learning_paths, path_progress |
| **ai_tutor.db** | 智能辅导对话 | tutor_sessions, tutor_messages, tutor_knowledge_refs |
| **ai_assessments.db** | 学习效果评估 | learning_assessments, assessment_dimensions, learning_activities |
| **ai_agents.db** | 智能体协作日志 | agent_collaboration_logs, agent_tasks |
| **ai_rag_knowledge.db** | RAG 知识库 | knowledge_documents, knowledge_points, document_categories |
| **ai_memory.db** | 记忆系统 | short_term_memory, episodic_memory, semantic_memory, entity_memory, entity_relations, memory_metadata, memory_conflicts, memory_access_log |

## 数据库关系

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

## 核心表结构

### ai_auth (认证库)

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'student' CHECK(role IN ('student', 'teacher', 'admin', 'guest')),
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT
);

-- 会话表
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### ai_profiles (画像库)

```sql
-- 学生画像（9 维度 JSON）
CREATE TABLE student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    profile_data TEXT NOT NULL,    -- JSON: 9维度画像
    conversation_log TEXT,         -- JSON: 对话历史
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 课程表
CREATE TABLE course_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    course_name TEXT NOT NULL,
    day_of_week INTEGER,          -- 1-7
    start_time TEXT,
    end_time TEXT,
    location TEXT,
    teacher TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 成绩
CREATE TABLE student_grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    course_name TEXT NOT NULL,
    score REAL,
    credit REAL,
    grade_type TEXT,              -- exam/assignment/quiz
    created_at TEXT DEFAULT (datetime('now'))
);

-- 错题本
CREATE TABLE error_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subject TEXT,
    question TEXT NOT NULL,
    answer TEXT,
    analysis TEXT,
    mastery INTEGER DEFAULT 0,   -- 0-100 掌握度
    tags TEXT,                    -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);

-- 学习计划
CREATE TABLE study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    semester TEXT,
    plan_type TEXT,               -- weekly/monthly/custom
    plan_data TEXT NOT NULL,      -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);
```

### ai_resources (资源库)

```sql
-- 学习资源
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
    created_at TEXT DEFAULT (datetime('now'))
);
```

### ai_rag_knowledge (知识库)

```sql
-- 知识文档
CREATE TABLE knowledge_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    content_text TEXT,
    embedding TEXT,                -- JSON: 动态维度向量（TF-IDF+SVD）
    uploaded_by INTEGER,
    usage_count INTEGER DEFAULT 0,
    is_public INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- FTS5 全文索引
CREATE VIRTUAL TABLE knowledge_documents_fts USING fts5(title, subject);
```

### ai_memory (记忆库)

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

-- 语义记忆：SPO 三元组
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

-- 实体记忆：KV 画像
CREATE TABLE entity_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entity_type TEXT,              -- person/concept/skill/course/tool
    entity_name TEXT NOT NULL,
    entity_alias TEXT,
    attributes TEXT,               -- JSON
    description TEXT,
    importance REAL DEFAULT 0.5,
    UNIQUE(user_id, entity_type, entity_name)
);

-- 记忆元数据：遗忘控制
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

## 设计优势

| 优势 | 说明 |
|------|------|
| 功能隔离 | 避免数据耦合，各模块独立 |
| 性能优化 | 针对性优化不同数据类型 |
| 易于维护 | 模块化设计，单库故障不影响全局 |
| 高可用性 | 故障隔离，单点故障不扩散 |
| 灵活扩展 | 新增功能不影响现有系统 |
| 无需外部服务 | SQLite 内置于 Python，零部署依赖 |
