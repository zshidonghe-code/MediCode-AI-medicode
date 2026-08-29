# 码医 MediCode API 参考文档

> 版本：1.0.0 | 基础路径：`/api/v1`

## 目录

- [认证与鉴权](#认证与鉴权)
- [编码接口](#编码接口)
- [DRG 分组接口](#drg-分组接口)
- [质控接口](#质控接口)
- [仪表盘接口](#仪表盘接口)
- [流水线接口](#流水线接口)
- [管理接口](#管理接口)
- [健康检查](#健康检查)
- [错误码说明](#错误码说明)
- [SDK 示例](#sdk-示例)

---

## 认证与鉴权

所有业务 API（`/api/v1/**`）均需携带 JWT Bearer Token，通过请求头 `Authorization: Bearer <token>` 传递。

### 登录

```
POST /api/v1/auth/login
```

**请求格式**：`application/x-www-form-urlencoded`

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `username` | string | 是 | 用户名 |
| `password` | string | 是 | 密码 |

**成功响应** `200`：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "username": "admin",
  "role": "admin",
  "name": "管理员"
}
```

**错误响应**：

| 状态码 | 说明 |
| --- | --- |
| `401` | 用户名或密码错误 |
| `429` | 登录尝试过多，60秒内最多 5 次 |

**演示账号**（开发环境）：

| 用户名 | 密码 | 角色 | 权限 |
| --- | --- | --- | --- |
| `admin` | `123456` | 管理员 | 全部权限，含数据重置与导出 |
| `coder` | `123456` | 编码员 | 编码、DRG、质控操作 |
| `doctor` | `123456` | 医生 | 编码、DRG、质控操作 |

**curl 示例**：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=123456"
```

**JavaScript (Axios) 示例**：

```javascript
import axios from 'axios';

const formData = new FormData();
formData.append('username', 'admin');
formData.append('password', '123456');

const { data } = await axios.post('/api/v1/auth/login', formData);
// 保存 token
localStorage.setItem('token', data.access_token);
axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
```

### 获取当前用户

```
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**成功响应** `200`：

```json
{
  "username": "admin",
  "role": "admin",
  "name": "管理员"
}
```

---

## 编码接口

### 自动编码

对病历文本执行 NLP 解析和 ICD 自动编码。

```
POST /api/v1/coding/auto-code
Authorization: Bearer <token>
```

**请求体** `application/json`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `record_id` | integer | 是 | 病历 ID（临时可用时间戳） |
| `record_type` | string | 是 | 病历类型，可选值见下表 |
| `content` | string | 是 | 病历文本，长度 10-50000 字符 |
| `use_llm` | boolean | 否 | 是否启用 LLM 辅助，默认 `false`（规则引擎快速响应） |

**`record_type` 可选值**：

| 值 | 说明 |
| --- | --- |
| `admission` | 入院记录 |
| `course` | 病程记录 |
| `surgery` | 手术记录 |
| `discharge` | 出院小结 |
| `consultation` | 会诊记录 |
| `exam` | 检查报告 |
| `lab` | 检验报告 |

**请求示例**：

```json
{
  "record_id": 1234567890,
  "record_type": "discharge",
  "content": "主诉：突发胸痛3小时...",
  "use_llm": false
}
```

**成功响应** `200`：

```json
{
  "record_id": 1234567890,
  "primary_diagnosis": {
    "code": "I21.300",
    "name": "急性ST段抬高型心肌梗死（前壁）",
    "category": "诊断",
    "is_primary": true,
    "confidence": 0.95
  },
  "secondary_diagnoses": [
    {
      "code": "I10.x00",
      "name": "原发性高血压",
      "category": "诊断",
      "is_primary": false,
      "confidence": 0.82
    }
  ],
  "procedures": [
    {
      "code": "36.0700",
      "name": "经皮冠状动脉支架植入术",
      "category": "手术操作",
      "is_primary": false,
      "confidence": 0.91
    }
  ],
  "suggestions": [],
  "total_confidence": 0.88,
  "processing_time_ms": 320
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `primary_diagnosis` | object / null | 主要诊断，算法自动从诊断列表中选出 |
| `secondary_diagnoses` | array | 次要诊断列表（去重、最多 9 条） |
| `procedures` | array | 手术操作编码列表 |
| `suggestions` | array | 候选编码建议（top 5） |
| `total_confidence` | float | 总体置信度，0-1 |
| `processing_time_ms` | integer | 处理耗时（毫秒） |

**编码对象字段**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | string | ICD 编码 |
| `name` | string | 编码名称 |
| `category` | string | 分类：`诊断` 或 `手术操作` |
| `is_primary` | boolean | 是否为主要诊断 |
| `confidence` | float | 单条置信度，0-1 |

**curl 示例**：

```bash
curl -X POST http://localhost:8000/api/v1/coding/auto-code \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": 123,
    "record_type": "discharge",
    "content": "出院诊断：急性ST段抬高型心肌梗死（前壁），高血压病3级，2型糖尿病。手术：经皮冠状动脉支架植入术。"
  }'
```

**JavaScript 示例**：

```javascript
const { data } = await axios.post('/api/v1/coding/auto-code', {
  record_id: Date.now(),
  record_type: 'discharge',
  content: '主诉：突发胸痛3小时...',
});

console.log(`主要诊断: ${data.primary_diagnosis.name}`);
console.log(`ICD编码: ${data.primary_diagnosis.code}`);
console.log(`置信度: ${data.total_confidence}`);
```

### 文件上传解析

上传病历文件（txt / docx / pdf），返回解析后的文本内容。不会执行编码，仅做文本提取。

```
POST /api/v1/coding/auto-code/upload
Authorization: Bearer <token>
```

**请求格式**：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | 病历文件，支持 `.txt` `.docx` `.pdf` |

**成功响应** `200`：

```json
{
  "filename": "病历001.docx",
  "file_type": "docx",
  "status": "parsed",
  "content": "主诉：突发胸痛3小时...",
  "text_length": 2456,
  "page_count": 3,
  "parse_time_ms": 520,
  "diagnosis_count": 3,
  "surgery_count": 1
}
```

**错误响应**：

| 状态码 | 说明 |
| --- | --- |
| `200` (status=unsupported_format) | 不支持的文件格式 |
| `200` (status=parse_error) | 文件解析失败 |
| `200` (status=empty_content) | 文件无有效内容 |

**curl 示例**：

```bash
curl -X POST http://localhost:8000/api/v1/coding/auto-code/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@病历.docx"
```

### 编码校验

对 AI 编码结果进行逻辑校验（性别冲突、主诊规则等）。

```
POST /api/v1/coding/validate
Authorization: Bearer <token>
```

**请求体** `application/json`：完整的 CodingResponse 对象。

**成功响应** `200`：

```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

### ICD 编码搜索

搜索 ICD 编码（支持中英文、拼音首字母、语义搜索）。

```
GET /api/v1/coding/search?keyword=<关键词>&limit=<数量>
Authorization: Bearer <token>
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 搜索关键词 |
| `limit` | integer | 否 | 返回数量上限，默认 20 |

**成功响应** `200`：

```json
{
  "keyword": "高血压",
  "results": [
    { "code": "I10.x00", "name": "原发性高血压", "score": 1.0 },
    { "code": "I15.000", "name": "肾性高血压", "score": 0.85 }
  ]
}
```

---

## DRG 分组接口

基于 CHS-DRG 1.2 版分组方案，输入诊断/手术编码和患者信息，输出 DRG 分组结果和预估费用。

### 执行 DRG 分组

```
POST /api/v1/drg/group
Authorization: Bearer <token>
```

**请求体** `application/json`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `patient_age` | integer | 是 | 患者年龄 |
| `patient_gender` | string | 是 | 性别：`male` / `female` |
| `primary_diagnosis_code` | string | 是 | 主要诊断 ICD-10 编码 |
| `secondary_diagnosis_codes` | string[] | 否 | 次要诊断编码列表 |
| `procedure_codes` | string[] | 否 | 手术操作编码列表（ICD-9-CM-3） |
| `discharge_type` | string | 否 | 离院方式，默认 `"1"`（医嘱离院） |
| `days_of_stay` | integer | 否 | 住院天数 |
| `newborn_weight` | integer | 否 | 新生儿出生体重（克） |
| `ventilation_hours` | integer | 否 | 有创呼吸机使用时间（小时） |

**请求示例**：

```json
{
  "patient_age": 65,
  "patient_gender": "male",
  "primary_diagnosis_code": "I21.300",
  "secondary_diagnosis_codes": ["I10.x00", "E11.900"],
  "procedure_codes": ["36.0700"],
  "discharge_type": "1",
  "days_of_stay": 10
}
```

**成功响应** `200`：

```json
{
  "mdc": "MDCE",
  "mdc_name": "循环系统疾病及功能障碍",
  "adrg": "FM1",
  "adrg_name": "经皮冠状动脉介入治疗，伴严重并发症或合并症",
  "drg_code": "FM11",
  "drg_name": "经皮冠状动脉介入治疗，伴严重并发症或合并症",
  "is_surgical": true,
  "weight": 3.45,
  "rate": 12000.0,
  "estimated_payment": 41400.0,
  "cc_flag": "MCC",
  "patient_complexity": "高风险"
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `mdc` | string | 26 个主要诊断大类编码 |
| `mdc_name` | string | MDC 中文名称 |
| `adrg` | string | 核心 DRG 组编码 |
| `adrg_name` | string | ADRG 中文名称 |
| `drg_code` | string | 最终 DRG 编码（ADRG + 合并症后缀） |
| `drg_name` | string | DRG 中文名称 |
| `is_surgical` | boolean | 是否为手术组 |
| `weight` | float | DRG 相对权重 (RW) |
| `rate` | float | 费率（元），由 `DRG_BASE_RATE` 配置 |
| `estimated_payment` | float | 预估医保支付金额 = RW x 费率 |
| `cc_flag` | string | 合并症标志：`MCC` / `CC` / 空 |
| `patient_complexity` | string | 患者复杂度：`高风险` / `中风险` / `低风险` |

**curl 示例**：

```bash
curl -X POST http://localhost:8000/api/v1/drg/group \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_age": 65,
    "patient_gender": "male",
    "primary_diagnosis_code": "I21.300",
    "procedure_codes": ["36.0700"]
  }'
```

**JavaScript 示例**：

```javascript
const { data } = await axios.post('/api/v1/drg/group', {
  patient_age: 65,
  patient_gender: 'male',
  primary_diagnosis_code: 'I21.300',
  secondary_diagnosis_codes: ['I10.x00', 'E11.900'],
  procedure_codes: ['36.0700'],
  days_of_stay: 10,
});

console.log(`DRG: ${data.drg_code} ${data.drg_name}`);
console.log(`权重: ${data.weight}`);
console.log(`预估支付: ¥${data.estimated_payment.toLocaleString()}`);
```

### 查询 DRG 详情

```
GET /api/v1/drg/group/{drg_code}
Authorization: Bearer <token>
```

**成功响应** `200`：

```json
{
  "drg_code": "FM11",
  "name": "经皮冠状动脉介入治疗，伴严重并发症或合并症",
  "mdc": "MDCE",
  "is_surgical": true,
  "weight": 3.45,
  "rate": 12000.0,
  "avg_days": 10.5
}
```

### DRG 对比

对比 AI 分组与人工分组的差异，自动计算费用差额。

```
GET /api/v1/drg/compare?record_id=<ID>&ai_drg=<AI分组>&manual_drg=<人工分组>
Authorization: Bearer <token>
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `record_id` | integer | 是 | 病历 ID |
| `ai_drg` | string | 是 | AI 分组的 DRG 编码 |
| `manual_drg` | string | 是 | 人工分组的 DRG 编码 |

**成功响应** `200`：

```json
{
  "same": false,
  "ai_drg": "FM11",
  "manual_drg": "FM13",
  "ai_weight": 3.45,
  "manual_weight": 1.82,
  "payment_gap": 19560.0
}
```

---

## 质控接口

基于 17 条基础规则（可扩展至 100+）的病历内涵质控引擎。检查维度包括完整性、逻辑一致性、编码一致性、时效性、规范表达、语义质量。

### 执行质控检查

```
POST /api/v1/qc/check
Authorization: Bearer <token>
```

**请求体** `application/json`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `record_id` | integer | 是 | 病历 ID |
| `record_type` | string | 是 | 病历类型 |
| `content` | string | 是 | 病历文本 |
| `coding_result` | object | 否 | 编码结果（用于编码一致性检查） |
| `patient_info` | object | 否 | 患者信息（用于性别/年龄逻辑检查） |
| `use_llm` | boolean | 否 | 是否启用 LLM 语义检查，默认 `false` |

**请求示例**：

```json
{
  "record_id": 456789,
  "record_type": "discharge",
  "content": "主诉：头痛3天。查体：T36.5...",
  "coding_result": {
    "primary_diagnosis": { "code": "I10.x00", "name": "原发性高血压" }
  },
  "use_llm": false
}
```

**成功响应** `200`：

```json
{
  "record_id": 456789,
  "total_issues": 3,
  "critical_count": 0,
  "major_count": 1,
  "minor_count": 2,
  "info_count": 0,
  "issues": [
    {
      "rule_id": "QC-001",
      "rule_name": "出院小结完整性-出院诊断",
      "rule_type": "completeness",
      "severity": "critical",
      "description": "出院小结中未找到出院诊断部分",
      "line_snippet": "...T36.5，P80次/分...",
      "suggestion": "出院小结必须包含出院诊断",
      "line_number": null
    }
  ],
  "qc_score": 86.0,
  "processing_time_ms": 45
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `total_issues` | integer | 缺陷总数 |
| `critical_count` | integer | 严重缺陷数（扣 10 分/条） |
| `major_count` | integer | 重要缺陷数（扣 5 分/条） |
| `minor_count` | integer | 一般缺陷数（扣 2 分/条） |
| `info_count` | integer | 提示数（扣 0.5 分/条） |
| `qc_score` | float | 质控评分，0-100 |
| `issues` | array | 缺陷列表 |

**缺陷严重级别**：

| 级别 | 代码 | 说明 | 扣分 |
| --- | --- | --- | --- |
| 严重 (Critical) | `critical` | 医保拒付风险 | -10 |
| 重要 (Major) | `major` | 影响 DRG 分组 | -5 |
| 一般 (Minor) | `minor` | 一般缺陷 | -2 |
| 提示 (Info) | `info` | 提示信息 | -0.5 |

**缺陷类型**：

| 类型 | 代码 | 说明 |
| --- | --- | --- |
| 完整性 | `completeness` | 必填字段/章节缺失 |
| 逻辑一致性 | `logic` | 前后矛盾、诊断冲突 |
| 编码一致性 | `coding` | 编码与文本不一致 |
| 时效性 | `timeliness` | 记录时间超期 |
| 规范表达 | `normalization` | 术语不规范 |
| 语义质量 | `semantic` | LLM 语义分析问题 |

**curl 示例**：

```bash
curl -X POST http://localhost:8000/api/v1/qc/check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "record_id": 789,
    "record_type": "discharge",
    "content": "主诉：发热3天。查体：T38.5..."
  }'
```

**JavaScript 示例**：

```javascript
const { data } = await axios.post('/api/v1/qc/check', {
  record_id: Date.now(),
  record_type: 'discharge',
  content: '主诉：发热3天...',
});

console.log(`质控评分: ${data.qc_score}`);
console.log(`严重缺陷: ${data.critical_count}`);
console.log(`重要缺陷: ${data.major_count}`);

data.issues.forEach(issue => {
  console.log(`[${issue.severity}] ${issue.rule_name}: ${issue.suggestion}`);
});
```

### 查询质控规则

```
GET /api/v1/qc/rules?rule_type=<类型>&severity=<级别>
Authorization: Bearer <token>
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `rule_type` | string | 否 | 筛选规则类型 |
| `severity` | string | 否 | 筛选严重级别 |

**成功响应** `200`：

```json
{
  "rules": [
    {
      "id": "QC-001",
      "name": "出院小结完整性-出院诊断",
      "type": "completeness",
      "severity": "critical",
      "suggestion": "出院小结必须包含出院诊断"
    }
  ],
  "total": 1
}
```

### 质控结果操作

```
PUT /api/v1/qc/results/{result_id}/accept
PUT /api/v1/qc/results/{result_id}/reject
Authorization: Bearer <token>
```

标记质控结果为"已采纳"或"已驳回"。

**成功响应** `200`：

```json
{ "result_id": 42, "accepted": true }
```

---

## 仪表盘接口

### 全院运营概览

```
GET /api/v1/dashboard/overview?start_date=<日期>&end_date=<日期>
Authorization: Bearer <token>
```

**成功响应** `200`：

```json
{
  "total_cases": 156,
  "total_weight": 234.56,
  "cmi": 1.52,
  "avg_cost": 18240,
  "avg_stay_days": 8.3,
  "cost_consumption_index": 1.05,
  "time_consumption_index": 0.92,
  "low_risk_mortality_rate": 0.0,
  "ai_coding_rate": 0.85,
  "qc_pass_rate": 0.72
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
| --- | --- | --- | --- |
| `total_cases` | integer | 总病例数 |
| `total_weight` | float | 总权重数（总 RW） |
| `cmi` | float | 病例组合指数 (Case Mix Index) |
| `avg_cost` | float | 例均费用（元） |
| `avg_stay_days` | float | 平均住院日 |
| `cost_consumption_index` | float | 费用消耗指数 |
| `time_consumption_index` | float | 时间消耗指数 |
| `low_risk_mortality_rate` | float | 低风险组死亡率 |
| `ai_coding_rate` | float | AI 编码率（0-1） |
| `qc_pass_rate` | float | 质控合格率（0-1） |

### 科室排名

```
GET /api/v1/dashboard/department-ranking?metric=cmi&limit=10
Authorization: Bearer <token>
```

### 质控趋势

```
GET /api/v1/dashboard/qc-trend?days=90
Authorization: Bearer <token>
```

按周聚合质控评分，3 周移动平均平滑，附带 CMI 趋势。

### 编码准确率趋势

```
GET /api/v1/dashboard/coding-accuracy?days=90
Authorization: Bearer <token>
```

### 高频质控缺陷

```
GET /api/v1/dashboard/high-frequency-issues?days=90&limit=10
Authorization: Bearer <token>
```

### 收入分析

```
GET /api/v1/dashboard/revenue-analysis?days=90
Authorization: Bearer <token>
```

按月聚合 DRG 预期收入趋势。

---

## 流水线接口

### 保存流水线结果

将全链路（编码 + 质控 + DRG）结果保存到数据库，供仪表盘统计分析。

```
POST /api/v1/pipeline/save
Authorization: Bearer <token>
```

**请求体** `application/json`：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content` | string | 否 | 病历文本（有 coding_result 时可为空） |
| `record_type` | string | 否 | 病历类型，默认 `discharge` |
| `coding_result` | object | 否 | 编码结果对象 |
| `qc_result` | object | 否 | 质控结果对象 |
| `drg_result` | object | 否 | DRG 分组结果对象 |
| `department` | string | 否 | 科室名称，默认 `"流水线"` |
| `patient_info` | object | 否 | 患者信息，含 `age` 和 `gender` |
| `primary_diagnosis_code` | string | 否 | 主要诊断编码 |
| `secondary_diagnosis_codes` | string[] | 否 | 次要诊断编码 |
| `procedure_codes` | string[] | 否 | 手术操作编码 |

**成功响应** `200`：

```json
{
  "success": true,
  "patient_id": "PIPE1A2B3C4D",
  "record_id": 42,
  "coding_result_id": 42,
  "qc_result_ids": [{ "id": 1, "severity": "major" }]
}
```

---

## 管理接口

所有管理接口需要 `admin` 角色权限。

### 重置数据

```
POST /api/v1/admin/reset
Authorization: Bearer <token> （需 admin 角色）
```

**请求体**：

```json
{ "confirm": true }
```

### 数据导出

```
GET /api/v1/admin/export/coding-results?format=json
GET /api/v1/admin/export/patient-summaries?format=csv
GET /api/v1/admin/export/qc-results?format=json
```

支持 `json` 和 `csv` 两种格式。返回文件下载流。

---

## 健康检查

```
GET /health
```

**响应** `200`：

```json
{ "status": "ok" }
```

```
GET /health/llm
```

**响应** `200`：

```json
{
  "llm_available": true,
  "llm_backend": "ollama"
}
```

当 Ollama 不可用时返回：

```json
{
  "llm_available": false,
  "llm_backend": "rule-based"
}
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 |
| --- | --- |
| `200` | 成功 |
| `400` | 请求参数错误（如 `content` 字段长度不足） |
| `401` | 未认证（token 缺失、过期或无效） |
| `403` | 无权限（需要管理员角色） |
| `404` | 资源不存在（如 DRG 编码查不到） |
| `422` | 请求体验证失败（字段类型/必填校验） |
| `429` | 请求频率超限（登录接口） |
| `500` | 服务器内部错误 |

### 通用错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误场景

| 场景 | 状态码 | 错误原因 |
| --- | --- | --- |
| 未携带 Authorization 头 | 401 | `"Not authenticated"` |
| Token 已过期 | 401 | `"无效的认证令牌"` |
| 非 admin 调用管理接口 | 403 | `"需要管理员权限"` |
| `content` 字段少于 10 字 | 422 | 字段长度校验失败 |
| 上传不支持的文件格式 | 200 | `status: "unsupported_format"` |
| 登录密码连续错误 | 429 | `"登录尝试过多，请稍后再试"` |

---

## SDK 示例

### JavaScript/TypeScript (Axios) 完整示例

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// 设置 token
function setToken(token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// 登录
async function login(username, password) {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  const { data } = await api.post('/auth/login', formData);
  setToken(data.access_token);
  return data;
}

// 自动编码
async function autoCode(content) {
  const { data } = await api.post('/coding/auto-code', {
    record_id: Date.now(),
    record_type: 'discharge',
    content: content,
  });
  return data;
}

// DRG 分组
async function groupDRG(primaryCode, procedureCodes, age, gender) {
  const { data } = await api.post('/drg/group', {
    patient_age: age,
    patient_gender: gender,
    primary_diagnosis_code: primaryCode,
    procedure_codes: procedureCodes,
  });
  return data;
}

// 质控检查
async function qcCheck(content, codingResult) {
  const { data } = await api.post('/qc/check', {
    record_id: Date.now(),
    record_type: 'discharge',
    content: content,
    coding_result: codingResult,
  });
  return data;
}

// 使用示例
(async () => {
  // 1. 登录
  await login('coder', '123456');
  console.log('登录成功');

  // 2. 编码
  const coding = await autoCode('出院诊断：急性心肌梗死，高血压病');
  console.log('主要诊断:', coding.primary_diagnosis?.name);

  // 3. DRG 分组
  const drg = await groupDRG(
    coding.primary_diagnosis.code,
    coding.procedures.map(p => p.code),
    65,
    'male'
  );
  console.log('DRG:', drg.drg_code, '预估支付:', drg.estimated_payment);

  // 4. 质控
  const qc = await qcCheck(
    '出院诊断：急性心肌梗死，高血压病',
    coding
  );
  console.log('质控评分:', qc.qc_score);

  // 5. 保存全链路结果
  await api.post('/pipeline/save', {
    content: '出院诊断：急性心肌梗死，高血压病',
    record_type: 'discharge',
    coding_result: coding,
    drg_result: drg,
    qc_result: qc,
    department: '流水线',
  });
  console.log('全链路结果已保存');
})();
```

### Python (httpx) 示例

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient(base_url=BASE) as client:
        # 1. 登录
        r = await client.post("/auth/login", data={
            "username": "admin",
            "password": "123456",
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 自动编码
        r = await client.post("/coding/auto-code", json={
            "record_id": 1,
            "record_type": "discharge",
            "content": "出院诊断：急性心肌梗死，高血压病3级。手术：PCI术。",
        }, headers=headers)
        coding = r.json()
        print(f"主要诊断: {coding['primary_diagnosis']['name']} ({coding['primary_diagnosis']['code']})")

        # 3. DRG 分组
        r = await client.post("/drg/group", json={
            "patient_age": 65,
            "patient_gender": "male",
            "primary_diagnosis_code": coding["primary_diagnosis"]["code"],
            "procedure_codes": [p["code"] for p in coding.get("procedures", [])],
        }, headers=headers)
        drg = r.json()
        print(f"DRG: {drg['drg_code']}, 预估支付: {drg['estimated_payment']}")

        # 4. 质控
        r = await client.post("/qc/check", json={
            "record_id": 1,
            "record_type": "discharge",
            "content": "出院诊断：急性心肌梗死...",
            "coding_result": coding,
        }, headers=headers)
        qc = r.json()
        print(f"质控评分: {qc['qc_score']}, 缺陷数: {qc['total_issues']}")

import asyncio
asyncio.run(main())
```

### curl 完整流程示例

```bash
#!/bin/bash

BASE="http://localhost:8000/api/v1"

# 1. 登录
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -d "username=admin&password=123456" | jq -r '.access_token')

AUTH="Authorization: Bearer $TOKEN"

# 2. 编码
CODING=$(curl -s -X POST "$BASE/coding/auto-code" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{
    "record_id": 1,
    "record_type": "discharge",
    "content": "出院诊断：急性ST段抬高型心肌梗死（前壁），高血压病3级（极高危）。手术：PCI术。"
  }')

echo "编码结果:"
echo "$CODING" | jq '{primary: .primary_diagnosis.name, code: .primary_diagnosis.code, confidence: .total_confidence}'

# 提取主要诊断编码
PRI_CODE=$(echo "$CODING" | jq -r '.primary_diagnosis.code')

# 3. DRG 分组
DRG=$(curl -s -X POST "$BASE/drg/group" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{
    \"patient_age\": 65,
    \"patient_gender\": \"male\",
    \"primary_diagnosis_code\": \"$PRI_CODE\",
    \"procedure_codes\": [\"36.0700\"]
  }")

echo "DRG结果:"
echo "$DRG" | jq '{drg: .drg_code, name: .drg_name, weight: .weight, payment: .estimated_payment}'

# 4. 质控
QC=$(curl -s -X POST "$BASE/qc/check" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{
    \"record_id\": 1,
    \"record_type\": \"discharge\",
    \"content\": \"出院诊断：急性ST段抬高型心肌梗死（前壁），高血压病3级（极高危）。手术：PCI术。\"
  }")

echo "质控结果:"
echo "$QC" | jq '{score: .qc_score, total_issues: .total_issues, critical: .critical_count}'
```
