import { useState } from 'react'
import { Typography, Card, Row, Col, Steps, Tag, Divider, Collapse, Timeline, Button, Space } from 'antd'
import {
  ReadOutlined, NodeIndexOutlined, FileTextOutlined,
  MedicineBoxOutlined, SafetyCertificateOutlined, DashboardOutlined,
  ThunderboltOutlined, QuestionCircleOutlined, SmileOutlined,
  RocketOutlined, SearchOutlined, CheckCircleOutlined, DollarOutlined,
  RightOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text, Paragraph } = Typography

// ─── 大白话术语表 ──────────────────────────────────────────────────────────

const JARGON_MAP: { term: string; plain: string; icon: string }[] = [
  { term: 'ICD编码', plain: '给每个病起一个标准编号。比如"急性心肌梗死"在全国都用统一编号 I21.900，医保就认这个号', icon: '🏷️' },
  { term: 'DRG分组', plain: '按疾病的严重程度和治疗方式，把病人分到不同的"付费组"。同一个组的病，医保给的钱一样', icon: '📦' },
  { term: 'CMI', plain: '病例组合指数。数值越高，说明医院收治的病人越重、越复杂。一般大医院 CMI > 1.0', icon: '📊' },
  { term: '权重 (RW)', plain: '每个DRG组的"价格系数"。权重 3.5 的病，医保给的钱是权重 1.0 的 3.5 倍', icon: '⚖️' },
  { term: 'MCC/CC', plain: '重要合并症/合并症。有严重并发症的病人（如心梗+肾衰），DRG分组会升级，给的钱更多', icon: '🔴' },
  { term: '质控 (QC)', plain: '质量检查。看编码有没有漏、有没有错、有没有逻辑矛盾（比如男病人写了妇科诊断）', icon: '🔍' },
  { term: '主要诊断', plain: '这次住院最花钱、最要命的那个病。选错了，DRG分组就错了，医院就亏了', icon: '🎯' },
  { term: 'ADRG', plain: 'DRG分组的中间站。先按器官系统分大类（MDC），再按治疗方式分ADRG，最后细化到DRG', icon: '🗂️' },
]

// ─── 常见问题 ──────────────────────────────────────────────────────────────

const FAQ = [
  {
    q: '我完全不懂医学编码，能用这个系统吗？',
    a: '能。系统内置了上万条ICD编码规则和DRG分组逻辑，你只需要粘贴病历，AI会自动识别诊断、匹配编码、完成分组。你做的事就是"复制、粘贴、点按钮"。',
  },
  {
    q: '为什么编码准确率很重要？',
    a: '医保是按DRG分组来给医院拨钱的。编码错了 → 分组错了 → 拨的钱少了，医院直接亏钱。或者编码"升级"过度 → 医保拒付 → 医院被罚款。准确编码 = 医院不亏钱。',
  },
  {
    q: '什么是最佳主要诊断选择？',
    a: '选"最花钱、最要命的那个病"。比如病人同时有心肌梗死和高血压，主要诊断应该选心肌梗死（急性、危重），而不是高血压（慢性、稳定）。系统会自动帮你判断。',
  },
  {
    q: '演示模式是干什么的？',
    a: '在"智能流水线"页面，点击"演示模式"，系统会自动把一篇真实病历逐字敲出来，然后自动走完编码→质控→DRG→费用测算全流程。适合给领导演示或者自己不熟时先看一遍。',
  },
  {
    q: '系统支持哪些类型的病历？',
    a: '出院小结、入院记录、手术记录都可以。支持直接粘贴文本，也支持上传 .txt、.docx、.pdf 文件。',
  },
  {
    q: '质控评分为 0 分是什么意思？',
    a: '质控评分满分 100 分，表示"没有发现任何问题"。每个发现的缺陷会按严重程度扣分：严重（critical）扣 10 分，重要（major）扣 5 分，一般（minor）扣 2 分，提示（info）扣 0.5 分。分数越低说明问题越多，0 分表示所有分数都被扣光，病历质量存在严重问题。',
  },
]

// ─── 功能导览 ──────────────────────────────────────────────────────────────

const FEATURES = [
  {
    path: '/pipeline',
    icon: <NodeIndexOutlined style={{ fontSize: 28, color: '#6366f1' }} />,
    title: '智能流水线',
    tag: '推荐首试',
    desc: '一站式全流程：输入病历 → AI编码 → 质控检查 → DRG分组 → 费用测算。适合新手上手和对外演示。',
    steps: ['粘贴病历或点击"演示模式"自动输入', '系统自动识别诊断和手术', '自动完成质控检查和DRG分组', '展示预估医保支付金额'],
  },
  {
    path: '/coding',
    icon: <FileTextOutlined style={{ fontSize: 28, color: '#1677ff' }} />,
    title: '编码工作台',
    tag: '日常使用',
    desc: '专业的ICD编码工具。输入病历，系统给出推荐的诊断编码和手术编码，支持手动调整和搜索。',
    steps: ['输入出院小结等内容', '点击"智能编码"', '查看AI推荐的诊断和手术编码', '可以搜索特定编码，也可以手动调整'],
  },
  {
    path: '/qc',
    icon: <SafetyCertificateOutlined style={{ fontSize: 28, color: '#52c41a' }} />,
    title: '质控中心',
    tag: '质量把关',
    desc: '检查编码质量的"啄木鸟"。自动检测漏编、错编、逻辑矛盾，给出质控评分和修改建议。',
    steps: ['输入病历内容和编码结果', '系统逐条检查 16 条质控规则', '查看问题清单（严重/重要/一般/提示）', '根据建议修改编码'],
  },
  {
    path: '/drg',
    icon: <MedicineBoxOutlined style={{ fontSize: 28, color: '#722ed1' }} />,
    title: 'DRG分组',
    tag: '付费测算',
    desc: '输入诊断和手术编码，系统自动分到对应的DRG付费组，展示权重和预估医保支付金额。',
    steps: ['输入主要诊断编码（如 I21.900）', '输入次要诊断和手术编码', '查看DRG分组结果和预估费用', '可与人工分组对比差异'],
  },
  {
    path: '/dashboard',
    icon: <DashboardOutlined style={{ fontSize: 28, color: '#fa8c16' }} />,
    title: '数据驾驶舱',
    tag: '管理视角',
    desc: '全院的编码和DRG数据概览。CMI趋势、科室排名、质控评分变化、收入分析，一眼看清全院运营状况。',
    steps: ['查看全院CMI和病例数', '对比各科室的编码质量排名', '追踪质控评分的变化趋势', '分析DRG预期收入和实际收入'],
  },
]

export default function GuidePage() {
  const navigate = useNavigate()
  const [showJargon, setShowJargon] = useState(false)

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>

      {/* ── 头部 ──────────────────────────────────────────────────────── */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{
          width: 72, height: 72, borderRadius: 20, margin: '0 auto 16px',
          background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <ReadOutlined style={{ fontSize: 36, color: '#fff' }} />
        </div>
        <Title level={2} style={{ marginBottom: 4 }}>码医 MediCode 使用指南</Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          不会编码？没关系。看完这篇，你也能用 AI 做医疗编码和医保测算
        </Text>
      </div>

      {/* ── 一句话介绍 ────────────────────────────────────────────────── */}
      <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #f0f7ff 0%, #f5f3ff 100%)', border: '1px solid #d6e4ff' }}>
        <Row align="middle" gutter={24}>
          <Col>
            <RocketOutlined style={{ fontSize: 40, color: '#6366f1' }} />
          </Col>
          <Col flex={1}>
            <Title level={4} style={{ marginBottom: 4 }}>这个系统是干什么的？</Title>
            <Paragraph style={{ marginBottom: 0, fontSize: 15, lineHeight: 1.8 }}>
              简单说：<Text strong>帮医院把病历"翻译"成医保局看得懂的标准编码，算出该拨多少钱。</Text>
              <br />
              医生写完病历 → 系统自动识别得了什么病、做了什么手术 → 给每个病和手术配上国家标准编码 →
              按DRG规则分组 → 算出医保该给多少钱 → 同时检查编码有没有问题。
              <br />
              以前靠编码员人工翻书查码，<Text mark>现在粘贴病历，几秒钟出结果。</Text>
            </Paragraph>
          </Col>
        </Row>
      </Card>

      {/* ── 功能导览 ──────────────────────────────────────────────────── */}
      <Title level={3} style={{ marginBottom: 16 }}>
        <ThunderboltOutlined /> 五大功能模块
      </Title>

      {FEATURES.map((f) => (
        <Card
          key={f.path}
          hoverable
          style={{ marginBottom: 16 }}
          onClick={() => navigate(f.path)}
        >
          <Row gutter={24} align="middle">
            <Col span={2} style={{ textAlign: 'center' }}>
              {f.icon}
            </Col>
            <Col span={6}>
              <Space>
                <Text strong style={{ fontSize: 16 }}>{f.title}</Text>
                <Tag color="blue">{f.tag}</Tag>
              </Space>
              <br />
              <Text type="secondary">{f.desc}</Text>
            </Col>
            <Col span={10}>
              <Timeline
                items={f.steps.map((s) => ({
                  color: 'gray',
                  children: <span style={{ fontSize: 13 }}>{s}</span>,
                }))}
              />
            </Col>
            <Col span={4} style={{ textAlign: 'right' }}>
              <Button type="primary" ghost icon={<RightOutlined />}>
                去试试
              </Button>
            </Col>
          </Row>
        </Card>
      ))}

      <Divider />

      {/* ── 大白话术语表 ──────────────────────────────────────────────── */}
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        <Button
          size="large"
          type={showJargon ? 'primary' : 'default'}
          icon={<SmileOutlined />}
          onClick={() => setShowJargon(!showJargon)}
        >
          {showJargon ? '收起术语表' : '看不懂专业名词？点这里，用大白话解释'}
        </Button>
      </div>

      {showJargon && (
        <Card title={<><SmileOutlined /> 医学编码大白话词典</>} style={{ marginBottom: 24 }}>
          <Row gutter={[16, 12]}>
            {JARGON_MAP.map((j) => (
              <Col span={12} key={j.term}>
                <div style={{
                  padding: 12, background: '#fafafa', borderRadius: 10,
                  border: '1px solid #f0f0f0',
                }}>
                  <div style={{ marginBottom: 4 }}>
                    <Tag color="purple">{j.icon} {j.term}</Tag>
                  </div>
                  <Text style={{ fontSize: 13, lineHeight: 1.6 }}>{j.plain}</Text>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      <Divider />

      {/* ── 常见问题 ──────────────────────────────────────────────────── */}
      <Title level={3} style={{ marginBottom: 16 }}>
        <QuestionCircleOutlined /> 常见问题
      </Title>

      <Collapse
        size="large"
        items={FAQ.map((f, i) => ({
          key: String(i),
          label: <Text strong>{f.q}</Text>,
          children: <Paragraph style={{ fontSize: 14, lineHeight: 1.8 }}>{f.a}</Paragraph>,
        }))}
        style={{ marginBottom: 24 }}
      />

      <Divider />

      {/* ── 快速上手三步 ──────────────────────────────────────────────── */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={3}>上手只需 3 步</Title>
        <Steps
          style={{ marginTop: 24, maxWidth: 700, margin: '0 auto' }}
          direction="vertical"
          current={-1}
          items={[
            {
              title: <Text strong style={{ fontSize: 16 }}>第一步：登录</Text>,
              description: (
                <Text type="secondary">
                  用管理员给的账号密码登录。演示环境用户名 <Text code>admin</Text>，密码 <Text code>medicode2024</Text>
                </Text>
              ),
              icon: <SmileOutlined />,
            },
            {
              title: <Text strong style={{ fontSize: 16 }}>第二步：去"智能流水线"点"演示模式"</Text>,
              description: (
                <Text type="secondary">
                  系统会自动演示完整流程。看完一遍你就知道每个模块是干什么的了
                </Text>
              ),
              icon: <PlayCircleIcon />,
            },
            {
              title: <Text strong style={{ fontSize: 16 }}>第三步：粘贴你自己的病历试试</Text>,
              description: (
                <Text type="secondary">
                  在"编码工作台"粘贴一份出院小结，点"智能编码"，看 AI 能识别出哪些诊断和手术
                </Text>
              ),
              icon: <CheckCircleOutlined />,
            },
          ]}
        />
      </div>
    </div>
  )
}

// 小图标（Steps 里需要 component 而非 element）
function PlayCircleIcon() {
  return <span style={{ fontSize: 16 }}>▶️</span>
}
