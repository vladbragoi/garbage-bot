# WhatsApp Garbage Bot - Guida Installazione Home Assistant Add-on

Bot WhatsApp per la gestione automatica dei turni spazzatura e del calendario condominiale.

Questa guida descrive l'installazione e la configurazione su **Home Assistant OS**, che costituisce l'ambiente di runtime principale e supportato dell'applicazione.

---

## Installazione Passo dopo Passo

### Prerequisiti

- Home Assistant OS funzionante (versione 2024.1 o successiva).
- Accesso alla cartella di configurazione di Home Assistant tramite File Editor, Studio Code Server o integrazione Samba.
- Account Google Cloud Console con Service Account abilitato su Google Sheets API v4.
- Numero WhatsApp dedicato per il bot (o numero secondario abilitato su WhatsApp Web).

---

### Step 1: Creazione Credenziali Google Cloud (credentials.json)

1. Accedi a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un nuovo progetto (es. `GarbageBot`).
3. Abilita l'API Google Sheets:
   - Vai su **APIs & Services > Library**.
   - Cerca **Google Sheets API** e clicca su **ENABLE**.
4. Crea un Service Account:
   - Vai su **APIs & Services > Credentials**.
   - Clicca **Create Credentials > Service Account**.
   - Assegna un nome (es. `garbage-bot-service`) e clicca **Create and Continue**.
   - Salta i ruoli opzionali e termina con **Done**.
5. Genera la chiave privata in formato JSON:
   - Clicca sul Service Account appena creato.
   - Apri la scheda **Keys** (Chiavi).
   - Clicca **Add Key > Create new key > JSON**.
   - Il browser scarichera un file JSON: rinominalo esattamente `credentials.json`.
6. Condividi il Google Sheet:
   - Apri il file `credentials.json` con un editor di testo e copia l'indirizzo `client_email` (es. `garbage-bot-service@progetto.iam.gserviceaccount.com`).
   - Apri il tuo foglio Google Sheet del condominio, clicca su **Condividi**, incolla l'email del service account e assegna i permessi di **Editor**.
   - Per la configurazione e la struttura richiesta del foglio, consulta [SETUP_CALENDARIO.md](SETUP_CALENDARIO.md).

---

### Step 2: Caricamento credentials.json in Home Assistant

In Home Assistant OS, i file dell'utente risiedono nella directory `/config/` (la cartella di configurazione principale di Home Assistant, accessibile da File Editor o Samba).

1. Apri **File Editor** o **Studio Code Server** in Home Assistant.
2. Posizionati nella radice della cartella `/config/`.
3. Carica il file `credentials.json`.
   Percorso risultante: `/config/credentials.json`.
4. All'avvio dell'add-on, lo script di avvio (`run.sh`) copiera automaticamente questo file nella partizione sicura e persistente `/data/credentials.json`, applicando i permessi restrittivi `600`.

---

### Step 3: Installazione Add-on in Home Assistant

[![Open your Home Assistant instance and show the add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvladbragoi%2Fgarbage-bot)

1. Clicca sul pulsante sopra per aggiungere direttamente il repository alla tua istanza Home Assistant, oppure vai su **Impostazioni > Componenti aggiuntivi > Raccolta di componenti aggiuntivi**.
2. Clicca sui tre puntini in alto a destra e seleziona **Repository**.
3. Inserisci l'URL del repository:
   `https://github.com/vladbragoi/garbage-bot`
4. Clicca **Aggiungi** e poi **Chiudi**.
5. Ricarica la pagina e cerca **GarbageBot WhatsApp**.
6. Clicca **Installa**.

---

### Step 4: Configurazione Opzioni Add-on

Nella scheda **Configurazione** dell'add-on in Home Assistant puoi personalizzare:

- `log_level`: Livello di dettaglio dei log (`debug`, `info`, `warning`, `error`). Default: `info`.
- `telegram_token`: Token del bot Telegram fornito da @BotFather (opzionale ma consigliato per ricevere QR code e alert).
- `telegram_chat_id`: ID numerico della chat Telegram fornito da @RawDataBot.
- `bot_mobile_number`: Numero di telefono associato al bot WhatsApp (formato internazionale senza il prefisso +, es. `393501234567`).

Salva le modifiche.

---

### Step 5: Primo Avvio e Associazione WhatsApp

1. Avvia l'add-on dalla scheda **Info**.
2. Apri la scheda **Registri** (Logs) dell'add-on:
   - Se hai configurato Telegram, riceverai l'immagine del QR code direttamente nella tua chat Telegram.
   - In alternativa, lo sniffer QR del bot stampa il payload nei registri di Home Assistant.
3. Apri **WhatsApp** sullo smartphone:
   - Vai su **Impostazioni > Dispositivi collegati > Collega un dispositivo**.
   - Inquadra il QR code ricevuto.
4. Una volta associato, nei registri comparira la conferma di connessione e il JID del bot.

---

### Step 6: Attivazione del Gruppo Condominiale

1. Aggiungi il numero WhatsApp del bot all'interno del gruppo WhatsApp del condominio.
2. Un amministratore del gruppo deve inviare nel gruppo il comando:
   `/attiva <link_del_google_sheet>`
   Esempio:
   `/attiva https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit`
3. Il bot salvera la configurazione nel database persistente (`/data/garbage_bot_config.sqlite`) e confermera l'attivazione.

---

## Elenco Comandi Disponibili

### Comandi Utente (all'interno del gruppo)
- `/oggi`: Mostra chi e di turno oggi e quale bidone esporre.
- `/prossimi`: Mostra i prossimi 10 turni in calendario.
- `/regole`: Restituisce il contenuto del foglio "Regole".
- `/calendario`: Genera e invia il documento PDF del calendario aggiornato nel gruppo.
- `/info` (o `/help`, `/comandi`): Mostra la guida a tutti i comandi.

### Comandi Amministratore (all'interno del gruppo)
- `/attiva <link_sheet>`: Collega il foglio Google al gruppo corrente.
- `/disattiva`: Rimuove il gruppo dal database del bot.
- `/genera`: Resetta i turni futuri a partire dal lunedi successivo ripartendo dal primo condomino.
- `/genera nuovi`: Genera una nuova rotazione (NuovoCalendario) partendo dalla data di fine del ciclo attuale.

### Comandi Superadmin (in chat privata col bot)
- `/config <link_gruppo> <link_sheet>`: Collega un gruppo da remoto tramite link di invito.
- `/config_check`: Mostra tutte le configurazioni attive salvate.
- `/config_reset <numero>`: Rimuove la configurazione con l'indice specificato.
- `/db_reset`: Ricrea le tabelle del database di configurazione.

---

## Architettura File e Mappature Cartelle in Home Assistant

| Percorso | Tipo di Mount | Descrizione |
|---|---|---|
| `/config` | Host (sola lettura `:ro`) | Cartella condivisa di Home Assistant. Il bot legge `credentials.json` da qui. |
| `/data` | Host (lettura/scrittura `:rw`) | Storage persistente isolato dell'add-on. Contiene i database e le credenziali protette. |
| `/data/garbage_bot.sqlite` | File SQLite | Sessione e chiavi crittografiche WhatsApp gestite da Neonize/whatsmeow. |
| `/data/garbage_bot_config.sqlite` | File SQLite | Mappatura gruppi, URL Google Sheets e metadati. |
| `/data/credentials.json` | File JSON | Copia sicura della chiave di servizio Google (permessi `600`). |
| `/data/options.json` | File JSON | Configurazioni generate automaticamente da Home Assistant UI. |

---

## Risoluzione Problemi (Troubleshooting)

### Errore 405: "Client outdated (405) connect failure"
- **Messaggio di errore:**
  `ERROR - Client outdated (405) connect failure (client version: 2.3000.1039406452)`
- **Causa:** WhatsApp dismette periodicamente il supporto per le versioni obsolete del protocollo WhatsApp Web. Se la versione inviata dalla libreria sottostante e deprecata dai server WhatsApp, la connessione fallisce con errore 405.
- **Risoluzione:**
  1. L'errore richiede un aggiornamento dell'add-on di Home Assistant (o della libreria di connessione).
  2. Aggiorna l'add-on di Home Assistant all'ultima versione disponibile per ottenere il client compatibile con i requisiti attuali dei server WhatsApp.
  3. Il database di sessione (`/data/garbage_bot.sqlite`) viene preservato, garantendo la riconnessione automatica senza dover scansionare nuovamente il codice QR.

### Errore: "credentials.json non trovato"
- Verifica di aver caricato il file in `/config/credentials.json` (la directory principale di Home Assistant accessibile da File Editor o Samba).
- Non caricare il file in sottocartelle; il nome deve essere rigorosamente `credentials.json`.
- Riavvia l'add-on dopo il caricamento.

### Errore: "API Error 403 / Permessi Google Sheets"
- Assicurati di aver aperto il Google Sheet e condiviso il file con l'indirizzo email presente nel campo `client_email` del file `credentials.json`, concedendo il ruolo di **Editor**.

### Il bot non risponde nel gruppo
1. Controlla la sezione **Registri** dell'add-on per verificare che la connessione sia attiva.
2. Verifica che il gruppo sia stato attivato con il comando `/attiva <link_sheet>`.
3. Assicurati che il bot non sia stato espulso dal gruppo o limitato nelle impostazioni di gruppo di WhatsApp.

---

## Guide di Riferimento

- [Guida Configurazione Google Sheets](SETUP_CALENDARIO.md)
- [Guida Esecuzione e Test Locale](INSTALL_LOCAL.md)
- [README Add-on](README.md)
- [README Principale](../README.md)

---

## Licenza

MIT License.
