import logging
import hashlib
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.v1.endpoints.auth import get_current_user
from src.models.database import async_session
from src.models.patient import Patient, MedicalRecord, Gender, RecordType
from src.models.icd import CodingResult
from src.models.qc import QCResult, QCSeverity

logger = logging.getLogger(__name__)
router = APIRouter()


class PipelineSaveRequest(BaseModel):
    content: str | None = None
    record_type: str = "discharge"
    coding_result: dict | None = None
    qc_result: dict | None = None
    drg_result: dict | None = None
    department: str = "流水线"
    patient_info: dict | None = None
    primary_diagnosis_code: str | None = None
    secondary_diagnosis_codes: list[str] | None = None
    procedure_codes: list[str] | None = None


def _extract_diag_names(coding: dict) -> str:
    """从 coding_result 中提取诊断名称，用于生成 content"""
    names = []
    pri = coding.get("primary_diagnosis") or {}
    if isinstance(pri, dict) and pri.get("name"):
        names.append(pri["name"])
    for s in coding.get("secondary_diagnoses", []):
        if isinstance(s, dict) and s.get("name"):
            names.append(s["name"])
    for p in coding.get("procedures", []):
        if isinstance(p, dict) and p.get("name"):
            names.append(p["name"])
    return "诊断: " + ", ".join(names) if names else ""


@router.post("/save")
async def save_pipeline_result(req: PipelineSaveRequest, user: dict = Depends(get_current_user)):
    """保存流水线全链路结果到数据库，供 Dashboard 展示
    支持四种场景：全流水线 / 仅编码 / 仅质控 / 仅DRG"""
    try:
        return await _do_save(req, user)
    except Exception:
        logger.exception("Pipeline save failed")
        raise


async def _do_save(req: PipelineSaveRequest, user: dict):
    async with async_session() as db:
        # --- Resolve content ---
        content = req.content or ""
        if not content:
            parts = []
            if req.coding_result:
                parts.append(_extract_diag_names(req.coding_result))
            if req.drg_result:
                drg_parts = []
                if req.primary_diagnosis_code:
                    drg_parts.append(req.primary_diagnosis_code)
                if req.secondary_diagnosis_codes:
                    drg_parts.extend(req.secondary_diagnosis_codes)
                if req.procedure_codes:
                    drg_parts.extend(req.procedure_codes)
                if drg_parts:
                    parts.append("编码: " + ", ".join(drg_parts))
            content = "; ".join(parts) if parts else f"{req.department} - 自动生成记录"

        # --- Patient demographics ---
        patient_info = req.patient_info or {}
        age = patient_info.get("age", 50)
        gender_str = patient_info.get("gender", "male")
        try:
            gender = Gender(gender_str)
        except ValueError:
            gender = Gender.MALE

        # --- Department-based prefix ---
        dept_prefix_map = {"智能编码": "CODE", "质控中心": "QC", "DRG分组": "DRG", "流水线": "PIPE"}
        prefix = dept_prefix_map.get(req.department, "REC")

        # 1. Find or create patient (IntegrityError-safe for concurrent requests)
        # Patient ID is derived from content hash for demo dedup — same medical
        # record text maps to the same patient. Production should use deterministic
        # matching on demographic fields (name, DOB, gender) instead.
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        patient_id_str = f"{prefix}{content_hash[:8].upper()}"
        existing = (await db.execute(
            select(Patient).where(Patient.patient_id == patient_id_str)
        )).scalar_one_or_none()
        if existing is not None:
            patient = existing
        else:
            patient = Patient(
                patient_id=patient_id_str,
                name_hash=hashlib.sha256(user.get("username", "user").encode()).hexdigest()[:64],
                gender=gender,
                age=age,
                birth_year=date.today().year - age,
            )
            db.add(patient)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                existing = (await db.execute(
                    select(Patient).where(Patient.patient_id == patient_id_str)
                )).scalar_one_or_none()
                if existing is not None:
                    patient = existing
                else:
                    raise

        # 2. Create medical record
        try:
            record_type = RecordType(req.record_type)
        except ValueError:
            record_type = RecordType.DISCHARGE
        record = MedicalRecord(
            patient_id=patient.id,
            record_type=record_type,
            title=f"{req.department}分析 - {patient_id_str}",
            content=content,
            department=req.department,
            doctor_hash=hashlib.sha256(user.get("name", "user").encode()).hexdigest()[:64],
            admission_date=date.today(),
            discharge_date=date.today(),
        )
        db.add(record)
        await db.flush()

        # 3. Save coding result (if any)
        has_coding = req.coding_result is not None or req.drg_result is not None
        if has_coding:
            if req.coding_result:
                coding_input = req.coding_result
                primary_code = coding_input.get("primary_diagnosis") or {}
                if isinstance(primary_code, dict):
                    pri_code = primary_code.get("code", "")
                    pri_name = primary_code.get("name", "")
                else:
                    pri_code = str(primary_code) if primary_code else ""
                    pri_name = ""
                secondary = []
                for s in coding_input.get("secondary_diagnoses", []):
                    if isinstance(s, dict):
                        secondary.append({"code": s.get("code", ""), "name": s.get("name", "")})
                procedures = []
                for p in coding_input.get("procedures", []):
                    if isinstance(p, dict):
                        procedures.append({"code": p.get("code", ""), "name": p.get("name", "")})
                confidence = coding_input.get("total_confidence", 0)
            else:
                # DRG-only: build minimal codes from the ICD code fields
                pri_code = req.primary_diagnosis_code or ""
                pri_name = ""
                secondary = [{"code": c, "name": ""} for c in (req.secondary_diagnosis_codes or [])]
                procedures = [{"code": c, "name": ""} for c in (req.procedure_codes or [])]
                confidence = 0

            drg = req.drg_result or {}
            codes_dict = {
                "primary": {"code": pri_code, "name": pri_name},
                "secondary": secondary,
                "procedures": procedures,
                "drg_code": drg.get("drg_code", ""),
                "drg_weight": drg.get("weight", 0),
            }

            coding = CodingResult(
                record_id=record.id,
                coder_type="ai",
                codes=codes_dict,
                confidence_scores={"total": confidence},
                suggestions={},
                revision=1,
                is_final=True,
            )
            db.add(coding)

        # 4. Save QC results
        qc_result_ids = []
        if req.qc_result:
            qc_rows = []
            for issue in req.qc_result.get("issues", []):
                severity_str = issue.get("severity", "minor")
                try:
                    severity = QCSeverity(severity_str)
                except ValueError:
                    severity = QCSeverity.MINOR
                qc = QCResult(
                    record_id=record.id,
                    rule_id=1,
                    severity=severity,
                    line_snippet=(issue.get("line_snippet") or issue.get("description") or "")[:200],
                    suggestion=issue.get("suggestion", ""),
                )
                qc_rows.append(qc)
            db.add_all(qc_rows)
            await db.flush()
            for qc, issue in zip(qc_rows, req.qc_result.get("issues", [])):
                qc_result_ids.append({"id": qc.id, "severity": issue.get("severity", "minor")})

        await db.commit()

        return {
            "success": True,
            "patient_id": patient_id_str,
            "record_id": record.id,
            "coding_result_id": coding.id if has_coding else None,
            "qc_result_ids": qc_result_ids,
        }
