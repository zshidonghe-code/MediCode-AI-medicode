import { useState, useEffect, useCallback, useRef } from 'react'
import { dashboardAPI } from '../services/api'

export interface TodayStats {
  total: number
  avgMs: number
  savedYuan: number
  loading: boolean
}

export interface TrendPoint {
  day: string
  total: number
}

export interface UseLayoutDataResult {
  todayStats: TodayStats
  trend7d: TrendPoint[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

const EMPTY_TREND: TrendPoint[] = Array.from({ length: 7 }, (_, i) => ({
  day: `${i + 1}`,
  total: 0,
}))

const INITIAL_STATS: TodayStats = {
  total: 0,
  avgMs: 0,
  savedYuan: 0,
  loading: true,
}

/**
 * Layout 级数据 hook：今日统计 + 近 7 日趋势。
 * - 挂载时拉一次
 * - 60 秒自动刷新（卸载时清理 interval）
 * - 提供手动 refresh()
 * - API 失败时 error 填充，stats 走 fallback（不抛）
 */
export function useLayoutData(refreshIntervalMs = 60000): UseLayoutDataResult {
  const [todayStats, setTodayStats] = useState<TodayStats>(INITIAL_STATS)
  const [trend7d, setTrend7d] = useState<TrendPoint[]>(EMPTY_TREND)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const isMounted = useRef(true)

  const fetchAll = useCallback(async () => {
    try {
      const [overviewRes, trendRes] = await Promise.all([
        dashboardAPI.getOverview({ days: 1 }),
        dashboardAPI.getTrendDaily(7),
      ])
      if (!isMounted.current) return

      const data = overviewRes?.data ?? {}
      const total = data.today_count ?? data.total_cases ?? 0
      const avgMs = data.today_avg_ms ?? data.avg_processing_ms ?? 0
      const savedYuan = data.today_saved_yuan ?? data.estimated_savings ?? total * 240

      setTodayStats({ total, avgMs, savedYuan, loading: false })

      const list: any[] = trendRes?.data?.trend ?? []
      const arr: TrendPoint[] = list.map((row, i) => ({
        day: row.day || row.date?.slice(5) || `${i + 1}`,
        total: Number(row.total ?? 0),
      }))
      while (arr.length < 7) arr.push({ day: `${arr.length + 1}`, total: 0 })
      setTrend7d(arr)
      setError(null)
    } catch (e) {
      if (!isMounted.current) return
      setError(e instanceof Error ? e : new Error(String(e)))
      setTodayStats((s) => ({ ...s, loading: false }))
      setTrend7d(EMPTY_TREND)
    } finally {
      if (isMounted.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    isMounted.current = true
    fetchAll()
    const id = setInterval(fetchAll, refreshIntervalMs)
    return () => {
      isMounted.current = false
      clearInterval(id)
    }
  }, [fetchAll, refreshIntervalMs])

  const refresh = useCallback(() => fetchAll(), [fetchAll])

  return { todayStats, trend7d, loading, error, refresh }
}