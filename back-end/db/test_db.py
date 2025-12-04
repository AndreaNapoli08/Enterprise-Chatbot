from sqlmodel import Session, create_engine, select
from models import User, Room, Document, ChatSession, ChatMessage
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    # Controlla utenti
    users = session.exec(select(User)).all()
    print("UTENTI:", users)

    # Controlla stanze
    rooms = session.exec(select(Room)).all()
    print("STANZE:", rooms)

    # Controlla documenti
    documents = session.exec(select(Document)).all()
    print("DOCUMENTI:", documents)

    # ChatSession vuote
    chats = session.exec(select(ChatSession)).all()
    print("CHAT SESSIONS:", chats)

    # ChatMessage vuote
    messages = session.exec(select(ChatMessage)).all()
    print("CHAT MESSAGES:", messages)