# API 接口参考

> **版本**：v9.1.0

## 接口规范

- **协议**：RESTful HTTP + SSE 流式
- **认证**：Bearer Token（JWT HS256，24h 有效期）
- **限流**：全局 120 次/分钟，登录 10 次/分钟，注册 5 次/分钟
- **请求校验**：全部端点使用 Pydantic 模型验证
- **响应格式**：`{ "success": bool, "message": string, "data": any }`

## 认证接口 `/api/auth`

| 方法 | 端点 | 功能 | 认证 | 限流 |
|------|------|------|------|------|
| POST | /login | 用户登录 | 否 | 10/min |
| POST | /register | 用户注册 | 否 | 5/min |
| POST | /guest | 游客模式 | 否 | 120/min |
| GET | /me | 获取当前用户 | 是 | 120/min |
| POST | /change-password | 修改密码 | 是 | 120/min |

### 登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "Test@123"
}
```

响应：
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "id": 1, "username": "testuser", "role": "student" }
}
```

## 智能体接口 `/api/agent`

### 学生画像

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /build-profile | 构建学生画像 |
| GET | /get-profile | 获取画像 |
| POST | /update-profile-field | 更新画像字段 |
| POST | /evaluate-profile | AI 评定画像（6维度雷达图分数） |

### 学生数据管理

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /save-course-schedule | 保存课程表 |
| GET | /get-course-schedule | 获取课程表 |
| GET | /list-semesters | 获取学期列表 |
| POST | /save-grades | 保存成绩 |
| GET | /get-grades | 获取成绩 |
| POST | /save-error-note | 保存错题 |
| GET | /get-error-notes | 获取错题列表 |
| POST | /update-error-mastery | 更新错题掌握度 |
| POST | /delete-error-note | 删除错题 |
| POST | /generate-study-plan | 生成学习计划 |
| GET | /get-study-plans | 获取学习计划 |

### 学习资源

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /generate-resources | 生成学习资源 |
| GET | /list-resources | 获取资源列表 |
| POST | /save-resource | 保存资源 |
| POST | /export-resource | 导出资源 |

### Bilibili 视频资源

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /bilibili/search | 搜索 Bilibili 视频 |
| GET | /bilibili/recommend | 获取推荐视频 |
| GET | /bilibili/cover | 封面图片代理 |

### 图书资源（国家图书馆 + 鸠摩搜书）

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /books/search | 搜索图书 |
| GET | /books/recommend | 获取推荐图书 |
| GET | /books/cover | 封面图片代理 |

### 学习路径与规划

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /plan-path | 规划学习路径 |
| POST | /update-path-progress | 更新路径进度 |
| POST | /generate-study-plan | 生成学习计划 |
| GET | /get-study-plans | 获取历史计划 |

### 学习行为追踪（前端 localStorage）

| 活动类型 | 说明 | 存储字段 |
|----------|------|----------|
| video_view | 视频浏览记录 | type, action, category, time |
| book_view | 图书查阅记录 | type, action, category, time, source |

### 智能辅导

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /tutor | 智能辅导答疑 |

### 效果评估

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /assess | 学习效果评估 |
| POST | /comprehensive-plan | 综合学习计划 |

### 文件导入

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /import-courses-from-file | 导入课程表（图片/PDF/Excel） |
| POST | /import-grades-from-file | 导入成绩（Excel/CSV） |
| POST | /import-errors-from-file | 导入错题（CSV） |

### RAG 知识库

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /upload-to-rag | 上传文档到知识库 |
| GET | /rag-documents | 获取知识库文档列表 |
| POST | /analyze-documents | 分析文档 |

### 高级检索

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /advanced-search | 统一检索入口（12 种策略） |
| POST | /hyde-search | HyDE 假设性文档嵌入 |
| POST | /multi-query-search | 多查询检索 |
| POST | /rag-fusion-search | RAG-Fusion + RRF |
| POST | /graph-search | 图谱增强检索 |
| POST | /contextual-upload | 上下文分块上传 |

### 自学习闭环

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /feedback | 提交用户反馈（点赞/点踩/评分/评论） |
| GET | /learning-stats | 获取自学习统计 |
| POST | /trigger-learning | 手动触发自学习循环 |

### RAGAS 评估（取代旧检索评测）

基于 [RAGAS](https://github.com/explodinggradients/ragas) 的 EduRAG 端到端评估。

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /eval-rag/datasets | 获取评估数据集列表 |
| POST | /eval-rag/datasets | 创建评估数据集 |
| POST | /eval-rag/samples | 添加评估样本（user_input/reference） |
| POST | /eval-rag/run | 运行 RAGAS 评估 |
| GET | /eval-rag/history | 获取评估历史 |
| GET | /eval-rag/compare | 对比策略指标 |

**评估指标**

| 指标 | 说明 | 需参考答案 |
|------|------|-----------|
| faithfulness | 答案是否忠实于检索上下文 | 否 |
| context_precision | 检索上下文精确度 | 是 |
| context_recall | 检索上下文召回率 | 是 |
| answer_relevancy | 答案与问题相关性 | 否 |
| factual_correctness | 事实正确性 | 是 |

**请求示例**

```bash
POST /api/agent/eval-rag/datasets
{"name": "edu_eval", "description": "EduRAG 评估集"}

POST /api/agent/eval-rag/samples
{
  "dataset_id": 1,
  "user_input": "什么是二叉树？",
  "reference": "二叉树是每个节点最多有两个子节点的树形数据结构。",
  "reference_contexts": ["二叉树是树形数据结构……"]
}

POST /api/agent/eval-rag/run
{"dataset_id": 1, "strategy": "hybrid", "top_k": 5}
```

**响应示例**

```json
{
  "success": true,
  "framework": "ragas",
  "strategy": "hybrid",
  "metrics": {
    "faithfulness": 1.0,
    "context_precision": 1.0,
    "context_recall": 1.0,
    "answer_relevancy": 0.773,
    "factual_correctness": 1.0
  },
  "total_samples": 3
}
```

结果持久化至 `retrieval_eval` 库 `eval_runs` 表。

### Multi-Hop / ReAct（v8.0 新增）

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /multi-hop-search | Multi-Hop 多跳推理检索（含可视化数据） |
| POST | /react-search | ReAct 推理-检索交替检索 |

### Milvus 索引（v8.0 新增）

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /faiss-info | 获取 Milvus 索引信息 |

### Agent 可视化（v8.0 新增）

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /agent-status/{session_id} | 获取 Agent 协作状态 |
| GET | /agent-status-stream/{session_id} | SSE 实时推送 Agent 状态 |

### 工作台

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /dashboard/stats | 工作台统计 |
| GET | /activity-logs | 活动日志 |
| GET | /learning-recommendations | 个性化学习推荐（v8.1 升级：专业学习规划师） |
| GET | /review-due | 待复习错题（v8.5 升级：SM-2 间隔重复调度） |
| GET | /review-reminder | 综合学习提醒（v8.5 升级：基于 next_review 调度） |
| POST | /review-submit | 提交复习结果（v8.5 新增，更新间隔重复调度） |

### 在线做题

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /quiz/start | 开始答题会话 |
| POST | /quiz/submit | 提交单题答案（v8.5 升级：答错自动保存错题本） |
| POST | /quiz/finish | 结束答题会话 |
| GET | /quiz/history | 答题历史 |
| GET | /quiz/stats | 答题统计 |
| GET | /quiz/weak-topics | 薄弱知识点 |
| POST | /quiz/adaptive | 自适应出题（v8.5 升级：题库复用，最多60%来自题库） |
| POST | /quiz/import-bank | 导入题库文件 |

## 流式接口 `/api/stream`

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /generate-resources-real | SSE 学习资源 |
| POST | /tutor | SSE 智能辅导 |
| POST | /quiz/adaptive | SSE 自适应出题（v8.5 新增） |
| POST | /plan-path | SSE 学习路径生成（v8.5 新增） |
| POST | /check-content-safety | 内容安全检查 |
| POST | /verify-fact | 事实验证 |
| POST | /add-citations | 添加引用 |
| POST | /cross-validate | 交叉验证 |

### SSE 学习资源

```http
GET /api/stream/generate-resources-real?subject=数据结构&topic=二叉树&resource_types=document,mindmap&difficulty=intermediate
Authorization: Bearer <token>
Accept: text/event-stream
```

SSE 事件格式：
```
data: {"type": "progress", "stage": "analyzing", "message": "正在分析需求..."}

data: {"type": "resource", "resource_type": "document", "content": "..."}

data: {"type": "complete", "total_resources": 2, "message": "生成完成"}
```

## 系统接口

| 方法 | 端点 | 功能 | 认证 |
|------|------|------|------|
| GET | /health | 健康检查 | 否 |
| GET | /info | 系统信息 | 否 |

## 考试/批改接口 `/api/exam`（v9.1.0 新增）

教师 AI 出题/组卷 + 主观题批改（手写识别 + RAG 评分 + 教师复核 + 班级报告）。
请求/响应统一 `{ "success": bool, "message": string, "data": any }`。
权限列：**teacher** = `require_role("teacher")`；**登录** = `require_auth`（学生可建自己的作答/上传手写图）。

### A. AI 组卷与试卷管理（teacher）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | /papers/generate | AI 组卷（仅预览，不落库） | teacher |
| POST | /papers | 保存试卷 | teacher |
| GET | /papers | 我的试卷列表（`?subject=&paper_type=`） | teacher |
| GET | /papers/{id} | 试卷详情（含题目） | teacher |
| PUT | /papers/{id} | 更新试卷（含题目整体替换） | teacher |
| DELETE | /papers/{id} | 删除试卷 | teacher |
| POST | /papers/{id}/export | 导出可打印 DOCX（试题卷+答案解析分页） | teacher |
| GET | /download/{filename} | 下载导出文件（防目录穿越） | 登录 |

**AI 组卷请求**

```http
POST /api/exam/papers/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "subject": "数据结构",
  "grade": "大一",
  "topic": "二叉树",
  "knowledge_points": ["二叉树遍历", "平衡树"],
  "difficulty": "medium",
  "paper_type": "practice",
  "title": "二叉树练习卷",
  "total_score": 100,
  "duration_minutes": 60,
  "use_bank": true,
  "question_spec": { "multiple_choice": 5, "judge": 3, "fill_blank": 3, "short_answer": 2 }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subject | string | | 学科（默认「综合」） |
| grade | string | | 年级 |
| topic | string | | 主题 |
| knowledge_points | string[] | | 知识点列表 |
| difficulty | string | | easy/medium/hard/mixed（默认 medium） |
| paper_type | string | | practice（练习卷）/ exam（考试卷） |
| title | string | | 试卷标题（缺省自动生成） |
| total_score | number | | 总分（默认 100，按题型权重折算每题分值） |
| duration_minutes | int | | 考试时长（默认 60） |
| use_bank | bool | | 是否复用题库（≤50% 来自题库，默认 true） |
| question_spec | object | | 各题型数量（默认 选择5/判断3/填空3/简答2） |

响应 `data`：`{ paper: {...}, questions: [{question_type, question_text, options, correct_answer, reference_answer, scoring_points, explanation, knowledge_point, difficulty, score}], reused_count, generated_count }`。
LLM 失败时自动兜底模板题（`_fallback_questions`），返回 `success=true` 且标注兜底来源。

**保存试卷请求**（`POST /papers`）：与组卷响应中的 `paper` + `questions` 结构一致；`teacher_id` 由 Token 注入。
**导出**（`POST /papers/{id}/export`）：返回 `{filename}`，文件存 `exports/`，再经 `GET /download/{filename}` 下载。

### B. 发布到班级（teacher）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | /papers/{id}/assign | 发布试卷到班级 | teacher |
| GET | /assignments | 我发布的作业/考试列表 | teacher |
| GET | /assignments/{id} | 发布详情（含试卷题目） | teacher |
| POST | /assignments/{id}/close | 截止收卷 | teacher |

**发布请求**

```http
POST /api/exam/papers/{paper_id}/assign
{ "class_id": 1, "due_at": "2026-11-01 23:59:00", "title": "第3周作业", "allow_late": true }
```

### C. 提交与批改（teacher 为主）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| POST | /submissions | 创建/获取作答记录（教师可代建，学生只能建自己的） | 登录 |
| GET | /assignments/{id}/submissions | 提交列表（批改进度一览） | teacher |
| GET | /submissions/{id} | 提交详情（逐题作答 + 批改结果） | 登录 |
| POST | /submissions/{id}/answers/{qid}/image?ocr=true | 上传手写图 + 自动 OCR | 登录 |
| GET | /answers/{id}/image | 查看手写答案图片（权限校验） | 登录 |
| POST | /answers/{id}/ocr | 对已上传手写图执行/重跑识别 | 登录 |
| PUT | /answers/{id} | 修改作答文本（OCR 识别修正） | 登录 |
| POST | /answers/{id}/grade | AI 批改单题 | teacher |
| POST | /submissions/{id}/grade | AI 批改整卷 | teacher |
| PUT | /answers/{id}/review | 教师复核改分（最终成绩以教师为准） | teacher |
| GET | /assignments/{id}/report | 班级批改报告 | teacher |

**手写图上传**（multipart/form-data，字段 `file`，jpg/png/bmp/webp，≤15MB；`?ocr=true` 上传后自动识别）
响应 `data`：`{ answer_id, ocr_text, ocr_confidence, ocr_engine: "rapidocr"|"vision", segments, low_confidence }`。
识别链路：手写增强预处理 → RapidOCR/PP-OCRv6(onnxruntime) 主力 → 置信度 < 0.55 或无文本时切 MiMo 视觉手写 prompt 兜底 → 择优返回。

**单题批改**（`POST /answers/{id}/grade`）：客观题（multiple_choice/judge/fill_blank）自动判分；主观题（short_answer）流程为 RAG 检索评分依据（`rag_evidence`）→ LLM 评分 → 关键词兜底。
响应 `data`：`{ ai_score, score, feedback, knowledge_hits, rag_evidence, grade_status }`。

**教师复核**（`PUT /answers/{id}/review`）

```json
{ "teacher_score": 8.5, "teacher_feedback": "思路正确，步骤不完整" }
```

**班级报告**（`GET /assignments/{id}/report`）响应 `data`：得分分布 / 逐题统计 / 薄弱知识点 / 排名。

### D. 学生端（登录即可）

| 方法 | 端点 | 功能 | 权限 |
|------|------|------|------|
| GET | /my-assignments | 我的班级作业列表 | 登录 |
| GET | /assignments/{id}/paper | 获取作业题目（脱敏，不含答案） | 登录（须在班级内） |
| POST | /assignments/{id}/submit | 提交作答（文本答案） | 登录 |

学生也可 `POST /submissions` 建自己的作答记录，并上传手写图（同 C 组端点）。
`POST /assignments/{id}/submit` 请求体：`{ "answers": [{ "question_id": 1, "answer_text": "…" }] }`。

**数据表**：`ai_assessments` 库 `exam_papers` / `exam_questions` / `exam_assignments` / `exam_submissions` / `exam_answers`（详见 [database.md](database.md)）。
**相关文档**：教师操作见 [teacher-guide.md](teacher-guide.md)，教师端 API 明细见 [api-reference-teacher.md](api-reference-teacher.md)。

## 协同学习接口 `/api/collaboration`（v8.0 新增）

### 小组管理

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /create-group | 创建学习小组 |
| POST | /join-group | 通过邀请码加入小组 |
| POST | /leave-group | 退出小组 |
| GET | /my-groups | 获取我的小组列表 |
| GET | /group/{group_id} | 获取小组详情 |

### 资源共享

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /share-resource | 共享资源到小组 |
| GET | /shared-resources/{group_id} | 获取小组共享资源 |

### 学习动态

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /activities/{group_id} | 获取小组学习动态 |

### 互评

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /review | 添加互评 |

### 进度对比

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /learning-stats/{group_id} | 获取小组学习统计 |
