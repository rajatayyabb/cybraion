# CYBRAION

**Runtime security and action authorization gateway for autonomous AI agents.**

> An AI model should never be responsible for authorizing its own actions.

CYBRAION sits between an AI agent and the real tools it tries to use (payment APIs, databases,
email services, etc.). Every sensitive action is evaluated by a **deterministic policy engine**
— not an LLM — before it's allowed to execute. Decisions are `ALLOW`, `BLOCK`, or
`REQUIRE_APPROVAL`, and everything is recorded to an audit log.

This repo is the Semester 7 core: Agent/Tool Registry, Action Gateway, Policy Engine, Human
Approval workflow, Audit Logging, and a **provenance-aware detection layer** that escalates
decisions when an action was justified by upstream content (a document, a retrieved chunk)
containing a hidden/embedded instruction — i.e. detecting when the *reasoning* behind an action
was poisoned, not just checking whether the final tool call looks policy-compliant.

---

## Running on Kali Linux

Kali ships with Python 3.11+ already installed. Everything below is free and runs fully offline
except the initial `pip install`.

```bash
# 1. Clone your repo
git clone https://github.com/<your-username>/cybraion.git
cd cybraion

# 2. Create a virtual environment (recommended on Kali, which blocks system-wide pip installs)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the API server
uvicorn app.main:app --reload
```

The API is now live at **http://127.0.0.1:8000**, with interactive docs at
**http://127.0.0.1:8000/docs**.

### Run the end-to-end demo

In a second terminal (with the venv activated):

```bash
python scripts/demo_scenario.py
```

This reproduces the full walkthrough: registering an agent and a `RefundPayment` tool, creating
tiered policies, then running four scenarios —

| Scenario | Request | Expected decision |
|---|---|---|
| A | Refund $75 | `ALLOW` — executes immediately |
| B | Refund $600 | `REQUIRE_APPROVAL` — paused, then approved by a simulated human, then executes |
| C | Export customer database | `BLOCK` — execution attempt is rejected |
| D | Refund $50, justified by a poisoned document | Escalated to `REQUIRE_APPROVAL` even though a plain amount-based check would `ALLOW` it |

### Run the test suite

```bash
pytest -v
```

Tests cover: threshold-based ALLOW/BLOCK, the fail-closed default when no policy matches, proof
that AI-generated override text embedded in parameters has zero effect on the decision, and the
provenance-taint escalation behavior.

---

## Project layout

```
cybraion/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models/models.py     # Agent, Tool, Policy, ActionRequest, Approval, AuditEvent
│   ├── core/
│   │   ├── database.py      # SQLModel engine/session (SQLite by default)
│   │   └── policy_engine.py # The deterministic decision engine
│   ├── services/
│   │   ├── detection.py     # Prompt-injection / provenance content scanning (baseline heuristic)
│   │   └── audit.py         # Audit log writer
│   └── routers/
│       ├── agents.py        # Agent Registry endpoints
│       ├── tools.py         # Tool Registry endpoints
│       ├── policies.py      # Policy management endpoints
│       ├── actions.py       # THE ACTION GATEWAY — core enforcement endpoint
│       ├── approvals.py     # Human approval workflow
│       └── audit.py         # Audit log + dashboard metrics
├── scripts/demo_scenario.py # End-to-end walkthrough script
├── tests/test_policy_engine.py
├── requirements.txt
└── README.md
```

## Database

Defaults to a local SQLite file (`cybraion.db`), created automatically on first run — zero setup
required. To point at PostgreSQL instead (recommended once you deploy in Semester 8):

```bash
export CYBRAION_DB_URL="postgresql://user:password@localhost:5432/cybraion"
```

## Swapping in a real prompt-injection detector

`app/services/detection.py` currently uses a small regex-based heuristic so the project runs
fully offline with zero dependencies beyond `requirements.txt`. For Semester 7, Week 11, replace
or augment `classify_prompt()` / `scan_content_for_injection()` with an open-source detector such
as [Rebuff](https://github.com/protectai/rebuff), [LLM Guard](https://github.com/protectai/llm-guard),
or [Vigil-LLM](https://github.com/deadbits/vigil-llm), and compare detection rates against this
baseline in your evaluation chapter.

## Status

This is the **Semester 7 core engine** scope: Action Gateway, Policy Engine, Agent/Tool Registry,
Approval workflow, Audit Logging, and provenance-aware detection. Auth, multi-tenant org/project
management, and the full dashboard UI are Semester 8 scope — see the accompanying
`CYBRAION_FYP_Execution_Guide.pdf` for the full two-semester plan.

## License

MIT — see `LICENSE`.
