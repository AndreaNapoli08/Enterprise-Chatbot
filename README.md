# Enterprise-Chatbot

Un sistema di chatbot conversazionale intelligente progettato per supportare i dipendenti di organizzazioni enterprise nell'accesso a informazioni aziendali, gestione di risorse condivise e risoluzione di problematiche comuni. Implementa NLU con RASA, Retrieval-Augmented Generation con ChromaDB e Ollama, e una moderna interfaccia frontend con Angular.

## 🎯 Panoramica del Progetto

Enterprise-Chatbot è una soluzione end-to-end che dimostra come combinare tecnologie moderne di intelligenza artificiale conversazionale per creare un assistente virtuale enterprise-ready. Il sistema gestisce conversazioni multi-turn complesse, integra documenti aziendali tramite ricerca semantica, e automatizza operazioni critiche come la prenotazione di sale riunioni e la gestione delle credenziali utente.

### Casi d'Uso Principali

- **Ricerca Documentale**: Ricerca semantica in documenti aziendali (policy, procedure, linee guida) con risposte generate tramite RAG
- **Prenotazione Sale Riunioni**: Flusso conversazionale multi-turn per prenotare sale con parametri intelligenti (capienza, caratteristiche, orari)
- **Gestione Credenziali**: Cambio password sicuro con validazione e hashing bcrypt
- **Gestione Profilo**: Accesso alle prenotazioni personali e gestione delle sessioni di chat
- **Help Desk 24/7**: Primo livello di supporto automatizzato con escalation intelligente

## ✨ Caratteristiche Principali

### Back-end
- **RASA NLU**: Riconoscimento intenti con accuracy 92.37% e gestione intelligente del fallback
- **Dialog Management**: Policy-based dialog management con regole deterministiche e modelli neurali
- **RAG Pipeline**: Integrazione ChromaDB + Ollama per risposta documentale semanticamente consapevole
- **FastAPI**: Server REST asincrono con type safety, documentazione OpenAPI auto-generata
- **PostgreSQL**: Database relazionale con supporto JSONB per dati semi-strutturati
- **Custom Actions**: Framework estensibile per integrazioni con sistemi backend

### Front-end
- **Angular 16+**: Framework SPA moderno con componenti standalone
- **Real-time Chat**: Interfaccia conversazionale con support multi-turn e persistenza sessioni
- **Responsive Design**: Tailwind CSS + Flowbite per UI professionale e mobile-friendly
- **Dark Mode**: Sincronizzazione automatica con preferenze di sistema
- **Jasmine Testing**: Suite completa di test unitari (100% pass rate)

### Architettura
- **Modularità**: Separazione netta tra NLU, Dialog Management, Custom Actions
- **Scalabilità**: Architettura ASGI asincrona per gestione elevato throughput
- **Persistenza**: Chat history completa per analisi, debugging e miglioramento continuo
- **Sicurezza**: Password hashing bcrypt, JWT-ready, CORS configurabile

## 📊 Risultati della Valutazione

La valutazione sistematica del sistema su 118 test cases ha prodotto i seguenti risultati:

| Componente | Metrica | Risultato | Valutazione |
|-----------|---------|-----------|------------|
| NLU | Intent Accuracy | 92.37% |  Eccellente |
| NLU | Precision (weighted) | 94.05% |  Eccellente |
| NLU | F1-score (weighted) | 92.83% |  Eccellente |
| Dialog | Action Accuracy | 91.53% |  Eccellente |
| Dialog | Precision (weighted) | 92.53% |  Eccellente |
| RAG | Answer Accuracy | 86.44% |  Buono |
| Risposte | Tempo Medio | 11.53 sec |  Critico |
| Frontend | Test Pass Rate | 100% (40+ test) |  Eccellente |

### Performance per Intent
- Intent con F1=1.00 (performance perfetta): 16/23
- Intent con F1>0.90: 22/23
- Intent problematico identificato: `nlu_fallback` (F1: 0.71)

### Azioni Critiche
- `action_answer_from_chroma`: F1=0.96 (35 occorrenze - azione RAG core)
- `action_change_password`: F1=1.00
- `action_delete_reservation`: F1=1.00
- `action_get_reservation`: F1=0.86

## 🚀 Quick Start

### Prerequisiti
- Python 3.8+
- Node.js 18+
- PostgreSQL 12+
- Docker & Docker Compose (opzionale)

### Installation

**1. Backend Setup**
```bash
cd back-end
pip install -r requirements.txt
cp config.example.yml config.yml
# Configurare le credenziali database in config.yml
python main.py
# RASA server sarà disponibile su http://localhost:5005
```

**2. Frontend Setup**
```bash
cd front-end
npm install
ng serve
# App sarà disponibile su http://localhost:4200
```

**3. Database Setup**
```bash
cd back-end/db
python init_neon_db.py  # Inizializzare database PostgreSQL
python import_json.py   # Importare dati di esempio
```

**4. Docker Setup (Alternativa)**
```bash
docker-compose up -d
# Tutti i servizi saranno orchestrati automaticamente
```

### Configurazione

Creare un file `.env` nella root del back-end:
```
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot_db
RASA_URL=http://localhost:5005
OLLAMA_URL=http://localhost:11434
CHROMA_HOST=localhost
CHROMA_PORT=8000
JWT_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:4200
```

## 📁 Struttura del Progetto

```
Enterprise-Chatbot/
├── back-end/
│   ├── main.py                 # Entry point FastAPI
│   ├── server.py              # Server RASA launcher
│   ├── utils.py               # Utility functions
│   ├── requirements.txt        # Python dependencies
│   ├── config.yml             # RASA configuration
│   ├── domain.yml             # RASA domain definition
│   ├── endpoints.yml          # RASA endpoints
│   ├── actions/               # Custom actions
│   │   ├── actions_context.py
│   │   ├── actions_documents.py
│   │   ├── actions_fallback.py
│   │   ├── actions_meetings.py
│   │   ├── actions_users.py
│   │   └── data/              # Vector database & documents
│   ├── data/                  # NLU & Dialog training data
│   │   ├── nlu.yml
│   │   ├── rules.yml
│   │   └── stories.yml
│   ├── db/                    # Database layer
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── db.py              # Database connection
│   │   └── json/              # Sample data
│   └── test/                  # Testing suite
│       ├── test.py            # Main test runner
│       ├── test.json          # Test cases (118 examples)
│       └── chatbot_evaluation_results.csv
│
├── front-end/
│   ├── src/
│   │   ├── main.ts            # Bootstrap Angular
│   │   ├── index.html
│   │   ├── styles.css
│   │   ├── app/
│   │   │   ├── app.component.ts
│   │   │   ├── app.routes.ts  # Routing configuration
│   │   │   ├── auth.guard.ts  # Authentication guard
│   │   │   ├── services/      # HTTP services
│   │   │   ├── login/
│   │   │   ├── home/          # Main chat interface
│   │   │   ├── chat-bubble/
│   │   │   ├── input-text/
│   │   │   ├── profile/
│   │   │   ├── sidebar/
│   │   │   └── interfaces/    # TypeScript interfaces
│   ├── package.json
│   ├── tsconfig.json
│   └── angular.json
│
├── docker-compose.yml         # Docker orchestration
└── README.md                  # This file
```

## 🔧 Architettura del Sistema

```
┌─────────────────────────────────────────────────┐
│           Frontend (Angular 16+)                │
│  ┌────────────────┬──────────────┬────────────┐ │
│  │ Login/Auth     │ Chat Bubble  │ Sidebar    │ │
│  │ Input Handler  │ Input Text   │ Profile    │ │
│  └────────────────┴──────────────┴────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │ REST API (HTTPS)
        ┌──────────────┴───────────────┐
        │                              │
   ┌────▼──────────────────┐   ┌──────▼──────────────┐
   │   FastAPI Server      │   │  RASA Dialog Engine │
   │  (Port 8000)          │   │  (Port 5005)        │
   │ ┌──────────────────┐  │   │ ┌────────────────┐  │
   │ │ /users/*         │  │   │ │ NLU (Intent    │  │
   │ │ /documents/*     │  │   │ │ Classification)│  │
   │ │ /bookings/*      │  │   │ │ Dialog Policy  │  │
   │ │ /sessions/*      │  │   │ │ Actions        │  │
   │ └──────────────────┘  │   │ └────────────────┘  │
   └────┬─────────────────┘   └──────┬───────────────┘
        │                           │
        └─────────────┬─────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
   ┌────▼──────────┐      ┌─────────▼─────┐
   │ PostgreSQL    │      │ ChromaDB +     │
   │ Database      │      │ Ollama         │
   │ ┌──────────┐  │      │ (RAG Pipeline) │
   │ │ Users    │  │      │ ┌────────────┐ │
   │ │ Documents│  │      │ │ Embeddings │ │
   │ │ Bookings │  │      │ │ LLM Gen    │ │
   │ │ Sessions │  │      │ └────────────┘ │
   │ │ Messages │  │      │                │
   │ └──────────┘  │      └────────────────┘
   └───────────────┘
```

## 🎓 Flussi Conversazionali Implementati

### 1. Ricerca Documentale (RAG)
```
Utente: "Come posso aggiornare i dati bancari?"
  ↓
NLU: Intent = ask_information_aziendale
  ↓
Custom Action: ActionAnswerFromChroma
  - Embedding query
  - Similarity search in ChromaDB
  - Retrieval top-2 documenti
  - Generazione risposta con Ollama
  ↓
Chatbot: "Secondo la policy aziendale... [fonte: informazioni_aziendali.pdf]"
```

### 2. Prenotazione Sale Riunioni
```
Utente: "Vorrei prenotare una sala per domani"
  ↓
NLU: Intent = book_room
  ↓
Dialog Manager: Multi-turn form collection
  - Data (date picker)
  - Ora inizio/fine
  - Numero partecipanti
  - Caratteristiche richieste (checkbox)
  ↓
Custom Action: ActionAvailabilityCheckRoom
  - Verifica capienza
  - Controllo conflitti temporali
  - Selezione sala ottimale
  ↓
Database: INSERT prenotazione in JSONB array
  ↓
Chatbot: "Prenotazione confermata - Sala 12, 14 gennaio 10:00-11:00 [ID: abc123]"
```

### 3. Cambio Password
```
Utente: "Voglio cambiare password"
  ↓
NLU: Intent = change_password
  ↓
Dialog: Request current password (masked input)
  ↓
Backend: Verify password con bcrypt
  ↓
Dialog: Request new password + confirmation
  ↓
Backend: Hash new password, UPDATE user
  ↓
Chatbot: "✓ Password modificata con successo"
```

## 📈 Metriche Chiave

### Intent Classification
- **Accuracy**: 92.37% (109/118 test cases)
- **Precision (macro)**: 0.92
- **Recall (macro)**: 0.89
- **F1-score (weighted)**: 92.83%

### Dialog Management
- **Action Accuracy**: 91.53%
- **Most reliable actions**: utter_greet (F1=0.91), action_answer_from_chroma (F1=0.96)
- **Problem area**: nlu_fallback (F1=0.71)

### Response Quality
- **Answer Accuracy**: 86.44%
- **Average Response Time**: 11.53 seconds
- **Bottleneck**: Ollama text generation on CPU

## 🔐 Sicurezza

### Implemented
- ✅ Password hashing con bcrypt (12 salt rounds)
- ✅ CORS configuration
- ✅ Type validation via Pydantic
- ✅ Input sanitization


---

**Ultima modifica**: Gennaio 2026  
**Versione**: 1.0 (Thesis Release)  
**Status**: Prototype - Ready for Evaluation & Research