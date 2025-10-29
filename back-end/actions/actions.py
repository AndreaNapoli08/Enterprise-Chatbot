from typing import Any, Text, Dict, List
import os
import re
import warnings
import psutil
import json, requests, re
from datetime import datetime
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
        # === PROMPT PERSONALIZZATO PER DOMANDE SUI DOCUMENTI ===
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
        # if total_ram_gb < 8:
        #     model_name = "llama3.2:1b"      # ultra leggero
        # elif total_ram_gb < 12:
        #     model_name = "phi3:mini"        # bilanciato
        # else:
        #     model_name = "mistral"          # potente
        model_name = "mistral" 
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
            print("Catena di domanda-risposta costruita correttamente.")

            result = qa({"query": query})
            print("Risultato QA:", result)
            answer_text = result.get("result") if isinstance(result, dict) else str(result)
            print("Risposta generata dall'LLM:", answer_text)
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
    

# Provo a salvare in automatico il contesto
class ActionExtractContext(Action):
    def name(self) -> Text:
        return "action_extract_context"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text")
        if not user_message:
            return []

        # 🔹 Prompt GENERICO: il modello decide cosa estrarre
        prompt = f"""
            Sei un assistente italiano che estrae informazioni strutturate da un messaggio in formato JSON.
            
            Regole fondamentali:
            1. L'output DEVE essere solo un oggetto JSON valido, non aggiungere altro testo.
            2. Se l'utente esprime uno stato d'animo, USA SEMPRE la chiave "mood".
            3. Se una chiave non si applica, non includerla.

            Esempi:
            - Messaggio: "Oggi sono molto felice!" -> Risposta: {{"mood": "felice"}}
            - Messaggio: "Devo fissare una riunione per domani." -> Risposta: {{"azione": "fissare riunione", "data": "domani"}}
            - Messaggio: "Sono triste." -> Risposta: {{"mood": "triste"}}

            Messaggio dell'utente da analizzare: "{user_message}"
        """

        # Chiamata al modello locale (Ollama). Qui non uso LangChain per quello devo fare la chiamata al modello per diminuire l'overhead
        # LangChain ha senso se vogliamo integrare più fonti di conoscenza. In questo caso va bene solo la chiamata al modello essendo che abbiamo un singolo JSON 
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                #json={"model": "phi3:mini", "prompt": prompt, "stream": False},
                json={"model": "mistral", "prompt": prompt, "stream": False},
                timeout=200
            )
            print(response)
            data = response.json()
            print(data)
            text_output = data.get("response", data.get("text", "{}"))
            print(text_output)
        except Exception as e:
            text_output = "{}"

        # 🔹 Estrai il primo JSON valido dal testo
        match = re.search(r"\{.*\}", text_output, re.DOTALL)
        extracted = {}
        if match:
            try:
                extracted = json.loads(match.group(0))
            except Exception:
                extracted = {}

        # Aggiungi metadati (data e ultimo messaggio)
        extracted["_last_user_message"] = user_message
        extracted["_timestamp"] = datetime.utcnow().isoformat() + "Z"

        # 🔹 Recupera il contesto precedente (se esiste)
        prev_context = tracker.get_slot("auto_context")
        try:
            prev = json.loads(prev_context) if prev_context else {}
        except Exception:
            prev = {}

        # 🔹 Unisci vecchio e nuovo contesto
        merged = dict(prev)
        for k, v in extracted.items():
            # se entrambi liste → unisci
            if k in merged and isinstance(merged[k], list) and isinstance(v, list):
                merged[k] = list(dict.fromkeys(merged[k] + v))
            else:
                merged[k] = v

        new_context = json.dumps(merged, ensure_ascii=False)

        print(new_context)
        # 🔹 Salva tutto nello slot
        return [SlotSet("auto_context", new_context)]


class ActionQueryContext(Action):
    def name(self) -> Text:
        return "action_query_context"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Messaggio dell'utente (es: "con chi avevo la riunione?")
        user_question = tracker.latest_message.get("text")

        print("Domanda utente:", user_question)
        # Contesto salvato in auto_context
        context_json = tracker.get_slot("auto_context")

        print("Contesto:", context_json)
        if not context_json:
            dispatcher.utter_message("Non ho ancora informazioni salvate su di te")
            return []

        # Prompt dinamico per interrogare il contesto
        prompt = f"""
            Sei un assistente italiano che risponde alle domande basandosi solo sul seguente contesto JSON:

            {context_json}

            Domanda: "{user_question}"

            Istruzioni:
            - Rispondi sempre in italiano.
            - Rispondi all'utente usando il "tu", riferendoti a lui/lei in seconda persona.
            - Non parlare in prima persona.
            - Se la risposta è chiaramente deducibile dal contesto, rispondi in una o due frasi concise.
            - Se l'utente chiede il suo umore, rispondi come: "Oggi sei felice" o "Oggi sei triste".
            - Se la risposta non è nel contesto, di' chiaramente che non hai quell'informazione.
            - Non inventare nulla.
            - Restituisci solo una frase chiara.
        """
        print("Prompt generato:", prompt)
        # Chiamata all'LLM (esempio con Ollama)
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                #json={"model": "phi3:mini", "prompt": prompt, "stream": False, "options": {"temperature": 0}},
                json={"model": "mistral", "prompt": prompt, "stream": False, "options": {"temperature": 0}},
                timeout=200
            )
            print("qui arriva", response)
            data = response.json()
            print(data)
            answer = data.get("response", data.get("text", "")).strip()
            print(answer)
        except Exception as e:
            answer = f"Errore durante l'interrogazione del contesto: {e}"

        dispatcher.utter_message(text=answer)
        return []