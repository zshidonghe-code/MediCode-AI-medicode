import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card, Row, Col, Input, Button, Select, Tag, Table, Statistic, Typography,
  Divider, Space, message, Spin, Steps, Progress, Descriptions, Upload,
  Segmented, InputNumber
} from 'antd'
import {
  ThunderboltOutlined, UploadOutlined, SafetyCertificateOutlined,
  MedicineBoxOutlined, DollarOutlined, FileTextOutlined,
  CheckCircleOutlined, LoadingOutlined, PlayCircleOutlined,
  PauseCircleOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { codingAPI, qcAPI, drgAPI, pipelineAPI, rejectionAPI } from '../services/api'
import IcdCodingResult from '../components/IcdCodingResult'
import type { CodeItem, CodingResultData } from '../components/IcdCodingResult'
import PipelineRejectionRedirect from '../components/x_features/PipelineRejectionRedirect'
import type { RejectionAssessRequest, RejectionResultData } from '../types/api'

const { TextArea } = Input
const { Title, Text } = Typography

// ─── Sample Cases ───────────────────────────────────────────────────────────

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
  {
    name: '⭐ 边界病例 · 腹痛待查（AI不确定）',
    content: `主诉：反复上腹部隐痛不适2月，加重伴嗳气3天。
现病史：患者2月来无明显诱因反复出现上腹部隐痛，进食后加重。近3天疼痛加重，伴嗳气反酸。自服"斯达舒"效果不佳。
既往史：高血压病3年。否认糖尿病史。吸烟20年，每日半包。
查体：T 36.4℃，P 76次/分，BP 142/86mmHg。腹软，上腹部轻压痛，Murphy征阴性，麦氏点无压痛。
辅助检查：胃镜示慢性浅表性胃炎伴糜烂，Hp(+)。幽门螺杆菌呼气试验阳性。
初步诊断：慢性浅表性胃炎，幽门螺杆菌感染，高血压病。
治疗经过：予四联疗法根除Hp（阿莫西林+克拉霉素+奥美拉唑+枸橼酸铋钾），抑酸护胃等对症治疗。
出院诊断：慢性浅表性胃炎，幽门螺杆菌感染，高血压病1级。`,
  },
]

const SPEED_MAP: Record<string, number> = { fast: 12, normal: 28, slow: 55 }

// ─── Types ──────────────────────────────────────────────────────────────────

interface QCIssue {
  rule_id: string; rule_name: string; rule_type: string; severity: string
  line_snippet: string; suggestion: string; line_number: number | null; id?: number
}

interface DRGResult {
  mdc: string; mdc_name: string; adrg: string; adrg_name: string
  drg_code: string; drg_name: string; is_surgical: boolean
  weight: number; rate: number; estimated_payment: number
  cc_flag: string; patient_complexity: string
  avg_days?: number
}

const severityColor: Record<string, string> = {
  critical: 'red', major: 'orange', minor: 'gold', info: 'blue',
}

// ─── PipelinePage ───────────────────────────────────────────────────────────

export default function PipelinePage() {
  // Core state
  const [content, setContent] = useState('')
  const [currentStep, setCurrentStep] = useState(-1)
  const [loading, setLoading] = useState(false)

  const [codingResult, setCodingResult] = useState<CodingResultData | null>(null)

  const [qcResult, setQcResult] = useState<{
    total_issues: number; critical_count: number; major_count: number
    minor_count: number; info_count: number; issues: QCIssue[]; qc_score: number
  } | null>(null)

  const [drgResult, setDrgResult] = useState<DRGResult | null>(null)
  const [rejectionResult, setRejectionResult] = useState<RejectionResultData | null>(null)
  const [rejectionContext, setRejectionContext] = useState<RejectionAssessRequest | null>(null)

  // Persisted QC result IDs for accept/reject
  const [qcResultIds, setQcResultIds] = useState<{ id: number; severity: string }[]>([])

  // Demo state
  const [demoMode, setDemoMode] = useState(false)
  const [demoRunning, setDemoRunning] = useState(false)
  const [caseIdx, setCaseIdx] = useState(0)
  const [demoSpeed, setDemoSpeed] = useState<string>('fast')
  const [fastMode, setFastMode] = useState(true)  // 快速模式：跳过打字机，1秒出结果
  const [typingDone, setTypingDone] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [patientAge, setPatientAge] = useState<number | null>(null)
  const [patientGender, setPatientGender] = useState<string>('male')
  const [daysOfStay, setDaysOfStay] = useState<number | null>(null)
  const typewriterRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef(0)

  // ─── Pipeline execution ─────────────────────────────────────────────────

  const handleStart = useCallback(async (overrideContent?: string) => {
    const text = overrideContent ?? content
    if (!text.trim()) { message.warning('请先输入病历内容'); return }

    setLoading(true)
    setCurrentStep(0)
    setCodingResult(null)
    setQcResult(null)
    setDrgResult(null)
    setRejectionResult(null)
    setRejectionContext(null)
    startTimeRef.current = Date.now()
    setElapsedTime(0)

    try {
      // Step 1: NLP + ICD Coding
      setCurrentStep(0)
      const { data: coding } = await codingAPI.autoCode({
        record_id: Date.now(), record_type: 'discharge', content: text,
      })
      setCodingResult(coding)

      // Step 2: QC Quality Check
      setCurrentStep(1)
      const { data: qc } = await qcAPI.check({
        record_id: Date.now(), record_type: 'discharge', content: text,
        coding_result: coding,
      })
      setQcResult(qc)

      // Step 3: DRG Grouping
      setCurrentStep(2)
      const primaryCode = coding.primary_diagnosis?.code || 'R69.900'
      const secCodes = (coding.secondary_diagnoses || []).map((d: CodeItem) => d.code)
      const procCodes = (coding.procedures || []).map((p: CodeItem) => p.code)

      const { data: drg } = await drgAPI.group({
        patient_age: patientAge ?? undefined,
        patient_gender: patientGender,
        primary_diagnosis_code: primaryCode,
        secondary_diagnosis_codes: secCodes,
        procedure_codes: procCodes,
        discharge_type: '1',
        days_of_stay: daysOfStay ?? undefined,
      })
      setDrgResult(drg)

      // Step 4: Rejection Risk Assessment
      setCurrentStep(3)
      try {
        const priDiag = coding.primary_diagnosis
        const rejectionRequest: RejectionAssessRequest = {
          primary_diagnosis: priDiag ? { code: priDiag.code, name: priDiag.name } : null,
          secondary_diagnoses: (coding.secondary_diagnoses || []).map((d: CodeItem) => ({ code: d.code, name: d.name })),
          procedures: (coding.procedures || []).map((p: CodeItem) => ({ code: p.code, name: p.name })),
          drg_result: {
            drg_code: drg.drg_code ?? '',
            drg_name: drg.drg_name ?? '',
            weight: drg.weight ?? 1,
            avg_los: drg.avg_days ?? 7,
          },
          patient_info: {
            age: patientAge ?? 0,
            gender: patientGender ?? '',
            days_of_stay: daysOfStay ?? 0,
          },
          content: text,
          hospital_cost: 0,
        }
        setRejectionContext(rejectionRequest)
        const { data: rejection } = await rejectionAPI.assess(rejectionRequest)
        setRejectionResult(rejection)
      } catch { /* rejection is optional, don't block */ }

      // Done
      setCurrentStep(4)
      if (startTimeRef.current) {
        setElapsedTime(Date.now() - startTimeRef.current)
      }

      // Auto-save pipeline results to database
      try {
        const { data: saved } = await pipelineAPI.save({
          content: text,
          record_type: 'discharge',
          coding_result: coding,
          qc_result: qc,
          drg_result: drg,
        })
        setQcResultIds(saved.qc_result_ids || [])
      } catch (e: unknown) {
        console.warn('自动保存失败:', e instanceof Error ? e.message : '未知错误')
      }

      if (!demoRunning) message.success('全流程分析完成')
    } catch {
      message.error('分析失败，请重试')
    } finally {
      setLoading(false)
    }
  }, [content, demoRunning, patientAge, patientGender, daysOfStay])

  // ─── Demo mode: typewriter effect ──────────────────────────────────────

  const stopDemo = useCallback(() => {
    if (typewriterRef.current) {
      clearInterval(typewriterRef.current)
      typewriterRef.current = null
    }
    setDemoRunning(false)
    setTypingDone(false)
  }, [])

  const startDemo = useCallback(() => {
    setDemoMode(true)
    setCodingResult(null)
    setQcResult(null)
    setDrgResult(null)
    setRejectionResult(null)
    setRejectionContext(null)
    setCurrentStep(-1)
    setElapsedTime(0)

    if (fastMode) {
      // 快速模式：直接粘贴全文，立即开始分析
      const text = SAMPLE_CASES[caseIdx]?.content ?? ''
      setContent(text)
      setTypingDone(true)
      setDemoRunning(false)
      // 短暂延迟让UI刷新后自动触发
      setTimeout(() => {
        handleStart(text)
      }, 100)
    } else {
      // 传统打字机模式
      setDemoRunning(true)
      setTypingDone(false)
    }
  }, [fastMode, caseIdx, handleStart])

  // Typewriter
  useEffect(() => {
    if (!demoRunning) return

    const text = SAMPLE_CASES[caseIdx]?.content ?? ''
    setContent('')
    let i = 0
    const speed = SPEED_MAP[demoSpeed] ?? 28

    typewriterRef.current = setInterval(() => {
      i++
      setContent(text.slice(0, i))
      if (i >= text.length) {
        if (typewriterRef.current) clearInterval(typewriterRef.current)
        typewriterRef.current = null
        setTypingDone(true)
      }
    }, speed)

    return () => {
      if (typewriterRef.current) clearInterval(typewriterRef.current)
    }
  }, [demoRunning, caseIdx, demoSpeed])

  // Auto-start pipeline when typewriter finishes
  useEffect(() => {
    if (!typingDone || !demoRunning) return
    const text = SAMPLE_CASES[caseIdx]?.content ?? ''
    const timeout = setTimeout(() => {
      handleStart(text)
    }, 500)
    return () => clearTimeout(timeout)
  }, [typingDone, demoRunning, caseIdx, handleStart])

  const demoRunningRef = useRef(demoRunning)
  demoRunningRef.current = demoRunning

  // Completion message when DRG result arrives in demo mode
  useEffect(() => {
    if (!demoRunningRef.current || !drgResult) return
    setDemoRunning(false)
    message.success('全流程分析完成')
  }, [drgResult])

  // ─── Static data ────────────────────────────────────────────────────────

  const stepItems = [
    { title: '智能编码', icon: <FileTextOutlined />, desc: 'NLP识别 + ICD编码' },
    { title: '质控检查', icon: <SafetyCertificateOutlined />, desc: '完整性 + 逻辑校验' },
    { title: 'DRG分组', icon: <MedicineBoxOutlined />, desc: 'CHS-DRG 1.2分组' },
    { title: '费用预估', icon: <DollarOutlined />, desc: '医保支付测算' },
    { title: '拒付预测', icon: <ThunderboltOutlined />, desc: '医保审核风险扫描' },
  ]

  // ─── Render ─────────────────────────────────────────────────────────────

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={3}><ThunderboltOutlined /> 智能编码流水线</Title>
          <Text type="secondary">一站式病历智能分析 — NLP编码 → 质控校验 → DRG分组 → 费用测算，全流程可视化</Text>
        </div>

        {/* Demo mode controls */}
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
              {!fastMode && (
                <Segmented
                  size="small"
                  value={demoSpeed}
                  onChange={(v) => setDemoSpeed(v as string)}
                  options={[
                    { value: 'fast', label: '快' },
                    { value: 'normal', label: '中' },
                    { value: 'slow', label: '慢' },
                  ]}
                />
              )}
              {demoRunning ? (
                <Button
                  size="small" icon={<PauseCircleOutlined />}
                  onClick={stopDemo} danger
                >
                  停止
                </Button>
              ) : (
                <Button
                  size="small" icon={<ReloadOutlined />}
                  onClick={startDemo}
                  style={{ background: 'linear-gradient(135deg, #6366f1, #0ea5e9)', border: 'none', color: '#fff' }}
                >
                  {fastMode ? '重新演示' : '重新演示'}
                </Button>
              )}
              <Button size="small" onClick={() => { setDemoMode(false); stopDemo(); setContent(''); setCodingResult(null); setQcResult(null); setDrgResult(null); setRejectionResult(null); setCurrentStep(-1); }}>
                退出
              </Button>
            </Space>
          )}
          {demoMode && (
            <Space size={4}>
              {fastMode && (
                <Tag color="orange" icon={<ThunderboltOutlined />}>
                  快速模式（离线）
                </Tag>
              )}
              <Tag
                color={loading ? 'processing' : demoRunning ? 'processing' : 'success'}
                icon={loading ? <LoadingOutlined /> : demoRunning ? <LoadingOutlined /> : <CheckCircleOutlined />}
              >
                {loading ? '分析中...' : demoRunning ? '打字中...' : elapsedTime > 0 ? `完成 (${(elapsedTime / 1000).toFixed(1)}s)` : typingDone ? '分析中...' : '准备就绪'}
              </Tag>
            </Space>
          )}
        </Space>
      </div>

      <Divider />

      {/* Input Area */}
      <Card
        title="病历输入"
        extra={
          !demoMode ? (
            <Upload accept=".txt,.docx,.pdf" showUploadList={false}
              customRequest={async ({ file, onSuccess, onError }) => {
                if (file instanceof File) {
                  try {
                    if (file.name.endsWith('.txt')) {
                      const text = await file.text()
                      setContent(text)
                      message.success('文件加载成功')
                    } else {
                      const { data } = await codingAPI.uploadAndCode(file)
                      if (data.status === 'parsed' && data.content) {
                        setContent(data.content)
                        message.success(`文件解析成功 (${data.file_type}, ${data.text_length} 字)`)
                      } else if (data.status === 'unsupported_format') {
                        message.error('不支持的文件格式，请上传 .txt / .docx / .pdf')
                      } else {
                        message.error(data.error || '文件解析失败')
                      }
                    }
                    onSuccess?.('ok')
                  } catch {
                    message.error('文件读取失败')
                    onError?.({ name: 'error', message: '文件读取失败' })
                  }
                }
              }}
            >
              <Button icon={<UploadOutlined />}>上传文件 (.txt/.docx/.pdf)</Button>
            </Upload>
          ) : null
        }
        style={{ marginBottom: 16 }}
        className={demoRunning ? 'pipeline-card-processing' : ''}
      >
        <div style={{ position: 'relative' }}>
          <TextArea
            value={content}
            onChange={(e) => { if (!demoRunning) setContent(e.target.value) }}
            placeholder={demoMode ? '演示模式：AI将自动输入病历内容...' : '请粘贴住院病历内容（出院小结、入院记录等）...'}
            rows={10}
            readOnly={demoRunning}
            style={{
              fontFamily: 'monospace',
              ...(demoRunning ? { background: '#fafeff', borderColor: '#0ea5e9' } : {}),
            }}
          />
          {/* Typewriter cursor */}
          {demoRunning && (
            <span style={{
              position: 'absolute', bottom: 16, right: 16,
              display: 'inline-block', width: 10, height: 20,
              background: '#0ea5e9',
              animation: 'pulse-border 0.8s ease-in-out infinite',
              borderRadius: 2,
            }} />
          )}
        </div>

        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Select defaultValue="discharge" style={{ width: 160 }} disabled={demoRunning}>
              <Select.Option value="admission">入院记录</Select.Option>
              <Select.Option value="discharge">出院小结</Select.Option>
              <Select.Option value="surgery">手术记录</Select.Option>
            </Select>
            <Text type="secondary">年龄</Text>
            <InputNumber min={0} max={120} value={patientAge} onChange={(v) => setPatientAge(v ?? null)} style={{ width: 72 }} disabled={demoRunning} placeholder="岁" />
            <Select value={patientGender} onChange={setPatientGender} style={{ width: 72 }} disabled={demoRunning}>
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
            </Select>
            <Text type="secondary">住院</Text>
            <InputNumber min={1} max={365} value={daysOfStay} onChange={(v) => setDaysOfStay(v ?? null)} style={{ width: 80 }} disabled={demoRunning} placeholder="天" />
            <Text type="secondary">支持 .txt / .docx / .pdf 格式</Text>
          </Space>
          {!demoMode && (
            <Button
              type="primary" size="large" icon={<ThunderboltOutlined />}
              loading={loading} onClick={() => handleStart()}
              style={{ minWidth: 160, height: 44 }}
            >
              开始智能分析
            </Button>
          )}
          {demoMode && !demoRunning && typingDone && (
            <Button
              type="primary" size="large" icon={<ThunderboltOutlined />}
              loading={loading} onClick={() => handleStart()}
              style={{ minWidth: 160, height: 44 }}
            >
              重新分析
            </Button>
          )}
        </div>
      </Card>

      {/* Pipeline Steps */}
      <Card style={{ marginBottom: 16 }}>
        <Steps
          current={currentStep}
          status={loading ? 'process' : currentStep === 3 ? 'finish' : 'wait'}
          items={stepItems.map((item, i) => ({
            title: item.title,
            description: item.desc,
            icon: currentStep > i ? <CheckCircleOutlined /> : item.icon,
          }))}
        />
      </Card>

      <Spin spinning={loading} tip={demoMode ? 'AI自动分析中...' : 'AI分析中...'}>
        {/* Step 1 Result: ICD Coding */}
        {codingResult && (
          <Card
            title={<Space><FileTextOutlined style={{ color: '#1677ff' }} />智能编码结果</Space>}
            extra={
              <Space>
                <Tag color="blue">{codingResult.processing_time_ms}ms</Tag>
                <Text type="secondary">
                  总体置信度: <Text strong>{(codingResult.total_confidence * 100).toFixed(0)}%</Text>
                </Text>
              </Space>
            }
            style={{ marginBottom: 16 }}
            className={currentStep === 0 && loading ? 'pipeline-card-processing' : currentStep > 0 ? 'pipeline-card-complete' : ''}
          >
            <IcdCodingResult result={codingResult} />
          </Card>
        )}

        {/* Step 2 Result: QC */}
        {qcResult && (
          <Card
            title={<Space><SafetyCertificateOutlined style={{ color: qcResult.qc_score >= 90 ? '#52c41a' : '#fa8c16' }} />质控检查结果</Space>}
            extra={
              <Space size="large">
                <span>
                  {qcResult.critical_count > 0 && <Tag color="red">严重 {qcResult.critical_count}</Tag>}
                  {qcResult.major_count > 0 && <Tag color="orange">重要 {qcResult.major_count}</Tag>}
                  {qcResult.minor_count > 0 && <Tag color="gold">一般 {qcResult.minor_count}</Tag>}
                  {qcResult.info_count > 0 && <Tag color="blue">提示 {qcResult.info_count}</Tag>}
                </span>
              </Space>
            }
            style={{ marginBottom: 16 }}
            className={currentStep === 1 && loading ? 'pipeline-card-processing' : currentStep > 1 ? 'pipeline-card-complete' : ''}
          >
            <Row gutter={24} align="middle">
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="dashboard" percent={qcResult.qc_score} size={120}
                    strokeColor={qcResult.qc_score >= 90 ? '#52c41a' : qcResult.qc_score >= 70 ? '#fa8c16' : '#ff4d4f'}
                    format={(p) => <span style={{ fontSize: 24, fontWeight: 'bold' }}>{p}</span>} />
                  <div style={{ marginTop: 4 }}><Text type="secondary">质控评分</Text></div>
                </div>
              </Col>
              <Col span={18}>
                {qcResult.issues.length > 0 ? (
                  <Table
                    dataSource={qcResult.issues}
                    rowKey="rule_id"
                    size="small"
                    pagination={false}
                    columns={[
                      {
                        title: '级别', dataIndex: 'severity', key: 'severity', width: 80,
                        render: (s: string) => (
                          <Tag color={severityColor[s]}>
                            {s === 'critical' ? '严重' : s === 'major' ? '重要' : s === 'minor' ? '一般' : '提示'}
                          </Tag>
                        ),
                      },
                      { title: '检查项', dataIndex: 'rule_name', key: 'rule_name', width: 160 },
                      { title: '问题描述', dataIndex: 'line_snippet', key: 'line_snippet' },
                      {
                        title: '建议', dataIndex: 'suggestion', key: 'suggestion',
                        render: (v: string) => <Text type="secondary" ellipsis={{ tooltip: v }}>{v}</Text>,
                      },
                      {
                        title: '', key: 'action', width: 100,
                        render: (_: unknown, _record: QCIssue, index: number) => {
                          const qcId = qcResultIds[index]?.id
                          if (!qcId) return null
                          return (
                            <Space size={4}>
                              <Button size="small" type="primary" ghost
                                onClick={async () => {
                                  try { await qcAPI.acceptResult(qcId); message.success('已采纳') }
                                  catch { message.error('操作失败') }
                                }}>采纳</Button>
                              <Button size="small" type="text" danger
                                onClick={async () => {
                                  try { await qcAPI.rejectResult(qcId); message.info('已忽略') }
                                  catch { message.error('操作失败') }
                                }}>忽略</Button>
                            </Space>
                          )
                        },
                      },
                    ]}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: 40 }}>
                    <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 32 }} />
                    <div style={{ marginTop: 8 }}><Text type="secondary">未发现质控缺陷，病历质量良好</Text></div>
                  </div>
                )}
              </Col>
            </Row>
          </Card>
        )}

        {/* Step 3 & 4: DRG + Payment */}
        {drgResult && (
          <Row gutter={24}>
            <Col span={14}>
              <Card
                title={<Space><MedicineBoxOutlined style={{ color: '#722ed1' }} />DRG分组结果</Space>}
                extra={
                  <Tag color={drgResult.is_surgical ? 'blue' : 'green'}>
                    {drgResult.is_surgical ? '手术组' : '非手术组'}
                  </Tag>
                }
                className="pipeline-card-complete"
              >
                <Descriptions column={2} bordered size="small">
                  <Descriptions.Item label="DRG编码">
                    <Text strong style={{ fontSize: 18, color: '#722ed1' }}>{drgResult.drg_code || '待确定'}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="DRG名称">{drgResult.drg_name}</Descriptions.Item>
                  <Descriptions.Item label="MDC大类">{drgResult.mdc} - {drgResult.mdc_name}</Descriptions.Item>
                  <Descriptions.Item label="ADRG">{drgResult.adrg} - {drgResult.adrg_name}</Descriptions.Item>
                  <Descriptions.Item label="合并症/并发症">
                    <Tag color={drgResult.cc_flag === 'MCC' ? 'red' : drgResult.cc_flag === 'CC' ? 'orange' : 'default'}>
                      {drgResult.cc_flag || '无'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="病例复杂度">{drgResult.patient_complexity}</Descriptions.Item>
                  <Descriptions.Item label="权重 (RW)">{drgResult.weight.toFixed(3)}</Descriptions.Item>
                  <Descriptions.Item label="费率">¥{drgResult.rate.toLocaleString()}</Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            <Col span={10}>
              <Card
                title={<Space><DollarOutlined style={{ color: '#3f8600' }} />医保支付测算</Space>}
                style={{ background: 'linear-gradient(135deg, #f6ffed 0%, #f0fff0 100%)' }}
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: 36, fontWeight: 'bold', color: '#3f8600', fontFamily: 'monospace' }}>
                    ¥{drgResult.estimated_payment.toLocaleString()}
                  </div>
                  <div style={{ marginTop: 8, color: '#888' }}>预估医保支付金额</div>

                  <Divider />

                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic title="权重 (RW)" value={drgResult.weight} precision={3} />
                    </Col>
                    <Col span={12}>
                      <Statistic title="费率" value={drgResult.rate} prefix="¥" precision={0} />
                    </Col>
                  </Row>

                  <div style={{
                    marginTop: 16, padding: 12, background: '#fff', borderRadius: 8,
                    border: '1px solid #d9f7be',
                  }}>
                    <Text type="secondary">
                      支付公式: RW × 费率 = {drgResult.weight.toFixed(3)} × ¥{drgResult.rate.toLocaleString()} = {' '}
                      <Text strong style={{ color: '#3f8600', fontSize: 16 }}>
                        ¥{drgResult.estimated_payment.toLocaleString()}
                      </Text>
                    </Text>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>
        )}

        {/* Step 5: Rejection Risk */}
        {rejectionResult && (
          <Card
            title={
              <Space>
                <ThunderboltOutlined style={{ color: rejectionResult.overall_risk === 'high' ? '#ff4d4f' : rejectionResult.overall_risk === 'medium' ? '#faad14' : '#52c41a' }} />
                医保拒付风险预测
              </Space>
            }
            extra={
              <Space>
                <Tag color={rejectionResult.overall_risk === 'high' ? 'red' : rejectionResult.overall_risk === 'medium' ? 'orange' : 'green'}>
                  {rejectionResult.overall_risk === 'high' ? '高风险' : rejectionResult.overall_risk === 'medium' ? '中风险' : '低风险'}
                </Tag>
                <Text type="secondary">风险评分: {rejectionResult.risk_score}/100</Text>
              </Space>
            }
            style={{
              marginTop: 16,
              borderColor: rejectionResult.overall_risk === 'high' ? '#ffccc7' : rejectionResult.overall_risk === 'medium' ? '#ffe58f' : '#d9f7be',
            }}
          >
            {/* Risk summary */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Statistic
                  title="风险评分"
                  value={rejectionResult.risk_score}
                  suffix="/ 100"
                  valueStyle={{ color: rejectionResult.overall_risk === 'high' ? '#ff4d4f' : rejectionResult.overall_risk === 'medium' ? '#faad14' : '#52c41a' }}
                />
              </Col>
              <Col span={8}>
                <Statistic title="风险项" value={rejectionResult.risks.length} suffix="条" />
              </Col>
              <Col span={8}>
                <Statistic
                  title="可规避金额"
                  value={rejectionResult.preventable_amount}
                  prefix="¥"
                  precision={0}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>

            {/* Risk items */}
            {rejectionResult.risks.length > 0 && (
              <Table
                dataSource={rejectionResult.risks.map((r, i) => ({ ...r, key: i }))}
                columns={[
                  {
                    title: '级别', dataIndex: 'risk_level', width: 80,
                    render: (v: string) => (
                      <Tag color={v === 'high' ? 'red' : v === 'medium' ? 'orange' : 'blue'}>
                        {v === 'high' ? '严重' : v === 'medium' ? '重要' : '提示'}
                      </Tag>
                    ),
                  },
                  { title: '检查项', dataIndex: 'rule_name', width: 160 },
                  { title: '问题描述', dataIndex: 'description', ellipsis: true },
                  { title: '修正建议', dataIndex: 'suggestion', ellipsis: true },
                  {
                    title: '预估损失', dataIndex: 'estimated_loss', width: 110,
                    render: (v: number) => v > 0 ? <Text type="danger">¥{v.toLocaleString()}</Text> : '-',
                  },
                ]}
                pagination={false}
                size="small"
              />
            )}
          </Card>
        )}

        {/* Empty state */}
        {!codingResult && !loading && !demoMode && (
          <Card>
            <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
              <ThunderboltOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block' }} />
              <Text type="secondary" style={{ fontSize: 16 }}>
                粘贴病历内容，点击"开始智能分析"查看完整的编码→质控→DRG→付费流水线
              </Text>
            </div>
          </Card>
        )}

        {/* Demo empty state */}
        {!codingResult && !loading && demoMode && !demoRunning && !typingDone && (
          <Card>
            <div style={{ textAlign: 'center', padding: 60, color: '#ccc' }}>
              <ThunderboltOutlined style={{ fontSize: 64, marginBottom: 16, display: 'block', color: '#0ea5e9' }} />
              <Text type="secondary" style={{ fontSize: 16 }}>
                {fastMode ? '快速模式：跳过打字动画，1秒内完成全流程分析' : '点击"重新演示"开始完整演示'}
              </Text>
            </div>
          </Card>
        )}

        {/* B v2: 流水线分析完成后, 引导跳转至独立 /rejection 页面 */}
        <PipelineRejectionRedirect
          trigger={!!rejectionResult && !!rejectionContext}
          prefill={{
            ...(rejectionContext ?? { content }),
            assessment_result: rejectionResult ?? undefined,
          }}
        />
      </Spin>
    </div>
  )
}
