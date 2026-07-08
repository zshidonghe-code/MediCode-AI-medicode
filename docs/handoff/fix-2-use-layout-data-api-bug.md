# Fix #2 — useLayoutData API 不存在 Bug — Handoff

> **TL;DR**：本分支 `fix/#2-get-trend-daily-api-bug` 修复 `useLayoutData` hook 调用了不存在的 `dashboardAPI.getTrendDaily` 的 bug + 字段映射全面对齐真后端。TDD red→green 全过；build/tsc/lint 全绿；9/9 测试通过。

---

## 0. 问题（Issue #2 真实 Bug）

PR #8（Issue #3）恢复 `useLayoutData` hook 时埋的雷：

### Bug 1 — API 名错误
```ts
// 错的（useLayoutData.ts:55）
(dashboardAPI as any).getTrendDaily(7)

// 真 API（frontend/src/services/api.ts:75）
dashboardAPI.getQCTrend(days = 30)  // → GET /dashboard/qc-trend
```

### Bug 2 — 字段映射臆造（更严重）
hook 用的字段在真后端**根本不存在**：

| hook 用 | 真后端 /dashboard/overview 返回 | 状态 |
|---------|-------------------------------|------|
| `today_count` | `total_cases` | ❌ 臆造 |
| `today_avg_ms` | `avg_stay_days` | ❌ 臆造 |
| `today_saved_yuan` | `avg_cost` | ❌ 臆造 |

| hook 用 | 真后端 /dashboard/qc-trend 返回 | 状态 |
|---------|-------------------------------|------|
| `row.day` | `row.date` | ❌ |
| `row.total` | `row.total_checks` | ❌ |

**结论**：即使代码不崩，`useLayoutData` 一旦集成到 AppLayout 会渲染空白/NaN，因为字段全是 undefined → fallback 到 0。

### Bug 3 — `(dashboardAPI as any)`
类型保护失效，未来 API 改名也不会报错。

---

## 1. 改动清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/src/hooks/useLayoutData.ts` | **重写** | API 名修正 + 字段映射对齐 + 删 `as any` |
| `frontend/src/hooks/useLayoutData.test.ts` | **重写** | fixture 对齐真后端 shape（MOCK_OVERVIEW + MOCK_QC_TREND） |

> **基础设施恢复**（vitest.config / setup.ts / package.json + CommandPaletteModal 等）通过 cherry-pick commit `ccf80c3` 复用，与 #8 PR 一致。

---

## 2. TDD 流程（5 vertical slices）

| Slice | 测试 | RED → GREEN |
|-------|------|-------------|
| 1 | 加载时调真 API + todayStats 字段对齐 | RED: `getTrendDaily is not a function` → GREEN |
| 2 | refresh 重拉 | ✅ 4/5 → 5/5 |
| 3 | 错误 fallback | ✅ |
| 4 | loading 状态翻转 | ✅ |
| 5 | 卸载清理 | ✅ |

### 关键技术点

- **RED 信号明确**：`expect ... 'net fail'` 拿到 `getTrendDaily is not a function` —— bug 真实暴露
- **fixture 严格对齐**：`MOCK_OVERVIEW` 用 dashboard.py:89 真实返回；`MOCK_QC_TREND` 用 dashboard.py:196 真实返回
- **类型守卫**：mock 用 `as unknown as Awaited<ReturnType<...>>` 替代 `as any`，保住测试侧类型推断

---

## 3. 与真后端的字段对齐表

### `/dashboard/overview` → `todayStats`

| TodayStats 字段 | 后端字段 | 后端行号 |
|----------------|---------|---------|
| `totalCases` | `total_cases` | dashboard.py:90 |
| `cmi` | `cmi` | dashboard.py:60 |
| `avgStayDays` | `avg_stay_days` | dashboard.py:36 |
| `aiCodingRate` | `ai_coding_rate` | dashboard.py:42 |
| `qcPassRate` | `qc_pass_rate` | dashboard.py:49 |

### `/dashboard/qc-trend` → `trend7d[]`

| TrendPoint 字段 | 后端字段 | 后端行号 |
|---------------|---------|---------|
| `date` | `date` (YYYY-MM-DD) | dashboard.py:197 |
| `score` | `avg_score` | dashboard.py:195 |
| `checks` | `total_checks` | dashboard.py:199 |
| `defectRate` | `defect_rate` | dashboard.py:194 |
| `cmi` | `cmi` (nullable) | dashboard.py:235 |

---

## 4. 验收清单

| 验证 | 命令 | 结果 |
|------|------|------|
| 测试 | `npx vitest run` | **9/9 通过**（4 CommandPalette + 5 useLayoutData）|
| 类型 | `npx tsc --noEmit` | **0 错误** |
| 构建 | `npm run build` | **✓ built in 11.00s** |
| Lint | `npx eslint src/hooks/useLayoutData*` | **0 errors / 0 warnings** |

---

## 5. Git 状态

```
分支：fix/#2-get-trend-daily-api-bug
基于：master (48ec557) + cherry-pick ccf80c3 (Issue #3 命令面板 + 基建)
最新 commit：useLayoutData 重写 + test 重写
```

---

## 6. 后续

1. push + 创建 PR (`fix(#2): align useLayoutData with real /dashboard/overview + /qc-trend API`)
2. close Issue #2
3. 合并后 AppLayout 可安全集成 `useLayoutData`（本次未集成，保留给后续 layout 升级 PR）