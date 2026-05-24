import { useState, useCallback } from 'react'
import {
  Card, Row, Col, Input, Button, Select, Table, Tag, Statistic, Progress, Typography,
  Divider, Space, message, List, Tooltip, Modal, Descriptions, Empty,
} from 'antd'
import {
  SafetyCertificateOutlined, WarningOutlined, CheckCircleOutlined,
  CloseCircleOutlined, InfoCircleOutlined, ThunderboltOutlined,
  FilterOutlined, ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { qcAPI } from '../services/api'

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
    } catch {
      message.error('质控检查失败')
    } finally { setLoading(false) }
  }, [content, recordType])

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
        {result && (
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => handleCheck()}>重新检查</Button>
          </Space>
        )}
      </div>

      <Divider />

      <Row gutter={24}>
        {/* Left */}
        <Col span={10}>
          <Card title="病历输入" extra={
            <Select value={recordType} onChange={setRecordType} size="small" style={{ width: 120 }}
              options={RECORD_TYPES} />
          }>
            <TextArea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请粘贴待质控的病历内容（出院小结、入院记录、手术记录等）..."
              rows={16}
              style={{ fontFamily: 'monospace', fontSize: 13 }}
            />
            <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">{content.length} 字</Text>
              <Button type="primary" size="large" icon={<SafetyCertificateOutlined />}
                loading={loading} onClick={() => handleCheck()}
                style={{ minWidth: 160, height: 44 }}>
                执行质控检查
              </Button>
            </div>
          </Card>

          {/* Quick tips */}
          <Card title="质控知识库" size="small" style={{ marginTop: 12 }}>
            <List size="small" dataSource={[
              { title: '完整性', desc: '出院小结必须包含出院诊断、入院情况、诊疗经过、出院医嘱四部分' },
              { title: '逻辑性', desc: '手术操作必须有对应的诊断支持，诊断与性别/年龄不矛盾' },
              { title: '编码规范', desc: '主要诊断应为病因诊断，不能选择症状或体征编码' },
              { title: '时效要求', desc: '入院记录24h内完成，手术记录术后24h内完成' },
            ]} renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Tag color="blue">{item.title}</Tag>}
                  description={item.desc}
                />
              </List.Item>
            )} />
          </Card>
        </Col>

        {/* Right */}
        <Col span={14}>
          {result ? (
            <>
              {/* Score + summary */}
              <Row gutter={12} style={{ marginBottom: 12 }}>
                <Col span={8}>
                  <Card bodyStyle={{ textAlign: 'center', padding: '20px 16px' }}>
                    <Progress type="dashboard" percent={result.qc_score} size={100}
                      strokeColor={scoreColor(result.qc_score)}
                      format={(p) => <span style={{ fontSize: 22, fontWeight: 'bold' }}>{p}</span>} />
                    <div style={{ marginTop: 4 }}><Text strong>质控评分</Text></div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {result.qc_score >= 90 ? '优秀' : result.qc_score >= 70 ? '良好' : '需改进'}
                    </Text>
                  </Card>
                </Col>
                <Col span={16}>
                  <Row gutter={[8, 8]}>
                    <Col span={6}>
                      <Card size="small" bodyStyle={{ textAlign: 'center', padding: '12px 8px' }}>
                        <Statistic title="严重" value={result.critical_count}
                          valueStyle={{ color: '#ff4d4f', fontSize: 24 }} />
                        <Text type="secondary" style={{ fontSize: 11 }}>医保拒付风险</Text>
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small" bodyStyle={{ textAlign: 'center', padding: '12px 8px' }}>
                        <Statistic title="重要" value={result.major_count}
                          valueStyle={{ color: '#fa8c16', fontSize: 24 }} />
                        <Text type="secondary" style={{ fontSize: 11 }}>影响DRG分组</Text>
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small" bodyStyle={{ textAlign: 'center', padding: '12px 8px' }}>
                        <Statistic title="一般" value={result.minor_count}
                          valueStyle={{ color: '#faad14', fontSize: 24 }} />
                        <Text type="secondary" style={{ fontSize: 11 }}>编目质量缺陷</Text>
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small" bodyStyle={{ textAlign: 'center', padding: '12px 8px' }}>
                        <Statistic title="提示" value={result.info_count}
                          valueStyle={{ color: '#1677ff', fontSize: 24 }} />
                        <Text type="secondary" style={{ fontSize: 11 }}>规范建议</Text>
                      </Card>
                    </Col>
                  </Row>
                  <Card size="small" style={{ marginTop: 8, background: '#f6ffed' }}>
                    <Space>
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      <Text>
                        质控检查完成，共 {result.total_issues} 个问题。{' '}
                        {result.critical_count > 0 ? (
                          <Text strong type="danger">需重点关注 {result.critical_count} 个严重缺陷</Text>
                        ) : (
                          <Text type="success">无严重缺陷</Text>
                        )}
                      </Text>
                    </Space>
                  </Card>
                </Col>
              </Row>

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
              <Card bodyStyle={{ padding: 0 }}>
                <Table columns={columns} dataSource={filteredIssues}
                  rowKey={(r, i) => `${r.rule_id}-${i}`}
                  size="small" pagination={filteredIssues.length > 10 ? { pageSize: 10, showSizeChanger: false } : false}
                  locale={{ emptyText: '当前筛选条件下未发现质控缺陷' }} />
              </Card>
            </>
          ) : (
            <Empty
              image={<SafetyCertificateOutlined style={{ fontSize: 56, color: '#d9d9d9' }} />}
              description="输入病历内容，点击「执行质控检查」开始质量审核"
              style={{ padding: '100px 0' }}
            >
              <Button type="primary" icon={<ThunderboltOutlined />} onClick={() => {
                // Load sample content for demo
                setContent(`主诉：突发胸痛3小时。
现病史：患者于3小时前无明显诱因突发胸骨后压榨性疼痛。
既往史：高血压病史8年，2型糖尿病5年。
查体：T 36.5℃，P 96次/分，BP 150/95mmHg。
初步诊断：冠状动脉粥样硬化性心脏病，急性心肌梗死，高血压病3级，2型糖尿病。
治疗经过：行急诊PCI术。
出院诊断：急性心肌梗死，PCI术后，高血压病，2型糖尿病。`)
                message.info('已加载示例病历，请点击"执行质控检查"')
              }}>
                加载示例病历
              </Button>
            </Empty>
          )}
        </Col>
      </Row>
    </div>
  )
}
