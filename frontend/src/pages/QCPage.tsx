import { useState, useCallback, useEffect, useRef } from 'react'
import {
  Card, Row, Col, Input, Button, Select, Segmented, Table, Tag, Statistic, Progress, Typography,
  Divider, Space, message, List, Tooltip, Modal, Descriptions, Empty, Steps,
} from 'antd'
import {
  SafetyCertificateOutlined, WarningOutlined, CheckCircleOutlined,
  CloseCircleOutlined, InfoCircleOutlined, ThunderboltOutlined,
  FilterOutlined, ReloadOutlined,
  PlayCircleOutlined, PauseCircleOutlined, LoadingOutlined, FileTextOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { qcAPI, pipelineAPI } from '../services/api'

const { TextArea } = Input
const { Title, Text } = Typography

interface QCIssue {
  rule_id: string
  rule_name: string
  rule_type: string
  severity: string
  line_snippet: string
  suggestion: string
  line_number: number | null
}

const SEVERITY_CONFIG: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
  critical: { color: 'red', label: '严重', icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> },
  major: { color: 'orange', label: '重要', icon: <WarningOutlined style={{ color: '#fa8c16' }} /> },
  minor: { color: 'gold', label: '一般', icon: <InfoCircleOutlined style={{ color: '#faad14' }} /> },
  info: { color: 'blue', label: '提示', icon: <InfoCircleOutlined style={{ color: '#1677ff' }} /> },
}

const RULE_TYPE_LABELS: Record<string, string> = {
  completeness: '完整性', logic: '逻辑一致性', coding: '编码一致性',
  timeliness: '时效性', normalization: '规范表达', semantic: '语义质量',
}

const RECORD_TYPES = [
  { value: 'admission', label: '入院记录' },
  { value: 'discharge', label: '出院小结' },
  { value: 'surgery', label: '手术记录' },
]

const SAMPLE_CASES = [
  {
    name: '心内科 · 急性心肌梗死',
    content: `主诉：突发胸痛3小时。
现病史：患者于3小时前无明显诱因突发胸骨后压榨性疼痛，向左肩放射，伴大汗淋漓、恶心，休息后不缓解，来我院急诊。
既往史：高血压病史8年，最高180/100mmHg；2型糖尿病5年。否认肝炎结核史。
查体：T 36.5℃，P 96次/分，R 22次/分，BP 150/95mmHg。神清，双肺呼吸音清，心率96次/分，律齐，各瓣膜区未及病理性杂音。
辅助检查：急诊心电图示V1-V4导联ST段抬高0.3-0.5mV。肌钙蛋白I 3.2ng/mL（↑）。
初步诊断：冠状动脉粥样硬化性心脏病，急性ST段抬高型心肌梗死（前壁），高血压病3级（极高危），2型糖尿病。
治疗经过：行急诊经皮冠状动脉介入治疗（PCI），于前降支植入药物洗脱支架1枚。术后胸痛缓解，生命体征平稳。
出院诊断：急性ST段抬高型心肌梗死（前壁），冠状动脉支架植入术后，高血压病3级，2型糖尿病。`,
  },
  {
    name: '呼吸科 · COPD急性加重',
    content: `主诉：反复咳嗽咳痰伴气促3天，加重1天。
现病史：患者有慢性支气管炎病史10余年，每于冬春季发作。3天前受凉后出现咳嗽、咳黄色粘痰，伴胸闷气促，活动后加重。今晨出现发热，体温最高38.7℃。
既往史：慢性阻塞性肺疾病10年，长期吸入噻托溴铵。吸烟史40年，每日20支。
查体：T 38.3℃，P 102次/分，R 28次/分，BP 130/80mmHg。桶状胸，双肺可及散在哮鸣音，肺底湿啰音。
辅助检查：血常规WBC 13.2×10⁹/L，N% 85%。血气分析：pH 7.32，PaCO₂ 58mmHg，PaO₂ 62mmHg。胸部CT示双肺气肿征象，右下肺斑片状渗出影。
初步诊断：慢性阻塞性肺疾病伴急性加重，肺部感染，Ⅱ型呼吸衰竭，慢性肺源性心脏病（代偿期）。
治疗经过：给予抗感染、祛痰、支气管扩张剂雾化吸入及无创正压通气支持治疗。
出院诊断：慢性阻塞性肺疾病急性加重期，社区获得性肺炎，Ⅱ型呼吸衰竭，慢性肺源性心脏病。`,
  },
  {
    name: '骨科 · 股骨颈骨折',
    content: `主诉：摔伤后左髋疼痛、活动受限2天。
现病史：患者2天前在家中不慎滑倒，左髋着地，当即感左髋剧痛，不能站立行走。由家属送至我院急诊。
既往史：高血压病5年，口服硝苯地平控制可。否认糖尿病史。
查体：T 36.8℃，P 80次/分，R 18次/分，BP 140/85mmHg。左下肢外旋短缩畸形，左腹股沟区压痛（+），左髋关节活动受限，足背动脉搏动良好。
辅助检查：X线示左股骨颈骨折（Garden IV型），骨折端明显移位。骨密度检查示骨量减少（T值-2.1）。
初步诊断：左股骨颈骨折（Garden IV型），骨质疏松症，高血压病。
治疗经过：入院后完善检查，在腰硬联合麻醉下行左侧人工全髋关节置换术，手术顺利。术后预防性抗感染、抗凝及康复功能锻炼指导。
出院诊断：左股骨颈骨折，全髋关节置换术后，骨质疏松症，高血压病。`,
  },
]

export default function QCPage() {
  const [content, setContent] = useState('')
  const [recordType, setRecordType] = useState('discharge')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    total_issues: number; critical_count: number; major_count: number
    minor_count: number; info_count: number; issues: QCIssue[]; qc_score: number
  } | null>(null)

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState<string[]>([])

  // Demo state
  const [demoMode, setDemoMode] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)
  const [fastMode, setFastMode] = useState(true)
  const [caseIdx, setCaseIdx] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const startTimeRef = useRef(0)
  const demoActiveRef = useRef(false)

  const handleCheck = useCallback(async (text?: string) => {
    const input = text ?? content
    if (!input.trim()) { message.warning('请先输入病历内容'); return }
    setLoading(true)
    try {
      const { data } = await qcAPI.check({
        record_id: Date.now(), record_type: recordType, content: input,
      })
      setResult(data)
      const total = data.total_issues || 0
      if (total === 0) {
        message.success('质控检查通过，未发现缺陷')
      } else {
        message.warning(`发现 ${total} 个质控问题（严重${data.critical_count} / 重要${data.major_count} / 一般${data.minor_count}）`)
      }
      pipelineAPI.save({
        content: input,
        record_type: recordType,
        qc_result: data,
        department: '质控中心',
      }).catch((e: any) => { console.warn('自动保存失败:', e?.response?.data || e?.message) })
    } catch {
      message.error('质控检查失败')
    } finally { setLoading(false) }
  }, [content, recordType])

  // Demo handlers
  const stopDemo = useCallback(() => {
    setDemoRunning(false)
    demoActiveRef.current = false
  }, [])

  const startDemo = useCallback(() => {
    setDemoMode(true)
    setResult(null)
    setElapsedTime(0)
    demoActiveRef.current = true

    const text = SAMPLE_CASES[caseIdx]?.content ?? ''
    setContent(text)
    startTimeRef.current = Date.now()

    setTimeout(() => {
      handleCheck(text)
    }, 100)
  }, [caseIdx, handleCheck])

  // Celebration when result arrives in demo mode
  useEffect(() => {
    if (!demoActiveRef.current || !result) return
    demoActiveRef.current = false
    setDemoRunning(false)
    setElapsedTime(Date.now() - startTimeRef.current)
  }, [result])

  useEffect(() => {
    return () => { demoActiveRef.current = false }
  }, [])

  const filteredIssues = (result?.issues || []).filter((i) => {
    if (severityFilter.length > 0 && !severityFilter.includes(i.severity)) return false
    if (typeFilter.length > 0 && !typeFilter.includes(i.rule_type)) return false
    return true
  })

  const columns: ColumnsType<QCIssue> = [
    {
      title: '级别', dataIndex: 'severity', key: 'severity', width: 80,
      render: (s: string) => {
        const cfg = SEVERITY_CONFIG[s] || { color: 'default', label: s, icon: null }
        return <Tag color={cfg.color}>{cfg.label}</Tag>
      },
    },
    { title: '规则', dataIndex: 'rule_name', key: 'rule_name', width: 180, ellipsis: true },
    {
      title: '类型', dataIndex: 'rule_type', key: 'rule_type', width: 90,
      render: (t: string) => <Text type="secondary" style={{ fontSize: 12 }}>{RULE_TYPE_LABELS[t] || t}</Text>,
    },
    {
      title: '缺陷描述', dataIndex: 'line_snippet', key: 'line_snippet', ellipsis: true,
      render: (v: string, r: QCIssue) => (
        <Tooltip title={r.line_snippet}>
          <Text>{v || '-'}</Text>
        </Tooltip>
      ),
    },
    {
      title: '建议', dataIndex: 'suggestion', key: 'suggestion', width: 200,
      render: (v: string) => <Text type="secondary" ellipsis={{ tooltip: v }}>{v}</Text>,
    },
    {
      title: '', key: 'action', width: 100,
      render: (_: any, record: QCIssue) => (
        <Space size={4}>
          <Button size="small" type="primary" ghost onClick={async () => {
            const id = (record as any).id
            if (id) {
              try { await qcAPI.acceptResult(id); message.success('已采纳建议') }
              catch { message.error('操作失败') }
            } else {
              message.success('已采纳建议')
            }
          }}>采纳</Button>
          <Button size="small" type="text" danger onClick={async () => {
            const id = (record as any).id
            if (id) {
              try { await qcAPI.rejectResult(id); message.info('已忽略') }
              catch { message.error('操作失败') }
            } else {
              message.info('已忽略')
            }
          }}>忽略</Button>
        </Space>
      ),
    },
  ]

  const scoreColor = (score: number) =>
    score >= 90 ? '#3f8600' : score >= 70 ? '#fa8c16' : '#ff4d4f'

  const ruleTypeOptions = Object.entries(RULE_TYPE_LABELS).map(([k, v]) => ({ value: k, label: v }))
  const severityOptions = [
    { value: 'critical', label: '严重' },
    { value: 'major', label: '重要' },
    { value: 'minor', label: '一般' },
    { value: 'info', label: '提示' },
  ]

  return (
    <div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={3}><SafetyCertificateOutlined /> 病历质控中心</Title>
          <Text type="secondary">AI自动检查病历完整性、逻辑一致性、编码准确性 — 支持规则引擎 + LLM语义双模质控</Text>
        </div>
        <Space direction="vertical" align="end" size={4}>
          {!demoMode ? (
            <Space>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={() => { setFastMode(true); startDemo(); }}
                style={{
                  background: 'linear-gradient(135deg, #6366f1, #0ea5e9)',
                  border: 'none', borderRadius: 8, fontWeight: 600,
                  boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                }}
              >
                快速演示
              </Button>
              <Button icon={<PlayCircleOutlined />} onClick={() => { setFastMode(false); startDemo(); }}>
                完整演示
              </Button>
              {result && (
                <Button icon={<ReloadOutlined />} onClick={() => handleCheck()}>重新检查</Button>
              )}
            </Space>
          ) : (
            <Space>
              <Select
                size="small"
                value={caseIdx}
                onChange={(v) => { setCaseIdx(v); stopDemo(); }}
                style={{ width: 180 }}
                options={SAMPLE_CASES.map((c, i) => ({ value: i, label: c.name }))}
              />
              {demoRunning ? (
                <Button size="small" icon={<PauseCircleOutlined />} onClick={stopDemo} danger>停止</Button>
              ) : (
                <Button size="small" icon={<ReloadOutlined />} onClick={startDemo}
                  style={{ background: 'linear-gradient(135deg, #6366f1, #0ea5e9)', border: 'none', color: '#fff' }}>
                  重新演示
                </Button>
              )}
              <Button size="small" onClick={() => { setDemoMode(false); stopDemo(); setContent(''); setResult(null); }}>
                退出
              </Button>
            </Space>
          )}
          {demoMode && (
            <Space size={4}>
              {fastMode && <Tag color="orange" icon={<ThunderboltOutlined />}>快速模式</Tag>}
              <Tag
                color={loading ? 'processing' : elapsedTime > 0 ? 'success' : 'default'}
                icon={loading ? <LoadingOutlined /> : elapsedTime > 0 ? <CheckCircleOutlined /> : undefined}
              >
                {loading ? '检查中...' : elapsedTime > 0 ? `完成 (${(elapsedTime / 1000).toFixed(1)}s)` : '准备就绪'}
              </Tag>
            </Space>
          )}
        </Space>
      </div>

      <Divider />

      {/* Pipeline Steps */}
      <Card style={{ marginBottom: 16 }}>
        <Steps
          current={result ? 1 : 0}
          status={loading ? 'process' : result ? 'finish' : 'wait'}
          items={[
            { title: '质控检查', description: '完整性 + 逻辑校验', icon: result ? <CheckCircleOutlined /> : <SafetyCertificateOutlined /> },
          ]}
        />
      </Card>

      {/* Input Area */}
      <Card
        title={<Space><FileTextOutlined />病历输入</Space>}
        extra={
          <Select value={recordType} onChange={setRecordType} size="small" style={{ width: 120 }}
            options={RECORD_TYPES} disabled={demoMode} />
        }
        style={{ marginBottom: 16 }}
        className={loading ? 'pipeline-card-processing' : ''}
      >
        <TextArea
          value={content}
          onChange={(e) => { if (!demoMode) setContent(e.target.value) }}
          placeholder={demoMode ? '演示模式：AI将自动执行质控检查...' : '请粘贴待质控的病历内容（出院小结、入院记录、手术记录等）...'}
          rows={8}
          readOnly={demoMode}
          style={{ fontFamily: 'monospace', fontSize: 13 }}
        />
        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text type="secondary">{content.length} 字</Text>
          <Button type="primary" size="large" icon={<SafetyCertificateOutlined />}
            loading={loading} onClick={() => handleCheck()}
            disabled={demoMode}
            style={{ minWidth: 160, height: 44 }}>
            执行质控检查
          </Button>
        </div>
      </Card>

      {/* Result */}
      {result && (
        <Card
          title={<Space><SafetyCertificateOutlined style={{ color: result.qc_score >= 90 ? '#52c41a' : '#fa8c16' }} />质控检查结果</Space>}
          extra={
            <Space size="large">
              <span>
                {result.critical_count > 0 && <Tag color="red">严重 {result.critical_count}</Tag>}
                {result.major_count > 0 && <Tag color="orange">重要 {result.major_count}</Tag>}
                {result.minor_count > 0 && <Tag color="gold">一般 {result.minor_count}</Tag>}
                {result.info_count > 0 && <Tag color="blue">提示 {result.info_count}</Tag>}
              </span>
            </Space>
          }
          className="pipeline-card-complete"
        >
          <Row gutter={24} align="middle">
            <Col span={6}>
              <div style={{ textAlign: 'center' }}>
                <Progress type="dashboard" percent={result.qc_score} size={120}
                  strokeColor={scoreColor(result.qc_score)}
                  format={(p) => <span style={{ fontSize: 24, fontWeight: 'bold' }}>{p}</span>} />
                <div style={{ marginTop: 4 }}><Text type="secondary">质控评分</Text></div>
              </div>
            </Col>
            <Col span={18}>
              {result.issues.length > 0 ? (
                <>
                  {/* Filters */}
                  <Card size="small" style={{ marginBottom: 8 }}>
                    <Space wrap>
                      <FilterOutlined />
                      <Select mode="multiple" placeholder="缺陷级别" style={{ minWidth: 120 }} size="small"
                        value={severityFilter} onChange={setSeverityFilter} options={severityOptions}
                        allowClear />
                      <Select mode="multiple" placeholder="规则类型" style={{ minWidth: 140 }} size="small"
                        value={typeFilter} onChange={setTypeFilter} options={ruleTypeOptions}
                        allowClear />
                      {(severityFilter.length > 0 || typeFilter.length > 0) && (
                        <Button size="small" onClick={() => { setSeverityFilter([]); setTypeFilter([]) }}>
                          清除筛选
                        </Button>
                      )}
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        显示 {filteredIssues.length}/{result.issues.length} 条
                      </Text>
                    </Space>
                  </Card>
                  {/* Issues table */}
                  <Table columns={columns} dataSource={filteredIssues}
                    rowKey={(r, i) => `${r.rule_id}-${i}`}
                    size="small" pagination={filteredIssues.length > 10 ? { pageSize: 10, showSizeChanger: false } : false}
                    locale={{ emptyText: '当前筛选条件下未发现质控缺陷' }} />
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 32 }} />
                  <div style={{ marginTop: 8 }}><Text type="secondary">未发现质控缺陷，病历质量良好</Text></div>
                </div>
              )}
            </Col>
          </Row>
        </Card>
      )}

      {/* Empty state */}
      {!result && !loading && !demoMode && (
        <Card>
          <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
            <SafetyCertificateOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block' }} />
            <Text type="secondary" style={{ fontSize: 16 }}>
              粘贴病历内容，点击「执行质控检查」开始质量审核
            </Text>
          </div>
        </Card>
      )}

      {/* Demo empty state */}
      {!result && !loading && demoMode && (
        <Card>
          <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
            <ThunderboltOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block', color: '#0ea5e9' }} />
            <Text type="secondary" style={{ fontSize: 16 }}>
              点击「重新演示」开始质控检查演示
            </Text>
          </div>
        </Card>
      )}
    </div>
  )
}
