# 码医 MediCode — AI 医疗 DRG 编码与病历质控系统

> 用 AI 自动完成住院病历的 ICD-10 诊断编码和 DRG 付费分组，同时做病历内涵质控 — 帮医院不被医保扣钱，帮医保基金不被浪费。

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 项目简介

DRG/DIP 付费改革是国家医保局重点推进的政策 — 每一份病历的 ICD 编码直接决定医院的收入。但目前全国编码员缺口超 10 万人，人工编码错误率高达 10-15%，每年导致数百亿医保基金流失。

**码医 MediCode** 是一个 AI 驱动的医疗编码与质控一体化平台，集成了：

- **智能 ICD 编码引擎** — NLP 解析 + 医学知识库 + LLM 语义理解，自动推荐 ICD-10 诊断编码和 ICD-9-CM-3 手术编码
- **DRG 自动分组器** — 基于 CHS-DRG 1.2 方案，自动判定 MDC/ADRG/DRG 分组，计算权重和预估支付金额
- **病历内涵质控引擎** — 100+ 规则 + AI 语义一致性检查，覆盖完整性、逻辑性、编码规范、时效性
- **数据驾驶舱** — 全院 DRG 运营概览、CMI 分析、质控趋势、收入分析

**核心差异化优势：** "编码 + DRG 分组 + 质控" 三合一，市场上没有同类一体化产品。

---

## 核心功能

| 模块 | 功能 | 说明 |
|------|------|------|
| 智能流水线 | NLP → 编码 → 质控 → DRG → 费用 | 一站式全流程分析，支持演示模式 |
| 编码工作台 | 自动编码 + ICD 搜索 + 编码校验 | 支持手动调整，对比 AI 与人工编码差异 |
| DRG 分组 | CHS-DRG 1.2 自动分组 | 输入编码、年龄、性别，输出分组和支付测算 |
| 质控中心 | 100+ 规则引擎 + LLM 语义检查 | 六级缺陷分级，质控评分，采纳/忽略建议 |
| 数据驾驶舱 | 图表化运营数据 | CMI、DRG 分布、质控趋势、收入分析、高频缺陷 |
| 系统管理 | 数据重置 + 多格式导出 | 管理员专属，支持 JSON/CSV 导出 |

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | React 18 + TypeScript + Ant Design 5 + ECharts | 组件化 UI，医疗行业成熟方案 |
| **后端** | Python 3.12+ + FastAPI + SQLAlchemy 2.0 (async) | 高性能异步 API，自动 Swagger 文档 |
| **AI/ML** | Ollama (Qwen2.5:3B) + LangChain + 规则引擎 | 大模型编码推荐 + 规则兜底 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | 轻量到企业级灵活切换 |
| **部署** | Docker Compose | 一键启动，支持医院私有化 |

---

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- Ollama（可选，用于 LLM 增强）

### 1. 克隆项目

```bash
git clone https://github.com/MediCode-AI/medicode.git
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
# LLM 上线后编码准确率从 80% 提升至 95%+
```

### 5. 访问系统

1. 打开 `http://localhost:5173`
2. 默认管理员账号：`admin` / `medicode2024`
3. 首次启动自动填充演示数据

---

## 项目结构

```
medicode/
├── backend/
│   ├── src/
│   │   ├── api/v1/endpoints/    # API 端点（auth, coding, drg, qc, dashboard, admin, pipeline）
│   │   ├── config/              # 配置管理
│   │   ├── data/                # ICD 编码数据（JSON，920条诊断 + 571条手术，CHS-DRG 2.0）
│   │   ├── models/              # SQLAlchemy 数据模型
│   │   ├── scripts/             # 种子数据脚本
│   │   └── services/            # 核心服务（NLP 引擎、ICD 编码器、DRG 分组器、质控引擎、LLM 引擎）
│   └── tests/                   # 17 个单元测试
├── frontend/
│   └── src/
│       ├── pages/               # 7 个页面（Pipeline, Coding, DRG, QC, Dashboard, Guide, Admin）
│       ├── components/          # 共享组件
│       └── services/            # API 调用 + 状态管理
├── docs/                        # 项目文档（项目计划、技术架构、竞赛策略）
└── docker-compose.yml           # Docker 编排
```

---

## 商业模式

- **SaaS 订阅**：按床位分级定价（8-25 万/年）
- **私有化部署**：一次性授权 30-80 万 + 年维保费 20%
- **目标市场**：全国 3,000+ 二级以上医院，可及市场 45 亿/年

---

## 团队

| 角色 | 成员 |
|------|------|
| 项目负责人 | 郑诗东和 — 上海对外经贸大学，方向决策、路演答辩 |
| 技术开发 | 郑诗东和（AI辅助）— 利用AI开发工具，单人完成全栈开发 |
| 医学顾问 | 招募中 — 已与医学院和医院编码科取得联系 |

---

## 竞赛目标

参加中国国际"互联网+"大学生创新创业大赛，目标全国第一名。

- 赛道：高教主赛道 · 本科生创意组
- 关键词：AI + 医疗、医保支付改革、大语言模型应用

---

## License

MIT License
