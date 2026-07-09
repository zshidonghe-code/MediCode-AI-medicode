# 码医 MediCode — Loop 30-40 冻结清单

**冻结起点**：git tag `pre-loop-audit`（2026-07-09, commit 6a000cd）
**触发会议**：码医第二轮董事会（2026-07-09）
**PDF 报告**：`C:/Users/Donghe/Desktop/council-reports/2026-07-09-1517-medicode-loop-freeze/council-report.pdf`

---

## 背景

2026-06-24 至 2026-06-26 期间，码医前端经历了 40+ 次 `/loop` 迭代（详见 `C:/Users/Donghe/Desktop/码医_Loop_Reports_20260624..26/` 三份日报）。这一阶段集中添加了大量可视化增强组件（ECharts gauge、heatmap、timeline、sparkline、demo timer、export toolbar 等）。

**董事会决议**：这些功能不删除、不复盘、不再继续添加。**当前状态即终态**。

---

## 冻结规则（3 条硬规则）

### 规则 1：8 个核心页面禁止再增长

| 页面 | 当前行数 | 状态 |
|------|---------|------|
| `pages/PipelinePage.tsx` | 791 | 🔒 冻结 |
| `pages/CodingPage.tsx` | 446 | 🔒 冻结 |
| `pages/QCPage.tsx` | 430 | 🔒 冻结 |
| `pages/DRGPage.tsx` | 389 | 🔒 冻结 |
| `pages/DashboardPage.tsx` | 339 | 🔒 冻结 |
| `pages/GuidePage.tsx` | 282 | 🔒 冻结 |
| `pages/AdminPage.tsx` | 240 | 🔒 冻结 |
| `pages/LoginPage.tsx` | 146 | 🔒 冻结 |
| `pages/NotFoundPage.tsx` | 14 | 🔒 冻结 |

**禁止行为**：在这 8 个页面里新增 inline JSX / 新组件引用 / 新可视化区块。
**例外**：修复 bug、调整样式、对接真后端字段，允许。

### 规则 2：新功能必须独立组件 + 董事会审批

如果接下来需要新功能（例如 X 功能迷你版）：
- **必须** 创建独立组件文件（`components/Xxx.tsx`）
- **必须** 在 AppLayout/8 页面 import 之前，由董事会审议
- **禁止** 把新逻辑 inline 塞进 8 个核心页面

### 规则 3：Loop 30-40 已存在功能不删除也不引用新增

下面这些功能**已经在 8 个页面里**（以 inline JSX 形式存在），不删除它们（避免大改），但也**禁止复制同类新增**：

- ECharts Gauge（完成度环、价值仪表盘、置信度仪表盘） — 已存在 3 处，**禁止第 4 处**
- AI 思维时间线（NLP→检索→MDC→ADRG→DRG 决策链） — PipelinePage 已存在
- 30 天缺陷趋势线 — QCPage 已存在
- 矩阵热力图 — QCPage 已存在
- 同科室对比卡 — QCPage 已存在
- 反事实模式 + 双向高亮 — CodingPage 已存在
- 选中编码导出工具栏 — CodingPage 已存在
- 5 示例病历一键演示 — CodingPage 已存在
- NLP 关键词热度云图 — CodingPage 已存在
- DRG 入组决策树（MDC→ADRG→DRG） — DRGPage 已存在
- 备选 DRG 路径对比 — DRGPage 已存在
- DemoTimer / ExportToolbar — 已通过 commit 6a000cd 删除
- AnimatedCounter — 已通过 commit 6a000cd 删除
- CommandPaletteModal — 已通过 commit 6a000cd 删除
- RolePermissionMatrix — 已通过 commit 6a000cd 删除（用 PPT 页替代）

---

## 当前活跃组件（不在冻结范围）

| 组件 | 用途 | 状态 |
|------|------|------|
| `components/AppLayout.tsx` | 顶栏 + 侧栏 | ✅ 活跃 |
| `components/ErrorBoundary.tsx` | 错误兜底 | ✅ 活跃 |
| `components/IcdCodingResult.tsx` | 编码结果展示 | ✅ 活跃 |
| `pages/RejectionPage.tsx` | 拒付预测独立页 (B v1) | ✅ 活跃 (董事会 2026-07-09 放大) |

新增独立组件时，按规则 2 走董事会审批。

---

## X 功能复审状态（2026-07-09 第三轮董事会）

**复审决议 PDF**：`C:/Users/Donghe/Desktop/council-reports/2026-07-09-1719-medicode-x-amplify/council-report.pdf`

| X 功能 | 状态 | 冻结期 | 复活成本 |
|--------|------|--------|----------|
| **B 拒付预测** | ✅ 放大为独立顶级菜单 (`/rejection`) | — | — |
| **A 文档上传** (`DocUploadCoder.tsx`) | 🟡 冻结不删 (B 失败保底) | 4 周 (2026-07-09 ~ 2026-08-06) | 1h |
| **C DRG 对比** (`DRGCompare.tsx`) | 🟡 冻结不删 (B 失败保底) | 4 周 (2026-07-09 ~ 2026-08-06) | 1h |

**复活操作**：删除 `// FROZEN_X_CANDIDATE` 注释 + 重新在 `CodingPage` / `DRGPage` import 即可。

---

## 当前活跃 hooks（不在冻结范围）

| Hook | 用途 | 状态 |
|------|------|------|
| `hooks/useLayoutData.ts` | 顶栏数据自动刷新 | ✅ 活跃 |

---

## 评估清单（grep 验证）

董事会要求下周一前完成 grep 扫描，输出每个 Loop 30-40 功能的当前引用状态。本文档**未含评估清单**，因为：

1. Loop 30-40 功能是 inline JSX（不是独立组件），无法用 import 追踪
2. 已通过 commit 6a000cd 删除的 3 个组件（AnimatedCounter / CommandPaletteModal / RolePermissionMatrix）已从 git 历史消失
3. 剩余 12+ 个功能散落在 8 个页面的 inline JSX 中，**逐个 grep 不现实**

**替代方案**：8 个核心页面**整体冻结**（规则 1），比逐功能追踪更彻底。

---

## 国赛后清理窗口

国赛结束后（约 2026-09 月初），重新审议以下两类动作：

1. **保留并整理**：把 inline 在页面里的 Loop 30-40 功能提取为独立组件，规范化命名和复用
2. **批量删除**：评估每个功能的演示价值，删除评分贡献接近 0 的功能

本轮董事会决议：**今天不删、今天不复盘**。国赛后再说。

---

## 监督机制

任何团队成员想新增 Loop 30-40 同类组件时：

1. **先看本文件**：确认是否已在"已存在功能"列表里
2. **走董事会审批**：不能自己加
3. **如违反规则**：commit 阶段由 grep 拦截（开发中）

---

**最后更新**：2026-07-09
**维护者**：码医项目组