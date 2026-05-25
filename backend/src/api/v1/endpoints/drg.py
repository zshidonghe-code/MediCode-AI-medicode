import re
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from src.services.drg_grouper.grouper import drg_grouper
from src.models.database import async_session
from src.models.icd import DRGGroup
from src.config.settings import get_settings
from src.api.v1.endpoints.auth import get_current_user
from sqlalchemy import select

router = APIRouter()
settings = get_settings()

ICD_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\w{1,5})?$")


class DRGRequest(BaseModel):
    patient_age: int = Field(default=50, ge=0, le=150)
    patient_gender: Literal["male", "female"] = "male"
    primary_diagnosis_code: str = Field(..., min_length=3, max_length=16)
    secondary_diagnosis_codes: list[str] = Field(default=[], max_length=30)
    procedure_codes: list[str] = Field(default=[], max_length=30)
    days_of_stay: int = Field(default=0, ge=0, le=365)
    newborn_weight: Optional[int] = Field(default=None, ge=0, le=10000)
    ventilation_hours: Optional[int] = Field(default=None, ge=0, le=10000)

    @field_validator("primary_diagnosis_code")
    @classmethod
    def validate_icd_format(cls, v: str) -> str:
        if not ICD_PATTERN.match(v):
            raise ValueError(f"无效的ICD编码格式: {v}")
        return v

    @field_validator("secondary_diagnosis_codes")
    @classmethod
    def validate_secondary_codes(cls, v: list[str]) -> list[str]:
        for code in v:
            if not ICD_PATTERN.match(code):
                raise ValueError(f"无效的ICD编码: {code}")
        return v


class DRGResponse(BaseModel):
    mdc: str = ""
    mdc_name: str = ""
    adrg: str = ""
    adrg_name: str = ""
    drg_code: str = ""
    drg_name: str = ""
    is_surgical: bool = False
    weight: float = 0.0
    rate: float = 0.0
    estimated_payment: float = 0.0
    cc_flag: str = ""
    patient_complexity: str = ""


@router.post("/group", response_model=DRGResponse)
async def group_drg(request: DRGRequest, user: dict = Depends(get_current_user)):
    result = drg_grouper.group(
        primary_diag_code=request.primary_diagnosis_code,
        secondary_diag_codes=request.secondary_diagnosis_codes,
        procedure_codes=request.procedure_codes,
        patient_info={
            "gender": request.patient_gender,
            "age": request.patient_age,
            "days_of_stay": request.days_of_stay,
            "newborn_weight": request.newborn_weight,
        },
    )
    return DRGResponse(
        mdc=result.mdc,
        mdc_name=result.mdc_name,
        adrg=result.adrg,
        adrg_name=result.adrg_name,
        drg_code=result.drg_code,
        drg_name=result.drg_name,
        is_surgical=result.is_surgical,
        weight=result.weight,
        rate=result.rate,
        estimated_payment=result.estimated_payment,
        cc_flag=result.cc_flag,
        patient_complexity=result.patient_complexity,
    )


@router.get("/group/{drg_code}")
async def get_drg_detail(drg_code: str, user: dict = Depends(get_current_user)):
    """查询DRG详情（优先查数据库，fallback到分组器）"""
    async with async_session() as db:
        result = (await db.execute(
            select(DRGGroup).where(DRGGroup.code == drg_code)
        )).scalar_one_or_none()
        if result:
            return {
                "drg_code": result.code,
                "name": result.name,
                "mdc": result.mdc,
                "is_surgical": result.is_surgical,
                "weight": result.weight,
                "rate": result.rate,
                "avg_days": result.avg_days,
            }
    raise HTTPException(status_code=404, detail=f"DRG code '{drg_code}' not found")


@router.get("/compare")
async def compare_drg(record_id: int, ai_drg: str = "", manual_drg: str = "",
                       user: dict = Depends(get_current_user)):
    """对比AI与人工分组差异，自动计算费用差额"""
    ai_weight = 1.0
    manual_weight = 1.0
    async with async_session() as db:
        ai_row = (await db.execute(
            select(DRGGroup.weight).where(DRGGroup.code == ai_drg)
        )).scalar_one_or_none()
        if ai_row:
            ai_weight = ai_row
        manual_row = (await db.execute(
            select(DRGGroup.weight).where(DRGGroup.code == manual_drg)
        )).scalar_one_or_none()
        if manual_row:
            manual_weight = manual_row

    rate = settings.drg_base_rate
    same = ai_drg == manual_drg
    gap = 0.0 if same else abs(ai_weight - manual_weight) * rate
    return {
        "same": same,
        "ai_drg": ai_drg,
        "manual_drg": manual_drg,
        "ai_weight": round(ai_weight, 2),
        "manual_weight": round(manual_weight, 2),
        "payment_gap": round(gap, 2),
    }
