import { useState, useCallback } from 'react'
import {
  Card, Row, Col, Input, Button, Select, Space, Tag, Table, Descriptions, Statistic,
  Divider, Typography, message, Spin, Upload, Modal, List, Tooltip, Empty,
} from 'antd'
import {
  ThunderboltOutlined, UploadOutlined, SearchOutlined,
  FileTextOutlined, MedicineBoxOutlined, HistoryOutlined,
} from '@ant-design/icons'
import { codingAPI, pipelineAPI } from '../services/api'
import IcdCodingResult from '../components/IcdCodingResult'
import type { CodeItem, CodingResultData } from '../components/IcdCodingResult'

const { TextArea } = Input
const { Title, Text } = Typography

interface SearchResult {
  code: string; name: string; score: number
}

const RECORD_TYPE_OPTIONS = [
  { value: 'admission', label: '入院记录' },
  { value: 'course', label: '病程记录' },
  { value: 'surgery', label: '手术记录' },
  { value: 'discharge', label: '出院小结' },
  { value: 'consultation', label: '会诊记录' },
]

export default function CodingPage() {
  const [content, setContent] = useState('')
  const [recordType, setRecordType] = useState('discharge')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<(CodingResultData & { suggestions?: CodeItem[] }) | null>(null)

  // ICD search modal
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)

  // Recent coding history
  const [history, setHistory] = useState<{ time: string; text: string; codes: number }[]>([])

  const handleAutoCode = useCallback(async (text?: string) => {
    const input = text ?? content
    if (!input.trim()) { message.warning('请先输入病历内容'); return }
    setLoading(true)
    try {
      const { data } = await codingAPI.autoCode({
        record_id: Date.now(), record_type: recordType, content: input,
      })
      setResult(data)
      setHistory(prev => [{
        time: new Date().toLocaleTimeString(),
        text: input,
        codes: (data.primary_diagnosis ? 1 : 0) + (data.secondary_diagnoses?.length || 0) + (data.procedures?.length || 0),
      }, ...prev].slice(0, 10))
      message.success(`编码完成，共识别 ${(data.primary_diagnosis ? 1 : 0) + (data.secondary_diagnoses?.length || 0)} 个诊断 + ${data.procedures?.length || 0} 个手术`)
      pipelineAPI.save({
        content: input,
        record_type: recordType,
        coding_result: data,
        department: '智能编码',
      }).catch((e: any) => { console.warn('自动保存失败:', e?.response?.data || e?.message) })
    } catch {
      message.error('编码失败，请重试')
    } finally { setLoading(false) }
  }, [content, recordType])

  const handleSearch = useCallback(async () => {
    if (!searchKeyword.trim()) return
    setSearchLoading(true)
    try {
      const { data } = await codingAPI.searchICD(searchKeyword, 15)
      setSearchResults(data.results || [])
    } catch {
      message.error('检索失败')
    } finally { setSearchLoading(false) }
  }, [searchKeyword])

  const copyCode = useCallback((code: string) => {
    navigator.clipboard.writeText(code)
    message.success(`已复制 ${code}`)
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={3}><ThunderboltOutlined /> 智能编码工作台</Title>
          <Text type="secondary">输入病历文本，AI自动完成ICD-10诊断编码和ICD-9-CM-3手术操作编码</Text>
        </div>
        <Space>
          <Button icon={<SearchOutlined />} onClick={() => setSearchOpen(true)}>
            ICD编码检索
          </Button>
        </Space>
      </div>

      <Divider />

      <Row gutter={24}>
        {/* Left: Input */}
        <Col span={12}>
          <Card title={
            <Space><FileTextOutlined />病历输入</Space>
          } extra={
            <Upload accept=".txt,.docx,.pdf" showUploadList={false}
              customRequest={async ({ file }) => {
                if (file instanceof File) {
                  setLoading(true)
                  try {
                    const { data } = await codingAPI.uploadAndCode(file)
                    if (data.status === 'parsed') {
                      setContent(data.content || '')
                      message.success(`文件解析成功: ${data.filename} (${data.file_type}, ${data.text_length}字, ${data.diagnosis_count}诊断)`)
                    } else {
                      message.warning(data.status)
                    }
                  } catch { message.error('上传处理失败') }
                  finally { setLoading(false) }
                }
              }}
            >
              <Button icon={<UploadOutlined />}>上传DOCX/PDF/TXT</Button>
            </Upload>
          }>
            <TextArea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请粘贴住院病历内容（出院小结、入院记录、手术记录等）..."
              rows={16}
              style={{ fontFamily: 'monospace', fontSize: 13 }}
            />
            <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                <Select value={recordType} onChange={setRecordType} style={{ width: 140 }}
                  options={RECORD_TYPE_OPTIONS} />
                <Text type="secondary">{content.length} 字</Text>
              </Space>
              <Button type="primary" size="large" icon={<ThunderboltOutlined />}
                loading={loading} onClick={() => handleAutoCode()}
                style={{ minWidth: 160, height: 44 }}>
                AI智能编码
              </Button>
            </div>
          </Card>

          {/* Recent history */}
          {history.length > 0 && (
            <Card title={<Space><HistoryOutlined />最近编码记录</Space>} size="small" style={{ marginTop: 12 }}>
              <List size="small" dataSource={history.slice(0, 5)}
                renderItem={(item) => (
                  <List.Item style={{ cursor: 'pointer', padding: '4px 0' }}
                    onClick={() => { setContent(item.text); handleAutoCode(item.text) }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>{item.time}</Text>
                    <Text ellipsis style={{ flex: 1, marginLeft: 8, fontSize: 13 }}>{item.text}</Text>
                    <Tag>{item.codes}个编码</Tag>
                  </List.Item>
                )} />
            </Card>
          )}
        </Col>

        {/* Right: Results */}
        <Col span={12}>
          <Spin spinning={loading} tip="AI编码中...">
            <Card title={<Space><MedicineBoxOutlined />编码结果</Space>}
              extra={result ? <Tag color="blue">{result.processing_time_ms}ms</Tag> : null}>
              {result ? (
                <>
                  <Row gutter={16} style={{ marginBottom: 12 }}>
                    <Col span={8}>
                      <Statistic title="总体置信度"
                        value={result.total_confidence * 100}
                        suffix="%" precision={1}
                        valueStyle={{ color: result.total_confidence >= 0.85 ? '#3f8600' : '#fa8c16' }} />
                    </Col>
                    <Col span={8}>
                      <Statistic title="诊断编码"
                        value={(result.secondary_diagnoses?.length || 0) + (result.primary_diagnosis ? 1 : 0)} />
                    </Col>
                    <Col span={8}>
                      <Statistic title="手术编码" value={result.procedures?.length || 0} />
                    </Col>
                  </Row>

                  <IcdCodingResult result={result} />

                  {result.suggestions && result.suggestions.length > 0 && (
                    <>
                      <Divider orientation="left" plain style={{ margin: '8px 0', fontSize: 13 }}>AI编码建议</Divider>
                      <List size="small" dataSource={result.suggestions.slice(0, 5)}
                        renderItem={(s: CodeItem) => (
                          <List.Item>
                            <Space>
                              <Text code>{s.code}</Text>
                              <Text>{s.name}</Text>
                              <Tag>{s.category}</Tag>
                              <Tooltip title="采纳此编码">
                                <Button size="small" type="link">采纳</Button>
                              </Tooltip>
                            </Space>
                          </List.Item>
                        )} />
                    </>
                  )}
                </>
              ) : (
                <Empty
                  image={<ThunderboltOutlined style={{ fontSize: 56, color: '#d9d9d9' }} />}
                  description="输入病历内容，点击「AI智能编码」开始分析"
                  style={{ padding: '60px 0' }}
                />
              )}
            </Card>
          </Spin>
        </Col>
      </Row>

      {/* ICD Search Modal */}
      <Modal
        title="ICD编码检索"
        open={searchOpen}
        onCancel={() => setSearchOpen(false)}
        footer={null}
        width={600}
      >
        <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
          <Input
            placeholder="输入诊断/手术名称关键词..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onPressEnter={handleSearch}
          />
          <Button type="primary" icon={<SearchOutlined />}
            loading={searchLoading} onClick={handleSearch}>
            检索
          </Button>
        </Space.Compact>
        <Table
          dataSource={searchResults}
          rowKey="code"
          size="small"
          pagination={false}
          loading={searchLoading}
          locale={{ emptyText: '输入关键词开始检索ICD编码' }}
          columns={[
            {
              title: '编码', dataIndex: 'code', key: 'code', width: 120,
              render: (v: string) => <Text code>{v}</Text>,
            },
            { title: '名称', dataIndex: 'name', key: 'name' },
            {
              title: '匹配度', dataIndex: 'score', key: 'score', width: 90,
              render: (v: number) => (
                <Tag color={v >= 0.8 ? 'green' : v >= 0.6 ? 'orange' : 'default'}>
                  {(v * 100).toFixed(0)}%
                </Tag>
              ),
            },
            {
              title: '', key: 'action', width: 60,
              render: (_: any, r: SearchResult) => (
                <Button size="small" type="link" onClick={() => copyCode(r.code)}>复制</Button>
              ),
            },
          ]}
        />
      </Modal>
    </div>
  )
}
