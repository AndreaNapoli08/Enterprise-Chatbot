from flask import Flask, jsonify, request, send_from_directory # type: ignore
from flask_cors import CORS # type: ignore
import os, json, uuid
from actions.utils import load_users, save_users, hash_password, check_password, load_rooms, save_rooms, parse_datetime, send_gmail_email
from datetime import datetime, timedelta
app = Flask(__name__)
CORS(app)  # abilita CORS per tutte le rotte

# cartella dove tieni i PDF
PDF_DIR = os.path.join(os.path.dirname(__file__), "data/docs")

# ============================================================
#                     ROUTE DOCUMENTI
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
    """Restituisce la lista di tutti gli utenti"""
    users = load_users()
    return jsonify(users)


@app.route("/users/login", methods=["POST"])
def login_user():
    """Login utente: verifica email e password"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email o password mancante"}), 400

    users = load_users()
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    # 🔐 verifica la password con la funzione importata da utils
    if not check_password(password, user["password"]):
        return jsonify({"error": "Password errata"}), 401

    # ✅ accesso riuscito: restituisci le info (senza password)
    user_copy = {k: v for k, v in user.items() if k != "password"}
    return jsonify(user_copy), 200


@app.route("/users/<email>", methods=["GET"])
def get_user_by_email(email):
    """Restituisce un singolo utente per email"""
    users = load_users()
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404

    # non includere la password nella risposta
    user_copy = {k: v for k, v in user.items() if k != "password"}
    return jsonify(user_copy), 200


@app.route("/users/update_password", methods=["PATCH"])
def update_password():
    """Aggiorna la password di un utente"""
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("password")

    if not email or not new_password:
        return jsonify({"error": "email o password mancante"}), 400

    users = load_users()
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return jsonify({"error": "utente non trovato"}), 404

    # 🔒 Cifra la nuova password prima di salvarla
    user["password"] = hash_password(new_password)
    save_users(users)

    return jsonify({"message": "password aggiornata correttamente!"})


# ============================================================
#                     ENDPOINT STANZE
# ============================================================

@app.route("/rooms", methods=["GET"])
def get_rooms():
    """Restituisce la lista di tutte le sale con le rispettive caratteristiche"""
    try:
        rooms = load_rooms()
    except FileNotFoundError:
        return jsonify({"error": "File delle sale non trovato"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Errore nel formato del file delle sale"}), 500
    except Exception as e:
        return jsonify({"error": f"Errore imprevisto: {e}"}), 500

    # Trasformiamo il dizionario in una lista più leggibile
    formatted_rooms = []
    for name, info in rooms.items():
        formatted_rooms.append({
            "nome": name,
            "numero": info.get("numero"),
            "caratteristiche": info.get("caratteristiche", []),
            "capienza": info.get("capienza"),
            "prenotazioni": info.get("prenotazioni", [])
        })

    return jsonify(formatted_rooms), 200

@app.route("/rooms/book", methods=["POST"])
def book_room():
    """Effettua una prenotazione sala, se disponibile"""
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

    def is_available(room, start, end):
        for booking in room["prenotazioni"]:
            booking_start = datetime.strptime(booking["start"], "%Y-%m-%d %H:%M")
            booking_end = datetime.strptime(booking["end"], "%Y-%m-%d %H:%M")
            if not (end <= booking_start or start >= booking_end):
                return False
        return True

    room_features = [f.lower() for f in room_features]
    available_room = None

    for name, info in rooms.items():
        room_features_in_room = [f.lower() for f in info["caratteristiche"]]
        if all(feature in room_features_in_room for feature in room_features):
            # Controlla disponibilità oraria
            if is_available(info, requested_start, requested_end):
                # Controlla capienza
                try:
                    persone = int(person_picker)
                except (ValueError, TypeError):
                    return jsonify({"error": "Numero partecipanti non valido"}), 400
                
                if persone <= info["capienza"]:
                    available_room = (name, info)
                    break

    if not available_room:
        return jsonify({"message": "Nessuna sala disponibile con le caratteristiche richieste"}), 404

    # Prenota
    name, info = available_room
    booking_id = str(uuid.uuid4())
    info["prenotazioni"].append({
        "id": booking_id,
        "user": email,
        "start": requested_start.strftime("%Y-%m-%d %H:%M"),
        "end": requested_end.strftime("%Y-%m-%d %H:%M"),
        "persons": person_picker
    })
    save_rooms(rooms)

    
    response = {
        "message": "Prenotazione effettuata con successo",
        "room_name": name,
        "numero": info["numero"],
        "caratteristiche": info["caratteristiche"],
        "capienza": info["capienza"],
        "start": requested_start.strftime("%Y-%m-%d %H:%M"),
        "end": requested_end.strftime("%Y-%m-%d %H:%M"),
        "booking_id": booking_id
    }

    features_str = ", ".join(info["caratteristiche"])
    email_subject = f"Prenotazione confermata: {name}"
    email_body = (
        f"Buongiorno,\n"
        f"La sala {name} (n. {info['numero']}) è stata prenotata con successo!\n\n"
        f"Data: {appointment_date}\n"
        f"Orario: {appointment_hour} - {requested_end.strftime('%H:%M')}\n"
        f"Partecipanti: {person_picker}\n"
        f"Caratteristiche: {features_str}\n"
        f"Capienza massima: {info['capienza']} persone."
    )
    #(Opzionale) invia email
    try:
        send_gmail_email(email, email_subject, email_body)
    except Exception as e:
        response["email_error"] = str(e)

    return jsonify(response), 200


# ============================================================
#                     AVVIO SERVER
# ============================================================

def run_flask_server():
    """Avvia il server Flask"""
    app.run(host="0.0.0.0", port=5050)


if __name__ == "__main__":
    # Esegui questo file direttamente per avviare il server
    run_flask_server()
