import os
import time
import json
import requests
import subprocess
from dotenv import load_dotenv # type: ignore
from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

load_dotenv()

app = FastAPI(title="Enterprise Chatbot API", version="1.0.0")
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# ------------ CONFIG ------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
NGROK_PATH = "C:\\Program Files\\WindowsApps\\ngrok.ngrok_3.24.0.0_x64__1g87z0zv29zzc\\ngrok.exe"
NGROK_CONFIG = "ngrok.yml"
# --------------------------------

ollama_url = None
rasa_base_url = None

# ----------------------------------------------------
# Avvia ngrok tramite ngrok.yml
# ----------------------------------------------------
def start_ngrok():
    global ollama_url, rasa_base_url

    subprocess.Popen([NGROK_PATH, "start", "--all", f"--config={NGROK_CONFIG}"])
    time.sleep(2)

    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels").json()["tunnels"]

        ollama_tunnel = next(t for t in resp if "11434" in t["config"]["addr"])
        rasa_tunnel = next(t for t in resp if "5005" in t["config"]["addr"])

        ollama_url = ollama_tunnel["public_url"]
        rasa_base_url = rasa_tunnel["public_url"]

        print("Ngrok Ollama:", ollama_url)
        print("Ngrok RASA (BASE):", rasa_base_url)

        return ollama_url, rasa_base_url

    except Exception as e:
        print("Errore avvio ngrok:", e)
        return None

# ----------------------------------------------------
# Aggiorna Gist
# ----------------------------------------------------
def update_gist(ollama_url, rasa_base_url):
    if not GITHUB_TOKEN or not GIST_ID:
        print("⚠️  GITHUB_TOKEN o GIST_ID mancanti")
        return

    api_url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "ollama_url.txt": {"content": ollama_url},
            "rasa_base_url.txt": {"content": rasa_base_url},
        }
    }

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        requests.patch(api_url, headers=headers, data=json.dumps(payload))
        print("✅ Gist aggiornato")
    except Exception as e:
        print("Errore aggiornamento Gist:", e)

# ----------------------------------------------------
# Funzione principale
# ----------------------------------------------------
@app.on_event("startup")
def startup_event():
    ollama_url, rasa_base_url = start_ngrok()
    if ollama_url and rasa_base_url:
        update_gist(ollama_url, rasa_base_url)