# WhatsApp Garbage Bot - Home Assistant Add-on Repository

Soluzione per la gestione automatica dei turni spazzatura via WhatsApp e Google Sheets.

Repository ufficiale di custom add-ons per [Home Assistant](https://www.home-assistant.io/). Questo add-on e ottimizzato e sviluppato primariamente per **Home Assistant OS**.

## Add-on Disponibile

### WhatsApp Garbage Bot
Bot WhatsApp per gestione automatica turni spazzatura e calendario condominiale con integrazione Google Sheets.

**Caratteristiche:**
- Gestione automatica calendario turni su Google Sheets
- Comandi WhatsApp per consultazione e amministrazione
- Integrazione completa con Google Sheets API v4
- Promemoria giornalieri via WhatsApp per il condomino di turno
- Generazione automatica e manuale di PDF del calendario
- Notifica di ciclo e report PDF inviati via Telegram
- Gestione automatica della rotazione e dei cicli di turnazione
- Configurazione avanzata tramite interfaccia Home Assistant

Guida di riferimento: [INSTALL_HOMEASSISTANT.md](file:///home/jarvis/whatsapp_bot/garbage_bot/INSTALL_HOMEASSISTANT.md)

## Comandi Disponibili

### Comandi Generali (Gruppo)
- `/oggi` - Mostra chi e di turno oggi
- `/prossimi` - Visualizza i prossimi 10 turni
- `/regole` - Legge il regolamento rifiuti dal foglio Google
- `/calendario` - Invia il PDF del calendario aggiornato
- `/info` (o `/help`, `/comandi`) - Mostra l'elenco completo dei comandi

### Comandi Amministratore (Gruppo)
- `/attiva <link_sheet>` - Attiva e collega il bot nel gruppo WhatsApp associandolo al foglio Google Sheets
- `/disattiva` - Disattiva il bot e rimuove la configurazione per il gruppo corrente
- `/genera` - Corregge il ciclo corrente, azzera i turni futuri e riavvia dal prossimo lunedi
- `/genera nuovi` - Crea una nuova turnazione partendo dalla data di fine del ciclo attuale

### Comandi Superadmin (Chat Privata col Bot)
- `/config <link_gruppo> <link_sheet>` - Configura un gruppo da remoto tramite link d'invito
- `/config_check` - Elenca tutte le configurazioni attive salvate nel database
- `/config_reset <numero>` - Rimuove una configurazione tramite indice numerico
- `/db_reset` - Cancella e ricrea la tabella di configurazione nel database

## Installazione su Home Assistant OS

### Prerequisiti
- Home Assistant OS installato
- File `credentials.json` ottenuto da Google Cloud Console (Service Account)

### Passaggi di Installazione

1. Apri Home Assistant e accedi a **Impostazioni > Componenti aggiuntivi > Raccolta di componenti aggiuntivi**
2. Clicca sui tre puntini in alto a destra, seleziona **Repository** e aggiungi:
   `https://github.com/vladbragoi/garbage-bot`
3. Cerca **GarbageBot WhatsApp** nella raccolta e clicca **Installa**
4. Carica il file `credentials.json` nella cartella `/config/` di Home Assistant (usando Studio Code Server, File Editor o condivisione Samba)
5. Configura i parametri opzionali (token Telegram, Chat ID, numero del bot) nella scheda **Configurazione** dell'add-on
6. Avvia l'add-on e consulta i log per scansionare il QR code di WhatsApp (o riceverlo direttamente su Telegram se configurato)

Per la procedura dettagliata passo dopo passo: [INSTALL_HOMEASSISTANT.md](file:///home/jarvis/whatsapp_bot/garbage_bot/INSTALL_HOMEASSISTANT.md).

## Struttura Google Sheets Richiesta

- **Foglio "Impostazioni"**: lista dei condomini (colonna A: Nome, colonna B: Telefono).
- **Foglio "Calendario"**: turni generati automaticamente dal bot (Data, Bidone, Condomino, Telefono).
- **Foglio "NuovoCalendario"**: bozza per il ciclo successivo generata quando mancano meno di 30 giorni.
- **Foglio "Regole"** (opzionale): testo delle norme condominiali restituito da `/regole`.

Formato data utilizzato: `DD/MM/YYYY`.

Dettagli completi sullo schema del foglio: [SETUP_CALENDARIO.md](file:///home/jarvis/whatsapp_bot/garbage_bot/SETUP_CALENDARIO.md).

## Risoluzione Problemi: Errore 405 (Client Outdated)

Se nei log compare l'errore:
`ERROR - Client outdated (405) connect failure (client version: 2.3000.1039406452)`

**Causa:**
I server WhatsApp hanno revocato il supporto per la versione web del client segnalata dalla libreria sottostante (`whatsmeow`/`neonize`).

**Soluzione:**
1. L'errore richiede un aggiornamento della libreria di connessione o dell'add-on di Home Assistant.
2. In ambiente Home Assistant OS, aggiornare l'add-on all'ultima versione disponibile per ottenere il client aggiornato compatibile con i requisiti correnti di WhatsApp.
3. In ambiente locale, aggiornare le dipendenze con `pip install --upgrade neonize`.
4. Riavviare l'applicazione. La sessione memorizzata nel database non viene distrutta e si riconnettera senza richiedere una nuova scansione QR.

## Indice Documentazione

| Documento | Descrizione |
|---|---|
| [INSTALL_HOMEASSISTANT.md](file:///home/jarvis/whatsapp_bot/garbage_bot/INSTALL_HOMEASSISTANT.md) | Guida principale di installazione e configurazione per Home Assistant OS |
| [SETUP_CALENDARIO.md](file:///home/jarvis/whatsapp_bot/garbage_bot/SETUP_CALENDARIO.md) | Struttura e configurazione del foglio Google Sheets |
| [garbage_bot/README.md](file:///home/jarvis/whatsapp_bot/garbage_bot/README.md) | Dettaglio tecnico dei componenti e comandi del bot |
| [INSTALL_LOCAL.md](file:///home/jarvis/whatsapp_bot/garbage_bot/INSTALL_LOCAL.md) | Guida alternativa per test e sviluppo locale su Linux/Raspberry Pi |

## Architettura

- **Ambiente primario:** Home Assistant Container (Docker, base Python 3.12-slim)
- **Framework di connessione:** Neonize (Go bridge whatsmeow)
- **Persistenza dati:** SQLite (`/data/garbage_bot.sqlite` e `/data/garbage_bot_config.sqlite`)
- **API Esterne:** Google Sheets API v4 (gspread), Telegram Bot API (alert e documenti PDF)

## Licenza

MIT License.