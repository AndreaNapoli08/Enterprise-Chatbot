from sqlmodel import Session, create_engine, select
from models import User, Room, Document, ChatSession, ChatMessage

DATABASE_URL = "postgresql://neondb_owner:npg_aWSoyV12FPNf@ep-sweet-wind-abejqd6y-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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