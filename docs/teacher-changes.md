# 灵犀 · 教师端改动总结

> 版本：v1.0 | 日期：2026-10-12 | 状态：已交付

---

## 一、改动目标

在现有学生端全部功能（10 个功能面）基础上，新增**教师端**：

- **一一对应**：8 大教学模块与学生端功能对齐
- **独有新增**：班级管理（邀请码）+ 学生学情查看
- **数据边界**：老师仅查看自己班级内学生数据

---

## 二、交付清单（28 项）

### 后端（11 项）

| # | 文件 | 类型 | 阶段 | 说明 |
|---|------|------|------|------|
| 1 | `scripts/init_databases.py` | 修改 | P0 | role CHECK 扩展 + classes/class_students 表 |
| 2 | `scripts/migrate_teacher_roles.py` | 🆕 | P0 | 一次性迁移：角色统一 + 班级表 |
| 3 | `backend/schemas/models.py` | 修改 | P0 | RegisterRequest 增 role + 班级 5 模型 |
| 4 | `services/auth_service.py` | 修改 | P0 | register_user 默认 role=student |
| 5 | `backend/api/auth.py` | 修改 | P0 | 注册透传真实 role + 存量 user→student 映射 |
| 6 | `backend/api/teacher.py` | 🆕 | P1 | 22 个老师端 API |
| 7 | `backend/main.py` | 修改 | P1 | 挂载 teacher/student_class 路由 |
| 8 | `backend/dependencies.py` | 修改 | P0/P1 | teacher 权限补 class:manage/student:read/analytics:read |
| 9 | `services/class_service.py` | 🆕 | P1 | ClassService + StudentMonitorService |
| 10 | `backend/api/student_class.py` | 🆕 | P1 | 3 个学生入班 API |
| 11 | `tests/test_teacher_api.py` | 🆕 | P5 | 16 个测试用例 |

### 前端（13 项）

| # | 文件 | 类型 | 阶段 | 说明 |
|---|------|------|------|------|
| 12 | `stores/index.ts` | 修改 | P2 | isTeacher/isStudent 派生状态 |
| 13 | `lib/api.ts` | 修改 | P2 | 25 个 API 方法 + register 增 role |
| 14 | `components/modules/types.ts` | 修改 | P2 | ModuleType 扩展 + 班级类型 |
| 15 | `app/LoginContent.tsx` | 修改 | P2 | 注册角色选择 + 按角色跳转 |
| 16 | `app/teacher/page.tsx` | 🆕 | P2 | 老师端入口 |
| 17 | `components/TeacherDashboard.tsx` | 🆕 | P2 | 老师工作台外壳 |
| 18 | `middleware.ts` | 修改 | P2 | 路由角色标记 |
| 19 | `app/layout.tsx` | 修改 | P2 | metadata 更新 |
| 20 | `components/teacher/StudentMonitorView.tsx` | 🆕 | P3 | 学生列表 + 11 Tab 下钻 |
| 21 | `components/teacher/ClassAnalyticsView.tsx` | 🆕 | P3 | 班级聚合统计 + 排行 |
| 22 | `components/teacher/TeacherModuleViews.tsx` | 🆕 | P3 | 6 大教学模块视图 |
| 23 | `components/teacher/ClassModule.tsx` | 🆕 | P4 | 班级管理完整 UI |
| 24 | `components/teacher/MyClassView.tsx` | 🆕 | P4 | 学生侧「我的班级」 |

### 文档/工具（4 项）

| # | 文件 | 类型 | 阶段 | 说明 |
|---|------|------|------|------|
| 25 | `docs/teacher-guide.md` | 🆕 | P6 | 教师端使用指南 |
| 26 | `docs/api-reference-teacher.md` | 🆕 | P6 | 教师端 API 参考 |
| 27 | `docs/deployment.md` | 修改 | P6 | 部署指南增加迁移步骤 |
| 28 | `docs/README.md` | 修改 | P6 | 文档导航更新 |

---

## 三、5 项设计决策

| # | 问题 | 决定 | 实现 |
|---|------|------|------|
| 1 | 存量 11 个 `role='user'` | **升级为 `student`** | 迁移脚本 `UPDATE users SET role='student' WHERE role='user'` |
| 2 | 成绩/错题查看权限 | **老师直接可看** | 不设开关，teacher API 直接查询 |
| 3 | 老师端个人数据 | **保留课程表** | `teacherStudentCourseSchedule` 端点 |
| 4 | 班级人数上限 | **老师自设** | `max_students` 字段（NULL=不限） |
| 5 | 发布资源到班级 | **学生侧「班级资源」** | 老师可查看学生资源列表 |

---

## 四、API 端点总览

### 老师端（22 个）

```
POST   /api/teacher/classes                         创建班级
GET    /api/teacher/classes                         班级列表
GET    /api/teacher/classes/{id}                    班级详情
PUT    /api/teacher/classes/{id}                    更新班级
POST   /api/teacher/classes/{id}/reset-code         重置邀请码
POST   /api/teacher/classes/{id}/close              关闭入班
POST   /api/teacher/classes/{id}/open               开启入班
GET    /api/teacher/classes/{id}/students           学生名单
DELETE /api/teacher/classes/{id}/students/{sid}     移除学生
GET    /api/teacher/classes/{id}/overview           班级概览
GET    /api/teacher/students                        全部学生
GET    /api/teacher/students/{sid}/brief            学生摘要
GET    /api/teacher/students/{sid}/profile          学生画像
GET    /api/teacher/students/{sid}/course-schedule  学生课程表
GET    /api/teacher/students/{sid}/resources        学生资源
GET    /api/teacher/students/{sid}/learning-path    学生路径
GET    /api/teacher/students/{sid}/quiz             学生做题
GET    /api/teacher/students/{sid}/assessment       学生评估
GET    /api/teacher/students/{sid}/analytics/{m}    学情 6 指标
GET    /api/teacher/students/{sid}/activities       学生活跃度
GET    /api/teacher/students/{sid}/errors           学生错题
GET    /api/teacher/students/{sid}/grades           学生成绩
```

### 学生入班（3 个）

```
POST /api/student/join-class            邀请码入班
GET  /api/student/my-classes            我的班级
POST /api/student/leave-class/{id}      退出班级
```

---

## 五、数据库变更

### 新增表（ai_auth.db）

```sql
classes          -- 班级表（name/teacher_id/invite_code/is_open/max_students）
class_students   -- 班级-学生关联表（class_id/student_id/joined_at/status）
```

### 存量数据迁移

| 项目 | 迁移前 | 迁移后 |
|------|--------|--------|
| role 值 | 11 个 `user` | 11 个 `student` |
| role CHECK | `('user','admin','guest')` | `('user','admin','guest','teacher','student')` |
| classes 表 | 不存在 | 已创建 |
| class_students 表 | 不存在 | 已创建 |

备份文件：`data/databases/ai_auth.db.bak_<timestamp>`

---

## 六、知识图谱

| 项目 | 变更前 | 变更后 |
|------|--------|--------|
| 节点 | 255 | **298** |
| 边 | 99 | **340** |
| Teacher 相关节点 | 0 | **24** |
| graph-data.json 乱码 | 有 | **已修复** |

新增节点包含：`classes`/`class_students` 表、`class_service`、22 个 endpoint、5 个前端组件、`api:teacher`/`api:student_class`。

---

## 七、测试报告

### 新增测试（16 个）

| 测试类 | 数量 | 覆盖 |
|--------|------|------|
| TestClassService | 9 | 班级 CRUD / 师生关系校验 |
| TestStudentMonitorService | 4 | 学情代查（空数据边界） |
| TestRoleMigration | 3 | 角色迁移 / 表存在 / CHECK 约束 |

### 回归结果

| 项目 | 结果 |
|------|------|
| 新增测试 | 16/16 ✅ |
| 存量测试 | 53/53 ✅ |
| 全量测试 | **69/69 ✅** |
| TypeScript | **0 errors** |
| 学生端端点 | 10/10 完好 |
| 总路由数 | 142（新增 25） |

---

## 八、部署注意

1. **已有数据库**需执行一次迁移：
   ```bash
   python scripts/migrate_teacher_roles.py
   ```
2. 迁移脚本自动备份 `ai_auth.db`
3. 新环境直接 `python scripts/init_databases.py` 即可
4. 前端无需额外配置，`npm run dev` / `npm run build` 正常
