#!/bin/bash
set -e

# Log prefix per Home Assistant
echo "[WhatsApp Bot] Avvio in corso..."

# Verifica che credentials.json esista
if [ ! -f "/data/credentials.json" ]; then
    echo "[WhatsApp Bot] ❌ ERRORE: credentials.json non trovato in /data/"
    echo "[WhatsApp Bot] Per favore, copia il file credentials.json ottenuto da Google Cloud Console in /data/"
    echo "[WhatsApp Bot] Vedi: https://cloud.google.com/docs/authentication/getting-started"
    exit 1
fi

# Verifica che requirement.txt sia presente
if [ ! -f "/app/requirements.txt" ]; then
    echo "[WhatsApp Bot] ❌ ERRORE: requirements.txt non trovato"
    exit 1
fi

# Crea cartelle di dati se non esistono
mkdir -p /data
mkdir -p /config

# Copia credentials.json se necessario (da /config a /data per compatibilità)
if [ -f "/config/credentials.json" ] && [ ! -f "/data/credentials.json" ]; then
    echo "[WhatsApp Bot] 📋 Copia credentials.json da /config a /data..."
    cp /config/credentials.json /data/credentials.json
fi

# Setta variabili di environment se necessario
export PYTHONUNBUFFERED=1
export TZ=Europe/Rome

# Cambia directory e avvia il bot
cd /app

echo "[WhatsApp Bot] ✅ Ambiente pronto"
echo "[WhatsApp Bot] 🚀 Avvio bot..."

# Avvia il bot e gestisce i segnali correttamente
exec python3 -u garbage_bot.py
