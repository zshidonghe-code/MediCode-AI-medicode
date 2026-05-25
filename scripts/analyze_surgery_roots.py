"""Surgery coding root cause analysis — 203 cases.

Categorizes every procedure coding failure into:
  A) Missing from code library (expected code not in icd_procedures.json)
  B) Non-standard name (no alias matches the query text)
  C) Text doesn't mention surgery (query text contains no surgery keywords)

Also outputs a distribution across departments.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent))  # for 'scripts' package

# Load ICD procedure data directly (no DB dependency)
DATA_DIR = Path(__file__).parent.parent / "backend" / "src" / "data"
with open(DATA_DIR / "icd_procedures.json", "r", encoding="utf-8") as f:
    PROCEDURES = json.load(f)

# Build code->entry index and name/alias->code index
CODE_INDEX: dict[str, dict] = {}
NAME_TO_CODE: dict[str, str] = {}  # name or alias -> code
for entry in PROCEDURES:
    CODE_INDEX[entry["code"]] = entry
    if entry["name"] not in NAME_TO_CODE:
        NAME_TO_CODE[entry["name"]] = entry["code"]
    for alias in entry.get("aliases", []):
        if alias not in NAME_TO_CODE:
            NAME_TO_CODE[alias] = entry["code"]

# Import test cases
from scripts.benchmark_coding import TEST_CASES


def analyze():
    cases_with_proc = [tc for tc in TEST_CASES if tc.expected_proc_codes]

    results = []
    stats = {
        "total_with_proc": len(cases_with_proc),
        "total_expected_codes": sum(len(tc.expected_proc_codes) for tc in cases_with_proc),
        "code_in_library": 0,       # expected code exists in ICD JSON
        "code_not_in_library": 0,   # expected code NOT in ICD JSON
        "alias_matches_query": 0,   # query text has matching alias/name
        "alias_misses_query": 0,    # query text has NO matching alias/name
        "surgery_keywords_found": 0,
        "surgery_keywords_missing": 0,
        "dept_stats": defaultdict(lambda: {"cases": 0, "codes_expected": 0, "codes_in_lib": 0,
                                            "codes_not_in_lib": 0, "alias_hits": 0, "alias_misses": 0}),
    }

    # Surgery keyword list (common Chinese procedure terms)
    surgery_keywords = [
        "手术", "切除术", "植入", "支架", "搭桥", "修复", "重建", "置换",
        "切开", "引流", "穿刺", "吻合", "结扎", "摘除", "剥除", "成形",
        "介入", "PCI", "搭桥", "固定", "复位", "缝合", "移植", "消融",
        "剖宫产", "分娩", "阑尾", "胆囊", "腹腔镜", "关节", "冠脉",
    ]

    for tc in cases_with_proc:
        diag_text = tc.diagnosis_text
        dept = tc.department
        ds = stats["dept_stats"][dept]
        ds["cases"] += 1

        for code in tc.expected_proc_codes:
            ds["codes_expected"] += 1
            entry = CODE_INDEX.get(code)

            # Check A: code in library?
            if entry:
                stats["code_in_library"] += 1
                ds["codes_in_lib"] += 1
                # Check if any alias/name matches the query text
                names_to_check = [entry["name"]] + entry.get("aliases", [])
                any_match = any(n in diag_text for n in names_to_check)
                if any_match:
                    stats["alias_matches_query"] += 1
                    ds["alias_hits"] += 1
                else:
                    stats["alias_misses_query"] += 1
                    ds["alias_misses"] += 1
            else:
                stats["code_not_in_library"] += 1
                ds["codes_not_in_lib"] += 1

            # Check C: surgery keywords in query?
            has_kw = any(kw in diag_text for kw in surgery_keywords)
            if has_kw:
                stats["surgery_keywords_found"] += 1
            else:
                stats["surgery_keywords_missing"] += 1

            results.append({
                "case_id": tc.id,
                "department": dept,
                "query": diag_text,
                "expected_code": code,
                "in_library": entry is not None,
                "code_name": entry["name"] if entry else "N/A",
                "aliases": entry.get("aliases", []) if entry else [],
                "has_surgery_keywords": has_kw,
            })

    # ── Output ──
    print("=" * 72)
    print("  手术编码根因分析 (203份病历)")
    print("=" * 72)
    print(f"  含手术的病例: {stats['total_with_proc']}")
    print(f"  预期手术编码总数: {stats['total_expected_codes']}")
    print()

    print("─" * 72)
    print("  【根因A：编码库覆盖】")
    print(f"  编码在库中: {stats['code_in_library']} ({stats['code_in_library']/max(stats['total_expected_codes'],1):.1%})")
    print(f"  编码不在库中: {stats['code_not_in_library']} ({stats['code_not_in_library']/max(stats['total_expected_codes'],1):.1%})")
    print()

    print("─" * 72)
    print("  【根因B：别名/名称匹配】")
    print(f"  查询文本含匹配别名: {stats['alias_matches_query']} ({stats['alias_matches_query']/max(stats['code_in_library'],1):.1%})")
    print(f"  查询文本无匹配别名: {stats['alias_misses_query']} ({stats['alias_misses_query']/max(stats['code_in_library'],1):.1%})")
    print()

    print("─" * 72)
    print("  【根因C：手术关键词覆盖】")
    print(f"  查询含手术关键词: {stats['surgery_keywords_found']}")
    print(f"  查询不含手术关键词: {stats['surgery_keywords_missing']}")
    print()

    # ── Per-Department Breakdown ──
    print("─" * 72)
    print("  【科室分项】")
    print(f"  {'科室':<10s} {'病例':>5s} {'预期编码':>8s} {'在库':>6s} {'缺库':>6s} {'别名命中':>8s} {'别名缺失':>8s}")
    print("  " + "-" * 60)
    for dept in sorted(stats["dept_stats"]):
        ds = stats["dept_stats"][dept]
        print(f"  {dept:<10s} {ds['cases']:>5d} {ds['codes_expected']:>8d} "
              f"{ds['codes_in_lib']:>6d} {ds['codes_not_in_lib']:>6d} "
              f"{ds['alias_hits']:>8d} {ds['alias_misses']:>8d}")

    print()

    # ── Missing Codes Detail ──
    print("─" * 72)
    print("  【不在库中的编码详情】")
    missing = [r for r in results if not r["in_library"]]
    if missing:
        for m in sorted(missing, key=lambda x: x["department"]):
            print(f"  #{m['case_id']} [{m['department']}] \"{m['query']}\" → 缺码:{m['expected_code']}")
    else:
        print("  (无) 所有预期编码均已在手术编码库中")
    print()

    # ── Alias Misses Detail (code exists but name/alias doesn't match query) ──
    print("─" * 72)
    print("  【编码在库但别名不匹配的详情】(最需要加别名的)")
    alias_misses = [r for r in results if r["in_library"] and not r["has_surgery_keywords"]]
    # Also show those with surgery keywords but no alias match
    alias_misses_all = [r for r in results if r["in_library"] and r["expected_code"] not in [
        r2["expected_code"] for r2 in results if r2["in_library"] and any(
            a in r2["query"] for a in (CODE_INDEX.get(r2["expected_code"], {}).get("aliases", []) +
            [CODE_INDEX.get(r2["expected_code"], {}).get("name", "")])
        )
    ]]

    # Group by expected code
    by_code = defaultdict(list)
    for r in results:
        if r["in_library"]:
            entry = CODE_INDEX[r["expected_code"]]
            all_names = [entry["name"]] + entry.get("aliases", [])
            if not any(n in r["query"] for n in all_names):
                by_code[r["expected_code"]].append(r)

    if by_code:
        for code, items in sorted(by_code.items()):
            entry = CODE_INDEX[code]
            queries = [f"\"{r['query']}\"" for r in items]
            print(f"  编码 {code} ({entry['name']})")
            print(f"    现有别名: {entry.get('aliases', [])}")
            print(f"    未匹配查询: {', '.join(set(queries))}")
            print()
    else:
        print("  (无) 所有编码均有别名匹配")
    print()

    # ── Surgery keyword gaps ──
    print("─" * 72)
    print("  【查询中缺少手术关键词的病例】")
    no_kw = [r for r in results if not r["has_surgery_keywords"]]
    # deduplicate by case_id
    seen = set()
    for r in no_kw:
        if r["case_id"] not in seen:
            seen.add(r["case_id"])
            print(f"  #{r['case_id']} [{r['department']}] \"{r['query']}\"")

    print()
    print("=" * 72)
    print("  总结")
    print(f"  根因A (编码不在库): {stats['code_not_in_library']} 个编码 → 扩充编码库")
    print(f"  根因B (别名不匹配): {sum(1 for v in by_code.values() for _ in v)} 个匹配失败 → 加别名")
    print(f"  根因C (查询无手术信息): {stats['surgery_keywords_missing']} 个 → 需多文本来源")
    print("=" * 72)


if __name__ == "__main__":
    analyze()
