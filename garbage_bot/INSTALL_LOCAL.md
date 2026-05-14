# 🐧 Installazione Locale - Linux / Raspberry Pi

**⚠️ Nota:** Questa è un'installazione alternativa. Se usi **Home Assistant**, é consigliato installare il bot come [add-on ufficiale](INSTALL_HOMEASSISTANT.md).

Guida per installare ed eseguire **WhatsApp Garbage Bot** su **Linux** (incluso Raspberry Pi OS).

---

## 📋 Prerequisiti

- **Python 3.10+** (verifica con `python3 --version`)
- **Git** (opzionale, per clonare il repository)
- **Google Sheet** configurato (vedi [SETUP_CALENDARIO.md](SETUP_CALENDARIO.md))
- **Credenziali Google** in file `credentials.json` (vedi [Step 1](#step-1-ottieni-le-credenziali-google))

---

## 🚀 Step 1: Ottieni le Credenziali Google

### Crea un Service Account su Google Cloud

1. Vai su https://console.cloud.google.com/
2. Crea un nuovo progetto (o seleziona uno esistente)
3. Naviga a **APIs & Services > Enable APIs and Services**
4. Cerca e abilita **Google Sheets API**
5. Vai a **Service Accounts** (menu sinistro)
6. Clicca **Create Service Account**
7. Compila nome e descrizione, poi clicca **Create and Continue**
8. Salta i ruoli opzionali, clicca **Continue**
9. Clicca **Create Key > JSON**
10. Salvo il file come `credentials.json` (scaricato automaticamente)

### Condividi il Google Sheet con il Service Account

1. Apri il file `credentials.json` con un editor di testo
2. Copia il value di `client_email` (es: `bot-service@project-id.iam.gserviceaccount.com`)
3. Apri il tuo **Google Sheet**
4. Clicca **Share** in alto a destra
5. Incolla l'email del service account
6. Dai permessi di **Editor**
7. Disabilita **"Notify people"** e clicca **Share**

✅ Il bot ora ha accesso allo sheet!

---

## 🚀 Step 2: Scarica il Bot

### Opzione A: Git (Consigliato)

```bash
cd ~
git clone https://github.com/your-username/whatsapp-garbage-bot.git
cd whatsapp-garbage-bot
```

### Opzione B: Scarica ZIP

1. Vai al repository GitHub
2. Clicca **<> Code** > **Download ZIP**
3. Estrai il file in una cartella
4. `cd` nella cartella

---

## 🚀 Step 3: Installa le Dipendenze

### Crea un Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

### Installa i Pacchetti

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Verifica l'Installazione

```bash
pip list | grep -E "neonize|gspread|xhtml2pdf"
```

Dovresti vedere:
```
gspread
neonize
xhtml2pdf
```

---

## 🚀 Step 4: Configurazione Iniziale

### Copia il File credentials.json

```bash
# Se scaricato in Downloads
cp ~/Downloads/credentials.json .

# Verifica che sia presente
ls -la credentials.json
```

---

## ⚙️ Step 4b: Configurazione Variabili del Bot

Il bot supporta le stesse variabili configurabili di Home Assistant attraverso **variabili d'ambiente** (consigliato per sicurezza) o tramite il file `options.json`.

### Prioritario: Variabili d'Ambiente (Consigliato ⭐)

Le variabili d'ambiente hanno **priorità** rispetto a options.json e non vengono salvate persistentemente.

#### Esecuzione Manuale

```bash
# Imposta le variabili e avvia il bot
export LOG_LEVEL="info"
export TELEGRAM_TOKEN="123456789:ABCDefGhijKlmnoPqrstUvwxyz"
export TELEGRAM_CHAT_ID="987654321"
export BOT_MOBILE_NUMBER="393501234567"

python3 garbage_bot.py
```

#### Con Systemd

Modifica il file di servizio:

```bash
sudo nano /etc/systemd/system/whatsapp_bot.service
```

Nella sezione `[Service]` aggiungi:

```ini
[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/whatsapp-garbage-bot
Environment="PATH=/home/pi/whatsapp-garbage-bot/venv/bin"
Environment="PYTHONUNBUFFERED=1"
# Aggiungi le variabili d'ambiente (facoltative - ometti se non usate):
Environment="LOG_LEVEL=info"
Environment="TELEGRAM_TOKEN=123456789:ABCDefGhijKlmnoPqrstUvwxyz"
Environment="TELEGRAM_CHAT_ID=987654321"
Environment="BOT_MOBILE_NUMBER=393501234567"
ExecStart=/home/pi/whatsapp-garbage-bot/venv/bin/python3 garbage_bot.py
Restart=on-failure
RestartSec=10
```

Poi riavvia:
```bash
sudo systemctl daemon-reload
sudo systemctl restart whatsapp_bot
```

#### Con Docker

```bash
docker run -d \
  --name whatsapp_bot \
  -v ~/whatsapp_bot_data:/data \
  -e LOG_LEVEL="info" \
  -e TELEGRAM_TOKEN="123456789:ABCDefGhijKlmnoPqrstUvwxyz" \
  -e TELEGRAM_CHAT_ID="987654321" \
  -e BOT_MOBILE_NUMBER="393501234567" \
  whatsapp-garbage-bot
```

### Variabili d'Ambiente Disponibili

| Variabile | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `LOG_LEVEL` | `DEBUG\|INFO\|WARNING\|ERROR` | `INFO` | Livello di dettaglio dei log |
| `TELEGRAM_TOKEN` | stringa | (vuoto) | Token bot Telegram (da @BotFather) |
| `TELEGRAM_CHAT_ID` | stringa | (vuoto) | Chat ID Telegram (da @RawDataBot) |
| `BOT_MOBILE_NUMBER` | stringa | (vuoto) | Numero WhatsApp del bot (prefisso int. senza +) |

### Alternativa: File options.json (Fallback)

Se non usi variabili d'ambiente, il bot legge da `/data/options.json`:

```json
{
  "log_level": "info",
  "telegram_token": "123456789:ABCDefGhijKlmnoPqrstUvwxyz",
  "telegram_chat_id": "987654321",
  "bot_mobile_number": "393501234567"
}
```

⚠️ **Nota:** Le variabili d'ambiente sovrascrivono il file options.json! Usa le env vars per maggiore sicurezza.

### Come Ottenere i Dati Telegram

1. **Token Bot Telegram:**
   - Apri Telegram e scrivi a [@BotFather](https://t.me/botfather)
   - Invia `/start` → `/newbot`
   - Dai un nome e username
   - Copia il token (es: `123456789:ABCDefGhijKlmnoPqrstUvwxyz`)

2. **Chat ID:**
   - Scrivi a [@RawDataBot](https://t.me/rawdatabot)
   - Invia un messaggio qualsiasi
   - Ti risponde con il tuo ID sotto `"id": XXXXX`

---

## 🚀 Step 5: Avvia il Bot

### Prima Esecuzione

```bash
python3 garbage_bot.py
```

Dovresti vedere:

```
⚙️ Logging configurato
⚡ Bot inizializzato
🔑 Attendendo QR code WhatsApp...
```

### Scansiona il QR Code

1. Apri **WhatsApp** sul tuo telefono
2. Vai a **Settings > Linked Devices**
3. Clicca **Link Device**
4. Usa la fotocamera per scansionare il **QR code** stampato nel terminale
5. Autorizza il dispositivo

```
✅ Connessione completata!
👤 Bot User: +39XXXXXXXXX
```

---

## ⚙️ Step 6: Test dei Comandi

### Invia un Messaggio di Test

Da qualsiasi chat WhatsApp:

```
/help
```

Dovresti ricevere la lista di comandi.

### Configura il Primo Gruppo

Copia il link del gruppo WhatsApp (da Share):
```
https://chat.whatsapp.com/xxxxx
```

Nel gruppo:
```
/config https://chat.whatsapp.com/xxxxx https://docs.google.com/spreadsheets/d/xxxxx
```

✅ Fatto!

---

## 🔄 Esecuzione Continua (Raspberry Pi)

Se vuoi che il bot rimanga sempre acceso su Raspberry Pi, usa **systemd**.

### Crea il Service File

```bash
sudo nano /etc/systemd/system/whatsapp_bot.service
```

Incolla:

```ini
[Unit]
Description=WhatsApp Garbage Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi  # Cambia se il tuo username è diverso
WorkingDirectory=/home/pi/whatsapp-garbage-bot  # Cambia il path
Environment="PATH=/home/pi/whatsapp-garbage-bot/venv/bin"
Environment="PYTHONUNBUFFERED=1"
# Le variabili di configurazione sono lette da /data/options.json
ExecStart=/home/pi/whatsapp-garbage-bot/venv/bin/python3 garbage_bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=whatsapp_bot

[Install]
WantedBy=multi-user.target
```

### Configurare le Variabili per systemd

Se stai usando systemd e vuoi configurare il bot, puoi:

**Opzione A: Usare variabili d'ambiente (Consigliato)**

Vedi la sezione "[Con Systemd](#con-systemd)" sopra per impostare le env vars direttamente nel service file.

**Opzione B: Usare file options.json**

Crea `/data/options.json` come descritto nel [Step 4b](#-step-4b-configurazione-variabili-del-bot):

```json
{
  "log_level": "info",
  "telegram_token": "123456789:ABCDefGhijKlmnoPqrstUvwxyz",
  "telegram_chat_id": "987654321",
  "bot_mobile_number": "393501234567"
}
```

Il bot leggerà automaticamente questo file al fallback (se le env vars non sono presenti).

Poi riavvia il servizio:
```bash
sudo systemctl restart whatsapp_bot
```

### Abilita il Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable whatsapp_bot
sudo systemctl start whatsapp_bot
```

### Verifica che Funzioni

```bash
sudo systemctl status whatsapp_bot

# Output atteso:
# ● whatsapp_bot.service - WhatsApp Garbage Bot
#    Loaded: loaded (/etc/systemd/system/whatsapp_bot.service; enabled)
#    Active: active (running)
```

### Visualizza i Log

```bash
# Log in tempo reale
sudo journalctl -u whatsapp_bot -f

# Ultimi 50 log
sudo journalctl -u whatsapp_bot -n 50

# Log di oggi
sudo journalctl -u whatsapp_bot --since today
```

### Riavvia il Service

```bash
sudo systemctl restart whatsapp_bot
```

---

## 🐳 Alternativa: Esecuzione con Docker

Se hai Docker installato:

### Build dell'Immagine

```bash
docker build -t whatsapp-garbage-bot .
```

### Crea una Cartella per i Dati

```bash
mkdir -p ~/whatsapp_bot_data
cp credentials.json ~/whatsapp_bot_data/
```

### Esegui il Container

**Opzione A: Con variabili d'ambiente (Consigliato)**

```bash
docker run -d \
  --name whatsapp_bot \
  -v ~/whatsapp_bot_data:/data \
  -e LOG_LEVEL="info" \
  -e TELEGRAM_TOKEN="123456789:ABCDefGhijKlmnoPqrstUvwxyz" \
  -e TELEGRAM_CHAT_ID="987654321" \
  -e BOT_MOBILE_NUMBER="393501234567" \
  whatsapp-garbage-bot
```

**Opzione B: Con file options.json (Fallback)**

Crea `/home/your_user/whatsapp_bot_data/options.json`:

```json
{
  "log_level": "info",
  "telegram_token": "123456789:ABCDefGhijKlmnoPqrstUvwxyz",
  "telegram_chat_id": "987654321",
  "bot_mobile_number": "393501234567"
}
```

Poi esegui:

```bash
docker run -d \
  --name whatsapp_bot \
  -v ~/whatsapp_bot_data:/data \
  whatsapp-garbage-bot
```

### Visualizza i Log

```bash
docker logs -f whatsapp_bot
```

### Arresta il Container

```bash
docker stop whatsapp_bot
docker rm whatsapp_bot
```

---

## 📁 Struttura Directory

Dopo l'installazione completa:

```
whatsapp-garbage-bot/
├── venv/                  # Virtual environment
├── garbage_bot.py         # Bot principale
├── requirements.txt
├── credentials.json       # Credenziali Google (segreto!)
├── SETUP_CALENDARIO.md    # Come configurare Sheets
├── README.md
├── Dockerfile            # Se vuoi usare Docker
└── (altri file)
```

**File Generati al Primo Avvio:**

```
/data/
├── garbage_bot.sqlite        # Dati Neonize (WhatsApp)
├── garbage_bot_config.sqlite # Configurazioni gruppi/sheet
├── credentials.json          # Credenziali Google
└── options.json             # (Opzionale) Configurazioni bot
```

---

## 🔐 Sicurezza

### ⚠️ Proteggi le Credenziali

```bash
# Rendi il file leggibile solo dall'utente
chmod 600 credentials.json

# Non caricare su GitHub!
# Aggiungi a .gitignore:
echo "credentials.json" >> .gitignore
echo "garbage_bot*.sqlite" >> .gitignore
```

### 🔑 Ruota le Credenziali

Se esponi accidentalmente le credenziali:

1. Vai a https://console.cloud.google.com/iam-admin/service-accounts
2. Trova il Service Account
3. Elimina la vecchia chiave JSON
4. Crea una nuova chiave JSON
5. Scarica il nuovo `credentials.json`
6. Aggiorna il file localmente

---

## 🧹 Manutenzione

### Aggiorna il Bot

```bash
cd whatsapp-garbage-bot
git pull origin main  # Se usi Git

# Riavvia il service
sudo systemctl restart whatsapp_bot
```

### Pulisci i Database (Reset Totale)

```bash
# Ferma il bot
sudo systemctl stop whatsapp_bot

# Elimina i database
rm ~/.garbage_bot/garbage_bot*.sqlite

# Riavvia
sudo systemctl start whatsapp_bot

# Il bot ricreerà i database vuoti
```

### Localizzazione Timezone

Se non sei in Europe/Rome, modifica il Service:

```bash
sudo nano /etc/systemd/system/whatsapp_bot.service

# Cerca la sezione [Service] e aggiungi:
Environment="TZ=Your/Timezone"

# Salva e ricarica:
sudo systemctl daemon-reload
sudo systemctl restart whatsapp_bot
```

Timezone comuni:
- `Europe/Rome` (default)
- `Europe/London`
- `Europe/Berlin`
- `America/New_York`
- `Asia/Tokyo`

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'neonize'"

```bash
# Verifica che sei nel virtual environment
which python3
# Output deve contenere "venv"

# Se no, attiva il venv
source venv/bin/activate

# Reinstalla le dipendenze
pip install -r requirements.txt
```

### "credentials.json not found"

```bash
# Verifica che il file esista nella corretta directory
ls -la credentials.json

# Se manca, scaricalo di nuovo da Google Cloud Console
# e posizionalo nella cartella del bot
```

### "Port already in use"

```bash
# Se il bot non si arresta correttamente e usa ancora una porta:
# Trova il processo
lsof -i :8000  # O la porta che usa

# Uccidi il processo
kill -9 <PID>
```

### "Permission denied" su systemd

```bash
# Assicurati che l'utente `pi` (o tuo username) 
# possieda la cartella del bot:
sudo chown -R pi:pi /home/pi/whatsapp-garbage-bot

# E la cartella dati:
sudo chown -R pi:pi ~/.garbage_bot
```

### Log di Debug

Per più informazioni sugli errori:

```bash
# Avvia il bot manualmente per vedere output dettagliato
python3 garbage_bot.py

# Se è in systemd:
sudo journalctl -u whatsapp_bot -n 100 --no-pager
```

### Problemi di Configurazione

**Problema: "Telegram non configurato" ma ho impostato telegram_token"**

```bash
# Verifica che il file /data/options.json sia presente e valido
cat /data/options.json

# Assicurati che il JSON sia formattato correttamente (senza virgole extra)
# Se corretto, riavvia il bot:
python3 garbage_bot.py

# O se usi systemd:
sudo systemctl restart whatsapp_bot
```

**Problema: log_level non cambia anche se impostato in options.json**

- Il file viene letto al startup
- Se lo modifichi dopo l'avvio, devi riavviare il bot
- Verifica il contenuto: `cat /data/options.json`

**Problema: "options.json not found" nei log**

- È normale! Il file è opzionale
- Se non lo crei, il bot usa i valori di default
- Se vuoi personalizzare, crea il file come descritto nel [Step 4b](#-step-4b-configurazione-variabili-del-bot)

---

## 📚 Link Utili

- [Python venv documentation](https://docs.python.org/3/tutorial/venv.html)
- [Systemd service docs](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Docker documentation](https://docs.docker.com/)
- [Neonize GitHub](https://github.com/Alfie-Lk/neonize)

---

## ✅ Checklist Finale

- [ ] Python 3.10+ installato
- [ ] Virtual environment creato e attivato
- [ ] Dipendenze installate (requirements.txt)
- [ ] Google Sheets API abilitata
- [ ] Service Account creato e credenziali salvate
- [ ] Sheet condiviso con service account
- [ ] Bot avviato e QR code scansionato
- [ ] Primo gruppo configurato con `/config`
- [ ] Comandi funzionano (`/help`)
- [ ] Service systemd configurato (opzionale)
- [ ] File `/data/options.json` configurato (opzionale ma consigliato per Telegram)

🎉 **Completato!** Il bot è pronto per funzionare 24/7.

---

## 📌 Configurazione Rapida di Riferimento

Se vuoi configurare il bot rapidamente, ecco il template `/data/options.json`:

```json
{
  "log_level": "info",
  "telegram_token": "YOUR_BOT_TOKEN_HERE",
  "telegram_chat_id": "YOUR_CHAT_ID_HERE",
  "bot_mobile_number": "393501234567"
}
```

Con questa configurazione riceverai:
- ✅ QR code su Telegram per il primo login
- ✅ Notifiche di errore istantanee
- ✅ Log controllabili dal file di configurazione
