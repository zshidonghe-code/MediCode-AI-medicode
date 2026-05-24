"""管理员端点：数据重置与导出"""

import io
import csv
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, delete, func

from src.api.v1.endpoints.auth import require_admin
from src.config.settings import get_settings
from src.models.database import async_session
from src.models.icd import CodingResult
from src.models.patient import Patient, MedicalRecord
from src.models.qc import QCRule, QCResult, CodingLog

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ── Pydantic models ──────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    confirm: bool = False


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row.values())
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _make_json_response(data: list[dict], filename: str) -> StreamingResponse:
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _make_export(data: list[dict], filename: str, fmt: str) -> StreamingResponse:
    if fmt == "csv":
        return _make_csv_response(data, filename.replace(".json", ".csv"))
    return _make_json_response(data, filename)


# ── Reset ────────────────────────────────────────────────────────────────

@router.post("/reset")
async def reset_data(body: ResetRequest, _admin: dict = Depends(require_admin)):
    """重置用户数据（保留 ICD、DRG、QC 规则等参考数据）"""
    async with async_session() as db:
        # 1. Count what would be deleted
        tables = {
            "coding_logs": CodingLog,
            "qc_results": QCResult,
            "coding_results": CodingResult,
            "medical_records": MedicalRecord,
            "patients": Patient,
        }
        counts = {}
        for name, model in tables.items():
            r = await db.execute(select(func.count()).select_from(model))
            counts[name] = r.scalar() or 0

        if not body.confirm:
            return {
                "preview": True,
                "message": f"将清空 {sum(counts.values())} 条记录（{', '.join(f'{k}:{v}条' for k, v in counts.items())}），" +
                           f"参考数据（icd_codes/drg_groups/qc_rules）不受影响。发送 confirm=true 确认执行。",
                "counts": counts,
            }

        # 2. Execute deletion in FK-safe order
        deleted = {}
        for name, model in tables.items():
            r = await db.execute(delete(model))
            deleted[name] = r.rowcount

        # 3. Reset SQLite autoincrement counters
        try:
            from sqlalchemy import text
            await db.execute(text(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('coding_logs', 'qc_results', 'coding_results', 'medical_records', 'patients')"
            ))
        except Exception:
            pass  # Non-SQLite or table doesn't exist

        await db.commit()
        logger.info(f"Data reset by admin: {deleted}")
        return {"success": True, "deleted": deleted}


# ── Export ───────────────────────────────────────────────────────────────

@router.get("/export/coding-results")
async def export_coding_results(
    format: str = Query("json", pattern="^(json|csv)$"),
    _admin: dict = Depends(require_admin),
):
    """导出编码结果"""
    async with async_session() as db:
        r = await db.execute(
            select(CodingResult, MedicalRecord.record_type)
            .join(MedicalRecord, CodingResult.record_id == MedicalRecord.id, isouter=True)
        )
        rows = []
        for cr, rec_type in r.all():
            codes = cr.codes if isinstance(cr.codes, dict) else {}
            conf = cr.confidence_scores if isinstance(cr.confidence_scores, dict) else {}

            def _extract_codes(items) -> str:
                """Flatten dict items like {code, name} or plain strings to pipe-delimited codes."""
                if not items:
                    return ""
                result = []
                for item in items:
                    if isinstance(item, dict):
                        result.append(item.get("code", str(item)))
                    else:
                        result.append(str(item))
                return "|".join(result)

            def _extract_primary(val) -> str:
                if isinstance(val, dict):
                    return val.get("code", "")
                return str(val) if val else ""

            rows.append({
                "id": cr.id,
                "record_id": cr.record_id,
                "record_type": rec_type or "",
                "coder_type": cr.coder_type,
                "primary_diagnosis_code": _extract_primary(codes.get("primary", "")),
                "secondary_diagnosis_codes": _extract_codes(codes.get("secondary", [])),
                "procedure_codes": _extract_codes(codes.get("procedures", [])),
                "confidence": conf.get("total", 0),
                "is_final": cr.is_final,
                "created_at": cr.created_at.isoformat() if cr.created_at else "",
            })
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return _make_export(rows, f"medicode_coding_results_{ts}.json", format)


@router.get("/export/patient-summaries")
async def export_patient_summaries(
    format: str = Query("json", pattern="^(json|csv)$"),
    _admin: dict = Depends(require_admin),
):
    """导出患者摘要"""
    async with async_session() as db:
        r = await db.execute(select(Patient))
        patients = r.scalars().all()

        # Fetch all medical records in one query, grouped by patient
        all_records = (await db.execute(
            select(MedicalRecord.patient_id, MedicalRecord.record_type, MedicalRecord.department)
        )).all()
        records_by_patient: dict[int, list] = {}
        for rec in all_records:
            records_by_patient.setdefault(rec.patient_id, []).append(rec)

        rows = []
        for p in patients:
            records = records_by_patient.get(p.id, [])
            rows.append({
                "patient_id": p.patient_id,
                "gender": p.gender.value if p.gender else "",
                "age": p.age,
                "birth_year": p.birth_year,
                "total_records": len(records),
                "departments": "|".join(sorted(set(r.department for r in records if r.department))),
                "created_at": p.created_at.isoformat() if p.created_at else "",
            })
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return _make_export(rows, f"medicode_patient_summaries_{ts}.json", format)


@router.get("/export/qc-results")
async def export_qc_results(
    format: str = Query("json", pattern="^(json|csv)$"),
    _admin: dict = Depends(require_admin),
):
    """导出质控结果"""
    async with async_session() as db:
        r = await db.execute(
            select(QCResult, MedicalRecord.record_type, QCRule.rule_name)
            .join(MedicalRecord, QCResult.record_id == MedicalRecord.id, isouter=True)
            .join(QCRule, QCResult.rule_id == QCRule.id, isouter=True)
        )
        rows = []
        for qr, rec_type, rule_name in r.all():
            rows.append({
                "id": qr.id,
                "record_id": qr.record_id,
                "record_type": rec_type or "",
                "severity": qr.severity.value if qr.severity else "",
                "rule_name": rule_name or "",
                "line_snippet": qr.line_snippet or "",
                "suggestion": qr.suggestion or "",
                "is_accepted": qr.is_accepted,
                "created_at": qr.created_at.isoformat() if qr.created_at else "",
            })
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return _make_export(rows, f"medicode_qc_results_{ts}.json", format)
