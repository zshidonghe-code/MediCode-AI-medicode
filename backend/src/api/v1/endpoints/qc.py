import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select

from src.services.qc_engine.engine import qc_engine, Severity, RuleType
from src.api.v1.endpoints.auth import get_current_user
from src.models.database import async_session
from src.models.qc import QCResult

router = APIRouter()


class QCRequest(BaseModel):
    record_id: int
    record_type: str
    content: str
    coding_result: Optional[dict] = None
    patient_info: Optional[dict] = None
    use_llm: bool = False  # 默认关闭LLM，用规则引擎保证快速响应


class QCIssueOut(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    severity: str
    description: str = ""
    line_snippet: str
    suggestion: str
    line_number: Optional[int] = None


class QCResponse(BaseModel):
    record_id: int
    total_issues: int
    critical_count: int
    major_count: int
    minor_count: int
    info_count: int
    issues: list[QCIssueOut] = []
    qc_score: float = 0.0
    processing_time_ms: int = 0


@router.post("/check", response_model=QCResponse)
async def run_qc_check(request: QCRequest, user: dict = Depends(get_current_user)):
    t0 = time.time()
    result = await qc_engine.check(
        record_type=request.record_type,
        content=request.content,
        coding_result=request.coding_result,
        patient_info=request.patient_info,
        use_llm=request.use_llm,
    )
    issues_out = [
        QCIssueOut(
            rule_id=i.rule_id,
            rule_name=i.rule_name,
            rule_type=i.rule_type.value if isinstance(i.rule_type, RuleType) else i.rule_type,
            severity=i.severity.value if isinstance(i.severity, Severity) else i.severity,
            description=i.description,
            line_snippet=i.line_snippet,
            suggestion=i.suggestion,
            line_number=i.line_number if i.line_number else None,
        )
        for i in result.issues
    ]
    return QCResponse(
        record_id=request.record_id or result.record_id,
        total_issues=result.total,
        critical_count=result.critical_count,
        major_count=result.major_count,
        minor_count=result.minor_count,
        info_count=result.info_count,
        issues=issues_out,
        qc_score=round(result.score, 1),
        processing_time_ms=int((time.time() - t0) * 1000),
    )


@router.get("/rules")
async def list_qc_rules(rule_type: str = "", severity: str = "", user: dict = Depends(get_current_user)):
    rules = []
    for r in qc_engine.rules:
        rt = r["type"].value if isinstance(r["type"], RuleType) else str(r["type"])
        sv = r["severity"].value if isinstance(r["severity"], Severity) else str(r["severity"])
        if rule_type and rt != rule_type:
            continue
        if severity and sv != severity:
            continue
        rules.append({
            "id": r["id"],
            "name": r["name"],
            "type": rt,
            "severity": sv,
            "suggestion": r.get("suggestion", ""),
        })
    return {"rules": rules, "total": len(rules)}


async def _update_qc_acceptance(result_id: int, accepted: bool) -> dict:
    async with async_session() as db:
        r = (await db.execute(select(QCResult).where(QCResult.id == result_id))).scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="质控结果不存在")
        r.is_accepted = accepted
        await db.commit()
    return {"result_id": result_id, "accepted": accepted}


@router.put("/results/{result_id}/accept")
async def accept_qc_result(result_id: int, user: dict = Depends(get_current_user)):
    return await _update_qc_acceptance(result_id, True)


@router.put("/results/{result_id}/reject")
async def reject_qc_result(result_id: int, user: dict = Depends(get_current_user)):
    return await _update_qc_acceptance(result_id, False)
