from typing import Any, Text, Dict, List
import os, json, requests, re
from actions.utils import check_password

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore
from rasa_sdk.events import FollowupAction # type: ignore

# === Controlla il ruolo dell'utente loggato ===
class ActionCheckUserRole(Action):
    def name(self) -> Text:
        return "action_check_user_role"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> list:

        # 1️⃣ Prendi l'email dall'ultimo messaggio
        email = tracker.latest_message.get("metadata", {}).get("email")
        
        if not email:
            dispatcher.utter_message(text="Non riesco a identificare chi sei. Per favore loggati.")
            return []

        # 2️⃣ Chiamata HTTP al server per ottenere la lista utenti
        try:
            response = requests.get("http://localhost:5050/users") 
            response.raise_for_status()
            users = response.json()  # lista di utenti
        except Exception as e:
            dispatcher.utter_message(text="Errore nel recuperare gli utenti dal server.")
            return []

        # 3️⃣ Trova l'utente con la mail corretta
        user = next((u for u in users if u["email"] == email), None)
        if not user:
            dispatcher.utter_message(text="Utente non trovato.")
            return []

        if user["role"] != "Manager":
            dispatcher.utter_message(
                text=f"Mi dispiace, solo gli utenti con ruolo 'manager' possono eseguire questa azione."
            )
            return []

        # 5️⃣ Utente autorizzato
        dispatcher.utter_message(text=f"Accesso autorizzato come {user['role']} ✅")
         # Esegue un'altra azione subito dopo
        return [FollowupAction(name="utter_ask_meeting_date")]
    

# Cambio password dell'utente
class ActionChangePassword(Action):
    def name(self) -> Text:
        return "action_change_password"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> list:
        
        user_message = tracker.latest_message.get("text", "")
        print(user_message)
        pattern = r"vecchia password.*?:\s*([A-Za-z0-9@#\$%\^&\*\(\)_\-\+=!?\.:]{4,}).*?nuova password.*?:\s*([A-Za-z0-9@#\$%\^&\*\(\)_\-\+=!?\.:]{4,})"
        email = tracker.latest_message.get("metadata", {}).get("email")
        match = re.search(pattern, user_message, re.IGNORECASE)
        if not match:
            dispatcher.utter_message(text="Non sono riuscito a capire le password. Assicurati di scriverle così: 'La vecchia password è: ... La nuova password è: ...'")
            return []

        old_password, new_password = match.groups()
        print(f"Old: {old_password}, New: {new_password}")
        try:
            response = requests.get("http://localhost:5050/users") 
            response.raise_for_status()
            users = response.json()  # lista di utenti
        except Exception as e:
            dispatcher.utter_message(text="Errore nel recuperare gli utenti dal server.")
            return []
        
        user = next((u for u in users if u["email"] == email), None)
        print(user)
        if not user:
            dispatcher.utter_message(text="Utente non trovato.")
            return []

        if not check_password(old_password, user["password"]):
            dispatcher.utter_message(text="La vecchia password non è corretta.")
            return []
        
        try:
            update_response = requests.patch(
                "http://localhost:5050/users/update_password",
                json={"email": email, "password": new_password},
            )
            update_response.raise_for_status()
        except Exception as e:
            dispatcher.utter_message(text="Errore durante l'aggiornamento della password.")
            return []

        dispatcher.utter_message(text="✅ La password è stata modificata con successo.")
        return []