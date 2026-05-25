import { Card, Row, Col, Table, Descriptions, Tag, Typography, Space, Divider, Tooltip } from 'antd'
import { CheckCircleOutlined, CopyOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Text } = Typography

export interface CodeItem {
  code: string; name: string; category?: string; is_primary?: boolean; confidence?: number
}

export interface CodingResultData {
  primary_diagnosis: CodeItem | null
  secondary_diagnoses: CodeItem[]
  procedures: CodeItem[]
  total_confidence: number
  processing_time_ms: number
}

const columns: ColumnsType<CodeItem> = [
  {
    title: '编码', dataIndex: 'code', key: 'code', width: 110,
    render: (v: string) => (
      <Space size={4}>
        <Text code style={{ fontSize: 12 }}>{v}</Text>
        <CopyOutlined style={{ cursor: 'pointer', fontSize: 11, color: '#999' }}
          onClick={() => { navigator.clipboard.writeText(v) }} aria-label={`复制编码 ${v}`} role="button" tabIndex={0} />
      </Space>
    ),
  },
  { title: '名称', dataIndex: 'name', key: 'name' },
  {
    title: '置信度', dataIndex: 'confidence', key: 'confidence', width: 80,
    render: (v: number | undefined) => {
      if (v === undefined) return null
      return (
        <Tag color={v >= 0.9 ? 'green' : v >= 0.7 ? 'orange' : 'red'}>
          {(v * 100).toFixed(0)}%
        </Tag>
      )
    },
  },
]

interface Props {
  result: CodingResultData
  /** Extra content in card header */
  headerExtra?: React.ReactNode
  /** Highlight color for primary diagnosis section */
  highlightColor?: string
}

export default function IcdCodingResult({ result, headerExtra, highlightColor = '#52c41a' }: Props) {
  return (
    <>
      {/* Primary diagnosis */}
      <div style={{ background: '#f6ffed', padding: '8px 12px', borderRadius: 8, marginBottom: 12 }}>
        <Space>
          <CheckCircleOutlined style={{ color: highlightColor }} />
          <Text strong>主要诊断</Text>
        </Space>
        {result.primary_diagnosis ? (
          <Descriptions column={2} size="small" style={{ marginTop: 8 }}>
            <Descriptions.Item label="编码">
              <Text code style={{ fontSize: 14 }}>{result.primary_diagnosis.code}</Text>
              <CopyOutlined style={{ marginLeft: 6, cursor: 'pointer', fontSize: 11 }}
                onClick={() => navigator.clipboard.writeText(result.primary_diagnosis!.code)}
                aria-label={`复制编码 ${result.primary_diagnosis!.code}`} role="button" tabIndex={0} />
            </Descriptions.Item>
            <Descriptions.Item label="名称">{result.primary_diagnosis.name}</Descriptions.Item>
          </Descriptions>
        ) : (
          <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>未识别到主要诊断</Text>
        )}
      </div>

      {/* Secondary diagnoses */}
      <Divider orientation="left" plain style={{ margin: '8px 0', fontSize: 13 }}>
        其他诊断 ({result.secondary_diagnoses?.length || 0})
      </Divider>
      {result.secondary_diagnoses?.length > 0 ? (
        <Table columns={columns} dataSource={result.secondary_diagnoses}
          rowKey="code" size="small" pagination={false} style={{ marginBottom: 8 }} />
      ) : (
        <Text type="secondary" style={{ fontSize: 12 }}>无</Text>
      )}

      {/* Procedures */}
      <Divider orientation="left" plain style={{ margin: '8px 0', fontSize: 13 }}>
        手术操作 ({result.procedures?.length || 0})
      </Divider>
      {result.procedures?.length > 0 ? (
        <Table columns={columns} dataSource={result.procedures}
          rowKey="code" size="small" pagination={false} style={{ marginBottom: 8 }} />
      ) : (
        <Text type="secondary" style={{ fontSize: 12 }}>无</Text>
      )}
    </>
  )
}
