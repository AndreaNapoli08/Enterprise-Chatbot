# back-end/main.py
import os
import requests
import subprocess
import time
import json
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Importa l'app di server.py
from actions.server import app as server_app

load_dotenv()

# ------------ CONFIG ------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
NGROK_PATH = "C:\\Program Files\\WindowsApps\\ngrok.ngrok_3.24.0.0_x64__1g87z0zv29zzc\\ngrok.exe"
# --------------------------------

# Prendi l'app di server.py
app = server_app

# Aggiungi il middleware CORS se non già presente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # eventualmente mettere il dominio del front-end
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variabile globale per URL pubblico
public_url = None

# ---------------------------
# 🔧 Funzione: avvia ngrok e prende l'URL pubblico
# ---------------------------
def start_ngrok():
    global public_url
    subprocess.Popen([NGROK_PATH, "http", "11434"])
    time.sleep(2)
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = resp.json()["tunnels"]
        public_url = tunnels[0]["public_url"]
        print("Ngrok URL:", public_url)
        return public_url
    except Exception as e:
        print("Errore avvio ngrok:", e)
        return None

# ---------------------------
# 🔧 Funzione: aggiorna Gist
# ---------------------------
def update_gist(url):
    if not GITHUB_TOKEN or not GIST_ID:
        print("GITHUB_TOKEN o GIST_ID non impostati")
        return
    api_url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "ngrok_url.txt": {
                "content": url
            }
        }
    }
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        requests.patch(api_url, headers=headers, data=json.dumps(payload))
        print("Gist aggiornato:", url)
    except Exception as e:
        print("Errore aggiornamento Gist:", e)

# ---------------------------
# Endpoint per fornire l'URL pubblico al front-end
# ---------------------------
@app.get("/api/info")
def info():
    return {"public_url": public_url}

# ---------------------------
# 🔧 Avvio di ngrok + aggiornamento Gist all'avvio del server
# ---------------------------
@app.on_event("startup")
def startup_event():
    url = start_ngrok()
    if url:
        update_gist(url)
