#!/bin/bash
set -e

# Log prefix per Home Assistant
echo "[WhatsApp Bot] Avvio in corso..."

# Crea cartelle di dati se non esistono
mkdir -p /config
mkdir -p /data

# Copia credentials.json da /config a /data se necessario
if [ -f "/config/credentials.json" ] && [ ! -f "/data/credentials.json" ]; then
    echo "[WhatsApp Bot] 📋 Copia credentials.json da /config a /data..."
    cp /config/credentials.json /data/credentials.json
    chmod 600 /data/credentials.json
fi

# Copia credentials.json da /config a /data se necessario
if [ -f "credentials.json" ] && [ ! -f "/data/credentials.json" ]; then
    echo "[WhatsApp Bot] 📋 Copia credentials.json in /data..."
    cp credentials.json /data/credentials.json
    chmod 600 /data/credentials.json
fi

# Verifica che credentials.json esista dopo la copia
if [ ! -f "/data/credentials.json" ]; then
    echo "[WhatsApp Bot] ❌ ERRORE: credentials.json non trovato!"
    echo "[WhatsApp Bot] Posizioni cercate:"
    echo "[WhatsApp Bot]   - /config/credentials.json (Home Assistant config folder)"
    echo "[WhatsApp Bot]   - /data/credentials.json (appuntamento interno)"
    echo "[WhatsApp Bot]"
    echo "[WhatsApp Bot] Soluzione:"
    echo "[WhatsApp Bot] Copia il file credentials.json da Google Cloud Console in /config/ via SSH o FTP."
    echo "[WhatsApp Bot] Il bot lo copierà automaticamente in /data/ al prossimo avvio."
    echo "[WhatsApp Bot] Vedi: https://cloud.google.com/docs/authentication/getting-started"
    exit 1
fi

# Verifica che requirement.txt sia presente
if [ ! -f "/app/requirements.txt" ]; then
    echo "[WhatsApp Bot] ❌ ERRORE: requirements.txt non trovato"
    exit 1
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
