"""流水线演示数据种子脚本 — 生成全链路数据供仪表盘展示

Usage:
    python -m src.scripts.seed_pipeline_demo

数据量: ~100位患者 × ~100份病历 → 全链路编码+QC+DRG结果
"""

import asyncio, sys, os, random, hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from datetime import date, timedelta
from src.models.database import async_session
from src.models.patient import Patient, MedicalRecord, Gender, RecordType
from src.models.icd import CodingResult, DRGGroup
from src.models.qc import QCResult, QCSeverity
from src.config.settings import get_settings
from sqlalchemy import select, delete

# ─── 病例模板池 ─────────────────────────────────────────────────

CASE_TEMPLATES = [
    # (科室, 性别倾向, 年龄范围, 标题, 病历内容, 主诊编码, 主诊名称, 次诊列表, 手术列表, DRG编码, DRG权重, 住院天数范围)
    # 心内科 (12条)
    ("心血管内科", "male", (45, 78), "急性心肌梗死PCI术后出院小结",
     "因'持续性胸痛3小时'入院。ECG示V1-V4 ST段抬高，肌钙蛋白I升高。急诊行冠脉造影+前降支PCI术，植入药物洗脱支架1枚。出院诊断：急性心肌梗死，冠心病，高血压，2型糖尿病。",
     "I21.900", "急性心肌梗死",
     [("I25.100", "冠状动脉粥样硬化性心脏病"), ("I10.x00", "原发性高血压"), ("E11.900", "2型糖尿病")],
     [("36.0700", "冠状动脉药物洗脱支架植入")],
     "FC1", 3.74, (5, 10)),
    ("心血管内科", "female", (55, 82), "心力衰竭合并房颤出院小结",
     "因'反复胸闷气促1周加重2天'入院。BNP 2850pg/mL，心脏超声LVEF 38%。既往冠心病15年，高血压20年。出院诊断：慢性心力衰竭，冠心病，心房颤动，高血压。",
     "I50.900", "心力衰竭",
     [("I25.100", "冠状动脉粥样硬化性心脏病"), ("I48.900", "心房颤动和心房扑动"), ("I10.x00", "原发性高血压")],
     [],
     "FD1", 1.85, (7, 14)),
    ("心血管内科", "male", (50, 70), "不稳定型心绞痛出院小结",
     "因'反复胸痛1月加重1周'入院。冠脉CTA示前降支中段狭窄75%。行冠脉造影+药物球囊扩张术。出院诊断：不稳定型心绞痛，冠心病，高脂血症。",
     "I20.000", "不稳定型心绞痛",
     [("I25.100", "冠状动脉粥样硬化性心脏病"), ("E78.500", "高脂血症")],
     [("00.6600", "经皮冠状动脉腔内血管成形术")],
     "FC2", 2.55, (4, 8)),

    # 神经内科 (10条)
    ("神经内科", "male", (45, 75), "急性脑梗死溶栓后出院小结",
     "因'突发右侧肢体无力伴言语不清2小时'入院。MRI示左侧基底节区急性梗死灶。予rt-PA静脉溶栓治疗。出院诊断：急性脑梗死，高血压3级。",
     "I63.900", "脑梗死",
     [("I10.x03", "原发性高血压3级")],
     [],
     "BR1", 2.15, (8, 15)),
    ("神经内科", "female", (55, 80), "脑出血保守治疗后出院小结",
     "因'突发头痛伴呕吐3小时'入院。CT示右侧基底节区出血约15mL。保守治疗。出院诊断：脑出血，高血压3级。",
     "I61.900", "脑出血",
     [("I10.x03", "原发性高血压3级")],
     [],
     "BR2", 3.20, (12, 20)),
    ("神经内科", "male", (30, 60), "癫痫持续状态出院小结",
     "因'反复抽搐伴意识障碍2天'入院。EEG示双侧额叶尖慢波。予抗癫痫药物控制。出院诊断：癫痫，症状性癫痫。",
     "G40.900", "癫痫",
     [],
     [],
     "BL1", 1.10, (5, 10)),

    # 呼吸内科 (9条)
    ("呼吸内科", "female", (30, 65), "社区获得性肺炎出院小结",
     "因'发热咳嗽5天'入院。WBC 14.2×10⁹/L，CRP 98mg/L，胸片示右下肺片状渗出。抗感染治疗。出院诊断：社区获得性肺炎。",
     "J18.900", "肺炎",
     [],
     [],
     "ED1", 0.95, (6, 12)),
    ("呼吸内科", "male", (50, 78), "COPD急性加重出院小结",
     "因'反复咳痰喘10年加重3天'入院。肺功能FEV1/FVC 55%。既往吸烟40年。出院诊断：COPD急性加重，慢性呼吸衰竭。",
     "J44.100", "慢性阻塞性肺疾病急性加重",
     [("J96.900", "呼吸衰竭")],
     [],
     "ET1", 1.55, (8, 16)),
    ("呼吸内科", "female", (20, 50), "支气管哮喘急性发作出院小结",
     "因'反复喘息3年加重1天'入院。双肺哮鸣音。予激素+支扩剂治疗。出院诊断：支气管哮喘急性发作。",
     "J45.900", "支气管哮喘",
     [],
     [],
     "ET2", 0.85, (3, 7)),

    # 消化内科 (9条)
    ("消化内科", "male", (30, 60), "急性胰腺炎出院小结",
     "因'上腹持续性剧痛8小时'入院，向背部放射。血淀粉酶1520U/L。CT示胰腺肿胀伴渗出。出院诊断：急性胰腺炎，高脂血症。",
     "K85.900", "急性胰腺炎",
     [("E78.500", "高脂血症")],
     [],
     "HD1", 1.42, (8, 16)),
    ("消化内科", "female", (40, 70), "上消化道出血出院小结",
     "因'呕血黑便1天'入院。胃镜示十二指肠球部溃疡伴出血。予内镜下止血。出院诊断：十二指肠球部溃疡伴出血，慢性胃炎。",
     "K26.400", "十二指肠溃疡伴出血",
     [("K29.500", "慢性胃炎")],
     [("44.4300", "内镜下胃十二指肠止血术")],
     "GK1", 1.68, (5, 10)),
    ("消化内科", "male", (35, 65), "肝硬化腹水出院小结",
     "因'腹胀尿少1月加重1周'入院。超声示大量腹水，肝缩小。既往乙肝史20年。出院诊断：乙型肝炎肝硬化失代偿期，腹水。",
     "K74.600", "肝硬化",
     [("R18.900", "腹水"), ("B18.100", "慢性乙型肝炎")],
     [],
     "HL1", 2.35, (10, 20)),

    # 骨科 (9条)
    ("骨科", "female", (60, 85), "股骨颈骨折人工髋关节置换术后出院小结",
     "因'摔伤致右髋疼痛活动受限1天'入院。X线示右侧股骨颈骨折Garden IV型。行全髋关节置换术。出院诊断：股骨颈骨折，骨质疏松。",
     "S72.000", "股骨颈骨折",
     [("M81.900", "骨质疏松")],
     [("81.5100", "全髋关节置换术")],
     "IC1", 5.62, (10, 20)),
    ("骨科", "male", (20, 55), "胫腓骨骨折内固定术后出院小结",
     "因'车祸伤致左小腿肿痛畸形2小时'入院。X线示左侧胫腓骨中段粉碎性骨折。行切开复位内固定术。出院诊断：左侧胫腓骨骨折。",
     "S82.200", "胫腓骨骨折",
     [],
     [("79.3600", "胫腓骨骨折切开复位内固定术")],
     "ID1", 3.85, (8, 18)),
    ("骨科", "female", (50, 75), "腰椎间盘突出术后出院小结",
     "因'反复腰痛伴右下肢放射痛3月'入院。MRI示L4-5、L5-S1椎间盘突出。行椎间盘镜下髓核摘除术。出院诊断：腰椎间盘突出症。",
     "M51.100", "腰椎间盘突出症",
     [],
     [("80.5100", "椎间盘切除术")],
     "IB1", 2.45, (7, 14)),

    # 普外科 (9条)
    ("普外科", "male", (15, 55), "急性阑尾炎腹腔镜切除术后出院小结",
     "因'转移性右下腹痛1天'入院。McBurney点压痛反跳痛阳性。急诊行腹腔镜下阑尾切除术。出院诊断：急性阑尾炎。",
     "K35.900", "急性阑尾炎",
     [],
     [("47.0900", "阑尾切除术")],
     "GC1", 1.25, (3, 7)),
    ("普外科", "female", (35, 65), "胆囊结石腹腔镜胆囊切除术后出院小结",
     "因'反复右上腹痛1年加重2天'入院。超声示胆囊多发结石。行腹腔镜下胆囊切除术。出院诊断：胆囊结石伴胆囊炎。",
     "K80.100", "胆囊结石伴胆囊炎",
     [],
     [("51.2300", "腹腔镜下胆囊切除术")],
     "HC1", 1.55, (3, 8)),
    ("普外科", "male", (45, 70), "腹股沟疝修补术后出院小结",
     "因'右侧腹股沟可复性肿物2年'入院。行无张力疝修补术。出院诊断：右侧腹股沟斜疝，高血压。",
     "K40.900", "腹股沟疝",
     [("I10.x00", "原发性高血压")],
     [("53.0000", "腹股沟疝修补术")],
     "GE1", 0.95, (2, 5)),

    # 肾内科 (7条)
    ("肾内科", "male", (30, 65), "慢性肾病5期血液透析出院小结",
     "因'反复浮肿尿少3年加重1周'入院。肌酐856μmol/L，GFR 8mL/min。行血液透析治疗。出院诊断：慢性肾病5期，肾性贫血。",
     "N18.500", "慢性肾病5期",
     [("D64.900", "贫血"), ("I10.x00", "原发性高血压")],
     [],
     "LS1", 2.85, (7, 15)),
    ("肾内科", "female", (25, 55), "急性肾盂肾炎出院小结",
     "因'发热腰痛尿频3天'入院。尿镜检WBC满视野，尿培养大肠杆菌阳性。抗感染治疗。出院诊断：急性肾盂肾炎。",
     "N10.900", "急性肾盂肾炎",
     [],
     [],
     "LT1", 0.75, (5, 10)),

    # 内分泌科 (7条)
    ("内分泌科", "male", (40, 70), "2型糖尿病伴并发症出院小结",
     "因'多饮多尿多食伴消瘦2年加重1月'入院。HbA1c 9.8%，合并周围神经病变。调整降糖方案。出院诊断：2型糖尿病，糖尿病周围神经病变。",
     "E11.900", "2型糖尿病",
     [("G63.200", "糖尿病性周围神经病变"), ("I10.x00", "原发性高血压")],
     [],
     "KS1", 1.25, (6, 12)),
    ("内分泌科", "female", (35, 60), "甲状腺功能亢进出院小结",
     "因'心悸手抖多食消瘦3月'入院。FT3 FT4升高，TSH降低。予甲巯咪唑治疗。出院诊断：甲状腺功能亢进症。",
     "E05.900", "甲状腺功能亢进",
     [],
     [],
     "KT1", 0.85, (4, 8)),

    # 泌尿外科 (7条)
    ("泌尿外科", "male", (45, 75), "前列腺增生经尿道电切术后出院小结",
     "因'排尿困难进行性加重2年'入院。行TURP手术。出院诊断：前列腺增生。",
     "N40.900", "前列腺增生",
     [("I10.x00", "原发性高血压")],
     [("60.2100", "经尿道前列腺电切术")],
     "LD1", 1.35, (4, 9)),
    ("泌尿外科", "female", (35, 60), "输尿管结石ESWL术后出院小结",
     "因'右侧腰痛伴血尿2天'入院。CT示右侧输尿管上段结石约8mm。行体外冲击波碎石术。出院诊断：输尿管结石，肾积水。",
     "N20.100", "输尿管结石",
     [("N13.300", "肾积水")],
     [("98.5100", "体外冲击波碎石术")],
     "LD2", 0.72, (2, 5)),

    # 妇产科 (7条)
    ("妇产科", "female", (22, 42), "剖宫产术后出院小结",
     "因'孕39周头盆不称'入院。行子宫下段剖宫产术，娩出一活女婴，Apgar评分9-10分。出院诊断：单胎头位顺产，头盆不称。",
     "O82.900", "单胎头位顺产",
     [],
     [("74.0000", "子宫下段剖宫产术")],
     "OB1", 0.68, (3, 7)),
    ("妇产科", "female", (30, 55), "子宫肌瘤腹腔镜子宫切除术后出院小结",
     "因'经量增多经期延长3年'入院。超声示子宫多发性肌瘤，最大5cm。行腹腔镜下全子宫切除术。出院诊断：多发性子宫肌瘤。",
     "D25.900", "子宫平滑肌瘤",
     [],
     [("68.4100", "腹腔镜下全子宫切除术")],
     "OF1", 1.85, (5, 10)),

    # 肿瘤科 (7条)
    ("肿瘤科", "male", (45, 72), "肺癌化疗后出院小结",
     "因'肺癌术后第3周期辅助化疗'入院。行GP方案化疗，过程顺利。出院诊断：右肺上叶腺癌术后，化疗后。",
     "C34.100", "肺上叶恶性肿瘤",
     [],
     [],
     "RE1", 2.15, (6, 12)),
    ("肿瘤科", "female", (40, 65), "乳腺癌术后化疗出院小结",
     "因'右乳腺癌术后辅助化疗'入院。行TC方案第2周期化疗。出院诊断：右乳腺癌术后，化疗后。",
     "C50.900", "乳房恶性肿瘤",
     [],
     [],
     "RF1", 2.05, (4, 8)),

    # 眼科 (5条)
    ("眼科", "male", (55, 80), "白内障超声乳化术后出院小结",
     "因'双眼视力下降2年加重半年'入院。行右眼白内障超声乳化+人工晶体植入术。出院诊断：老年性白内障，2型糖尿病。",
     "H25.900", "老年性白内障",
     [("E11.900", "2型糖尿病")],
     [("13.4100", "白内障超声乳化+人工晶体植入术")],
     "CB1", 0.78, (2, 4)),

    # 耳鼻喉科 (5条)
    ("耳鼻喉科", "male", (20, 50), "慢性扁桃体炎扁桃体切除术后出院小结",
     "因'反复咽痛发热3年'入院。行双侧扁桃体切除术。出院诊断：慢性扁桃体炎。",
     "J35.000", "慢性扁桃体炎",
     [],
     [("28.2000", "扁桃体切除术")],
     "DA1", 0.58, (3, 5)),

    # 皮肤科 (4条)
    ("皮肤科", "female", (18, 55), "带状疱疹出院小结",
     "因'右侧胸背部皮疹伴疼痛5天'入院。皮疹呈带状分布。予抗病毒+神经营养治疗。出院诊断：带状疱疹。",
     "B02.900", "带状疱疹",
     [],
     [],
     "JA1", 0.55, (4, 8)),
]

# ─── QC缺陷预设 ──────────────────────────────────────────────

QC_ISSUE_POOL = [
    {"rule_id": "QC-004", "severity": "critical", "desc": "缺少出院医嘱部分", "suggestion": "出院小结必须包含出院医嘱"},
    {"rule_id": "QC-104", "severity": "major", "desc": "住院天数异常偏长，请确认是否有特殊原因", "suggestion": "住院天数与诊断/手术复杂度不匹配"},
    {"rule_id": "QC-201", "severity": "major", "desc": "诊断编码中的关键临床术语在病历文本中未找到", "suggestion": "ICD编码与病历中诊断描述不一致"},
    {"rule_id": "QC-001", "severity": "critical", "desc": "主要诊断为症状而非病因", "suggestion": "应选择病因为主要诊断"},
    {"rule_id": "QC-301", "severity": "minor", "desc": "诊断名称口语化，建议使用规范术语", "suggestion": "请使用ICD规范诊断名称"},
    {"rule_id": "QC-302", "severity": "minor", "desc": "缺少手术日期记录", "suggestion": "手术记录必须包含精确手术日期"},
    {"rule_id": "QC-005", "severity": "major", "desc": "入院记录超24小时完成", "suggestion": "入院记录应在患者入院24小时内完成"},
    {"rule_id": "QC-202", "severity": "major", "desc": "漏编次要诊断", "suggestion": "病历提及的慢性病应在次要诊断中完整编码"},
]


def _rng_age(given_range):
    lo, hi = given_range
    return random.randint(lo, hi)


def _rng_days(given_range):
    lo, hi = given_range
    return random.randint(lo, hi)


def _random_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))


async def seed_pipeline_demo():
    async with async_session() as db:
        # ── Clear existing demo data ────────────────────────────────────
        await db.execute(delete(QCResult))
        await db.execute(delete(CodingResult))
        await db.execute(delete(MedicalRecord))
        await db.execute(delete(Patient))
        await db.commit()

        # ── Step 1: Ensure DRG groups exist ──────────────────────────────
        drg_data = [
            ("FC1", "PCI+STEMI", 3.74, True),
            ("FC2", "PTCA", 2.55, True),
            ("FD1", "心力衰竭", 1.85, False),
            ("BR1", "脑梗死", 2.15, False),
            ("BR2", "脑出血", 3.20, False),
            ("BL1", "癫痫", 1.10, False),
            ("ED1", "肺炎", 0.95, False),
            ("ET1", "COPD急性加重", 1.55, False),
            ("ET2", "哮喘急性发作", 0.85, False),
            ("HD1", "急性胰腺炎", 1.42, False),
            ("GK1", "消化性溃疡出血", 1.68, True),
            ("HL1", "肝硬化腹水", 2.35, False),
            ("IC1", "髋关节置换", 5.62, True),
            ("ID1", "胫腓骨骨折内固定", 3.85, True),
            ("IB1", "椎间盘切除术", 2.45, True),
            ("GC1", "阑尾切除术", 1.25, True),
            ("HC1", "腹腔镜胆囊切除术", 1.55, True),
            ("GE1", "疝修补术", 0.95, True),
            ("LS1", "慢性肾病5期", 2.85, False),
            ("LT1", "急性肾盂肾炎", 0.75, False),
            ("KS1", "2型糖尿病并发症", 1.25, False),
            ("KT1", "甲状腺功能亢进", 0.85, False),
            ("LD1", "TURP手术", 1.35, True),
            ("LD2", "ESWL碎石", 0.72, True),
            ("OB1", "剖宫产", 0.68, True),
            ("OF1", "腹腔镜子宫切除术", 1.85, True),
            ("RE1", "肺癌化疗", 2.15, False),
            ("RF1", "乳腺癌化疗", 2.05, False),
            ("CB1", "白内障超声乳化", 0.78, True),
            ("DA1", "扁桃体切除术", 0.58, True),
            ("JA1", "带状疱疹", 0.55, False),
        ]
        # MDC prefix → organ system mapping (CHS-DRG 1.2)
        _drg_to_mdc = {
            "A": "MDCA", "B": "MDCA",  # 神经系统
            "C": "MDCC",                # 眼科
            "D": "MDCD",                # 耳鼻喉
            "E": "MDCD",                # 呼吸系统
            "F": "MDCE",                # 循环系统
            "G": "MDCG",                # 消化系统
            "H": "MDCG",                # 肝/胆/胰
            "I": "MDCI",                # 骨骼/肌肉
            "J": "MDCJ",                # 皮肤
            "K": "MDCK",                # 内分泌
            "L": "MDCL",                # 肾脏/泌尿
            "M": "MDCM",                # 男性生殖
            "N": "MDCN",                # 女性生殖
            "O": "MDCN",                # 女性生殖
            "R": "MDCR",                # 肿瘤
        }
        for code, name, weight, surgical in drg_data:
            existing = (await db.execute(select(DRGGroup).where(DRGGroup.code == code))).scalar_one_or_none()
            if not existing:
                prefix = code[0] if code else "X"
                mdc = _drg_to_mdc.get(prefix, "MDCZ")
                db.add(DRGGroup(code=code, name=name, mdc=mdc, adrg=code[:2],
                                is_surgical=surgical, weight=weight, rate=get_settings().drg_base_rate,
                                avg_days=weight * 3.5))
        await db.flush()

        # ── Step 2: Generate records across 3 months ─────────────────────
        total_records = 0
        total_coding = 0
        total_qc = 0
        patient_idx = 0

        # Duplicate template pool to reach ~100 entries
        expanded_pool = CASE_TEMPLATES * 4  # 28 × 4 = 112 templates
        random.shuffle(expanded_pool)
        expanded_pool = expanded_pool[:100]  # Take exactly 100

        for tmpl in expanded_pool:
            dept, gender_pref, age_range, title, content, pri_code, pri_name, secs, procs, drg_code, drg_weight, days_range = tmpl

            # Alternate gender but respect preference
            if gender_pref == "male":
                gender = random.choice([Gender.MALE, Gender.MALE, Gender.FEMALE])
            else:
                gender = random.choice([Gender.FEMALE, Gender.FEMALE, Gender.MALE])

            age = _rng_age(age_range)
            patient_idx += 1
            patient_id_str = f"P{20260000 + patient_idx:08d}"
            patient = Patient(
                patient_id=patient_id_str,
                name_hash=hashlib.sha256(f"demo_patient_{patient_idx}".encode()).hexdigest()[:64],
                gender=gender,
                age=age,
                birth_year=2026 - age,
            )
            db.add(patient)
            await db.flush()

            # Random admission date within Mar-May 2026
            adm_date = _random_date_in_range(date(2026, 3, 1), date(2026, 5, 20))
            stay_days = _rng_days(days_range)
            dis_date = adm_date + timedelta(days=stay_days)

            record = MedicalRecord(
                patient_id=patient.id,
                record_type=RecordType.DISCHARGE,
                title=f"{title}",
                content=f"入院情况：{content}\n出院医嘱：1.定期随访 2.药物治疗 3.康复指导",
                department=dept,
                doctor_hash=hashlib.sha256(f"demo_doctor_{random.randint(1,20)}".encode()).hexdigest()[:64],
                admission_date=adm_date,
                discharge_date=dis_date,
            )
            db.add(record)
            await db.flush()

            # Coding result with slight confidence variation
            confidence = round(random.uniform(0.85, 0.99), 2)
            coding = CodingResult(
                record_id=record.id,
                coder_type="ai",
                codes={
                    "primary": {"code": pri_code, "name": pri_name},
                    "secondary": [{"code": c, "name": n} for c, n in secs],
                    "procedures": [{"code": c, "name": n} for c, n in procs],
                    "drg_code": drg_code,
                    "drg_weight": drg_weight,
                },
                confidence_scores={"total": confidence},
                suggestions=[],
                revision=1,
                is_final=True,
            )
            db.add(coding)
            total_coding += 1 + len(secs) + len(procs)

            # ~20% of records get QC issues
            if random.random() < 0.20:
                num_issues = random.randint(1, 2)
                chosen = random.sample(QC_ISSUE_POOL, min(num_issues, len(QC_ISSUE_POOL)))
                for d in chosen:
                    qc = QCResult(
                        record_id=record.id,
                        rule_id=1,
                        severity=QCSeverity(d["severity"]),
                        line_snippet=d["desc"][:200],
                        suggestion=d["suggestion"],
                    )
                    db.add(qc)
                    total_qc += 1

            total_records += 1

        await db.commit()

        # ── Step 3: Summarize ────────────────────────────────────────────
        patient_count = (await db.execute(select(Patient))).scalars().all()
        record_count = (await db.execute(select(MedicalRecord))).scalars().all()
        coding_count = (await db.execute(select(CodingResult))).scalars().all()
        qc_count = (await db.execute(select(QCResult))).scalars().all()

        print(f"Pipeline demo seed complete!")
        print(f"  Patients:  {len(patient_count)}")
        print(f"  Records:   {len(record_count)}")
        print(f"  Codings:   {len(coding_count)} ({total_coding} codes)")
        print(f"  QC issues: {len(qc_count)}")
        print(f"  DRG groups:{len(drg_data)}")


if __name__ == "__main__":
    asyncio.run(seed_pipeline_demo())
