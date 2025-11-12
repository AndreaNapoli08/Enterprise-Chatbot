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
        
        endpoint = os.getenv("BOOKING_API_URL")
        payload = {
            "appointment_date": appointment_date,
            "appointment_hour": appointment_hour,
            "appointment_duration": appointment_duration,
            "person_picker": person_picker,
            "room_features": room_features,
            "email": email,
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=10)
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

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Recupera l'email (dal metadata o dallo slot)
        user_email = tracker.latest_message.get("metadata", {}).get("email") or tracker.get_slot("email")

        if not user_email:
            dispatcher.utter_message(text="Non ho trovato la tua email. Puoi fornirmela per favore?")
            return []

        endpoint = os.getenv("RESERVATIONS_API_URL")
        api_url = f"{endpoint}{user_email}"

        try:
            response = requests.get(api_url, timeout=10)
            data = response.json()
        except Exception as e:
            dispatcher.utter_message(text=f"Errore di connessione al server: {e}")
            return []

        if response.status_code == 200:
            prenotazioni = data.get("prenotazioni", [])
            dispatcher.utter_message(
                text=f"📅 Prenotazioni trovate per {user_email}:",
                json_message={
                    "type": "lista_prenotazioni",
                    "email": user_email,
                    "prenotazioni": prenotazioni
                }
            )
        else:
            dispatcher.utter_message(text=f"Non ho trovato prenotazioni a nome di {user_email}.")

        return []
    
class ActionDeleteReservation(Action):
    def name(self) -> Text:
        return "action_delete_reservation"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get("text", "")
        match = re.search(r"[0-9a-fA-F-]{36}", text)

        if not match:
            dispatcher.utter_message(text="Non ho trovato un ID prenotazione nel messaggio.")
            return []

        reservation_id = match.group(0)

        endpoint = api_url = os.getenv("RESERVATIONS_API_URL")
        api_url = f"{endpoint}{reservation_id}"

        try:
            response = requests.delete(api_url, timeout=10)
            data = response.json()
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Errore di connessione al server: {e}")
            return []

        if response.status_code == 200:
            dispatcher.utter_message(text=data.get("message", "Prenotazione cancellata con successo."))
        else:
            dispatcher.utter_message(text=data.get("error", "Non è stato possibile cancellare la prenotazione."))

        return []