#!/bin/bash
set -e

echo "Inizio configurazione ambiente Bot WhatsApp..."

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

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "garbage_bot/requirements.txt" ]; then
    pip install -r garbage_bot/requirements.txt
fi

echo "Ambiente pronto."
echo "Per avviare il bot: cd ~/whatsapp_bot && source venv/bin/activate && python3 garbage_bot.py"