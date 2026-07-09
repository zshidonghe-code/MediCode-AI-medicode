import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

// Mock the api module BEFORE importing the hook
vi.mock('../services/api', () => ({
  dashboardAPI: {
    getOverview: vi.fn(),
    getTrendDaily: vi.fn(),
  },
}))

import { dashboardAPI } from '../services/api'
import { useLayoutData } from './useLayoutData'

describe('useLayoutData', () => {
  beforeEach(() => {
    vi.mocked(dashboardAPI.getOverview).mockResolvedValue({
      data: { today_count: 12, today_avg_ms: 350, today_saved_yuan: 2880 },
    } as any)
    vi.mocked(dashboardAPI.getTrendDaily).mockResolvedValue({
      data: {
        trend: [
          { date: '2026-07-02', day: '07-02', total: 5 },
          { date: '2026-07-03', day: '07-03', total: 8 },
        ],
      },
    } as any)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // Test 1: 初始加载 — 调一次 API + 状态正确填充
  it('loads todayStats and trend7d on mount', async () => {
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(dashboardAPI.getOverview).toHaveBeenCalledWith({ days: 1 })
    expect(dashboardAPI.getTrendDaily).toHaveBeenCalledWith(7)
    expect(result.current.todayStats).toEqual({
      total: 12, avgMs: 350, savedYuan: 2880, loading: false,
    })
    expect(result.current.trend7d).toHaveLength(7) // 补 0 占位
    expect(result.current.trend7d[0]).toEqual({ day: '07-02', total: 5 })
    expect(result.current.error).toBeNull()
  })

  // Test 2: refresh — 手动刷新重新拉数据
  it('refresh() re-fetches data', async () => {
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(dashboardAPI.getOverview).toHaveBeenCalledTimes(1)

    await act(async () => {
      await result.current.refresh()
    })
    expect(dashboardAPI.getOverview).toHaveBeenCalledTimes(2)
    expect(dashboardAPI.getTrendDaily).toHaveBeenCalledTimes(2)
  })

  // Test 3: 错误处理 — API 失败时 error 字段填充，不抛
  it('captures error when API fails', async () => {
    vi.mocked(dashboardAPI.getOverview).mockRejectedValueOnce(new Error('network down'))
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('network down')
    // fallback 仍可用
    expect(result.current.todayStats.total).toBe(0)
    expect(result.current.trend7d).toHaveLength(7)
  })

  // Test 4: loading 状态 — 加载中为 true，加载完为 false
  it('flips loading flag during fetch', async () => {
    vi.mocked(dashboardAPI.getOverview).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ data: {} } as any), 100))
    )
    const { result } = renderHook(() => useLayoutData())
    // 同步阶段：loading = true
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
  })

  // Test 5: 卸载清理 — 卸载后不再触发 setState / interval 被清理
  it('cleans up interval on unmount', async () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval')
    const { unmount, result } = renderHook(() => useLayoutData())
    await waitFor(() => expect(result.current.loading).toBe(false))
    const callCountBefore = clearIntervalSpy.mock.calls.length
    unmount()
    expect(clearIntervalSpy.mock.calls.length).toBeGreaterThan(callCountBefore)
    clearIntervalSpy.mockRestore()
  })
})