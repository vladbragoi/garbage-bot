#!/bin/bash

echo "🚀 Inizio configurazione ambiente Bot WhatsApp..."

# Aggiorna il sistema
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip libsqlite3-dev

# Crea la cartella del progetto se non esiste
mkdir -p ~/whatsapp_bot

# Copia tutto nella cartella del progetto
cp -r ./* ~/whatsapp_bot/

cd ~/whatsapp_bot

# Crea l'ambiente virtuale
python3 -m venv venv

# Attiva l'ambiente virtuale e installa le dipendenze
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Ambiente pronto!"
echo "👉 Per avviare il bot: cd ~/whatsapp_bot && source venv/bin/activate && python garbage_bot.py"