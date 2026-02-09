# Usa un'immagine base Debian (risolve i problemi di compatibilità)
FROM python:3.12-slim

# Imposta la cartella di lavoro
WORKDIR /app

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libmagic1 \
    git \
    curl \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia i requisiti e installali
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Copia lo script di avvio
COPY run.sh /
RUN chmod a+x /run.sh

# Crea cartelle necessarie
RUN mkdir -p /config /data && \
    echo "# Copy your credentials.json here" > /config/README.txt

# Volume mounts per Home Assistant
# /config  -> Configurazione (credentials.json, config files)
# /data    -> Database persistenti (garbage_bot.sqlite, garbage_bot_config.sqlite)

# Healthcheck endpoint (opzionale - richiede webserver leggero)
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Avvio
CMD [ "/run.sh" ]
