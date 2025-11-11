import os
from typing import Any, Text, Dict, List
import re
from PyPDF2 import PdfReader # type: ignore

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore
from rasa_sdk.events import SlotSet, FollowupAction # type: ignore

# LangChain / Chroma / Embeddings / LLMs
from langchain.embeddings import HuggingFaceEmbeddings # type: ignore
from langchain.vectorstores import Chroma # type: ignore
from langchain.llms import Ollama # type: ignore
from langchain.chains import RetrievalQA # type: ignore
from langchain.prompts import PromptTemplate # type: ignore

# === CONFIGURAZIONI ===
PDF_DIR = os.path.join(os.path.dirname(__file__), "data/docs")
CHROMA_DIR = "actions/data/chroma_db" 
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Invio di un PDF locale in risposta a una richiesta dell'utente
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
                dispatcher.utter_message(text="Indicami il nome o l'argomento del documento che desideri visualizzare")
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