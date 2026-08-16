import os
from sqlmodel import SQLModel, Session, create_engine

DB_URL = os.getenv("CYBRAION_DB_URL", "sqlite:///./cybraion.db")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    # Import models so SQLModel metadata is registered before create_all
    from app.models import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
