import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { navigateMock } = vi.hoisted(() => ({
  navigateMock: vi.fn(),
}))

vi.mock('react-router-dom', () => ({
  useNavigate: () => navigateMock,
}))

import { PipelineRejectionRedirect } from './PipelineRejectionRedirect'

describe('PipelineRejectionRedirect', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('navigates only after an explicit user action', () => {
    const prefill = {
      content: 'case summary',
      assessment_result: {
        overall_risk: 'low' as const,
        risk_score: 0,
        preventable_amount: 0,
        risks: [],
      },
    }

    render(<PipelineRejectionRedirect trigger prefill={prefill} />)

    act(() => {
      vi.advanceTimersByTime(10_000)
    })
    expect(navigateMock).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: /进入拒付风险评估/ }))
    expect(navigateMock).toHaveBeenCalledWith('/rejection', { state: prefill })
  })
})
