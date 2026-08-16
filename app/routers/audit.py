from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.models.models import AuditEvent, ActionRequest, Approval, ApprovalStatus, Decision

router = APIRouter(tags=["Audit & Dashboard"])


@router.get("/audit", response_model=list[AuditEvent])
def list_audit_events(project: str = "default", session: Session = Depends(get_session)):
    return session.exec(
        select(AuditEvent).where(AuditEvent.project == project).order_by(AuditEvent.created_at.desc())
    ).all()


@router.get("/dashboard/overview")
def dashboard_overview(project: str = "default", session: Session = Depends(get_session)):
    total = session.exec(
        select(func.count()).select_from(ActionRequest).where(ActionRequest.project == project)
    ).one()
    allowed = session.exec(
        select(func.count()).select_from(ActionRequest)
        .where(ActionRequest.project == project, ActionRequest.decision == Decision.ALLOW)
    ).one()
    blocked = session.exec(
        select(func.count()).select_from(ActionRequest)
        .where(ActionRequest.project == project, ActionRequest.decision == Decision.BLOCK)
    ).one()
    pending = session.exec(
        select(func.count()).select_from(Approval).where(Approval.status == ApprovalStatus.PENDING)
    ).one()
    tainted = session.exec(
        select(func.count()).select_from(ActionRequest)
        .where(ActionRequest.project == project, ActionRequest.provenance_tainted == True)  # noqa: E712
    ).one()

    return {
        "total_requests": total,
        "allowed": allowed,
        "blocked": blocked,
        "pending_approvals": pending,
        "provenance_tainted_requests": tainted,
    }
