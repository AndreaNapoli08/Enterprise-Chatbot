from flask import Flask, jsonify, request, send_from_directory # type: ignore
from flask_cors import CORS # type: ignore
import os
from actions.utils import load_users, save_users, hash_password, check_password

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
#                     ROUTE UTENTI
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
#                     AVVIO SERVER
# ============================================================

def run_flask_server():
    """Avvia il server Flask"""
    app.run(host="0.0.0.0", port=5050)


if __name__ == "__main__":
    # Esegui questo file direttamente per avviare il server
    run_flask_server()
