import { useState, useCallback, useEffect, useRef } from 'react'
import {
  Card, Row, Col, Input, Button, Select, Segmented, Space, Tag, Table, Descriptions, Statistic,
  Divider, Typography, message, Spin, Upload, Modal, List, Tooltip, Empty, Steps,
} from 'antd'
import {
  ThunderboltOutlined, UploadOutlined, SearchOutlined,
  FileTextOutlined, MedicineBoxOutlined, HistoryOutlined,
  PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined,
  CheckCircleOutlined, LoadingOutlined,
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

const SAMPLE_CASES = [
  {
    name: '心内科 · 急性心肌梗死',
    content: `主诉：突发胸痛3小时。
现病史：患者于3小时前无明显诱因突发胸骨后压榨性疼痛，向左肩放射，伴大汗淋漓、恶心，休息后不缓解，来我院急诊。
既往史：高血压病史8年，最高180/100mmHg；2型糖尿病5年。否认肝炎结核史。
查体：T 36.5℃，P 96次/分，R 22次/分，BP 150/95mmHg。神清，双肺呼吸音清，心率96次/分，律齐，各瓣膜区未及病理性杂音。
辅助检查：急诊心电图示V1-V4导联ST段抬高0.3-0.5mV。肌钙蛋白I 3.2ng/mL（↑）。
初步诊断：冠状动脉粥样硬化性心脏病，急性ST段抬高型心肌梗死（前壁），高血压病3级（极高危），2型糖尿病。
治疗经过：行急诊经皮冠状动脉介入治疗（PCI），于前降支植入药物洗脱支架1枚。术后胸痛缓解，生命体征平稳。
出院诊断：急性ST段抬高型心肌梗死（前壁），冠状动脉支架植入术后，高血压病3级，2型糖尿病。`,
  },
  {
    name: '呼吸科 · COPD急性加重',
    content: `主诉：反复咳嗽咳痰伴气促3天，加重1天。
现病史：患者有慢性支气管炎病史10余年，每于冬春季发作。3天前受凉后出现咳嗽、咳黄色粘痰，伴胸闷气促，活动后加重。今晨出现发热，体温最高38.7℃。
既往史：慢性阻塞性肺疾病10年，长期吸入噻托溴铵。吸烟史40年，每日20支。
查体：T 38.3℃，P 102次/分，R 28次/分，BP 130/80mmHg。桶状胸，双肺可及散在哮鸣音，肺底湿啰音。
辅助检查：血常规WBC 13.2×10⁹/L，N% 85%。血气分析：pH 7.32，PaCO₂ 58mmHg，PaO₂ 62mmHg。胸部CT示双肺气肿征象，右下肺斑片状渗出影。
初步诊断：慢性阻塞性肺疾病伴急性加重，肺部感染，Ⅱ型呼吸衰竭，慢性肺源性心脏病（代偿期）。
治疗经过：给予抗感染、祛痰、支气管扩张剂雾化吸入及无创正压通气支持治疗。
出院诊断：慢性阻塞性肺疾病急性加重期，社区获得性肺炎，Ⅱ型呼吸衰竭，慢性肺源性心脏病。`,
  },
  {
    name: '骨科 · 股骨颈骨折',
    content: `主诉：摔伤后左髋疼痛、活动受限2天。
现病史：患者2天前在家中不慎滑倒，左髋着地，当即感左髋剧痛，不能站立行走。由家属送至我院急诊。
既往史：高血压病5年，口服硝苯地平控制可。否认糖尿病史。
查体：T 36.8℃，P 80次/分，R 18次/分，BP 140/85mmHg。左下肢外旋短缩畸形，左腹股沟区压痛（+），左髋关节活动受限，足背动脉搏动良好。
辅助检查：X线示左股骨颈骨折（Garden IV型），骨折端明显移位。骨密度检查示骨量减少（T值-2.1）。
初步诊断：左股骨颈骨折（Garden IV型），骨质疏松症，高血压病。
治疗经过：入院后完善检查，在腰硬联合麻醉下行左侧人工全髋关节置换术，手术顺利。术后预防性抗感染、抗凝及康复功能锻炼指导。
出院诊断：左股骨颈骨折，全髋关节置换术后，骨质疏松症，高血压病。`,
  },
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

  // Demo state
  const [demoMode, setDemoMode] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)
  const [fastMode, setFastMode] = useState(true)
  const [caseIdx, setCaseIdx] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const startTimeRef = useRef(0)
  const demoActiveRef = useRef(false)

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

  // Demo handlers
  const stopDemo = useCallback(() => {
    setDemoRunning(false)
    demoActiveRef.current = false
  }, [])

  const startDemo = useCallback(() => {
    setDemoMode(true)
    setResult(null)
    setElapsedTime(0)
    demoActiveRef.current = true

    const text = SAMPLE_CASES[caseIdx]?.content ?? ''
    setContent(text)
    startTimeRef.current = Date.now()

    setTimeout(() => {
      handleAutoCode(text)
    }, 100)
  }, [caseIdx, handleAutoCode])

  // Completion when result arrives in demo mode
  useEffect(() => {
    if (!demoActiveRef.current || !result) return
    demoActiveRef.current = false
    setDemoRunning(false)
    setElapsedTime(Date.now() - startTimeRef.current)
    message.success('智能编码演示完成')
  }, [result])

  // Cleanup on unmount
  useEffect(() => {
    return () => { demoActiveRef.current = false }
  }, [])

  return (
    <div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={3}><ThunderboltOutlined /> 智能编码工作台</Title>
          <Text type="secondary">输入病历文本，AI自动完成ICD-10诊断编码和ICD-9-CM-3手术操作编码</Text>
        </div>
        <Space direction="vertical" align="end" size={4}>
          {!demoMode ? (
            <Space>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={() => { setFastMode(true); startDemo(); }}
                style={{
                  background: 'linear-gradient(135deg, #6366f1, #0ea5e9)',
                  border: 'none', borderRadius: 8, fontWeight: 600,
                  boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                }}
              >
                快速演示
              </Button>
              <Button
                icon={<PlayCircleOutlined />}
                onClick={() => { setFastMode(false); startDemo(); }}
              >
                完整演示
              </Button>
              <Button icon={<SearchOutlined />} onClick={() => setSearchOpen(true)}>
                ICD编码检索
              </Button>
            </Space>
          ) : (
            <Space>
              <Select
                size="small"
                value={caseIdx}
                onChange={(v) => { setCaseIdx(v); stopDemo(); }}
                style={{ width: 180 }}
                options={SAMPLE_CASES.map((c, i) => ({ value: i, label: c.name }))}
              />
              {demoRunning ? (
                <Button size="small" icon={<PauseCircleOutlined />} onClick={stopDemo} danger>停止</Button>
              ) : (
                <Button size="small" icon={<ReloadOutlined />} onClick={startDemo}
                  style={{ background: 'linear-gradient(135deg, #6366f1, #0ea5e9)', border: 'none', color: '#fff' }}>
                  重新演示
                </Button>
              )}
              <Button size="small" onClick={() => { setDemoMode(false); stopDemo(); setContent(''); setResult(null); }}>
                退出
              </Button>
            </Space>
          )}
          {demoMode && (
            <Space size={4}>
              {fastMode && <Tag color="orange" icon={<ThunderboltOutlined />}>快速模式</Tag>}
              <Tag
                color={loading ? 'processing' : elapsedTime > 0 ? 'success' : 'default'}
                icon={loading ? <LoadingOutlined /> : elapsedTime > 0 ? <CheckCircleOutlined /> : undefined}
              >
                {loading ? '分析中...' : elapsedTime > 0 ? `完成 (${(elapsedTime / 1000).toFixed(1)}s)` : '准备就绪'}
              </Tag>
            </Space>
          )}
        </Space>
      </div>

      <Divider />

      {/* Pipeline Steps */}
      <Card style={{ marginBottom: 16 }}>
        <Steps
          current={result ? 1 : 0}
          status={loading ? 'process' : result ? 'finish' : 'wait'}
          items={[
            { title: '智能编码', description: 'NLP识别 + ICD编码', icon: result ? <CheckCircleOutlined /> : <FileTextOutlined /> },
          ]}
        />
      </Card>

      {/* Input Area */}
      <Card
        title={<Space><FileTextOutlined />病历输入</Space>}
        extra={
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
            <Button icon={<UploadOutlined />} disabled={demoMode}>上传DOCX/PDF/TXT</Button>
          </Upload>
        }
        style={{ marginBottom: 16 }}
        className={loading ? 'pipeline-card-processing' : ''}
      >
        <TextArea
          value={content}
          onChange={(e) => { if (!demoMode) setContent(e.target.value) }}
          placeholder={demoMode ? '演示模式：AI将自动分析病历内容...' : '请粘贴住院病历内容（出院小结、入院记录、手术记录等）...'}
          rows={10}
          readOnly={demoMode}
          style={{ fontFamily: 'monospace', fontSize: 13 }}
        />
        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Select value={recordType} onChange={setRecordType} style={{ width: 140 }}
              options={RECORD_TYPE_OPTIONS} disabled={demoMode} />
            <Text type="secondary">{content.length} 字</Text>
          </Space>
          <Button type="primary" size="large" icon={<ThunderboltOutlined />}
            loading={loading} onClick={() => handleAutoCode()}
            disabled={demoMode}
            style={{ minWidth: 160, height: 44 }}>
            AI智能编码
          </Button>
        </div>
      </Card>

      {/* Recent history */}
      {history.length > 0 && !demoMode && (
        <Card title={<Space><HistoryOutlined />最近编码记录</Space>} size="small" style={{ marginBottom: 16 }}>
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

      {/* Result */}
      <Spin spinning={loading} tip="AI编码中...">
        {result && (
          <Card
            title={<Space><MedicineBoxOutlined style={{ color: '#1677ff' }} />智能编码结果</Space>}
            extra={
              <Space>
                <Tag color="blue">{result.processing_time_ms}ms</Tag>
                <Text type="secondary">
                  总体置信度: <Text strong>{(result.total_confidence * 100).toFixed(0)}%</Text>
                </Text>
              </Space>
            }
            className="pipeline-card-complete"
          >
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
          </Card>
        )}

        {/* Empty state */}
        {!result && !loading && !demoMode && (
          <Card style={{ marginTop: 16 }}>
            <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
              <ThunderboltOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block' }} />
              <Text type="secondary" style={{ fontSize: 16 }}>
                粘贴病历内容，点击「AI智能编码」开始分析
              </Text>
            </div>
          </Card>
        )}

        {/* Demo empty state */}
        {!result && !loading && demoMode && (
          <Card style={{ marginTop: 16 }}>
            <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
              <ThunderboltOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block', color: '#0ea5e9' }} />
              <Text type="secondary" style={{ fontSize: 16 }}>
                点击「重新演示」开始智能编码演示
              </Text>
            </div>
          </Card>
        )}
      </Spin>

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
