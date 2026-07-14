import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

const { assessMock } = vi.hoisted(() => ({
  assessMock: vi.fn(),
}))

vi.mock('../../services/api', () => ({
  rejectionAPI: {
    assess: assessMock,
  },
}))

import { RejectionPredictor } from './RejectionPredictor'

describe('RejectionPredictor', () => {
  it('renders lowercase API risk levels with the correct labels', async () => {
    assessMock.mockResolvedValue({
      data: {
        overall_risk: 'high',
        risk_score: 60,
        preventable_amount: 1_800,
        risks: [
          {
            rule_id: 'RR-001',
            rule_name: 'DRG mismatch',
            risk_level: 'high',
            description: 'Mismatch detected',
          },
        ],
      },
    })

    render(<RejectionPredictor defaultContent="case summary" />)
    fireEvent.click(screen.getByRole('button', { name: '实时预测拒付风险' }))

    expect(await screen.findAllByText('高风险')).toHaveLength(2)
    expect(screen.queryByText('high')).not.toBeInTheDocument()
  })
})
