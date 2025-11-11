from typing import Any, Text, Dict, List
import requests
from PyPDF2 import PdfReader
from datetime import datetime
import os, json, requests, re

# import per rasa
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction

# Salvataggio del contesto
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


# Prelievo del contesto e risposta alle domande
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