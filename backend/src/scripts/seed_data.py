"""数据库种子脚本 —— 填充ICD编码、DRG分组、质控规则和演示数据

Usage:
    python -m src.scripts.seed_data
"""

import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.models.database import async_session, engine, Base
from src.models.icd import ICDCode, ICDVersion, DRGGroup
from src.models.patient import Patient, MedicalRecord, Gender, RecordType
from src.models.qc import QCRule, QCSeverity, QCRuleType
from sqlalchemy import delete, func, select
from datetime import date


# 从统一的 JSON 数据文件加载 ICD 编码
_DATA_DIR = Path(__file__).parent.parent / "data"


async def seed_reference_data_if_needed() -> bool:
    """Seed each reference dataset independently and report whether work was done."""
    async with async_session() as session:
        counts = {
            "icd_codes": (await session.execute(select(func.count()).select_from(ICDCode))).scalar() or 0,
            "drg_groups": (await session.execute(select(func.count()).select_from(DRGGroup))).scalar() or 0,
            "qc_rules": (await session.execute(select(func.count()).select_from(QCRule))).scalar() or 0,
        }

    seeded = False
    if counts["icd_codes"] == 0:
        await seed_icd_codes()
        seeded = True
    if counts["drg_groups"] == 0:
        await seed_drg_groups()
        seeded = True
    if counts["qc_rules"] == 0:
        await seed_qc_rules()
        seeded = True
    return seeded


def _load_icd_json(filename: str) -> list[dict]:
    path = _DATA_DIR / filename
    if not path.exists():
        print(f"WARNING: ICD data file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_icd_codes():
    """Seed ICD diagnosis and procedure codes from unified JSON data."""
    async with async_session() as session:
        # Check existing
        result = await session.execute(select(ICDCode).limit(1))
        if result.scalars().first():
            print("[SKIP] ICD codes already seeded")
            return

        codes = []
        for item in _load_icd_json("icd_diagnoses.json"):
            codes.append(ICDCode(
                code=item["code"], name=item["name"],
                category=item.get("category", ""),
                version=ICDVersion.ICD10_CLINICAL,
                py_code=item.get("py", ""),
                search_terms={"alias": item.get("aliases", [])},
            ))

        for item in _load_icd_json("icd_procedures.json"):
            codes.append(ICDCode(
                code=item["code"], name=item["name"],
                category=item.get("category", "手术操作"),
                version=ICDVersion.ICD9_CM3,
                py_code=item.get("py", ""),
                search_terms={"alias": item.get("aliases", [])},
            ))

        session.add_all(codes)
        await session.commit()
        diag_count = len(_load_icd_json("icd_diagnoses.json"))
        proc_count = len(_load_icd_json("icd_procedures.json"))
        print(f"[OK] Seeded {len(codes)} ICD codes ({diag_count} diagnoses + {proc_count} procedures)")


async def seed_drg_groups():
    """Seed DRG group definitions"""
    async with async_session() as session:
        result = await session.execute(select(DRGGroup).limit(1))
        if result.scalars().first():
            print("[SKIP] DRG groups already seeded")
            return

        drg_defs = [
            # MDCE 循环系统
            ("FC13", "PCI手术，伴MCC/CC", "MDCE", "FC1", True, 3.80, 12000, 13.5),
            ("FC15", "PCI手术，不伴MCC/CC", "MDCE", "FC1", True, 3.40, 12000, 10.2),
            ("FR11", "急性心肌梗死，伴MCC", "MDCE", "FR1", False, 2.50, 12000, 14.0),
            ("FR13", "急性心肌梗死，伴CC", "MDCE", "FR1", False, 1.80, 12000, 11.0),
            ("FR15", "急性心肌梗死，不伴MCC/CC", "MDCE", "FR1", False, 1.30, 12000, 8.0),
            ("FS11", "心力衰竭，伴MCC", "MDCE", "FS1", False, 1.60, 12000, 12.0),
            ("FT15", "高血压，不伴MCC/CC", "MDCE", "FT1", False, 0.65, 12000, 7.0),
            ("FU15", "冠心病，不伴MCC/CC", "MDCE", "FU1", False, 0.85, 12000, 7.5),
            ("FV15", "心律失常，不伴MCC/CC", "MDCE", "FV1", False, 0.80, 12000, 6.5),
            # MDCD 呼吸系统
            ("ER11", "肺炎，伴MCC", "MDCD", "ER1", False, 1.30, 12000, 14.0),
            ("ER13", "肺炎，伴CC", "MDCD", "ER1", False, 1.15, 12000, 11.0),
            ("ER15", "肺炎，不伴MCC/CC", "MDCD", "ER1", False, 0.95, 12000, 8.0),
            ("ES11", "COPD，伴MCC", "MDCD", "ES1", False, 1.40, 12000, 14.5),
            ("ES13", "COPD，伴CC", "MDCD", "ES1", False, 1.10, 12000, 10.0),
            ("ES15", "COPD，不伴MCC/CC", "MDCD", "ES1", False, 0.90, 12000, 7.5),
            ("ET15", "支气管哮喘", "MDCD", "ET1", False, 0.55, 12000, 5.5),
            ("EV11", "呼吸衰竭，伴MCC", "MDCD", "EV1", False, 2.00, 12000, 16.0),
            # MDCF 消化系统
            ("GC15", "阑尾切除术", "MDCF", "GC1", True, 1.00, 12000, 5.0),
            ("GR15", "胃炎/溃疡", "MDCF", "GR1", False, 0.70, 12000, 6.0),
            ("GS15", "肠炎/肠梗阻", "MDCF", "GS1", False, 0.75, 12000, 7.0),
            # MDCG 肝胆胰
            ("HB13", "胆囊切除术，伴CC", "MDCG", "HB1", True, 2.00, 12000, 8.0),
            ("HB15", "胆囊切除术，不伴MCC/CC", "MDCG", "HB1", True, 1.80, 12000, 6.0),
            ("HR13", "肝炎/肝硬化，伴CC", "MDCG", "HR1", False, 1.20, 12000, 10.0),
            ("HS15", "胆道疾病", "MDCG", "HS1", False, 0.85, 12000, 7.0),
            ("HT15", "胰腺炎", "MDCG", "HT1", False, 1.10, 12000, 8.0),
            # MDCH 骨骼肌肉
            ("IA13", "髋关节置换，伴CC", "MDCH", "IA1", True, 5.00, 12000, 18.0),
            ("IA15", "髋关节置换，不伴MCC/CC", "MDCH", "IA1", True, 4.50, 12000, 15.0),
            ("IB15", "膝关节置换", "MDCH", "IB1", True, 4.30, 12000, 14.0),
            ("ID15", "骨折内固定术", "MDCH", "ID1", True, 2.20, 12000, 10.0),
            ("IS15", "关节炎", "MDCH", "IS1", False, 0.75, 12000, 7.0),
            # MDCA 神经系统
            ("BR15", "脑卒中", "MDCA", "BR1", False, 1.60, 12000, 14.0),
            ("BU15", "帕金森病", "MDCA", "BU1", False, 0.90, 12000, 8.0),
            # MDCK 泌尿
            ("LB15", "经尿道手术", "MDCK", "LB1", True, 1.10, 12000, 6.0),
            ("LR15", "慢性肾病", "MDCK", "LR1", False, 0.90, 12000, 8.0),
            ("LS15", "尿路感染/结石", "MDCK", "LS1", False, 0.55, 12000, 4.0),
            # MDCJ 内分泌
            ("KR15", "糖尿病", "MDCJ", "KR1", False, 0.75, 12000, 7.0),
            ("KS15", "甲状腺疾病", "MDCJ", "KS1", False, 0.65, 12000, 5.0),
            # MDCN 产科
            ("OA15", "剖宫产", "MDCN", "OA1", True, 1.05, 12000, 5.5),
            ("OR15", "正常分娩", "MDCN", "OR1", False, 0.60, 12000, 3.5),
            # MDCP 血液
            ("QR15", "贫血", "MDCP", "QR1", False, 0.60, 12000, 5.0),
            # MDCQ 感染
            ("RR15", "传染病", "MDCQ", "RR1", False, 0.85, 12000, 8.0),
            # MDCL 男性
            ("MR15", "前列腺增生", "MDCL", "MR1", False, 0.60, 12000, 5.0),
        ]

        groups = []
        for code, name, mdc, adrg, is_surg, weight, rate, avg_days in drg_defs:
            groups.append(DRGGroup(
                code=code, name=name, mdc=mdc, adrg=adrg,
                is_surgical=is_surg, weight=weight, rate=rate,
                avg_days=avg_days,
            ))

        session.add_all(groups)
        await session.commit()
        print(f"[OK] Seeded {len(groups)} DRG groups")


async def seed_qc_rules():
    """Seed QC rules into database"""
    async with async_session() as session:
        result = await session.execute(select(QCRule).limit(1))
        if result.scalars().first():
            print("[SKIP] QC rules already seeded")
            return

        rules = [
            # 完整性
            ("出院小结完整性-出院诊断", QCRuleType.COMPLETENESS, QCSeverity.CRITICAL,
             "出院小结必须包含出院诊断", "_check_section_exists", {"section": "出院诊断"}),
            ("出院小结完整性-入院情况", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "出院小结必须包含入院情况描述", "_check_section_exists", {"section": "入院情况"}),
            ("出院小结完整性-诊疗经过", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "出院小结必须包含诊疗经过", "_check_section_exists", {"section": "诊疗经过"}),
            ("出院小结完整性-出院医嘱", QCRuleType.COMPLETENESS, QCSeverity.CRITICAL,
             "出院小结必须包含出院医嘱", "_check_section_exists", {"section": "出院医嘱"}),
            ("手术记录完整性-手术日期", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "手术记录必须包含手术日期", "_check_surgery_date", {}),
            ("手术记录完整性-手术名称", QCRuleType.COMPLETENESS, QCSeverity.CRITICAL,
             "手术记录必须包含手术名称且与编码一致", "_check_surgery_name", {}),
            ("入院记录完整性-主诉", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "入院记录必须包含主诉", "_check_section_exists", {"section": "主诉"}),
            ("入院记录完整性-现病史", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "入院记录必须包含现病史", "_check_section_exists", {"section": "现病史"}),
            ("入院记录完整性-既往史", QCRuleType.COMPLETENESS, QCSeverity.MINOR,
             "入院记录必须包含既往史", "_check_section_exists", {"section": "既往史"}),
            ("入院记录完整性-体格检查", QCRuleType.COMPLETENESS, QCSeverity.MAJOR,
             "入院记录必须包含体格检查", "_check_section_exists", {"section": "查体"}),
            # 逻辑一致性
            ("诊断与性别一致性", QCRuleType.LOGIC, QCSeverity.CRITICAL,
             "诊断编码与患者性别不一致", "_check_diagnosis_gender_consistency", {}),
            ("手术与诊断一致性", QCRuleType.LOGIC, QCSeverity.CRITICAL,
             "手术部位与诊断部位不一致", "_check_surgery_diagnosis_consistency", {}),
            ("主要诊断选择正确性", QCRuleType.LOGIC, QCSeverity.CRITICAL,
             "主要诊断应选择对健康危害最大、消耗医疗资源最多的诊断", "_check_primary_diagnosis_validity", {}),
            ("住院天数逻辑检查", QCRuleType.LOGIC, QCSeverity.MAJOR,
             "住院天数与诊断/手术复杂度不匹配", "_check_length_of_stay", {}),
            ("主要诊断与次要诊断重复", QCRuleType.LOGIC, QCSeverity.MINOR,
             "主要诊断与次要诊断不应出现编码重复", "_check_duplicate_diag", {}),
            ("手术日期在住院期间内", QCRuleType.LOGIC, QCSeverity.MAJOR,
             "手术日期应在入院日期和出院日期之间", "_check_surgery_date_range", {}),
            # 编码一致性
            ("诊断编码与诊断文本匹配", QCRuleType.CODING, QCSeverity.MAJOR,
             "ICD编码与病历中诊断描述不一致", "_check_code_text_consistency", {}),
            ("漏编次要诊断检查", QCRuleType.CODING, QCSeverity.MAJOR,
             "病历中存在可能遗漏的次要诊断编码", "_check_missing_secondary_diagnosis", {}),
            ("手术操作编码完整性", QCRuleType.CODING, QCSeverity.CRITICAL,
             "有手术记录则必须有对应的手术操作编码", "_check_procedure_coding", {}),
            ("MCC/CC编码完整性", QCRuleType.CODING, QCSeverity.MAJOR,
             "存在重要合并症时应正确编码以反映疾病严重程度", "_check_cc_coding", {}),
            # 时效性
            ("入院记录24h完成", QCRuleType.TIMELINESS, QCSeverity.MINOR,
             "入院记录应在入院后24小时内完成", "_check_admission_record_timeliness", {"hours": 24}),
            ("手术记录术后即时完成", QCRuleType.TIMELINESS, QCSeverity.MINOR,
             "手术记录应在术后24小时内完成", "_check_surgery_record_timeliness", {"hours": 24}),
            ("出院小结及时完成", QCRuleType.TIMELINESS, QCSeverity.MINOR,
             "出院小结应在出院后24小时内完成", "_check_discharge_timeliness", {"hours": 24}),
            # 规范表达
            ("主要诊断为病因诊断", QCRuleType.NORMALIZATION, QCSeverity.MAJOR,
             "主要诊断应为病因诊断，不应选择症状或体征作为主要诊断", "_check_primary_is_etiology", {}),
            ("诊断名称规范化", QCRuleType.NORMALIZATION, QCSeverity.MINOR,
             "诊断名称应使用标准医学名词，避免口语化或简写", "_check_diagnosis_naming", {}),
            ("手术名称规范化", QCRuleType.NORMALIZATION, QCSeverity.MINOR,
             "手术名称应使用标准医学术语", "_check_surgery_naming", {}),
            ("病历无复制粘贴痕迹", QCRuleType.NORMALIZATION, QCSeverity.MINOR,
             "病历内容不应有大量重复的复制粘贴文本", "_check_copy_paste", {}),
        ]

        db_rules = []
        for name, rtype, severity, desc, check_fn, params in rules:
            db_rules.append(QCRule(
                rule_name=name, rule_type=rtype, severity=severity,
                description=desc, check_function=check_fn, params=params,
            ))

        session.add_all(db_rules)
        await session.commit()
        print(f"[OK] Seeded {len(db_rules)} QC rules")


async def seed_demo_patients():
    """Seed demo patient and medical record data"""
    async with async_session() as session:
        result = await session.execute(select(Patient).limit(1))
        if result.scalars().first():
            print("[SKIP] Demo patients already seeded")
            return

        demo_patients = [
            {
                "patient_id": "P20240001",
                "name_hash": "a1b2c3d4e5",
                "gender": Gender.MALE,
                "age": 68, "birth_year": 1956,
            },
            {
                "patient_id": "P20240002",
                "name_hash": "f6g7h8i9j0",
                "gender": Gender.MALE,
                "age": 72, "birth_year": 1952,
            },
            {
                "patient_id": "P20240003",
                "name_hash": "k1l2m3n4o5",
                "gender": Gender.FEMALE,
                "age": 65, "birth_year": 1959,
            },
            {
                "patient_id": "P20240004",
                "name_hash": "p6q7r8s9t0",
                "gender": Gender.MALE,
                "age": 55, "birth_year": 1969,
            },
            {
                "patient_id": "P20240005",
                "name_hash": "u1v2w3x4y5",
                "gender": Gender.FEMALE,
                "age": 45, "birth_year": 1979,
            },
            {
                "patient_id": "P20240006",
                "name_hash": "z6a7b8c9d0",
                "gender": Gender.MALE,
                "age": 70, "birth_year": 1954,
            },
            {
                "patient_id": "P20240007",
                "name_hash": "e1f2g3h4i5",
                "gender": Gender.FEMALE,
                "age": 58, "birth_year": 1966,
            },
            {
                "patient_id": "P20240008",
                "name_hash": "j6k7l8m9n0",
                "gender": Gender.MALE,
                "age": 62, "birth_year": 1962,
            },
            {
                "patient_id": "P20240009",
                "name_hash": "o1p2q3r4s5",
                "gender": Gender.FEMALE,
                "age": 38, "birth_year": 1986,
            },
            {
                "patient_id": "P20240010",
                "name_hash": "t6u7v8w9x0",
                "gender": Gender.MALE,
                "age": 75, "birth_year": 1949,
            },
        ]

        patients = []
        for p in demo_patients:
            patients.append(Patient(**p))
        session.add_all(patients)
        await session.flush()
        pid_map = {p.patient_id: p.id for p in patients}

        # Demo medical records
        demo_records = [
            {
                "patient_id": "P20240001",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-急性心肌梗死PCI术后",
                "content": "患者因急性ST段抬高型心肌梗死（前壁）入院，行急诊PCI术，于前降支植入药物洗脱支架1枚。住院12天，术后恢复良好出院。",
                "department": "心血管内科",
                "doctor_hash": "doc_001",
                "admission_date": date(2024, 1, 5),
                "discharge_date": date(2024, 1, 17),
            },
            {
                "patient_id": "P20240002",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-COPD急性加重",
                "content": "患者因COPD急性加重入院，合并肺部感染和II型呼吸衰竭。给予抗感染、无创正压通气等治疗。住院15天，病情好转出院。",
                "department": "呼吸内科",
                "doctor_hash": "doc_002",
                "admission_date": date(2024, 1, 10),
                "discharge_date": date(2024, 1, 25),
            },
            {
                "patient_id": "P20240003",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-左股骨颈骨折术后",
                "content": "患者因摔伤致左股骨颈骨折（Garden IV型），行左侧人工全髋关节置换术。住院18天，术后康复良好。",
                "department": "骨科",
                "doctor_hash": "doc_003",
                "admission_date": date(2024, 2, 3),
                "discharge_date": date(2024, 2, 21),
            },
            {
                "patient_id": "P20240004",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-胆囊结石伴胆囊炎",
                "content": "患者因右上腹疼痛入院，B超示胆囊结石伴急性胆囊炎。行腹腔镜胆囊切除术，术后恢复顺利。住院7天。",
                "department": "普外科",
                "doctor_hash": "doc_004",
                "admission_date": date(2024, 2, 15),
                "discharge_date": date(2024, 2, 22),
            },
            {
                "patient_id": "P20240005",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-子宫肌瘤",
                "content": "患者因子宫肌瘤入院，行腹腔镜子宫肌瘤切除术。住院8天，术后恢复良好。",
                "department": "妇产科",
                "doctor_hash": "doc_005",
                "admission_date": date(2024, 3, 1),
                "discharge_date": date(2024, 3, 9),
            },
            {
                "patient_id": "P20240006",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-脑梗死",
                "content": "患者因突发右侧肢体无力入院，CT示左侧基底节区脑梗死。给予抗血小板、改善循环等治疗。住院14天。",
                "department": "神经内科",
                "doctor_hash": "doc_006",
                "admission_date": date(2024, 3, 10),
                "discharge_date": date(2024, 3, 24),
            },
            {
                "patient_id": "P20240007",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-2型糖尿病伴肾病",
                "content": "患者因血糖控制不佳入院，合并糖尿病肾病。调整降糖方案，给予肾保护治疗。住院10天。",
                "department": "内分泌科",
                "doctor_hash": "doc_007",
                "admission_date": date(2024, 3, 15),
                "discharge_date": date(2024, 3, 25),
            },
            {
                "patient_id": "P20240008",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-前列腺增生",
                "content": "患者因排尿困难入院，行经尿道前列腺电切术。住院9天，排尿功能明显改善。",
                "department": "泌尿外科",
                "doctor_hash": "doc_008",
                "admission_date": date(2024, 4, 1),
                "discharge_date": date(2024, 4, 10),
            },
            {
                "patient_id": "P20240009",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-剖宫产",
                "content": "患者因胎儿窘迫行剖宫产术。住院5天，母婴平安出院。",
                "department": "妇产科",
                "doctor_hash": "doc_005",
                "admission_date": date(2024, 4, 5),
                "discharge_date": date(2024, 4, 10),
            },
            {
                "patient_id": "P20240010",
                "record_type": RecordType.DISCHARGE,
                "title": "出院小结-心力衰竭",
                "content": "患者因胸闷气促入院，诊断为慢性心力衰竭急性加重。给予利尿、强心、扩血管等治疗。住院16天，病情稳定出院。",
                "department": "心血管内科",
                "doctor_hash": "doc_001",
                "admission_date": date(2024, 4, 8),
                "discharge_date": date(2024, 4, 24),
            },
        ]

        records = []
        for r in demo_records:
            r_copy = dict(r)
            r_copy["patient_id"] = pid_map[r["patient_id"]]
            records.append(MedicalRecord(**r_copy))
        session.add_all(records)
        await session.commit()
        print(f"[OK] Seeded {len(patients)} patients + {len(records)} medical records")


async def main():
    print("=" * 50)
    print("  MediCode Database Seed Script")
    print("=" * 50)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_icd_codes()
    await seed_drg_groups()
    await seed_qc_rules()
    await seed_demo_patients()

    print("=" * 50)
    print("  Seed complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
