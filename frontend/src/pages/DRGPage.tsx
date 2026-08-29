import { useState, useCallback, useEffect, useRef } from 'react'
import { Card, Row, Col, Descriptions, Statistic, Tag, Divider, Typography, Button, Space, Input, InputNumber, Select, message, Steps } from 'antd'
import {
  MedicineBoxOutlined, CalculatorOutlined, ThunderboltOutlined,
  PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined,
  CheckCircleOutlined, LoadingOutlined, FileTextOutlined,
} from '@ant-design/icons'
import { drgAPI, pipelineAPI } from '../services/api'
import DRGCompare from '../components/x_features/DRGCompare'

const { Title, Text } = Typography

interface DRGResult {
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

const SAMPLE_CASES = [
  {
    name: '高血压 + 糖尿病 + PCI术后',
    primary: 'I10.x00',
    secondary: 'E11.900, N18.3',
    procedures: '36.0700',
    age: 65,
    gender: 'male' as const,
    days: 10,
  },
  {
    name: 'COPD + 肺炎 + 呼衰',
    primary: 'J44.100',
    secondary: 'J15.902, J96.000',
    procedures: '93.9600',
    age: 72,
    gender: 'male' as const,
    days: 14,
  },
  {
    name: '股骨颈骨折 + 髋关节置换',
    primary: 'S72.000',
    secondary: 'M81.099, I10.x00',
    procedures: '81.5100',
    age: 78,
    gender: 'female' as const,
    days: 21,
  },
]

export default function DRGPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DRGResult | null>(null)
  const [primaryCode, setPrimaryCode] = useState('')
  const [secondaryCodes, setSecondaryCodes] = useState('')
  const [procedureCodes, setProcedureCodes] = useState('')
  const [age, setAge] = useState<number | null>(null)
  const [gender, setGender] = useState<'male' | 'female'>('male')
  const [daysOfStay, setDaysOfStay] = useState<number | null>(null)
  const [dischargeType, setDischargeType] = useState('1')

  // Demo state
  const [demoMode, setDemoMode] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)
  const [fastMode, setFastMode] = useState(true)
  const [caseIdx, setCaseIdx] = useState(0)
  const [elapsedTime, setElapsedTime] = useState(0)
  const startTimeRef = useRef(0)
  const demoActiveRef = useRef(false)

  const handleGroup = async () => {
    setLoading(true)
    try {
      const secCodes = secondaryCodes
        .split(/[,，\s]+/)
        .map(s => s.trim())
        .filter(Boolean)
      const procCodes = procedureCodes
        .split(/[,，\s]+/)
        .map(s => s.trim())
        .filter(Boolean)

      const { data } = await drgAPI.group({
        patient_age: age ?? 50,
        patient_gender: gender,
        primary_diagnosis_code: primaryCode.trim(),
        secondary_diagnosis_codes: secCodes,
        procedure_codes: procCodes,
        discharge_type: dischargeType,
        days_of_stay: daysOfStay ?? 0,
      })
      setResult(data)
      message.success('DRG分组完成')
      pipelineAPI.save({
        record_type: 'discharge',
        drg_result: data,
        department: 'DRG分组',
        patient_info: { age: age ?? undefined, gender },
        primary_diagnosis_code: primaryCode.trim(),
        secondary_diagnosis_codes: secCodes,
        procedure_codes: procCodes,
      }).catch((e: unknown) => { console.warn('自动保存失败:', e instanceof Error ? e.message : '未知错误') })
    } catch {
      message.error('分组失败，请检查编码格式')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => {
    setPrimaryCode('I10.x00')
    setSecondaryCodes('E11.900, N18.3')
    setProcedureCodes('36.0700')
    setAge(65)
    setGender('male')
    setDaysOfStay(10)
  }

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

    const c = SAMPLE_CASES[caseIdx]
    setPrimaryCode(c.primary)
    setSecondaryCodes(c.secondary)
    setProcedureCodes(c.procedures)
    setAge(c.age)
    setGender(c.gender)
    setDaysOfStay(c.days)
    startTimeRef.current = Date.now()

    // Auto-trigger grouping
    setTimeout(async () => {
      setLoading(true)
      try {
        const secCodes = c.secondary
          .split(/[,，\s]+/)
          .map(s => s.trim())
          .filter(Boolean)
        const procCodes = c.procedures
          .split(/[,，\s]+/)
          .map(s => s.trim())
          .filter(Boolean)

        const { data } = await drgAPI.group({
          patient_age: c.age,
          patient_gender: c.gender,
          primary_diagnosis_code: c.primary.trim(),
          secondary_diagnosis_codes: secCodes,
          procedure_codes: procCodes,
          discharge_type: dischargeType,
          days_of_stay: c.days,
        })
        setResult(data)
        pipelineAPI.save({
          record_type: 'discharge',
          drg_result: data,
          department: 'DRG分组',
          patient_info: { age: c.age, gender: c.gender },
          primary_diagnosis_code: c.primary,
          secondary_diagnosis_codes: secCodes,
          procedure_codes: procCodes,
        }).catch((e: unknown) => { console.warn('自动保存失败:', e instanceof Error ? e.message : '未知错误') })
      } catch {
        message.error('分组失败，请检查编码格式')
      } finally {
        setLoading(false)
      }
    }, 200)
  }, [caseIdx, dischargeType])

  // Celebration when result arrives in demo mode
  useEffect(() => {
    if (!demoActiveRef.current || !result) return
    demoActiveRef.current = false
    setDemoRunning(false)
    setElapsedTime(Date.now() - startTimeRef.current)
  }, [result])

  useEffect(() => {
    return () => { demoActiveRef.current = false }
  }, [])

  return (
    <div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={3}><MedicineBoxOutlined /> DRG分组查询</Title>
          <Text type="secondary">基于CHS-DRG 1.2版分组方案，输入ICD编码自动判定DRG分组</Text>
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
              <Button icon={<PlayCircleOutlined />} onClick={() => { setFastMode(false); startDemo(); }}>
                完整演示
              </Button>
            </Space>
          ) : (
            <Space>
              <Select
                size="small"
                value={caseIdx}
                onChange={(v) => { setCaseIdx(v); stopDemo(); }}
                style={{ width: 200 }}
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
              <Button size="small" onClick={() => { setDemoMode(false); stopDemo(); setResult(null); }}>
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
                {loading ? '分组中...' : elapsedTime > 0 ? `完成 (${(elapsedTime / 1000).toFixed(1)}s)` : '准备就绪'}
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
            { title: 'DRG分组', description: 'CHS-DRG 1.2分组', icon: result ? <CheckCircleOutlined /> : <MedicineBoxOutlined /> },
          ]}
        />
      </Card>

      {/* Input Area */}
      <Card
        title={<Space><FileTextOutlined />分组参数</Space>}
        extra={
          !demoMode ? (
            <Button size="small" icon={<ThunderboltOutlined />} onClick={fillDemo}>加载演示数据</Button>
          ) : null
        }
        style={{ marginBottom: 16 }}
        className={loading ? 'pipeline-card-processing' : ''}
      >
        <Row gutter={[16, 12]}>
          <Col span={8}>
            <Text strong>主要诊断编码</Text>
            <Input value={primaryCode} onChange={(e) => setPrimaryCode(e.target.value)} placeholder="如 I10.x00" aria-label="主要诊断编码" />
          </Col>
          <Col span={8}>
            <Text strong>次要诊断编码（逗号分隔）</Text>
            <Input value={secondaryCodes} onChange={(e) => setSecondaryCodes(e.target.value)} placeholder="如 E11.900, N18.3" aria-label="次要诊断编码" />
          </Col>
          <Col span={8}>
            <Text strong>手术操作编码（逗号分隔）</Text>
            <Input value={procedureCodes} onChange={(e) => setProcedureCodes(e.target.value)} placeholder="如 36.0700" aria-label="手术操作编码" />
          </Col>
        </Row>
        <Row gutter={12} style={{ marginTop: 12 }}>
          <Col span={6}>
            <Text strong>年龄</Text>
            <InputNumber min={0} max={120} value={age} onChange={(v) => setAge(v ?? 65)} style={{ width: '100%' }} aria-label="患者年龄" />
          </Col>
          <Col span={6}>
            <Text strong>性别</Text>
            <Select value={gender} onChange={setGender} style={{ width: '100%' }} aria-label="患者性别">
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
            </Select>
          </Col>
          <Col span={6}>
            <Text strong>住院天数</Text>
            <InputNumber min={1} max={365} value={daysOfStay} onChange={(v) => setDaysOfStay(v ?? 1)} style={{ width: '100%' }} aria-label="住院天数" />
          </Col>
          <Col span={6}>
            <Text strong>离院方式</Text>
            <Select value={dischargeType} onChange={setDischargeType} style={{ width: '100%' }}>
              <Select.Option value="1">医嘱离院</Select.Option>
              <Select.Option value="2">医嘱转院</Select.Option>
              <Select.Option value="5">死亡</Select.Option>
              <Select.Option value="9">其他</Select.Option>
            </Select>
          </Col>
        </Row>
        <div style={{ marginTop: 16 }}>
          <Button type="primary" size="large" icon={<CalculatorOutlined />} loading={loading}
            onClick={handleGroup} disabled={demoMode} style={{ minWidth: 200, height: 44 }}>
            执行DRG分组
          </Button>
        </div>
      </Card>

      {/* Result */}
      {result && (
        <Card
          title={<Space><MedicineBoxOutlined style={{ color: '#722ed1' }} />DRG分组结果</Space>}
          extra={
            <Tag color={result.is_surgical ? 'blue' : 'green'}>
              {result.is_surgical ? '手术组' : '非手术组'}
            </Tag>
          }
          className="pipeline-card-complete"
        >
          <Row gutter={16}>
            <Col span={6}><Statistic title="DRG编码" value={result.drg_code || '-'} valueStyle={{ color: '#722ed1' }} /></Col>
            <Col span={6}><Statistic title="权重(RW)" value={result.weight} precision={3} /></Col>
            <Col span={6}><Statistic title="费率" value={result.rate} prefix="¥" precision={2} /></Col>
            <Col span={6}>
              <Statistic title="预估支付"
                value={result.estimated_payment} prefix="¥" precision={2}
                valueStyle={{ color: '#3f8600' }} />
            </Col>
          </Row>

          <Divider />

          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="MDC大类">{result.mdc} - {result.mdc_name}</Descriptions.Item>
            <Descriptions.Item label="ADRG">{result.adrg || '待确定'}</Descriptions.Item>
            <Descriptions.Item label="DRG名称">{result.drg_name}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag color={result.is_surgical ? 'blue' : 'green'}>
                {result.is_surgical ? '手术组' : '非手术组'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="合并症/并发症">
              <Tag color={result.cc_flag === 'MCC' ? 'red' : result.cc_flag === 'CC' ? 'orange' : 'default'}>
                {result.cc_flag || '无'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="病例复杂度">{result.patient_complexity || '常规'}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* Empty state */}
      {!result && !loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
            <MedicineBoxOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block' }} />
            <Text type="secondary" style={{ fontSize: 16 }}>
              输入诊断和手术编码，点击「执行DRG分组」开始分析
            </Text>
          </div>
        </Card>
      )}

      {/* X 功能迷你版 C: AI vs 人工 DRG 对比 */}
      <DRGCompare defaultRecordId={1} />
    </div>
  )
}
