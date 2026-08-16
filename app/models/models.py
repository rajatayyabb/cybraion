"""
CYBRAION core data models.

These map directly onto the entities described in the CYBRAION PRD:
Agent, Tool, Policy, ActionRequest, Decision, Approval, AuditEvent.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, JSON, Column


def new_id() -> str:
    return str(uuid.uuid4())


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REDACT = "REDACT"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Agent(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str = Field(index=True)
    project: str = Field(default="default", index=True)
    description: Optional[str] = None
    environment: str = Field(default="development")
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tool(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str = Field(index=True)
    project: str = Field(default="default", index=True)
    description: Optional[str] = None
    risk_classification: RiskLevel = Field(default=RiskLevel.MEDIUM)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Policy(SQLModel, table=True):
    """
    A deterministic rule evaluated against an ActionRequest.

    condition is a small JSON-based expression, e.g.:
      {"tool": "RefundPayment", "field": "amount", "op": "<=", "value": 100, "decision": "ALLOW"}
      {"tool": "RefundPayment", "field": "amount", "op": ">", "value": 1000, "decision": "BLOCK"}
      {"tool": "ExportDatabase", "decision": "BLOCK"}

    Policies are evaluated in ascending `priority` order; the first matching
    rule wins. If nothing matches, the engine falls back to `default_decision`.
    """
    id: str = Field(default_factory=new_id, primary_key=True)
    project: str = Field(default="default", index=True)
    name: str
    tool_name: str = Field(index=True)
    condition: dict = Field(sa_column=Column(JSON))
    decision: Decision
    priority: int = Field(default=100)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActionRequest(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project: str = Field(default="default", index=True)
    agent_id: str = Field(index=True)
    agent_name: str
    tool_name: str = Field(index=True)
    operation: Optional[str] = None
    target_resource: Optional[str] = None
    parameters: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Provenance-aware fields (the project's novel research angle):
    # which upstream content this action was justified by, and whether
    # that content was flagged as containing an embedded/hidden instruction.
    provenance_source: Optional[str] = None
    provenance_tainted: bool = Field(default=False)
    provenance_reason: Optional[str] = None

    decision: Optional[Decision] = None
    policy_id: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    executed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Approval(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    action_request_id: str = Field(index=True)
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    reviewer: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class AuditEvent(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    project: str = Field(default="default", index=True)
    event_type: str = Field(index=True)
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    decision: Optional[str] = None
    detail: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
