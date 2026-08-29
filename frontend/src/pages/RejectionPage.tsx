import { useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Card, Row, Col, Input, Button, Tag, Statistic, Typography,
  Space, Spin, Alert, Empty, Table, Divider, message,
} from 'antd'
import {
  ThunderboltOutlined, FileTextOutlined, DollarOutlined,
  WarningOutlined, CheckCircleOutlined, ArrowLeftOutlined,
  SafetyCertificateOutlined, FireOutlined,
} from '@ant-design/icons'
import { REJECTION_RISK_META } from '../components/x_features/rejectionRiskMeta'
import { rejectionAPI } from '../services/api'
import type { RejectionAssessRequest, RejectionPageState, RejectionPatientInfo, RejectionResultData, RejectionRiskItemData, RejectionRiskLevel } from '../types/api'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

interface AssessmentContext {
  secondary_diagnoses: NonNullable<RejectionAssessRequest['secondary_diagnoses']>
  procedures: NonNullable<RejectionAssessRequest['procedures']>
  drg_result: RejectionAssessRequest['drg_result']
  patient_info: Pick<RejectionPatientInfo, 'age' | 'gender'>
}

const SAMPLE_CONTENT = `男性 65 岁,主诊:急性前壁心肌梗死(I21.0),次诊:高血压 3 级(I10.x00)、2 型糖尿病(E11.900)、慢性肾脏病 3 期(N18.3),手术:经皮冠状动脉支架植入(36.0600) + 冠状动脉造影(88.5700),住院 8 天,总费用 58000 元。既往 PCI 术后 1 年,长期服用阿司匹林+氯吡格雷。`

export default function RejectionPage() {
  const navigate = useNavigate()
  const location = useLocation()

  // 来自 pipeline 的预填数据
  const prefill = (location.state as RejectionPageState | null) ?? null

  // 表单
  const [content, setContent] = useState<string>(prefill?.content ?? '')
  const [primaryCode, setPrimaryCode] = useState<string>(prefill?.primary_diagnosis?.code ?? '')
  const [primaryName, setPrimaryName] = useState<string>(prefill?.primary_diagnosis?.name ?? '')
  const [hospitalCost, setHospitalCost] = useState<number | null>(prefill?.hospital_cost ?? 0)
  const [daysOfStay, setDaysOfStay] = useState<number | null>(prefill?.patient_info?.days_of_stay ?? 8)
  const [assessmentContext, setAssessmentContext] = useState<AssessmentContext>({
    secondary_diagnoses: prefill?.secondary_diagnoses ?? [],
    procedures: prefill?.procedures ?? [],
    drg_result: prefill?.drg_result,
    patient_info: {
      age: prefill?.patient_info?.age ?? 0,
      gender: prefill?.patient_info?.gender ?? '',
    },
  })

  // 状态
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RejectionResultData | null>(prefill?.assessment_result ?? null)
  const [error, setError] = useState<string | null>(null)

  const onAssess = useCallback(async () => {
    if (!content.trim() && !primaryCode.trim()) {
      message.warning('请输入病历摘要或主诊编码')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await rejectionAPI.assess({
        ...assessmentContext,
        content: content.trim(),
        primary_diagnosis: primaryCode.trim() ? { code: primaryCode.trim(), name: primaryName.trim() || primaryCode.trim() } : null,
        hospital_cost: hospitalCost ?? 0,
        patient_info: {
          ...assessmentContext.patient_info,
          days_of_stay: daysOfStay ?? 0,
        },
      })
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '评估失败，请检查后端服务')
    } finally {
      setLoading(false)
    }
  }, [assessmentContext, content, primaryCode, primaryName, hospitalCost, daysOfStay])

  const onLoadSample = () => {
    setContent(SAMPLE_CONTENT)
    setPrimaryCode('I21.0')
    setPrimaryName('急性前壁心肌梗死')
    setHospitalCost(58000)
    setDaysOfStay(8)
    setAssessmentContext({
      secondary_diagnoses: [],
      procedures: [],
      drg_result: undefined,
      patient_info: { age: 65, gender: 'male' },
    })
    setResult(null)
    setError(null)
  }

  const onReset = () => {
    setContent('')
    setPrimaryCode('')
    setPrimaryName('')
    setHospitalCost(0)
    setDaysOfStay(8)
    setAssessmentContext({
      secondary_diagnoses: [],
      procedures: [],
      drg_result: undefined,
      patient_info: { age: 0, gender: '' },
    })
    setResult(null)
    setError(null)
  }

  const meta = result ? REJECTION_RISK_META[result.overall_risk] : null
  const highCount = result?.risks?.filter(r => r.risk_level === 'high').length || 0
  const mediumCount = result?.risks?.filter(r => r.risk_level === 'medium').length || 0
  const lowCount = result?.risks?.filter(r => r.risk_level === 'low').length || 0

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <Button
            type="link" icon={<ArrowLeftOutlined />} size="small"
            onClick={() => navigate(-1)} style={{ padding: 0, marginBottom: 8 }}
          >
            返回
          </Button>
          <Title level={3} style={{ margin: 0 }}>
            <SafetyCertificateOutlined style={{ color: '#cf1322', marginRight: 8 }} />
            医保拒付风险评估
          </Title>
          <Text type="secondary">
            基于 DRG 编码组合的医保审核规则扫描,实时量化拒付风险与可避免损失
          </Text>
        </div>
        <Space>
          <Button icon={<FileTextOutlined />} onClick={onLoadSample}>加载示例</Button>
          <Button onClick={onReset}>重置</Button>
        </Space>
      </div>

      <Divider style={{ margin: '16px 0' }} />

      {/* 3 数字主指标 (Hero) */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card
            variant="borderless"
            style={{
              background: meta?.bg || '#fafafa',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            }}
          >
            <Statistic
              title={<Text strong>综合风险等级</Text>}
              value={meta ? meta.label : '待评估'}
              prefix={
                result ? (
                  result.overall_risk?.toLowerCase() === 'high' ? <FireOutlined /> :
                  result.overall_risk?.toLowerCase() === 'medium' ? <WarningOutlined /> :
                  <CheckCircleOutlined />
                ) : <ThunderboltOutlined />
              }
              valueStyle={{ color: meta?.textColor || '#999', fontSize: 32, fontWeight: 700 }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {result ? `扫描 ${result.risks?.length || 0} 个风险因子` : '点击「开始评估」开始风险扫描'}
            </Text>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}
          >
            <Statistic
              title={<Text strong>风险评分</Text>}
              value={result?.risk_score ?? 0}
              suffix="/ 100"
              valueStyle={{
                color: result
                  ? (result.risk_score >= 60 ? '#cf1322' : result.risk_score >= 30 ? '#d48806' : '#3f8600')
                  : '#999',
                fontSize: 32,
                fontWeight: 700,
              }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {result
                ? (result.risk_score >= 60 ? '高风险阈值 (≥60)' : result.risk_score >= 30 ? '中风险阈值 (≥30)' : '安全区间 (<30)')
                : '数值越高,被医保拒付概率越大'}
            </Text>
          </Card>
        </Col>
        <Col span={8}>
          <Card
            variant="borderless"
            style={{
              background: result && result.preventable_amount > 0
                ? 'linear-gradient(135deg, #fff1f0 0%, #ffccc7 100%)'
                : '#fafafa',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
            }}
          >
            <Statistic
              title={<Text strong>可避免损失</Text>}
              value={result?.preventable_amount || 0}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{
                color: result && result.preventable_amount > 0 ? '#cf1322' : '#999',
                fontSize: 32,
                fontWeight: 700,
                fontFamily: 'monospace',
              }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {result && result.preventable_amount > 0
                ? '修订编码可挽回的医保支付金额'
                : '当前无高风险项,预测安全'}
            </Text>
          </Card>
        </Col>
      </Row>

      {/* 输入区 */}
      <Card
        title={<Space><ThunderboltOutlined />评估输入</Space>}
        style={{ marginBottom: 16, borderRadius: 12 }}
      >
        <Row gutter={16}>
          <Col span={17}>
            <Text strong>病历摘要 <Text type="secondary">(必填,越详细越准确)</Text></Text>
            <TextArea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={6}
              placeholder="例:男性 65 岁,主诊:急性前壁心肌梗死(I21.0),手术:经皮冠状动脉支架植入(36.06),住院 8 天,总费用 58000 元..."
              style={{ marginTop: 4, fontFamily: 'monospace', fontSize: 13 }}
              data-testid="rejection-page-input"
            />
          </Col>
          <Col span={7}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Text strong>主诊编码</Text>
                <Input
                  value={primaryCode}
                  onChange={(e) => setPrimaryCode(e.target.value)}
                  placeholder="例: I21.0"
                  style={{ marginTop: 4 }}
                />
              </div>
              <div>
                <Text strong>主诊名称</Text>
                <Input
                  value={primaryName}
                  onChange={(e) => setPrimaryName(e.target.value)}
                  placeholder="例: 急性前壁心肌梗死"
                  style={{ marginTop: 4 }}
                />
              </div>
              <Row gutter={8}>
                <Col span={12}>
                  <Text strong>住院天数</Text>
                  <Input
                    type="number"
                    value={daysOfStay ?? ''}
                    onChange={(e) => setDaysOfStay(e.target.value ? Number(e.target.value) : null)}
                    style={{ marginTop: 4 }}
                  />
                </Col>
                <Col span={12}>
                  <Text strong>总费用 (¥)</Text>
                  <Input
                    type="number"
                    value={hospitalCost ?? ''}
                    onChange={(e) => setHospitalCost(e.target.value ? Number(e.target.value) : null)}
                    style={{ marginTop: 4 }}
                  />
                </Col>
              </Row>
            </Space>
          </Col>
        </Row>

        <Divider style={{ margin: '16px 0 12px' }} />

        <div style={{ textAlign: 'right' }}>
          <Button
            type="primary" size="large" icon={<ThunderboltOutlined />}
            loading={loading} onClick={onAssess}
            disabled={!content.trim() && !primaryCode.trim()}
            style={{
              minWidth: 200, height: 48, fontSize: 16, fontWeight: 600,
              background: 'linear-gradient(135deg, #cf1322 0%, #fa541c 100%)',
              border: 'none',
              boxShadow: '0 4px 14px rgba(207, 19, 34, 0.3)',
            }}
            data-testid="rejection-page-assess-btn"
          >
            开始评估拒付风险
          </Button>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <Card style={{ borderRadius: 12, textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 8 }}>AI 正在扫描医保审核规则...</div>
        </Card>
      )}

      {/* Error */}
      {error && !loading && (
        <Alert type="error" message="评估失败" description={error} showIcon style={{ borderRadius: 12 }} />
      )}

      {/* Result: 风险因子列表 */}
      {result && !loading && (
        <Card
          title={
            <Space>
              <SafetyCertificateOutlined style={{ color: meta?.textColor }} />
              <Text strong>风险因子详情</Text>
              <Tag color={meta?.color}>{meta?.label}</Tag>
              {highCount > 0 && <Tag color="red">高风险 {highCount}</Tag>}
              {mediumCount > 0 && <Tag color="orange">中风险 {mediumCount}</Tag>}
              {lowCount > 0 && <Tag color="gold">低风险 {lowCount}</Tag>}
            </Space>
          }
          style={{ borderRadius: 12 }}
        >
          {result.risks && result.risks.length > 0 ? (
            <Table
              dataSource={result.risks.map((r, i) => ({ ...r, key: i }))}
              pagination={false}
              size="small"
              columns={[
                {
                  title: '级别', dataIndex: 'risk_level', width: 90,
                  render: (v: RejectionRiskLevel) => {
                    const m = REJECTION_RISK_META[v]
                    return <Tag color={m.color}>{m.label}</Tag>
                  },
                },
                {
                  title: '检查项', dataIndex: 'rule_name', width: 180,
                  render: (v: string, r: RejectionRiskItemData) => (
                    <Space direction="vertical" size={0}>
                      <Text strong>{v}</Text>
                      <Text type="secondary" style={{ fontSize: 11 }} code>{r.rule_id}</Text>
                    </Space>
                  ),
                },
                {
                  title: '问题描述', dataIndex: 'description',
                  render: (v: string, r: RejectionRiskItemData) => (
                    <Space direction="vertical" size={0}>
                      <Text>{v}</Text>
                      {r.affected_code && <Tag color="default" style={{ fontSize: 11 }}>编码: {r.affected_code}</Tag>}
                    </Space>
                  ),
                },
                {
                  title: '修正建议', dataIndex: 'suggestion',
                  render: (v: string) => v ? <Text type="secondary" ellipsis={{ tooltip: v }}>{v}</Text> : '-',
                },
                {
                  title: '预估损失', dataIndex: 'estimated_loss', width: 120,
                  render: (v: number) => v > 0
                    ? <Text type="danger" strong style={{ fontFamily: 'monospace' }}>¥{v.toLocaleString()}</Text>
                    : <Text type="secondary">-</Text>,
                },
              ]}
            />
          ) : (
            <Empty
              image={<CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a' }} />}
              description={
                <Space direction="vertical" size={4}>
                  <Text strong style={{ fontSize: 16, color: '#3f8600' }}>未发现拒付风险</Text>
                  <Text type="secondary">当前编码组合符合医保审核规则,可正常结算</Text>
                </Space>
              }
            />
          )}
        </Card>
      )}

      {/* Empty State (无结果时) */}
      {!result && !loading && !error && (
        <Card style={{ borderRadius: 12, marginTop: 16 }}>
          <Empty
            image={<ThunderboltOutlined style={{ fontSize: 64, color: '#cf1322' }} />}
            description={
              <Space direction="vertical" size={8}>
                <Text strong style={{ fontSize: 16 }}>医保拒付风险评估</Text>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  输入病历摘要或主诊编码,系统将基于 50+ 条医保审核规则,<br />
                  实时扫描 DRG 编码组合的拒付风险,并量化可挽回的医保损失金额
                </Paragraph>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ⏱ 评估耗时: 1-3 秒 · 🎯 准确率: 基于真实 DRG 数据训练 · 💰 量化输出: 可避免损失金额
                </Text>
              </Space>
            }
          />
        </Card>
      )}
    </div>
  )
}
