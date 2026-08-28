# 码医 MediCode 部署指南

> 版本：1.0.0 | 最后更新：2025-05-25

## 目录

- [系统架构概览](#系统架构概览)
- [环境要求](#环境要求)
- [后端部署](#后端部署)
- [前端部署](#前端部署)
- [Ollama LLM 配置](#ollama-llm-配置)
- [开发工作流](#开发工作流)
- [数据库说明](#数据库说明)
- [生产部署注意事项](#生产部署注意事项)
- [常见问题](#常见问题)

---

## 系统架构概览

```
+---------------------------+     +---------------------------+
|       前端 (React)         |     |      后端 (FastAPI)        |
|   Vite + Ant Design       |     |   Python 3.12 + SQLAlchemy |
|   localhost:5173          | <-> |   localhost:8000           |
+---------------------------+     +---------------------------+
                                              |
                +-----------------------------+------------------------------+
                |                             |                             |
        +-------v--------+        +----------v---------+        +----------v--------+
        |  NLP Engine     |        |   ICD Coder         |        |   Ollama LLM      |
        |  (jieba分词)    |        |   (向量/语义搜索)    |        |   qwen2.5:3b      |
        +-----------------+        +--------------------+        |   localhost:11434  |
                |                             |                  +-------------------+
        +-------v--------+        +----------v---------+
        |  DRG Grouper    |        |   QC Engine         |
        |  (CHS-DRG 1.2)  |        |   (27条当前规则)    |
        +----------------+        +--------------------+
                                              |
                                   +----------v---------+
                                   |   SQLite/PostgreSQL |
                                   |   业务数据库         |
                                   +--------------------+
```

---

## 环境要求

### 硬件最低配置

| 组件 | 最低要求 | 推荐配置 |
| --- | --- | --- |
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+（如需本地运行 LLM） |
| 磁盘 | 10 GB 可用 | 50 GB+ SSD |

### 软件依赖

| 软件 | 版本要求 | 用途 | 安装验证 |
| --- | --- | --- | --- |
| Python | 3.12+ | 后端运行环境 | `python --version` |
| Node.js | 18+ | 前端构建运行 | `node --version` |
| npm | 9+ | 前端包管理 | `npm --version` |
| Git | 2.x+ | 版本管理 | `git --version` |
| Ollama | 最新版 | 本地 LLM 推理（可选） | `ollama list` |

---

## 后端部署

### 第一步：进入后端目录

```bash
cd "C:\Users\Donghe\Desktop\码医-MediCode\backend"
```

或在 Unix/macOS 上：

```bash
cd /path/to/码医-MediCode/backend
```

### 第二步：创建 Python 虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

验证激活成功——命令行前应显示 `(.venv)`。

### 第三步：安装依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 安装开发依赖（测试/调试用）
pip install -r requirements-dev.txt
```

依赖列表说明：

| 依赖 | 用途 |
| --- | --- |
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `sqlalchemy[asyncio]` | 异步 ORM |
| `aiosqlite` | SQLite 异步驱动（开发环境） |
| `asyncpg` | PostgreSQL 异步驱动（生产环境） |
| `alembic` | 数据库迁移工具 |
| `pydantic` | 数据验证 |
| `python-docx` | Word 文档解析 |
| `PyPDF2` | PDF 文档解析 |
| `pyjwt` | JWT 令牌生成与验证 |
| `passlib[bcrypt]` | 密码哈希 |
| `jieba` | 中文分词 |
| `pypinyin` | 拼音转换（编码搜索） |
| `pandas` / `numpy` | 数据分析 |
| `httpx` | HTTP 客户端（测试用） |
| `pytest` | 测试框架（开发依赖） |

### 第四步：配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```env
# 调试模式（开发用，生产环境务必设为 false）
DEBUG=true

# 数据库（默认 SQLite，开箱即用）
DATABASE_URL=sqlite+aiosqlite:///./medicode.db
DATABASE_SYNC_URL=sqlite:///./medicode.db

# JWT 密钥（开发环境自动生成，生产环境必须手动设置高强度随机串）
SECRET_KEY=your-production-secret-key-here

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 演示账号密码（仅在 DEBUG=true 时生效，生产环境通过环境变量覆盖）
DEMO_ADMIN_PASSWORD=medicode2024
DEMO_CODER_PASSWORD=code123
DEMO_DOCTOR_PASSWORD=doc123

# LLM 配置
LLM_MODEL=qwen2.5:3b
LLM_BASE_URL=http://localhost:11434

# DRG 基础费率（元），根据当地医保政策调整
DRG_BASE_RATE=12000.0

# CORS 允许的前端地址
# 默认可不设：["http://localhost:5173", "http://localhost:3000"]
```

### 第五步：初始化数据库

数据库会在首次启动时自动创建（SQLAlchemy `create_all`）。如果需要手动初始化：

```bash
# 方式一：直接启动，自动建表
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 方式二：使用 Alembic 迁移
alembic upgrade head
```

### 第六步：种子数据（可选）

首次启动时，如果数据库为空，系统会自动植入演示数据（3 份模拟病历 + 编码结果 + DRG 分组 + 质控结果）。也可以手动执行：

```bash
python -m src.scripts.seed_pipeline_demo
```

ICD 编码参考数据通过 `src/data/icd_diagnoses.json` 和 `src/data/icd_procedures.json` 加载。

### 第七步：启动后端服务

```bash
# 开发模式（热重载）
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式（多 worker）
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

启动成功后输出类似：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     LLM backend: ollama (qwen2.5:3b)
INFO:     Application startup complete.
```

验证后端运行：

```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl http://localhost:8000/health/llm
# {"llm_available": true, "llm_backend": "ollama"}
```

查看 API 文档（仅 DEBUG 模式）：

浏览器访问 `http://localhost:8000/docs` 查看 Swagger UI 交互式文档。

---

## 前端部署

### 第一步：进入前端目录

```bash
cd "C:\Users\Donghe\Desktop\码医-MediCode\frontend"
```

### 第二步：安装依赖

```bash
npm install
```

前端技术栈：

| 依赖 | 用途 |
| --- | --- |
| `react` / `react-dom` | 前端框架 |
| `react-router-dom` | 路由管理 |
| `antd` | UI 组件库 |
| `zustand` | 状态管理 |
| `axios` | HTTP 请求 |
| `echarts` | 数据可视化 |
| `react-quill` | 富文本编辑器 |
| `dayjs` | 日期处理 |
| `vite` | 构建工具 |

### 第三步：验证代理配置

前端的 `vite.config.ts` 已配置开发代理，将 `/api`、`/health`、`/docs` 请求转发到后端 `http://localhost:8000`：

```typescript
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true },
    '/health': { target: 'http://localhost:8000', changeOrigin: true },
    '/docs': { target: 'http://localhost:8000', changeOrigin: true },
  },
}
```

如果你的后端不在 `localhost:8000`，修改 `target` 为实际地址。

### 第四步：启动开发服务器

```bash
npm run dev
```

启动成功后输出类似：

```
VITE v5.3.1  ready in 823 ms
-> Local:   http://localhost:5173/
```

浏览器访问 `http://localhost:5173` 即可看到登录页面。

### 第五步：构建生产包

```bash
npm run build
```

构建产物在 `frontend/dist/` 目录，可直接部署到 Nginx 等静态服务器。

### 启动脚本（一行命令）

在项目根目录创建启动脚本 `start.bat`（Windows）：

```bat
@echo off
echo ========================================
echo   码医 MediCode - 启动脚本
echo ========================================

REM 启动 Ollama（如果未运行）
echo [1/3] 检查 Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo 正在启动 Ollama...
    start "Ollama" ollama serve
)

REM 启动后端
echo [2/3] 启动后端...
start "MediCode Backend" cmd /c "cd backend && .venv\Scripts\activate && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

REM 启动前端
echo [3/3] 启动前端...
start "MediCode Frontend" cmd /c "cd frontend && npm run dev"

echo ========================================
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo   API文档: http://localhost:8000/docs
echo ========================================
pause
```

或 Unix/macOS `start.sh`：

```bash
#!/bin/bash
echo "=============================="
echo "  码医 MediCode - 启动脚本"
echo "=============================="

# 启动后端
echo "[1/2] 启动后端..."
cd backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 启动前端
echo "[2/2] 启动前端..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "=============================="
echo "  后端: http://localhost:8000"
echo "  前端: http://localhost:5173"
echo "  API文档: http://localhost:8000/docs"
echo "  Ctrl+C 停止所有服务"
echo "=============================="

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
```

---

## Ollama LLM 配置

LLM 是可选组件。系统设计为**降级运行**——当 Ollama 不可用时自动回退到纯规则引擎模式。

### 安装 Ollama

```bash
# Windows: 下载安装包 https://ollama.com/download/windows
# macOS:  下载安装包 https://ollama.com/download/mac
# Linux:  curl -fsSL https://ollama.com/install.sh | sh
```

### 拉取模型

```bash
# 推荐模型（3B参数，资源占用低）
ollama pull qwen2.5:3b

# 更高精度可选
ollama pull qwen2.5:7b

# 验证拉取成功
ollama list
```

如果使用非默认模型，修改 `.env` 中的 `LLM_MODEL`：

```env
LLM_MODEL=qwen2.5:7b
```

### 验证 LLM 连通性

```bash
curl http://localhost:11434/api/tags
# 返回可用模型列表

curl http://localhost:8000/health/llm
# {"llm_available": true, "llm_backend": "ollama"}
```

### 无 LLM 模式

如果不需要 LLM，完全无需安装 Ollama。API 请求中的 `use_llm` 参数默认为 `false`。系统会使用以下降级策略：

| 功能 | 有 LLM | 无 LLM |
| --- | --- | --- |
| ICD 编码 | LLM 重排序候选编码 | 规则引擎 + 向量搜索 |
| 质控语义检查 | LLM 语义分析 | 仅规则检查 |

---

## 开发工作流

### 目录结构

```
码医-MediCode/
├── backend/
│   ├── alembic/                 # 数据库迁移
│   │   └── versions/
│   ├── src/
│   │   ├── api/
│   │   │   ├── router.py        # 路由注册
│   │   │   └── v1/
│   │   │       └── endpoints/   # API 端点
│   │   │           ├── auth.py
│   │   │           ├── coding.py
│   │   │           ├── drg.py
│   │   │           ├── qc.py
│   │   │           ├── dashboard.py
│   │   │           ├── pipeline.py
│   │   │           └── admin.py
│   │   ├── config/
│   │   │   └── settings.py      # 全局配置
│   │   ├── data/                # 静态数据文件
│   │   ├── models/              # 数据库模型
│   │   │   ├── database.py
│   │   │   ├── patient.py
│   │   │   ├── icd.py
│   │   │   └── qc.py
│   │   ├── scripts/             # 脚本工具
│   │   └── services/            # 核心服务
│   │       ├── drg_grouper/     # DRG 分组引擎
│   │       ├── icd_coder/       # ICD 编码引擎
│   │       ├── llm_engine/      # LLM 推理引擎
│   │       ├── nlp_engine/      # NLP 分词引擎
│   │       ├── qc_engine/       # 质控引擎
│   │       └── vector_search/   # 向量语义搜索
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/          # 可复用组件
│   │   ├── pages/               # 页面组件
│   │   │   ├── LoginPage.tsx
│   │   │   ├── PipelinePage.tsx
│   │   │   ├── CodingPage.tsx
│   │   │   ├── DRGPage.tsx
│   │   │   ├── QCPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts           # API 客户端
│   │   │   └── authStore.ts     # 认证状态
│   │   └── types/
│   │       └── api.ts           # 类型定义
│   ├── package.json
│   └── vite.config.ts
└── docs/
    ├── API.md
    ├── DEPLOY.md
    └── USER_GUIDE.md
```

### 日常开发流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 启动后端（终端1）
cd backend
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn src.main:app --reload

# 3. 启动前端（终端2）
cd frontend
npm run dev

# 4. 运行测试
cd backend
pytest tests/ -v

# 5. 数据库迁移（模型变更后）
cd backend
alembic revision --autogenerate -m "描述变更"
alembic upgrade head
```

### 代码风格

**后端 Python**：

- 遵循 PEP 8 规范
- 类型标注：所有函数入参和返回值使用 type hints
- 异步优先：数据库操作和 I/O 使用 `async/await`
- 日志：使用 `logging.getLogger(__name__)`

**前端 TypeScript**：

- 使用函数组件 + Hooks
- 状态管理使用 Zustand
- API 调用集中管理在 `services/api.ts`
- UI 组件使用 Ant Design 5.x

### 测试

```bash
# 后端测试
cd backend
pytest tests/ -v --cov=src

# 单文件测试
pytest tests/test_drg.py -v
pytest tests/test_qc.py -v

# 全链路集成测试
python test_pipeline_full.py
```

---

## 数据库说明

### 开发环境：SQLite

默认使用 SQLite，数据库文件 `backend/medicode.db`，零配置开箱即用。适合开发、演示和单机部署。

### 生产环境：PostgreSQL

切换到 PostgreSQL 只需修改 `.env`：

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/medicode
DATABASE_SYNC_URL=postgresql://user:password@host:5432/medicode
```

数据库会自动检测 SQLite/PostgreSQL 并应用对应的连接参数（SQLite 设置 `check_same_thread=False`，PostgreSQL 启用连接池）。

### 数据表

| 表名 | 说明 |
| --- | --- |
| `patients` | 患者信息（匿名化） |
| `medical_records` | 病历记录 |
| `coding_results` | AI 编码结果 |
| `qc_results` | 质控缺陷记录 |
| `coding_logs` | 编码变更日志 |
| `icd_codes` | ICD 编码参考库 |
| `drg_groups` | DRG 分组参考库 |
| `qc_rules` | 质控规则库 |

### 重置数据

通过管理接口或 API 调用：

```bash
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

重置仅清空用户数据（patients / medical_records / coding_results / qc_results / coding_logs），参考数据（icd_codes / drg_groups / qc_rules）不受影响。

---

## 生产部署注意事项

### 安全配置

生产环境中**必须**设置以下环境变量（不要使用默认值）：

```env
DEBUG=false
SECRET_KEY=<至少 64 位随机字符串>
DEMO_ADMIN_PASSWORD=<高强度密码>
DEMO_CODER_PASSWORD=<高强度密码>
DEMO_DOCTOR_PASSWORD=<高强度密码>
```

生成安全密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 反向代理配置（Nginx 示例）

```nginx
server {
    listen 80;
    server_name medicode.your-domain.com;

    # 前端静态文件
    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 进程守护

使用 systemd 托管后端（`/etc/systemd/system/medicode.service`）：

```ini
[Unit]
Description=MediCode Backend Service
After=network.target

[Service]
Type=simple
User=medicode
WorkingDirectory=/path/to/backend
EnvironmentFile=/path/to/backend/.env
ExecStart=/path/to/backend/.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 资源预估

| 并发用户数 | 建议配置 |
| --- | --- |
| 1-5 | 4 核 / 8 GB / 无 GPU（规则模式） |
| 5-20 | 8 核 / 16 GB / 可选 GPU |
| 20-50+ | 16 核 / 32 GB / GPU 建议 + PostgreSQL |

---

## 常见问题

### Q: 启动后端时提示 "ModuleNotFoundError: No module named 'xxx'"

**A**: 虚拟环境可能未激活或依赖未安装完全。

```bash
source .venv/bin/activate   # 或 Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果用到 aiosqlite
```

### Q: 前端页面空白，控制台报 "Failed to fetch"

**A**: 后端未启动或端口冲突。确认 `uvicorn` 正在本地 8000 端口运行，且前端开发代理配置正确。

### Q: 编码/质控结果显示无 LLM

**A**: Ollama 未运行或模型未拉取。检查：

```bash
ollama list               # 确认 qwen2.5:3b 已安装
curl http://localhost:8000/health/llm   # 确认后端能连通 Ollama
```

不需要 LLM 也可正常工作，系统会自动降级到规则引擎。

### Q: 如何切换数据库从 SQLite 到 PostgreSQL？

**A**: 修改 `.env` 中的 `DATABASE_URL`，然后重启服务。注意需要先安装 `asyncpg` 驱动（已在 requirements.txt 中）。

### Q: 前端报 401 错误

**A**: Token 过期或未登录。Token 有效期默认 60 分钟。重新登录即可。

### Q: Windows 下虚拟环境激活失败

**A**: PowerShell 可能需要先执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

或使用 CMD 直接执行 `venv\Scripts\activate.bat`。
