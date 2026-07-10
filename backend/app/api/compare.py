"""
Comparison route.

Deliberately stateless and disconnected from the user account system:
this endpoint takes up to 5 manually-typed (label, marks, max_marks)
entries and returns computed percentages. Nothing here is persisted,
and it does NOT look up other users' accounts or records.

This is intentional, not an oversight — see the earlier discussion in
the project's design: a "compare 5 people" feature that looked up
other real users' full academic histories by username would expose
every user's complete record (including backlogs, low semesters, etc.)
to any of the 100+ people on the platform with zero consent involved.
A manual-entry scratch-pad avoids that entirely, since it never touches
any account other than the one making the request.

Still protected by login (not open to the public internet) simply to
keep it consistent with the rest of the API and to prevent anonymous
abuse of the endpoint — but it does not require or use any other
user's data.
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.academic_record import ComparisonRequest, ComparisonResult

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", response_model=list[ComparisonResult])
def compare_marks(
    payload: ComparisonRequest,
    current_user: User = Depends(get_current_user),
):
    return [
        ComparisonResult(
            label=entry.label,
            marks=entry.marks,
            max_marks=entry.max_marks,
            percentage=entry.percentage,
        )
        for entry in payload.entries
    ]
