# WhatsApp Garbage Bot

Bot WhatsApp per la gestione automatica di turni spazzatura e calendario con integrazione Google Sheets.

Monitora le scadenze dei turni, genera cicli e PDF automaticamente e gestisce i promemoria del condominio via WhatsApp e Telegram.

L'ambiente di esecuzione primario e consigliato e **Home Assistant OS** come add-on nativo. E supportata anche una modalita alternativa per test e sviluppo locale su Linux/Raspberry Pi.

---

## Caratteristiche Principali

- **Ottimizzato per Home Assistant**: Funziona come add-on nativo con container Docker basato su Debian (Python 3.12).
- **Calendario intelligente**: Monitoraggio orario con generazione automatica del nuovo ciclo a 30 giorni dalla scadenza.
- **Comandi WhatsApp**: Consultazione rapida dei turni correnti e futuri all'interno dei gruppi.
- **Promemoria giornalieri**: Notifica ogni mattina alle 09:00 per il condomino di turno.
- **Google Sheets integrato**: Sincronizzazione con Google Sheets API v4 tramite Service Account.
- **Notifiche Telegram**: Invio del QR code di associazione al primo avvio, ricezione di alert per errori critici e consegna del PDF del nuovo ciclo generato.

---

## Comandi Disponibili

### Comandi per Tutti (Gruppo)
```text
/oggi              Chi e di turno oggi
/prossimi          Prossimi 10 turni in programma
/regole            Regolamento rifiuti condominiale
/calendario        Invia il PDF del calendario turni attuale
/help (o /info)    Elenco completo dei comandi
```

### Comandi Amministratore (Gruppo)
```text
/attiva <link_sheet>  Collega e attiva il bot nel gruppo con il foglio Google
/disattiva            Disattiva il bot e rimuove la configurazione del gruppo
/genera               Corregge il ciclo corrente troncando i turni futuri e riavviando da zero
/genera nuovi         Crea un nuovo ciclo (NuovoCalendario) partendo dalla fine del ciclo attuale
```

### Comandi Superadmin (Chat Privata col Bot)
```text
/config <link_grp> <link_sheet>  Collega un gruppo da remoto tramite link di invito
/config_check                    Mostra le configurazioni attive salvate
/config_reset <numero>           Rimuove una configurazione specifica
/db_reset                        Ricrea le tabelle del database di configurazione
```

---

## Quick Start su Home Assistant OS

1. **Configura Google Sheets**:
   Prepara il foglio con la struttura indicata in [SETUP_CALENDARIO.md](SETUP_CALENDARIO.md) e scarica `credentials.json` dalla Google Cloud Console.

2. **Copia credentials.json**:
   Posiziona il file `credentials.json` nella cartella `/config/` principale di Home Assistant (usando File Editor, Studio Code Server o Samba). All'avvio, `run.sh` lo trasferira automaticamente in `/data/credentials.json`.

3. **Installa l'Add-on**:
   Aggiungi il repository `https://github.com/vladbragoi/garbage-bot` nella Raccolta Add-on di Home Assistant e installa **GarbageBot WhatsApp**.

4. **Avvia e Associa WhatsApp**:
   Avvia l'add-on. Riceverai il QR code nei log dell'add-on oppure su Telegram (se configurato). Inquadra il QR da WhatsApp (Dispositivi collegati).

5. **Attiva il Gruppo**:
   Invia nel gruppo del condominio il comando:
   `/attiva https://docs.google.com/spreadsheets/d/TUO_FOGLIO_ID/edit`

---

## Architettura e Storage in Home Assistant

Home Assistant Supervisor mappa due directory all'interno del container Docker:
- `/config`: Directory di configurazione di Home Assistant (montata in sola lettura `:ro`). Usata per la consegna sicura del file `credentials.json`.
- `/data`: Directory persistente isolata per l'add-on (montata in lettura e scrittura `:rw`). Contiene:
  - `credentials.json`: Chiave di accesso Google Service Account (permessi `600`).
  - `garbage_bot.sqlite`: Sessione WhatsApp gestita da Neonize/whatsmeow.
  - `garbage_bot_config.sqlite`: Mappatura JID dei gruppi, nomi e URL Google Sheets.
  - `options.json`: Opzioni salvate dall'interfaccia utente di Home Assistant.

---

## Struttura del Progetto

```text
garbage_bot/
├── garbage_bot.py              # Applicazione principale Python
├── requirements.txt            # Dipendenze Python
├── config.yaml                 # Metadata add-on Home Assistant
├── Dockerfile                  # Immagine Docker Debian-based
├── run.sh                      # Entrypoint container con gestione credenziali
├── translations/               # Traduzioni interfaccia opzioni HA (it, en)
│   ├── it.yaml
│   └── en.yaml
├── README.md                   # Documentazione add-on
├── INSTALL_HOMEASSISTANT.md    # Guida installazione Home Assistant OS
├── SETUP_CALENDARIO.md         # Istruzioni Google Sheets
├── INSTALL_LOCAL.md            # Guida esecuzione locale / development
├── garbage_bot.service         # Template systemd per esecuzione locale
└── setup.sh                    # Script di provisioning locale
```

---

## Risoluzione Errori Comuni

### Errore: "Client outdated (405) connect failure"
- **Sintomo:** Il bot fallisce la connessione e nei log compare:
  `ERROR - Client outdated (405) connect failure (client version: 2.3000.1039406452)`
- **Causa:** WhatsApp richiede periodicamente versioni aggiornate del protocollo web. Quando la versione riportata dalla libreria sottostante e deprecata dai server WhatsApp, la connessione viene respinta con errore 405.
- **Soluzione:** L'errore richiede un aggiornamento della libreria di connessione o dell'add-on di Home Assistant. In Home Assistant OS, aggiornare l'add-on all'ultima versione. In ambiente locale, eseguire `pip install --upgrade neonize`. Il bot preserva il database di sessione, evitando la necessita di effettuare nuovamente la scansione QR.

### Errore: "credentials.json non trovato"
- Copia il file scaricato da Google Cloud Console dentro la cartella `/config/` di Home Assistant denominandolo esattamente `credentials.json`.
- Riavvia l'add-on.

### PDF non generato
- Assicurati che il foglio "Calendario" esista e contenga le 4 colonne: `Data`, `Bidone`, `Condomino`, `Telefono`.
- Verifica che il formato delle date sia `DD/MM/YYYY`.

---

## Guide di Riferimento

- [Guida Installazione Home Assistant OS](INSTALL_HOMEASSISTANT.md)
- [Guida Configurazione Google Sheets](SETUP_CALENDARIO.md)
- [Guida Esecuzione e Test Locale](INSTALL_LOCAL.md)
- [README Principale](../README.md)

---

## Licenza

MIT License.
