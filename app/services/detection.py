"""
Lightweight, dependency-free detection layer.

This is intentionally a heuristic baseline you can run out of the box on
Kali with zero API keys and zero internet access. In Semester 7 you are
expected to swap/extend this with a proper open-source detector
(e.g. Rebuff, LLM Guard, or Vigil-LLM) and compare results against this
baseline in your evaluation chapter -- that comparison is good material
for your report.

Two responsibilities:
  1. classify_prompt()   -> input security (Section 9.1 / 14 of the PRD)
  2. scan_content_for_injection() -> provenance tagging support (Part 4:
     detect whether upstream content the agent read contains a hidden/
     embedded instruction, so the Action Gateway can mark the resulting
     action request as "tainted").
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Patterns commonly seen in prompt-injection / jailbreak attempts.
# Not exhaustive -- this is a baseline, not a production detector.
INJECTION_PATTERNS = [
    r"ignore (all|the|any) (previous|prior|above) instructions",
    r"disregard (all|the|any) (previous|prior|above) (instructions|rules|policy)",
    r"system override",
    r"you are now (in )?(developer|admin|god) mode",
    r"do not require approval",
    r"act as if you (have|are) (no|unrestricted)",
    r"reveal (the|your) (system prompt|instructions)",
    r"this is (a|an) (authorized|legitimate) (override|exception)",
    r"i am (authorized|the admin|the developer)",
    r"bypass (the|all) (policy|security|approval)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


@dataclass
class DetectionResult:
    flagged: bool
    matched_patterns: list[str]
    risk: str  # "none" | "low" | "high"


def classify_prompt(text: str) -> DetectionResult:
    """Classify a single prompt/message as permitted / flagged / blocked-risk."""
    matches = [p.pattern for p in _COMPILED if p.search(text or "")]
    if not matches:
        return DetectionResult(flagged=False, matched_patterns=[], risk="none")
    risk = "high" if len(matches) > 1 else "low"
    return DetectionResult(flagged=True, matched_patterns=matches, risk=risk)


def scan_content_for_injection(content: str, source_id: str) -> DetectionResult:
    """
    Scan upstream content (a document, retrieved chunk, uploaded file, etc.)
    that an agent read BEFORE deciding to act. Used to populate the
    provenance_tainted / provenance_reason fields on an ActionRequest.
    """
    return classify_prompt(content)
