import time
import logging
from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import Optional
from src.services.nlp_engine.engine import nlp_parser
from src.services.icd_coder.coder import icd_coder, ICDCandidate
from src.api.v1.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class CodingRequest(BaseModel):
    record_id: int
    record_type: str
    content: str = Field(..., min_length=10, max_length=50000)
    use_llm: bool = False  # 默认关闭LLM，用规则引擎保证快速响应


class ICDCodeItem(BaseModel):
    code: str
    name: str
    category: str
    is_primary: bool = False
    confidence: float = 0.0


class CodingResponse(BaseModel):
    record_id: int
    primary_diagnosis: Optional[ICDCodeItem] = None
    secondary_diagnoses: list[ICDCodeItem] = []
    procedures: list[ICDCodeItem] = []
    suggestions: list[ICDCodeItem] = []
    total_confidence: float = 0.0
    processing_time_ms: int = 0


def _to_item(c: ICDCandidate) -> ICDCodeItem:
    return ICDCodeItem(
        code=c.code, name=c.name, category=c.category,
        is_primary=False, confidence=round(c.score, 2),
    )


def _dedup(items: list[ICDCodeItem]) -> list[ICDCodeItem]:
    """Deduplicate by code, keeping highest confidence"""
    best: dict[str, ICDCodeItem] = {}
    for item in items:
        key = item.code
        if key not in best or item.confidence > best[key].confidence:
            best[key] = item
    return list(best.values())


# ── Module-level scoring & filtering helpers ──────────────────────────────────

# Chronic/stable conditions: usually comorbidities, penalized as primary
_CHRONIC_STABLE: dict[str, str] = {
    "I10": "原发性高血压", "I15": "继发性高血压",
    "E11": "2型糖尿病", "E10": "1型糖尿病",
    "E78": "高脂血症", "E79": "高尿酸血症",
    "E66": "肥胖",
}

# Acute/critical conditions: preferred as primary diagnosis
_ACUTE_PREFIXES: list[str] = [
    "I21", "I22",  # Acute MI
    "I26",         # Pulmonary embolism
    "I60", "I61", "I62", "I63", "I64",  # Stroke/bleed
    "I50.1", "I50.2",  # Acute heart failure
    "J12", "J13", "J14", "J15", "J16", "J17", "J18",  # Pneumonia
    "J96.0",       # Acute respiratory failure
    "A41",         # Sepsis
    "K85",         # Acute pancreatitis
    "K35",         # Acute appendicitis
    "N17",         # Acute kidney injury
    "T79",         # Trauma complications
    "S06", "S26", "S36",  # Major trauma
]


def _primary_score(item: ICDCodeItem, *, cardiac: bool = False,
                   ortho: bool = False, neuro: bool = False) -> float:
    """Score an ICD code for primary diagnosis selection (higher = better primary)"""
    s = item.confidence
    code = item.code

    if code[0] == "O":
        s -= 0.9
    if code.startswith("R") and not code.startswith("R5"):
        s -= 0.5
    if code.startswith("Z"):
        s -= 0.6
    for prefix in _CHRONIC_STABLE:
        if code.startswith(prefix):
            s -= 0.35
            break
    for prefix in _ACUTE_PREFIXES:
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


def _conflicts(code_a: str, code_b: str) -> bool:
    """Check if two ICD codes represent conflicting versions of the same condition"""
    conflict_groups = [
        (("I21",), ("I25.2",)),     # Acute MI vs Old MI
        (("E11",), ("E10",)),       # Type 2 DM vs Type 1 DM
        (("I10",), ("I15",)),       # Essential HTN vs Secondary HTN
        (("J44",), ("J45",)),       # COPD vs Asthma
        (("K29.5",), ("K29.1",)),   # Chronic gastritis vs Acute gastritis
    ]
    for group_a, group_b in conflict_groups:
        a_in_a = any(code_a.startswith(p) for p in group_a)
        a_in_b = any(code_a.startswith(p) for p in group_b)
        b_in_a = any(code_b.startswith(p) for p in group_a)
        b_in_b = any(code_b.startswith(p) for p in group_b)
        if (a_in_a and b_in_b) or (a_in_b and b_in_a):
            return True
    return False


@router.post("/auto-code", response_model=CodingResponse)
async def auto_code(request: CodingRequest, user: dict = Depends(get_current_user)):
    t0 = time.time()
    record = nlp_parser.parse(request.record_type, request.content)

    diag_items = []
    for entity in record.diagnoses:
        candidates = await icd_coder.recommend(entity.text, use_llm=request.use_llm)
        if candidates:
            diag_items.extend(_to_item(c) for c in candidates)
        else:
            diag_items.append(ICDCodeItem(
                code=icd_coder.lookup_code(entity.text),
                name=entity.text,
                category="诊断",
                confidence=entity.confidence,
            ))

    proc_items = []
    for entity in record.surgeries:
        candidates = await icd_coder.recommend(entity.text, use_llm=request.use_llm)
        if candidates:
            proc_items.extend(_to_item(c) for c in candidates)
        else:
            proc_items.append(ICDCodeItem(
                code=icd_coder.lookup_code(entity.text),
                name=entity.text,
                category="手术操作",
                confidence=entity.confidence,
            ))

    diag_items = _dedup(diag_items)
    proc_items = _dedup(proc_items)

    # Select primary diagnosis with medical logic
    primary = None
    secondaries = []
    if diag_items:
        # Detect procedure context for boosting related diagnoses
        has_cardiac_proc = any(
            p.code.startswith(("36.", "37.", "00.6")) for p in proc_items
        )
        has_ortho_proc = any(
            p.code.startswith(("81.", "80.", "79.", "78.")) for p in proc_items
        )
        has_neuro_proc = any(
            p.code.startswith(("01.", "02.", "03.")) for p in proc_items
        )

        diag_items.sort(key=lambda item: _primary_score(
            item, cardiac=has_cardiac_proc, ortho=has_ortho_proc, neuro=has_neuro_proc), reverse=True)
        primary = diag_items[0]
        primary.is_primary = True

        # Build secondaries: filter same-category sub-codes, keep top 9
        secondaries = []
        primary_prefix = primary.code.split(".")[0] if primary else ""
        for item in diag_items[1:]:
            item_prefix = item.code.split(".")[0]
            # Skip codes with very low adjusted score
            if _primary_score(item) < 0.1:
                continue
            # Skip O-codes (pregnancy/obstetric)
            if item.code.startswith("O"):
                continue
            # Skip DM complication subcodes (E11.2-.7, E10.2-.7) — rarely independently diagnosed
            if item_prefix in ("E11", "E10"):
                parts = item.code.split(".")
                if len(parts) > 1 and parts[1] and parts[1][0] in ("2", "3", "4", "5", "6", "7"):
                    continue
            # Skip sub-codes of the same ICD category as primary
            if item_prefix == primary_prefix and item_prefix not in ("",):
                if item_prefix == "I10":
                    if item.code == "I10.x00":
                        pass  # Allow base HTN code as comorbidity
                    else:
                        continue
                else:
                    continue
            secondaries.append(item)

        # Post-filter: remove conflicting codes
        filtered = []
        kept_codes: list[str] = [primary.code]
        for item in secondaries:
            if any(_conflicts(item.code, kc) for kc in kept_codes):
                continue
            kept_codes.append(item.code)
            filtered.append(item)
        secondaries = filtered[:9]

    total_conf = primary.confidence if primary else 0.0
    if secondaries:
        total_conf = (total_conf + sum(c.confidence for c in secondaries)) / (len(secondaries) + 1)

    return CodingResponse(
        record_id=request.record_id,
        primary_diagnosis=primary,
        secondary_diagnoses=secondaries,
        procedures=proc_items,
        suggestions=diag_items[:5],
        total_confidence=round(total_conf, 2),
        processing_time_ms=int((time.time() - t0) * 1000),
    )


@router.post("/auto-code/upload")
async def auto_code_upload(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    raw = await file.read()
    filename = file.filename or "upload.txt"

    try:
        from src.services.file_parser import parse_file
        result = await parse_file(raw, filename)
        content = result.text
    except ValueError:
        return {"filename": filename, "status": "unsupported_format",
                "supported": [".txt", ".docx", ".pdf"]}
    except Exception as e:
        logger.warning(f"File parse failed for '{filename}': {e}")
        return {"filename": filename, "status": "parse_error", "error": str(e)}

    if not content.strip():
        return {"filename": filename, "status": "empty_content"}

    record = nlp_parser.parse("discharge", content)
    return {
        "filename": filename,
        "file_type": result.file_type,
        "status": "parsed",
        "content": content,
        "text_length": len(content),
        "page_count": result.page_count,
        "parse_time_ms": int(result.parse_time_ms),
        "diagnosis_count": len(record.diagnoses),
        "surgery_count": len(record.surgeries),
    }


@router.post("/validate")
async def validate_coding(coding: CodingResponse, user: dict = Depends(get_current_user)):
    patient_info = {"gender": "male"}
    errors = []
    warnings = []
    if coding.primary_diagnosis:
        code = coding.primary_diagnosis.code
        if code.startswith("N70"):
            warnings.append(f"编码 {code} 可能不适用于当前患者性别")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


@router.get("/search")
async def search_icd(keyword: str, limit: int = 20, user: dict = Depends(get_current_user)):
    results = await icd_coder.search_by_keyword(keyword, limit)
    return {"keyword": keyword, "results": [{"code": r.code, "name": r.name, "score": r.score} for r in results]}
