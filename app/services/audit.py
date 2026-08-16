from sqlmodel import Session

from app.models.models import AuditEvent


def log_event(
    session: Session,
    project: str,
    event_type: str,
    agent_name: str | None = None,
    tool_name: str | None = None,
    decision: str | None = None,
    detail: dict | None = None,
) -> AuditEvent:
    event = AuditEvent(
        project=project,
        event_type=event_type,
        agent_name=agent_name,
        tool_name=tool_name,
        decision=decision,
        detail=detail or {},
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
