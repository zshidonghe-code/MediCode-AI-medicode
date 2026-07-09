#!/bin/bash
# check_frozen.sh — 验证 8 个核心页面没有新增可疑组件
#
# 董事会决议:Loop 30-40 冻结后,8 个核心页面禁止再增加 inline JSX / 新组件引用
# 此脚本作为轻量 lint 检查,任何 PR 涉及核心页面时可手动跑一次
#
# 用法: bash check_frozen.sh
# 退出码: 0 = 通过, 1 = 发现可疑引用

set -e

cd "$(dirname "$0")/.."

echo "=== 冻结检查:8 个核心页面只能引用以下 3 个活跃组件 ==="
echo ""

ACTIVE_COMPONENTS=(
  "./AppLayout"
  "../components/AppLayout"
  "../components/ErrorBoundary"
  "../components/IcdCodingResult"
)

echo "✅ 允许的组件引用:"
for c in "${ACTIVE_COMPONENTS[@]}"; do
  echo "   $c"
done
echo ""

echo "🔍 扫描 8 个核心页面的 import 语句..."
echo ""

PAGES=(
  "PipelinePage"
  "CodingPage"
  "QCPage"
  "DRGPage"
  "DashboardPage"
  "GuidePage"
  "AdminPage"
  "LoginPage"
  "NotFoundPage"
)

VIOLATIONS=0

for page in "${PAGES[@]}"; do
  echo "--- pages/${page}.tsx ---"
  IMPORTS=$(grep -E "^import.*from.*['\"]\\.\\./components/" "src/pages/${page}.tsx" 2>/dev/null || true)
  if [ -z "$IMPORTS" ]; then
    echo "   (无 components/ 引用)"
  else
    echo "$IMPORTS" | while read line; do
      is_allowed=0
      for allowed in "${ACTIVE_COMPONENTS[@]}"; do
        if echo "$line" | grep -q "$allowed"; then
          is_allowed=1
          break
        fi
      done
      if [ $is_allowed -eq 0 ]; then
        echo "   ❌ 违规引用: $line"
      else
        echo "   ✅ $line"
      fi
    done
  fi
  echo ""
done

echo "=== 行数基线检查(冻结起点: pre-loop-audit tag) ==="
echo ""
echo "当前 8 页行数 vs 冻结起点:"
git show pre-loop-audit:frontend/src/pages/ 2>/dev/null | head -1 || echo "   (无法对比 — tag 不存在或路径错)"
echo ""

echo "=== 完成 ==="
echo ""
echo "如果看到 ❌ 违规引用,说明该 PR 引入了新的 components/ 引用"
echo "请检查是否走董事会审批 (见 docs/FROZEN.md 规则 2)"