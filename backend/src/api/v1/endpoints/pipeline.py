import logging
import hashlib
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.v1.endpoints.auth import get_current_user
from src.models.database import async_session
from src.models.patient import Patient, MedicalRecord, Gender, RecordType
from src.models.icd import CodingResult
from src.models.qc import QCResult, QCSeverity

logger = logging.getLogger(__name__)
router = APIRouter()


class PipelineSaveRequest(BaseModel):
    content: str
    record_type: str = "discharge"
    coding_result: dict
    qc_result: dict | None = None
    drg_result: dict | None = None


@router.post("/save")
async def save_pipeline_result(req: PipelineSaveRequest, user: dict = Depends(get_current_user)):
    """保存流水线全链路结果到数据库，供 Dashboard 展示"""
    async with async_session() as db:
        # 1. Create patient
        content_hash = hashlib.sha256(req.content.encode()).hexdigest()
        patient_id_str = f"PIPE{content_hash[:8].upper()}"
        patient = Patient(
            patient_id=patient_id_str,
            name_hash=hashlib.sha256(user.get("name", "user").encode()).hexdigest()[:64],
            gender=Gender.MALE,
            age=50,
            birth_year=date.today().year - 50,
        )
        db.add(patient)
        await db.flush()

        # 2. Create medical record
        record = MedicalRecord(
            patient_id=patient.id,
            record_type=RecordType.DISCHARGE if req.record_type == "discharge" else RecordType.ADMISSION,
            title=f"流水线分析 - {patient_id_str}",
            content=req.content,
            department="流水线",
            doctor_hash=hashlib.sha256(user.get("name", "user").encode()).hexdigest()[:64],
            admission_date=date.today(),
            discharge_date=date.today(),
        )
        db.add(record)
        await db.flush()

        # 3. Save coding result
        coding = req.coding_result
        primary_code = coding.get("primary_diagnosis") or {}
        if isinstance(primary_code, dict):
            pri_code = primary_code.get("code", "")
            pri_name = primary_code.get("name", "")
        else:
            pri_code = str(primary_code) if primary_code else ""
            pri_name = ""

        secondary = []
        for s in coding.get("secondary_diagnoses", []):
            if isinstance(s, dict):
                secondary.append({"code": s.get("code", ""), "name": s.get("name", "")})

        procedures = []
        for p in coding.get("procedures", []):
            if isinstance(p, dict):
                procedures.append({"code": p.get("code", ""), "name": p.get("name", "")})

        drg = req.drg_result or {}
        codes_dict = {
            "primary": {"code": pri_code, "name": pri_name},
            "secondary": secondary,
            "procedures": procedures,
            "drg_code": drg.get("drg_code", ""),
            "drg_weight": drg.get("weight", 0),
        }

        coding_result = CodingResult(
            record_id=record.id,
            coder_type="ai",
            codes=codes_dict,
            confidence_scores={"total": coding.get("total_confidence", 0)},
            suggestions=[],
            revision=1,
            is_final=True,
        )
        db.add(coding_result)

        # 4. Save QC results
        qc_result_ids = []
        if req.qc_result:
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
                db.add(qc)
                await db.flush()
                qc_result_ids.append({"id": qc.id, "severity": severity_str})

        await db.commit()

        return {
            "success": True,
            "patient_id": patient_id_str,
            "record_id": record.id,
            "coding_result_id": coding_result.id,
            "qc_result_ids": qc_result_ids,
        }
