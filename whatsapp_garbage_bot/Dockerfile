ARG BUILD_FROM=python:3.12-slim
FROM ${BUILD_FROM}

# Metadata
LABEL maintainer="Your Name <your.email@example.com>" \
      io.hass.version="1.0.0" \
      io.hass.type="addon" \
      io.hass.arch="armhf|armv7|aarch64|amd64"

# Imposta la cartella di lavoro
WORKDIR /app

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y \
    libmagic1 \
    git \
    curl \
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
RUN mkdir -p /data /config

# Healthcheck endpoint (opzionale - richiede webserver leggero)
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Avvio
CMD [ "/run.sh" ]
