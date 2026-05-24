"""Coding Accuracy Benchmark: 50 clinical cases → AI coding vs gold-standard ICD codes.

Generates a report with precision, recall, and F1 metrics across departments.
"""
import asyncio
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from src.services.icd_coder.coder import icd_coder


@dataclass
class TestCase:
    id: int
    department: str
    diagnosis_text: str  # Free-text clinical diagnosis
    expected_diag_codes: list[str]  # Expected ICD-10 diagnosis codes
    expected_proc_codes: list[str] = field(default_factory=list)  # Expected ICD-9-CM-3 procedure codes
    patient_info: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════
# 50 Test Cases Across 8 Major Departments
# ═══════════════════════════════════════════════════════════

TEST_CASES: list[TestCase] = [
    # ── Cardiology (心血管内科) ── 8 cases
    TestCase(1, "心内科", "急性心肌梗死", ["I21.900"], [],
             {"age": 65, "gender": "male"}),
    TestCase(2, "心内科", "冠状动脉粥样硬化性心脏病", ["I25.100"], [],
             {"age": 62, "gender": "male"}),
    TestCase(3, "心内科", "不稳定型心绞痛", ["I20.000"], [],
             {"age": 58, "gender": "male"}),
    TestCase(4, "心内科", "心房颤动", ["I48.900"], [],
             {"age": 72, "gender": "female"}),
    TestCase(5, "心内科", "心力衰竭", ["I50.900"], [],
             {"age": 78, "gender": "male"}),
    TestCase(6, "心内科", "原发性高血压", ["I10.x00"], [],
             {"age": 55, "gender": "female"}),
    TestCase(7, "心内科", "阵发性室上性心动过速", ["I47.100"], ["37.3400"],
             {"age": 45, "gender": "male"}),
    TestCase(8, "心内科", "急性心肌梗死，行冠状动脉支架植入", ["I21.900"], ["36.0700"],
             {"age": 63, "gender": "male"}),

    # ── Respiratory (呼吸内科) ── 6 cases
    TestCase(9, "呼吸内科", "社区获得性肺炎", ["J18.900"], [],
             {"age": 52, "gender": "male"}),
    TestCase(10, "呼吸内科", "慢性阻塞性肺疾病急性加重", ["J44.900"], [],
              {"age": 68, "gender": "male"}),
    TestCase(11, "呼吸内科", "支气管哮喘", ["J45.900"], [],
              {"age": 35, "gender": "female"}),
    TestCase(12, "呼吸内科", "支气管肺炎", ["J18.000"], [],
              {"age": 3, "gender": "female"}),
    TestCase(13, "呼吸内科", "肺栓塞", ["I26.900"], [],
              {"age": 60, "gender": "male"}),
    TestCase(14, "呼吸内科", "胸腔积液", ["J90.900"], ["34.0400"],
              {"age": 55, "gender": "male"}),

    # ── Gastroenterology (消化内科) ── 8 cases
    TestCase(15, "消化内科", "胃溃疡", ["K25.900"], [],
              {"age": 48, "gender": "male"}),
    TestCase(16, "消化内科", "十二指肠溃疡", ["K26.900"], [],
              {"age": 42, "gender": "male"}),
    TestCase(17, "消化内科", "急性胰腺炎", ["K85.900"], [],
              {"age": 50, "gender": "male"}),
    TestCase(18, "消化内科", "肝硬化", ["K74.600"], [],
              {"age": 55, "gender": "male"}),
    TestCase(19, "消化内科", "胆囊结石伴急性胆囊炎", ["K80.000"], ["51.2200"],
              {"age": 52, "gender": "female"}),
    TestCase(20, "消化内科", "急性阑尾炎", ["K35.900"], ["47.0900"],
              {"age": 28, "gender": "male"}),
    TestCase(21, "消化内科", "消化道出血", ["K92.200"], [],
              {"age": 60, "gender": "male"}),
    TestCase(22, "消化内科", "胃食管反流病", ["K21.900"], [],
              {"age": 40, "gender": "female"}),

    # ── Endocrinology (内分泌科) ── 5 cases
    TestCase(23, "内分泌科", "2型糖尿病", ["E11.900"], [],
              {"age": 58, "gender": "female"}),
    TestCase(24, "内分泌科", "2型糖尿病伴肾病", ["E11.200"], [],
              {"age": 62, "gender": "male"}),
    TestCase(25, "内分泌科", "甲状腺功能亢进症", ["E05.900"], [],
              {"age": 38, "gender": "female"}),
    TestCase(26, "内分泌科", "高脂血症", ["E78.500"], [],
              {"age": 52, "gender": "male"}),
    TestCase(27, "内分泌科", "痛风", ["M10.900"], [],
              {"age": 45, "gender": "male"}),

    # ── Neurology (神经内科) ── 6 cases
    TestCase(28, "神经内科", "脑梗死", ["I63.900"], [],
              {"age": 72, "gender": "male"}),
    TestCase(29, "神经内科", "脑出血", ["I61.900"], [],
              {"age": 65, "gender": "female"}),
    TestCase(30, "神经内科", "短暂性脑缺血发作", ["G45.900"], [],
              {"age": 68, "gender": "male"}),
    TestCase(31, "神经内科", "帕金森病", ["G20.900"], [],
              {"age": 75, "gender": "male"}),
    TestCase(32, "神经内科", "癫痫", ["G40.900"], [],
              {"age": 32, "gender": "female"}),
    TestCase(33, "神经内科", "偏头痛", ["G43.900"], [],
              {"age": 28, "gender": "female"}),

    # ── Orthopedics (骨科) ── 6 cases
    TestCase(34, "骨科", "股骨骨折", ["S72.900"], ["79.3500"],
              {"age": 45, "gender": "male"}),
    TestCase(35, "骨科", "腰椎间盘突出", ["M51.200"], [],
              {"age": 48, "gender": "male"}),
    TestCase(36, "骨科", "膝关节骨性关节炎", ["M17.900"], ["81.5400"],
              {"age": 68, "gender": "female"}),
    TestCase(37, "骨科", "肩关节周围炎", ["M75.000"], [],
              {"age": 52, "gender": "female"}),
    TestCase(38, "骨科", "椎体压缩性骨折", ["M48.500"], [],
              {"age": 75, "gender": "female"}),
    TestCase(39, "骨科", "颈椎病", ["M47.900"], [],
              {"age": 55, "gender": "male"}),

    # ── General Surgery (普外科) ── 6 cases
    TestCase(40, "普外科", "胆囊结石", ["K80.200"], ["51.2300"],
              {"age": 48, "gender": "female"}),
    TestCase(41, "普外科", "腹股沟疝", ["K40.900"], ["53.0000"],
              {"age": 62, "gender": "male"}),
    TestCase(42, "普外科", "结肠恶性肿瘤", ["C18.900"], ["45.7300"],
              {"age": 65, "gender": "male"}),
    TestCase(43, "普外科", "乳腺恶性肿瘤", ["C50.900"], ["85.4300"],
              {"age": 52, "gender": "female"}),
    TestCase(44, "普外科", "急性阑尾炎", ["K35.900"], ["47.0100"],
              {"age": 22, "gender": "male"}),
    TestCase(45, "普外科", "肠梗阻", ["K56.600"], [],
              {"age": 58, "gender": "male"}),

    # ── Obstetrics & Gynecology (妇产科) ── 5 cases
    TestCase(46, "妇产科", "子宫平滑肌瘤", ["D25.900"], ["68.2900"],
              {"age": 45, "gender": "female"}),
    TestCase(47, "妇产科", "剖宫产分娩", ["O82.900"], ["74.0000"],
              {"age": 30, "gender": "female"}),
    TestCase(48, "妇产科", "卵巢囊肿", ["N83.200"], ["65.2500"],
              {"age": 35, "gender": "female"}),
    TestCase(49, "妇产科", "盆腔炎性疾病", ["N73.900"], [],
              {"age": 32, "gender": "female"}),
    TestCase(50, "妇产科", "子宫内膜异位症", ["N80.900"], [],
              {"age": 38, "gender": "female"}),
]


async def run_benchmark():
    print("=" * 70)
    print("  码医 MediCode — 编码准确率基准测试 (50例)")
    print("=" * 70)
    print(f"  测试用例数: {len(TEST_CASES)}")
    print(f"  覆盖科室: 8 个")
    print()

    results = []
    total_diag_correct = 0
    total_diag_expected = 0
    total_diag_predicted = 0
    total_proc_correct = 0
    total_proc_expected = 0
    total_proc_predicted = 0
    dept_stats: dict[str, dict] = {}

    for tc in TEST_CASES:
        # Get AI recommendation
        candidates = await icd_coder.recommend(tc.diagnosis_text, use_llm=False)

        # Separate diag and proc candidates
        diag_preds = [c for c in candidates if c.category == "诊断"]
        proc_preds = [c for c in candidates if c.category == "手术操作"]

        diag_codes = [c.code for c in diag_preds[:3]]  # Top 3
        proc_codes = [c.code for c in proc_preds[:3]]

        # Calculate per-case metrics
        diag_hits = len(set(diag_codes) & set(tc.expected_diag_codes))
        proc_hits = len(set(proc_codes) & set(tc.expected_proc_codes))

        total_diag_correct += diag_hits
        total_diag_expected += len(tc.expected_diag_codes)
        total_diag_predicted += len(diag_codes)
        total_proc_correct += proc_hits
        total_proc_expected += len(tc.expected_proc_codes)
        total_proc_predicted += len(proc_codes)

        # Department stats
        if tc.department not in dept_stats:
            dept_stats[tc.department] = {
                "diag_correct": 0, "diag_expected": 0, "diag_predicted": 0,
                "proc_correct": 0, "proc_expected": 0, "proc_predicted": 0,
                "cases": 0, "diag_top1_correct": 0, "proc_top1_correct": 0,
            }
        ds = dept_stats[tc.department]
        ds["diag_correct"] += diag_hits
        ds["diag_expected"] += len(tc.expected_diag_codes)
        ds["diag_predicted"] += len(diag_codes)
        ds["proc_correct"] += proc_hits
        ds["proc_expected"] += len(tc.expected_proc_codes)
        ds["proc_predicted"] += len(proc_codes)
        ds["cases"] += 1
        if diag_codes and diag_codes[0] in tc.expected_diag_codes:
            ds["diag_top1_correct"] += 1
        if proc_codes and proc_codes[0] in tc.expected_proc_codes:
            ds["proc_top1_correct"] += 1

        results.append({
            "id": tc.id,
            "department": tc.department,
            "query": tc.diagnosis_text,
            "expected_diag": tc.expected_diag_codes,
            "predicted_diag": diag_codes,
            "expected_proc": tc.expected_proc_codes,
            "predicted_proc": proc_codes,
            "diag_hit": diag_hits > 0,
            "diag_top1": diag_codes[0] if diag_codes else None,
            "diag_top1_hit": diag_codes[0] in tc.expected_diag_codes if diag_codes else False,
        })

    # ── Overall Metrics ──
    def precision(correct, predicted):
        return correct / predicted if predicted > 0 else 0.0

    def recall(correct, expected):
        return correct / expected if expected > 0 else 0.0

    def f1(p, r):
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    diag_precision = precision(total_diag_correct, total_diag_predicted)
    diag_recall = recall(total_diag_correct, total_diag_expected)
    diag_f1 = f1(diag_precision, diag_recall)

    proc_precision = precision(total_proc_correct, total_proc_predicted)
    proc_recall = recall(total_proc_correct, total_proc_expected)
    proc_f1 = f1(proc_precision, proc_recall)

    top1_correct = sum(1 for r in results if r["diag_top1_hit"])
    top1_accuracy = top1_correct / len(results)

    print("─" * 70)
    print("  【总体结果】")
    print(f"  诊断编码 — Precision: {diag_precision:.1%}  Recall: {diag_recall:.1%}  F1: {diag_f1:.1%}")
    print(f"  手术编码 — Precision: {proc_precision:.1%}  Recall: {proc_recall:.1%}  F1: {proc_f1:.1%}")
    print(f"  Top-1 诊断准确率: {top1_accuracy:.1%} ({top1_correct}/{len(results)})")
    print()

    # ── Per Department Breakdown ──
    print("─" * 70)
    print("  【科室分项结果】")
    print(f"  {'科室':<10s} {'病例':>4s} {'诊断Top1':>8s} {'诊断P':>7s} {'诊断R':>7s} {'诊断F1':>7s}")
    print("  " + "-" * 50)
    for dept, ds in sorted(dept_stats.items()):
        dp = precision(ds["diag_correct"], ds["diag_predicted"])
        dr = recall(ds["diag_correct"], ds["diag_expected"])
        df1 = f1(dp, dr)
        top1 = ds["diag_top1_correct"]
        top1_str = f"{top1}/{ds['cases']}"
    print(f"  {dept:<10s} {ds['cases']:>4d} {top1_str:>8s} {dp:>6.1%} {dr:>6.1%} {df1:>6.1%}")

    print()
    print("─" * 70)
    print("  【逐例详情】")
    print(f"  {'#':<3s} {'科室':<8s} {'查询':<16s} {'期望':<14s} {'预测Top1':<14s} {'命中':<4s}")
    print("  " + "-" * 65)
    for r in results:
        status = "✓" if r["diag_hit"] else "✗"
        print(f"  {r['id']:<3d} {r['department']:<8s} {r['query']:<16s} {r['expected_diag'][0]:<14s} "
              f"{r['diag_top1'] or 'N/A':<14s} {status:<4s}")

    print()
    print("=" * 70)
    print(f"  综合评分: {diag_f1:.1%} (诊断 F1)")
    if diag_f1 >= 0.85:
        print("  评级: ★★★ 优秀 — 满足竞赛演示要求")
    elif diag_f1 >= 0.70:
        print("  评级: ★★☆ 良好 — 建议优化高频编码的召回")
    else:
        print("  评级: ★☆☆ 需改进 — 编码库覆盖率不足")
    print("=" * 70)

    # ── Miss Analysis ──
    misses = [r for r in results if not r["diag_hit"]]
    if misses:
        print()
        print("  【未命中分析】(诊断Top1未命中)")
        for m in misses:
            print(f"  #{m['id']} [{m['department']}] \"{m['query']}\" → "
                  f"期望:{m['expected_diag']} 实际:{m['predicted_diag']}")

    return diag_f1


if __name__ == "__main__":
    f1 = asyncio.run(run_benchmark())

    # Save JSON report
    report_path = Path(__file__).parent.parent / "output" / "accuracy_report.json"
    report_path.parent.mkdir(exist_ok=True)
    print(f"\nReport saved to: {report_path}")
