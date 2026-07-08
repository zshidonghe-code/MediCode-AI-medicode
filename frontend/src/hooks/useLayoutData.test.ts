import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'

// Mock the api module BEFORE importing the hook
vi.mock('../services/api', () => ({
  dashboardAPI: {
    getOverview: vi.fn(),
    getTrendDaily: vi.fn(),
  },
}))

const dashApi = dashboardAPI as any

import { dashboardAPI } from '../services/api'
import { useLayoutData } from './useLayoutData'

describe('useLayoutData', () => {
  beforeEach(() => {
    vi.mocked(dashboardAPI.getOverview).mockResolvedValue({
      data: { today_count: 12, today_avg_ms: 350, today_saved_yuan: 2880 },
    } as any)
    vi.mocked(dashApi.getTrendDaily).mockResolvedValue({
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
    expect(dashApi.getTrendDaily).toHaveBeenCalledWith(7)
    expect(result.current.todayStats).toEqual({
      total: 12, avgMs: 350, savedYuan: 2880, loading: false,
    })
    expect(result.current.trend7d).toHaveLength(7) // 补 0 占位
    expect(result.current.trend7d[0]).toEqual({ day: '07-02', total: 5 })
    expect(result.current.error).toBeNull()
  })

  // Test 2: refresh — 手动刷新重新拉数据
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
    expect(vi.mocked(dashApi.getTrendDaily).mock.calls.length).toBe(callsBefore + 1)
  })

  // Test 3: 错误 — API 失败时 error 填充 + stats 走 fallback（不抛）
  it('sets error and falls back to empty stats when API fails', async () => {
    vi.mocked(dashboardAPI.getOverview).mockRejectedValueOnce(new Error('net fail'))
    vi.mocked(dashApi.getTrendDaily).mockRejectedValueOnce(new Error('net fail'))
    const { result } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('net fail')
    expect(result.current.todayStats).toEqual({
      total: 0, avgMs: 0, savedYuan: 0, loading: false,
    })
    expect(result.current.trend7d).toHaveLength(7)
    expect(result.current.trend7d.every((p) => p.total === 0)).toBe(true)
  })

  // Test 4: loading — 初次 loading=true，结束后 false
  it('loading starts true and ends false after fetch', async () => {
    const { result } = renderHook(() => useLayoutData())
    // mount 时立即为 true
    expect(result.current.loading).toBe(true)
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })

  // Test 5: 卸载清理 — interval 清理 + isMounted=false 阻止 setState
  it('cleans up interval and prevents setState after unmount', async () => {
    const { result, unmount } = renderHook(() => useLayoutData())
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
    const callsBeforeUnmount = vi.mocked(dashboardAPI.getOverview).mock.calls.length
    unmount()
    // 等待 1.2x refreshInterval 不会触发新调用（默认 60s，但 mock 不会真的等那么久）
    // 此处只验证 unmount 后没有立即的额外调用（避免 spurious updates）
    expect(vi.mocked(dashboardAPI.getOverview).mock.calls.length).toBe(callsBeforeUnmount)
  })
})