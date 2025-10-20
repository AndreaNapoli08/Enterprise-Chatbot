from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

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
        if fallback_count == 1:
            dispatcher.utter_message(response="utter_fallback")
        elif fallback_count == 2:
            dispatcher.utter_message(response="utter_fallback")
        else:
            dispatcher.utter_message(response="utter_contact_operator")
            fallback_count = 0  # reset dopo il terzo fallback

        # Aggiorna lo slot fallback_count
        return [SlotSet("fallback_count", fallback_count)]
