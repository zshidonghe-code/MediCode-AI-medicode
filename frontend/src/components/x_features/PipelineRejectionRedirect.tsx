import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Space, Typography } from 'antd'
import { ArrowRightOutlined, CloseOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import type { RejectionPageState } from '../../types/api'

const { Text } = Typography

interface PipelineRejectionRedirectProps {
  // 流水线完成后触发 (即 rejectionResult 存在)
  trigger: boolean
  // 传递给 /rejection 页面的预填数据
  prefill: RejectionPageState
}

/**
 * Pipeline completion CTA for optional detailed rejection review.
 *
 * Navigation is always initiated by an explicit user action.
 */
export function PipelineRejectionRedirect({
  trigger,
  prefill,
}: PipelineRejectionRedirectProps) {
  const navigate = useNavigate()
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!trigger) setDismissed(false)
  }, [trigger])

  if (!trigger || dismissed) return null

  const handleJumpNow = () => {
    navigate('/rejection', { state: prefill })
  }

  return (
    <div
      data-testid="pipeline-rejection-redirect"
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 1000,
        background: 'linear-gradient(135deg, #fff1f0 0%, #ffccc7 100%)',
        border: '1px solid #ffa39e',
        borderRadius: 12,
        padding: '16px 20px',
        boxShadow: '0 6px 20px rgba(207, 19, 34, 0.15)',
        minWidth: 360,
        maxWidth: 420,
        animation: 'slideUp 0.3s ease-out',
      }}
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <SafetyCertificateOutlined style={{ color: '#cf1322', fontSize: 18 }} />
            <Text strong style={{ color: '#cf1322', fontSize: 14 }}>
              流水线分析完成
            </Text>
          </Space>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={() => setDismissed(true)}
            aria-label="关闭拒付风险入口"
            style={{ color: '#999' }}
          />
        </Space>

        <Text style={{ fontSize: 13, color: '#5c0011' }}>
          点击进入拒付风险独立评估页,查看 3 维指标 + 详细修正建议
        </Text>

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Button
            type="primary"
            size="middle"
            icon={<ArrowRightOutlined />}
            onClick={handleJumpNow}
            data-testid="pipeline-rejection-jump-btn"
            style={{
              background: 'linear-gradient(135deg, #cf1322 0%, #fa541c 100%)',
              border: 'none',
              fontWeight: 600,
              boxShadow: '0 2px 8px rgba(207, 19, 34, 0.3)',
            }}
          >
            进入拒付风险评估
          </Button>
        </Space>
      </Space>
    </div>
  )
}

export default PipelineRejectionRedirect
