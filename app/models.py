from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy import Column, JSON as SA_JSON


class CallSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    caller_id: Optional[str] = None
    # Use SQLAlchemy JSON column for arbitrary transcript array
    transcript: Optional[list] = Field(default_factory=list, sa_column=Column(SA_JSON))
    # Order summary stored as JSON
    order_summary: Optional[dict] = Field(default=None, sa_column=Column(SA_JSON))
    drift_detected: bool = False
    drift_log: Optional[list] = Field(default_factory=list, sa_column=Column(SA_JSON))


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    display_name: str
    hashed_password: str
    is_active: bool = True
    otp: Optional[str] = None
    otp_expires: Optional[datetime] = None
