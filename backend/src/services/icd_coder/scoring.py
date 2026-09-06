"""ICD code scoring helpers for primary diagnosis selection.

Shared between the API endpoint (coding.py) and the accuracy benchmark.
"""

# Chronic/stable conditions: usually comorbidities, penalized as primary
CHRONIC_STABLE: dict[str, str] = {
    "I10": "原发性高血压",
    "I15": "继发性高血压",
    "E10": "1型糖尿病",
    "E11": "2型糖尿病",
    "E13": "其他特指糖尿病",
    "E14": "未特指糖尿病",
    "E78": "高脂血症",
    "E79": "高尿酸血症",
    "E66": "肥胖",
}

# Acute/critical conditions: preferred as primary diagnosis
ACUTE_PREFIXES: list[str] = [
    "I21",
    "I22",  # Acute MI
    "I26",  # Pulmonary embolism
    "I60",
    "I61",
    "I62",
    "I63",
    "I64",  # Stroke/bleed
    "I50.1",
    "I50.2",  # Acute heart failure
    "J12",
    "J13",
    "J14",
    "J15",
    "J16",
    "J17",
    "J18",  # Pneumonia
    "J96.0",  # Acute respiratory failure
    "A41",  # Sepsis
    "K85",  # Acute pancreatitis
    "K35",  # Acute appendicitis
    "N17",  # Acute kidney injury
    "T79",  # Trauma complications
    "S06",
    "S26",
    "S36",  # Major trauma
]


def primary_score(
    code: str, confidence: float, *, cardiac: bool = False, ortho: bool = False, neuro: bool = False
) -> float:
    """Score an ICD code for primary diagnosis selection (higher = better primary)."""
    s = confidence

    if code[0] == "O":
        s -= 0.9
    if code.startswith("R") and not code.startswith("R5"):
        s -= 0.5
    if code.startswith("Z"):
        s -= 0.6
    for prefix in CHRONIC_STABLE:
        if code.startswith(prefix):
            s -= 0.35
            break
    for prefix in ACUTE_PREFIXES:
        if code.startswith(prefix):
            s += 0.40
            break
    if cardiac and code.startswith("I") and not code.startswith(("I10", "I15")):
        s += 0.30
    if ortho and code.startswith(("M", "S", "T")):
        s += 0.25
    if neuro and code.startswith(("I6", "G")):
        s += 0.25
    return s


# Procedure code refinement pairs: (specific code, generic code).
# When the specific code is present, the generic one is dropped — the same
# procedure must never be coded twice, and ICD requires the most specific
# code available (药物洗脱支架 36.07 supersedes unspecified 冠脉支架 36.06).
PROCEDURE_REFINEMENTS: list[tuple[str, str]] = [
    ("36.07", "36.06"),
]


def conflicts(code_a: str, code_b: str) -> bool:
    """Check if two ICD codes represent conflicting versions of the same condition."""
    conflict_groups = [
        (("I21",), ("I25.2",)),  # Acute MI vs Old MI
        (("E11",), ("E10",)),  # Type 2 DM vs Type 1 DM
        (("I10",), ("I15",)),  # Essential HTN vs Secondary HTN
        (("J44",), ("J45",)),  # COPD vs Asthma
        (("K29.5",), ("K29.1",)),  # Chronic gastritis vs Acute gastritis
    ]
    for group_a, group_b in conflict_groups:
        a_in_a = any(code_a.startswith(p) for p in group_a)
        a_in_b = any(code_a.startswith(p) for p in group_b)
        b_in_a = any(code_b.startswith(p) for p in group_a)
        b_in_b = any(code_b.startswith(p) for p in group_b)
        if (a_in_a and b_in_b) or (a_in_b and b_in_a):
            return True
    return False
