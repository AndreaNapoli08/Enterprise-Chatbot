from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
# === Configurazioni ===
CHROMA_DIR = "actions/data/chroma_db"
COLLECTION_NAME = "company_docs"

# === Embeddings locali multilingua ===
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)

# ====================================================
# ===============   ACTIONS PERSONALIZZATE   ==========
# ====================================================

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
        if fallback_count < 3:
            dispatcher.utter_message(response="utter_fallback")
        else:
            dispatcher.utter_message(response="utter_contact_operator")
            fallback_count = 0  # reset dopo il terzo fallback consecutiv

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

# --- Salvataggio stato d'animo ---
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

# --- Richiamo dello stato d'animo ---
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

# --- Recupero risposte dai documenti ---
class ActionAnswerFromChroma(Action):
    def name(self) -> Text:
        return "action_answer_from_chroma"

    def run(self, dispatcher, tracker, domain):
        query = tracker.latest_message.get("text", "").strip().lower()
        if not query:
            dispatcher.utter_message(text="Scusa, non ho capito la domanda.")
            return []
        
        # Carica il database Chroma
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings
        )

        retriever = vectordb.as_retriever(search_kwargs={"k": 10})
        docs = retriever.get_relevant_documents(query)
        print(f"🔍 Query: {query}")
        for d in docs:
            print(f"→ Score: {getattr(d, 'score', '?')} | Contenuto: {d.page_content[:150]}")

        if not docs:
            dispatcher.utter_message(
                text="Non ho trovato informazioni rilevanti nei documenti."
            )
            return []

        # Mostra i migliori snippet
        snippets = []
        for i, d in enumerate(docs[:3], start=1):
            content = d.page_content.replace("\n", " ").strip()
            source = d.metadata.get("source", "")
            snippets.append(f"{i}. {content[:400]}... (fonte: {source})")

        dispatcher.utter_message(text="Ecco cosa ho trovato nei documenti:")
        dispatcher.utter_message(text="\n\n".join(snippets))
        return []