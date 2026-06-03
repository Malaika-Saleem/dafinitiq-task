from sqlmodel import SQLModel, create_engine, Session
from typing import Optional
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./voice_agent.db")
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
