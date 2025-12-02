FROM python:3.9-slim

WORKDIR /app

# Installa pacchetti necessari
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il tuo backend
COPY . .

# Rendi eseguibile lo script di startup
RUN chmod +x start.sh

# Espone le porte interne del container (non usate da Render, ma utili)
EXPOSE 5005
EXPOSE 5055
EXPOSE 10000

# Comando di avvio
CMD ["./start.sh"]
