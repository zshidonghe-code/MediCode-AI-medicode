"""医保拒付风险预测 API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from src.api.v1.endpoints.auth import get_current_user
from src.services.rejection_risk import RiskLevel, rejection_engine

router = APIRouter()


class DiagItem(BaseModel):
    code: str
    name: str


class ProcItem(BaseModel):
    code: str
    name: str


class DRGInfo(BaseModel):
    drg_code: str = ""
    drg_name: str = ""
    weight: float = 1.0
    avg_los: float = 7.0


class PatientInfo(BaseModel):
    age: int = 0
    gender: str = ""
    days_of_stay: int = 0


class RejectionRequest(BaseModel):
    primary_diagnosis: Optional[DiagItem] = None
    secondary_diagnoses: list[DiagItem] = []
    procedures: list[ProcItem] = []
    drg_result: Optional[DRGInfo] = None
    patient_info: Optional[PatientInfo] = None
    content: str = ""
    hospital_cost: float = 0.0


class RejectionRiskItem(BaseModel):
    rule_id: str
    rule_name: str
    risk_level: RiskLevel
    description: str
    affected_code: str = ""
    suggestion: str = ""
    estimated_loss: float = 0.0


class RejectionResponse(BaseModel):
    overall_risk: RiskLevel
    risk_score: int = Field(ge=0, le=100)
    preventable_amount: float
    risks: list[RejectionRiskItem]


@router.post("/assess", response_model=RejectionResponse)
async def assess_rejection_risk(
    req: RejectionRequest,
    user: dict = Depends(get_current_user),
):
    """评估当前编码组合的医保拒付风险"""
    report = rejection_engine.assess(
        primary_diag=req.primary_diagnosis.model_dump() if req.primary_diagnosis else {},
        secondary_diags=[d.model_dump() for d in req.secondary_diagnoses],
        procedures=[p.model_dump() for p in req.procedures],
        drg_result=req.drg_result.model_dump() if req.drg_result else None,
        patient_info=req.patient_info.model_dump() if req.patient_info else None,
        content=req.content,
        hospital_cost=req.hospital_cost,
    )
    return RejectionResponse(
        overall_risk=report.overall_risk,
        risk_score=report.risk_score,
        preventable_amount=report.preventable_amount,
        risks=[
            RejectionRiskItem(
                rule_id=r.rule_id,
                rule_name=r.rule_name,
                risk_level=r.risk_level,
                description=r.description,
                affected_code=r.affected_code,
                suggestion=r.suggestion,
                estimated_loss=r.estimated_loss,
            )
            for r in report.risks
        ],
    )
