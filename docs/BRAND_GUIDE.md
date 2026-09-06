# 码医 MediCode -- 品牌视觉规范手册

> 版本：v1.0  
> 日期：2026-05-25  
> 适用范围：码医 MediCode 全产品线（Web 平台、路演材料、文档、宣传品）  
> 品牌定位：B2B 医疗 AI SaaS -- 专业（医疗级）、创新（AI 驱动）、可信（金融/医保级）

---

## 1. 品牌定位

### 1.1 品牌使命（Mission）

让每一份病历都编码准确，让每一分医保基金都花在刀刃上。

### 1.2 品牌愿景（Vision）

成为中国医疗机构首选的 AI 编码与质控基础设施，推动 DRG 付费改革在全国范围内落地。

### 1.3 品牌价值观（Values）

| 价值观 | 关键词 | 行为准则 |
|--------|--------|---------|
| **精准** | Accuracy | 每一个编码有据可查，每一次判断可追溯 |
| **高效** | Efficiency | 用 AI 替代重复劳动，让编码员专注于决策 |
| **可信** | Trustworthiness | 技术透明、结果可审计，经得起监管审查 |
| **一体化** | Integration | 编码 + 分组 + 质控三合一，打破数据孤岛 |

### 1.4 品牌人格（Personality）

- **专业的医者** -- 严谨、权威、有一说一，不夸大
- **冷静的工程师** -- 数据驱动、逻辑清晰、系统化思考
- **可靠的风控官** -- 守护医保基金安全，不容有失

### 1.5 品牌承诺（Brand Promise）

一份病历进入码医系统，编码推荐、DRG 分组、质控报告和风险提示同时输出 -- 每个结果均可追溯，并由人工审核确认。

---

## 2. 品牌标识（Logo）规范

### 2.1 主标识构成

码医的 Logo 由两部分组成：
- **图形标**：36x36px 圆角方形（border-radius: 10px），渐变背景 `linear-gradient(135deg, #0ea5e9, #6366f1)`，内含白色 MedicineBox（医疗箱）图标
- **文字标**：中文 "码医" + 英文 "MediCode"，白色（深色背景）或深色（浅色背景），字间距 1px

### 2.2 Logo 变体

| 变体 | 使用场景 | 规格 |
|------|---------|------|
| **横向组合**（图标+文字横排） | 导航栏、页头、名片 | 图标 36px，文字 17px/700，间距 10px |
| **纵向组合**（图标上+文字下） | 登录页、启动屏 | 图标 72px（登录），间距 16px |
| **纯图标（Icon-only）** | Favicon、小尺寸位置 | 最小 32x32px |
| **纯文字（Wordmark）** | 文档页眉、水印 | 中文 "码医" + 英文 "MediCode" |

### 2.3 安全空间（Clear Space）

以图形标的高度为 1 单位，Logo 四周至少保留 **1 单位**的空白空间。登录页大图标（72px）安全空间为 72px。

### 2.4 最小尺寸

| 使用场景 | 最小高度 | 
|---------|---------|
| 屏幕显示（横向组合） | 24px（图标 16px） |
| 印刷品 | 15mm |
| Favicon | 16x16px（纯图标） |

### 2.5 使用禁忌

- 禁止拉伸、压缩、旋转 Logo
- 禁止改变 Logo 颜色（除黑白单色版本外）
- 禁止在低对比度背景上使用 Logo
- 禁止在 Logo 上叠加文字、纹理或阴影
- 禁止仅使用英文 "MediCode" 作为独立标识

---

## 3. 色彩体系（Color Palette）

### 3.1 主色系（Primary）

码医的品牌色为**天蓝到靛蓝渐变**，传达科技感与医疗纯净感。

| 色阶 | 色名 | Hex | CSS 变量 | 用途 |
|------|------|-----|---------|------|
| **Primary** | 天蓝 | `#0ea5e9` | `--brand-primary` | 主按钮、链接、选中态、主操作 |
| **Primary Dark** | 深天蓝 | `#0284c7` | `--brand-primary-dark` | 按钮 Hover、按压态 |
| **Primary Light** | 浅天蓝 | `#7dd3fc` | `--brand-primary-light` | 标签背景、Pulse 动画 |
| **Indigo** | 靛蓝 | `#6366f1` | `--brand-indigo` | 渐变终点、信息提示、高亮文字 |
| **Gradient** | 品牌渐变 | `linear-gradient(135deg, #0ea5e9, #6366f1)` | `--brand-gradient` | Logo、CTA 按钮、重点区域 |

### 3.2 背景色系（Background）

| 色阶 | 色名 | Hex | 用途 |
|------|------|-----|------|
| **Layout BG** | 浅灰蓝 | `#f0f5f9` | 内容区底色、页面背景 |
| **Container BG** | 纯白 | `#ffffff` | 卡片、表格、容器背景 |
| **Sidebar BG** | 深海军蓝 | `linear-gradient(180deg, #0f172a, #162d50)` | 侧边栏渐变背景 |
| **Menu Selected** | 暗蓝 | `#1e3a5f` | 菜单选中态 |
| **Menu Hover** | 深蓝 | `#1a2744` | 菜单悬停态 |

### 3.3 语义色彩（Semantic）

| 语义 | 主色 Hex | 浅色背景 | 用途 |
|------|---------|---------|------|
| **Success（成功/通过）** | `#10b981` | `#f6ffed` | 质控通过、操作成功、DRG 收入 |
| **Warning（警告/注意）** | `#f59e0b` | `#fffbe6` | 质控一般问题、注意提示 |
| **Warning Strong（重要）** | `#fa8c16` | `#fff7e6` | 质控重要问题 |
| **Error（错误/严重）** | `#ef4444` | `#fff2f0` | 质控严重缺陷、操作失败、医保拒付风险 |
| **Info（信息/提示）** | `#6366f1` | `#f0f5ff` | 质控提示、一般信息 |

### 3.4 文本色系（Text）

| 色阶 | 色名 | Hex | 用途 |
|------|------|-----|------|
| **Primary** | 主文本 | `#1e293b` | 标题、正文 |
| **Secondary** | 次要文本 | `#64748b` | 辅助说明、描述文字 |
| **Tertiary** | 禁用/占位 | `#94a3b8` | 输入框占位符、禁用文字 |
| **White Primary** | 深色底白字 | `#ffffff` | 侧边栏文字、按钮白色文字 |

### 3.5 分割线与边框

| 色名 | Hex | 用途 |
|------|-----|------|
| Border Light | `#f0f0f0` | 页头下边框 |
| Border Default | `#e8edf2` | 卡片边框、表格边框 |
| Sidebar Border | `rgba(255,255,255,0.06)` | 侧边栏分割线 |

### 3.6 色彩使用规则

1. **主按钮**必须使用品牌渐变 `linear-gradient(135deg, #0ea5e9, #6366f1)`，不可使用纯色
2. **成功/错误状态**使用语义色，不可与品牌蓝混用
3. **数据可视化**优先使用语义色，详见第 9 章图表规范
4. **暗色背景**上文字必须使用白色或半透明白色（opacity 0.3-0.5），确保 WCAG AA 对比度

---

## 4. 字体排印（Typography）

### 4.1 字体族（Font Family）

```css
/* 主字体 -- 品牌标准 */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
             'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB',
             sans-serif;

/* 等宽字体 -- 代码、病历文本、数字 */
font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code',
             'Consolas', 'Courier New', monospace;
```

### 4.2 中文字体回落链（Chinese Font Fallback）

优先级：**PingFang SC**（macOS/iOS） > **Microsoft YaHei**（Windows） > **Hiragino Sans GB**（旧版 macOS）

关键原则：西文在前、中文在后。Inter 处理西文和数字，PingFang SC / Microsoft YaHei 处理中文。此顺序确保中西文混排时视觉协调。

### 4.3 字号层级（Heading Scale）

| 层级 | 字号 | 字重 | 行高 | 字间距 | 使用场景 |
|------|------|------|------|--------|---------|
| **H1** | 28px | 700 | 1.4 | -0.5px | 页面大标题（罕见使用） |
| **H2** | 24px | 600 | 1.4 | 0 | 登录页品牌名 |
| **H3** | 20px | 600 | 1.4 | 0 | 各功能页标题 |
| **H4** | 16px | 600 | 1.5 | 0 | 卡片标题、区块标题 |
| **H5** | 14px | 500 | 1.5 | 0 | 小标题 |
| **Body** | 14px | 400 | 1.6 | 0 | 正文、段落 |
| **Small** | 12-13px | 400 | 1.5 | 0 | 辅助说明、标签 |
| **Caption** | 10-11px | 400 | 1.4 | 0 | 侧边栏脚注、提示文字 |

### 4.4 代码/数据字体使用规则

- **病历文本输入框**：等宽字体，13px（模拟医疗信息系统终端感）
- **ICD 编码显示**：`<Text code>` 组件，自动使用等宽字体
- **金额数字**：`tabular-nums`，字间距 `-0.5px`，确保数字对齐
- **统计数字（Statistic）**：28px 大标题 + 14px 次级文字

### 4.5 排版规则

1. 中文段落首行不缩进
2. 中西文混排时，西文单词两侧各留一个半角空格（如 "DRG 编码"）
3. 数字与单位之间不加空格（如 "28px"）
4. 中文使用全角标点，英文使用半角标点
5. 页面标题层级不超过 3 层

---

## 5. 图标系统（Iconography）

### 5.1 图标库

统一使用 **Ant Design Icons 5.x**（`@ant-design/icons`），不再引入其他图标库。

### 5.2 功能图标语义映射

| 功能模块 | 图标 | 颜色 | 说明 |
|---------|------|------|------|
| 智能流水线 | `ThunderboltOutlined` | `#0ea5e9` | AI 速度感 |
| 编码工作台 | `FileTextOutlined` | `#1677ff` | 文档/病历 |
| DRG 分组 | `MedicineBoxOutlined` | `#722ed1` | 医疗/分组 |
| 质控中心 | `SafetyCertificateOutlined` | `#52c41a` | 盾牌/质量 |
| 数据驾驶舱 | `DashboardOutlined` | `#0ea5e9` | 仪表/监控 |
| 系统设置 | `SettingOutlined` | `#64748b` | 齿轮/设置 |
| 使用指南 | `ReadOutlined` | `#64748b` | 文档/帮助 |
| 用户头像 | `UserOutlined` | `#fff` | 账户 |
| 退出登录 | `LogoutOutlined` | `#ff4d4f` | 登出 |

### 5.3 图标尺寸规范

| 场景 | 尺寸 | 圆角（如有背景） |
|------|------|-----------------|
| 菜单图标 | 14px | -- |
| 卡片标题图标 | 16px | -- |
| 按钮内图标 | 14-16px | -- |
| 空状态图标 | 56-64px | -- |
| Logo 内图标 | 18px（侧边栏）/ 36px（登录页） | 10px / 18px |
| 统计卡片图标 | 20-24px | -- |

### 5.4 自定义图标规范

如需创建自定义图标（未来场景）：
- 风格：线性（Outlined），与 Ant Design Icons 保持一致
- 笔画宽度：1.5-2px
- 圆角端点：round cap / round join
- 画布尺寸：1024x1024px（SVG viewBox）
- 导出格式：SVG（优先）、PNG 2x

---

## 6. 间距系统（Spacing）

### 6.1 基础网格

基于 **4px 基准网格**，所有间距为 4 的倍数。

| Token 名称 | 值 | CSS 变量 | 使用场景 |
|-----------|-----|---------|---------|
| `space-xs` | 4px | `--space-xs` | 图标与文字间距、紧密元素 |
| `space-sm` | 8px | `--space-sm` | 表单项间距、标签排列 |
| `space-md` | 16px | `--space-md` | 卡片间距（gutter）、区块内边距 |
| `space-lg` | 24px | `--space-lg` | 页面内容区内边距、大区块间距 |
| `space-xl` | 32px | `--space-xl` | 页头与内容间距 |
| `space-2xl` | 48px | `--space-2xl` | 页面级大区块分割 |
| `space-3xl` | 64px | `--space-3xl` | 页面上下留白（罕见） |

### 6.2 组件内间距规范

| 组件 | 内边距 | 外间距 |
|------|--------|--------|
| **页面内容区** | padding: 24px | margin: 16px |
| **卡片（Card body）** | padding: 24px（大型）/ 16px（小型） | margin-bottom: 16px |
| **表格单元格** | padding: 8px 16px | -- |
| **按钮（大）** | height: 44-48px, padding: 0 24px | -- |
| **输入框（大）** | height: 44px, padding: 0 12px | margin-bottom: 16px |
| **Divider** | -- | margin: 12-16px 上下 |

### 6.3 栅格系统

使用 Ant Design `Row` / `Col` 24 栏栅格：
- **标准栏间距**：`gutter={16}` 或 `gutter={24}`
- **页面左右布局**：`span={10}` + `span={14}`（如编码页、质控页）或 `span={12}` + `span={12}`
- **统计卡片行**：`span={4}` x 6 或 `span={6}` x 4

---

## 7. 组件样式规范（Component Patterns）

### 7.1 按钮（Button）

```css
/* 主按钮（Primary）-- 必须有品牌渐变 */
background: linear-gradient(135deg, #0ea5e9, #6366f1);
border: none;
border-radius: 8px;
height: 44px;          /* large 尺寸 */
font-weight: 600;
box-shadow: 0 2px 8px rgba(14, 165, 233, 0.35);

/* Hover */
box-shadow: 0 4px 16px rgba(14, 165, 233, 0.45);

/* 次按钮（Default/Outline） */
background: #ffffff;
border: 1px solid #d9d9d9;
border-radius: 8px;
```

按钮状态层级（视觉权重从上到下）：
1. **Primary Gradient**（CTA 主操作）：开始分析、登录、快速演示
2. **Primary Ghost**（次要确认）：表格内"采纳"
3. **Default**（常规操作）：上传文件、检索、清除筛选
4. **Text / Link**（轻量操作）：API 文档、重新演示
5. **Danger Text**（删除/忽略）：退出登录、忽略缺陷

### 7.2 卡片（Card）

```css
/* 标准卡片 */
border: 1px solid #e8edf2;
border-radius: 12px;         /* Content area */
border-radius: 16px;         /* Login card */
background: #ffffff;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

/* Hover */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
transform: translateY(0);    /* 可选微上浮 */

/* 特殊状态卡片 */
.pipeline-card-processing    { border-left: 3px solid #0ea5e9; }  /* 处理中 */
.pipeline-card-complete      { border-left: 3px solid #10b981; }  /* 已完成 */
```

卡片类型：
- **标准卡片**：标题 + 内容，白色背景
- **统计卡片**：居中统计数字，`hoverable` 可点击
- **流程卡片**：左侧 3px 色带标识状态
- **收入卡片**：浅绿色渐变背景 `linear-gradient(135deg, #f6ffed, #f0fff0)`

### 7.3 表格（Table）

```css
/* 表头 */
background: #f8fafc;
color: #475569;
font-weight: 600;
font-size: 13px;

/* 行悬停 */
background: #f0f9ff;

/* 尺寸 */
默认: size="small"（内页表格）
```

表格使用规则：
- 功能页内表格使用 `size="small"`，节省纵向空间
- 数字列右对齐，文本列左对齐
- 排名列：前三名使用金银铜色（`#faad14` / `#999` / `#c47f3c`）
- 空数据使用 `<Empty />` 组件，不可留白

### 7.4 表单输入（Form Input）

```css
/* 输入框 */
border-radius: 8px;
height: 44px;            /* 大号输入框 */
font-size: 14px;
border: 1px solid #d9d9d9;

/* 前缀图标 */
color: #94a3b8;

/* 文本域 */
font-family: monospace;
font-size: 13px;
border-radius: 8px;

/* 只读/演示模式 */
background: #fafeff;
border-color: #0ea5e9;
```

### 7.5 标签/徽章（Tag / Badge）

```css
/* 标准标签 */
border-radius: 4px;
font-weight: 500;

/* 胶囊标签（功能标签） */
border-radius: 20px;
padding: 2px 12px;
```

标签色彩语义：
- **Blue**：AI 功能标签（NLP 智能编码）、信息提示
- **Green**：成功状态、质控通过
- **Orange**：重要警告、质控重要问题
- **Red**：严重缺陷、医保拒付风险
- **Gold**：一般缺陷
- **Purple**：DRG 分组相关
- **Processing**（动画）：进行中状态

### 7.6 进度条与步骤条（Progress / Steps）

```css
/* 步骤条 */
.ant-steps-item-finish .ant-steps-item-icon {
  background: #10b981;       /* 已完成 = 绿色 */
  border-color: #10b981;
}
.ant-steps-item-process .ant-steps-item-icon {
  background: #0ea5e9;       /* 进行中 = 品牌蓝 */
  border-color: #0ea5e9;
}

/* 仪表盘进度 */
.ant-progress-dashboard {
  stroke: 基于分数着色:
    >= 90: #52c41a (绿)
    >= 70: #fa8c16 (橙)
    < 70:  #ff4d4f (红)
}
```

---

## 8. 数据可视化（Data Visualization）

### 8.1 图表色彩序列（ECharts Color Palette）

按优先级排列（用于多系列图表）：

| 序号 | 色值 | 色名 | 场景 |
|------|------|------|------|
| 1 | `#1677ff` | 图表蓝 | 主要数据系列（AI准确率、质控评分） |
| 2 | `#52c41a` | 图表绿 | 第二数据系列（CMI、收入） |
| 3 | `#fa8c16` | 图表橙 | 对比系列（人工编码） |
| 4 | `#722ed1` | 图表紫 | 第四系列 |
| 5 | `#13c2c2` | 青色 | 第五系列 |
| 6 | `#f5222d` | 图表红 | 预警/异常系列 |

### 8.2 折线图（Line Chart）

```javascript
{
  series: [{
    type: 'line',
    smooth: true,            // 平滑曲线 -- 医疗数据需要这种柔和感
    areaStyle: { opacity: 0.15 },  // 半透明面积填充
    itemStyle: { color: '#1677ff' },
    lineStyle: { width: 2 },
    symbol: 'circle',
    symbolSize: 4,
  }]
}
```

### 8.3 柱状图（Bar Chart）

```javascript
{
  series: [{
    type: 'bar',
    itemStyle: { color: '#1677ff' },
    barWidth: '60%',         // 适中宽度，不过细不过粗
    barGap: '30%',
  }]
}
```

### 8.4 饼图/环形图

不使用饼图。所有单值占比展示使用 Ant Design `<Progress type="dashboard">`（仪表盘样式）。

### 8.5 仪表盘进度（Dashboard Progress）

- **质控评分**使用仪表盘进度，分数区间着色：
  - 90-100：绿色 `#52c41a`，文字显示"优秀"
  - 70-89：橙色 `#fa8c16`，文字显示"良好"
  - <70：红色 `#ff4d4f`，文字显示"需改进"
- 尺寸：120px（大）/ 100px（中）

### 8.6 图表通用规范

- 所有图表必须包含 `aria: { enabled: true }` 无障碍支持
- X 轴日期标签：小于等于 30 天显示 `MM-DD`，超过 30 天显示 `YYYY-MM`
- Y 轴数值：百分比格式化为 `(v*100).toFixed(0) + '%'`，金额超过 10000 除以 10000 加"万元"
- Tooltip 必须启用（`trigger: 'axis'` 或 `trigger: 'item'`）
- 多 Y 轴时使用 `yAxisIndex` 区分
- Grid 留白：left 60-80px（Y 轴标签空间），right 20-60px

---

## 9. 文案规范（Voice & Tone）

### 9.1 品牌中文名称

**码医**（Ma Yi）-- "码"取编码之义，"医"为医疗领域。二字简洁有力，直接传达产品功能。

### 9.2 品牌英文名称

**MediCode** -- Medical + Code 的合成词。首字母大写，CamelCase 风格。使用时始终与中文名同时出现："码医 MediCode"。

### 9.3 品牌标语（Tagline）

```
AI驱动 · DRG编码 · 病历质控 · 医保支付
```

使用间隔号（·）分隔四个关键词，简洁传达产品核心价值。不换行、不使用其他分隔符。

### 9.4 文案风格原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **专业准确** | 使用医疗/DGR 专业术语，不错用 | "主要诊断编码"而非"主病编码" |
| **简洁直接** | B2B 不需要营销修辞，说清楚功能和价值即可 | "400 份注入式质控基准：缺陷召回 100%（17/17 规则）"，用可核验的数字说话 |
| **数据说话** | 能用量化数据就不用形容词 | "年节省 100 万+"而非"大幅节省成本" |
| **行动导向** | 按钮和提示用动词引导操作 | "开始智能分析"而非"点击这里分析" |
| **拒绝制造焦虑** | 医疗场景不用恐吓式文案 | "发现 3 个待完善项"而非"你的病历有 3 个严重错误" |
| **拒绝假大空** | 不用"赋能""升级""重构"等空洞词汇 | "用 AI 自动完成编码"而非"AI 赋能编码体验升级" |

### 9.5 场景文案模板

**空状态（Empty State）**：
```
粘贴病历内容，点击"开始智能分析"查看完整的编码→质控→DRG→付费流水线
```

**加载状态（Loading）**：
```
AI分析中...（使用 Spin 组件 + 文案）
```

**成功状态（Success）**：
```
全流程分析完成
编码完成，共识别 3 个诊断 + 1 个手术
```

**错误状态（Error）**：
```
分析失败，请重试
部分数据加载失败，已显示可用数据
```

### 9.6 术语规范表

| ✅ 正确用法 | ❌ 禁止用法 |
|------------|------------|
| 病历 | 病例（"病例"仅用于医学讨论） |
| 质控检查/质控审核 | 质量检查 |
| 编码员 | 打字员/录入员 |
| 医保支付 | 保险报销 |
| DRG 分组 | DRG 分类 |
| ICD-10 编码 | ICD10 编码 |
| 诊断编码 | 病种编码 |

---

## 10. 品牌资产保护（Brand Protection）

### 10.1 文件命名规范

```
medicode-{资产类型}-{用途}-{尺寸}.{格式}

示例：
medicode-logo-horizontal-200px.png
medicode-banner-competition-1920x1080.png
medicode-icon-favicon-32x32.png
```

### 10.2 品牌检查清单

每次发布前验证：
- [ ] 所有 Logo 使用规范版本，安全空间符合要求
- [ ] 配色使用品牌色板内的颜色，无自定义颜色
- [ ] 字体使用规范字体栈，中英文回落正确
- [ ] 间距符合 4px 网格
- [ ] 按钮主操作使用品牌渐变
- [ ] 图表使用规范的图表配色序列
- [ ] 文案符合品牌口吻，无禁用词汇
- [ ] 暗色背景文字对比度达标

### 10.3 竞品差异化视觉原则

码医是**B2B 医疗 AI SaaS**，不是消费级应用。视觉上必须区别于：
- **消费医疗 App**（过于活泼的颜色、圆润设计）-- 我们的设计更理性、克制
- **传统 HIS 系统**（老旧界面、高密度信息）-- 我们的设计更现代、有呼吸感
- **纯技术工具**（极客风格、缺乏温度）-- 我们的设计保留医疗的严谨与人文关怀

核心视觉策略：**深色侧边栏 + 明亮内容区**，形成专业稳重与高效操作的视觉双层结构。

---

## 附录 A：CSS 变量速查表

```css
:root {
  /* Brand Colors */
  --brand-primary: #0ea5e9;
  --brand-primary-dark: #0284c7;
  --brand-primary-light: #7dd3fc;
  --brand-indigo: #6366f1;
  --brand-gradient: linear-gradient(135deg, #0ea5e9, #6366f1);

  /* Background */
  --bg-layout: #f0f5f9;
  --bg-container: #ffffff;
  --bg-sidebar-start: #0f172a;
  --bg-sidebar-end: #162d50;

  /* Semantic */
  --success: #10b981;
  --success-bg: #f6ffed;
  --warning: #f59e0b;
  --warning-strong: #fa8c16;
  --error: #ef4444;
  --info: #6366f1;

  /* Text */
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-tertiary: #94a3b8;
  --text-white: #ffffff;

  /* Border */
  --border-light: #f0f0f0;
  --border-default: #e8edf2;

  /* Spacing (4px base) */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 20px;

  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Courier New', monospace;

  /* Font Sizes */
  --text-h1: 28px;
  --text-h2: 24px;
  --text-h3: 20px;
  --text-body: 14px;
  --text-small: 12px;
  --text-caption: 10px;
}
```

---

## 附录 B：品牌文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 品牌规范手册 | `docs/BRAND_GUIDE.md` | 本文档 |
| PPT 设计大纲 | `docs/PPT_OUTLINE.md` | 路演 PPT 视觉规范 |
| 竞赛策略 | `docs/COMPETITION_STRATEGY.md` | 比赛策略与 Demo 脚本 |
| 全局样式 | `frontend/src/styles/global.css` | CSS 实现 |
| Ant Design 主题 | `frontend/src/main.tsx` | ConfigProvider 主题配置 |

---

> **Brand Guardian 签字**：本手册是码医 MediCode 品牌的唯一视觉规范来源。所有产品界面、路演材料、文档和宣传品的设计与开发必须以此为准。对规范的任何修改需要经过品牌策略评审。
