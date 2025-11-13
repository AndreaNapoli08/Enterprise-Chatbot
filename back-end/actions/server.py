from fastapi import FastAPI, HTTPException, Depends, Query # type: ignore
from fastapi.responses import FileResponse # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel, EmailStr
from typing import List

import os, json, uuid
from actions.utils import load_users, hash_password, check_password, load_rooms, save_rooms, parse_datetime, send_gmail_email, get_user_by_email
from datetime import datetime, timedelta

# import per il database
from sqlmodel import Session, select # type: ignore
from db.db import engine, get_session
from db.models import User, Room, Document, ChatSession, ChatMessage

# toglie i warning 
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = FastAPI(title="Enterprise Chatbot API", version="1.0.0")
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# cartella dove tieni i PDF
PDF_DIR = os.path.join(os.path.dirname(__file__), "data/docs")

# ============================================================
#                     ENDPOINT DOCUMENTI
# ============================================================

@app.get("/documents")
def list_documents():
    with Session(engine) as session:
        docs = session.exec(select(Document)).all()
        return [
            {
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "filename": d.filename
            } for d in docs
        ]
    
@app.get("/documents/{filename}")
def serve_pdf(filename: str):
    """Serve un documento PDF usando l'ID del documento dal database"""
    with Session(engine) as session:
        statement = select(Document).where(Document.filename == filename)
        document = session.exec(statement).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento non trovato")

        # Percorso del file fisico
        file_path = os.path.join(PDF_DIR, document.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File fisico non trovato")

        return FileResponse(file_path, filename=document.filename)

# ============================================================
#                     ENDPOINT UTENTI
# ============================================================

@app.get("/users")
def get_users():
    users = load_users()
    users_list = [
        {
            "id": u.id,
            "firstName": u.first_name,
            "lastName": u.last_name,
            "email": u.email,
            "role": u.role
        } for u in users
    ]
    return users_list

class CredentialRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/users/login")
def login_user(data: CredentialRequest):
    user = get_user_by_email(data.email)

    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # verifica la password con la funzione importata da utils
    if not check_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Password errata")

    # accesso riuscito: restituisci le info (senza password)
    user_copy = {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "role": user.role
    }
    return user_copy


@app.get("/users/{email}")
def get_user(email: str):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    user_copy = {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "role": user.role
    }
    return user_copy

@app.post("/users/verify_password")
def verify_password(data: CredentialRequest):
    with Session(engine) as session:
        statement = select(User).where(User.email == data.email)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")

        is_correct = check_password(data.password, user.password)
        return {"success": is_correct}
    
@app.patch("/users/update_password")
def update_password(data: CredentialRequest):
    """Aggiorna la password di un utente"""
    with Session(engine) as session:
        statement = select(User).where(User.email == data.email)
        user = session.exec(statement).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        
        # Cifra la nuova password
        user.password = hash_password(data.password)

        # Salva il cambiamento nel DB
        session.add(user)
        session.commit()

    return {"message": "Password aggiornata con successo"}

# ============================================================
#                     ENDPOINT STANZE
# ============================================================

@app.get("/rooms")
def get_rooms():
    """Restituisce la lista di tutte le sale con le rispettive caratteristiche"""
    rooms = load_rooms()
    rooms_list = [
        {
            "id": u.id,
            "name": u.name,
            "numero": u.numero,
            "capienza": u.capienza,
            "caratteristiche": u.caratteristiche,
            "prenotazioni": u.prenotazioni
        } for u in rooms
    ]
    return rooms_list
        
class BookRoomRequest(BaseModel):
    appointment_date: str
    appointment_hour: str
    appointment_duration: float
    person_picker: int
    room_features: List[str]
    email: EmailStr

@app.post("/rooms/book")
def book_room(data: BookRoomRequest):
    appointment_date = data.appointment_date
    appointment_hour = data.appointment_hour
    appointment_duration = data.appointment_duration
    person_picker = data.person_picker
    room_features = data.room_features
    email = data.email

    if not all([appointment_date, appointment_hour, appointment_duration, room_features]):
        raise HTTPException(status_code=400, detail="Dati insufficienti per la prenotazione")

    # Parsing data e ora
    try:
        requested_start = parse_datetime(appointment_date, appointment_hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Data/ora non valida: {e}")

    requested_end = requested_start + timedelta(hours=float(appointment_duration))

    # Carica sale
    rooms = load_rooms()
    room_features = [f.lower() for f in room_features]
    available_room = None

    def is_available(room, start, end):
        for booking in room.prenotazioni:
            booking_start = datetime.strptime(booking["start"], "%Y-%m-%d %H:%M")
            booking_end = datetime.strptime(booking["end"], "%Y-%m-%d %H:%M")
            if not (end <= booking_start or start >= booking_end):
                return False
        return True

    for room in rooms:
        features = [f.lower() for f in room.caratteristiche]
        if all(feature in features for feature in room_features):
            # Controlla disponibilità oraria
            if is_available(room, requested_start, requested_end):
                # Controlla capienza
                try:
                    persone = int(person_picker)
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail="Numero partecipanti non valido")
                
                if persone <= room.capienza:
                    available_room = room
                    break

    if not available_room:
        raise HTTPException(status_code=404, detail="Nessuna sala disponibile con le caratteristiche richieste in questo orario.")

    prenotazioni = available_room.prenotazioni or []
    booking_id = str(uuid.uuid4())
    prenotazioni.append({
        "id": booking_id,    
        "user": email,
        "start": requested_start.strftime("%Y-%m-%d %H:%M"),
        "end": requested_end.strftime("%Y-%m-%d %H:%M"),
        "persons": person_picker
    })
    available_room.prenotazioni = prenotazioni
    save_rooms(available_room)

    response = {
        "message": "Prenotazione effettuata con successo",
        "room_name": available_room.name,
        "numero": available_room.numero,
        "caratteristiche": available_room.caratteristiche,
        "capienza": available_room.capienza,
        "start": requested_start.strftime("%Y-%m-%d %H:%M"),
        "end": requested_end.strftime("%Y-%m-%d %H:%M"),
        "booking_id": booking_id
    }

    features_str = ", ".join(available_room.caratteristiche)
    email_subject = f"Prenotazione confermata: {available_room.name}"
    email_body = (
        f"Buongiorno,\n"
        f"La sala {available_room.name} (n. {available_room.numero}) è stata prenotata con successo!\n\n"
        f"Data: {appointment_date}\n"
        f"Orario: {appointment_hour} - {requested_end.strftime('%H:%M')}\n"
        f"Partecipanti: {person_picker}\n"
        f"Caratteristiche: {features_str}\n"
        f"Capienza massima: {available_room.capienza} persone."
    )
    #(Opzionale) invia email
    # try:
    #     send_gmail_email(email, email_subject, email_body)
    # except Exception as e:
    #     response["email_error"] = str(e)

    return response

@app.get("/rooms/reservations/{email}")
def get_user_reservations(email: str):
    """Restituisce tutte le prenotazioni associate a un utente (tramite email)"""
    
    rooms = load_rooms()
    prenotazioni_utente = []

    # Cicla tra tutte le sale e le loro prenotazioni
    for room in rooms:
        for prenotazione in room.prenotazioni or []:
            if prenotazione["user"] == email:
                prenotazioni_utente.append({
                    "id": prenotazione["id"],
                    "sala": room.name,
                    "numero": room.numero,
                    "inizio": prenotazione["start"],
                    "fine": prenotazione["end"],
                    "persone": prenotazione["persons"]
                })

    if not prenotazioni_utente:
        raise HTTPException(status_code=404, detail="Nessuna prenotazione trovata per questo utente.")

    return prenotazioni_utente

@app.delete("/rooms/reservations/{reservation_id}")
def delete_reservation(reservation_id: str):
    """Elimina una prenotazione tramite il suo ID"""
    
    rooms = load_rooms()
    found = False

    for room in rooms:
        prenotazioni = room.prenotazioni or []
        for p in prenotazioni:
            if p["id"] == reservation_id:
                prenotazioni.remove(p)
                found = True
                save_rooms(room)
                return {"message": "Prenotazione eliminata con successo"}

    if not found:
        raise HTTPException(status_code=404, detail="Nessuna prenotazione trovata con l'ID fornito.")
    
# ============================================================
#                     ENDPOINT CHAT
# ============================================================

@app.post("/chat/save_message")
def save_message(payload: dict, session: Session = Depends(get_session)):
    """
    Salva un messaggio nella chat dell'utente.
    payload deve contenere: user_email, sender, type, content
    """
    user_email = payload.get("user_email")
    sender = payload.get("sender")
    type_ = payload.get("type", "text")
    content = payload.get("content")

    if not user_email or not sender or content is None:
        raise HTTPException(status_code=400, detail="Dati mancanti nel payload")

    # Recupera o crea una sessione attiva per l'utente
    chat_session = session.exec(
        select(ChatSession).where(
            ChatSession.user_email == user_email,
            ChatSession.active == True
        )
    ).first()

    if not chat_session:
        chat_session = ChatSession(user_email=user_email)
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)

    # Salva il messaggio
    chat_message = ChatMessage(
        session_id=chat_session.id,
        sender=sender,
        type=type_,
        content=content,
        timestamp=datetime.utcnow()
    )
    session.add(chat_message)

    # Aggiorna last_activity della sessione
    chat_session.last_activity = datetime.utcnow()
    session.commit()

    return {"message": "Messaggio salvato con successo"}

@app.get("/chat/get_messages")
def get_messages(user_email: str, session: Session = Depends(get_session)):
    # Recupera la sessione attiva dell'utente
    chat_session = session.exec(
        select(ChatSession).where(
            ChatSession.user_email == user_email
        )
    ).first()

    if not chat_session:
        return {"messages": []}  # nessuna chat attiva

    # Recupera tutti i messaggi della sessione
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == chat_session.id)
    ).all()

    # Trasforma in un formato JSON-friendly
    messages_list = [
        {
            "id": m.id,
            "sender": m.sender,
            "type": m.type,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ]

    return {"messages": messages_list, "active": chat_session.active}

@app.post("/chat/close_session")
def close_session(user_email: str = Query(...), session: Session = Depends(get_session)):
    """
    Chiude la sessione attiva dell'utente impostando active=False.
    """
    chat_session = session.exec(
        select(ChatSession).where(
            ChatSession.user_email == user_email,
            ChatSession.active == True
        )
    ).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Nessuna sessione attiva trovata")

    chat_session.active = False
    chat_session.last_activity = datetime.utcnow()
    session.add(chat_session)
    session.commit()

    return {"message": f"Sessione di {user_email} chiusa con successo"}