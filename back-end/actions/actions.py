from typing import Any, Text, Dict, List
import os
import re
import warnings
import psutil
warnings.filterwarnings("ignore", category=DeprecationWarning)

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# LangChain / Chroma / Embeddings / LLMs
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# === CONFIGURAZIONI ===
CHROMA_DIR = "actions/data/chroma_db"   # aggiorna se il tuo percorso è diverso
COLLECTION_NAME = "company_docs"

# Embeddings (stesso modello usato in ingest.py)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# === PROMPT ===
PROMPT_TEMPLATE = """Sei un assistente che risponde solo in italiano.
Hai a disposizione delle informazioni provenienti da documenti (contesto).
Rispondi alla domanda in modo breve, chiaro e preciso, in una o due frasi.
Se la risposta non è nel contesto, di' che non è specificato nel documento.

Contesto:
{context}

Domanda:
{question}

Risposta concisa in italiano:
"""

PROMPT = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

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
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # ----------- ESTRAI LA DOMANDA DALLA TRACCIA ---------
        query = tracker.latest_message.get("text", "").strip()
        if not query:
            dispatcher.utter_message(text="Scusa, non ho capito la domanda.")
            return []

        # --- CARICA IL DATABASE CHROMA ---
        try:
            vectordb = Chroma(
                persist_directory=CHROMA_DIR,
                collection_name=COLLECTION_NAME,
                embedding_function=embeddings
            )
        except Exception as e:
            dispatcher.utter_message(text=f"Errore caricando il database Chroma: {e}")
            return []
        
        print("Database Chroma caricato correttamente.")

        # Recuperatore: cerchiamo i chunk più pertinenti
        retriever = vectordb.as_retriever(search_kwargs={"k": 2})

        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        print("RAM totale disponibile:", total_ram_gb, "GB")
        if total_ram_gb < 8:
            model_name = "llama3.2:1b"      # ultra leggero
        elif total_ram_gb < 12:
            model_name = "phi3:mini"        # bilanciato
        else:
            model_name = "mistral"          # potente
        
        try:
            llm = Ollama(model=model_name, temperature=0)

        except Exception as e:
            dispatcher.utter_message(text=f"Errore inizializzando il modello Ollama: {e}")
            return []
        
        print("Modello Ollama", model_name, "inizializzato correttamente.")
        
        # === COSTRUISCI CATENA DI DOMANDA-RISPOSTA ===
        try:
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                chain_type="stuff",  # sufficiente per piccoli contesti
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )

            result = qa({"query": query})
            answer_text = result.get("result") if isinstance(result, dict) else str(result)

        except Exception as e:
            answer_text = None
            print("Errore nel processo QA:", e)

        # === FALLBACK: se LLM non risponde, cerca manualmente ===
        if not answer_text:
            docs = retriever.get_relevant_documents(query)
            if not docs:
                dispatcher.utter_message(text="Non ho trovato informazioni rilevanti nei documenti.")
                return []
            answer_text = docs[0].page_content.strip()[:300] + "..."

        # Pulizia finale
        answer_text = re.sub(r"\s+", " ", answer_text).strip()
        if len(answer_text) > 400:
            answer_text = answer_text[:400] + "..."

        dispatcher.utter_message(text=answer_text)
        return []