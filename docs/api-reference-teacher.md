# 教师端 API 参考

> 教师端 REST API 接口文档 — 班级管理 + 学情代查 + 学生入班 + AI 出题/组卷 + 主观题批改
>
> **版本**：v9.1.0

---

## 认证

所有教师端接口需要 **Bearer Token** 认证，且角色为 `teacher` 或 `admin`。

```http
Authorization: Bearer <jwt_token>
```

**鉴权失败响应**：
```json
{ "detail": "权限不足: 需要 teacher 及以上角色" }  // 403
{ "detail": "请先登录" }  // 401
```

---

## 一、班级管理（`/api/teacher/classes`）

### 创建班级

```http
POST /api/teacher/classes
```

**请求体**：
```json
{
  "name": "高一(3)班",
  "subject": "数学",
  "grade_level": "高一",
  "semester": "2026春",
  "description": "实验班",
  "max_students": 50
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 班级名称（1-50字符） |
| subject | string | | 学科 |
| grade_level | string | | 年级 |
| semester | string | | 学期 |
| description | string | | 备注 |
| max_students | int\|null | | 人数上限（1-500，null=不限） |

**响应**：
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "success": true,
    "class_id": 1,
    "invite_code": "A1B2C3"
  }
}
```

### 获取班级列表

```http
GET /api/teacher/classes
```

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "高一(3)班",
      "teacher_id": 5,
      "subject": "数学",
      "invite_code": "A1B2C3",
      "is_open": 1,
      "max_students": 50,
      "student_count": 32,
      "created_at": "2026-10-12 10:00:00"
    }
  ]
}
```

### 获取班级详情

```http
GET /api/teacher/classes/{class_id}
```

### 更新班级

```http
PUT /api/teacher/classes/{class_id}
```

**请求体**（部分字段即可）：
```json
{ "name": "新班名", "max_students": 60 }
```

### 重置邀请码

```http
POST /api/teacher/classes/{class_id}/reset-code
```

**响应**：
```json
{ "success": true, "data": { "invite_code": "X7Y8Z9" } }
```

### 关闭入班

```http
POST /api/teacher/classes/{class_id}/close
```

### 开启入班

```http
POST /api/teacher/classes/{class_id}/open
```

### 学生名单

```http
GET /api/teacher/classes/{class_id}/students
```

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "id": 15,
      "username": "张三",
      "email": "zhang@example.com",
      "joined_at": "2026-10-12 11:00:00",
      "status": "active"
    }
  ]
}
```

### 移除学生

```http
DELETE /api/teacher/classes/{class_id}/students/{sid}
```

### 班级概览

```http
GET /api/teacher/classes/{class_id}/overview
```

---

## 二、学情代查（`/api/teacher/students`）

> **权限校验**：所有接口验证目标学生在当前老师的任一班级内，否则返回 403。

### 全部学生列表

```http
GET /api/teacher/students
```

### 学生摘要

```http
GET /api/teacher/students/{sid}/brief
```

**响应**：
```json
{
  "success": true,
  "data": {
    "user_id": 15,
    "profile_scores": { "knowledge_base": 4, "cognitive_style": 3 },
    "resource_count": 25,
    "quiz_count": 12,
    "quiz_avg_score": 82.5,
    "study_seconds": 72000
  }
}
```

### 学生画像

```http
GET /api/teacher/students/{sid}/profile
```

### 学生课程表

```http
GET /api/teacher/students/{sid}/course-schedule
```

### 学生学习资源

```http
GET /api/teacher/students/{sid}/resources
```

### 学生学习路径

```http
GET /api/teacher/students/{sid}/learning-path
```

### 学生做题数据

```http
GET /api/teacher/students/{sid}/quiz
```

**响应**：
```json
{
  "success": true,
  "data": {
    "sessions": [{ "subject": "数学", "score": 85, "correct_count": 17, "total_questions": 20 }],
    "stats": { "c": 12, "avg_score": 82.5 },
    "weak_topics": [{ "knowledge_point": "二次函数", "accuracy": 45.5 }]
  }
}
```

### 学生评估报告

```http
GET /api/teacher/students/{sid}/assessment
```

### 学生学情指标

```http
GET /api/teacher/students/{sid}/analytics/{metric}
```

**metric 可选值**：
| 值 | 说明 |
|----|------|
| overview | 总览统计 |
| subject-breakdown | 学科分布 |
| quiz-trend | 做题趋势 |
| study-trend | 学习趋势 |
| knowledge-mastery | 知识点掌握度 |
| weekly-report | 周报 |

### 学生活跃度

```http
GET /api/teacher/students/{sid}/activities
```

### 学生错题本

```http
GET /api/teacher/students/{sid}/errors
```

### 学生成绩

```http
GET /api/teacher/students/{sid}/grades
```

---

## 三、学生入班（`/api/student`）

### 邀请码入班

```http
POST /api/student/join-class
```

**请求体**：
```json
{ "invite_code": "A1B2C3" }
```

**响应**：
```json
{ "success": true, "message": "已加入「高一(3)班」", "data": { "class_id": 1 } }
```

**错误场景**：
| 错误信息 | 说明 |
|---------|------|
| 邀请码无效 | 6 位码不存在 |
| 该班级已关闭入班 | 老师已关闭 |
| 您已在该班级中 | 重复加入 |
| 班级人数已满 | 达到 max_students 上限 |

### 我的班级

```http
GET /api/student/my-classes
```

### 退出班级

```http
POST /api/student/leave-class/{class_id}
```

---

## 四、AI 出题/组卷 + 主观题批改（`/api/exam`，v9.1.0 新增）

> 全部挂载于 `/api/exam`，共 **26 个端点**。教师端（A/B/C 组）需 `teacher` 或 `admin` 角色；学生端（D 组）登录即可。完整条目见 [api-reference.md](api-reference.md#考试批改接口-apiexamv910-新增)。

### 4.1 端点总览

#### A. 组卷与试卷管理（teacher）

```http
POST   /api/exam/papers/generate              AI 组卷（仅预览，不落库）
POST   /api/exam/papers                       保存试卷
GET    /api/exam/papers                       我的试卷列表（?subject=&paper_type=）
GET    /api/exam/papers/{id}                  试卷详情（含题目）
PUT    /api/exam/papers/{id}                  更新试卷（含题目整体替换）
DELETE /api/exam/papers/{id}                  删除试卷
POST   /api/exam/papers/{id}/export           导出可打印 DOCX（试题卷+答案解析）
GET    /api/exam/download/{filename}          下载导出文件（防目录穿越）
```

#### B. 发布到班级（teacher）

```http
POST   /api/exam/papers/{id}/assign           发布试卷到班级
GET    /api/exam/assignments                  我发布的作业/考试列表
GET    /api/exam/assignments/{id}             发布详情（含试卷题目）
POST   /api/exam/assignments/{id}/close       截止收卷
```

#### C. 提交与批改（teacher 为主）

```http
POST   /api/exam/submissions                        创建/获取作答记录
GET    /api/exam/assignments/{id}/submissions       提交列表（批改进度一览）
GET    /api/exam/submissions/{id}                   提交详情（逐题作答+批改结果）
POST   /api/exam/submissions/{id}/answers/{qid}/image?ocr=   上传手写图+自动OCR
GET    /api/exam/answers/{id}/image                 查看手写答案图片（权限校验）
POST   /api/exam/answers/{id}/ocr                   执行/重跑手写识别
PUT    /api/exam/answers/{id}                       修改作答文本（OCR修正）
POST   /api/exam/answers/{id}/grade                 AI 批改单题
POST   /api/exam/submissions/{id}/grade             AI 批改整卷
PUT    /api/exam/answers/{id}/review                教师复核改分（最终分以教师为准）
GET    /api/exam/assignments/{id}/report            班级批改报告
```

#### D. 学生端（登录即可）

```http
GET    /api/exam/my-assignments                 我的班级作业列表
GET    /api/exam/assignments/{id}/paper         作业题目（脱敏不含答案，须在班级内）
POST   /api/exam/assignments/{id}/submit        提交作答（文本答案）
```

学生也可 `POST /api/exam/submissions` 建自己的作答记录，并上传手写图。

### 4.2 AI 组卷

```http
POST /api/exam/papers/generate
```

**请求体**：
```json
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
| knowledge_points | string[] | | 知识点 |
| difficulty | string | | easy/medium/hard/mixed |
| paper_type | string | | practice / exam |
| total_score | number | | 总分，按题型权重折算每题分值 |
| duration_minutes | int | | 时长（分钟） |
| use_bank | bool | | 题库复用（≤50% 来自题库） |
| question_spec | object | | 各题型数量（默认 5/3/3/2） |

**响应**：
```json
{
  "success": true,
  "data": {
    "paper": { "title": "二叉树练习卷", "subject": "数据结构", "total_score": 100, "difficulty": "medium" },
    "questions": [
      {
        "q_index": 1,
        "question_type": "multiple_choice",
        "question_text": "……",
        "options": ["A. …", "B. …"],
        "correct_answer": "A",
        "reference_answer": "",
        "scoring_points": [],
        "explanation": "……",
        "knowledge_point": "二叉树遍历",
        "difficulty": "medium",
        "score": 4.0
      }
    ],
    "reused_count": 4,
    "generated_count": 9
  }
}
```

- 取材链路：RAG 知识库取材 → 题库复用（≤50%）→ LLM 生成 → 分值折算
- **仅预览不落库**；确认后 `POST /api/exam/papers` 保存
- LLM 失败自动兜底模板题，仍返回 `success=true`

### 4.3 发布与批改

**发布到班级**

```http
POST /api/exam/papers/{paper_id}/assign
{
  "class_id": 1,
  "due_at": "2026-11-01 23:59:00",
  "title": "第3周作业",
  "allow_late": true
}
```

**上传手写答案**（multipart/form-data）

```http
POST /api/exam/submissions/{submission_id}/answers/{question_id}/image?ocr=true
Content-Type: multipart/form-data

file: <jpg|png|bmp|webp，≤15MB>
```

响应：
```json
{
  "success": true,
  "data": {
    "answer_id": 12,
    "ocr_text": "……",
    "ocr_confidence": 0.91,
    "ocr_engine": "rapidocr",
    "segments": [{"text": "……", "confidence": 0.93}],
    "low_confidence": false
  }
}
```

- 识别链路：手写增强预处理 → **RapidOCR/PP-OCRv6(onnxruntime)** 主力 → 置信度 < 0.55 或无文本切 MiMo 视觉手写 prompt 兜底 → 择优
- 依赖：`rapidocr` + `onnxruntime`（见 [deployment.md](deployment.md)）
- 前端下载手写图/文件须走 blob + Bearer（`<img src>`/`window.open` 带不了认证头会 401）

**单题 AI 批改**

```http
POST /api/exam/answers/{answer_id}/grade
```

- 客观题（multiple_choice/judge/fill_blank）：自动判分
- 主观题（short_answer）：RAG 检索评分依据（`rag_evidence`）→ LLM 评分（分数/评语/知识点命中缺失/改进建议）→ 关键词兜底

响应：
```json
{
  "success": true,
  "data": {
    "ai_score": 8.5,
    "score": 8.5,
    "feedback": "……",
    "knowledge_hits": ["二叉树遍历"],
    "rag_evidence": "……",
    "grade_status": "ai_graded"
  }
}
```

**教师复核改分**（最终成绩以教师为准）

```http
PUT /api/exam/answers/{answer_id}/review
{ "teacher_score": 8.5, "teacher_feedback": "思路正确，步骤不完整" }
```

**班级批改报告**

```http
GET /api/exam/assignments/{assignment_id}/report
```

响应 `data`：得分分布 / 逐题统计 / 薄弱知识点 / 排名。

### 4.4 题型与批改状态

| 题型 | 值 | 判分方式 |
|------|-----|---------|
| 选择题 | multiple_choice | 自动判分 |
| 判断题 | judge | 自动判分 |
| 填空题 | fill_blank | 自动判分 |
| 简答题 | short_answer（=主观题） | RAG + AI 评分 + 教师复核 |

| grade_status | 说明 |
|--------------|------|
| pending | 未批改 |
| ai_graded | AI 已批改 |
| teacher_reviewed | 教师已复核 |

---

## 五、错误码汇总

| HTTP 状态码 | 场景 |
|------------|------|
| 200 | 操作成功 |
| 400 | 请求参数无效（如无效 metric） |
| 401 | 未登录 / Token 过期 |
| 403 | 权限不足（非老师角色 / 学生不在班级内） |
| 404 | 班级不存在 |
