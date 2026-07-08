import { useState, useEffect, useCallback, useRef } from 'react'
import { dashboardAPI } from '../services/api'

/**
 * Layout 级统计数据 — 字段对齐真后端 /dashboard/overview 返回 shape。
 * 后端源：backend/src/api/v1/endpoints/dashboard.py:89
 */
export interface TodayStats {
  totalCases: number
  cmi: number
  avgStayDays: number
  aiCodingRate: number
  qcPassRate: number
  loading: boolean
}

/**
 * 质控趋势点 — 字段对齐真后端 /dashboard/qc-trend 返回 shape。
 * 后端源：backend/src/api/v1/endpoints/dashboard.py:196
 */
export interface TrendPoint {
  date: string
  score: number
  checks: number
  defectRate: number
  cmi: number | null
}

export interface UseLayoutDataResult {
  todayStats: TodayStats
  trend7d: TrendPoint[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

const EMPTY_TREND: TrendPoint[] = Array.from({ length: 7 }, () => ({
  date: '',
  score: 0,
  checks: 0,
  defectRate: 0,
  cmi: null,
}))

const INITIAL_STATS: TodayStats = {
  totalCases: 0,
  cmi: 0,
  avgStayDays: 0,
  aiCodingRate: 0,
  qcPassRate: 0,
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
      // 调真 API：getOverview + getQCTrend（之前错调 getTrendDaily，已修复）
      const [overviewRes, trendRes] = await Promise.all([
        dashboardAPI.getOverview({}),
        dashboardAPI.getQCTrend(7),
      ])
      if (!isMounted.current) return

      const overview = overviewRes?.data ?? {}
      setTodayStats({
        totalCases: Number(overview.total_cases ?? 0),
        cmi: Number(overview.cmi ?? 0),
        avgStayDays: Number(overview.avg_stay_days ?? 0),
        aiCodingRate: Number(overview.ai_coding_rate ?? 0),
        qcPassRate: Number(overview.qc_pass_rate ?? 0),
        loading: false,
      })

      const rawList = (trendRes?.data?.trend ?? []) as Array<{
        date?: string
        avg_score?: number
        total_checks?: number
        defect_rate?: number
        cmi?: number | null
      }>
      const mapped: TrendPoint[] = rawList.map((row) => ({
        date: row.date ?? '',
        score: Number(row.avg_score ?? 0),
        checks: Number(row.total_checks ?? 0),
        defectRate: Number(row.defect_rate ?? 0),
        cmi: row.cmi != null ? Number(row.cmi) : null,
      }))
      // 补齐到 7 个点（不足则用占位）
      while (mapped.length < 7) {
        mapped.push({ date: '', score: 0, checks: 0, defectRate: 0, cmi: null })
      }
      setTrend7d(mapped.slice(0, 7))
      setError(null)
    } catch (e) {
      if (!isMounted.current) return
      setError(e instanceof Error ? e : new Error(String(e)))
      setTodayStats({
        totalCases: 0,
        cmi: 0,
        avgStayDays: 0,
        aiCodingRate: 0,
        qcPassRate: 0,
        loading: false,
      })
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