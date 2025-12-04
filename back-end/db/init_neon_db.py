# back-end/db/init_db.py
from sqlmodel import SQLModel, create_engine, Session
from models import User, Room, Document, ChatSession, ChatMessage
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()
# Connection string Neon
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

# Crea tutte le tabelle
SQLModel.metadata.create_all(engine)

# Inserisci dati iniziali
with Session(engine) as session:
    # 1️⃣ utenti
    users = [
        User(
            id=1,
            first_name="Andrea",
            last_name="Napoli",
            email="spospociao08@gmail.com",
            password="$2b$12$UAJxjZUPC4jErwK0bhxXDueavtLvaLf38HkjgJS33KVBlNCaF.U8u",
            role="Manager"
        ),
        User(
            id=2,
            first_name="Luca",
            last_name="Rossi",
            email="l.rossi@reply.it",
            password="$2b$12$1d/CX2Z8fEpquVxwDLd98umzkqXu5vsN5aaBYa2UpnbTRRCW7uOxG",
            role="Dipendente"
        )
    ]
    session.add_all(users)

    # 2️⃣ stanze
    rooms_data = {
        "Sala Rossa": {
            "numero": 101,
            "capienza": 6,
            "caratteristiche": [
            "Monitor",
            "Prese di corrente multiple",
            "Accesso disabili"
            ],
            "prenotazioni": []
        },
        "Sala Blu": {
            "numero": 102,
            "capienza": 10,
            "caratteristiche": [
            "Videoproiettore",
            "Microfono",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Verde": {
            "numero": 103,
            "capienza": 8,
            "caratteristiche": [
            "Monitor",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Gialla": {
            "numero": 104,
            "capienza": 20,
            "caratteristiche": [
            "Videoproiettore",
            "Microfono",
            "Prese di corrente multiple",
            "Aria condizionata",
            "Accesso disabili"
            ],
            "prenotazioni": []
        },
        "Sala Viola": {
            "numero": 105,
            "capienza": 12,
            "caratteristiche": [
            "Monitor",
            "Microfono",
            "Accesso disabili"
            ],
            "prenotazioni": []
        },
        "Sala Arancione": {
            "numero": 106,
            "capienza": 16,
            "caratteristiche": [
            "Videoproiettore",
            "Lavagna digitale",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Bianca": {
            "numero": 107,
            "capienza": 5,
            "caratteristiche": [
            "Monitor",
            "Prese di corrente multiple"
            ],
            "prenotazioni": []
        },
        "Sala Nera": {
            "numero": 108,
            "capienza": 25,
            "caratteristiche": [
            "Videoproiettore",
            "Microfono",
            "Lavagna digitale",
            "Aria condizionata",
            "Accesso disabili"
            ],
            "prenotazioni": [
            {
                "id": "06e7c7c9-58a1-4e20-be53-a56020d44697",
                "user": "spospociao08@gmail.com",
                "start": "2025-11-19 18:45",
                "end": "2025-11-19 20:15",
                "persons": "5"
            }
            ]
        },
        "Sala Grigia": {
            "numero": 109,
            "capienza": 14,
            "caratteristiche": [
            "Monitor",
            "Prese di corrente multiple",
            "Lavagna digitale"
            ],
            "prenotazioni": []
        },
        "Sala Azzurra": {
            "numero": 110,
            "capienza": 18,
            "caratteristiche": [
            "Videoproiettore",
            "Microfono",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Oro": {
            "numero": 111,
            "capienza": 9,
            "caratteristiche": [
            "Monitor",
            "Aria condizionata",
            "Prese di corrente multiple"
            ],
            "prenotazioni": []
        },
        "Sala Argento": {
            "numero": 112,
            "capienza": 7,
            "caratteristiche": [
            "Lavagna digitale",
            "Accesso disabili"
            ],
            "prenotazioni": []
        },
        "Sala Bronzo": {
            "numero": 113,
            "capienza": 15,
            "caratteristiche": [
            "Videoproiettore",
            "Prese di corrente multiple",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Turchese": {
            "numero": 114,
            "capienza": 11,
            "caratteristiche": [
            "Monitor",
            "Microfono",
            "Accesso disabili",
            "Aria condizionata"
            ],
            "prenotazioni": []
        },
        "Sala Smeraldo": {
            "numero": 115,
            "capienza": 22,
            "caratteristiche": [
            "Videoproiettore",
            "Lavagna digitale",
            "Microfono",
            "Accesso disabili",
            "Aria condizionata",
            "Prese di corrente multiple"
            ],
            "prenotazioni": []
        }
    }
    rooms = []
    for name, info in rooms_data.items():
        room = Room(
            id=uuid.uuid4(),
            name=name,
            numero=info["numero"],
            capienza=info["capienza"],
            caratteristiche=info["caratteristiche"],
            prenotazioni=info["prenotazioni"]
        )
        rooms.append(room)
    session.add_all(rooms)

    # 3️⃣ documenti
    documents = [
        Document(
            id=1, 
            title="Informazioni Aziendali", 
            filename="informazioni_aziendali.pdf", 
            description="Documento contenente tutte le informazioni aziendali", 
            uploaded_at=datetime.fromisoformat("2025-09-01")
        ),
        Document(
            id=2, 
            title="Linee Guida", 
            filename="linee_guida.pdf",
            description="Consigli su come scrivere una buona relazione di tirocinio", 
            uploaded_at=datetime.fromisoformat("2025-10-15")
        )
    ]
    session.add_all(documents)

    # ChatSession e ChatMessage rimangono vuote, le tabelle sono già create

    session.commit()

print("Database popolato correttamente!")
