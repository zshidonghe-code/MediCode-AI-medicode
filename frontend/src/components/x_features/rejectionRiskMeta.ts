import type { RejectionRiskLevel } from '../../types/api'

interface RejectionRiskMeta {
  label: string
  color: string
  bg: string
  textColor: string
  alertType: 'error' | 'warning' | 'info'
}

export const REJECTION_RISK_META: Record<RejectionRiskLevel, RejectionRiskMeta> = {
  high: {
    label: '高风险',
    color: 'red',
    bg: 'linear-gradient(135deg, #fff1f0 0%, #ffccc7 100%)',
    textColor: '#cf1322',
    alertType: 'error',
  },
  medium: {
    label: '中风险',
    color: 'orange',
    bg: 'linear-gradient(135deg, #fffbe6 0%, #ffe58f 100%)',
    textColor: '#d48806',
    alertType: 'warning',
  },
  low: {
    label: '低风险',
    color: 'green',
    bg: 'linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%)',
    textColor: '#3f8600',
    alertType: 'info',
  },
}
