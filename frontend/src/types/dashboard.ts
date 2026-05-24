export interface OverviewData {
  total_cases: number
  total_weight: number
  cmi: number
  avg_cost: number
  avg_stay_days: number
  cost_consumption_index: number
  time_consumption_index: number
  low_risk_mortality_rate: number
  ai_coding_rate: number
  qc_pass_rate: number
}

export interface DepartmentRanking {
  rank: number
  dept: string
  cases: number
  cmi: number
  cost_index: number
  avg_days: number
}

export interface QcTrendItem {
  date: string
  avg_score: number
  total_checks: number
  defect_rate: number
  cmi: number | null
}

export interface AccuracyTrendItem {
  date: string
  ai_accuracy: number
}

export interface HighFrequencyIssue {
  issue: string
  count: number
  rate: string
}

export interface RevenueTrendItem {
  month: string
  expected: number
  cases: number
}

export interface RevenueData {
  expected_total: number
  trend: RevenueTrendItem[]
}
