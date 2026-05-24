"""Full pipeline integration test: Coding → QC → DRG"""
import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CASE = {
    "record_id": 1,
    "record_type": "discharge",
    "content": (
        "入院情况：患者因'持续性胸痛3小时'入院，伴大汗。"
        "既往有高血压病史10年，2型糖尿病史5年，否认肝炎病史。"
        "体格检查：BP160/95mmHg，HR78次/分。"
        "辅助检查：ECG示V1-V4导联ST段弓背向上抬高，肌钙蛋白I升高。"
        "入院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
        "诊疗经过：急诊行冠状动脉造影+前降支PCI术，植入药物洗脱支架1枚。"
        "出院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
        "出院医嘱：1.阿司匹林100mg qd 2.氯吡格雷75mg qd 3.阿托伐他汀20mg qn 4.一月后复查"
    ),
}

def sep(title): print(f"\n{'='*60}\n  {title}\n{'='*60}")

# Step 1: ICD Coding
sep("STEP 1: ICD Coding")
r = requests.post("http://localhost:8000/api/v1/coding/auto-code", json=CASE)
coding = r.json()
print(f"Primary: {coding['primary_diagnosis']['code']} - {coding['primary_diagnosis']['name']}")
print(f"Secondaries: {len(coding['secondary_diagnoses'])}")
for s in coding['secondary_diagnoses']:
    print(f"  {s['code']} - {s['name']}")
print(f"Procedures: {len(coding['procedures'])}")
for p in coding['procedures']:
    print(f"  {p['code']} - {p['name']}")
print(f"Confidence: {coding['total_confidence']} | Time: {coding['processing_time_ms']}ms")

# Step 2: QC Check
sep("STEP 2: QC Check")
r = requests.post("http://localhost:8000/api/v1/qc/check", json={
    **CASE,
    "coding_result": {
        "primary_diagnosis": coding['primary_diagnosis'],
        "secondary_diagnoses": coding['secondary_diagnoses'],
        "procedures": coding['procedures'],
    },
    "patient_info": {"gender": "male", "age": 65, "days_of_stay": 7},
})
qc = r.json()
print(f"QC Score: {qc['qc_score']} | Issues: {qc['total_issues']}")
for i in qc['issues']:
    print(f"  [{i['severity']}] {i['rule_id']}: {i['description']}")

# Step 3: DRG Grouping
sep("STEP 3: DRG Grouping")
r = requests.post("http://localhost:8000/api/v1/drg/group", json={
    "patient_age": 65,
    "patient_gender": "male",
    "primary_diagnosis_code": coding['primary_diagnosis']['code'],
    "secondary_diagnosis_codes": [s['code'] for s in coding['secondary_diagnoses']],
    "procedure_codes": [p['code'] for p in coding['procedures']],
    "days_of_stay": 7,
})
drg = r.json()
print(f"MDC: {drg['mdc']} - {drg['mdc_name']}")
print(f"ADRG: {drg['adrg']} - {drg['adrg_name']}")
print(f"DRG: {drg['drg_code']} - {drg['drg_name']}")
print(f"Surgical: {drg['is_surgical']} | Weight: {drg['weight']} | Rate: {drg['rate']}")
print(f"Estimated Payment: ¥{drg['estimated_payment']:,.0f}")
print(f"CC Flag: {drg['cc_flag']} | Complexity: {drg['patient_complexity']}")

# Summary
sep("PIPELINE SUMMARY")
print(f"Coding: {coding['primary_diagnosis']['code']} + {len(coding['secondary_diagnoses'])} sec + {len(coding['procedures'])} proc ({coding['processing_time_ms']}ms)")
print(f"QC: Score {qc['qc_score']}, {qc['total_issues']} issues")
print(f"DRG: {drg['drg_code']} (weight {drg['weight']}) -> ¥{drg['estimated_payment']:,.0f}")
