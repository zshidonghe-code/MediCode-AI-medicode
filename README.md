# 码医 MediCode · AI 医疗 DRG 编码与病历质控系统 | 2026

> 用 AI 辅助完成住院病历的 ICD-10 诊断编码和 DRG 付费分组，同时做病历内涵质控 — 辅助医院降低医保拒付风险，最终结果由人工审核确认。

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 什么是 AI 医疗 DRG 编码？为什么医院每年损失数百亿？

**AI 医疗 DRG 编码**是利用自然语言处理（NLP）和大语言模型（LLM）自动从住院病历中识别临床信息、推荐 ICD-10 诊断编码和 ICD-9-CM-3 手术编码，并基于 CHS-DRG 1.2 方案自动完成 DRG 付费分组的医疗 AI 应用。

DRG/DIP 付费改革是国家医保局重点推进的政策 — 每一份病历的 ICD 编码直接决定医院的收入。但目前全国编码员缺口超 10 万人，人工编码错误率高达 10-15%，每年导致数百亿医保基金流失。

**码医 MediCode** 是一个 AI 驱动的医疗编码与质控一体化平台，集成了：

- **智能 ICD 编码引擎** — NLP 解析 + 医学知识库 + LLM 语义理解，自动推荐 ICD-10 诊断编码和 ICD-9-CM-3 手术编码
- **DRG 自动分组器** — 基于 CHS-DRG 1.2 方案，自动判定 MDC/ADRG/DRG 分组，计算权重和预估支付金额
- **病历内涵质控引擎** — 内置规则 + AI 语义一致性检查，覆盖完整性、逻辑性、编码规范、时效性
- **数据驾驶舱** — 全院 DRG 运营概览、CMI 分析、质控趋势、收入分析
- **医保拒付风险预测**（新功能）— 基于编码 + DRG + 病历内容，提前预警医保飞检高风险病历

**核心差异化优势：** "编码 + DRG 分组 + 质控 + 拒付预测" 四合一，面向提交前人工审核场景。

---

## 行业数据与政策背景

本项目基于以下公开权威数据：

- **国家医保局《DRG/DIP 支付方式改革三年行动计划》**（2021）— 要求 2024 年底全国所有二级以上医院全面覆盖 DRG/DIP
- **国家卫生健康委《病案管理质量控制指标（2021 版）》** — 编码错误率纳入医院等级评审
- **中国医院协会病案管理专业委员会 2023 年报告** — 全国编码员缺口超 10 万人
- **《中国卫生统计年鉴 2023》** — 三级医院年住院量 1.2 亿人次，编码质量直接关系医保支付
- **CHS-DRG 1.2 分组方案**（国家医保局 2024）— 1,000+ DRG 编码，覆盖全部住院场景

---

## 为什么选择码医 MediCode？

| 维度 | 单独编码工具 | 单独 DRG 分组器 | 单独质控系统 | **码医 MediCode** |
|------|------------|----------------|-------------|------------------|
| ICD-10 自动编码 | ✓ | ✗ | ✗ | **✓** |
| ICD-9-CM-3 手术编码 | 部分 | ✗ | ✗ | **✓** |
| CHS-DRG 1.2 自动分组 | ✗ | ✓ | ✗ | **✓** |
| 病历内涵质控 | ✗ | ✗ | ✓ | **✓** |
| LLM 增强（Qwen2.5:3B） | 选配 | ✗ | 选配 | **✓ 内置** |
| 医保拒付风险预测 | ✗ | ✗ | ✗ | **✓** |
| 数据驾驶舱 | 基础 | 基础 | ✗ | **✓ 4 维图表** |
| 一站式流水线 | ✗ | ✗ | ✗ | **✓ NLP→编码→质控→DRG→拒付** |
| 私有化部署 | ✓ | ✓ | ✓ | **✓ Docker Compose 一键** |
| 医院内网运行 | ✓ | ✓ | ✓ | **✓ 数据不出院** |

---

## 核心功能

| 模块 | 功能 | 说明 |
|------|------|------|
| 智能流水线 | NLP → 编码 → 质控 → DRG → 费用 → 拒付预测 | 一站式全流程分析，支持 30 秒快速演示 |
| 编码工作台 | 自动编码 + ICD 搜索 + 编码校验 | 支持手动调整，对比 AI 与人工编码差异 |
| DRG 分组 | CHS-DRG 1.2 自动分组 | 输入编码、年龄、性别，输出分组和支付测算 |
| 质控中心 | 规则引擎 + LLM 语义检查 | 六级缺陷分级，质控评分，采纳/忽略建议 |
| 数据驾驶舱 | 图表化运营数据 | CMI、DRG 分布、质控趋势、收入分析、高频缺陷 |
| 拒付风险预测 | DRG 飞检预警 | 基于规则 + LLM，可规避金额估算 |
| 系统管理 | 数据重置 + 多格式导出 | 管理员专属，支持 JSON/CSV 导出 |

---

## 常见问题 FAQ

### 码医 MediCode 适合什么类型的医院？

适用于**二级以上医院**（≥300 床位）。目前全国 3,000+ 家二三级医院是目标市场，可及市场约 **45 亿/年**（按 8-25 万/床位年费测算）。

### 编码效果目前如何验证？

当前仓库仅有 **4 例验证性测试**，测试的是无 LLM 的本地索引模式；结果只能用于发现问题，不能据此宣称生产级准确率。`920` 条诊断和 `611` 条手术是编码字典规模，不是测试集规模。LLM 增强模式尚未完成独立评估。

测试方法、实际执行结果和限制详见 `docs/BENCHMARK_REPORT.md`。系统定位为提交前辅助审核工具，不能替代编码员进行无人审核的最终编码。

### 和市面上的单独编码系统、DRG 系统有什么区别？

**码医 MediCode 将"编码 + DRG 分组 + 质控 + 拒付预测"整合在一条流水线中**，用于辅助处理 DRG 改革相关工作（详见上方对比表）。

### 数据安全怎么保证？医院内网能跑吗？

✅ 支持医院内网**私有化部署**，**数据不出院**。
- Docker Compose 一键启动
- 最低配置：8C16G + 50G 存储
- 支持在内网环境进行 POC 验证
- Ollama 本地推理，无需外网

详见 `docs/DEPLOY.md`。

### 系统管理员、编码员、医生用什么账号？

| 角色 | 账号 | 权限 |
|------|------|------|
| 管理员 | `admin` | 全功能（数据驾驶舱、系统管理、用户管理） |
| 编码员 | `coder` | 编码工作台、智能流水线 |
| 医生 | `doctor` | 病历质控、流水线 |

**演示密码统一 `123456`**（仅 DEBUG 模式，生产环境必须修改）。

### 参赛项目能用于商业化吗？

✅ 可以。**MIT License** 允许商业使用、修改、分发。详细授权条款见 `LICENSE` 文件。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | React 18 + TypeScript + Ant Design 5 + ECharts | 组件化 UI，医疗行业成熟方案 |
| **后端** | Python 3.12+ + FastAPI + SQLAlchemy 2.0 (async) | 高性能异步 API，自动 Swagger 文档 |
| **AI/ML** | Ollama (Qwen2.5:3B) + LangChain + 规则引擎 | 大模型编码推荐 + 规则兜底 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | 轻量到企业级灵活切换 |
| **PDF 解析** | pypdf 5.x + python-docx | 支持 .txt / .docx / .pdf 多格式病历 |
| **认证** | JWT + pbkdf2_sha256 | 无状态认证，密码哈希安全 |
| **部署** | Docker Compose | 一键启动，支持医院私有化 |

---

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- Ollama（可选，用于 LLM 增强）

### 1. 克隆项目

```bash
git clone https://github.com/zshidonghe-code/MediCode-AI-medicode.git
cd medicode
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m src.main
# API 运行在 http://localhost:8000
# Swagger 文档: http://localhost:8000/docs
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

### 4. （可选）安装 Ollama

```bash
ollama pull qwen2.5:3b
# LLM 增强模式的效果需要单独基准测试，本仓库尚未提供可用于宣称的结果
```

### 5. 访问系统

1. 打开 `http://localhost:5173`
2. 演示账号（密码统一 `123456`）：
   - 管理员：`admin` / `123456`
   - 编码员：`coder` / `123456`
   - 医生：`doctor` / `123456`
3. 首次启动自动填充演示数据（500 条病历）

---

## 项目结构

```
medicode/
├── backend/
│   ├── src/
│   │   ├── api/v1/endpoints/    # API 端点（auth, coding, drg, qc, dashboard, admin, pipeline, rejection）
│   │   ├── config/              # 配置管理
│   │   ├── data/                # ICD 编码数据（JSON，920条诊断 + 611条手术，CHS-DRG 1.2）
│   │   ├── models/              # SQLAlchemy 数据模型
│   │   ├── scripts/             # 种子数据脚本（500 条病历）
│   │   └── services/            # 核心服务（NLP 引擎、ICD 编码器、DRG 分组器、质控引擎、LLM 引擎、拒付风险预测）
│   └── tests/                   # 单元测试（11 个测试文件）
├── frontend/
│   └── src/
│       ├── pages/               # 8 个页面（Pipeline, Coding, DRG, QC, Dashboard, Admin, Login, NotFound）
│       ├── components/          # 共享组件（IcdCodingResult, AnimatedCounter, AppLayout, ErrorBoundary）
│       └── services/            # API 调用 + 状态管理
├── docs/                        # 项目文档（项目计划、技术架构、竞赛策略、API、BENCHMARK、QA_PREP、DEMO_RECORDING_GUIDE 等）
└── docker-compose.yml           # Docker 编排
```

---

## 商业模式

- **SaaS 订阅**：按床位分级定价（500 床以下 8 万/年，500-1500 床 15 万/年，1500 床以上 25 万/年）
- **私有化部署**：一次性授权费 30-80 万 + 年维保费 20%
- **目标市场**：全国 3,000+ 二级以上医院，可及市场 **45 亿/年**
- **初期目标**：第一年签约 10 家医院，第二年 50 家，第三年 200 家

---

## 团队

| 角色 | 成员 |
|------|------|
| 项目负责人 | 郑诗东和 — 上海对外经贸大学，方向决策、路演答辩 |
| 技术开发 | 郑诗东和（AI辅助）— 利用 AI 开发工具，单人完成全栈开发 |
| 医学顾问 | 招募中 |

---

## 竞赛目标

参加中国国际"互联网+"大学生创新创业大赛，**目标全国第一名**。

- 赛道：高教主赛道 · 本科生创意组
- 关键词：AI + 医疗、医保支付改革、大语言模型应用

---

## 文档导航

| 文档 | 用途 |
|------|------|
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | 项目背景、痛点、技术架构、商业模式 |
| [docs/TECH_WHITEPAPER.md](docs/TECH_WHITEPAPER.md) | 技术白皮书（44KB，深度技术细节） |
| [docs/BENCHMARK_REPORT.md](docs/BENCHMARK_REPORT.md) | 编码引擎验证报告 |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 用户使用指南 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署指南（生产环境） |
| [docs/QA_PREP.md](docs/QA_PREP.md) | 答辩问答准备 |
| [docs/DEMO_RECORDING_GUIDE.md](docs/DEMO_RECORDING_GUIDE.md) | Demo 录屏制作指南 |
| [docs/COMPETITION_STRATEGY.md](docs/COMPETITION_STRATEGY.md) | 竞赛策略与评委反馈 |
| [docs/BUSINESS_PLAN.md](docs/BUSINESS_PLAN.md) | 商业计划书 v2.0 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 产品路线图 |
| [docs/OFFLINE_BACKUP.html](docs/OFFLINE_BACKUP.html) | 离线环境备份页 |

---

## License

MIT License
