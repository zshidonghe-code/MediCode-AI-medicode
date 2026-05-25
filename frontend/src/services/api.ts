import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

export { api }

export function setApiAuth(token: string | null) {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// Response interceptor for error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('medicode_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// === Coding API ===
export const codingAPI = {
  autoCode: (data: { record_id: number; record_type: string; content: string }) =>
    api.post('/coding/auto-code', data),

  uploadAndCode: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/coding/auto-code/upload', formData)
  },

  validate: (coding: any) => api.post('/coding/validate', coding),

  searchICD: (keyword: string, limit = 20) =>
    api.get('/coding/search', { params: { keyword, limit } }),
}

// === DRG API ===
export const drgAPI = {
  group: (data: any) => api.post('/drg/group', data),

  getDetail: (code: string) => api.get(`/drg/group/${code}`),

  compare: (recordId: number, aiDrg: string, manualDrg: string) =>
    api.get('/drg/compare', { params: { record_id: recordId, ai_drg: aiDrg, manual_drg: manualDrg } }),
}

// === QC API ===
export const qcAPI = {
  check: (data: { record_id: number; record_type: string; content: string; coding_result?: any }) =>
    api.post('/qc/check', data),

  getRules: (ruleType = '', severity = '') =>
    api.get('/qc/rules', { params: { rule_type: ruleType, severity } }),

  acceptResult: (id: number, note = '') => api.put(`/qc/results/${id}/accept`, { note }),

  rejectResult: (id: number, note = '') => api.put(`/qc/results/${id}/reject`, { note }),
}

// === Dashboard API ===
export const dashboardAPI = {
  getOverview: (params: any) => api.get('/dashboard/overview', { params }),
  getDepartmentRanking: (metric = 'cmi', limit = 10) =>
    api.get('/dashboard/department-ranking', { params: { metric, limit } }),
  getQCTrend: (days = 30) => api.get('/dashboard/qc-trend', { params: { days } }),
  getCodingAccuracy: (days = 30) => api.get('/dashboard/coding-accuracy', { params: { days } }),
  getHighFrequencyIssues: (days = 30, limit = 10) =>
    api.get('/dashboard/high-frequency-issues', { params: { days, limit } }),
  getRevenueAnalysis: (days = 30) => api.get('/dashboard/revenue-analysis', { params: { days } }),
}

// === Pipeline API ===
export const pipelineAPI = {
  save: (data: {
    content?: string
    record_type: string
    coding_result?: any
    qc_result?: any
    drg_result?: any
    department?: string
    patient_info?: { age?: number; gender?: string }
    primary_diagnosis_code?: string
    secondary_diagnosis_codes?: string[]
    procedure_codes?: string[]
  }) =>
    api.post('/pipeline/save', data),
}

// === Admin API ===
export const adminAPI = {
  reset: (confirm: boolean = false) =>
    api.post('/admin/reset', { confirm }),

  exportCodingResults: (format: 'json' | 'csv' = 'json') =>
    api.get('/admin/export/coding-results', { params: { format }, responseType: 'blob' }),

  exportPatientSummaries: (format: 'json' | 'csv' = 'json') =>
    api.get('/admin/export/patient-summaries', { params: { format }, responseType: 'blob' }),

  exportQCResults: (format: 'json' | 'csv' = 'json') =>
    api.get('/admin/export/qc-results', { params: { format }, responseType: 'blob' }),
}
