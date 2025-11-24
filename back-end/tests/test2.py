import json
import requests
import argparse
import os
import pandas as pd #type: ignore
import warnings
from sklearn.exceptions import UndefinedMetricWarning #type: ignore
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score, precision_recall_fscore_support #type: ignore
import seaborn as sns #type: ignore
import matplotlib.pyplot as plt #type: ignore

warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

# Questo
RASA_PARSE_URL = "http://localhost:5005/model/parse"
RASA_WEBHOOK_URL = "http://localhost:5005/webhooks/rest/webhook"

dataset_path = "test.json" 

# ------------------------------------------------------------
#  Funzione per interrogare RASA
# ------------------------------------------------------------
def send_to_rasa(message, email):
    """Ritorna: response_text """
    response = requests.post(RASA_WEBHOOK_URL, json={'message': message, 'metadata': {'email': email}})

    try:
        data = response.json()
    except:
        return "", None

    bot_response = ""

    for item in data:
        if "text" in item:
            bot_response += item["text"] + " "

    return bot_response.strip()

def get_last_action(sender_id="default"):
    """
    Recupera l'ultima action eseguita leggendo dal tracker di RASA.
    """
    try:
        tracker = requests.get(f"http://localhost:5005/conversations/{sender_id}/tracker").json()
        events = tracker.get("events", [])
    except Exception as e:
        print("Errore tracker:", e)
        return "no_action"

    last_action = "no_action"

    # Scorro gli eventi al contrario (dall'ultimo al primo)
    for ev in reversed(events):
        if ev.get("event") == "action":
            name = ev.get("name")
            if name not in ["action_listen", "action_reset_fallback", "action_handle_fallback"]:
                last_action = name
                break
    
    return last_action

def reset_conversation(sender_id="default"):
    requests.post(f"http://localhost:5005/conversations/{sender_id}/reset")

# ------------------------------------------------------------
#  MAIN
# ------------------------------------------------------------
def main(dataset_path: str):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"✔ Dataset caricato: {len(dataset)} esempi trovati.")
    results = []

    predicted_intents = []
    expected_intents = []

    index = 0
    sender = "test_user_1"
    email = "spospociao08@gmail.com"
    # MAIN LOOP
    for entry in dataset:
        print(f"Processing {index+1}/{len(dataset)}", end='\r')
        reset_conversation(sender)
        q = entry["question"]
        expected_intent = entry["expected_intent"]
        expected_action = entry["expected_action"]
        gold_answer = entry["gold_answer"]

        # 1) Intent prediction
        parse_response = requests.post(RASA_PARSE_URL, json={"text": q}).json()
        predicted_intent = parse_response.get("intent", {}).get("name")

        # 2) Action + Response
        bot_answer = send_to_rasa(q,email)
        executed_action = get_last_action("default")

        print("Bot answer: ", bot_answer)
        print("Executed action: ", executed_action)
        print("Gold answer: ", gold_answer) 
        predicted_intents.append(predicted_intent)
        expected_intents.append(expected_intent)

        # ------------------------------------------------------------
        #  RUBRIC EVALUATION
        # ------------------------------------------------------------
        intent_ok = (predicted_intent == expected_intent)
        action_ok = (expected_action == executed_action)

        # ------------------------------------------------------------
        #  NUOVA LOGICA RISPOSTA OK
        # ------------------------------------------------------------

        # Caso 1: se expected_action è solo custom (es: utter_ask_features_room) → usa action_ok
        if gold_answer is None or gold_answer == "" or expected_action.startswith("utter_"):
            answer_ok = action_ok

        else:
            # Caso 2: risposta testuale → usa vecchio soft-match delle keywords
            keywords = [
                k.strip().lower()
                for k in gold_answer.split()
                if len(k) > 4
            ]
            answer_ok = any(k in bot_answer.lower() for k in keywords)

        print("Punteggio answer: ",answer_ok)
        print("---------------------------------------------------\n")
        # ------------------------------------------------------------

        formatted_pair = f"Domanda:\n{q}\n\nRisposta:\n{bot_answer}"

        results.append({
            "pair": formatted_pair,
            "question": q,
            "bot_answer": bot_answer,
            "gold_answer": gold_answer,
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "intent_ok": intent_ok,
            "expected_action": expected_action,
            "executed_action": executed_action,
            "action_ok": action_ok,
            "answer_ok": answer_ok
        })

        index += 1

    # ------------------------------------------------------------
    #  CONFUSION MATRIX
    # ------------------------------------------------------------
    intent_labels = sorted(set(expected_intents + predicted_intents))
    intent_cm = confusion_matrix(expected_intents, predicted_intents, labels=intent_labels)

    plt.figure(figsize=(14,12))
    sns.heatmap(intent_cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=intent_labels, yticklabels=intent_labels)
    plt.xlabel("Predicted Intent")
    plt.ylabel("Expected Intent")
    plt.title("Confusion Matrix - INTENT")
    plt.tight_layout()
    plt.savefig("confusion_matrix_intent.png")
    plt.close()

    # ------------------------------------------------------------
    #  METRICHE AVANZATE
    # ------------------------------------------------------------

    print("\n========================================================")
    print("                METRICHE INTENT")
    print("========================================================")

    # Intent accuracy
    intent_accuracy = accuracy_score(expected_intents, predicted_intents)
    print(f"Intent Accuracy: {intent_accuracy:.4f}")

    # Precision, recall, F1
    precision, recall, f1, _ = precision_recall_fscore_support(
        expected_intents,
        predicted_intents,
        average='weighted',
        zero_division=0
    )

    print(f"Precision (weighted): {precision:.4f}")
    print(f"Recall (weighted):    {recall:.4f}")
    print(f"F1-score (weighted):  {f1:.4f}")

    # Classification report dettagliato
    report = classification_report(expected_intents, predicted_intents)
    print("\nDETTAGLIO PER INTENT:")
    print(report)

    # ------------------------------------------------------------
    #  CONFUSION MATRIX ACTION
    # ------------------------------------------------------------
    print("\n==========================================================")
    print("                CONFUSION MATRIX ACTION")
    print("========================================================")
    executed_actions = [r["executed_action"] if r["executed_action"] is not None else "no_action" for r in results]
    expected_actions_list = [r["expected_action"] if r["expected_action"] is not None else "no_action" for r in results]

    # Ora possiamo fare il set senza errori
    action_labels = sorted(set(expected_actions_list + executed_actions))
    action_cm = confusion_matrix(expected_actions_list, executed_actions, labels=action_labels)

    plt.figure(figsize=(12,8))
    sns.heatmap(action_cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=action_labels, yticklabels=action_labels)
    plt.xlabel("Predicted Action")
    plt.ylabel("Expected Action")
    plt.title("Confusion Matrix - ACTION")
    plt.tight_layout()
    plt.savefig("confusion_matrix_action.png")
    plt.close()

    # ------------------------------------------------------------
    #  ACTION METRICS
    # ------------------------------------------------------------
    print("\n========================================================")
    print("                METRICHE ACTION")
    print("========================================================")

    action_accuracy = accuracy_score(expected_actions_list, executed_actions)
    precision_a, recall_a, f1_a, _ = precision_recall_fscore_support(
        expected_actions_list, executed_actions, average='weighted', zero_division=0
    )

    print(f"Action Accuracy: {action_accuracy:.4f}")
    print(f"Precision (weighted): {precision_a:.4f}")
    print(f"Recall (weighted):    {recall_a:.4f}")
    print(f"F1-score (weighted):  {f1_a:.4f}")
    print("\nDETTAGLIO PER ACTION:")
    print(classification_report(expected_actions_list, executed_actions, zero_division=0))

    # ------------------------------------------------------------
    #  ANSWER QUALITY METRICS
    # ------------------------------------------------------------
    print("\n========================================================")
    print("                METRICHE RISPOSTE")
    print("========================================================")

    answer_correct = [1 if r["answer_ok"] else 0 for r in results]
    answer_accuracy = sum(answer_correct) / len(answer_correct)
    print(f"Answer Accuracy: {answer_accuracy:.4f}")

    # ------------------------------------------------------------
    #   GRAFICI EXTRA
    # ------------------------------------------------------------
    os.makedirs("evaluation_plots", exist_ok=True)

    # Answer accuracy pie
    plt.figure(figsize=(7,7))
    plt.pie([sum(answer_correct), len(answer_correct)-sum(answer_correct)],
            labels=["Corrette", "Errate"], autopct='%1.1f%%')
    plt.title("Qualità Risposte (Corrette vs Errate)")
    plt.savefig("evaluation_plots/answer_quality_pie.png", bbox_inches='tight')
    plt.close()

    # Bar chart Precision/Recall/F1 per intent
    report_dict = classification_report(expected_intents, predicted_intents, output_dict=True, zero_division=0)
    labels_intent, precision_vals, recall_vals, f1_vals = [], [], [], []
    for key, val in report_dict.items():
        if key not in ["accuracy", "macro avg", "weighted avg"]:
            labels_intent.append(key)
            precision_vals.append(val["precision"])
            recall_vals.append(val["recall"])
            f1_vals.append(val["f1-score"])

    x = range(len(labels_intent))
    plt.figure(figsize=(12,6))
    plt.bar(x, precision_vals, width=0.25, label='Precision')
    plt.bar([i+0.25 for i in x], recall_vals, width=0.25, label='Recall')
    plt.bar([i+0.50 for i in x], f1_vals, width=0.25, label='F1-score')
    plt.xticks([i+0.25 for i in x], labels_intent, rotation=45)
    plt.title("Precision / Recall / F1 per Intent")
    plt.legend()
    plt.tight_layout()
    plt.savefig("evaluation_plots/intent_metrics_bar.png", bbox_inches='tight')
    plt.close()

    # Errori per intent
    intent_errors = {}
    for exp, pred in zip(expected_intents, predicted_intents):
        if exp not in intent_errors:
            intent_errors[exp] = 0
        if exp != pred:
            intent_errors[exp] += 1

    plt.figure(figsize=(12,6))
    plt.bar(intent_errors.keys(), intent_errors.values())
    plt.title("Errori per Intent")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("evaluation_plots/errors_per_intent.png", bbox_inches='tight')
    plt.close()

    # ------------------------------------------------------------
    #  SAVE CSV
    # ------------------------------------------------------------
    df = pd.DataFrame(results)
    df.to_csv("chatbot_evaluation_results.csv", index=False)

    print("\n✔ CSV salvato come 'chatbot_evaluation_results.csv'")
    print("✔ Grafici generati")
    print("✔ Valutazione completata!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Valutazione chatbot RASA + LangChain')
    parser.add_argument('--dataset', type=str, required=True, help='Percorso al dataset JSON')
    args = parser.parse_args()
    main(args.dataset)