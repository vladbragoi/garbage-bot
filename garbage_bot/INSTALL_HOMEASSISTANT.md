# 🤖 WhatsApp Garbage Bot - Home Assistant Add-on

**Bot WhatsApp intelligente per gestione automatica turni spazzatura e calendario condominiale**

Ottimizzato e sviluppato per **Home Assistant OS** come runtime principale. Gestisce automaticamente i turni, genera calendari PDF e mantiene il condominio organizzato via WhatsApp.

---

## ⚡ Installazione Rapida

### Aggiungi il Repository

[![Open your Home Assistant instance and show the add-on store.](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/)

1. Clicca il badge sopra
2. Vai su **Repositories** → **Create Repository**
3. Incolla: `https://github.com/vladbragoi/garbage-bot`
4. Aggiungi il repository
5. Torna alla Home e cerca **WhatsApp Garbage Bot**
6. Clicca **Install**

---

## 📋 Installazione Passo dopo Passo

### Prerequisiti

- ✅ **Home Assistant OS** installato e in esecuzione (versione 2024.1+)
- ✅ **Accesso SSH** o **File Editor** addon per caricare i file
- ✅ **Google Cloud Console** account con credenziali JSON per Sheets API
- ✅ **Numero WhatsApp** dedicato per il bot (o numero personale)

### Step 1️⃣ - Ottenere credentials.json da Google Cloud

**Tempo stimato: 5-10 minuti**

1. Vai a [Google Cloud Console](https://console.cloud.google.com/)
2. **Crea un nuovo progetto**:
   - Clicca il menu a tendina in alto
   - Clicca "NEW PROJECT"
   - Dai un nome (es. `GarbageBot`)
   - Crea il progetto

3. **Abilita l'API Google Sheets**:
   - Vai a **APIs & Services** → **Library**
   - Cerca "Google Sheets API"
   - Clicca su risultato
   - Clicca **ENABLE**

4. **Crea un Service Account**:
   - Vai a **APIs & Services** → **Credentials**
   - Clicca "Create Credentials" → **Service Account**
   - Compila: Nome = `GarbageBot`
   - Clicca **Create and Continue** (salta i ruoli)
   - Finalizza con **Done**

5. **Genera la chiave JSON**:
   - Vai a **APIs & Services** → **Service Accounts**
   - Clicca su `GarbageBot`
   - Tab **Keys**
   - **Create key** → **JSON**
   - Scarica automaticamente `credentials.json`

### Step 2️⃣ - Caricare credentials.json in Home Assistant

**Prima di installare l'add-on:**

1. Apri **Settings** → **System** → **File Editor** (se non l'hai, installa l'add-on)
2. Clicca l'icona cartella in alto a sinistra
3. Naviga a `/data/`
4. Clicca il menu (tre punti) → **Upload file**
5. Seleziona il file `credentials.json` che hai scaricato

**Percorso finale:** `/data/credentials.json` ✅

### Step 3️⃣ - Installare l'Add-on

1. Home Assistant → **Settings** → **Add-ons** → **Add-on Store**
2. Clicca su **Repositories** (in fondo)
3. Clicca **Create Repository**
4. Incolla: `https://github.com/vladbragoi/garbage-bot`
5. Clicca **Create**
6. Torna indietro, cerca **WhatsApp Garbage Bot**
7. Clicca **Install**
8. Una volta installato, clicca **Start**

### Step 4️⃣ - Primo Avvio e Scansione QR

1. Clicca **Logs** per vedere l'output
2. Se tutto è OK vedrai:
   ```
   ⚙️ Log level impostato su: INFO
   ✅ Sniffer QR agganciato
   🔌 Tentativo di connessione a WhatsApp...
   ```

3. Apri **Telegram** e troverai il QR Code
4. Apri **WhatsApp** sul tuo telefono → **Settings** → **Linked Devices** → **Link Device**
5. Scansiona il QR che hai ricevuto da Telegram
6. Autorizza il dispositivo

7. Tornerai ai log e vedrai:
   ```
   ✅ Connessione completata!
   👤 Bot User: +39XXXXXXXXX
   ```

### Step 5️⃣ - Configurare il Primo Gruppo

1. Apri un gruppo WhatsApp
2. Invia il comando:
   ```
   /config <link_gruppo> <link_sheet>
   ```

**Dove trovare i link:**

- **Link Gruppo**: Nel gruppo, clicca sui tre puntini → **Condividi gruppo** → copia il link (`https://chat.whatsapp.com/...`)
- **Link Sheet**: Apri il Google Sheet, clicca il pulsante **Share** in alto destra, copia l'URL

**Esempio completo:**
```
/config https://chat.whatsapp.com/ABC123xyz https://docs.google.com/spreadsheets/d/1qwerty-ASDFGHJKL/edit?usp=sharing
```

3. Se tutto va bene:
   ```
   ✅ Bot attivato con successo per il gruppo: Condominio XYZ
   ```

---

## 📊 Database e File

Dopo il primo avvio, il bot creerà in `/data/`:

| File | Descrizione |
|------|-------------|
| `garbage_bot.sqlite` | Dati persistenti WhatsApp (chat/config interna) |
| `garbage_bot_config.sqlite` | Configurazioni gruppi e link ai Google Sheets |
| `credentials.json` | Credenziali Google Cloud (segreto, non condividere!) |
| `options.json` | (Auto-generato) Opzioni add-on |

⚠️ **Attenzione:** Mantieni privata la cartella `/data/`. Se `credentials.json` viene compromesso, rigenera un nuovo Service Account.

## 🛠️ Configurazione Opzionale in Home Assistant

### Notifiche di Errore su Telegram

Il bot può inviare automaticamente notifiche su Telegram se configurato:

1. Crea un bot Telegram (parla con [@BotFather](https://t.me/botfather)):
   - Invia `/start`
   - Invia `/newbot`
   - Dai un nome e uno username
   - Copia il token (es. `123456:ABC-DEF123456789`)

2. Ottieni il tuo Chat ID:
   - Invia un messaggio a [@RawDataBot](https://t.me/rawdatabot)
   - Copia il valore `"chat":{"id": XXXXX}`

3. In Homes Assistant, vai all'add-on → **Settings** e compila:
   - `telegram_token`: Il token di BotFather
   - `telegram_chat_id`: Il tuo Chat ID

4. Riavvia l'add-on

Ora riceverai i QR code di login e notifiche di errore su Telegram!

---

## 📋 Comandi Disponibili

### Comandi Generali (Gruppo)
- **`/oggi`** - Chi è di turno oggi
- **`/prossimi`** - Prossimi 10 turni
- **`/regole`** - Regole e regolamento
- **`/calendario`** - Scarica PDF calendario
- **`/help`** - Lista di tutti i comandi

### Comandi Amministratore (Gruppo)
- **`/attiva <link_sheet>`** - Attiva il bot nel gruppo
- **`/disattiva`** - Disattiva il bot nel gruppo
- **`/genera`** - Corregge il ciclo corrente
- **`/genera nuovi`** - Crea nuovo ciclo

### Comandi Superadmin (Chat Privata)
- **`/config <link_gruppo> <link_sheet>`** - Configura gruppo
- **`/config_check`** - Lista configurazioni
- **`/config_reset <numero>`** - Rimuove configurazione
- **`/db_reset`** - Ricrea database

---

## 📁 Path Importanti in Home Assistant

| Path | Contenuto |
|------|----------|
| `/data/` | **Dati persistenti**: database SQLite, credentials.json, configurazioni |
| `/data/garbage_bot.sqlite` | Database WhatsApp (Neonize) |
| `/data/garbage_bot_config.sqlite` | Database configurazioni gruppi/sheet |
| `/data/credentials.json` | Credenziali Google Cloud (SEGRETO!) |
| `/app/` | Cartella applicazione (dentro container) |
| `Home Assistant → Settings → Add-ons → Logs` | Output del bot in tempo reale |

---

## 🔄 Upgrade e Manutenzione

### Aggiornare l'Add-on

1. Aspetta che sia disponibile un aggiornamento di GarbageBot
2. Home Assistant → **Settings** → **Add-ons** → **WhatsApp Garbage Bot**
3. Se il tasto è disponibile, clicca **Update**
4. L'add-on si riavvierà automaticamente

### Riavviare l'Add-on

- Clicca il pulsante **Restart** nella pagina dell'add-on
- Oppure clicca **Stop**, aspetta 5 secondi, poi **Start**

### Reset Completo (Cancella tutti i dati)

⚠️ **Attenzione:** Questa azione è irreversibile!

```bash
# Via SSH:
rm /data/garbage_bot*.sqlite

# Il bot ricrea automaticamente i database al prossimo avvio
```

---

## 🐛 Troubleshooting

### Problema: "Cannot connect to WhatsApp"
**Soluzione:**
- Verifica di aver scansionato il QR code correttamente
- Controlla che il numero WhatsApp sia online e connesso
- Se il QR non appare, riavvia l'add-on

### Problema: "credentials.json not found"
**Soluzione:**
1. Verifica che il file sia in `/data/credentials.json`
2. Se manca, caricalo tramite **File Editor**:
   - Settings → System → File Editor
   - Naviga a `/data/`
   - Upload `credentials.json`

### Problema: "API Error 403: Invalid credentials"
**Soluzione:**
- Il Service Account non ha permessi sul Google Sheet
- Apri lo Sheet, clicca **Share**
- Condividi con l'email del Service Account (email nel `credentials.json`)
- Dai permessi di **Editor**

### Problema: "No module named 'neonize'"
**Soluzione:**
- L'image Docker non è stata compilata correttamente
- Clicca **Rebuild** nella pagina dell'add-on
- Oppure rimuovi e reinstalla l'add-on

### Problema: Bot non risponde ai comandi
**Soluzione:**
1. Controlla i **Logs** dell'add-on
2. Verificà che il bot sia connesso (cerca `⚡ Bot Connesso!` nei log)
3. Assicurati che il gruppo sia configurato con `/config <link_sheet>`
4. Prova con un semplice `/help`

### Problema: "A sheet with the name 'Calendario' already exists"
**Soluzione:**
- Il bot ha rilevato un conflitto di nomi nei fogli
- Questo è stato risolto negli ultimi aggiornamenti
- Rinomina i fogli errati in "Cestino" e lascia che il bot ne crei uno nuovo
- Se persiste, clicca **Rebuild** dell'add-on

---

## 📞 Support e Debugging

### Abilitare Debug Logging

1. Home Assistant → **Settings** → **Add-ons** → **WhatsApp Garbage Bot**
2. Clicca **Settings**
3. Imposta `log_level` a `debug`
4. Riavvia l'add-on
5. I log dettagliati appariranno nella sezione **Logs**

### Raccogliere Informazioni per il Support

Se hai problemi, raccogli queste info:
1. **Output dei log** (ne ultimi 50 righe)
2. **Home Assistant version** (Settings → About)
3. **Add-on version** (nella pagina dell'add-on)
4. **Descrizione del problema** (cosa succede esattamente?)

Apri un issue nel [repository GitHub](https://github.com/vladbragoi/garbage-bot/issues)

---

## 💡 Tips & Tricks

### Backup dei Database
```bash
# Via SSH:
cp -r /data/garbage_bot*.sqlite /backup/
```

### Monitorare il Bot in Real-Time
- Apri Home Assistant
- Settings → Add-ons → **WhatsApp Garbage Bot** → **Logs**
- Attendi i log in tempo reale (non refreshare manualmente)

### Invio Errori su Telegram
Se configuri Telegram (vedi sopra), riceverai istantaneamente gli errori.

Utile per:
- Sessione scaduta WhatsApp
- Problemi API Google Sheets
- Errori di configurazione

---

## 📚 Documentazione Correlata

- [SETUP_CALENDARIO.md](SETUP_CALENDARIO.md) - Come strutturare il Google Sheet
- [README.md](README.md) - Feature e comandi disponibili
- [INSTALL_LOCAL.md](INSTALL_LOCAL.md) - Installazione alternativa per Linux

---

## 📄 Licenza

MIT License - Libero da usare nel tuo ambiente Home Assistant

## 🤝 Support

Domande o problemi? Apri un [issue](https://github.com/vladbragoi/garbage-bot/issues) nel repository! 🎉
