"""LLM prompt templates for medical coding tasks."""

ICD_CODING_SYSTEM = """你是一个专业的ICD-10和ICD-9-CM-3编码专家。你的任务是：
1. 根据诊断文本选择最合适的ICD-10编码
2. 根据手术文本选择最合适的ICD-9-CM-3编码
3. 判断编码之间的主次关系和逻辑一致性

注意：
- 主要诊断应该是患者本次住院最主要治疗的疾病
- 次要诊断按重要性排序
- 手术编码必须与诊断有逻辑关联
- 遵循CHS-DRG分组方案的编码规则"""

QC_SYSTEM = """你是一个病历质控审核专家。检查编码一致性、诊断合理性和完整性。
仅返回要求的JSON格式，不要额外解释。"""

CODE_RECOMMEND_PROMPT = """请分析以下诊断/手术文本，并从候选编码中选择最合适的编码。

## 病历摘要
{context}

## 待编码文本
{entity_text}

## 候选编码
{candidates}

## 任务
请选择最合适的编码并说明理由。如果候选编码都不合适，请给出新的建议编码。

返回JSON格式：
{{"selected_code": "编码", "selected_name": "名称", "confidence": 0.0-1.0, "reasoning": "理由"}}"""


QC_SURGERY_DIAG_CONSISTENCY = """检查手术操作与诊断之间是否存在逻辑矛盾。

## 诊断列表
{diagnoses}

## 手术操作
{surgeries}

## 任务
判断每个手术是否有对应的合理诊断支持。例如：
- "剖宫产术" 需要有产科相关诊断
- "阑尾切除术" 需要有阑尾炎相关诊断
- 男性患者不能有妇科手术

返回JSON格式：
{{"consistent": true/false, "issues": [{{"surgery": "手术名", "problem": "问题描述", "severity": "CRITICAL/MAJOR/MINOR"}}]}}"""


QC_PRIMARY_DIAGNOSIS_VALIDITY = """检查主要诊断的选择是否合理。

## 病历摘要
{content}

## 当前主要诊断
{primary_diagnosis}

## 所有诊断
{all_diagnoses}

## 任务
判断主要诊断是否是本次住院最主要治疗的疾病，是否有更合适的诊断被遗漏。

返回JSON格式：
{{"valid": true/false, "suggested_primary": "建议的主诊断", "reasoning": "理由", "severity": "CRITICAL/MAJOR/OK"}}"""


QC_CODE_TEXT_MATCH = """检查诊断编码与实际诊断文本是否匹配。

## 编码
{code} - {code_name}

## 病历中的诊断文本
{diagnosis_text}

## 任务
判断该编码是否准确反映了病历中的诊断描述。编码可能过于笼统或过于特异。

返回JSON格式：
{{"match": true/false, "score": 0.0-1.0, "suggested_code": "更合适的编码", "reasoning": "理由"}}"""


QC_CODE_TEXT_MATCH_BATCH = """批量检查以下诊断编码与病历文本的匹配度。

## 病历摘要
{content}

## 待检查的编码-文本对
{pairs}

## 任务
对每一对诊断编码和文本，判断是否匹配。编码可能过于笼统或过于特异。

返回JSON格式：
{{"results": [{{"index": 数字, "code": "编码", "match": true/false, "score": 0.0-1.0, "reasoning": "理由"}}]}}"""


QC_MISSED_DIAGNOSIS = """检查病历中是否有诊断被遗漏编码。

## 病历摘要
{content}

## 已编码的诊断
{coded_diagnoses}

## 任务
找出病历中明确提到但未编码的诊断、检查报告提示的异常结果、既往史中的重要慢性病。

返回JSON格式：
{{"missed": [{{"diagnosis_text": "诊断文本", "suggested_code": "建议编码", "suggested_name": "编码名称", "reasoning": "从病历中找到的依据"}}]}}"""


DRG_ANALYSIS_PROMPT = """分析DRG分组结果并提供优化建议。

## 患者信息
{patient_info}

## 主要诊断
{primary_diagnosis}

## 次要诊断
{secondary_diagnoses}

## 手术操作
{procedures}

## 当前DRG分组
{current_drg}

## 任务
1. 检查次要诊断中是否有MCC/CC被遗漏或错误编码
2. 检查手术编码是否完整（有无遗漏关键操作）
3. 给出编码优化建议以准确反映病例复杂度

返回JSON格式：
{{"suggestions": [{{"type": "add_diagnosis/add_procedure/modify_code", "code": "编码", "reason": "理由", "estimated_weight_change": "+0.5"}}], "optimized_drg": "优化后的DRG", "optimized_weight": 0.0}}"""
