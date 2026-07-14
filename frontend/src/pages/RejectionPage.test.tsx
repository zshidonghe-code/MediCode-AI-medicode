import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

const { assessMock } = vi.hoisted(() => ({
  assessMock: vi.fn(),
}))

vi.mock('../services/api', () => ({
  rejectionAPI: {
    assess: assessMock,
  },
}))

import RejectionPage from './RejectionPage'

describe('RejectionPage pipeline handoff', () => {
  it('keeps the complete assessment context and existing result', async () => {
    const assessmentResult = {
      overall_risk: 'medium' as const,
      risk_score: 30,
      preventable_amount: 960,
      risks: [],
    }
    const state = {
      content: 'case summary',
      primary_diagnosis: { code: 'I21.0', name: 'Acute myocardial infarction' },
      secondary_diagnoses: [{ code: 'I10', name: 'Hypertension' }],
      procedures: [{ code: '36.06', name: 'Coronary stent insertion' }],
      drg_result: {
        drg_code: 'FM19',
        drg_name: 'PCI group',
        weight: 1.8,
        avg_los: 7,
      },
      patient_info: { age: 65, gender: 'male', days_of_stay: 8 },
      hospital_cost: 58_000,
      assessment_result: assessmentResult,
    }
    assessMock.mockResolvedValue({ data: assessmentResult })

    render(
      <MemoryRouter initialEntries={[{ pathname: '/rejection', state }]}>
        <Routes>
          <Route path="/rejection" element={<RejectionPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getAllByText('中风险').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: /开始评估拒付风险/ }))

    await waitFor(() => {
      expect(assessMock).toHaveBeenCalledWith({
        content: state.content,
        primary_diagnosis: state.primary_diagnosis,
        secondary_diagnoses: state.secondary_diagnoses,
        procedures: state.procedures,
        drg_result: state.drg_result,
        patient_info: state.patient_info,
        hospital_cost: state.hospital_cost,
      })
    })
  })
})
