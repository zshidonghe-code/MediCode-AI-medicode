// API request/response type definitions

export interface CodeItem {
  code: string
  name: string
  category?: string
  score?: number
  semantic_score?: number
  freq_score?: number
}

export interface CodingResultData {
  primary_diagnosis: CodeItem | null
  secondary_diagnoses: CodeItem[]
  procedures: CodeItem[]
  suggestions: CodeItem[]
  confidence: number
  warnings: string[]
}

export interface CodingAutoCodeRequest {
  record_id: number
  record_type: string
  content: string
}

export interface DRGGroupRequest {
  primary_diagnosis_code: string
  secondary_diagnosis_codes: string[]
  procedure_codes: string[]
  patient_info: {
    age?: number
    gender?: string
    days_of_stay?: number
  }
  coding_result?: CodingResultData
}

export interface DRGResultData {
  mdc: string
  mdc_name: string
  adrg: string
  adrg_name: string
  drg_code: string
  drg_name: string
  is_surgical: boolean
  weight: number
  rate: number
  estimated_payment: number
  cc_flag: string
  patient_complexity: string
}

export interface QCCheckRequest {
  record_id: number
  record_type: string
  content: string
  coding_result?: CodingResultData
  patient_info?: Record<string, unknown>
  use_llm?: boolean
}

export interface QCIssueData {
  rule_id: string
  rule_name: string
  rule_type: string
  severity: 'critical' | 'major' | 'minor' | 'info'
  description: string
  line_snippet?: string
  suggestion?: string
  line_number?: number
}

export interface QCResultData {
  record_id: number
  issues: QCIssueData[]
  total: number
  critical_count: number
  major_count: number
  minor_count: number
  info_count: number
  score: number
}

export interface DashboardOverviewParams {
  days?: number
  department?: string
}

export interface PipelineSaveRequest {
  content?: string
  record_type: string
  coding_result?: CodingResultData
  qc_result?: QCResultData
  drg_result?: DRGResultData
  department?: string
  patient_info?: { age?: number; gender?: string }
  primary_diagnosis_code?: string
  secondary_diagnosis_codes?: string[]
  procedure_codes?: string[]
}

export type RejectionRiskLevel = 'high' | 'medium' | 'low'

export interface RejectionRiskItemData {
  rule_id: string
  rule_name: string
  risk_level: RejectionRiskLevel
  description: string
  affected_code: string
  suggestion: string
  estimated_loss: number
}

export interface RejectionResultData {
  overall_risk: RejectionRiskLevel
  risk_score: number
  preventable_amount: number
  risks: RejectionRiskItemData[]
}

export type RejectionCodeItem = Pick<CodeItem, 'code' | 'name'>

export interface RejectionDRGInfo {
  drg_code: string
  drg_name: string
  weight: number
  avg_los: number
}

export interface RejectionPatientInfo {
  age: number
  gender: string
  days_of_stay: number
}

export interface RejectionAssessRequest {
  primary_diagnosis?: RejectionCodeItem | null
  secondary_diagnoses?: RejectionCodeItem[]
  procedures?: RejectionCodeItem[]
  drg_result?: RejectionDRGInfo
  patient_info?: RejectionPatientInfo
  content?: string
  hospital_cost?: number
}

export interface RejectionPageState extends RejectionAssessRequest {
  assessment_result?: RejectionResultData
}
