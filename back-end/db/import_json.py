import json
from sqlmodel import Session
from db.db import engine
from db.models import User, Room, Document
import os

def import_users():
    USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
    with open(USERS_FILE, encoding="utf-8") as f:
        users = json.load(f)

    with Session(engine) as session:
        for u in users:
            user = User(
                id=u["id"],
                first_name=u["firstName"],
                last_name=u["lastName"],
                email=u["email"],
                password=u["password"],  # già bcrypt
                role=u["role"]
            )
            session.add(user)
        session.commit()
    print("✅ Utenti importati con successo!")

def import_rooms():
    ROOMS_FILE = os.path.join(os.path.dirname(__file__), "rooms.json")
    with open(ROOMS_FILE, encoding="utf-8") as f:
        rooms = json.load(f)

    with Session(engine) as session:
        for name, r in rooms.items():
            room = Room(
                name=name,
                numero=r["numero"],
                capienza=r["capienza"],
                caratteristiche=r["caratteristiche"],
                prenotazioni=r.get("prenotazioni", [])
            )
            session.add(room)
        session.commit()
    print("✅ Stanze importate con successo!")

def import_documents():
    DOCUMENTS_FILE = os.path.join(os.path.dirname(__file__), "documents.json")
    with open(DOCUMENTS_FILE, encoding="utf-8") as f:
        documents = json.load(f)

    with Session(engine) as session:
        for document_data in documents:
            document = Document(
                title=document_data["title"],
                description=document_data.get("description"),
                filename=document_data["filename"],
                uploaded_at=document_data["uploaded_at"]
            )
            session.add(document)
        session.commit()
    print("✅ Documenti importati con successo!")

if __name__ == "__main__":
    # import_users()
    # import_rooms()
    import_documents()