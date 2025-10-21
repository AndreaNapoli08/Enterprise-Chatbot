from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "company_docs"

# embeddings locali
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Contatore fallback consecutivi
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
    
# Resettare contatore fallback
class ActionResetFallbackCount(Action):
    def name(self) -> Text:
        return "action_reset_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Resetta il contatore dei fallback
        return [SlotSet("fallback_count", 0)]

# Salvare lo stato emotivo dell'utente
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

# Richiamare lo stato emotivo salvato
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

# Rispondere alle domande prendendo le informazioni dai file usando Chroma
class ActionAnswerFromChroma(Action):
    def name(self) -> Text:
        return "action_answer_from_chroma"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        query = tracker.latest_message.get("text")
        if not query:
            dispatcher.utter_message(text="Scusa, non ho capito la domanda.")
            return []

        # Carica il vectorstore persistente
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings
        )
        retriever = vectordb.as_retriever(search_kwargs={"k": 4})

        docs = retriever.get_relevant_documents(query)
        if not docs:
            dispatcher.utter_message(text="Non ho trovato informazioni rilevanti nei documenti.")
            return []

        # Risposta testuale semplice con i top-3 snippet
        snippets = []
        for i, d in enumerate(docs[:3], start=1):
            source = d.metadata.get("source", "")
            snippets.append(f"{i}. {d.page_content[:500]}... (source: {source})")

        dispatcher.utter_message(text="Ecco cosa ho trovato nei documenti:")
        dispatcher.utter_message(text="\n\n".join(snippets))
        return []