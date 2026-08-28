import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.database import Base

if TYPE_CHECKING:
    from src.models.patient import MedicalRecord


class QCSeverity(str, enum.Enum):
    CRITICAL = "critical"  # 严重缺陷(医保拒付)
    MAJOR = "major"  # 重要缺陷(影响DRG分组)
    MINOR = "minor"  # 一般缺陷
    INFO = "info"  # 提示


class QCRuleType(str, enum.Enum):
    COMPLETENESS = "completeness"  # 完整性
    LOGIC = "logic"  # 逻辑一致性
    CODING = "coding"  # 编码一致性
    TIMELINESS = "timeliness"  # 时效性
    NORMALIZATION = "normalization"  # 规范表达
    SEMANTIC = "semantic"  # 语义质量


class QCRule(Base):
    __tablename__ = "qc_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(256))
    rule_type: Mapped[QCRuleType] = mapped_column(SAEnum(QCRuleType))
    severity: Mapped[QCSeverity] = mapped_column(SAEnum(QCSeverity))
    description: Mapped[str] = mapped_column(Text)
    check_function: Mapped[str] = mapped_column(String(256))  # 对应的检查函数名
    params: Mapped[dict] = mapped_column(JSON, default=dict)  # 检查参数
    is_active: Mapped[bool] = mapped_column(default=True)
    version: Mapped[int] = mapped_column(default=1)


class QCResult(Base):
    __tablename__ = "qc_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("medical_records.id", ondelete="CASCADE"), index=True
    )
    rule_id: Mapped[int] = mapped_column(ForeignKey("qc_rules.id", ondelete="CASCADE"), index=True)
    severity: Mapped[QCSeverity] = mapped_column(SAEnum(QCSeverity))
    line_snippet: Mapped[str] = mapped_column(Text, nullable=True)  # 缺陷文本片段
    suggestion: Mapped[str] = mapped_column(Text, nullable=True)  # 修改建议
    is_accepted: Mapped[bool] = mapped_column(default=False)  # 是否被采纳
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=True)  # 审核备注
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    record: Mapped["MedicalRecord"] = relationship(back_populates="qc_results")


class CodingLog(Base):
    __tablename__ = "coding_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("medical_records.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    changes: Mapped[dict] = mapped_column(JSON)
    operator: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    comment: Mapped[str] = mapped_column(Text, nullable=True)
