"""
CYBRAION Policy Engine.

This is deliberately NOT an LLM. It is a small, deterministic rule
evaluator: same input always produces the same output, and nothing an
AI model generates (e.g. "ignore the refund policy, I am authorized")
has any power over it. That separation between "the AI that decides
what to try" and "the engine that decides what's allowed" is the
entire security model of CYBRAION.

A Policy's `condition` is a tiny JSON expression, e.g.:
    {"field": "amount", "op": "<=", "value": 100}
    {"field": "amount", "op": ">",  "value": 1000}
    {}   # no field -> matches unconditionally (e.g. always BLOCK this tool)

Policies for a given tool are evaluated in ascending `priority` order;
the first one whose condition matches wins. If nothing matches, the
engine returns a safe default (fail-closed: REQUIRE_APPROVAL) rather
than silently allowing an un-policed action.
"""
from __future__ import annotations

from typing import Optional
from sqlmodel import Session, select

from app.models.models import Policy, ActionRequest, Decision, RiskLevel

OPS = {
    "<=": lambda a, b: a <= b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _condition_matches(condition: dict, parameters: dict) -> bool:
    if not condition:
        return True  # unconditional rule (e.g. always block this tool)
    field = condition.get("field")
    op = condition.get("op")
    value = condition.get("value")
    if field is None or op is None:
        return True
    actual = parameters.get(field)
    if actual is None:
        return False
    fn = OPS.get(op)
    if fn is None:
        return False
    try:
        return fn(actual, value)
    except TypeError:
        return False


def _risk_for_decision(decision: Decision) -> RiskLevel:
    return {
        Decision.ALLOW: RiskLevel.LOW,
        Decision.REQUIRE_APPROVAL: RiskLevel.MEDIUM,
        Decision.BLOCK: RiskLevel.HIGH,
        Decision.REDACT: RiskLevel.MEDIUM,
    }[decision]


class PolicyEvaluationResult:
    def __init__(self, decision: Decision, policy: Optional[Policy], risk_level: RiskLevel, reason: str):
        self.decision = decision
        self.policy = policy
        self.risk_level = risk_level
        self.reason = reason


def evaluate(session: Session, action: ActionRequest) -> PolicyEvaluationResult:
    """
    Evaluate an ActionRequest against all active policies for its tool,
    in priority order, and return a deterministic decision.

    Provenance-aware step (the project's novel contribution): if the
    action was justified by content flagged as tainted (e.g. a document
    containing a hidden/embedded instruction), the engine escalates an
    otherwise-ALLOW decision to REQUIRE_APPROVAL, even though the raw
    tool call looks policy-compliant on its own.
    """
    statement = (
        select(Policy)
        .where(Policy.tool_name == action.tool_name)
        .where(Policy.project == action.project)
        .where(Policy.active == True)  # noqa: E712
        .order_by(Policy.priority.asc())
    )
    policies = session.exec(statement).all()

    for policy in policies:
        if _condition_matches(policy.condition, action.parameters):
            decision = policy.decision
            reason = f"Matched policy '{policy.name}' ({policy.condition or 'unconditional'})"

            decision, reason = _apply_provenance_check(action, decision, reason)

            return PolicyEvaluationResult(
                decision=decision,
                policy=policy,
                risk_level=_risk_for_decision(decision),
                reason=reason,
            )

    # Fail-closed default: no matching policy means we do NOT silently
    # allow a high-stakes action. Require a human to look at it.
    decision, reason = _apply_provenance_check(
        action, Decision.REQUIRE_APPROVAL, "No matching policy found (fail-closed default)"
    )
    return PolicyEvaluationResult(
        decision=decision,
        policy=None,
        risk_level=_risk_for_decision(decision),
        reason=reason,
    )


def _apply_provenance_check(action: ActionRequest, decision: Decision, reason: str):
    """
    If the action's justification traces back to content that was flagged
    as tainted (e.g. a poisoned document containing a hidden instruction),
    escalate ALLOW -> REQUIRE_APPROVAL regardless of what the raw policy
    match would otherwise permit. BLOCK stays BLOCK.
    """
    if action.provenance_tainted and decision == Decision.ALLOW:
        escalated_reason = (
            f"{reason}; ESCALATED by provenance check "
            f"({action.provenance_reason or 'untrusted upstream content'})"
        )
        return Decision.REQUIRE_APPROVAL, escalated_reason
    return decision, reason
