"""
CRUD operations for academic records, plus the trend calculation that
turns a flat list of records into rise/decline percentages.
"""
from typing import List, Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.models.academic_record import AcademicRecord
from app.schemas.academic_record import (
    AcademicRecordCreate,
    AcademicRecordUpdate,
    DashboardSummary,
    TrendPoint,
)


def get_records_for_user(db: Session, user_id: int) -> List[AcademicRecord]:
    """Always returns records ordered oldest-to-newest by date â€” every
    trend and chart calculation downstream depends on this ordering,
    so it's centralised here rather than re-sorted in multiple places."""
    return (
        db.query(AcademicRecord)
        .filter(AcademicRecord.user_id == user_id)
        .order_by(asc(AcademicRecord.date))
        .all()
    )


def get_record(db: Session, record_id: int, user_id: int) -> Optional[AcademicRecord]:
    """Scoped to user_id as well as record_id â€” this is the line that
    stops user A from editing or deleting user B's record by guessing
    an id. Every mutating endpoint must call this, never a bare
    id-only lookup."""
    return (
        db.query(AcademicRecord)
        .filter(AcademicRecord.id == record_id, AcademicRecord.user_id == user_id)
        .first()
    )


def create_record(db: Session, record_in: AcademicRecordCreate, user_id: int) -> AcademicRecord:
    record = AcademicRecord(**record_in.model_dump(), user_id=user_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_record(
    db: Session, record: AcademicRecord, record_in: AcademicRecordUpdate
) -> AcademicRecord:
    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record: AcademicRecord) -> None:
    db.delete(record)
    db.commit()


def _percent_change(previous: float, current: float) -> float:
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def _direction(change: float) -> str:
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def build_dashboard_summary(records: List[AcademicRecord]) -> DashboardSummary:
    """Builds the trend list (ðŸ“ˆ/ðŸ“‰ per semester) and the top-line
    summary cards from a chronologically-ordered list of records.

    Percentage change is computed on the GPA value itself,
    semester-over-semester â€” see the note in
    app/schemas/academic_record.py for why."""
    if not records:
        return DashboardSummary(
            total_records=0,
            current_gpa=None,
            highest_gpa=None,
            lowest_gpa=None,
            overall_change_percent=None,
            overall_direction=None,
            trend=[],
        )

    trend: List[TrendPoint] = []
    for i, record in enumerate(records):
        if i == 0:
            change_percent = None
            direction = None
        else:
            change_percent = _percent_change(records[i - 1].gpa, record.gpa)
            direction = _direction(change_percent)

        trend.append(
            TrendPoint(
                id=record.id,
                period=record.period,
                type=record.type,
                gpa=record.gpa,
                date=record.date,
                change_percent=change_percent,
                direction=direction,
            )
        )

    gpas = [r.gpa for r in records]
    overall_change = _percent_change(records[0].gpa, records[-1].gpa) if len(records) > 1 else None
    overall_direction = _direction(overall_change) if overall_change is not None else None

    return DashboardSummary(
        total_records=len(records),
        current_gpa=records[-1].gpa,
        highest_gpa=max(gpas),
        lowest_gpa=min(gpas),
        overall_change_percent=overall_change,
        overall_direction=overall_direction,
        trend=trend,
    )
