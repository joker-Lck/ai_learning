# 数据库设计

> **版本**：v9.1.0

## 多数据库架构（MySQL）

系统采用 **9 个 MySQL schema**（ai_auth / ai_profiles / ai_resources / ai_paths / ai_tutor / ai_assessments / ai_agents / ai_rag_knowledge / ai_memory），实现功能隔离、性能优化和故障隔离。

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
| **ai_assessments** | 学习效果评估 + 考试/批改 | learning_assessments, assessment_dimensions, learning_activities, quiz_sessions, quiz_answers, study_groups, **exam_papers, exam_questions, exam_assignments, exam_submissions, exam_answers**（v9.1.0） |
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

## 考试/批改数据表（ai_assessments，v9.1.0 新增）

建表真源：`scripts/migrate_to_mysql.py`。共 5 张表，支撑教师 AI 出题/组卷 + 主观题批改。

### exam_papers — 试卷

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 试卷 ID |
| teacher_id | BIGINT | 命题教师 |
| title | VARCHAR(255) | 试卷标题 |
| subject / grade / topic | VARCHAR | 学科 / 年级 / 主题 |
| paper_type | VARCHAR(32) | practice（练习卷）/ exam（考试卷） |
| total_score | DOUBLE | 总分（默认 100） |
| duration_minutes | INT | 考试时长（默认 60） |
| difficulty | VARCHAR(32) | easy/medium/hard/mixed |
| knowledge_points | TEXT | 知识点列表（JSON 数组） |
| question_source | VARCHAR(32) | 题目来源（ai/bank/mixed） |
| status | VARCHAR(32) | 状态（draft 等） |
| created_at / updated_at | TIMESTAMP | 创建 / 更新时间 |

索引：`idx_exam_papers_teacher (teacher_id)`

### exam_questions — 试题

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 题目 ID |
| paper_id | BIGINT | 所属试卷 |
| q_index | INT | 题目序号 |
| question_type | VARCHAR(64) | multiple_choice / judge / fill_blank / short_answer |
| question_text | TEXT | 题干 |
| options | TEXT | 选项（JSON，选择题用） |
| correct_answer | TEXT | 正确答案（客观题自动判分用） |
| **reference_answer** | TEXT | **参考答案（主观题）** |
| **scoring_points** | TEXT | **评分要点（JSON，主观题按点给分）** |
| explanation | TEXT | 解析 |
| knowledge_point | VARCHAR(255) | 知识点 |
| difficulty | VARCHAR(32) | 难度 |
| score | DOUBLE | 分值（按题型权重折算） |

索引：`idx_exam_questions_paper (paper_id)`

### exam_assignments — 发布到班级

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 发布 ID |
| paper_id | BIGINT | 试卷 |
| class_id | BIGINT | 目标班级 |
| assigned_by | BIGINT | 发布教师 |
| title | VARCHAR(255) | 作业标题 |
| due_at | TIMESTAMP NULL | 截止时间 |
| status | VARCHAR(32) | active / closed |
| allow_late | TINYINT | 是否允许补交 |
| created_at | TIMESTAMP | 发布时间 |

索引：`idx_exam_assign_paper`、`idx_exam_assign_class`

### exam_submissions — 提交

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 提交 ID |
| assignment_id | BIGINT | 所属发布 |
| paper_id | BIGINT | 试卷 |
| student_id | BIGINT | 学生 |
| status | VARCHAR(32) | in_progress 等 |
| objective_score | DOUBLE | 客观题自动得分 |
| ai_score | DOUBLE | AI 批改总分 |
| final_score | DOUBLE | 最终成绩（教师复核为准） |
| total_score | DOUBLE | 卷面总分 |
| submitted_at / graded_at / reviewed_at | TIMESTAMP NULL | 交卷 / 批改 / 复核时间 |
| created_at | TIMESTAMP | 创建时间 |

唯一键：`uk_exam_sub_assign_student (assignment_id, student_id)`；索引 `idx_exam_sub_student`

### exam_answers — 逐题作答

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 作答 ID |
| submission_id | BIGINT | 所属提交 |
| question_id | BIGINT | 题目 |
| q_index | INT | 题目序号 |
| question_type / question_text | VARCHAR / TEXT | 题型 / 题干快照 |
| answer_text | LONGTEXT | 作答文本（含 OCR 识别文本，可修正） |
| **answer_image_path** | VARCHAR(512) | **手写答案图片路径** |
| **ocr_text** | LONGTEXT | **OCR 识别文本** |
| **ocr_confidence** | DOUBLE | **识别置信度** |
| **ocr_engine** | VARCHAR(64) | **识别引擎（rapidocr / vision）** |
| correct_answer / reference_answer | TEXT | 正确答案 / 参考答案快照 |
| max_score | DOUBLE | 本题满分 |
| is_correct | TINYINT | 客观题是否正确 |
| ai_score | DOUBLE | AI 评分 |
| score | DOUBLE | 得分 |
| feedback | TEXT | 评语 |
| **rag_evidence** | TEXT | **RAG 检索到的评分依据** |
| **knowledge_hits** | TEXT | **知识点命中/缺失（JSON）** |
| **grade_status** | VARCHAR(32) | **pending / ai_graded / teacher_reviewed** |
| teacher_score | DOUBLE NULL | 教师复核得分（覆盖最终成绩） |
| teacher_feedback | TEXT | 教师评语 |
| reviewed_at | TIMESTAMP NULL | 复核时间 |
| created_at | TIMESTAMP | 创建时间 |

索引：`idx_exam_answers_sub (submission_id)`、`idx_exam_answers_question (question_id)`

### 题型与批改状态

| 题型值 | 含义 | 判分 |
|--------|------|------|
| multiple_choice | 选择题 | 自动 |
| judge | 判断题 | 自动 |
| fill_blank | 填空题 | 自动 |
| short_answer | 简答题（=主观题） | RAG + AI 评分 + 教师复核 |

手写图文件存 `uploads/exam_answers/`，导出 DOCX 存 `exports/`；手写图/文件下载需 Bearer 认证并做权限校验（提交人 / 任课教师 / 管理员）。

## 访问层

业务代码通过 `data/dbapi.py` 访问数据库，它是 **dbapi 兼容层**（基于 PyMySQL，保留 sqlite3 风格调用）：

```python
from data import dbapi as dbapi
from data.config import get_auth_db_path

conn = dbapi.connect(get_auth_db_path())  # → MySQL schema `ai_auth`
conn.row_factory = dbapi.Row
cur = conn.cursor()
cur.execute("SELECT * FROM users WHERE username = ?", (name,))  # ? 占位符
```

兼容特性：

| 兼容接口 | MySQL 实现 |
|-------------|-----------|
| `?` 占位符 | 自动转换为 `%s` |
| `row_factory = dbapi.Row` | 支持下标 + 列名访问 |
| `cursor.lastrowid` | `INSERT` 自增 ID |
| `PRAGMA ...` | 无操作（自动忽略） |
| `dbapi.IntegrityError` | 映射 pymysql 异常 |

## 全文检索

全文检索使用 **MySQL FULLTEXT + ngram 解析器**（支持中文）：

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

# 从 legacy 数据文件导入（一次性迁移）
python scripts/migrate_to_mysql.py --data

# 兼容旧入口
python scripts/init_databases.py
```

## 设计优势

| 优势 | 说明 |
|------|------|
| 功能隔离 | 避免数据耦合，各模块独立 schema |
| 并发能力 | MySQL InnoDB 行锁，支持多写 |
| 全文检索 | ngram FULLTEXT 原生支持中文 |
| 易于维护 | 模块化设计，单库故障不影响全局 |
| 高可用性 | 支持主从复制、备份与容灾 |
| 代码兼容 | dbapi 兼容层保留 sqlite3 风格调用 |
