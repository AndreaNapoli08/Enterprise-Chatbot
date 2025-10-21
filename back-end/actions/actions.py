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
        if fallback_count < 3:
            dispatcher.utter_message(response="utter_fallback")
        else:
            dispatcher.utter_message(response="utter_contact_operator")
            fallback_count = 0  # reset dopo il terzo fallback consecutiv

        # Aggiorna lo slot fallback_count
        return [SlotSet("fallback_count", fallback_count)]
    
class ActionResetFallbackCount(Action):
    def name(self) -> Text:
        return "action_reset_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Resetta il contatore dei fallback
        return [SlotSet("fallback_count", 0)]

class ActionSaveMood(Action):
    def name(self):
        return "action_save_mood"

    def run(self, dispatcher, tracker, domain):
        latest_intent = tracker.latest_message["intent"].get("name")
        if latest_intent == "mood_unhappy":
            return [SlotSet("mood", "triste")]
        elif latest_intent == "mood_great":
            return [SlotSet("mood", "felice")]
        return []

class ActionRecallMood(Action):
    def name(self):
        return "action_recall_mood"

    def run(self, dispatcher, tracker, domain):
        mood = tracker.get_slot("mood")
        if mood:
            dispatcher.utter_message(text=f"Prima mi avevi detto che eri {mood}.")
        else:
            dispatcher.utter_message(text="Non ricordo come ti sentivi prima.")
        return []