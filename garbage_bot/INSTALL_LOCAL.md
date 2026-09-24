# Installazione Locale e Sviluppo - Linux / Raspberry Pi

Questa guida illustra la configurazione del bot in ambiente locale o server Linux autonomo.

Nota: Questa modalita e destinata a test, sviluppo o esecuzione standalone. Per l'uso standard e consigliato l'add-on ufficiale per **Home Assistant OS** (vedi [INSTALL_HOMEASSISTANT.md](INSTALL_HOMEASSISTANT.md)).

---

## 1. Prerequisiti di Sistema

- Python 3.12 (o Python >= 3.10)
- Dipendenze C di sistema per la compilazione e rendering grafici:
  - `python3-venv`, `python3-dev`, `build-essential`
  - `libmagic1`, `libsqlite3-dev`
- File `credentials.json` rilasciato da Google Cloud Console per un Service Account con Google Sheets API v4 abilitata.
- Account e numero WhatsApp dedicato per il bot.

Installazione pacchetti di sistema su Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-dev build-essential libmagic1 libsqlite3-dev
```

---

## 2. Configurazione Ambiente Virtuale Python

Dalla cartella principale del progetto:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verifica la corretta installazione delle dipendenze:
```bash
python3 -c "import neonize; print('Neonize caricato con successo')"
```

---

## 3. Gestione Credenziali e File di Configurazione

1. Posiziona il file `credentials.json` nella cartella di lavoro:
   ```bash
   cp /percorso/del/tuo/credentials.json ./credentials.json
   chmod 600 credentials.json
   ```

2. Le variabili di configurazione possono essere passate come variabili d'ambiente (scelta consigliata):
   ```bash
   export LOG_LEVEL="info"
   export TELEGRAM_TOKEN="123456789:ABCDefGhijKlmnoPqrstUvwxyz"
   export TELEGRAM_CHAT_ID="987654321"
   export BOT_MOBILE_NUMBER="393501234567"
   ```

3. In alternativa, e possibile creare un file `options.json` nella directory dati del bot (es. `/data/options.json`).

---

## 4. Esecuzione Manuale

```bash
source venv/bin/activate
cd garbage_bot
python3 garbage_bot.py
```

All'avvio, il bot generera il QR code WhatsApp:
- Se il bot Telegram e configurato (`TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`), l'immagine QR verra recapitata direttamente su Telegram.
- In alternativa, inquadra la stringa QR catturata dallo sniffer da WhatsApp > Dispositivi collegati.

---

## 5. Esecuzione con Servizio Systemd

Per garantire l'esecuzione continua in background e il riavvio automatico:

1. Crea o adatta il file `/etc/systemd/system/garbage_bot.service`:

```ini
[Unit]
Description=WhatsApp Garbage Bot Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=jarvis
WorkingDirectory=/home/jarvis/whatsapp_bot/garbage_bot
Environment="PATH=/home/jarvis/whatsapp_bot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="TZ=Europe/Rome"
Environment="LOG_LEVEL=info"
# Environment="TELEGRAM_TOKEN=TUO_TOKEN"
# Environment="TELEGRAM_CHAT_ID=TUO_CHAT_ID"
# Environment="BOT_MOBILE_NUMBER=393501234567"
ExecStart=/home/jarvis/whatsapp_bot/venv/bin/python3 garbage_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Ricarica systemd e attiva il servizio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable garbage_bot
sudo systemctl start garbage_bot
```

3. Controlla lo stato e i log:
```bash
sudo systemctl status garbage_bot
journalctl -u garbage_bot -f
```

---

## 6. Risoluzione Errori

### Client outdated (405) connect failure
- **Messaggio di errore:** `ERROR - Client outdated (405) connect failure (client version: 2.3000.1039406452)`
- **Causa:** La versione del protocollo client non e piu accettata dai server WhatsApp.
- **Risoluzione:** L'errore richiede un aggiornamento della libreria. Eseguire `pip install --upgrade neonize`. Non cancellare i database `.sqlite`: una volta aggiornata la libreria, la sessione si ricollega senza richiedere nuova autenticazione.

### ModuleNotFoundError: No module named 'neonize'
- Assicurarsi che il virtual environment sia attivo (`source venv/bin/activate`) e che le dipendenze siano state installate da `requirements.txt`.

---

## Guide di Riferimento

- [Guida Installazione Home Assistant OS](INSTALL_HOMEASSISTANT.md)
- [Guida Configurazione Google Sheets](SETUP_CALENDARIO.md)
- [README Add-on](README.md)
- [README Principale](../README.md)
