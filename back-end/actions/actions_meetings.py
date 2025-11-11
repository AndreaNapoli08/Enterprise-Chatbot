from typing import Any, Text, Dict, List
from pathlib import Path
import json, re, os
from datetime import datetime, timedelta
import dateparser # type: ignore
import uuid

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore

# import per invio automatico dell'email
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from dotenv import load_dotenv # type: ignore

# === CONFIGURAZIONI ===
ROOMS_FILE = Path("actions/rooms.json")
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --- Controllo disponibilità sala ---
class ActionAvailabilityCheckRoom(Action):
    def name(self) -> Text:
        return "action_availability_check_room"

    @staticmethod
    def load_rooms():
        with open(ROOMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_rooms(data):
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
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

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Recupera gli slot
        appointment_date = tracker.get_slot("appointment_date")
        appointment_hour = tracker.get_slot("appointment_hour")
        appointment_duration = tracker.get_slot("appointment_duration")
        person_picker = tracker.get_slot("person_picker")
        room_features = tracker.get_slot("room_features")
        
        if not appointment_date or not room_features or not appointment_hour or not appointment_duration:
            dispatcher.utter_message(
                text="Mi servono data, ora di inizio, durata e caratteristiche richieste per verificare la disponibilità."
            )
            return []
        
        requested_start = self.parse_datetime(appointment_date, appointment_hour)
        requested_end = requested_start + timedelta(hours=float(appointment_duration))

        rooms = self.load_rooms()

        def is_available(room, start, end):
            for booking in room["prenotazioni"]:
                booking_start = datetime.strptime(booking["start"], "%Y-%m-%d %H:%M")
                booking_end = datetime.strptime(booking["end"], "%Y-%m-%d %H:%M")
                if not (end <= booking_start or start >= booking_end):
                    return False
            return True
        
        room_features = [f.lower() for f in room_features]
        
        # Cerca una sala disponibile
        available_room = None
        for name, info in rooms.items():
            room_features_in_room = [f.lower() for f in info["caratteristiche"]]
            if all(feature in room_features_in_room for feature in room_features):
                if is_available(info, requested_start, requested_end):
                    available_room = (name, info)
                    break

        if available_room:
            name, info = available_room
            email = tracker.latest_message.get("metadata", {}).get("email")
            booking_id = str(uuid.uuid4())
            # Salva la prenotazione
            info["prenotazioni"].append({
                "id": booking_id,
                "user": email,
                "start": requested_start.strftime("%Y-%m-%d %H:%M"),
                "end": requested_end.strftime("%Y-%m-%d %H:%M"),
                "persons": person_picker
            })
            self.save_rooms(rooms)

            # Crea il messaggio di conferma
            features_str = ", ".join(info["caratteristiche"])
            message = (
                f"✅ La sala {name} (n. {info['numero']}) è stata prenotata con successo!\n\u200B\n"
                f"📅 Data: {appointment_date}\n"
                f"🕓 Orario: {appointment_hour} - {requested_end.strftime('%H:%M')}\n"
                f"👥 Partecipanti: {person_picker}\n"
                f"🏢 Caratteristiche: {features_str}\n"
                f"👥 Capienza massima: {info['capienza']} persone."
            )

            dispatcher.utter_message(text=message)
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
            # Invio dell'email di conferma
            # try: 
            #     ActionAvailabilityCheckRoom.send_gmail_email(email, email_subject, email_body)
            # except Exception as e:
            #     dispatcher.utter_message(text=f"Errore nell'invio dell'email: {e}")
        else:
            dispatcher.utter_message(
                text="Mi dispiace, non ci sono sale disponibili con le caratteristiche richieste in questo orario."
            )

        return []
    
class ActionGetReservation(Action):
    def name(self) -> Text:
        return "action_get_reservation"
    
    @staticmethod
    def load_rooms():
        with open(ROOMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Recupera l'email (o nome utente) dallo slot
        user_email = tracker.latest_message.get("metadata", {}).get("email")

        if not user_email:
            dispatcher.utter_message(text="Non ho trovato la tua email. Puoi fornirmela per favore?")
            return []

        # Percorso del file JSON (modificalo secondo la tua struttura)
        file_path = os.path.join(os.path.dirname(__file__), "sale.json")

        # Leggi il file JSON
        data = self.load_rooms()

        # Cerca prenotazioni dell'utente
        prenotazioni_utente = []

        for nome_sala, info_sala in data.items():
            for prenotazione in info_sala.get("prenotazioni", []):
                # Ogni prenotazione può avere 'user' o 'email'
                if prenotazione.get("user") == user_email:
                    prenotazioni_utente.append({
                        "id": prenotazione.get("id"),
                        "sala": nome_sala,
                        "numero": info_sala.get("numero"),
                        "inizio": prenotazione.get("start"),
                        "fine": prenotazione.get("end"),
                        "persone": prenotazione.get("persons")
                    })

        # Risposta all’utente
        if not prenotazioni_utente:
            dispatcher.utter_message(text=f"Non ho trovato prenotazioni a nome di {user_email}.")
        else:
            dispatcher.utter_message(
                text=f"📅 Prenotazioni trovate per {user_email}:", 
                json_message={
                    "type": "lista_prenotazioni",
                    "email": user_email,
                    "prenotazioni": prenotazioni_utente
                }
            )
        return []
    
class ActionDeleteReservation(Action):
    def name(self) -> Text:
        return "action_delete_reservation"
    
    @staticmethod
    def load_rooms():
        with open(ROOMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_rooms(data):
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get("text", "")
        match = re.search(r"[0-9a-fA-F-]{36}", text)

        if not match:
            dispatcher.utter_message(text="Non ho trovato un ID prenotazione nel messaggio.")
            return []

        reservation_id = match.group(0)

        if not reservation_id:
            dispatcher.utter_message(text="Non ho ricevuto l'ID della prenotazione da cancellare.")
            return []

        # Carica le sale
        rooms = self.load_rooms()
        
        for sala, info in rooms.items():
            prenotazioni = info.get("prenotazioni", [])
            for p in prenotazioni:
                if p.get("id") == reservation_id:
                    prenotazioni.remove(p)
                    self.save_rooms(rooms)
                    dispatcher.utter_message(text=f"La prenotazione per {sala} (n.{info.get('numero')}) è stata cancellata con successo.")
                    return []
           
        dispatcher.utter_message(text="Non ho trovato nessuna prenotazione con l'ID fornito.")
        return []
    