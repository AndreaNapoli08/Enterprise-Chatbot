# back-end/db/models.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    password: str
    role: str


class Room(SQLModel, table=True):
    __tablename__ = "rooms"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    numero: int
    capienza: int
    caratteristiche: list[str] = Field(sa_column=Column(JSONB))
    prenotazioni: list[dict] = Field(default_factory=list, sa_column=Column(JSONB))

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    filename: str  # nome file salvato sul server
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)