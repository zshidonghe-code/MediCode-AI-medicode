import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Space, Typography, Progress } from 'antd'
import { ArrowRightOutlined, CloseOutlined, SafetyCertificateOutlined } from '@ant-design/icons'

const { Text } = Typography

interface PipelineRejectionRedirectProps {
  // 流水线完成后触发 (即 rejectionResult 存在)
  trigger: boolean
  // 传递给 /rejection 页面的预填数据
  prefill: {
    content: string
    primary_diagnosis?: { code: string; name: string } | null
    patient_info?: { age?: number; gender?: string; days_of_stay?: number }
    hospital_cost?: number
  }
  // 自动跳转倒计时秒数 (0 = 不自动跳转, 只显示按钮)
  countdownSeconds?: number
}

const COUNTDOWN_TOTAL = 5

/**
 * B v2 - PipelinePage 末尾自动跳转组件
 *
 * 董事会 2026-07-09 决议: B 拒付预测演示路径零摩擦
 * 流水线分析完成后, 此组件在页面底部显示 CTA, 默认 5 秒后自动跳转到 /rejection
 * 用户可点击按钮立即跳转, 或点击关闭取消自动跳转
 *
 * 独立组件 → 符合 FROZEN.md 规则 2 (新功能必须独立组件 + 董事会审批)
 */
export function PipelineRejectionRedirect({
  trigger,
  prefill,
  countdownSeconds = COUNTDOWN_TOTAL,
}: PipelineRejectionRedirectProps) {
  const navigate = useNavigate()
  const [secondsLeft, setSecondsLeft] = useState(countdownSeconds)
  const [cancelled, setCancelled] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 触发自动倒计时
  useEffect(() => {
    if (!trigger) {
      // 流水线未完成 → 重置
      setSecondsLeft(countdownSeconds)
      setCancelled(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      return
    }

    if (cancelled) return

    setSecondsLeft(countdownSeconds)

    timerRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          if (timerRef.current) {
            clearInterval(timerRef.current)
            timerRef.current = null
          }
          // 倒计时结束 → 跳转
          navigate('/rejection', { state: prefill })
          return 0
        }
        return s - 1
      })
    }, 1000)

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [trigger, cancelled]) // eslint-disable-line react-hooks/exhaustive-deps

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  if (!trigger) return null

  const percent = ((countdownSeconds - secondsLeft) / countdownSeconds) * 100

  const handleJumpNow = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    navigate('/rejection', { state: prefill })
  }

  const handleCancel = () => {
    setCancelled(true)
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
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
              ✅ 流水线分析完成
            </Text>
          </Space>
          {!cancelled && secondsLeft > 0 && (
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={handleCancel}
              aria-label="取消自动跳转"
              style={{ color: '#999' }}
            />
          )}
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

          {!cancelled && secondsLeft > 0 && (
            <Space size={4} align="center">
              <Text type="secondary" style={{ fontSize: 12 }}>自动跳转</Text>
              <Text strong style={{ color: '#cf1322', fontSize: 16, minWidth: 24, textAlign: 'center' }}>
                {secondsLeft}s
              </Text>
            </Space>
          )}
          {cancelled && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              已取消自动跳转
            </Text>
          )}
        </Space>

        {!cancelled && secondsLeft > 0 && (
          <Progress
            percent={percent}
            showInfo={false}
            strokeColor="#cf1322"
            size="small"
            style={{ marginBottom: 0 }}
          />
        )}
      </Space>
    </div>
  )
}

export default PipelineRejectionRedirect
