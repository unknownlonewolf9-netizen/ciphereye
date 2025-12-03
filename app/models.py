from typing import Optional, Dict
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import uuid
from sqlalchemy import Column, JSON

class Run(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    module: str
    target: str
    status: str = "queued"
    result: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = True
    is_admin: bool = Field(default=False)
    score: int = Field(default=0)  # NEW: Track Score
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Challenge(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    resources: str
    flag: str
    level: int
    points: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)

# NEW TABLE: Tracks who solved what
class Solve(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    challenge_id: uuid.UUID = Field(foreign_key="challenge.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
