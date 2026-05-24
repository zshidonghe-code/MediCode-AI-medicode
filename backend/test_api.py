import requests, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

payload = {
    "record_id": 1,
    "record_type": "discharge",
    "content": (
        "主诉：胸痛3小时。"
        "现病史：患者3小时前无明显诱因出现持续性胸骨后压榨样疼痛，伴大汗。"
        "既往有高血压病史10年，2型糖尿病病史5年，否认肝炎病史。"
        "体格检查：T36.5℃，P78次/分，BP160/95mmHg。"
        "辅助检查：心电图示V1-V4导联ST段弓背向上抬高，肌钙蛋白I升高。"
        "初步诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，2型糖尿病，原发性高血压。"
        "诊疗计划：拟行PCI术。"
    )
}

r = requests.post("http://localhost:8000/api/v1/coding/auto-code", json=payload)
data = r.json()

print("=" * 60)
print("PRIMARY DIAGNOSIS:")
if data.get("primary_diagnosis"):
    p = data["primary_diagnosis"]
    print(f"  {p['code']} - {p['name']} (conf={p['confidence']})")

print("\nSECONDARY DIAGNOSES:")
for item in data.get("secondary_diagnoses", []):
    print(f"  {item['code']} - {item['name']} (conf={item['confidence']})")

print("\nPROCEDURES:")
for item in data.get("procedures", []):
    print(f"  {item['code']} - {item['name']} (conf={item['confidence']})")

print(f"\nTotal Confidence: {data.get('total_confidence')}")
print(f"Processing Time: {data.get('processing_time_ms')}ms")
print("=" * 60)
