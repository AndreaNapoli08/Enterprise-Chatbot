# back-end/db/models.py
from sqlmodel import SQLModel, Field, Column, JSON # type: ignore
from sqlalchemy.dialects.postgresql import JSONB # type: ignore
from typing import Optional, Dict, Any
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

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    user_email: str = Field(index=True)
    title: str = Field(default="Nuova chat")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[uuid.UUID] = Field(foreign_key="chat_sessions.id")
    sender: str
    type: str = Field(default="text")
    content: Dict[str, Any] = Field(sa_column=Column(JSONB))
    timestamp: datetime = Field(default_factory=datetime.utcnow)