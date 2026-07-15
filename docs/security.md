# 安全机制

## 认证与授权

### JWT 认证

| 特性 | 说明 |
|------|------|
| 算法 | HS256 |
| 有效期 | 24 小时 |
| 密钥校验 | 启动时强制校验 JWT_SECRET 环境变量 |
| Token 格式 | `Authorization: Bearer <token>` |
| 游客模式 | 支持，user_id=0，role=guest |

### 认证流程

```
1. 用户登录 → POST /api/auth/login
2. 服务端验证密码（bcrypt 哈希）
3. 生成 JWT Token（含 user_id, role, exp）
4. 返回 Token 给客户端
5. 客户端后续请求携带 Token
6. 服务端验证 Token 有效性
```

## 速率限制

| 端点 | 限制 | 说明 |
|------|------|------|
| `/api/auth/register` | 5 次/分钟 | 防止批量注册 |
| `/api/auth/login` | 10 次/分钟 | 防止暴力破解 |
| 其他 API | 120 次/分钟 | 全局限流 |
| AI 生成端点 | 独立限流 | 防止资源滥用 |

### 实现

使用 `slowapi` 库，基于客户端 IP 地址限流。

## 输入校验

| 校验方式 | 说明 |
|---------|------|
| Pydantic 模型 | 全部端点使用 Pydantic 验证请求参数 |
| 类型检查 | 自动拒绝类型不匹配的参数 |
| 长度限制 | 超长输入自动截断或拒绝 |
| SQL 注入防护 | 全部使用参数化查询 |

## HTTP 安全头

| 安全头 | 值 | 作用 |
|--------|-----|------|
| X-Content-Type-Options | nosniff | 防 MIME 嗅探 |
| X-Frame-Options | DENY | 防 Clickjacking |
| X-XSS-Protection | 1; mode=block | 防 XSS |
| Referrer-Policy | strict-origin-when-cross-origin | 控制 Referer |
| Strict-Transport-Security | max-age=31536000 | 强制 HTTPS |

## CORS 配置

通过 `ALLOWED_ORIGINS` 环境变量配置白名单，默认允许 `localhost:3000`。

## 内容安全

### 敏感词检测

- **技术**：AC 自动机（Aho-Corasick）
- **词库**：127 条敏感词（`config/sensitive_words.json`）
- **复杂度**：O(n) 一次扫描
- **热更新**：支持外部 JSON 配置热更新

### 8 类敏感词覆盖

| 类别 | 示例 |
|------|------|
| 暴力 | 暴力行为描述 |
| 色情 | 色情内容描述 |
| 歧视 | 种族/性别歧视 |
| 违法 | 违法指导内容 |
| 虚假信息 | 明显错误知识点 |
| 仇恨言论 | 仇恨煽动 |
| 商业推广 | 广告推销 |
| 学术不端 | 代写/抄袭暗示 |

## 防幻觉机制

三层防护：

1. **RAG 优先检索**：回答前先检索知识库
2. **事实核查验证**：交叉验证关键事实
3. **引用标注溯源**：标注信息来源

```
confidence = rag_similarity × 0.6 + fact_check_score × 0.4
verified = confidence ≥ 0.7
```

## 异常处理体系

系统定义 8 种业务异常，实现分层异常处理：

| 异常类 | HTTP 状态码 | 用途 |
|--------|-----------|------|
| ValidationError | 400 | 请求参数校验失败 |
| AuthenticationError | 401 | 认证失败 |
| AuthorizationError | 403 | 权限不足 |
| RateLimitError | 429 | 请求过于频繁 |
| DatabaseError | 500 | 数据库操作异常 |
| AIServiceError | 502 | AI 服务调用失败 |
| ResourceGenerationError | 500 | 资源生成异常 |
| AppException | 可配置 | 业务基础异常 |

## 源文件

| 文件 | 说明 |
|------|------|
| `backend/dependencies.py` | JWT 认证、权限校验 |
| `backend/exceptions.py` | 自定义异常体系 |
| `services/content_safety_service.py` | 内容安全服务（AC 自动机 + 防幻觉） |
| `config/sensitive_words.json` | 敏感词库 |
