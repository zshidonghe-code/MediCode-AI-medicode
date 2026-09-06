# GitHub Pages 部署说明：码医 MediCode

本文说明如何从目标仓库发布根目录 `index.html`。它是静态介绍页，不连接后端 API，也不替代本地演示环境。

## 仓库位置

本机目标仓库：

```powershell
cd "C:\Users\Donghe\Desktop\04_MediCode码医\MediCode"
```

GitHub Pages 发布的是当前分支中的 `index.html`、`README.md` 和静态资源。发布前请确认页面中的验证结果与 `docs/BENCHMARK_REPORT.md`、`docs/PIPELINE_RUN_RECORD.md` 一致。

## 发布步骤

1. 将目标仓库推送到 GitHub 的公开仓库。
2. 打开仓库的 **Settings → Pages**。
3. 选择 **Deploy from a branch**。
4. 选择目标分支和 `/ (root)`，保存后等待 GitHub Pages 构建。
5. 使用 Pages 页面显示的地址检查首页、链接和移动端布局。

## 内容边界

- 首页只描述当前已经实现的功能和可追溯验证结果。
- 公开基准：400 份注入式质控测试，缺陷召回 100%，纯规则模式。
- 920 条诊断和 611 条手术是当前编码数据规模，不是测试集规模。
- LLM 增强路径尚未完成独立评估。
- 系统定位为提交前辅助审核工具，最终编码由人工确认。
- 不在静态页中填写患者信息、API Key、医院客户信息或未经授权的合作信息。

## 发布前检查

```powershell
git status --short
git diff --check
```

- [ ] `index.html` 不包含未经验证的准确率、医院部署或收入承诺。
- [ ] `docs/DEMO_SCRIPT.md` 中的路径和示例结果与当前运行记录一致。
- [ ] `README.md` 以 UTF-8 无 BOM 保存。
- [ ] 静态页不包含真实患者数据或凭据。

## 当前验证记录

详细结果见：

- `docs/BENCHMARK_REPORT.md`
- `docs/PIPELINE_RUN_RECORD.md`
- `docs/TEST_RUN_RECORD.md`
