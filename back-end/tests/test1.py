import json
import requests
import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, accuracy_score
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer, util

# ==============================
# CONFIGURAZIONE
# ==============================
RASA_PARSE_URL = 'http://localhost:5005/model/parse'
RASA_WEBHOOK_URL = 'http://localhost:5005/webhooks/rest/webhook'
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

# ==============================
# FUNZIONI DI SUPPORTO
# ==============================
model_embed = SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_rasa_intent(question: str) -> dict:
    resp = requests.post(RASA_PARSE_URL, json={'text': question})
    return resp.json()

def send_message_to_rasa(question: str, email: str = 'test@example.com') -> list:
    resp = requests.post(RASA_WEBHOOK_URL, json={'message': question, 'metadata': {'email': email}})
    if resp.status_code == 200:
        return resp.json()
    return []

def semantic_similarity(text1: str, text2: str) -> float:
    emb1 = model_embed.encode(text1, convert_to_tensor=True)
    emb2 = model_embed.encode(text2, convert_to_tensor=True)
    return util.cos_sim(emb1, emb2).item()

# ==============================
# EVALUATION SCRIPT
# ==============================
def main(dataset_path: str):
    # Carica dataset
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    intents_gold = []
    intents_pred = []
    semantic_scores = []
    qa_scores = []
    bot_answers = []  # <-- salviamo qui le risposte

    for entry in dataset:
        question = entry['question']
        gold_answer = entry['gold_answer']
        expected_intent = entry['expected_intent']
        collection = entry.get('collection', None)

        # --- Ottieni intent da RASA ---
        intent_data = get_rasa_intent(question)
        predicted_intent = intent_data.get('intent', {}).get('name', 'unknown')

        intents_gold.append(expected_intent)
        intents_pred.append(predicted_intent)

        # --- Ottieni risposta dal webhook ---
        responses = send_message_to_rasa(question)
        if responses:
            bot_text = responses[0].get('text', '')
        else:
            bot_text = ''
        bot_answers.append(bot_text)  # <-- salvo la risposta

        # --- Calcola similarità semantica ---
        sim_score = semantic_similarity(bot_text, gold_answer)
        semantic_scores.append(sim_score)

        # Placeholder QA score
        qa_scores.append(np.nan)

        print(f"Question: {question}")
        print(f"Expected intent: {expected_intent} | Predicted: {predicted_intent}")
        print(f"Gold answer: {gold_answer}")
        print(f"Bot answer: {bot_text}")
        print(f"Semantic similarity: {sim_score:.3f}")
        print("-"*50)

    # --- Confusion Matrix ---
    cm = confusion_matrix(intents_gold, intents_pred, labels=list(set(intents_gold)))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=list(set(intents_gold)))
    disp.plot(xticks_rotation=90)
    plt.title("Intent Confusion Matrix")
    plt.show()

    # --- Accuracy ---
    acc = accuracy_score(intents_gold, intents_pred)
    print(f"Intent Accuracy: {acc*100:.2f}%")

    # --- Salva CSV di valutazione ---
    df = pd.DataFrame({
        'question': [e['question'] for e in dataset],
        'expected_intent': intents_gold,
        'predicted_intent': intents_pred,
        'gold_answer': [e['gold_answer'] for e in dataset],
        'bot_answer': bot_answers,  # <-- uso le risposte salvate
        'semantic_similarity': semantic_scores,
        'qa_score': qa_scores
    })

    df.to_csv('chatbot_evaluation.csv', index=False)
    print("Evaluation CSV salvato come chatbot_evaluation.csv")

# ==============================
# ENTRY POINT
# ==============================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Valutazione chatbot RASA + LangChain')
    parser.add_argument('--dataset', type=str, required=True, help='Percorso al dataset JSON')
    args = parser.parse_args()

    main(args.dataset)
