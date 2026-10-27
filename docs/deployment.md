# 部署指南

> **版本**：v9.1.0

## 方式一：本地开发

### 环境要求

- Python 3.8+
- Node.js 18+
- MySQL 8.0+
- npm 或 yarn

### 快速配置

```bash
# 一键配置环境
setup.bat
```

### 手动配置

```bash
# 1. 安装后端依赖
pip install -r backend/requirements.txt

# 2. 安装手写识别依赖（v9.1.0 主观题批改）
pip install rapidocr onnxruntime

# 3. 安装前端依赖
cd frontend && npm install && cd ..

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 MiMo API 配置 + MySQL 连接配置

# 5. 初始化数据库（9 个 MySQL schema，含 exam 表）
python scripts/migrate_to_mysql.py --schema

# 6. 从 legacy 数据文件导入（一次性迁移，新环境可跳过）
python scripts/migrate_to_mysql.py --data

# 7. 执行老师端迁移（旧环境已有数据库时执行一次）
python scripts/migrate_teacher_roles.py

# 8. 创建管理员账户
python scripts/init_admin.py
```

> 兼容旧入口：`python scripts/init_databases.py` 等价于 `migrate_to_mysql.py --schema`。

### 启动服务

```bash
# 方式1: 一键启动 (Windows)
01_运行启动\启动.bat

# 方式2: 手动启动
# 终端1 - 后端
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 终端2 - 前端
cd frontend && npm run dev
```

### 访问地址

- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs（DEBUG 模式）
- 默认账号：admin / admin123

---

## 方式二：Docker 部署

### 使用 docker-compose

```bash
# 一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### Docker 镜像

| 镜像 | 说明 |
|------|------|
| backend | FastAPI 后端，非 root 用户运行 |
| frontend | Next.js 前端，standalone 模式 |

### 健康检查

容器级别健康检查，自动重启：
- 后端：`/api/health`
- 前端：HTTP 200 检查

---

## 方式三：PyInstaller + NSIS 打包

### 打包流程

```
1. 构建前端 (npm run build)
   ↓
2. 下载便携 Node.js；安装 MySQL 8.0
   ↓
3. PyInstaller 打包后端为 EXE
   ↓
4. 组装分发目录 (dist/AI学习智能体/)
   ↓
5. NSIS 编译安装程序 (AI学习智能体_Setup.exe)
```

### 使用构建脚本

```bash
# 一键构建
python 02_打包构建/build.py

# 编译 NSIS 安装程序
makensis 02_打包构建/installer.nsi
```

### 生成文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `AI学习智能体_Setup.exe` | ~340 MB | 完整安装程序 |
| `dist/AI学习智能体/` | ~1.2 GB | 免安装版本 |

### 安装包特性

- 标准 Windows 安装界面
- 桌面快捷方式（可选）
- 开始菜单程序组
- 注册表写入（支持卸载）
- 环境检测（端口/服务状态）
- 一键启动

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| JWT_SECRET | JWT 签名密钥（必须配置） | 必填 |
| DEBUG | 调试模式 | false |
| APP_VERSION | 应用版本 | 9.1.0 |
| ALLOWED_ORIGINS | CORS 白名单 | localhost:3000 |
| MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD | MySQL 8.0 连接（9 个 schema） | 127.0.0.1:3306/root |
| MIMO_API_KEY | MiMo API 密钥 | 必填 |
| MIMO_BASE_URL | MiMo API 地址 | https://api.xiaomimimo.com/v1 |
| MIMO_MODEL | 推理模型 | mimo-v2.5-pro |
| MIMO_VISION_MODEL | 视觉模型 | mimo-v2.5 |
| MIMO_IMAGE_MODEL | 图片生成模型 | mimo-image |
| MIMO_TTS_MODEL | 语音合成模型 | mimo-tts |
| LOG_LEVEL | 日志级别 | INFO |
| MAX_UPLOAD_SIZE | 上传限制(MB) | 50 |

## 依赖说明（v9.1.0 新增）

| 依赖 | 用途 |
|------|------|
| `rapidocr` | 手写答案识别主力引擎（PP-OCRv6） |
| `onnxruntime` | RapidOCR 推理运行时 |

> 手写识别链路：增强预处理 → RapidOCR 主力 → 置信度 < 0.55 或无文本时切 MiMo 视觉模型兜底 → 择优返回。
