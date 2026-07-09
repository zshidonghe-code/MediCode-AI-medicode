# Issue #4 — RolePermissionMatrix 独立组件 — Handoff

> **TL;DR**：本分支 `refactor/role-permission-matrix` 实现 Issue #4 — `RolePermissionMatrix` 独立组件（无 props，从 `useAuthStore` 读 role）。TDD 3 vertical slices 全过；测试 12/12 通过。

---

## 0. 实施前调研（与原 Issue spec 的差异）

master AppLayout（150 行）**完全没有** `DEMO_USERS` / `VERSION_INFO` / `ICON_MAP` 三个常量 — 这些是 spec 想象存在的字段。

**决策**：走 **路径 A**（贴合现实调整 spec）—— 从零创建组件（与"抽取"等价结果）。Issue #4 的实际产出 = **新建一个可在 admin 页面调用的角色权限矩阵展示组件**。

---

## 1. 改动清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/src/components/RolePermissionMatrix.tsx` | **新建** (122 行) | 独立组件 + DEMO_USERS / VERSION_INFO / ICON_MAP 三个常量 |
| `frontend/src/components/RolePermissionMatrix.test.tsx` | **新建** (62 行) | 3 个 vitest 用例（admin / coder / doctor） |
| `frontend/src/test/setup.ts` | **修改** (+ 19 行) | jsdom matchMedia polyfill（AntD Table/Card 必需） |

---

## 2. TDD 流程（3 vertical slices）

| Slice | 测试 | RED → GREEN |
|-------|------|-------------|
| 1 | admin 渲染 — 显示"管理员" + 数据驾驶舱 + 系统管理 | 🔴 RED (mock not set up) → 🟢 GREEN 1/3 |
| 2 | coder 渲染 — 显示"编码员" + 4 个菜单项 | 🟢 2/3 |
| 3 | doctor 渲染 — 显示"医生" + 4 个菜单项 | 🟢 3/3 |

### 关键技术细节

- **matchMedia polyfill**（slice 1 调试发现）：jsdom 不提供 `window.matchMedia`，AntD Card/Table/Grid 响应式 observer 报错。在 `test/setup.ts` 加 polyfill 让 matchMedia 永远返回 `matches: false`（禁用响应式分支）。
- **mock 函数工厂模式**：`mockUseAuthStore = vi.fn()` 暴露在测试作用域，`vi.mock` 工厂内引用，比 `vi.mocked` 更灵活。
- **无 props 接口**：组件完全靠 `useAuthStore()` 自给自足，符合 spec「role 从 useAuthStore 读」。

---

## 3. 验收对照

GitHub Issue #4 Acceptance Criteria 全部满足：

- [x] 新建 `frontend/src/components/RolePermissionMatrix.tsx`
- [x] 组件接口 `<RolePermissionMatrix />`（无 props，role 从 `useAuthStore` 读）
- [x] DEMO_USERS / VERSION_INFO / ICON_MAP 常量迁入新组件文件
- [x] AppLayout **未修改**（spec 说要删除对应代码，但 master AppLayout 本来就没有这些常量）
- [x] 角色权限表格视觉（图标 + 描述 + 角色标签）渲染正确
- [x] 提供 3 个测试：admin / coder / doctor
- [x] `npm run test -- --run RolePermissionMatrix` **3/3 通过**

---

## 4. 验证清单

| 验证 | 命令 | 结果 |
|------|------|------|
| 测试 (本组件) | `npx vitest run RolePermissionMatrix` | **3/3 通过** |
| 全测试 | `npx vitest run` | **12/12 通过**（4 CommandPalette + 5 useLayoutData + 3 RolePermissionMatrix）|
| Lint (新文件) | `npx eslint src/components/RolePermissionMatrix*` | **0 errors / 0 warnings** |
| Build | `npm run build` | **✓ built in 11.00s**（含 tsc 旧 useLayoutData 错误，与本 PR 无关）|

> ⚠️ **Pre-existing tsc errors**：`useLayoutData.ts:55` 调不存在的 `getTrendDaily`。这是 #9 待修内容，**不在本 PR scope**。等 #9 合并后自动修复。

---

## 5. 与原 spec 的差异

| # | Issue spec 写 | 现实 / 决定 | 理由 |
|---|---------------|-------------|------|
| 1 | "将 AppLayout 内嵌的权限表格抽取" | master AppLayout 无权限表格代码 | 从零创建（结果等价） |
| 2 | "完成后 AppLayout 不应有这些常量" | master AppLayout 本来就没有这些常量 | 无需修改 AppLayout |
| 3 | "3 个测试：3 个角色" | ✅ 完全一致 | — |

---

## 6. Git 状态

```
分支：refactor/role-permission-matrix
基于：b8b3f2a (refactor/command-palette-modal)
改动：2 new + 1 modified
测试：12/12 ✅
lint: ✅
build: ✅ (含 pre-existing useLayoutData tsc 错误)
```

---

## 7. 建议下一步

1. commit + push + 创建 PR（`refactor(#4): add RolePermissionMatrix component + 3 role tests`）
2. 合并到 b8b3f2a 的 ancestor（master 等 #8/#9 合完才能合 #4）
3. 关闭 Issue #4
4. 单独 PR 修 #9（useLayoutData 真后端字段对齐 — 已是 PR #9 draft）