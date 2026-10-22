# 数据库设计

## 多数据库架构（MySQL）

系统采用 **9 个独立 MySQL schema**，实现功能隔离、性能优化和故障隔离。

连接参数由 `.env` 提供：

```
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=...
MYSQL_CHARSET=utf8mb4
```

## 数据库清单

| MySQL schema | 用途 | 核心表 |
|-----------|------|--------|
| **ai_auth** | 认证与用户管理 | users, sessions, classes, class_students |
| **ai_profiles** | 学生画像存储 | student_profiles, course_schedules, student_grades, error_notes, study_plans |
| **ai_assessments** | 学习效果评估 | learning_assessments, assessment_dimensions, learning_activities, quiz_sessions, quiz_answers, study_groups |
| **ai_resources** | 学习资源管理 | learning_resources, resource_safety_logs |
| **ai_paths** | 学习路径规划 | learning_paths, path_progress |
| **ai_tutor** | 智能辅导对话 | tutor_sessions, tutor_messages, tutor_knowledge_refs |
| **ai_agents** | 智能体协作日志 | agent_collaboration_logs, agent_tasks |
| **ai_rag_knowledge** | RAG 知识库 | knowledge_documents, knowledge_points, document_categories |
| **ai_memory** | 记忆系统 | short_term_memory, episodic_memory, semantic_memory, entity_memory, entity_relations, memory_metadata |

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

## 访问层

业务代码通过 `data/dbapi.py` 访问数据库，它是 **sqlite3 兼容层**（基于 PyMySQL）：

```python
from data import dbapi as sqlite3
from data.config import get_auth_db_path

conn = sqlite3.connect(get_auth_db_path())  # → MySQL schema `ai_auth`
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM users WHERE username = ?", (name,))  # ? 占位符
```

兼容特性：

| sqlite3 接口 | MySQL 实现 |
|-------------|-----------|
| `?` 占位符 | 自动转换为 `%s` |
| `row_factory = sqlite3.Row` | 支持下标 + 列名访问 |
| `cursor.lastrowid` | `INSERT` 自增 ID |
| `PRAGMA ...` | 无操作（自动忽略） |
| `sqlite3.IntegrityError` | 映射 pymysql 异常 |

## 全文检索

原 SQLite FTS5 已替换为 **MySQL FULLTEXT + ngram 解析器**（支持中文）：

```sql
-- 索引
ALTER TABLE knowledge_documents
  ADD FULLTEXT KEY ft_knowledge_documents (title, subject) WITH PARSER ngram;

-- 查询
SELECT id, title,
       MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE) AS rank_score
FROM knowledge_documents
WHERE MATCH(title, subject) AGAINST (%s IN NATURAL LANGUAGE MODE)
ORDER BY rank_score DESC
LIMIT 10;
```

注意：`rank` 是 MySQL 8 保留字，排序列必须用别名（如 `rank_score`）。

## 初始化 / 迁移

```bash
# 建库建表（9 个 schema）
python scripts/migrate_to_mysql.py --schema

# 从 legacy SQLite 文件导入数据
python scripts/migrate_to_mysql.py --data

# 兼容旧入口
python scripts/init_databases.py
```

## 设计优势

| 优势 | 说明 |
|------|------|
| 功能隔离 | 避免数据耦合，各模块独立 schema |
| 并发能力 | MySQL InnoDB 行锁，优于 SQLite 文件锁 |
| 全文检索 | ngram FULLTEXT 原生支持中文 |
| 易于维护 | 模块化设计，单库故障不影响全局 |
| 高可用性 | 支持主从复制、备份与容灾 |
| 代码兼容 | dbapi 兼容层保留 sqlite3 调用风格 |
