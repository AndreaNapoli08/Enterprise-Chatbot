from typing import Any, Text, Dict, List
import os
import re
from unittest import result
import warnings
import json, requests, re
from datetime import datetime
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
import dateparser
import requests
import uuid

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("langchain.utils.math").setLevel(logging.ERROR)
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"

# import per invio automatico dell'email
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# import per server Flask per documenti
from flask import Flask, send_from_directory
import threading

# import per rasa
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

# LangChain / Chroma / Embeddings / LLMs
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import BM25Retriever
from langchain.retrievers import BM25Retriever
from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.retrievers import EnsembleRetriever
from PyPDF2 import PdfReader

# === CONFIGURAZIONI ===
CHROMA_DIR = "actions/data/chroma_db" 
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# === JSON con le stanze disponibili ===
ROOMS_FILE = Path("actions/rooms.json")

# Embeddings (stesso modello usato in ingest.py)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# === Server Flask per servire i documenti ===
app = Flask(__name__)

# cartella dove tieni i pdf
PDF_DIR = os.path.join(os.path.dirname(__file__), "data/docs")

@app.route("/documents/<filename>")
def serve_pdf(filename):
    return send_from_directory(
        directory=PDF_DIR,
        path=filename,
        as_attachment=True 
    )

def run_flask_server():
    app.run(host="0.0.0.0", port=5050)

# Avvia Flask in parallelo quando parte l’action server
threading.Thread(target=run_flask_server, daemon=True).start()


# ====================================================
# ===============   ACTIONS PERSONALIZZATE   =========
# ====================================================

# --- Invio PDF locali ---
class ActionSendLocalPDF(Action):
    def name(self) -> str:
        return "action_send_local_pdf"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text").lower()

        # Mappa di documenti disponibili
        pdf_map = {
            "informazioni": "informazioni_aziendali.pdf",
            "linee guida": "linee_guida.pdf",
        }

        # Trova il PDF più rilevante
        selected_pdf = None
        for key, filename in pdf_map.items():
            if key in user_message:
                selected_pdf = filename
                break
            
        if not selected_pdf:
            user_events = [e for e in tracker.events if e.get("event") == "user"]
            intent_name = user_events[-2].get("parse_data", {}).get("intent", {}).get("name")
            if intent_name == "ask_information_relazione":
                selected_pdf = "linee_guida.pdf"    
            elif intent_name == "ask_information_aziendale":
                selected_pdf = "informazioni_aziendali.pdf" 
            else:
                dispatcher.utter_message(text="Non ho trovato un documento corrispondente alla tua richiesta.")
                return []
        
        # path del file PDF
        pdf_path = os.path.join(PDF_DIR, selected_pdf)

        # Ottieni dimensione e numero di pagine
        size_bytes = os.path.getsize(pdf_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
        except Exception:
            num_pages = "N/D"

        pdf_url = f"http://localhost:5050/documents/{selected_pdf}"
        dispatcher.utter_message(
            text="Ecco il documento che hai richiesto:",
            attachment={
                "type": "file",
                "url": pdf_url,
                "name": selected_pdf,
                "size": size_mb,
                "pages": num_pages
            }
        )
        return []
    
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

# --- Elenco documenti disponibili da far scegliere all'utente quando non sa la risposta alla domanda ---
class ActionListAvailableDocuments(Action):
    def name(self) -> Text:
        return "action_list_available_documents"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Elenco dei file PDF nella cartella
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

        if not pdf_files:
            dispatcher.utter_message(text="Non ci sono documenti disponibili al momento.")
            return []

        # Crea i bottoni per ogni PDF
        buttons = []
        for f in pdf_files:
            title = os.path.splitext(f)[0].replace("_", " ").title()  # es. "policy_aziendale.pdf" -> "Policy Aziendale"
            payload = f'/choose_document{{"file_name":"{f}"}}'
            buttons.append({"title": title, "payload": payload})

        # Invia il messaggio con i bottoni
        dispatcher.utter_message(
            text="Ecco i documenti disponibili. Dove vuoi che cerco la risposta?",
            buttons=buttons
        )
        return []
    
# --- Recupero risposte dai documenti ---
class ActionAnswerFromChroma(Action):
    vectordbs = {}
    llm = None
    qa_chains = {}

    def name(self) -> Text:
        return "action_answer_from_chroma"
    
    def expand_query(q: str) -> str:
        synonyms = {
            "erogazione": ["accredito", "pagamento", "versamento"],
            "comunicare": ["pianificare", "informare"],
            "stipendio": ["retribuzione", "salario", "busta paga"],
            "giorno": ["data", "scadenza", "entro quando"],
            "ferie": ["vacanze", "congedo"],
        }
        for k, vals in synonyms.items():
            if k in q.lower():
                q += " " + " ".join(vals)

        return q

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        file_name = next(tracker.get_latest_entity_values("file_name"), None) or tracker.get_slot("file_name")

        # Recuperiamo l'intent della domanda e scegliamo la collezione dove cercare la risposta
        intent_name = tracker.latest_message.get("intent", {}).get("name")

        if intent_name == "ask_information_relazione":
            collection_name = "relazione_docs"
        elif intent_name == "ask_information_aziendale":
            collection_name = "azienda_docs"
        elif file_name:
            if(file_name == "linee_guida.pdf"):
                collection_name = "relazione_docs"
            elif(file_name == "informazioni_aziendali.pdf"):    
                collection_name = "azienda_docs" 
        else:
            dispatcher.utter_message(text="Non sono sicuro di dove cercare la risposta")
            return []

        # --- Inizializza il vectordb solo la prima volta ---
        if collection_name not in ActionAnswerFromChroma.vectordbs:
            try:
                vectordb = Chroma(
                    persist_directory=CHROMA_DIR,
                    collection_name=collection_name,
                    embedding_function=embeddings,
                )
                ActionAnswerFromChroma.vectordbs[collection_name] = vectordb
            except Exception as e:
                dispatcher.utter_message(text=f"Errore caricando Chroma: {e}")
                return []
        else:
            vectordb = ActionAnswerFromChroma.vectordbs[collection_name]

        # --- Inizializza l’LLM una sola volta ---
        if ActionAnswerFromChroma.llm is None:
            try:
                ActionAnswerFromChroma.llm = Ollama(
                    model="phi3:3.8b",
                    #model="mistral",
                    temperature=0
                )
            except Exception as e:
                dispatcher.utter_message(text=f"Errore inizializzando LLM: {e}")
                return []
            
        # --- Inizializza la QA chain per la collezione (una volta sola) ---
        if collection_name not in ActionAnswerFromChroma.qa_chains:
            semantic_retriever = vectordb.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 2, "fetch_k": 4, "lambda_mult": 0.5}
            )

            # === PROMPT OTTIMIZZATO ===
            PROMPT_TEMPLATE = """
            Sei un assistente che risponde solo in italiano. 
            Hai a disposizione delle informazioni provenienti da documenti (contesto).
            Rispondi in modo breve, chiaro e preciso (una o due frasi), salvo si tratti di una procedura: in quel caso spiega i passaggi essenziali.
            Se il contesto contiene riferimenti impliciti o sinonimi, deduci la risposta con ragionamento.
            Se non c'è davvero nessun riferimento, rispondi chiaramente che non è specificato nel documento senza spiegare nient'altro.

            Contesto:
            {context}

            Domanda:
            {question}

            Risposta concisa in italiano:
            """
            PROMPT = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])

            qa_chain = RetrievalQA.from_chain_type(
                llm=ActionAnswerFromChroma.llm,
                retriever=semantic_retriever,
                chain_type="stuff",
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT, "document_variable_name": "context"}
            )
            ActionAnswerFromChroma.qa_chains[collection_name] = qa_chain
        else:
            qa_chain = ActionAnswerFromChroma.qa_chains[collection_name]

        # ----------- ESTRAI LA DOMANDA DALLA TRACCIA ---------
        query = tracker.latest_message.get("text", "").strip()
        query = ActionAnswerFromChroma.expand_query(query)
        if query.startswith("/choose_document"):
            user_messages = [e for e in tracker.events if e.get("event") == "user"]
            query = user_messages[-3].get("text")

        if not query:
            dispatcher.utter_message(text="Scusa, non ho capito la domanda.")
            return []

        # === COSTRUISCI CATENA DI DOMANDA-RISPOSTA ===
        try:
            # Verifica se ci sono contenuti rilevanti nei documenti
            results_with_score = vectordb.similarity_search_with_score(query, k=2)
            if not results_with_score or all(score > 1.1  for _, score in results_with_score):
                dispatcher.utter_message(text="Nessuna risposta rilevante è stata trovata nei documenti")
                fallback_count = tracker.get_slot("fallback_count") or 0
                fallback_count += 1

                if fallback_count >= 2:
                    dispatcher.utter_message(response="utter_contact_operator")
                    fallback_count = 0 
    
                return [SlotSet("fallback_count", fallback_count)]
            
            result = qa_chain.invoke({"query": query})
            answer_text = result.get("result") if isinstance(result, dict) else str(result)
        except Exception as e:
            answer_text = None
            print("Errore nel processo QA:", e)

        # === FALLBACK: se LLM non risponde ===
        if not answer_text:
            docs = semantic_retriever.get_relevant_documents(query)
            if not docs:
                dispatcher.utter_message(text="Non ho trovato informazioni rilevanti nei documenti.")
                return []

        # Pulizia finale
        answer_text = re.sub(r"\s+", " ", answer_text).strip()

        # Estrazione delle fonti
        source_docs = result.get("source_documents", [])
        if source_docs:
            best_doc = source_docs[0]  # documento con similarità più alta
            meta = getattr(best_doc, "metadata", {})
            source_name = meta.get("source", "Documento sconosciuto")
            sources_text = f"Fonte: {os.path.basename(source_name)}"
        else:
            sources_text = ""

        # Invia la risposta completa all'utente
        final_message = f"{answer_text}\n\u200B\n{sources_text}"
        dispatcher.utter_message(text=final_message)

        return []

class ActionSaveContext(Action):
    def name(self) -> Text:
        return "action_save_context"

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
            2. Se l'utente esprime uno stato d'animo, usa la chiave "mood".
            3. Se ti chiede informazioni riguardo un documento, salva il nome del documento su cui ti ha fatto la domanda con la chiave "documents".
            4. Se una chiave non si applica, non includerla.

            Esempi:
            - Messaggio: "Oggi sono molto felice!" -> Risposta: {{"mood": "felice"}}
            - Messaggio: "Devo fissare una riunione per domani." -> Risposta: {{"azione": "fissare riunione", "data": "domani"}}
            - Messaggio: "Sono triste." -> Risposta: {{"mood": "triste"}}
            - Messaggio: "Chi deve approvare le mie ferie?" -> Risposta: {{"documents": ["informazioni_aziendali.pdf"]}}
            - Messaggio: "Che struttura ha la relazione?" -> Risposta: {{"documents": ["linee_guida.pdf"]}}

            Messaggio dell'utente da analizzare: "{user_message}"
        """

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi3:3.8b", "prompt": prompt, "stream": False},
                #json={"model": "mistral", "prompt": prompt, "stream": False},
                timeout=200
            )
            data = response.json()
            text_output = data.get("response", data.get("text", "{}"))
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
        # Contesto salvato in auto_context
        context_json = tracker.get_slot("auto_context")

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
        # Chiamata all'LLM (esempio con Ollama)
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "phi3:3.8b", "prompt": prompt, "stream": False, "options": {"temperature": 0}},
                #json={"model": "mistral", "prompt": prompt, "stream": False, "options": {"temperature": 0}},
                timeout=200
            )
            data = response.json()
            answer = data.get("response", data.get("text", "")).strip()
        except Exception as e:
            answer = f"Errore durante l'interrogazione del contesto: {e}"

        dispatcher.utter_message(text=answer)
        return []
    
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
            response = requests.get("http://localhost:3000/users") 
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
    
# --- Controllo disponibilità sala ---
class ActionAvailabilityCheckRoom(Action):
    def name(self) -> Text:
        return "action_availability_check_room"

    @staticmethod
    def load_rooms():
        with open(ROOMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_rooms(data):
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def parse_datetime(date_str: str, hour_str: str) -> datetime:
        # Combina data e ora
        datetime_str = f"{date_str} {hour_str}"
        dt = dateparser.parse(datetime_str, languages=['it'])
        if dt is None:
            raise ValueError(f"Impossibile parsare la data: {datetime_str}")
        return dt
    
    def send_gmail_email(to_email, subject, body):
        creds_file = os.getenv("GMAIL_CREDENTIALS")  # path dal .env
        token_file = 'token.json'  # verrà generato alla prima autorizzazione

        creds = None
        # Prova a caricare token già salvato
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        # Se non c’è token valido, fai flusso OAuth
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=8080, authorization_prompt_message="Apri questo link nel browser per autorizzare", access_type="offline", prompt="consent")
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        service = build('gmail', 'v1', credentials=creds)

        # Crea messaggio
        message = MIMEText(body)
        message['to'] = to_email
        message['from'] = creds.token_uri  # oppure tuo indirizzo Gmail
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw}).execute()

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Recupera gli slot
        appointment_date = tracker.get_slot("appointment_date")
        appointment_hour = tracker.get_slot("appointment_hour")
        appointment_duration = tracker.get_slot("appointment_duration")
        person_picker = tracker.get_slot("person_picker")
        room_features = tracker.get_slot("room_features")
        
        if not appointment_date or not room_features or not appointment_hour or not appointment_duration:
            dispatcher.utter_message(
                text="Mi servono data, ora di inizio, durata e caratteristiche richieste per verificare la disponibilità."
            )
            return []
        
        requested_start = self.parse_datetime(appointment_date, appointment_hour)
        requested_end = requested_start + timedelta(hours=float(appointment_duration))

        rooms = self.load_rooms()

        def is_available(room, start, end):
            for booking in room["prenotazioni"]:
                booking_start = datetime.strptime(booking["start"], "%Y-%m-%d %H:%M")
                booking_end = datetime.strptime(booking["end"], "%Y-%m-%d %H:%M")
                if not (end <= booking_start or start >= booking_end):
                    return False
            return True
        
        room_features = [f.lower() for f in room_features]
        
        # Cerca una sala disponibile
        available_room = None
        for name, info in rooms.items():
            room_features_in_room = [f.lower() for f in info["caratteristiche"]]
            if all(feature in room_features_in_room for feature in room_features):
                if is_available(info, requested_start, requested_end):
                    available_room = (name, info)
                    break

        if available_room:
            name, info = available_room
            email = tracker.latest_message.get("metadata", {}).get("email")
            booking_id = str(uuid.uuid4())
            # Salva la prenotazione
            info["prenotazioni"].append({
                "id": booking_id,
                "user": email,
                "start": requested_start.strftime("%Y-%m-%d %H:%M"),
                "end": requested_end.strftime("%Y-%m-%d %H:%M"),
                "persons": person_picker
            })
            self.save_rooms(rooms)

            # Crea il messaggio di conferma
            features_str = ", ".join(info["caratteristiche"])
            message = (
                f"✅ La sala {name} (n. {info['numero']}) è stata prenotata con successo!\n\u200B\n"
                f"📅 Data: {appointment_date}\n"
                f"🕓 Orario: {appointment_hour} - {requested_end.strftime('%H:%M')}\n"
                f"👥 Partecipanti: {person_picker}\n"
                f"🏢 Caratteristiche: {features_str}\n"
                f"👥 Capienza massima: {info['capienza']} persone."
            )

            dispatcher.utter_message(text=message)
            email_subject = f"Prenotazione confermata: {name}"
            email_body = (
                f"Buongiorno,\n"
                f"La sala {name} (n. {info['numero']}) è stata prenotata con successo!\n\n"
                f"Data: {appointment_date}\n"
                f"Orario: {appointment_hour} - {requested_end.strftime('%H:%M')}\n"
                f"Partecipanti: {person_picker}\n"
                f"Caratteristiche: {features_str}\n"
                f"Capienza massima: {info['capienza']} persone."
            )
            # Invio dell'email di conferma
            # try: 
            #     ActionAvailabilityCheckRoom.send_gmail_email(email, email_subject, email_body)
            # except Exception as e:
            #     dispatcher.utter_message(text=f"Errore nell'invio dell'email: {e}")
        else:
            dispatcher.utter_message(
                text="Mi dispiace, non ci sono sale disponibili con le caratteristiche richieste in questo orario."
            )

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

        # Percorso del file JSON (modificalo secondo la tua struttura)
        file_path = os.path.join(os.path.dirname(__file__), "sale.json")

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