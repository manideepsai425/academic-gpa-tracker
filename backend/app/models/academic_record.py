"""
AcademicRecord model — matches the data model in the brief exactly:
id, user_id, period, type, gpa, marks, max_marks, date, notes.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RecordType(str, enum.Enum):
    SCHOOL = "School"
    INTERMEDIATE = "Intermediate"
    COLLEGE = "College"


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    period: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Semester 3"
    type: Mapped[RecordType] = mapped_column(Enum(RecordType), nullable=False)
    gpa: Mapped[float] = mapped_column(Float, nullable=False)  # 0–10 scale
    marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    owner = relationship("User", back_populates="records")
