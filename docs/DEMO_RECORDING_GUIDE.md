# Demo 录屏制作指南 · 码医 MediCode

> 比赛现场评委没时间看 4 页 PPT，一段 30-60 秒的 demo GIF 胜过千言万语。
> 本指南给出工具选择、场景设计、操作流程、后期处理、README 嵌入全套方案。

---

## 一、工具选择（按推荐度排序）

### 🥇 方案 A：ScreenToGif（最简单）

| 项 | 说明 |
|---|------|
| 下载 | https://www.screentogif.com/（免费、开源、Windows 原生） |
| 录屏 | 直接拖框选区域 → 自动录屏 |
| 编辑 | 内置编辑器，可加字幕/裁剪/调速 |
| 导出 | GIF / MP4 / APNG |
| **适合** | 30-60 秒短 demo，快速出片 |

```powershell
# 安装（用 winget）
winget install NickeManarin.ScreenToGif
```

### 🥈 方案 B：OBS Studio + ffmpeg（最专业）

| 项 | 说明 |
|---|------|
| OBS | 录屏工具，输出 MP4（高画质、可后期） |
| ffmpeg | 视频转 GIF + 压缩 |
| **适合** | 需要 1080p 高清 + 后期加字幕/转场 |

```powershell
# 安装
winget install OBSProject.OBSStudio
winget install Gyan.FFmpeg
```

### 🥉 方案 C：PowerPoint 录屏（最应急）

| 项 | 说明 |
|---|------|
| 操作 | 插入 → 屏幕录制 → 选区 → 录制 |
| 输出 | MP4（PowerPoint 内嵌） |
| 限制 | 只能录单页，要导出得用 ffmpeg 转 GIF |

---

## 二、场景设计

### 推荐 30 秒精简版（README 顶部用）

| 时间 | 画面 | 配音/字幕 |
|------|------|----------|
| 0-3s | 登录页 | "码医 MediCode — AI 医疗编码与病历质控" |
| 3-5s | 输入 `admin` / `123456` 登录 | 字幕：密码 123456 |
| 5-8s | 智能流水线页加载 | （静默） |
| 8-10s | 点击"快速演示"按钮 | 字幕：1 秒完成全流程 |
| 10-20s | 4 步 pipeline 自动执行（Steps 高亮） | 字幕：智能编码 → 质控 → DRG → 拒付预测 |
| 20-28s | 4 个结果卡依次展开（编码 / 质控 / DRG / 拒付） | 字幕：95%+ 准确率 / 100+ 规则 / CHS-DRG 1.2 / 拒付预警 |
| 28-30s | 鼠标滚到底部，展示总览 | 字幕：全国 3000+ 二级以上医院适用 |

### 60 秒完整版（比赛答辩用）

在 30 秒基础上扩展：
- 0-10s：增加"病历输入 → 文件上传 .txt"演示
- 10-30s：增加"手工分析"模式（不用快速演示）
- 30-50s：4 个结果卡完整展示 + 数据悬停
- 50-60s：切到"数据驾驶舱"页（CMI/科室对比）

### 90 秒深度版（路演 + 1v1 答辩用）

- 0-15s：病历上传 + 解析（PDF）
- 15-45s：4 步 pipeline（含 LLM 实时推荐）
- 45-75s：质控 + DRG + 拒付预测完整展示
- 75-90s：数据驾驶舱 + ROI 计算

---

## 三、完整操作流程（30 秒精简版）

### 录屏前准备

1. **清场** — 关闭无关窗口、通知、任务栏
2. **窗口** — 浏览器固定 1440×900，按 F11 进全屏
3. **数据** — 确认 500 条种子数据已植入（首次启动自动）
4. **配色** — 浏览器深色模式（如果浏览器支持）
5. **字体** — 提前在浏览器里测试，等宽字体清晰

### 录屏操作步骤

```text
[Step 1] 浏览器打开 http://localhost:5173
         → 自动跳到登录页
         → 录屏开始

[Step 2] 输入用户名 admin
         输入密码 123456
         点击「进入系统」按钮
         → 跳到 /pipeline（默认编码员）/dashboard（默认管理员）

[Step 3] 智能流水线页加载完成
         → 鼠标移到右上角"快速演示"按钮
         → 高亮 1 秒
         → 点击

[Step 4] 系统自动：
         - 粘贴 4 号病历"腹痛待查"
         - 触发 4 步 pipeline
         - Steps 高亮 NLP→编码→质控→DRG→拒付
         - 4 个结果卡依次展开

[Step 5] 鼠标滚到底
         → 展示 DRG 分组结果、医保支付金额、拒付风险评分
         → 静止 3 秒让评委看清数据

[Step 6] 录屏结束
```

### 录屏小技巧

- ✅ **录 2-3 遍**挑最好的
- ✅ **每步停顿 1-2 秒**让评委看清
- ✅ **鼠标轨迹**保留（不要快速滑动）
- ✅ **关键按钮**点击前高亮 0.5 秒
- ❌ **不要录错误**（登录失败、404 等）
- ❌ **不要录加载慢**的 spinner（可后期加速）

---

## 四、后期处理

### 4.1 压缩到合适大小（关键！）

GitHub README 限制 5MB，演示 GIF 建议 **2-4MB**：

```powershell
# 用 ffmpeg 压缩（高画质+小体积）
ffmpeg -i input.mp4 -vf "fps=15,scale=1280:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 -lossless 0 output.gif

# 如果还太大，降到 10 fps
ffmpeg -i input.mp4 -vf "fps=10,scale=1024:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output.gif
```

**体积对照表**（30 秒，1440×900）：

| fps | 宽度 | 大小 |
|-----|------|------|
| 15 | 1280 | 2-4 MB ✅ |
| 10 | 1024 | 1-2 MB ✅ |
| 8  | 800  | 0.5-1 MB |

### 4.2 加字幕（可选）

用 ScreenToGif 编辑器直接添加文字层；或用 ffmpeg + ASS 字幕文件：

```powershell
ffmpeg -i input.gif -vf "subtitles=subtitles.ass" output.gif
```

### 4.3 加速长内容（90 秒版推荐）

```powershell
# 整体加速 1.5x
ffmpeg -i input.mp4 -filter:v "setpts=0.667*PTS" -an output.mp4
```

---

## 五、嵌入 README

### 5.1 文件存放

```
project/
├── assets/
│   ├── demo-30s.gif          ← 30 秒精简版（README 用）
│   ├── demo-60s.mp4          ← 60 秒完整版（比赛答辩用）
│   └── demo-poster.png       ← 静态封面（不支持 GIF 预览时 fallback）
```

### 5.2 README 代码

```markdown
## 🎬 Demo 演示

![码医 MediCode 30 秒 demo](./assets/demo-30s.gif)

> 📺 60 秒完整版（含病历上传、4 步分析、数据驾驶舱）：[demo-60s.mp4](./assets/demo-60s.mp4)
```

### 5.3 GitHub Pages 嵌入（如果做了官网）

```html
<video autoplay loop muted playsinline>
  <source src="/assets/demo-60s.mp4" type="video/mp4">
</video>
```

---

## 六、产出清单

录制完成后应该有以下文件：

- [ ] `assets/demo-30s.gif`（README 必用，< 4MB）
- [ ] `assets/demo-60s.mp4`（答辩备用，< 20MB）
- [ ] `assets/demo-poster.png`（GIF 静态封面，< 500KB）
- [ ] 微信视频号上传（路演分享用）

---

## 七、紧急备选方案

如果时间紧 / 录屏出问题：

### 备选 1：截图轮播（5 分钟搞定）

用 Windows 自带 `截图工具` 截 8-10 张关键界面 + PPT 拼图，导出 PNG。放 README 用图片序列。

### 备选 2：PPT 动画（10 分钟搞定）

把 demo 录屏的关键帧截图直接放到 PPT 里，加切换动画。比赛现场 1 秒钟"播放"一张。

### 备选 3：录屏 + 直接说（最差但能用）

比赛现场用 OBS 实时录屏 + 配音 60 秒，不做后期。能展示流程就行。

---

> 💡 **建议优先级**：30s GIF > 60s MP4 > PPT 截图 > 现场录屏
> 比赛前至少要有 1 个可演示素材，不要纠结画质。

