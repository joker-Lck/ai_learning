# API 接口参考

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

### 资源生成

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /generate-resources | 生成学习资源 |
| GET | /list-resources | 获取资源列表 |
| POST | /save-resource | 保存资源 |
| POST | /export-resource | 导出资源 |

### 学习路径

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /plan-path | 规划学习路径 |
| POST | /update-path-progress | 更新路径进度 |

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
| POST | /advanced-search | 统一检索入口（11 种策略） |
| POST | /hyde-search | HyDE 假设性文档嵌入 |
| POST | /multi-query-search | 多查询检索 |
| POST | /rag-fusion-search | RAG-Fusion + RRF |
| POST | /graph-search | 图谱增强检索 |
| POST | /contextual-upload | 上下文分块上传 |

### 工作台

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /dashboard/stats | 工作台统计 |
| GET | /activity-logs | 活动日志 |
| GET | /learning-recommendations | 个性化学习推荐 |

## 流式接口 `/api/stream`

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | /generate-resources-real | SSE 资源生成 |
| POST | /tutor | SSE 智能辅导 |
| POST | /safety-check | 内容安全检查 |
| POST | /fact-verify | 事实验证 |

### SSE 资源生成

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
