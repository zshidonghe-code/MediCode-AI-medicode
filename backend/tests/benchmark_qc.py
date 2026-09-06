"""MediCode QC defect-detection benchmark (injected known defects).

Why this benchmark exists
-------------------------
Coding accuracy needs an expert-labelled gold standard, which this project
does not have yet. Defect detection does not: a defect can be *injected* into
a synthetic record, which makes the expected answer unambiguous and lets us
measure true recall instead of guessing.

Design rules that keep the result honest
----------------------------------------
1. The base records are synthetic, never real patient data.
2. Defects are injected by this script, so the expected rule is known by
   construction and independent of the engine's own implementation.
3. A clean control group with no injected defects measures the false
   positive rate — an engine that flags everything would score 100% recall
   and be worthless.

Usage:
    cd backend && .venv/Scripts/python tests/benchmark_qc.py
    cd backend && .venv/Scripts/python tests/benchmark_qc.py --rebuild
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from src.services.icd_coder.coder import icd_coder  # noqa: E402
from src.services.nlp_engine.engine import nlp_parser  # noqa: E402
from src.services.qc_engine.engine import qc_engine  # noqa: E402

# The coding path queries SQLAlchemy with echo enabled; silence it so the
# benchmark report stays readable.
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

CASES_PATH = _ROOT / "tests" / "fixtures" / "competition_cases.json"
SEED = 20260906
PER_RULE = 20
CLEAN_CASES = 60

# Record types each rule is reachable from (mirrors _RULE_RECORD_TYPE_MAP).
RULE_RECORD_TYPES: dict[str, str] = {
    "QC-001": "discharge",
    "QC-002": "discharge",
    "QC-003": "discharge",
    "QC-004": "discharge",
    "QC-005": "surgery",
    "QC-006": "surgery",
    "QC-007": "surgery",
    "QC-101": "discharge",
    "QC-102": "discharge",
    "QC-103": "discharge",
    "QC-104": "discharge",
    "QC-201": "discharge",
    "QC-202": "discharge",
    "QC-301": "admission",
    "QC-302": "surgery",
    "QC-401": "discharge",
    "QC-402": "discharge",
}

RULE_DESCRIPTIONS: dict[str, str] = {
    "QC-001": "删除「出院诊断」段落",
    "QC-002": "删除「入院情况」段落",
    "QC-003": "删除「诊疗经过」段落",
    "QC-004": "删除「出院医嘱」段落",
    "QC-005": "手术记录缺少手术日期",
    "QC-006": "手术记录缺少手术名称",
    "QC-007": "手术记录缺少建议字段（手术经过/麻醉方式等）",
    "QC-101": "男性患者出现女性专有诊断（卵巢囊肿）",
    "QC-102": "编码含心血管手术但无循环系统诊断",
    "QC-103": "主要诊断为 Z 编码",
    "QC-104": "住院天数异常偏长（95 天）",
    "QC-201": "诊断编码名称的关键术语未出现在病历文本中",
    "QC-202": "病历提及高血压但未编码",
    "QC-301": "入院记录与记录日期相差超过 24 小时",
    "QC-302": "手术记录缺少可判断时效性的手术日期",
    "QC-401": "主要诊断为症状（发热）而非病因",
    "QC-402": "诊断使用口语化表达（感冒）",
}


@dataclass
class Department:
    """A synthetic clinical template used as the base for generated records."""

    key: str
    name: str
    complaint: str
    diagnosis: str
    diagnosis_code: str
    exam: str
    aux: str
    course: str
    advice: str
    surgery_name: str
    surgery_code: str


DEPARTMENTS: list[Department] = [
    Department(
        key="cardio",
        name="循环内科",
        complaint="持续性胸痛 3 小时，伴大汗",
        diagnosis="急性心肌梗死",
        diagnosis_code="I21.900",
        exam="BP 130/80mmHg，HR 82 次/分，律齐，各瓣膜听诊区未闻及病理性杂音",
        aux="心电图示 V1-V4 导联 ST 段抬高，肌钙蛋白 I 升高",
        course="入院后完善检查，给予抗血小板、抗凝、调脂等治疗，病情稳定",
        advice="1.阿司匹林 100mg 每日一次 2.氯吡格雷 75mg 每日一次 3.一月后门诊复查",
        surgery_name="冠状动脉药物洗脱支架植入术",
        surgery_code="36.0700",
    ),
    Department(
        key="resp",
        name="呼吸内科",
        complaint="发热、咳嗽、咳黄痰 5 天",
        diagnosis="社区获得性肺炎",
        diagnosis_code="J18.900",
        exam="T 38.6℃，左下肺可闻及湿啰音",
        aux="胸部 CT 示左下肺斑片状高密度影，血常规示 WBC 13.5×10^9/L",
        course="给予头孢曲松联合阿奇霉素抗感染、祛痰、补液等对症支持治疗",
        advice="1.注意休息 2.避免受凉 3.一周后复查血常规及胸片",
        surgery_name="胸腔闭式引流术",
        surgery_code="34.0400",
    ),
    Department(
        key="ortho",
        name="骨科",
        complaint="跌倒致右髋部疼痛、活动受限 2 小时",
        diagnosis="右股骨颈骨折",
        diagnosis_code="S72.000",
        exam="右下肢短缩外旋畸形，右髋部压痛明显，纵向叩击痛阳性",
        aux="X 线示右股骨颈骨折，Garden III 型，骨折端移位明显",
        course="入院后完善相关检查，于全麻下行右侧人工全髋关节置换术",
        advice="1.术后早期功能锻炼 2.预防深静脉血栓 3.一月后门诊复查",
        surgery_name="人工全髋关节置换术",
        surgery_code="81.5100",
    ),
    Department(
        key="gi",
        name="消化内科",
        complaint="转移性右下腹痛 12 小时",
        diagnosis="急性阑尾炎",
        diagnosis_code="K35.800",
        exam="右下腹麦氏点压痛、反跳痛明显，肠鸣音减弱",
        aux="腹部超声示阑尾增粗，直径约 11mm，血常规示中性粒细胞比例升高",
        course="完善术前检查后行腹腔镜阑尾切除术，术后抗感染治疗",
        advice="1.保持切口清洁干燥 2.清淡饮食 3.术后一周门诊复查",
        surgery_name="腹腔镜阑尾切除术",
        surgery_code="47.0100",
    ),
]

SURNAMES = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙"]
GIVEN = ["某", "某某"]
DOCTORS = ["王医生", "李医生", "张医生", "刘医生"]


@dataclass
class Case:
    id: str
    record_type: str
    department: str
    content: str
    patient_info: dict
    coding_override: dict | None = None
    coding_result: dict | None = None
    injected_defects: list[str] = field(default_factory=list)
    defect_description: str = ""


def _rand_patient(rng: random.Random) -> dict:
    return {
        "name": f"{rng.choice(SURNAMES)}{rng.choice(GIVEN)}",
        "gender": rng.choice(["male", "female"]),
        "age": rng.randint(32, 88),
        "days_of_stay": rng.randint(4, 14),
    }


def _dates(rng: random.Random) -> tuple[str, str]:
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return (f"2026-{month:02d}-{day:02d}", f"2026-{month:02d}-{min(day + 1, 28):02d}")


def build_discharge(dep: Department, pat: dict, rng: random.Random) -> str:
    admit, _discharge = _dates(rng)
    return (
        f"入院情况：患者因「{dep.complaint}」于 {admit} 入院。既往体健，"
        f"否认高血压、糖尿病等慢性病史，否认药物过敏史。\n"
        f"体格检查：{dep.exam}\n"
        f"辅助检查：{dep.aux}\n"
        f"入院诊断：{dep.diagnosis}\n"
        f"诊疗经过：{dep.course}\n"
        f"出院诊断：{dep.diagnosis}\n"
        f"出院医嘱：{dep.advice}\n"
    )


def build_surgery(dep: Department, pat: dict, rng: random.Random) -> str:
    admit, _ = _dates(rng)
    return (
        f"患者于 {admit} 在全身麻醉下接受手术治疗。\n"
        f"手术名称：{dep.surgery_name}\n"
        f"手术日期：{admit}\n"
        f"手术者：{rng.choice(DOCTORS)}\n"
        f"麻醉方式：全身麻醉\n"
        f"手术经过：常规消毒铺巾，按标准术式操作，手术顺利，出血量少。\n"
        f"术前诊断：{dep.diagnosis}\n"
        f"术后诊断：{dep.diagnosis}\n"
    )


def build_admission(dep: Department, pat: dict, rng: random.Random) -> str:
    admit, record = _dates(rng)
    return (
        f"入院记录\n"
        f"患者因「{dep.complaint}」入院。\n"
        f"入院日期：{admit}\n"
        f"记录日期：{record}\n"
        f"体格检查：{dep.exam}\n"
        f"辅助检查：{dep.aux}\n"
        f"初步诊断：{dep.diagnosis}\n"
    )


def _drop_section(content: str, header: str) -> str:
    """Remove one 段落 including its text, up to the next paragraph header."""
    pattern = re.compile(rf"^{re.escape(header)}[：:].*?(?=^[^\n]*[：:]|\Z)", re.M | re.S)
    stripped = pattern.sub("", content, count=1)
    return stripped if stripped.strip() else content


# --------------------------------------------------------------------------
# Defect injectors. Each mutates the case so that exactly one rule should fire.
# --------------------------------------------------------------------------


def _inj_missing_section(header: str):
    def apply(case: Case) -> None:
        case.content = _drop_section(case.content, header)

    return apply


def _inj_surgery_no_date(case: Case) -> None:
    case.content = re.sub(r"^手术日期：.*$\n?", "", case.content, count=1, flags=re.M)


def _inj_surgery_no_name(case: Case) -> None:
    case.content = re.sub(r"^手术名称：.*$\n?", "", case.content, count=1, flags=re.M)


def _inj_surgery_missing_recommended(case: Case) -> None:
    for field_name in ("手术经过", "术前诊断", "麻醉方式"):
        case.content = re.sub(rf"^{field_name}：.*$\n?", "", case.content, count=1, flags=re.M)


def _inj_gender_conflict(case: Case) -> None:
    case.patient_info["gender"] = "male"
    case.content = case.content.replace("既往体健，", "既往体健，门诊以「卵巢囊肿」收入院，")


def _inj_proc_diag_mismatch(case: Case) -> None:
    case.coding_override = {
        "primary_diagnosis": {"code": "J18.900", "name": "社区获得性肺炎"},
        "secondary_diagnoses": [],
        "procedures": [{"code": "36.0700", "name": "冠状动脉药物洗脱支架植入术"}],
    }


def _inj_primary_z_code(case: Case) -> None:
    case.coding_override = {
        "primary_diagnosis": {"code": "Z51.100", "name": "化学治疗"},
        "secondary_diagnoses": [],
        "procedures": [],
    }


def _inj_long_stay(case: Case) -> None:
    case.patient_info["days_of_stay"] = 95


def _inj_code_text_mismatch(case: Case) -> None:
    # Use a diagnosis from a *different* department, otherwise a cardio base
    # record paired with I21.900 contains no defect at all.
    other = next(d for d in DEPARTMENTS if d.name != case.department)
    case.coding_override = {
        "primary_diagnosis": {"code": other.diagnosis_code, "name": other.diagnosis},
        "secondary_diagnoses": [],
        "procedures": [],
    }


def _inj_missed_secondary(case: Case) -> None:
    case.content = case.content.replace(
        "否认高血压、糖尿病等慢性病史", "既往有高血压病史 10 年，规律服用氨氯地平"
    )
    case.coding_override = {
        "primary_diagnosis": {
            "code": case.department,
            "name": "placeholder",
        },
        "secondary_diagnoses": [],
        "procedures": [],
    }


def _inj_admission_timeliness(case: Case) -> None:
    case.content = re.sub(
        r"记录日期：(\d{4})-(\d{2})-(\d{2})",
        lambda m: f"记录日期：{m.group(1)}-{m.group(2)}-{min(int(m.group(3)) + 4, 28):02d}",
        case.content,
        count=1,
    )


def _inj_surgery_timeliness(case: Case) -> None:
    case.content = re.sub(r"\d{4}-\d{2}-\d{2}", "", case.content, count=1)
    case.content = "手术记录\n" + case.content


def _inj_symptom_as_primary(case: Case) -> None:
    case.coding_override = {
        "primary_diagnosis": {"code": "R50.900", "name": "发热"},
        "secondary_diagnoses": [],
        "procedures": [],
    }


def _inj_informal_term(case: Case) -> None:
    case.content = case.content.replace("既往体健，", "既往体健，患者自述近日感冒后症状加重，")


INJECTORS: dict[str, object] = {
    "QC-001": _inj_missing_section("出院诊断"),
    "QC-002": _inj_missing_section("入院情况"),
    "QC-003": _inj_missing_section("诊疗经过"),
    "QC-004": _inj_missing_section("出院医嘱"),
    "QC-005": _inj_surgery_no_date,
    "QC-006": _inj_surgery_no_name,
    "QC-007": _inj_surgery_missing_recommended,
    "QC-101": _inj_gender_conflict,
    "QC-102": _inj_proc_diag_mismatch,
    "QC-103": _inj_primary_z_code,
    "QC-104": _inj_long_stay,
    "QC-201": _inj_code_text_mismatch,
    "QC-202": _inj_missed_secondary,
    "QC-301": _inj_admission_timeliness,
    "QC-302": _inj_surgery_timeliness,
    "QC-401": _inj_symptom_as_primary,
    "QC-402": _inj_informal_term,
}

# Rules whose injector relies on a coding result that must reflect the case.
_CODING_FROM_DEPARTMENT = {"QC-202"}


def _build_case(rng: random.Random, case_id: str, record_type: str, defect: str | None) -> Case:
    dep = rng.choice(DEPARTMENTS)
    pat = _rand_patient(rng)
    if record_type == "surgery":
        content = build_surgery(dep, pat, rng)
    elif record_type == "admission":
        content = build_admission(dep, pat, rng)
    else:
        content = build_discharge(dep, pat, rng)

    case = Case(
        id=case_id,
        record_type=record_type,
        department=dep.name,
        content=content,
        patient_info=pat,
        injected_defects=[defect] if defect else [],
        defect_description=RULE_DESCRIPTIONS.get(defect, "") if defect else "无（对照组）",
    )
    if defect:
        injector = INJECTORS[defect]
        injector(case)  # type: ignore[operator]
        if defect in _CODING_FROM_DEPARTMENT and case.coding_override:
            case.coding_override["primary_diagnosis"] = {
                "code": dep.diagnosis_code,
                "name": dep.diagnosis,
            }
    return case


async def _attach_coding(case: Case) -> None:
    """Run the real coding pipeline so stored cases carry a genuine result."""
    if case.coding_override is not None:
        case.coding_result = case.coding_override
        return
    record = nlp_parser.parse(case.record_type, case.content)
    result = await icd_coder.auto_code(record)
    case.coding_result = {
        "primary_diagnosis": (
            {
                "code": result.primary_diagnosis.code,
                "name": result.primary_diagnosis.name,
            }
            if result.primary_diagnosis
            else None
        ),
        "secondary_diagnoses": [
            {"code": d.code, "name": d.name} for d in result.secondary_diagnoses
        ],
        "procedures": [{"code": p.code, "name": p.name} for p in result.procedures],
    }


def generate_cases() -> list[Case]:
    rng = random.Random(SEED)
    cases: list[Case] = []
    seq = 0
    for rule, record_type in RULE_RECORD_TYPES.items():
        for _ in range(PER_RULE):
            seq += 1
            cases.append(_build_case(rng, f"QCB-{seq:04d}", record_type, rule))
    for _ in range(CLEAN_CASES):
        seq += 1
        cases.append(
            _build_case(
                rng, f"QCB-{seq:04d}", rng.choice(["discharge", "surgery", "admission"]), None
            )
        )
    return cases


async def build_dataset() -> list[Case]:
    cases = generate_cases()
    for case in cases:
        await _attach_coding(case)
    return cases


def _dump(cases: list[Case]) -> None:
    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "id": c.id,
            "record_type": c.record_type,
            "department": c.department,
            "content": c.content,
            "patient_info": c.patient_info,
            "coding_result": c.coding_result,
            "injected_defects": c.injected_defects,
            "defect_description": c.defect_description,
        }
        for c in cases
    ]
    CASES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load() -> list[Case]:
    raw = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return [
        Case(
            id=item["id"],
            record_type=item["record_type"],
            department=item["department"],
            content=item["content"],
            patient_info=item["patient_info"],
            coding_result=item.get("coding_result"),
            injected_defects=item.get("injected_defects", []),
            defect_description=item.get("defect_description", ""),
        )
        for item in raw
    ]


async def run(cases: list[Case]) -> dict:
    per_rule: dict[str, dict[str, int]] = {
        rule: {"injected": 0, "detected": 0} for rule in RULE_RECORD_TYPES
    }
    clean_total = 0
    clean_flagged = 0
    false_positive_examples: list[str] = []
    latencies: list[float] = []

    for case in cases:
        started = time.perf_counter()
        result = await qc_engine.check(
            record_type=case.record_type,
            content=case.content,
            coding_result=case.coding_result,
            patient_info=case.patient_info,
            use_llm=False,
        )
        latencies.append((time.perf_counter() - started) * 1000)
        fired = {issue.rule_id for issue in result.issues}

        if case.injected_defects:
            rule = case.injected_defects[0]
            per_rule[rule]["injected"] += 1
            if rule in fired:
                per_rule[rule]["detected"] += 1
        else:
            clean_total += 1
            if fired:
                clean_flagged += 1
                if len(false_positive_examples) < 5:
                    false_positive_examples.append(f"{case.id}: {','.join(sorted(fired))}")

    return {
        "per_rule": per_rule,
        "clean_total": clean_total,
        "clean_flagged": clean_flagged,
        "false_positive_examples": false_positive_examples,
        "latency_ms": latencies,
    }


def _report(stats: dict, total_cases: int) -> None:
    per_rule = stats["per_rule"]
    print("=" * 78)
    print("  MediCode QC Defect-Detection Benchmark (injected known defects)")
    print("=" * 78)
    print(f"  Cases                 : {total_cases}")
    print(f"  Rules covered         : {len(per_rule)}")
    print(f"  Clean control cases   : {stats['clean_total']}")
    print("  LLM enhancement       : disabled (rule engine only)")
    print("-" * 78)
    print(f"  {'Rule':<8} {'Injected':>9} {'Detected':>9} {'Recall':>9}")
    print("-" * 78)

    total_injected = 0
    total_detected = 0
    covered = 0
    weak: list[tuple[str, float]] = []
    for rule in sorted(per_rule):
        injected = per_rule[rule]["injected"]
        detected = per_rule[rule]["detected"]
        total_injected += injected
        total_detected += detected
        recall = detected / injected if injected else 0.0
        if detected:
            covered += 1
        if recall < 1.0:
            weak.append((rule, recall))
        print(f"  {rule:<8} {injected:>9} {detected:>9} {recall * 100:>8.1f}%")

    print("-" * 78)
    overall = total_detected / total_injected if total_injected else 0.0
    latencies = stats["latency_ms"]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    clean_total = stats["clean_total"]
    clean_flagged = stats["clean_flagged"]
    fp_rate = clean_flagged / clean_total if clean_total else 0.0

    print(f"  Overall defect recall : {total_detected}/{total_injected} ({overall * 100:.1f}%)")
    print(f"  Rule coverage         : {covered}/{len(per_rule)} rules fired at least once")
    print(
        f"  False positive rate   : {clean_flagged}/{clean_total} clean cases "
        f"flagged ({fp_rate * 100:.1f}%)"
    )
    print(f"  Avg latency           : {avg_latency:.1f} ms")
    print("=" * 78)

    if stats["false_positive_examples"]:
        print("  False positive samples (clean cases that were flagged):")
        for example in stats["false_positive_examples"]:
            print(f"    - {example}")
    if weak:
        print("  Rules below 100% recall:")
        for rule, recall in weak:
            print(f"    - {rule} ({recall * 100:.1f}%) — {RULE_DESCRIPTIONS.get(rule, '')}")
    print("=" * 78)
    print("  Note: recall is measured against defects injected by this script.")
    print("  It is NOT a clinical accuracy figure and must not be presented as one.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the QC defect-detection benchmark")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="regenerate the case set instead of reusing the stored one",
    )
    args = parser.parse_args()

    if args.rebuild or not CASES_PATH.exists():
        print(f"Generating case set -> {CASES_PATH}")
        cases = await build_dataset()
        _dump(cases)
    else:
        cases = _load()

    stats = await run(cases)
    _report(stats, len(cases))


if __name__ == "__main__":
    asyncio.run(main())
