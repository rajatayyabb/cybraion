from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.models import Tool

router = APIRouter(prefix="/tools", tags=["Tool Registry"])


@router.post("", response_model=Tool)
def register_tool(tool: Tool, session: Session = Depends(get_session)):
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool


@router.get("", response_model=list[Tool])
def list_tools(project: str = "default", session: Session = Depends(get_session)):
    return session.exec(select(Tool).where(Tool.project == project)).all()


@router.get("/{tool_id}", response_model=Tool)
def get_tool(tool_id: str, session: Session = Depends(get_session)):
    tool = session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool
