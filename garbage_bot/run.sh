#!/bin/bash
set -e

echo "[GarbageBot] Avvio in corso..."

# In Home Assistant, /config e /data sono montati dal Supervisor,
# ma garantiamo che esistano anche in esecuzione locale o test
mkdir -p /config /data

CRED_DATA="/data/credentials.json"
CRED_CONFIG="/config/credentials.json"
CRED_LOCAL="credentials.json"
CRED_APP="/app/credentials.json"

# 1. Copia credentials.json da /config (cartella condivisa di HA) a /data
if [ -f "$CRED_CONFIG" ] && [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] Trovato credentials.json in /config. Copio in /data..."
    cp "$CRED_CONFIG" "$CRED_DATA"
    chmod 600 "$CRED_DATA"
fi

# 2. Copia credentials.json dalla cartella corrente a /data
if [ -f "$CRED_LOCAL" ] && [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] Trovato credentials.json locale. Copio in /data..."
    cp "$CRED_LOCAL" "$CRED_DATA"
    chmod 600 "$CRED_DATA"
fi

# 3. Copia credentials.json da /app a /data se presente
if [ -f "$CRED_APP" ] && [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] Trovato credentials.json in /app. Copio in /data..."
    cp "$CRED_APP" "$CRED_DATA"
    chmod 600 "$CRED_DATA"
fi

# 4. Verifica finale della presenza del file
if [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] ERRORE CRITICO: credentials.json non trovato!"
    echo "[GarbageBot] Posizioni cercate:"
    echo "  - /config/credentials.json (Home Assistant config folder)"
    echo "  - /data/credentials.json (Storage interno dell'add-on)"
    echo "  - /app/credentials.json"
    echo ""
    echo "Soluzione:"
    echo "Copia il file credentials.json scaricato da Google Cloud nella cartella 'config' principale di Home Assistant (usando Samba, File Editor o Studio Code Server)."
    echo "Riavvia questo add-on e il bot lo spostera automaticamente al sicuro in /data."

    # Mantiene il container attivo invece di crashare, per consultare i log dall'interfaccia HA
    sleep infinity
fi

# Imposta variabili di ambiente (orario italiano e output non bufferizzato)
export PYTHONUNBUFFERED=1
export TZ=Europe/Rome

cd /app

echo "[GarbageBot] Ambiente pronto."
echo "[GarbageBot] Avvio bot..."

# exec fa subentrare Python al processo bash per la gestione corretta dei segnali SIGTERM
exec python3 -u garbage_bot.py