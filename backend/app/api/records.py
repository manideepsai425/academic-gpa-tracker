"""
Academic record routes: full CRUD, scoped to the authenticated user,
plus the /dashboard endpoint that returns pre-computed trend data.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud.academic_record import (
    build_dashboard_summary,
    create_record,
    delete_record,
    get_record,
    get_records_for_user,
    update_record,
)
from app.models.user import User
from app.schemas.academic_record import (
    AcademicRecordCreate,
    AcademicRecordOut,
    AcademicRecordUpdate,
    DashboardSummary,
)

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("", response_model=List[AcademicRecordOut])
def list_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_records_for_user(db, current_user.id)


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = get_records_for_user(db, current_user.id)
    return build_dashboard_summary(records)


@router.post("", response_model=AcademicRecordOut, status_code=status.HTTP_201_CREATED)
def add_record(
    record_in: AcademicRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_record(db, record_in, current_user.id)


@router.patch("/{record_id}", response_model=AcademicRecordOut)
def edit_record(
    record_id: int,
    record_in: AcademicRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_record(db, record_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return update_record(db, record, record_in)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_record(db, record_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    delete_record(db, record)
