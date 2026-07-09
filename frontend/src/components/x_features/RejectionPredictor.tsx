import { useState } from 'react'
import { Card, Button, Input, Tag, Space, Typography, Spin, Alert, Statistic } from 'antd'
import { rejectionAPI } from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface RejectionPredictorProps {
  defaultContent?: string
}

interface RiskItem {
  rule_id: string
  rule_name: string
  risk_level: string
  description: string
}

const RISK_COLOR: Record<string, string> = {
  HIGH: 'red',
  MEDIUM: 'orange',
  LOW: 'gold',
}

const RISK_LABEL: Record<string, string> = {
  HIGH: '高风险',
  MEDIUM: '中风险',
  LOW: '低风险',
}

/**
 * X 功能迷你版 B — AI 拒付风险实时预测
 * 后端: POST /api/v1/rejection/assess
 * 演示路径: PipelinePage 流水线最后一步
 */
export function RejectionPredictor({ defaultContent = '' }: RejectionPredictorProps) {
  const [content, setContent] = useState(defaultContent)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    overall_risk: string
    risk_score: number
    preventable_amount: number
    risks: RiskItem[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onAssess = async () => {
    if (!content.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await rejectionAPI.assess({ content })
      setResult(res.data)
    } catch (e) {
      setError(e instanceof Error ? e.message : '预测失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      data-testid="rejection-predictor"
      title={<Space><span>🛡️</span><Title level={5} style={{ margin: 0 }}>AI 拒付风险实时预测</Title></Space>}
      extra={<Tag color="purple">X-Beta</Tag>}
      style={{ marginBottom: 16 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <Text type="secondary">输入病历摘要或诊断组合，AI 实时评估医保拒付风险</Text>
        </div>

        <TextArea
          rows={4}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="例：男性 65 岁,主诊:急性前壁心肌梗死(I21.0),手术:经皮冠状动脉支架植入(36.06),住院 8 天,费用 45000 元..."
          data-testid="rejection-input"
        />

        <Button
          type="primary"
          loading={loading}
          onClick={onAssess}
          disabled={!content.trim()}
          data-testid="rejection-assess-btn"
        >
          实时预测拒付风险
        </Button>

        {error && <Alert type="error" message={error} showIcon />}

        {loading && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin tip="AI 评估中..." />
          </div>
        )}

        {result && !loading && (
          <Card type="inner" title="预测结果">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Space size="large" wrap>
                <Statistic
                  title="综合风险等级"
                  value={RISK_LABEL[result.overall_risk] || result.overall_risk}
                  valueStyle={{ color: RISK_COLOR[result.overall_risk] === 'red' ? '#cf1322' : '#d48806' }}
                />
                <Statistic title="风险评分" value={result.risk_score} suffix="/ 100" />
                <Statistic
                  title="可避免损失"
                  value={result.preventable_amount}
                  prefix="¥"
                  precision={2}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Space>

              {result.risks && result.risks.length > 0 && (
                <div>
                  <Title level={5}>风险因子</Title>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    {result.risks.map((r, i) => (
                      <Alert
                        key={i}
                        type={r.risk_level === 'HIGH' ? 'error' : r.risk_level === 'MEDIUM' ? 'warning' : 'info'}
                        message={
                          <Space>
                            <Tag color={RISK_COLOR[r.risk_level]}>{RISK_LABEL[r.risk_level]}</Tag>
                            <Text strong>{r.rule_name}</Text>
                            <Text type="secondary" code>{r.rule_id}</Text>
                          </Space>
                        }
                        description={r.description}
                        showIcon
                      />
                    ))}
                  </Space>
                </div>
              )}
            </Space>
          </Card>
        )}
      </Space>
    </Card>
  )
}

export default RejectionPredictor