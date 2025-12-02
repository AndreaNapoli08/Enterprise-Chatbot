# Usa un'immagine leggera di Python
FROM python:3.9-slim

# Imposta la cartella di lavoro
WORKDIR /app

# Installa dipendenze di sistema necessarie a RASA e Postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt e installa pacchetti Python
COPY back-end/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il back-end
COPY . .

# Esponi le porte usate da RASA e FastAPI
EXPOSE 5005
EXPOSE 10000

# Avvia RASA + FastAPI insieme
CMD ["bash", "-c", "rasa run --enable-api --cors '*' & uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
