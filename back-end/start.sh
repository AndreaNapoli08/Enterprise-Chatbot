#!/bin/bash

# Avvia Rasa (NLU + Core)
rasa run --enable-api --cors "*" --port 5005 &

# Avvia il Rasa Action Server
rasa run actions --port 5055 &

# Avvia FastAPI sulla porta fornita da Render
uvicorn main:app --host 0.0.0.0 --port $PORT
