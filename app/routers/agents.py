from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.models import Agent

router = APIRouter(prefix="/agents", tags=["Agent Registry"])


@router.post("", response_model=Agent)
def register_agent(agent: Agent, session: Session = Depends(get_session)):
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


@router.get("", response_model=list[Agent])
def list_agents(project: str = "default", session: Session = Depends(get_session)):
    return session.exec(select(Agent).where(Agent.project == project)).all()


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str, session: Session = Depends(get_session)):
    agent = session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
