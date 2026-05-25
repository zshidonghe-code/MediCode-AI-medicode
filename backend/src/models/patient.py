from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey, Float, Boolean, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime, timezone
import enum
from src.models.database import Base


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_hash: Mapped[str] = mapped_column(String(128))
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender))
    age: Mapped[int] = mapped_column(Integer)
    birth_year: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    records: Mapped[list["MedicalRecord"]] = relationship(back_populates="patient")


class RecordType(str, enum.Enum):
    ADMISSION = "admission"          # 入院记录
    COURSE = "course"                 # 病程记录
    SURGERY = "surgery"              # 手术记录
    DISCHARGE = "discharge"          # 出院小结
    CONSULTATION = "consultation"    # 会诊记录
    EXAM = "exam"                    # 检查报告
    LAB = "lab"                      # 检验报告


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    record_type: Mapped[RecordType] = mapped_column(SAEnum(RecordType))
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(String(128), index=True)
    doctor_hash: Mapped[str] = mapped_column(String(128))
    admission_date: Mapped[date] = mapped_column(Date, nullable=True, index=True)
    discharge_date: Mapped[date] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient: Mapped[Patient] = relationship(back_populates="records")
    coding_results: Mapped[list["CodingResult"]] = relationship(back_populates="record")
    qc_results: Mapped[list["QCResult"]] = relationship(back_populates="record")
