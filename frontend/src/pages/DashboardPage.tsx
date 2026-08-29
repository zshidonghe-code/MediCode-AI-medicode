import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { Row, Col, Card, Statistic, Tag, Typography, Divider, Table, Spin, DatePicker, Space, Select, Alert, Button } from 'antd'
import {
  RiseOutlined, FallOutlined, TrophyOutlined, ReloadOutlined,
  ThunderboltOutlined, CheckCircleOutlined, LoadingOutlined,
} from '@ant-design/icons'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import {
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import { dashboardAPI } from '../services/api'
import type { OverviewData, DepartmentRanking, QcTrendItem, AccuracyTrendItem, HighFrequencyIssue, RevenueData } from '../types/dashboard'

echarts.use([
  AriaComponent,
  BarChart,
  CanvasRenderer,
  GridComponent,
  LegendComponent,
  LineChart,
  TooltipComponent,
])

const { Title, Text } = Typography

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [overview, setOverview] = useState<Partial<OverviewData>>({})
  const [rankings, setRankings] = useState<DepartmentRanking[]>([])
  const [issues, setIssues] = useState<HighFrequencyIssue[]>([])
  const [qcTrend, setQcTrend] = useState<QcTrendItem[]>([])
  const [accuracyTrend, setAccuracyTrend] = useState<AccuracyTrendItem[]>([])
  const [revenue, setRevenue] = useState<RevenueData | null>(null)
  const [days, setDays] = useState(30)

  // Demo state
  const [demoMode, setDemoMode] = useState(false)
  const demoActiveRef = useRef(false)

  useEffect(() => { fetchData() }, [days])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    const results = await Promise.allSettled([
      dashboardAPI.getOverview({}),
      dashboardAPI.getDepartmentRanking('cmi', 10),
      dashboardAPI.getHighFrequencyIssues(days, 8),
      dashboardAPI.getQCTrend(days),
      dashboardAPI.getCodingAccuracy(days),
      dashboardAPI.getRevenueAnalysis(days),
    ])

    const [ovR, rankR, issueR, qcR, accR, revR] = results
    let hasError = false

    if (ovR.status === 'fulfilled') {
      setOverview(ovR.value.data)
    } else { hasError = true }
    if (rankR.status === 'fulfilled') {
      setRankings(rankR.value.data.rankings || [])
    } else { hasError = true }
    if (issueR.status === 'fulfilled') {
      setIssues(issueR.value.data.issues || [])
    } else { hasError = true }
    if (qcR.status === 'fulfilled') {
      setQcTrend(qcR.value.data.trend || [])
    } else { hasError = true }
    if (accR.status === 'fulfilled') {
      setAccuracyTrend(accR.value.data.accuracy_trend || [])
    } else { hasError = true }
    if (revR.status === 'fulfilled') {
      setRevenue(revR.value.data)
    } else { hasError = true }

    if (hasError) {
      setError('部分数据加载失败，已显示可用数据')
    }
    setLoading(false)
  }, [days])

  // Demo handlers
  const startDemo = useCallback(() => {
    setDemoMode(true)
    demoActiveRef.current = true
    fetchData()
  }, [fetchData])

  // Celebration when loading completes in demo mode
  useEffect(() => {
    if (!demoActiveRef.current || loading) return
    demoActiveRef.current = false
  }, [loading])

  useEffect(() => {
    return () => { demoActiveRef.current = false }
  }, [])

  // === Chart options derived from API data ===
  const cmiOvernightOption = useMemo(() => ({
    aria: { enabled: true, decal: { show: true } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['CMI趋势', '质控评分'] },
    grid: { left: 60, right: 60, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: qcTrend.map((d) => d.date?.slice(5) || ''),
      axisLabel: { rotate: 45, fontSize: 10 },
    },
    yAxis: [
      { type: 'value', name: '质控评分', min: 0, max: 100 },
      { type: 'value', name: 'CMI', min: 0 },
    ],
    series: [
      {
        name: '质控评分', type: 'line',
        data: qcTrend.map((d) => d.avg_score),
        smooth: true, areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#1677ff' },
      },
      {
        name: 'CMI趋势', type: 'line', yAxisIndex: 1,
        data: qcTrend.map((d) => d.cmi ?? '-'),
        smooth: true, itemStyle: { color: '#52c41a' },
      },
    ],
  }), [qcTrend])

  const accuracyOption = useMemo(() => ({
    aria: { enabled: true },
    tooltip: { trigger: 'axis' },
    legend: { data: ['AI编码准确率'] },
    grid: { left: 60, right: 30, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: accuracyTrend.map((d) => d.date?.slice(5) || ''),
      axisLabel: { rotate: 45, fontSize: 10 },
    },
    yAxis: { type: 'value', name: '准确率', min: 0.7, max: 1.0, axisLabel: { formatter: (v: number) => (v * 100).toFixed(0) + '%' } },
    series: [
      {
        name: 'AI编码准确率', type: 'line',
        data: accuracyTrend.map((d) => d.ai_accuracy),
        smooth: true, areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#1677ff' },
      },
    ],
  }), [accuracyTrend])

  const revenueOption = useMemo(() => ({
    aria: { enabled: true },
    tooltip: { trigger: 'axis' },
    legend: { data: ['预期收入'] },
    grid: { left: 80, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: (revenue?.trend || []).map((d) => d.month?.slice(5) || ''),
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', name: '万元', axisLabel: { formatter: (v: number) => (v / 10000).toFixed(1) } },
    series: [
      { name: '预期收入', type: 'bar', data: (revenue?.trend || []).map((d) => d.expected), itemStyle: { color: '#1677ff' } },
    ],
  }), [revenue])

  const deptColumns = useMemo(() => [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 60,
      render: (v: number) => <span style={{ fontWeight: v <= 3 ? 'bold' : 'normal', color: v === 1 ? '#faad14' : v === 2 ? '#999' : v === 3 ? '#c47f3c' : undefined }}>{v}</span> },
    { title: '科室', dataIndex: 'dept', key: 'dept' },
    { title: '病例数', dataIndex: 'cases', key: 'cases' },
    { title: 'CMI', dataIndex: 'cmi', key: 'cmi', render: (v: number) => v?.toFixed(2) },
    {
      title: '费用指数', dataIndex: 'cost_index', key: 'cost_index',
      render: (v: number) => (
        <span style={{ color: v > 1 ? '#ff4d4f' : '#52c41a' }}>
          {v > 1 ? <RiseOutlined /> : <FallOutlined />} {v?.toFixed(2)}
        </span>
      ),
    },
    { title: '均住院日', dataIndex: 'avg_days', key: 'avg_days', render: (v: number) => v?.toFixed(1) + '天' },
  ], [])

  const { total_cases, cmi, total_weight, avg_stay_days, cost_consumption_index, time_consumption_index } = overview

  return (
    <div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3}><TrophyOutlined /> 数据驾驶舱</Title>
          <Text type="secondary">全院DRG运营概览与质控分析</Text>
        </div>
        <Space direction="vertical" align="end" size={4}>
          <Space>
            {!demoMode ? (
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={startDemo}
                style={{
                  background: 'linear-gradient(135deg, #6366f1, #0ea5e9)',
                  border: 'none', borderRadius: 8, fontWeight: 600,
                  boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                }}
              >
                快速演示
              </Button>
            ) : (
              <Button
                icon={<ReloadOutlined />}
                onClick={startDemo}
                style={{ background: 'linear-gradient(135deg, #6366f1, #0ea5e9)', border: 'none', color: '#fff' }}
              >
                重新演示
              </Button>
            )}
            <Select value={days} onChange={setDays}
              options={[
                { value: 7, label: '近7天' },
                { value: 30, label: '近30天' },
                { value: 90, label: '近90天' },
                { value: 180, label: '近半年' },
              ]}
              style={{ width: 100 }}
              disabled={demoMode}
            />
            <DatePicker.RangePicker />
            <ReloadOutlined onClick={fetchData} style={{ cursor: 'pointer', fontSize: 18 }} aria-label="刷新数据" role="button" tabIndex={0} />
          </Space>
          {demoMode && (
            <Tag
              color={loading ? 'processing' : 'success'}
              icon={loading ? <LoadingOutlined /> : <CheckCircleOutlined />}
            >
              {loading ? '数据加载中...' : '演示完成'}
            </Tag>
          )}
        </Space>
      </div>

      <Divider />

      {error && (
        <Alert type="error" message={error} closable showIcon
          action={<Button size="small" onClick={fetchData} icon={<ReloadOutlined />}>重试</Button>}
          style={{ marginBottom: 16 }} />
      )}

      <Spin spinning={loading}>
        {/* Top stat cards */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card hoverable><Statistic title="总病例数" value={total_cases ?? '-'} suffix="例" /></Card>
          </Col>
          <Col span={4}>
            <Card hoverable><Statistic title="CMI值" value={cmi ?? 0} precision={2} /></Card>
          </Col>
          <Col span={4}>
            <Card hoverable><Statistic title="总RW" value={total_weight ?? 0} precision={0} /></Card>
          </Col>
          <Col span={4}>
            <Card hoverable><Statistic title="平均住院日" value={avg_stay_days ?? 0} suffix="天" /></Card>
          </Col>
          <Col span={4}>
            <Card hoverable>
              <Statistic title="费用消耗指数" value={cost_consumption_index ?? 0} precision={2}
                valueStyle={{ color: (cost_consumption_index ?? 1) <= 1 ? '#3f8600' : '#ff4d4f' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card hoverable>
              <Statistic title="时间消耗指数" value={time_consumption_index ?? 0} precision={2}
                valueStyle={{ color: (time_consumption_index ?? 1) <= 1 ? '#3f8600' : '#ff4d4f' }} />
            </Card>
          </Col>
        </Row>

        {/* Charts row */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Card title="质控评分 & CMI 趋势">
              {qcTrend.length > 0 ? (
                <ReactEChartsCore echarts={echarts} option={cmiOvernightOption} style={{ height: 300 }} />
              ) : (
                <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc' }}>加载中...</div>
              )}
            </Card>
          </Col>
          <Col span={12}>
            <Card title="AI vs 人工编码准确率">
              {accuracyTrend.length > 0 ? (
                <ReactEChartsCore echarts={echarts} option={accuracyOption} style={{ height: 300 }} />
              ) : (
                <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc' }}>加载中...</div>
              )}
            </Card>
          </Col>
        </Row>

        {/* Rankings + Issues */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Card title="科室CMI排行榜（TOP10）">
              <Table columns={deptColumns} dataSource={rankings}
                rowKey="rank" size="small" pagination={false} />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="高频质控缺陷 TOP8">
              <Table
                dataSource={issues}
                columns={[
                  { title: '缺陷类型', dataIndex: 'issue', key: 'issue' },
                  { title: '次数', dataIndex: 'count', key: 'count', width: 60 },
                  { title: '占比', dataIndex: 'rate', key: 'rate', width: 60 },
                ]}
                rowKey="issue" size="small" pagination={false}
              />
            </Card>
          </Col>
        </Row>

        {/* Revenue analysis */}
        {revenue && revenue.trend.length > 0 && (
          <Row gutter={16}>
            <Col span={14}>
              <Card title="月度DRG预期收入">
                <ReactEChartsCore echarts={echarts} option={revenueOption} style={{ height: 280 }} />
              </Card>
            </Col>
            <Col span={10}>
              <Card title="DRG收入总览">
                <Row gutter={[0, 16]}>
                  <Col span={24}>
                    <Statistic title="预期总收入" value={revenue.expected_total} prefix="¥" precision={0}
                      valueStyle={{ color: '#1677ff' }} />
                  </Col>
                  {revenue.trend.slice(-1).map((m) => (
                    <Col span={12} key={m.month}>
                      <Statistic title={`${m.month} 月收入`} value={m.expected} prefix="¥" precision={0} />
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>
          </Row>
        )}
      </Spin>
    </div>
  )
}
