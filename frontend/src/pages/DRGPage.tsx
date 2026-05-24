import { useState } from 'react'
import { Card, Row, Col, Descriptions, Statistic, Tag, Divider, Typography, Button, Space, Input, InputNumber, Select, message } from 'antd'
import { MedicineBoxOutlined, CalculatorOutlined } from '@ant-design/icons'
import { drgAPI } from '../services/api'

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

export default function DRGPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DRGResult | null>(null)
  const [primaryCode, setPrimaryCode] = useState('I10.x00')
  const [secondaryCodes, setSecondaryCodes] = useState('E11.900, N18.3')
  const [procedureCodes, setProcedureCodes] = useState('')
  const [age, setAge] = useState(65)
  const [gender, setGender] = useState<'male' | 'female'>('male')
  const [daysOfStay, setDaysOfStay] = useState(10)
  const [dischargeType, setDischargeType] = useState('1')

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
        patient_age: age,
        patient_gender: gender,
        primary_diagnosis_code: primaryCode.trim(),
        secondary_diagnosis_codes: secCodes,
        procedure_codes: procCodes,
        discharge_type: dischargeType,
        days_of_stay: daysOfStay,
      })
      setResult(data)
      message.success('DRG分组完成')
    } catch {
      message.error('分组失败，请检查编码格式')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={3}><MedicineBoxOutlined /> DRG分组查询</Title>
      <Text type="secondary">基于CHS-DRG 1.2版分组方案，输入ICD编码自动判定DRG分组</Text>

      <Divider />

      <Row gutter={24}>
        <Col span={10}>
          <Card title="分组参数">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>主要诊断编码</Text>
                <Input
                  value={primaryCode}
                  onChange={(e) => setPrimaryCode(e.target.value)}
                  placeholder="如 I10.x00"
                />
              </div>
              <div>
                <Text strong>次要诊断编码（逗号分隔）</Text>
                <Input
                  value={secondaryCodes}
                  onChange={(e) => setSecondaryCodes(e.target.value)}
                  placeholder="如 E11.900, N18.3"
                />
              </div>
              <div>
                <Text strong>手术操作编码（逗号分隔）</Text>
                <Input
                  value={procedureCodes}
                  onChange={(e) => setProcedureCodes(e.target.value)}
                  placeholder="如 36.0700"
                />
              </div>
              <Row gutter={12}>
                <Col span={8}>
                  <Text strong>年龄</Text>
                  <InputNumber min={0} max={120} value={age}
                    onChange={(v) => setAge(v ?? 65)} style={{ width: '100%' }} />
                </Col>
                <Col span={8}>
                  <Text strong>性别</Text>
                  <Select value={gender} onChange={setGender} style={{ width: '100%' }}>
                    <Select.Option value="male">男</Select.Option>
                    <Select.Option value="female">女</Select.Option>
                  </Select>
                </Col>
                <Col span={8}>
                  <Text strong>住院天数</Text>
                  <InputNumber min={1} max={365} value={daysOfStay}
                    onChange={(v) => setDaysOfStay(v ?? 1)} style={{ width: '100%' }} />
                </Col>
              </Row>
              <Row gutter={12}>
                <Col span={12}>
                  <Text strong>离院方式</Text>
                  <Select value={dischargeType} onChange={setDischargeType} style={{ width: '100%' }}>
                    <Select.Option value="1">医嘱离院</Select.Option>
                    <Select.Option value="2">医嘱转院</Select.Option>
                    <Select.Option value="5">死亡</Select.Option>
                    <Select.Option value="9">其他</Select.Option>
                  </Select>
                </Col>
              </Row>
              <Button type="primary" icon={<CalculatorOutlined />} loading={loading}
                block onClick={handleGroup}>
                执行DRG分组
              </Button>
            </Space>
          </Card>
        </Col>

        <Col span={14}>
          <Card title="分组结果">
            {result ? (
              <>
                <Row gutter={16}>
                  <Col span={6}><Statistic title="DRG编码" value={result.drg_code || '-'} /></Col>
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
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: 80, color: '#ccc' }}>
                <MedicineBoxOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>输入诊断和手术编码，点击"执行DRG分组"</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
