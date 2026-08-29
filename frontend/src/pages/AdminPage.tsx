import { useState, useEffect } from 'react'
import {
  Typography, Card, Row, Col, Button, Modal, Input,
  Radio, Space, Alert, Spin, message, Statistic, Divider,
} from 'antd'
import {
  SettingOutlined, DeleteOutlined, DownloadOutlined,
  ExclamationCircleOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { adminAPI, getApiErrorMessage } from '../services/api'

const { Title, Text, Paragraph } = Typography

export default function AdminPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [exporting, setExporting] = useState<string | null>(null)
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json')
  const [resetModalOpen, setResetModalOpen] = useState(false)
  const [resetConfirmText, setResetConfirmText] = useState('')
  const [resetting, setResetting] = useState(false)

  const fetchPreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await adminAPI.reset(false)
      setCounts(res.data.counts || {})
    } catch (e: unknown) {
      setError(getApiErrorMessage(e, '无法获取数据预览'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPreview()
  }, [])

  const handleReset = async () => {
    setResetting(true)
    try {
      await adminAPI.reset(true)
      message.success('数据已重置')
      setResetModalOpen(false)
      setResetConfirmText('')
      // Refresh preview
      await fetchPreview()
    } catch (e: unknown) {
      message.error(getApiErrorMessage(e, '重置失败'))
    } finally {
      setResetting(false)
    }
  }

  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleExport = async (type: 'coding-results' | 'patient-summaries' | 'qc-results', label: string) => {
    setExporting(type)
    try {
      const ext = exportFormat === 'csv' ? 'csv' : 'json'
      let res
      if (type === 'coding-results') res = await adminAPI.exportCodingResults(exportFormat)
      else if (type === 'patient-summaries') res = await adminAPI.exportPatientSummaries(exportFormat)
      else res = await adminAPI.exportQCResults(exportFormat)

      const contentDisposition = res.headers?.['content-disposition']
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `medicode_${type}.${ext}`
      downloadFile(res.data as Blob, filename)
      message.success(`${label}导出成功`)
    } catch (e: unknown) {
      let detail = '导出失败'
      if (e instanceof Error) detail = e.message
      if (e && typeof e === 'object' && 'response' in e && e.response && typeof e.response === 'object' && 'data' in e.response && e.response.data instanceof Blob) {
        try {
          const text = await e.response.data.text()
          detail = JSON.parse(text).detail || detail
        } catch { /* ignore parse errors */ }
      }
      message.error(detail)
    } finally {
      setExporting(null)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}><SettingOutlined /> 系统管理</Title>
        <Text type="secondary">数据重置与导出操作（仅管理员可见）</Text>
      </div>

      {error && (
        <Alert
          type="error" message={error} closable showIcon
          action={<Button size="small" onClick={fetchPreview} icon={<ReloadOutlined />}>重试</Button>}
          style={{ marginBottom: 16 }}
        />
      )}

      <Spin spinning={loading}>

        {/* ── 数据重置 ──────────────────────────────────────────────── */}
        <Card
          title={<><DeleteOutlined /> 数据重置</>}
          style={{ marginBottom: 24 }}
        >
          <Alert
            type="warning"
            showIcon
            icon={<ExclamationCircleOutlined />}
            message="此操作将清空所有患者数据、病历记录、编码结果和质控结果"
            description="ICD编码库、DRG分组、质控规则等参考数据不受影响。此操作不可撤销，请谨慎执行。"
            style={{ marginBottom: 16 }}
          />

          <Row gutter={24} style={{ marginBottom: 16 }}>
            <Col span={6}><Statistic title="患者" value={counts.patients ?? 0} suffix="人" /></Col>
            <Col span={6}><Statistic title="病历" value={counts.medical_records ?? 0} suffix="份" /></Col>
            <Col span={6}><Statistic title="编码结果" value={counts.coding_results ?? 0} suffix="条" /></Col>
            <Col span={6}><Statistic title="质控结果" value={counts.qc_results ?? 0} suffix="条" /></Col>
          </Row>

          <Button
            type="primary" danger
            icon={<DeleteOutlined />}
            disabled={Object.values(counts).length === 0 || Object.values(counts).every(v => v === 0)}
            onClick={() => setResetModalOpen(true)}
          >
            重置全部数据
          </Button>
        </Card>

        {/* ── 数据导出 ──────────────────────────────────────────────── */}
        <Card
          title={<><DownloadOutlined /> 数据导出</>}
        >
          <Space style={{ marginBottom: 16 }}>
            <Text>导出格式：</Text>
            <Radio.Group value={exportFormat} onChange={e => setExportFormat(e.target.value)}>
              <Radio.Button value="json">JSON</Radio.Button>
              <Radio.Button value="csv">CSV</Radio.Button>
            </Radio.Group>
          </Space>

          <Divider />

          <Row gutter={16}>
            <Col span={8}>
              <Card size="small" style={{ background: '#fafafa' }}>
                <Paragraph strong>编码结果</Paragraph>
                <Paragraph type="secondary" style={{ fontSize: 12 }}>
                  含诊断编码、手术编码、置信度、创建时间等
                </Paragraph>
                <Button
                  icon={<DownloadOutlined />}
                  loading={exporting === 'coding-results'}
                  onClick={() => handleExport('coding-results', '编码结果')}
                  block
                >
                  下载编码结果
                </Button>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small" style={{ background: '#fafafa' }}>
                <Paragraph strong>患者摘要</Paragraph>
                <Paragraph type="secondary" style={{ fontSize: 12 }}>
                  含患者ID、性别、年龄、就诊科室、病历数量等
                </Paragraph>
                <Button
                  icon={<DownloadOutlined />}
                  loading={exporting === 'patient-summaries'}
                  onClick={() => handleExport('patient-summaries', '患者摘要')}
                  block
                >
                  下载患者摘要
                </Button>
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small" style={{ background: '#fafafa' }}>
                <Paragraph strong>质控结果</Paragraph>
                <Paragraph type="secondary" style={{ fontSize: 12 }}>
                  含缺陷等级、质检规则、问题片段、修改建议等
                </Paragraph>
                <Button
                  icon={<DownloadOutlined />}
                  loading={exporting === 'qc-results'}
                  onClick={() => handleExport('qc-results', '质控结果')}
                  block
                >
                  下载质控结果
                </Button>
              </Card>
            </Col>
          </Row>
        </Card>
      </Spin>

      {/* ── 重置确认弹窗 ──────────────────────────────────────────── */}
      <Modal
        title="确认重置数据"
        open={resetModalOpen}
        onOk={handleReset}
        onCancel={() => { setResetModalOpen(false); setResetConfirmText('') }}
        okText="确认重置"
        cancelText="取消"
        okButtonProps={{ danger: true, disabled: resetConfirmText !== 'RESET', loading: resetting }}
        destroyOnClose
      >
        <Alert
          type="error"
          showIcon
          message="此操作不可撤销！"
          description="所有患者数据、病历记录、编码结果、质控结果将被永久删除。"
          style={{ marginBottom: 16 }}
        />
        <Paragraph>请输入 <Text code strong>RESET</Text> 确认操作：</Paragraph>
        <Input
          value={resetConfirmText}
          onChange={e => setResetConfirmText(e.target.value)}
          placeholder="输入 RESET"
          style={{ marginTop: 8 }}
        />
      </Modal>
    </div>
  )
}
