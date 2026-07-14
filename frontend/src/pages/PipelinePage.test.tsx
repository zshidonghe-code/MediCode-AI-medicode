import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

const apiMocks = vi.hoisted(() => ({
  autoCode: vi.fn(),
  check: vi.fn(),
  group: vi.fn(),
  assess: vi.fn(),
  save: vi.fn(),
}))

vi.mock('../services/api', () => ({
  codingAPI: { autoCode: apiMocks.autoCode },
  qcAPI: { check: apiMocks.check },
  drgAPI: { group: apiMocks.group },
  rejectionAPI: { assess: apiMocks.assess },
  pipelineAPI: { save: apiMocks.save },
}))

vi.mock('../components/IcdCodingResult', () => ({ default: () => null }))
vi.mock('../components/x_features/PipelineRejectionRedirect', () => ({ default: () => null }))

import PipelinePage from './PipelinePage'

describe('PipelinePage patient context', () => {
  it('uses the latest patient fields in DRG grouping and rejection assessment', async () => {
    const codingResult = {
      primary_diagnosis: { code: 'I21.0', name: '急性心肌梗死' },
      secondary_diagnoses: [],
      procedures: [],
      confidence: 0.95,
    }
    const drgResult = {
      drg_code: 'FR11',
      drg_name: '急性心肌梗死组',
      mdc: 'MDCE',
      mdc_name: '循环系统',
      adrg: 'FR1',
      adrg_name: '急性心肌梗死',
      is_surgical: false,
      weight: 1.8,
      rate: 8_000,
      estimated_payment: 14_400,
      cc_flag: 'MCC',
      patient_complexity: '高',
      avg_days: 7,
    }

    apiMocks.autoCode.mockResolvedValue({ data: codingResult })
    apiMocks.check.mockResolvedValue({ data: { issues: [], quality_score: 100 } })
    apiMocks.group.mockResolvedValue({ data: drgResult })
    apiMocks.assess.mockResolvedValue({
      data: { overall_risk: 'low', risk_score: 0, preventable_amount: 0, risks: [] },
    })
    apiMocks.save.mockResolvedValue({ data: { qc_result_ids: [] } })

    render(
      <MemoryRouter>
        <PipelinePage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByPlaceholderText('请粘贴住院病历内容（出院小结、入院记录等）...'), {
      target: { value: '患者入院后完善检查。' },
    })
    fireEvent.change(screen.getByPlaceholderText('岁'), { target: { value: '67' } })
    fireEvent.change(screen.getByPlaceholderText('天'), { target: { value: '9' } })
    const genderSelect = screen.getAllByRole('combobox')[1]
    fireEvent.mouseDown(genderSelect)
    fireEvent.click(await screen.findByText('女'))
    fireEvent.click(screen.getByRole('button', { name: /开始智能分析/ }))

    await waitFor(() => {
      expect(apiMocks.group).toHaveBeenCalledWith(expect.objectContaining({
        patient_age: 67,
        patient_gender: 'female',
        days_of_stay: 9,
      }))
      expect(apiMocks.assess).toHaveBeenCalledWith(expect.objectContaining({
        patient_info: { age: 67, gender: 'female', days_of_stay: 9 },
      }))
    })
  })
})
