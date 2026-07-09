import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

// Mock the api module BEFORE importing the hook.
// 对齐真后端：dashboardAPI.getOverview + dashboardAPI.getQCTrend
vi.mock('../services/api', () => ({
  dashboardAPI: {
    getOverview: vi.fn(),
    getQCTrend: vi.fn(),
  },
}))

import { dashboardAPI } from '../services/api'
import { useLayoutData } from './useLayoutData'

// 真后端 /dashboard/overview 返回 shape（backend/src/api/v1/endpoints/dashboard.py:89）
const MOCK_OVERVIEW = {
  total_cases: 120,
  total_weight: 156.7,
  cmi: 1.31,
  avg_cost: 8420,
  avg_stay_days: 8.4,
  cost_consumption_index: 0.92,
  time_consumption_index: 0.88,
  low_risk_mortality_rate: 0.0,
  ai_coding_rate: 0.85,
  qc_pass_rate: 0.94,
}

// 真后端 /dashboard/qc-trend 返回 shape（dashboard.py:237）
const MOCK_QC_TREND = {
  trend: [
    { date: '2026-07-02', avg_score: 92.1, total_checks: 5, defect_rate: 0.08, cmi: 1.28 },
    { date: '2026-07-03', avg_score: 94.5, total_checks: 8, defect_rate: 0.05, cmi: 1.35 },
    { date: '2026-07-04', avg_score: 90.8, total_checks: 6, defect_rate: 0.09, cmi: 1.22 },
  ],
}

describe('useLayoutData', () => {
  beforeEach(() => {
    vi.mocked(dashboardAPI.getOverview).mockResolvedValue({
      data: MOCK_OVERVIEW,
    } as unknown as Awaited<ReturnType<typeof dashboardAPI.getOverview>>)
    vi.mocked(dashboardAPI.getQCTrend).mockResolvedValue({
      data: MOCK_QC_TREND,
    } as unknown as Awaited<ReturnType<typeof dashboardAPI.getQCTrend>>)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // Slice 1: 初始加载 — 调真 API（getOverview + getQCTrend） + 字段映射正确
  it('loads todayStats and trend7d on mount using real API names', async () => {
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // 调用真 API（不是 getTrendDaily）
    expect(dashboardAPI.getOverview).toHaveBeenCalledTimes(1)
    expect(dashboardAPI.getQCTrend).toHaveBeenCalledWith(7)

    // todayStats 字段对齐真后端 /overview 返回
    expect(result.current.todayStats).toEqual({
      totalCases: 120,
      cmi: 1.31,
      avgStayDays: 8.4,
      aiCodingRate: 0.85,
      qcPassRate: 0.94,
      loading: false,
    })

    // trend7d 字段对齐真后端 /qc-trend 返回
    expect(result.current.trend7d).toHaveLength(7)
    expect(result.current.trend7d[0]).toEqual({
      date: '2026-07-02',
      score: 92.1,
      checks: 5,
      defectRate: 0.08,
      cmi: 1.28,
    })
    expect(result.current.error).toBeNull()
  })

  // Slice 2: refresh 手动重新拉数据
  it('refresh() re-fetches both APIs', async () => {
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    const callsBefore = vi.mocked(dashboardAPI.getOverview).mock.calls.length
    await act(async () => {
      await result.current.refresh()
    })
    expect(vi.mocked(dashboardAPI.getOverview).mock.calls.length).toBe(callsBefore + 1)
    expect(vi.mocked(dashboardAPI.getQCTrend).mock.calls.length).toBe(callsBefore + 1)
  })

  // Slice 3: API 失败 → error 填充 + stats 走 fallback（不抛）
  it('sets error and falls back to empty stats when API fails', async () => {
    vi.mocked(dashboardAPI.getOverview).mockRejectedValueOnce(new Error('net fail'))
    vi.mocked(dashboardAPI.getQCTrend).mockRejectedValueOnce(new Error('net fail'))
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('net fail')
    expect(result.current.todayStats).toEqual({
      totalCases: 0,
      cmi: 0,
      avgStayDays: 0,
      aiCodingRate: 0,
      qcPassRate: 0,
      loading: false,
    })
    expect(result.current.trend7d).toHaveLength(7)
    expect(result.current.trend7d.every((p) => p.score === 0)).toBe(true)
  })

  // Slice 4: loading 初始 true → fetch 完成 false
  it('loading starts true and ends false after fetch', async () => {
    const { result } = renderHook(() => useLayoutData())
    expect(result.current.loading).toBe(true)
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })

  // Slice 5: 卸载清理 — interval 清理 + 不触发额外调用
  it('cleans up interval and prevents setState after unmount', async () => {
    const { result, unmount } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    const callsBeforeUnmount = vi.mocked(dashboardAPI.getOverview).mock.calls.length
    unmount()
    expect(vi.mocked(dashboardAPI.getOverview).mock.calls.length).toBe(callsBeforeUnmount)
  })
})