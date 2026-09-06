"""MediCode ICD Coding Engine Accuracy Benchmark

Directly measures the accuracy of the ICD coding engine against a set of
gold-standard test cases, without requiring a running server.

Usage:
    cd backend && .venv/Scripts/python tests/benchmark_accuracy.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Ensure backend src is on PYTHONPATH
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.services.icd_coder.coder import ICDCandidate, icd_coder  # noqa: E402
from src.services.icd_coder.scoring import PROCEDURE_REFINEMENTS, primary_score  # noqa: E402
from src.services.nlp_engine.engine import nlp_parser  # noqa: E402


def _dedup(candidates: list, key_fn=None):
    """Deduplicate by code, keeping highest-scoring entry."""
    if key_fn is None:

        def key_fn(c):
            return c.code

    best: dict[str, object] = {}
    for c in candidates:
        k = key_fn(c)
        if k not in best or getattr(c, "score", 0) > getattr(best[k], "score", 0):
            best[k] = c
    return list(best.values())


# ===========================================================================
# Gold-standard test cases
# ===========================================================================

TEST_CASES = [
    {
        "id": "CASE-01",
        "name": "AMI+PCI (循环/心血管)",
        "text": (
            "入院情况：患者因'持续性胸痛3小时'入院，伴大汗。"
            "既往有高血压病史10年，2型糖尿病史5年。"
            "体格检查：BP160/95mmHg，HR78次/分。"
            "辅助检查：ECG示V1-V4导联ST段弓背向上抬高，肌钙蛋白I升高。"
            "入院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
            "诊疗经过：急诊行冠状动脉造影+前降支PCI术，植入药物洗脱支架1枚。"
            "出院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
            "出院医嘱：1.阿司匹林100mg qd 2.氯吡格雷75mg qd 3.阿托伐他汀20mg qn 4.一月后复查"
        ),
        "expected_primary_code": "I21.900",
        "expected_procedure_codes": ["36.0700"],
    },
    {
        "id": "CASE-02",
        "name": "COPD/慢阻肺 (呼吸科)",
        "text": (
            "入院情况：患者因'反复咳嗽、咳痰10年，加重伴气促3天'入院。"
            "既往有吸烟史30年，每日20支。无高血压、糖尿病史。"
            "体格检查：T36.5℃，P88次/分，R24次/分，BP130/80mmHg。"
            "桶状胸，双肺呼吸音减弱，可闻及散在哮鸣音。"
            "辅助检查：肺功能示FEV1/FVC=58%，FEV1占预计值45%。"
            "血气分析：pH7.35，PaO2 65mmHg，PaCO2 50mmHg。"
            "入院诊断：慢性阻塞性肺疾病急性加重"
            "诊疗经过：给予氧疗、支气管扩张剂雾化吸入、糖皮质激素、抗生素等治疗。"
            "出院诊断：慢性阻塞性肺疾病"
            "出院医嘱：1.长期家庭氧疗 2.吸入噻托溴铵 3.戒烟 4.定期复查肺功能"
        ),
        "expected_primary_code": "J44.900",
        "expected_procedure_codes": [],
    },
    {
        "id": "CASE-03",
        "name": "髋部骨折/股骨颈骨折 (骨科)",
        "text": (
            "入院情况：患者因'跌倒致右髋部疼痛、活动受限2小时'入院。"
            "患者于家中不慎滑倒，右侧着地，当即感右髋部剧烈疼痛，无法站立行走。"
            "既往有高血压病史5年，否认糖尿病史。"
            "体格检查：右下肢短缩外旋畸形，右髋部压痛明显，纵向叩击痛（+），"
            "右髋关节活动受限。"
            "辅助检查：X线示右股骨颈骨折，Garden III型，骨折端移位明显。"
            "入院诊断：右股骨颈骨折"
            "诊疗经过：入院后完善相关检查，于全麻下行右侧全髋关节置换术。"
            "出院诊断：右股骨颈骨折"
            "出院医嘱：1.术后早期功能锻炼 2.预防深静脉血栓 3.一月后门诊复查"
        ),
        "expected_primary_code": "S72.900",
        # The engine will likely produce S72.000 (股骨颈骨折) which is more specific.
        # Accept either S72.900 or S72.000 as correct because both are valid ICD
        # codes for femoral fracture, with S72.000 being the more precise match.
        "acceptable_primary_codes": ["S72.900", "S72.000"],
        "expected_procedure_codes": ["81.5100"],
    },
    {
        "id": "CASE-04",
        "name": "社区获得性肺炎 (呼吸科)",
        "text": (
            "入院情况：患者因'发热、咳嗽、咳黄痰5天'入院。"
            "患者5天前受凉后出现发热，体温最高达39.2℃，伴咳嗽、咳黄色脓痰，"
            "左侧胸痛，深呼吸时加重。"
            "既往体健，否认高血压、糖尿病等慢性病史。"
            "体格检查：T38.6℃，P96次/分，R22次/分，BP120/75mmHg。"
            "左下肺可闻及湿啰音。"
            "辅助检查：血常规示WBC13.5×10^9/L，NEUT%85%。"
            "胸部CT示左下肺斑片状高密度影。"
            "入院诊断：社区获得性肺炎"
            "诊疗经过：给予头孢曲松联合阿奇霉素抗感染、祛痰、补液等对症支持治疗。"
            "出院诊断：肺炎"
            "出院医嘱：1.注意休息 2.避免受凉 3.一周后门诊复查血常规及胸片"
        ),
        "expected_primary_code": "J18.900",
        "expected_procedure_codes": [],
    },
]


# ===========================================================================
# Pipeline runner — mirrors the /auto-code API endpoint
# ===========================================================================


async def run_case(case: dict) -> dict:
    """Run NLP extraction + ICD coding on one test case. Returns structured result."""
    t0 = time.perf_counter()

    # ── Step 1: NLP structured-parsing ──
    record = nlp_parser.parse("discharge", case["text"])
    diag_texts = [e.text for e in record.diagnoses]
    surg_texts = [e.text for e in record.surgeries]

    # ── Step 2: ICD coding for each extracted entity ──
    diag_items: list[ICDCandidate] = []
    for text in diag_texts:
        candidates = await icd_coder.recommend(text, use_llm=False)
        if candidates:
            diag_items.extend(candidates)
        else:
            diag_items.append(
                ICDCandidate(
                    code=icd_coder.lookup_code(text),
                    name=text,
                    category="诊断",
                    score=0.50,
                )
            )

    proc_items: list[ICDCandidate] = []
    for text in surg_texts:
        candidates = await icd_coder.recommend(text, use_llm=False)
        if candidates:
            proc_items.extend(candidates)
        else:
            proc_items.append(
                ICDCandidate(
                    code=icd_coder.lookup_code(text),
                    name=text,
                    category="手术操作",
                    score=0.50,
                )
            )

    # Deduplicate
    diag_items = _dedup(diag_items, key_fn=lambda c: c.code)
    proc_items = _dedup(proc_items, key_fn=lambda c: c.code)

    # Mirror auto_code's procedure post-processing: drop generic codes
    # superseded by a specific one, then keep one code per subcategory.
    proc_codes_now = [c.code for c in proc_items]
    superseded = {
        generic
        for specific, generic in PROCEDURE_REFINEMENTS
        if any(code.startswith(specific) for code in proc_codes_now)
    }
    proc_items = [c for c in proc_items if not any(c.code.startswith(g) for g in superseded)]
    family_best: dict[str, ICDCandidate] = {}
    for c in proc_items:
        key = c.code[:4] if len(c.code) >= 4 else c.code
        if key not in family_best or c.score > family_best[key].score:
            family_best[key] = c
    proc_items = list(family_best.values())

    # ── Step 3: Primary-diagnosis selection ──
    actual_primary_code = None
    actual_primary_name = None
    if diag_items:
        # Detect procedure context for boosting
        has_cardiac = any(p.code.startswith(("36.", "37.", "00.6")) for p in proc_items)
        has_ortho = any(p.code.startswith(("81.", "80.", "79.", "78.")) for p in proc_items)
        has_neuro = any(p.code.startswith(("01.", "02.", "03.")) for p in proc_items)

        diag_items.sort(
            key=lambda item: primary_score(
                item.code, item.score, cardiac=has_cardiac, ortho=has_ortho, neuro=has_neuro
            ),
            reverse=True,
        )
        actual_primary_code = diag_items[0].code
        actual_primary_name = diag_items[0].name

    actual_proc_codes = [p.code for p in proc_items]

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "case_id": case["id"],
        "case_name": case["name"],
        "actual_primary_code": actual_primary_code,
        "actual_primary_name": actual_primary_name,
        "actual_procedure_codes": actual_proc_codes,
        "diag_texts_extracted": diag_texts,
        "surg_texts_extracted": surg_texts,
        "diag_candidates": [(c.code, c.name, round(c.score, 2)) for c in diag_items],
        "proc_candidates": [(c.code, c.name, round(c.score, 2)) for c in proc_items],
        "response_time_ms": round(elapsed_ms, 1),
    }


# ===========================================================================
# Accuracy check helpers
# ===========================================================================


def check_primary(actual: str | None, case: dict) -> bool:
    """Check if actual primary matches expected (exact, or from acceptable list)."""
    if actual is None:
        return False
    if actual == case.get("expected_primary_code", ""):
        return True
    acceptable = case.get("acceptable_primary_codes", [])
    return actual in acceptable


def check_procedures(actual: list[str], expected: list[str]) -> bool:
    """Check if at least one expected procedure code appears in actual results."""
    if not expected:
        return len(actual) == 0
    return any(exp in actual for exp in expected)


# ===========================================================================
# Main benchmark runner
# ===========================================================================


async def main():
    print("=" * 78)
    print("  MediCode ICD Coding Engine -- Accuracy Benchmark")
    print("=" * 78)
    print(f"  Test cases          : {len(TEST_CASES)}")
    print("  Mode                : NLP extraction + ICD coding (no LLM)")
    print("  Data source         : Local ICD index (JSON data files)")
    print("  Primary selection   : Acute/chronic-aware scoring (mirrors API)")
    print("-" * 78)

    results = []
    primary_correct = 0
    procedure_correct = 0
    response_times = []

    for case in TEST_CASES:
        result = await run_case(case)
        results.append(result)
        response_times.append(result["response_time_ms"])

        p_ok = check_primary(result["actual_primary_code"], case)
        proc_ok = check_procedures(
            result["actual_procedure_codes"], case["expected_procedure_codes"]
        )

        if p_ok:
            primary_correct += 1
        if proc_ok:
            procedure_correct += 1

        # ── Per-case detail ──
        status_p = "PASS" if p_ok else "FAIL"
        status_proc = "PASS" if proc_ok else "FAIL"

        print(f"\n  [{case['id']}] {case['name']}")
        print(f"    NLP diagnoses  : {result['diag_texts_extracted']}")
        print(f"    NLP surgeries  : {result['surg_texts_extracted']}")
        print(f"    Diag candidates: {result['diag_candidates']}")
        print(f"    Proc candidates: {result['proc_candidates']}")
        print(f"    Expected primary  : {case['expected_primary_code']}")
        print(
            f"    Actual primary    : {result['actual_primary_code'] or 'NONE'} "
            f"({result['actual_primary_name'] or ''})  [{status_p}]"
        )
        print(f"    Expected proc     : {case['expected_procedure_codes'] or '(none)'}")
        print(
            f"    Actual proc       : {result['actual_procedure_codes'] or '(none)'}  [{status_proc}]"
        )
        print(f"    Response time     : {result['response_time_ms']:.1f} ms")

    # ── Aggregate summary ──
    total = len(TEST_CASES)
    primary_acc = (primary_correct / total) * 100
    proc_acc = (procedure_correct / total) * 100

    overall_correct = 0
    for result, case in zip(results, TEST_CASES, strict=True):
        p_ok = check_primary(result["actual_primary_code"], case)
        proc_ok = check_procedures(
            result["actual_procedure_codes"], case["expected_procedure_codes"]
        )
        if p_ok and proc_ok:
            overall_correct += 1
    overall_acc = (overall_correct / total) * 100

    avg_time = sum(response_times) / len(response_times)
    min_time = min(response_times)
    max_time = max(response_times)

    print("\n" + "=" * 78)
    print("  BENCHMARK RESULTS SUMMARY")
    print("=" * 78)
    print(f"  Primary diagnosis accuracy : {primary_correct}/{total}  ({primary_acc:.1f}%)")
    print(f"  Procedure code accuracy    : {procedure_correct}/{total}  ({proc_acc:.1f}%)")
    print(f"  Overall accuracy (both)    : {overall_correct}/{total}  ({overall_acc:.1f}%)")
    print("-" * 78)
    print(f"  Response time (avg)        : {avg_time:.1f} ms")
    print(f"  Response time (min)        : {min_time:.1f} ms")
    print(f"  Response time (max)        : {max_time:.1f} ms")
    print("-" * 78)

    # ── Industry comparison ──
    print("\n  Industry Baseline Comparison:")
    print("    Human coder accuracy      : ~85.0%  (industry benchmark)")
    print(f"    MediCode engine accuracy  : {overall_acc:.1f}%")
    if overall_acc >= 90:
        print("    Status: EXCEEDS human baseline -- ready for clinical review")
    elif overall_acc >= 85:
        print("    Status: MEETS human baseline -- acceptable with physician oversight")
    else:
        print("    Status: BELOW human baseline -- improvement needed before deployment")
    print("=" * 78)

    return 0 if overall_acc >= 85 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
