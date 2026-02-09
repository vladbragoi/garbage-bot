# WhatsApp Garbage Bot - Home Assistant Add-on

Bot WhatsApp per gestione turni spazzatura e calendario con integrazione Google Sheets, ottimizzato per Home Assistant OS.

## Installazione in Home Assistant

### Prerequisiti
1. **Home Assistant OS** installato e in esecuzione
2. **Google Sheets API credentials** (file `credentials.json`)
3. **Numero WhatsApp** per il bot

### Configurazione

#### 1. Ottenere credentials.json da Google Cloud

1. Vai a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto
3. Abilita l'API **Google Sheets API**
4. Crea un **Service Account**:
   - Vai a "Service Accounts"
   - Crea nuovo account
   - Genera una chiave JSON
   - Scarica il file `credentials.json`

#### 2. Aggiungere l'Add-on a Home Assistant

**Opzione A: Repository Personalizzato (Consigliato)**

Se lo ospiti su GitHub:

1. Home Assistant → Settings → Add-ons → Create add-on repository
2. Aggiungi l'URL del tuo repository
3. Controlla la scheda "My repositories" per il nuovo add-on

**Opzione B: Installazione Manuale**

1. Accedi a Home Assistant via SSH
2. Naviga a: `/homeassistant/addons/`
3. Crea cartella: `whatsapp_garbage_bot`
4. Copia i file:
   - `Dockerfile`
   - `config.json`
   - `requirements.txt`
   - `run.sh`
   - `garbage_bot.py`
   - Tutti gli altri file Python

#### 3. Caricare credentials.json

**Prima di avviare il bot:**

1. Accedi a Home Assistant via SSH
2. Naviga a: `/data/` (oppure crea la cartella)
3. Copia il file `credentials.json` ottenuto da Google Cloud

Percorso finale: `/data/credentials.json`

#### 4. Avviare l'Add-on

1. Home Assistant → Settings → Add-ons → Whatsapp Garbage Bot
2. Clicca "Start"
3. Controlla i log per errori

```
[WhatsApp Bot] ✅ Ambiente pronto
[WhatsApp Bot] 🚀 Avvio bot...
```

## Struttura File

```
whatsapp_garbage_bot/
├── Dockerfile               # Configurazione Docker per HA
├── config.json             # Metadata add-on
├── run.sh                  # Script di avvio
├── requirements.txt        # Dipendenze Python
├── garbage_bot.py          # Bot principale
├── SETUP_CALENDARIO.md     # Documentazione calendario
└── calendar.gs             # Google Apps Script originale (reference)
```

## Configurazione del Bot

Dopo il primo avvio, il bot creerà due database SQLite in `/data/`:

- `garbage_bot.sqlite` - Dati chat WhatsApp Neonize
- `garbage_bot_config.sqlite` - Configurazioni gruppi/sheet

**Primo comando per configurare:**
```
/config <link_gruppo_wa> <link_google_sheet>
```

Esempio:
```
/config https://chat.whatsapp.com/xxxxx https://docs.google.com/spreadsheets/d/xxxxx/edit
```

## Path Importanti in HA

- `/data/` → Dati persistenti (database, credentials)
- `/config/` → Configurazioni Home Assistant (opzionale)
- `/app/` → Cartella applicazione nel container

## Upgrade

Se vuoi aggiornare il bot:

1. Home Assistant → Settings → Add-ons → Whatsapp Garbage Bot
2. Clicca "Stop" se in esecuzione
3. Aggiorna il codice nel repository
4. Clicca "Rebuild" (se ospitato su GitHub) o "Start"

## Troubleshooting

### "credentials.json not found"
```bash
# Verifica che il file esista in /data/
ls -la /data/credentials.json
```

### Errori di Google Sheets API
```bash
# Verifica che l'API sia abilitata in Google Cloud Console
# Verifica che le credenziali salvate siano valide
```

### Bot non risponde ai comandi
```bash
# Controlla i log in Home Assistant → Add-ons → Whatsapp Bot → Logs
# Verifica che il numero WhatsApp sia collegato al QR code
```

## Comandi Disponibili

- `/oggi` - Chi è di turno oggi
- `/prossimi` - Prossimi turni
- `/regole` - Regole e buone norme
- `/calendario` - Invia PDF calendario (utenti) / Rigeneran calendario (admin)
- `/config` - Configura gruppo/sheet (admin)
- `/config_check` - Lista configurazioni (admin)
- `/config_reset` - Rimuovi configurazione (admin)
- `/db_reset` - Ricrea database (admin)
- `/help` - Mostra questa lista

## Note Importanti

1. **Persistenza dati**: I database e credentials vengono salvati in `/data/` che è un volume persistente di HA
2. **Timezone**: Configurato automaticamente per Europe/Rome (modificabile in `run.sh`)
3. **Logging**: Tutti i log vanno a stdout (visibili in Home Assistant → Add-ons → Logs)
4. **Sicurezza**: `credentials.json` è sensibile - mantieni la privacy della cartella `/data/`

## License

MIT

## Support

Per bug o features, apri un issue nel repository.
