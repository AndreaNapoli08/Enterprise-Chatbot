import bcrypt
import json
from pathlib import Path
import os
from datetime import datetime, timedelta
import dateparser # type: ignore

# import per invio automatico dell'email
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from dotenv import load_dotenv # type: ignore

# import per il database
from db.models import User
from db.db import engine
from sqlmodel import Session, select

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
ROOMS_FILE = Path("actions/rooms.json")
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def hash_password(plain_password: str) -> str:
    """Restituisce l'hash della password in formato stringa UTF-8"""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se la password in chiaro corrisponde all'hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_by_email(email: str):
    """Restituisce l'utente dal DB dato l'email"""

    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        result = session.exec(statement).first()
        return result  # restituisce un oggetto User oppure None
    
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_rooms():
    with open(ROOMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_rooms(data):
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def parse_datetime(date_str: str, hour_str: str) -> datetime:
    # Combina data e ora
    datetime_str = f"{date_str} {hour_str}"
    dt = dateparser.parse(datetime_str, languages=['it'])
    if dt is None:
        raise ValueError(f"Impossibile parsare la data: {datetime_str}")
    return dt

def send_gmail_email(to_email, subject, body):
    creds_file = os.getenv("GMAIL_CREDENTIALS")  # path dal .env
    token_file = 'token.json'  # verrà generato alla prima autorizzazione

    creds = None
    # Prova a caricare token già salvato
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Se non c’è token valido, fai flusso OAuth
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
        creds = flow.run_local_server(port=8080, authorization_prompt_message="Apri questo link nel browser per autorizzare", access_type="offline", prompt="consent")
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Crea messaggio
    message = MIMEText(body)
    message['to'] = to_email
    message['from'] = creds.token_uri  # oppure tuo indirizzo Gmail
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()