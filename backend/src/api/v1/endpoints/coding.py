import time
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal as LiteralType
from src.services.nlp_engine.engine import nlp_parser
from src.services.icd_coder.coder import icd_coder, ICDCandidate
from src.services.icd_coder.scoring import primary_score, conflicts
from src.api.v1.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


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


# ── Module-level helpers ─────────────────────────────────────────────────────


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

        diag_items.sort(key=lambda item: primary_score(
            item.code, item.confidence, cardiac=has_cardiac_proc, ortho=has_ortho_proc, neuro=has_neuro_proc), reverse=True)
        primary = diag_items[0]
        primary.is_primary = True

        # Build secondaries: filter same-category sub-codes, keep top 9
        secondaries = []
        primary_prefix = primary.code.split(".")[0] if primary else ""
        for item in diag_items[1:]:
            item_prefix = item.code.split(".")[0]
            # Skip codes with very low adjusted score
            if primary_score(item.code, item.confidence) < 0.1:
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
            if any(conflicts(item.code, kc) for kc in kept_codes):
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
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="文件大小不能超过10MB")
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



class ValidateRequest(BaseModel):
    coding: CodingResponse
    patient_gender: LiteralType["male", "female"] = "male"
    patient_age: int = Field(default=0, ge=0, le=150)


@router.post("/validate")
async def validate_coding(request: ValidateRequest, user: dict = Depends(get_current_user)):
    patient_info = {"gender": request.patient_gender, "age": request.patient_age}
    errors: list[str] = []
    warnings: list[str] = []
    if request.coding.primary_diagnosis:
        code = request.coding.primary_diagnosis.code
        gender = request.patient_gender
        if gender == "male" and any(code.startswith(p) for p in ["N70", "N80", "O00"]):
            errors.append(f"编码 {code} 不适用于男性患者（女性特有诊断）")
        if gender == "female" and code.startswith("N40"):
            errors.append(f"编码 {code} 不适用于女性患者（男性特有诊断）")
        for prefix in ["R00", "R05", "R06", "R07", "R09", "R10", "R11",
                       "R50", "R51", "R52", "R53", "R54", "R55", "R56"]:
            if code.startswith(prefix):
                warnings.append(f"编码 {code} 为症状编码，不宜作为主要诊断")
        if code.startswith("Z"):
            warnings.append(f"编码 {code} 为健康状态编码，不宜作为主要诊断")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


@router.get("/search")
async def search_icd(keyword: str, limit: int = 20, user: dict = Depends(get_current_user)):
    results = await icd_coder.search_by_keyword(keyword, limit)
    return {"keyword": keyword, "results": [{"code": r.code, "name": r.name, "score": r.score} for r in results]}
