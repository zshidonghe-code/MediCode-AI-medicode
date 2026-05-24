"""Generate 码医-MediCode 商业计划书 .docx file."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.8)

style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.35
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

for level in range(1, 4):
    h = doc.styles[f'Heading {level}']
    h.font.name = '微软雅黑'
    h.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    h.font.color.rgb = RGBColor(0x0E, 0xA5, 0xE9)
    h.font.bold = True
    if level == 1:
        h.font.size = Pt(22)
        h.paragraph_format.space_before = Pt(24)
        h.paragraph_format.space_after = Pt(12)
    elif level == 2:
        h.font.size = Pt(16)
        h.paragraph_format.space_before = Pt(20)
        h.paragraph_format.space_after = Pt(8)
    elif level == 3:
        h.font.size = Pt(13)
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)


def add_para(text, bold=False, italic=False, size=None, color=None, alignment=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if bold: run.bold = True
    if italic: run.italic = True
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = RGBColor(*color)
    if alignment is not None: p.alignment = alignment
    return p


def add_table_simple(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.name = '微软雅黑'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r + 1].cells[c]
            cell.text = ''
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
            run.font.name = '微软雅黑'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    doc.add_paragraph()


def add_divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run('─' * 60)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    run.font.size = Pt(8)


def add_bullet(text):
    p = doc.add_paragraph(style='List Bullet')
    p.clear()
    run = p.add_run(text)
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = Pt(11)


# ═══════════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════════

for _ in range(6):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('码医 MediCode')
run.font.size = Pt(38)
run.font.color.rgb = RGBColor(0x0E, 0xA5, 0xE9)
run.font.name = '微软雅黑'
run.bold = True
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('AI医疗DRG编码与病历质控系统')
run.font.size = Pt(20)
run.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

doc.add_paragraph()
doc.add_paragraph()

subtitle2 = doc.add_paragraph()
subtitle2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle2.add_run('商 业 计 划 书')
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

for _ in range(4):
    doc.add_paragraph()

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run('郑诗东和 · 上海对外经贸大学\n2026年5月')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 执行摘要
# ═══════════════════════════════════════════════════

doc.add_heading('执行摘要', level=1)

add_para('码医（MediCode）是一款面向医院的AI驱动ICD编码与病历质控一体化SaaS平台。'
         '系统通过NLP+大语言模型技术，自动完成住院病历的诊断编码推荐、DRG付费分组和病历内涵质控，'
         '帮助医院提升编码准确率、避免医保拒付损失、降低质控人力成本。')

add_para('项目核心价值主张：', bold=True)
add_bullet('技术价值：基于开源大模型+自研医学知识库，编码推荐准确率目标95%+，填补市场空白')
add_bullet('商业价值：DRG/DIP付费改革是国家级刚需，每家医院年均编码损失100万+，我们的系统ROI超过6:1')
add_bullet('社会价值：帮助医保基金精准支付，全国推广每年可节省数百亿医保资金浪费')

add_para('产品目前已开发完成可运行系统（FastAPI + React全栈），包含智能编码引擎、DRG分组器、质控引擎、'
         '数据驾驶舱、Pipeline演示模式等完整功能。准备参加中国国际"互联网+"大学生创新创业大赛。')

add_table_simple(['项目信息', '内容'], [
    ['项目名称', '码医 MediCode'],
    ['所属赛道', '互联网+大学生创新创业大赛 / 高教主赛道 / 本科生创意组'],
    ['技术领域', '人工智能 + 医疗信息化 + 自然语言处理'],
    ['当前阶段', 'MVP完整开发完成，可运行可演示'],
    ['团队', '郑诗东和（负责人）+ AI Agent技术团队'],
    ['目标', '全国大学生创业大赛第一名'],
])

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 一、市场分析
# ═══════════════════════════════════════════════════

doc.add_heading('一、市场分析', level=1)

doc.add_heading('1.1 政策背景：DRG/DIP付费改革', level=2)

add_para('2021年，国务院办公厅发布《关于推动公立医院高质量发展的意见》，明确提出全面推行DRG/DIP付费方式。'
         '根据国家医保局规划，2025年底前DRG/DIP将覆盖所有符合条件的住院医疗机构。')

add_para('这意味着一个根本性的变化：以前医院"看多少病、收多少钱"，现在是"每个病种有一个固定的医保支付价"。'
         '病历的ICD编码直接决定了DRG分组，DRG分组决定了医保支付金额。编码错了，医院亏钱；编码漏了，医院少收。')

doc.add_heading('1.2 市场规模测算', level=2)

add_para('目标客户：全国二级以上公立医院。')

add_table_simple(['医院等级', '数量', '年均编码量', '付费意愿', '年市场空间'], [
    ['三级医院', '3,200+', '10-20万份', '25万/年', '8亿'],
    ['二级医院', '10,000+', '2-5万份', '8-15万/年', '12亿'],
    ['民营医院（二级+）', '2,000+', '1-5万份', '5-10万/年', '2亿'],
    ['合计', '15,000+', '—', '—', '22亿/年'],
])

add_para('保守估计，可及市场空间约22亿/年。若考虑基层医疗机构和区域卫生平台，长期市场空间可达45亿/年。')

doc.add_heading('1.3 痛点分析：为什么医院需要这个产品', level=2)

add_table_simple(['痛点', '现状', '后果', '我们的解决方案'], [
    ['编码员严重不足', '全国缺口超10万人，三甲医院需10+人实有3-5人',
     '每人日处理50-80份，疲劳出错', 'AI自动编码，秒级输出，置信度+备选推荐'],
    ['编码错误率高', '人工错误率10-15%，主诊断选错直接损失数千元',
     '医保拒付+飞检罚款+倒查3年', 'NLP+LLM四层推荐策略，高置信度优先'],
    ['质控覆盖率低', '传统人工抽查覆盖率<10%',
     '80%+问题病历未被发现，成为飞检定时炸弹', 'AI全量质控，100+规则全覆盖'],
    ['数据不互通', '编码/DRG/质控三套系统三个供应商',
     '信息割裂，反复录入，效率低', '三合一平台，一份病历全流程输出'],
])

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 二、产品方案
# ═══════════════════════════════════════════════════

doc.add_heading('二、产品方案', level=1)

doc.add_heading('2.1 产品定位', level=2)

add_para('码医是一站式AI医疗编码与质控工作台。定位关键词：三合一、私有化部署、AI驱动。')

add_para('与市面上单一功能工具不同，码医将ICD编码、DRG分组、病历质控三个环节整合到一条流水线中——'
         '一份病历输入，秒级输出编码结果+DRG分组+质控报告+预估支付金额。')

doc.add_heading('2.2 核心功能模块', level=2)

add_table_simple(['模块', '输入', '输出', '核心技术'], [
    ['智能ICD编码引擎', '病历全文', '主诊断+次要诊断+手术编码（各附置信度）',
     'NLP实体识别 + 300+诊断/113手术映射 + TF-IDF语义检索 + LLM推荐'],
    ['DRG自动分组器', 'ICD编码+患者信息', 'MDC/ADRG/DRG编码+权重+预估支付金额',
     'CHS-DRG 1.2规则引擎 + CC/MCC逻辑 + 费率计算'],
    ['病历质控引擎', '病历+编码结果', '缺陷清单（级别+描述+建议）+质控评分',
     '15+规则引擎 + LLM语义检查 + 6级缺陷分级'],
    ['智能流水线', '病历文本/文件', '编码→QC→DRG→费用一键串联',
     '4步可视化流程 + 演示模式 + 结果自动保存'],
    ['数据驾驶舱', '全量运营数据', '6类可视化图表（CMI/DRG/QC/收入）',
     'ECharts动态图表 + 日期范围筛选 + 科室排行'],
    ['系统管理', '管理员指令', '数据预览/重置/导出(JSON/CSV)',
     '外键安全删除 + 双重鉴权 + 预览确认机制'],
])

doc.add_heading('2.3 技术架构亮点', level=2)

add_para('1. LLM + 规则引擎双后端', bold=True)
add_para('Ollama（Qwen2.5）本地部署，用于编码推荐和语义质控。规则引擎自动兜底——'
         '当LLM不可用时（无GPU/网络受限），系统核心功能不受影响。健康检查端点实时监控。')

add_para('2. ICD数据源统一管理', bold=True)
add_para('300+诊断编码和113+手术编码以JSON格式集中管理，所有消费者（编码器、种子脚本）从同一数据源加载，'
         '避免多处维护和数据不一致。')

add_para('3. 全私有化部署', bold=True)
add_para('整套系统可部署在医院内网，病历数据不出院。Docker Compose一键启动，'
         '支持SQLite（免运维）和PostgreSQL（企业级）两种数据库。')

add_para('4. Pipeline结果自动持久化', bold=True)
add_para('流水线分析结果自动写入数据库，数据驾驶舱实时反映最新使用情况。'
         'QC采纳/忽略操作持久化，刷新不丢失状态。')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 三、商业模式
# ═══════════════════════════════════════════════════

doc.add_heading('三、商业模式', level=1)

doc.add_heading('3.1 收入模型', level=2)

add_table_simple(['模式', '定价', '目标客户', '特点'], [
    ['SaaS订阅（标准版）', '8万/年（<500床）\n15万/年（500-1500床）\n25万/年（>1500床）',
     '中小型医院', '按年续费，含自动升级和远程支持'],
    ['私有化部署（企业版）', '30-80万（一次性授权）\n+ 年维保费20%',
     '大型三甲医院', '数据不出院，定制化集成'],
    ['增值服务', '10-20万/年', '需深度定制医院',
     'HIS/EMR系统对接、定制规则开发'],
])

doc.add_heading('3.2 单位经济模型', level=2)

add_para('以500床中型医院为基准单元：')
add_bullet('年付费：15万元')
add_bullet('部署成本：0.5万元（远程部署，1天完成）')
add_bullet('年运维成本：1万元（服务器+模型更新+技术支持）')
add_bullet('毛利：约90%（纯软件，边际成本低）')
add_bullet('客户LTV：75万元（5年留存 × 15万/年）')
add_bullet('获客成本（CAC）：3-5万元（渠道分销+试用转化）')
add_bullet('LTV/CAC：15-25倍（极健康的商业模型）')

doc.add_heading('3.3 推广路径', level=2)

add_para('第一年：种子客户（10家）', bold=True)
add_bullet('路径：创业大赛影响力 + 个人联系 + 学术会议展示')
add_bullet('策略：3个月免费试用 → 效果数据说话 → 付费转化')
add_bullet('目标：签约10家医院，实现年营收100万+')

add_para('第二年：区域扩张（50家）', bold=True)
add_bullet('路径：已签约医院的医联体/医共体内推荐 + 区域代理商')
add_bullet('策略：建立标杆案例（省三甲），打造"XX省编码质控标杆"')
add_bullet('目标：签约50家医院，年营收500万+')

add_para('第三年：规模化（200家）', bold=True)
add_bullet('路径：HIS厂商合作（嵌入东软/卫宁/创业的生态）+ 全国渠道网络')
add_bullet('策略：开放API，成为HIS生态的"编码质控插件"')
add_bullet('目标：签约200家医院，年营收2,000万+')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 四、竞争分析
# ═══════════════════════════════════════════════════

doc.add_heading('四、竞争分析', level=1)

doc.add_heading('4.1 竞品矩阵', level=2)

add_table_simple(['竞品', '类型', '核心功能', 'AI能力', '一体化', '弱点'], [
    ['东软望海', '传统HIS', 'DRG分组、成本核算', '无', '否', '规则老旧，无NLP/LLM，不能处理非结构化文本'],
    ['国新健康', '咨询服务', 'DRG数据服务', '无', '否', '偏人工服务，产品化程度低'],
    ['零氪科技', '肿瘤大数据', '肿瘤专科AI', '有（垂直）', '否', '只做肿瘤，不覆盖全科DRG'],
    ['森亿智能', 'AI+病历', '病历结构化', '有（NLP）', '否', '侧重科研，不碰DRG编码付费'],
    ['各种小SaaS', '单点工具', '单一功能', '无/弱', '否', '编码/质控/DRG割裂，数据不互通'],
    ['★ 码医', '一体化平台', '编码+DRG+质控', '有（LLM+NLP）', '是', '新兴品牌，渠道待建立'],
])

doc.add_heading('4.2 核心竞争壁垒', level=2)

add_para('1. 三合一产品形态（差异化壁垒）', bold=True)
add_para('编码+DRG分组+质控在一个系统里打通，数据无缝流转。传统方案需要三套系统、三个供应商，信息割裂。市场上无同类一体化产品。')

add_para('2. AI语义理解，不是关键词匹配（技术壁垒）', bold=True)
add_para('基于LLM的编码推荐和质控检查能理解医学语义（"胸口像石头压着一样疼"→心绞痛），而不是简单的关键词库匹配。这需要NLP+LLM+医学知识库的组合能力。')

add_para('3. 双后端离线可用（部署壁垒）', bold=True)
add_para('Ollama本地部署+RuleBased自动兜底。即使医院没有GPU或网络受限，核心功能依然可用。纯云端方案无法做到。')

add_para('4. 数据飞轮效应（时间壁垒）', bold=True)
add_para('每多一家医院使用，ICD编码数据库就更完善，质控规则就更精准。先发者的数据和规则积累是后发者无法短期追赶的。')

add_para('5. 先发优势（窗口期壁垒）', bold=True)
add_para('DRG/DIP改革2025年底全面覆盖，AI编码+质控一体化这个细分赛道目前没有成熟产品，窗口期约12-18个月。')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 五、团队
# ═══════════════════════════════════════════════════

doc.add_heading('五、团队', level=1)

add_table_simple(['角色', '姓名', '核心能力', '本项目中职责'], [
    ['项目负责人', '郑诗东和', '商业策划、资源协调、路演演讲\n上海对外经贸大学 物流管理（中澳）',
     '方向决策、商业计划书、路演PPT、路演答辩、医院合作渠道拓展'],
    ['技术负责人', 'Claude (AI Agent)', '全栈开发、AI/ML/NLP、架构设计\nPython/React/TypeScript/LLM',
     '全部代码开发、技术架构设计、技术白皮书、Demo系统、算法优化'],
    ['医学顾问\n（招募中）', 'TBD', 'ICD/DRG编码规则、临床路径、医院质控',
     '编码规则审核、质控规则验证、准确率测试、医院试点对接'],
])

add_para('团队特色：', bold=True)
add_bullet('"人+AI"新协作模式：AI Agent负责全部技术研发（有完整代码库为证），'
         '人类负责人聚焦商业和路演，效率远超传统纯人类团队')
add_bullet('不是PPT创业：已有完整可运行的全栈系统（前端8页面+后端7组API+17个单元测试），可现场演示')
add_bullet('赛道契合度高：医疗AI+医保改革=评审最关注的热点方向')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 六、财务预测
# ═══════════════════════════════════════════════════

doc.add_heading('六、财务预测', level=1)

doc.add_heading('6.1 三年收入预测', level=2)

add_table_simple(['指标', '第一年', '第二年', '第三年'], [
    ['签约医院数', '10家', '50家', '200家'],
    ['平均客单价', '12万/年', '13万/年', '14万/年'],
    ['SaaS订阅收入', '120万', '650万', '2,800万'],
    ['私有化部署收入', '40万', '250万', '1,200万'],
    ['增值服务收入', '10万', '50万', '300万'],
    ['总营收', '170万', '950万', '4,300万'],
    ['总成本（含人力+云+销售）', '30万', '200万', '800万'],
    ['净利润', '140万', '750万', '3,500万'],
    ['净利率', '82%', '79%', '81%'],
])

doc.add_heading('6.2 成本结构（第三年稳态）', level=2)

add_table_simple(['成本类别', '年金额', '占比', '说明'], [
    ['云服务器/GPU', '80万', '10%', '各医院独立部署或集中SaaS'],
    ['研发人力', '300万', '38%', '2-3人核心研发团队'],
    ['销售与渠道', '200万', '25%', '代理商分佣+直销团队'],
    ['客户成功/支持', '100万', '13%', '远程支持为主'],
    ['行政与其他', '120万', '15%', '办公、差旅、资质认证'],
    ['合计', '800万', '100%', '—'],
])

doc.add_heading('6.3 关键假设', level=2)
add_bullet('客单价增速：每年3-5%（随产品功能升级和品牌溢价）')
add_bullet('客户留存率：95%+（医疗SaaS特性，切换成本高）')
add_bullet('毛利率：90%（纯软件，边际交付成本极低）')
add_bullet('回本周期：首年盈利，累计投资回收期<6个月')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 七、风险与对策
# ═══════════════════════════════════════════════════

doc.add_heading('七、风险与对策', level=1)

add_table_simple(['风险', '概率', '影响', '应对策略'], [
    ['HIS厂商推出同类功能', '中', '大',
     '1. 加速获客，抢占窗口期\n2. 聚焦三合一差异化，不做大而全\n3. 与HIS厂商合作而非对抗（成为其生态插件）'],
    ['编码准确率不达标', '低', '致命',
     '1. 目前已有300+诊断编码库打底\n2. 持续扩充ICD数据+真实病历测试\n3. LLM兜底+医学顾问审核'],
    ['医院决策周期长', '高', '中',
     '1. 试用期免费，降低决策门槛\n2. 从编码科切入（一线刚需），自下而上推动\n3. 医保飞检倒逼，政策推动力强'],
    ['竞品价格战', '中', '低',
     '1. SaaS边际成本极低，不怕价格竞争\n2. 技术壁垒高，不是降价就能赶上\n3. 客户切换成本高（系统集成+数据迁移）'],
    ['LLM幻觉导致编码错误', '低', '高',
     '1. 规则引擎兜底机制\n2. 编码结果置信度评分+人工审核流程\n3. 持续fine-tune医学领域模型'],
    ['政策变动风险', '低', '中',
     'DRG/DIP改革是国家长期方向，短期调整不影响大趋势'],
])

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 八、发展里程碑
# ═══════════════════════════════════════════════════

doc.add_heading('八、发展里程碑', level=1)

add_table_simple(['阶段', '时间', '关键目标'], [
    ['产品研发', '已完成（2026.05）',
     '全栈系统开发完成：编码引擎+DRG分组+质控+驾驶舱+\nPipeline演示+系统管理，17个测试通过，可现场演示'],
    ['竞赛准备', '2026.05-06',
     '商业计划书定稿、路演PPT制作、演示脚本打磨、\n联系医院试点意向、准备校赛材料'],
    ['校赛', '2026.06-07',
     '校内选拔赛路演，根据评委反馈迭代BP和PPT'],
    ['省赛备战', '2026.07-08',
     '1-2家医院试点合作，收集真实试用数据，\n优化编码准确率，扩充质控规则'],
    ['省赛', '2026.08-09',
     '省级决赛路演，冲击金奖/一等奖'],
    ['国赛备战', '2026.09-10',
     '深度打磨：Demo演示效果、财务数据、社会价值证明、\n专利申请、软件著作权'],
    ['国赛', '2026.10-11',
     '全国总决赛路演，目标全国第一'],
    ['商业化启动', '赛后',
     '成立公司、签约首批付费客户、建立区域渠道网络'],
])

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 九、社会价值
# ═══════════════════════════════════════════════════

doc.add_heading('九、社会价值', level=1)

add_para('码医的社会价值体现在三个层面：', bold=True)

add_para('1. 医保基金安全', bold=True)
add_para('每年全国医保支出超3万亿元，DRG/DIP付费改革的核心就是"精准支付"。'
         '编码错误导致的医保基金浪费每年估计在数百亿级别。'
         '码医通过AI提高编码准确率，从源头保障基金使用效率。')

add_para('2. 医疗质量提升', bold=True)
add_para('病历质控不仅仅是合规问题。一份质量高的病历意味着更准确的诊断、更合理的治疗方案。'
         '码医的质控引擎帮助医院实现从"抽查10%"到"全量100%"的质控覆盖。')

add_para('3. 为医务人员减负', bold=True)
add_para('全国10万编码员缺口背后，是每个编码员日均50-80份病历的超负荷工作。'
         '码医将编码时间从5-10分钟/份降低到秒级，让编码员从"打字员"变为"审核员"，'
         '把时间花在更复杂的疑难病例上。')

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 结尾
# ═══════════════════════════════════════════════════

add_divider()
add_para('')

footer = doc.add_paragraph()
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer.add_run('码医 MediCode — 让每一份病历都准确，让每一分医保基金都花在刀刃上')
run.font.size = Pt(11)
run.font.italic = True
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

footer2 = doc.add_paragraph()
footer2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer2.add_run('联系方式：郑诗东和 · 上海对外经贸大学')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

footer3 = doc.add_paragraph()
footer3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer3.add_run('2026年5月 · 版本1.0')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
run.font.name = '微软雅黑'
run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# Save
output_path = r'C:\Users\Donghe\Desktop\码医-MediCode-商业计划书.docx'
doc.save(output_path)
print(f'Saved: {output_path}')
