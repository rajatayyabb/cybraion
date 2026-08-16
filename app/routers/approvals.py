from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.services.audit import log_event
from app.models.models import Approval, ApprovalStatus, ActionRequest

router = APIRouter(prefix="/approvals", tags=["Human Approval"])


@router.get("", response_model=list[Approval])
def list_pending_approvals(session: Session = Depends(get_session)):
    return session.exec(
        select(Approval).where(Approval.status == ApprovalStatus.PENDING)
    ).all()


@router.post("/{approval_id}/decide", response_model=Approval)
def decide_approval(
    approval_id: str,
    approve: bool,
    reviewer: str = "security_engineer",
    session: Session = Depends(get_session),
):
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Approval already resolved")

    approval.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.DENIED
    approval.reviewer = reviewer
    approval.resolved_at = datetime.utcnow()
    session.add(approval)
    session.commit()
    session.refresh(approval)

    action = session.get(ActionRequest, approval.action_request_id)
    log_event(
        session,
        project=action.project if action else "default",
        event_type="approval_decided",
        agent_name=action.agent_name if action else None,
        tool_name=action.tool_name if action else None,
        decision=approval.status.value,
        detail={"reviewer": reviewer, "approval_id": approval.id},
    )
    session.refresh(approval)
    return approval
