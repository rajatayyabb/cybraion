"""
The Action Gateway.

This is the single most important endpoint in CYBRAION. An AI agent must
call POST /actions/request instead of calling a real tool directly. The
request is evaluated by the deterministic Policy Engine (never by an LLM)
and CYBRAION returns ALLOW / BLOCK / REQUIRE_APPROVAL. The caller (your
demo "tool executor") must only actually perform the real action when it
receives ALLOW, or after a pending REQUIRE_APPROVAL is later approved.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.policy_engine import evaluate
from app.services.audit import log_event
from app.services.detection import scan_content_for_injection
from app.models.models import (
    ActionRequest,
    Approval,
    ApprovalStatus,
    Decision,
)

router = APIRouter(prefix="/actions", tags=["Action Gateway"])


@router.post("/request", response_model=ActionRequest)
def request_action(action: ActionRequest, session: Session = Depends(get_session)):
    """
    Submit an action request for authorization.

    If the request includes `provenance_source` pointing at upstream
    content that hasn't been scanned yet, pass the raw content via
    `parameters["_provenance_content"]` and CYBRAION will scan it for
    embedded/hidden instructions before evaluating policy. This is what
    powers the provenance-aware detection described in the project's
    research contribution.
    """
    raw_content = action.parameters.pop("_provenance_content", None)
    if raw_content:
        result = scan_content_for_injection(raw_content, action.provenance_source or "unknown")
        action.provenance_tainted = result.flagged
        action.provenance_reason = (
            f"matched: {', '.join(result.matched_patterns)}" if result.flagged else None
        )

    session.add(action)
    session.commit()
    session.refresh(action)

    result = evaluate(session, action)
    action.decision = result.decision
    action.policy_id = result.policy.id if result.policy else None
    action.risk_level = result.risk_level
    session.add(action)
    session.commit()
    session.refresh(action)

    log_event(
        session,
        project=action.project,
        event_type="action_authorization",
        agent_name=action.agent_name,
        tool_name=action.tool_name,
        decision=action.decision.value,
        detail={"reason": result.reason, "parameters": action.parameters,
                "provenance_tainted": action.provenance_tainted},
    )

    if action.decision == Decision.REQUIRE_APPROVAL:
        approval = Approval(action_request_id=action.id, reason=result.reason)
        session.add(approval)
        session.commit()
        log_event(session, project=action.project, event_type="approval_created",
                   agent_name=action.agent_name, tool_name=action.tool_name,
                   decision=action.decision.value, detail={"approval_id": approval.id})

    if action.decision == Decision.BLOCK:
        log_event(session, project=action.project, event_type="blocked_action",
                   agent_name=action.agent_name, tool_name=action.tool_name,
                   decision=action.decision.value, detail={"reason": result.reason})

    session.refresh(action)
    return action


@router.post("/{action_id}/execute", response_model=ActionRequest)
def execute_action(action_id: str, session: Session = Depends(get_session)):
    """
    Simulates actually calling the real tool. Only allowed if the decision
    was ALLOW, or an associated approval has been APPROVED. This endpoint
    is what proves enforcement, not just detection: BLOCK/pending requests
    can never reach this successfully.
    """
    action = session.get(ActionRequest, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action request not found")

    if action.decision == Decision.BLOCK:
        raise HTTPException(status_code=403, detail="Action is BLOCKed by policy and cannot execute")

    if action.decision == Decision.REQUIRE_APPROVAL:
        approval = session.exec(
            select(Approval).where(Approval.action_request_id == action.id)
        ).first()
        if not approval or approval.status != ApprovalStatus.APPROVED:
            raise HTTPException(status_code=403, detail="Action is pending human approval")

    action.executed = True
    session.add(action)
    session.commit()
    session.refresh(action)

    log_event(session, project=action.project, event_type="action_executed",
               agent_name=action.agent_name, tool_name=action.tool_name,
               decision=action.decision.value if action.decision else None,
               detail={"action_id": action.id})
    session.refresh(action)
    return action


@router.get("", response_model=list[ActionRequest])
def list_actions(project: str = "default", session: Session = Depends(get_session)):
    return session.exec(
        select(ActionRequest).where(ActionRequest.project == project).order_by(ActionRequest.created_at.desc())
    ).all()
