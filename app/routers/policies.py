from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.models import Policy

router = APIRouter(prefix="/policies", tags=["Policy Management"])


@router.post("", response_model=Policy)
def create_policy(policy: Policy, session: Session = Depends(get_session)):
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.get("", response_model=list[Policy])
def list_policies(project: str = "default", session: Session = Depends(get_session)):
    return session.exec(select(Policy).where(Policy.project == project)).all()


@router.patch("/{policy_id}/deactivate", response_model=Policy)
def deactivate_policy(policy_id: str, session: Session = Depends(get_session)):
    policy = session.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.active = False
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy
