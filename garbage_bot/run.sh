#!/bin/bash
set -e

echo "[GarbageBot] Avvio in corso..."

# In Home Assistant, /config e /data sono già montati dal Supervisor,
# ma ci assicuriamo che esistano nel caso tu stia testando in locale
mkdir -p /config /data

CRED_DATA="/data/credentials.json"
CRED_CONFIG="/config/credentials.json"
CRED_LOCAL="credentials.json"

# 1. Copia credentials.json da /config (Cartella condivisa di HA) a /data
if [ -f "$CRED_CONFIG" ] && [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] 📋 Trovato credentials.json in /config. Copio in /data..."
    cp "$CRED_CONFIG" "$CRED_DATA"
    chmod 600 "$CRED_DATA"
fi

# 2. Copia credentials.json dalla cartella locale a /data
if [ -f "$CRED_LOCAL" ] && [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] 📋 Trovato credentials.json locale. Copio in /data..."
    cp "$CRED_LOCAL" "$CRED_DATA"
    chmod 600 "$CRED_DATA"
fi

# 3. Verifica finale della presenza del file
if [ ! -f "$CRED_DATA" ]; then
    echo "[GarbageBot] ❌ ERRORE CRITICO: credentials.json non trovato!"
    echo "[GarbageBot] Posizioni cercate:"
    echo "  - /config/credentials.json (Home Assistant config folder)"
    echo "  - /data/credentials.json (Storage interno dell'add-on)"
    echo ""
    echo "👉 SOLUZIONE:"
    echo "Copia il file credentials.json scaricato da Google Cloud nella cartella 'config' principale di Home Assistant (puoi usare Samba, File Editor o Studio Code Server)."
    echo "Riavvia questo add-on e il bot lo sposterà automaticamente al sicuro."
    
    # Mette il container in standby invece di crashare, così puoi leggere questo log nell'UI di HA
    sleep infinity
fi

# Imposta variabili di ambiente (forza l'orario italiano e l'output in tempo reale)
export PYTHONUNBUFFERED=1
export TZ=Europe/Rome

cd /app

echo "[GarbageBot] ✅ Ambiente pronto."
echo "[GarbageBot] 🚀 Avvio bot..."

# exec fa subentrare Python al processo bash. È vitale affinché 
# Home Assistant riesca a spegnere il bot in modo pulito (inviando il SIGTERM direttamente a Python).
exec python3 -u garbage_bot.py