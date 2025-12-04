from typing import Any, Text, Dict, List
import requests
from datetime import datetime
import os, json, requests, re

# import per rasa
from rasa_sdk import Action, Tracker # type: ignore
from rasa_sdk.executor import CollectingDispatcher # type: ignore
from rasa_sdk.events import SlotSet # type: ignore

def get_ollama_url():
    """
    Recupera l'URL di Ollama attraverso Ngrok leggendo il tuo Gist.
    """
    GIST_URL = "https://gist.githubusercontent.com/AndreaNapoli08/0b153d525eb3a45d37cafd65b32bca8c/raw/ollama_url.txt"

    try:
        res = requests.get(GIST_URL, timeout=5)
        url = res.text.strip()
        if url.startswith("http"):
            return url 
    except:
        pass

    return None

def call_ollama(prompt: str, model: str = "phi3:3.8b"):
    """
    Esegue una richiesta al modello Ollama usando l’URL dinamico Ngrok.
    """
    base_url = get_ollama_url()
    if not base_url:
        return "{}"  # fallback

    print(base_url)
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0}
            },
            timeout=200
        )
        data = response.json()
        return data.get("response", data.get("text", ""))
    except Exception as e:
        return "{}"


# Salvataggio del contesto
class ActionSaveContext(Action):
    def name(self) -> Text:
        return "action_save_context"

    async def run(self, dispatcher, tracker, domain):

        user_message = tracker.latest_message.get("text")
        if not user_message:
            return []

        # Prompt GENERICO: il modello decide cosa estrarre
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

        # 💡 Chiamata a Ollama via ngrok
        text_output = call_ollama(prompt)
        print("Ollama output:", text_output)
        # Estrazione JSON
        match = re.search(r"\{.*\}", text_output, re.DOTALL)
        extracted = {}
        if match:
            try:
                extracted = json.loads(match.group(0))
            except:
                extracted = {}

        extracted["_last_user_message"] = user_message
        extracted["_timestamp"] = datetime.utcnow().isoformat() + "Z"

        prev_context = tracker.get_slot("auto_context")
        try:
            prev = json.loads(prev_context) if prev_context else {}
        except:
            prev = {}

        merged = dict(prev)
        for k, v in extracted.items():
            if k in merged and isinstance(merged[k], list) and isinstance(v, list):
                merged[k] = list(dict.fromkeys(merged[k] + v))
            else:
                merged[k] = v

        return [SlotSet("auto_context", json.dumps(merged, ensure_ascii=False))]


# Prelievo del contesto e risposta alle domande
class ActionQueryContext(Action):
    def name(self) -> Text:
        return "action_query_context"

    async def run(self, dispatcher, tracker, domain):

        user_question = tracker.latest_message.get("text")
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

        # 💡 Chiamata ad Ollama via Ngrok
        answer = call_ollama(prompt).strip()
        if not answer:
            answer = "Non ho trovato informazioni rilevanti nel contesto."

        dispatcher.utter_message(text=answer)
        return []
