from typing import Any, Text, Dict, List
from pathlib import Path
import json, re, os, requests

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore

# === CONFIGURAZIONI ===
ROOMS_FILE = Path("actions/rooms.json")

# --- Controllo disponibilità sala ---
class ActionAvailabilityCheckRoom(Action):
    def name(self) -> Text:
        return "action_availability_check_room"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Recupera gli slot dal tracker
        appointment_date = tracker.get_slot("appointment_date")
        appointment_hour = tracker.get_slot("appointment_hour")
        appointment_duration = tracker.get_slot("appointment_duration")
        person_picker = tracker.get_slot("person_picker")
        room_features = tracker.get_slot("room_features")

        # Puoi passare l’email da metadata o da slot
        email = tracker.latest_message.get("metadata", {}).get("email") or tracker.get_slot("email")

        if not appointment_date or not room_features or not appointment_hour or not appointment_duration:
            dispatcher.utter_message(
                text="Mi servono data, ora di inizio, durata e caratteristiche richieste per verificare la disponibilità."
            )
            return []

        # Prepara la chiamata HTTP al server Flask
        api_url = "http://localhost:5050/rooms/book"
        payload = {
            "appointment_date": appointment_date,
            "appointment_hour": appointment_hour,
            "appointment_duration": appointment_duration,
            "person_picker": person_picker,
            "room_features": room_features,
            "email": email,
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            data = response.json()
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Errore di connessione al server prenotazioni: {e}")
            return []

        # Gestione della risposta
        if response.status_code == 200:
            room_name = data.get("room_name")
            numero = data.get("numero")
            start = data.get("start")
            end = data.get("end")
            capienza = data.get("capienza")
            caratteristiche = ", ".join(data.get("caratteristiche", []))
            persons = data.get("persons", person_picker)

            message = (
                f"✅ La sala {room_name} (n. {numero}) è stata prenotata con successo!\n\u200B\n"
                f"📅 Data: {appointment_date}\n"
                f"🕓 Orario: {appointment_hour} - {end[-5:]}\n"
                f"👥 Partecipanti: {persons}\n"
                f"🏢 Caratteristiche: {caratteristiche}\n"
                f"👥 Capienza massima: {capienza} persone."
            )
            dispatcher.utter_message(text=message)

        elif response.status_code == 404:
            dispatcher.utter_message(
                text="😞 Mi dispiace, non ci sono sale disponibili con le caratteristiche richieste in questo orario."
            )
        else:
            error = data.get("error") or data.get("message", "Errore sconosciuto.")
            dispatcher.utter_message(text=f"⚠️ Errore durante la prenotazione: {error}")

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
    