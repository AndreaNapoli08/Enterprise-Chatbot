from typing import Any, Text, Dict, List

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore
from rasa_sdk.events import SlotSet # type: ignore

    
# --- Gestione fallback consecutivi ---
class ActionHandleFallback(Action):
    def name(self) -> Text:
        return "action_handle_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Leggi il contatore fallback corrente
        fallback_count = tracker.get_slot("fallback_count") or 0

        # Incrementa il contatore
        fallback_count += 1

        # Decide quale risposta dare
        if fallback_count >= 2:
            dispatcher.utter_message(response="utter_contact_operator")
            fallback_count = 0 
        
        # Aggiorna lo slot fallback_count
        return [SlotSet("fallback_count", fallback_count)]
    
# --- Reset del contatore fallback ---
class ActionResetFallbackCount(Action):
    def name(self) -> Text:
        return "action_reset_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Resetta il contatore dei fallback
        return [SlotSet("fallback_count", 0)]