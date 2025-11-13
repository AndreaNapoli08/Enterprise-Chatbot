from flask import Flask, jsonify, request, send_from_directory # type: ignore
from flasgger import Swagger # type: ignore
from flask_cors import CORS # type: ignore
import os, json, uuid
from actions.utils import hash_password, check_password, load_rooms, save_rooms, parse_datetime, send_gmail_email, get_user_by_email
from datetime import datetime, timedelta

# import per il database
from sqlmodel import Session, select
from db.db import engine
from db.models import User
from db.models import Room

app = Flask(__name__)
swagger = Swagger(app)
CORS(app)  # abilita CORS per tutte le rotte

# cartella dove tieni i PDF
PDF_DIR = os.path.join(os.path.dirname(__file__), "data/docs")

# ============================================================
#                     ENDPOINT DOCUMENTI
# ============================================================

@app.route("/documents/<filename>")
def serve_pdf(filename):
    """Serve un documento PDF dalla cartella data/docs"""
    return send_from_directory(
        directory=PDF_DIR,
        path=filename,
        as_attachment=True
    )

# ============================================================
#                     ENDPOINT UTENTI
# ============================================================

@app.route("/users", methods=["GET"])
def get_users():
    """
    Restituisce la lista di tutti gli utenti dal database
    ---
    tags:
      - Utenti
    responses:
      200:
        description: Lista completa degli utenti
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              firstName:
                type: string
                example: "Mario"
              lastName:
                type: string
                example: "Rossi"
              email:
                type: string
                example: "mario.rossi@example.com"
              role:
                type: string
                example: "dipendente"
    """
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        users_list = [
            {
                "id": u.id,
                "firstName": u.first_name,
                "lastName": u.last_name,
                "email": u.email,
                "role": u.role
            } for u in users
        ]
        return jsonify(users_list)


@app.route("/users/login", methods=["POST"])
def login_user():
    """
    Effettua il login di un utente
    ---
    tags:
      - Utenti
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: mario.rossi@example.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Login riuscito
      401:
        description: Password errata
      404:
        description: Utente non trovato
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email o password mancante"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    # verifica la password con la funzione importata da utils
    if not check_password(password, user.password):
        return jsonify({"error": "Password errata"}), 401

    # accesso riuscito: restituisci le info (senza password)
    user_copy = {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "role": user.role
    }
    return jsonify(user_copy), 200


@app.route("/users/<email>", methods=["GET"])
def get_user(email):
    """
    Restituisce un singolo utente in base all'email
    ---
    tags:
      - Utenti
    parameters:
      - name: email
        in: path
        required: true
        type: string
        description: Email dell'utente da cercare
        example: mario.rossi@example.com
    responses:
      200:
        description: Dati dell'utente trovato
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            firstName:
              type: string
              example: "Mario"
            lastName:
              type: string
              example: "Rossi"
            email:
              type: string
              example: "mario.rossi@example.com"
            role:
              type: string
              example: "dipendente"
      404:
        description: Utente non trovato
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Utente non trovato"
    """
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    user_copy = {
        "id": user.id,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "role": user.role
    }
    return jsonify(user_copy), 200

@app.route("/users/verify_password", methods=["POST"])
def verify_password():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if not user:
            return jsonify({"success": False, "error": "Utente non trovato"}), 404

        is_correct = check_password(password, user.password)
        return jsonify({"success": is_correct}), 200
    
@app.route("/users/update_password", methods=["PATCH"])
def update_password():
    """Aggiorna la password di un utente"""
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("password")

    if not email or not new_password:
        return jsonify({"error": "email o password mancante"}), 400

    with Session(engine) as session:
        # Recupera l'utente dal DB
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if not user:
            return jsonify({"error": "Utente non trovato"}), 404

        # Cifra la nuova password
        user.password = hash_password(new_password)

        # Salva il cambiamento nel DB
        session.add(user)
        session.commit()

    return jsonify({"message": "Password aggiornata correttamente!"}), 200


# ============================================================
#                     ENDPOINT STANZE
# ============================================================

@app.route("/rooms", methods=["GET"])
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
    return jsonify(rooms_list), 200
        

@app.route("/rooms/book", methods=["POST"])
def book_room():
    """
    Effettua una prenotazione di una sala
    ---
    tags:
      - Stanze
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            appointment_date:
              type: string
              example: "2025-11-15"
            appointment_hour:
              type: string
              example: "10:00"
            appointment_duration:
              type: number
              example: 2
            person_picker:
              type: integer
              example: 4
            room_features:
              type: array
              items:
                type: string
              example: ["proiettore", "lavagna"]
            email:
              type: string
              example: mario.rossi@example.com
    responses:
      200:
        description: Prenotazione effettuata
      404:
        description: Nessuna sala disponibile
    """
    data = request.get_json()

    appointment_date = data.get("appointment_date")
    appointment_hour = data.get("appointment_hour")
    appointment_duration = data.get("appointment_duration")
    person_picker = data.get("person_picker")
    room_features = data.get("room_features")
    email = data.get("email")

    if not all([appointment_date, appointment_hour, appointment_duration, room_features]):
        return jsonify({"error": "Dati insufficienti per la prenotazione"}), 400

    # Parsing data e ora
    try:
        requested_start = parse_datetime(appointment_date, appointment_hour)
    except Exception as e:
        return jsonify({"error": f"Data/ora non valida: {e}"}), 400

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
                    return jsonify({"error": "Numero partecipanti non valido"}), 400
                
                if persone <= room.capienza:
                    available_room = room
                    break

    if not available_room:
        return jsonify({"message": "Nessuna sala disponibile con le caratteristiche richieste"}), 404

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
    try:
        send_gmail_email(email, email_subject, email_body)
    except Exception as e:
        response["email_error"] = str(e)

    return jsonify(response), 200

@app.route("/rooms/reservations/<email>", methods=["GET"])
def get_user_reservations(email):
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
        return jsonify({
            "message": f"Nessuna prenotazione trovata per l'utente {email}"
        }), 404

    return jsonify({
        "email": email,
        "prenotazioni": prenotazioni_utente
    }), 200

@app.route("/rooms/reservations/<reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
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
                return jsonify({
                    "message": f"La prenotazione per {room.name} (n.{room.numero}) è stata cancellata con successo."
                }), 200

    if not found:
        return jsonify({"error": "Nessuna prenotazione trovata con l'ID fornito."}), 404
    
# ============================================================
#                     AVVIO SERVER
# ============================================================

def run_flask_server():
    """Avvia il server Flask"""
    app.run(host="0.0.0.0", port=5050)


if __name__ == "__main__":
    # Esegui questo file direttamente per avviare il server
    run_flask_server()
