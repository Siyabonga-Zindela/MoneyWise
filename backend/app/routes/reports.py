"""Scam report endpoints - users file and track their own; admins see and moderate all."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..core.deps import client_ip, get_current_user, get_user_roles, require_admin
from ..core.security import hash_ip
from ..db.session import get_db
from ..models.enums import ReportStatus
from ..models.scam_report import ScamReport
from ..models.user import User
from ..repositories import reports as reports_repo
from ..repositories import reviews as reviews_repo
from ..schemas.common import Page
from ..schemas.report import ReportCreate, ReportOut, VisibilityUpdate
from ..schemas.review import ReviewOut
from ..services import report_service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScamReport:
    """File a new scam report. Duplicate content is LINKED, never merged (§8)."""
    return report_service.create_report(
        db, user, payload, ip_hash_value=hash_ip(client_ip(request))
    )


@router.get("", response_model=Page[ReportOut])
def list_reports(
    scope: str = Query(default="mine", pattern="^(mine|all)$"),
    status: ReportStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """scope=mine (default) lists my reports; scope=all is admin-only."""
    if scope == "all":
        if "ADMIN" not in get_user_roles(db, user.user_id):
            raise HTTPException(status_code=403, detail="Administrator privileges required")
        items, total = reports_repo.list_all(db, status=status, limit=limit, offset=offset)
    else:
        items, total = reports_repo.list_for_user(
            db, user.user_id, limit=limit, offset=offset
        )
    return Page(items=items, total=total, limit=limit, offset=offset)


def _report_or_denied(db: Session, report_id: int, user: User) -> ScamReport:
    report = reports_repo.get(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    is_admin = "ADMIN" in get_user_roles(db, user.user_id)
    if report.reporter_id != user.user_id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only access your own reports")
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScamReport:
    return _report_or_denied(db, report_id, user)


@router.get("/{report_id}/reviews", response_model=list[ReviewOut])
def report_reviews(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Decision trail for a report (owner or admin)."""
    report = _report_or_denied(db, report_id, user)
    return reviews_repo.list_for_report(db, report.report_id)


@router.patch("/{report_id}/visibility", response_model=ReportOut)
def set_visibility(
    report_id: int,
    payload: VisibilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ScamReport:
    """Admin-only: publish/unpublish a report (identity-safe, off by default)."""
    report = reports_repo.get(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_service.set_visibility(
        db, admin, report, payload, ip_hash_value=hash_ip(client_ip(request))
    )
