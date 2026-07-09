import { useState } from 'react'
import { Card, Button, Upload, Tag, Space, Typography, Spin, Alert, List } from 'antd'
import { InboxOutlined, FileTextOutlined } from '@ant-design/icons'
import { codingAPI } from '../../services/api'

const { Title, Text, Paragraph } = Typography
const { Dragger } = Upload

interface DocUploadCoderProps {
  onCoded?: (result: any) => void
}

/**
 * X 功能迷你版 A — 病历文档上传 → 自动编码
 * 后端: POST /api/v1/coding/auto-code/upload (multipart)
 * 支持: .txt / .docx / .pdf (≤10MB)
 * 演示路径: CodingPage 编码工作台
 */
export function DocUploadCoder({ onCoded }: DocUploadCoderProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    filename: string
    status: string
    text?: string
    coding_result?: {
      primary_diagnosis?: { code: string; name: string }
      secondary_diagnoses?: Array<{ code: string; name: string }>
      procedures?: Array<{ code: string; name: string }>
      confidence?: number
    }
    supported?: string[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.txt,.docx,.pdf',
    showUploadList: false,
    beforeUpload: async (file: File) => {
      setLoading(true)
      setError(null)
      setResult(null)
      try {
        const res = await codingAPI.uploadAndCode(file)
        setResult(res.data)
        onCoded?.(res.data)
      } catch (e) {
        setError(e instanceof Error ? e.message : '上传编码失败')
      } finally {
        setLoading(false)
      }
      return false // 阻止 antd 默认上传
    },
  }

  return (
    <Card
      data-testid="doc-upload-coder"
      title={<Space><FileTextOutlined /><Title level={5} style={{ margin: 0 }}>病历文档上传自动编码</Title></Space>}
      extra={<Tag color="purple">X-Beta</Tag>}
      style={{ marginBottom: 16 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Paragraph type="secondary" style={{ margin: 0 }}>
          上传 .txt / .docx / .pdf 病历文档(≤10MB),AI 自动提取主诊/手术并推荐 ICD 编码
        </Paragraph>

        <Dragger {...uploadProps} disabled={loading} data-testid="doc-upload-dragger">
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽病历文档到此区域</p>
          <p className="ant-upload-hint">支持 .txt / .docx / .pdf 格式,单文件不超过 10MB</p>
        </Dragger>

        {loading && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin tip="AI 解析中..." />
          </div>
        )}

        {error && <Alert type="error" message={error} showIcon />}

        {result && !loading && (
          <Card type="inner" title={`📄 ${result.filename}`}>
            {result.status === 'unsupported_format' ? (
              <Alert
                type="warning"
                message={`不支持的文件格式,仅支持: ${result.supported?.join(', ')}`}
                showIcon
              />
            ) : (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {result.coding_result?.confidence != null && (
                  <Tag color="blue">AI 置信度: {(result.coding_result.confidence * 100).toFixed(1)}%</Tag>
                )}

                {result.coding_result?.primary_diagnosis && (
                  <div>
                    <Text strong>主诊断:</Text>{' '}
                    <Tag color="red">{result.coding_result.primary_diagnosis.code}</Tag>
                    <Text>{result.coding_result.primary_diagnosis.name}</Text>
                  </div>
                )}

                {result.coding_result?.secondary_diagnoses && result.coding_result.secondary_diagnoses.length > 0 && (
                  <div>
                    <Text strong>其他诊断:</Text>
                    <List
                      size="small"
                      dataSource={result.coding_result.secondary_diagnoses}
                      renderItem={(d: any) => (
                        <List.Item>
                          <Tag color="orange">{d.code}</Tag>
                          <Text>{d.name}</Text>
                        </List.Item>
                      )}
                    />
                  </div>
                )}

                {result.coding_result?.procedures && result.coding_result.procedures.length > 0 && (
                  <div>
                    <Text strong>手术操作:</Text>
                    <List
                      size="small"
                      dataSource={result.coding_result.procedures}
                      renderItem={(p: any) => (
                        <List.Item>
                          <Tag color="purple">{p.code}</Tag>
                          <Text>{p.name}</Text>
                        </List.Item>
                      )}
                    />
                  </div>
                )}
              </Space>
            )}
          </Card>
        )}
      </Space>
    </Card>
  )
}

export default DocUploadCoder