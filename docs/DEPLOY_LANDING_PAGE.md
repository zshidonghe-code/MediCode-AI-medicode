# GitHub Pages 部署指南 · 码医 MediCode

> 5 分钟把 `index.html` 部署到 `username.github.io/medicode/`，比赛评委/留学推荐人/投资人扫个码就能看。

---

## 一、文件位置说明

我们刚才生成的 `index.html` 放在**项目根目录**：

```
码医-MediCode/
├── index.html              ← 项目官网（landing page）
├── README.md
├── backend/
├── frontend/
├── docs/
└── ...
```

`index.html` 是 GitHub Pages 默认查找的文件名，放在根目录最省事。

---

## 二、部署步骤（5 分钟）

### 步骤 1：把 index.html 提交到 GitHub

```powershell
# 在项目根目录执行
cd "C:\Users\Donghe\Desktop\码医-MediCode"

# 提交
git add index.html README.md
git commit -m "feat: 项目官网 landing page + README SEO 改版"
git push origin master
```

> ⚠️ **需要先配 GitHub 远端**。如果还没配：
> ```powershell
> # 1. 在 GitHub 网页上创建空仓库 MediCode-AI/medicode
> # 2. 然后：
> git remote add origin https://github.com/MediCode-AI/medicode.git
> git push -u origin master
> ```

### 步骤 2：开启 GitHub Pages

1. 打开 GitHub 仓库页面 → **Settings** → **Pages**
2. **Source**：选 `Deploy from a branch`
3. **Branch**：选 `master`（或 `main`，看你用什么） + `/ (root)`
4. 点击 **Save**
5. 等 30 秒 - 2 分钟，刷新页面会显示：

> ✅ Your site is live at `https://medicode-ai.github.io/medicode/`

### 步骤 3：自定义域名（可选）

如果你有自己的域名 `medicode.cn`：

1. 在 `docs/` 同级创建 `CNAME` 文件：
   ```
   medicode.cn
   ```
2. 在域名 DNS 添加 CNAME 记录：`www` → `medicode-ai.github.io`
3. 在 GitHub Pages 设置填入 `medicode.cn`
4. 等待 DNS 生效（10 分钟 - 24 小时）

---

## 三、部署后必做验证

### 3.1 基础检查

- [ ] 浏览器打开 `https://medicode-ai.github.io/medicode/`
- [ ] 页面正常显示（Hero / 功能 / 对比表 / FAQ / CTA）
- [ ] GitHub badges 正常显示
- [ ] 所有链接可点击

### 3.2 SEO 验证（关键！）

#### Google 收录检查

1. 打开 [Google Search Console](https://search.google.com/search-console/)
2. 添加你的 GitHub Pages 域名
3. 等 1-3 天 Google 抓取
4. 搜索 `site:medicode-ai.github.io/medicode` 验证收录

#### Schema.org 验证

1. 打开 [Schema Markup Validator](https://validator.schema.org/)
2. 输入 URL：`https://medicode-ai.github.io/medicode/`
3. 应该看到 2 个 schema：
   - `SoftwareApplication` ✅
   - `FAQPage` ✅

#### AI 引擎引用测试

1. **ChatGPT**（开了 web browsing）：
   > 问："有哪些 AI 医疗 DRG 编码的开源项目？"
   > 看是否引用你的页面

2. **Perplexity AI**：
   > 搜 "MediCode 码医 AI 医疗编码"
   > 看搜索结果是否包含

3. **Google AI Overview**：
   > 搜 "AI 医疗 ICD 编码 准确率"
   > 看 AI 摘要是否引用

> 💡 **AI 引用不是立刻生效**，通常需要 2-4 周持续生产内容（博客、技术文章）才能建立 domain authority。

### 3.3 移动端测试

- [ ] iPhone Safari 打开正常
- [ ] Android Chrome 打开正常
- [ ] 按钮可点击（不重叠）
- [ ] 字体不溢出

---

## 四、可选增强

### 4.1 加 OG 图片（社交分享缩略图）

GitHub 仓库的 `og-image.png` 引用了 `medicode-ai.github.io/medicode/og-image.png`，**必须存在**才能正常显示。

**生成方法**：

1. 打开 [https://www.bannerbear.com/](https://www.bannerbear.com/) 或 [https://www.canva.com/](https://www.canva.com/)
2. 用模板生成 1200×630 PNG
3. 放到 `og-image.png`（项目根目录）
4. 重新 push

**简易替代**：

```powershell
# 用 PowerPoint 做一个 1200x630 封面，导出 PNG
# 或用 ffmpeg 从你的 demo GIF 截一帧
ffmpeg -i assets/demo-30s.gif -ss 00:00:10 -vframes 1 -y og-image.png
```

### 4.2 加 Google Analytics（流量分析）

在 `index.html` 的 `</head>` 前加：

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

> 把 `G-XXXXXXXXXX` 换成你的 GA4 ID。

### 4.3 加 favicon

1. 用 [favicon.io](https://favicon.io/) 生成 32×32 ICO
2. 放到 `favicon.ico`（项目根目录）
3. 在 `index.html` 的 `<head>` 加：
   ```html
   <link rel="icon" href="/favicon.ico" />
   ```

---

## 五、SEO 长期策略（不只 README）

| 频率 | 动作 | 工具 |
|------|------|------|
| 每周 | 发 1 篇技术博客（知乎/CSDN/掘金）| Markdown + 外链回主页 |
| 每月 | 更新 1 次 BENCHMARK 报告 | 跑测试 → 更新数据 |
| 每月 | 申请 1 个外链（医疗行业网站/媒体）| 媒体投稿/采访 |
| 每季 | 申请 1 次媒体报道 | 36 氪 / 虎嗅 / 动脉网 |

> ⏱️ **见效时间**：3-6 个月后 ChatGPT/Perplexity 会主动引用你。

---

## 六、紧急情况

### 部署后页面 404

1. 检查 GitHub Pages Settings 里的 Source 是否正确
2. 检查分支名（master vs main）
3. 等 5 分钟，GitHub 缓存
4. 强制刷新浏览器（Ctrl+Shift+R）

### 部署后样式乱掉

- 检查 `index.html` 是否完整上传
- 浏览器 F12 → Console 看有没有 404
- 检查 GitHub Pages URL 是否带 trailing slash

### 想换回 docs/landing/

如果觉得 `index.html` 在根目录碍事，移走：
```powershell
mkdir docs/landing
move index.html docs/landing/
# GitHub Pages Settings → Source 改成 /docs
```

---

## 七、产出清单

- [ ] `index.html`（已完成，根目录）
- [ ] `README.md` 改版（已完成，SEO 增强）
- [ ] `og-image.png`（待生成）
- [ ] `favicon.ico`（可选）
- [ ] GitHub 远端配置（待配置）
- [ ] GitHub Pages 开启（待操作）
- [ ] Google Search Console 验证（待提交）

> 完成后把这个 URL 发到：留学申请材料、比赛报名表、投资人邮件、社交媒体个人简介。

