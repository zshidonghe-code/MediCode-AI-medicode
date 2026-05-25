from sqlalchemy import String, Integer, Float, Text, Enum as SAEnum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import enum
from src.models.database import Base


class ICDVersion(str, enum.Enum):
    ICD10_CLINICAL = "icd10_cn_clinical"      # ICD-10临床版(国标)
    ICD9_CM3 = "icd9_cm3"                     # ICD-9-CM-3 手术操作
    ICD10_WHO = "icd10_who"                   # ICD-10 WHO标准版


class ICDCode(Base):
    __tablename__ = "icd_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(512))
    category: Mapped[str] = mapped_column(String(64))           # 章节/大类
    subcategory: Mapped[str] = mapped_column(String(128), nullable=True)
    version: Mapped[ICDVersion] = mapped_column(SAEnum(ICDVersion))
    py_code: Mapped[str] = mapped_column(String(256))           # 拼音码
    search_terms: Mapped[dict] = mapped_column(JSON, default=dict)  # 同义词/别名
    gender_limit: Mapped[str] = mapped_column(String(1), nullable=True)  # M/F 性别限制
    age_min: Mapped[int] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int] = mapped_column(Integer, nullable=True)
    is_primary_only: Mapped[bool] = mapped_column(default=False)  # 只能做主诊断


class CodingResult(Base):
    __tablename__ = "coding_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("medical_records.id", ondelete="CASCADE"), index=True)
    coder_type: Mapped[str] = mapped_column(String(32), index=True)  # "ai" / "human" / "ai_reviewed"
    codes: Mapped[dict] = mapped_column(JSON)                     # {"primary": "I10.x00", "secondary": [...], "procedures": [...]}
    confidence_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[dict] = mapped_column(JSON, nullable=True)  # AI推荐的候选编码列表
    revision: Mapped[int] = mapped_column(default=1)
    is_final: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    record: Mapped["MedicalRecord"] = relationship(back_populates="coding_results")


class DRGGroup(Base):
    __tablename__ = "drg_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)  # DRG编码
    name: Mapped[str] = mapped_column(String(256))
    mdc: Mapped[str] = mapped_column(String(16))                    # 主要诊断大类
    adrg: Mapped[str] = mapped_column(String(16))                    # ADRG
    is_surgical: Mapped[bool] = mapped_column(default=False)        # 是否手术组
    weight: Mapped[float] = mapped_column(Float, default=1.0)      # RW权重
    rate: Mapped[float] = mapped_column(Float, default=0.0)        # 费率
    avg_days: Mapped[float] = mapped_column(Float, default=7.0)    # 平均住院日
    cc_threshold: Mapped[str] = mapped_column(Text, nullable=True)  # CC/MCC判定逻辑
