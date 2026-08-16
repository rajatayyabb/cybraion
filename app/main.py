from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.routers import agents, tools, policies, actions, approvals, audit

app = FastAPI(
    title="CYBRAION",
    description="Runtime security and action authorization gateway for autonomous AI agents. "
                 "An AI model should never be responsible for authorizing its own actions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "product": "CYBRAION",
        "status": "online",
        "principle": "An AI model should never be responsible for authorizing its own actions.",
        "docs": "/docs",
    }


app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(policies.router)
app.include_router(actions.router)
app.include_router(approvals.router)
app.include_router(audit.router)
