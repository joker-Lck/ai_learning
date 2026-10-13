# 教师端 API 参考

> 教师端 REST API 接口文档 — 班级管理 + 学情代查 + 学生入班

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

## 四、错误码汇总

| HTTP 状态码 | 场景 |
|------------|------|
| 200 | 操作成功 |
| 400 | 请求参数无效（如无效 metric） |
| 401 | 未登录 / Token 过期 |
| 403 | 权限不足（非老师角色 / 学生不在班级内） |
| 404 | 班级不存在 |
