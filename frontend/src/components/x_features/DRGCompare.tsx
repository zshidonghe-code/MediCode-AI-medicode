import { useState } from 'react'
import { Card, Button, Input, Tag, Space, Typography, Spin, Alert, Statistic, Row, Col } from 'antd'
import { SwapOutlined } from '@ant-design/icons'
import { drgAPI } from '../../services/api'

const { Title, Text } = Typography

interface DRGCompareProps {
  defaultRecordId?: number
}

/**
 * X 功能迷你版 C — AI vs 人工 DRG 分组对比
 * 后端: GET /api/v1/drg/compare?record_id=&ai_drg=&manual_drg=
 * 演示路径: DRGPage 备选 DRG 路径对比
 */
export function DRGCompare({ defaultRecordId = 1 }: DRGCompareProps) {
  const [recordId, setRecordId] = useState(defaultRecordId)
  const [aiDrg, setAiDrg] = useState('')
  const [manualDrg, setManualDrg] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    ai_drg: string
    manual_drg: string
    same: boolean
    gap: number
    ai_weight: number
    manual_weight: number
    rate: number
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onCompare = async () => {
    if (!aiDrg || !manualDrg) return
    setLoading(true)
    setError(null)
    try {
      const res = await drgAPI.compare(recordId, aiDrg, manualDrg)
      setResult(res.data)
    } catch (e) {
      setError(e instanceof Error ? e.message : '对比失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      data-testid="drg-compare"
      title={<Space><SwapOutlined /><Title level={5} style={{ margin: 0 }}>AI vs 人工 DRG 分组对比</Title></Space>}
      extra={<Tag color="purple">X-Beta</Tag>}
      style={{ marginBottom: 16 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Text type="secondary">输入 AI 与人工各自的 DRG 码,系统自动计算权重差与费用差额</Text>

        <Row gutter={12}>
          <Col span={6}>
            <Text>病历 ID</Text>
            <Input
              type="number"
              value={recordId}
              onChange={(e) => setRecordId(Number(e.target.value))}
              data-testid="drg-record-id"
            />
          </Col>
          <Col span={9}>
            <Text>AI 分组码</Text>
            <Input
              value={aiDrg}
              onChange={(e) => setAiDrg(e.target.value)}
              placeholder="例: FM19"
              data-testid="drg-ai-code"
            />
          </Col>
          <Col span={9}>
            <Text>人工分组码</Text>
            <Input
              value={manualDrg}
              onChange={(e) => setManualDrg(e.target.value)}
              placeholder="例: FM15"
              data-testid="drg-manual-code"
            />
          </Col>
        </Row>

        <Button
          type="primary"
          loading={loading}
          onClick={onCompare}
          disabled={!aiDrg || !manualDrg}
          data-testid="drg-compare-btn"
        >
          对比 DRG
        </Button>

        {error && <Alert type="error" message={error} showIcon />}

        {result && !loading && (
          <Card type="inner" title="对比结果">
            <Row gutter={16}>
              <Col span={8}>
                <Card size="small" style={{ background: result.same ? '#f6ffed' : '#fff7e6' }}>
                  <Statistic
                    title="一致性"
                    value={result.same ? '一致' : '不一致'}
                    valueStyle={{ color: result.same ? '#3f8600' : '#d48806' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="权重差"
                    value={Math.abs(result.ai_weight - result.manual_weight).toFixed(2)}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ background: result.gap > 0 ? '#fff1f0' : '#f6ffed' }}>
                  <Statistic
                    title="费用差额"
                    value={result.gap}
                    prefix="¥"
                    precision={2}
                    valueStyle={{ color: result.gap > 0 ? '#cf1322' : '#3f8600' }}
                  />
                </Card>
              </Col>
            </Row>

            <div style={{ marginTop: 16 }}>
              <Space>
                <Tag color="blue">AI: {result.ai_drg}</Tag>
                <Text type="secondary">权重 {result.ai_weight}</Text>
                <Text type="secondary">vs</Text>
                <Tag color="purple">人工: {result.manual_drg}</Tag>
                <Text type="secondary">权重 {result.manual_weight}</Text>
                <Text type="secondary">· 费率 ¥{result.rate}</Text>
              </Space>
            </div>
          </Card>
        )}
      </Space>
    </Card>
  )
}

export default DRGCompare