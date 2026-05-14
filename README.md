# 🚀 WhatsApp Garbage Bot - Home Assistant Add-on Repository

**Soluzione Completa per la gestione automatica dei turni spazzatura via WhatsApp + Google Sheets**

Repository ufficiale di custom add-ons per [Home Assistant](https://www.home-assistant.io/). Questo add-on è **ottimizzato e consigliato per Home Assistant OS**.

## 📦 Add-on Disponibile

### 🤖 WhatsApp Garbage Bot
Bot WhatsApp intelligente per gestione automatica turni spazzatura e calendario condominiale con integrazione Google Sheets.

**Caratteristiche:**
- 📅 Gestione automatica calendario turni su Google Sheets
- 📱 Comandi WhatsApp intuitivi e reattivi
- 📊 Integrazione completa con Google Sheets
- 🔔 Promemoria giornalieri via WhatsApp
- 📝 Generazione PDF del calendario
- 🔄 Gestione automatica cicli di turnazioni
- ⚙️ Comandi amministrativi per configurazione

[Documenti dell'add-on](whatsapp_garbage_bot/INSTALL_HOMEASSISTANT.md)

## 🎯 Comandi Disponibili

### Comandi Generali
- **`/oggi`** - Mostra chi è di turno oggi
- **`/prossimi`** - Visualizza i prossimi 10 turni
- **`/regole`** - Leggi il regolamento rifiuti
- **`/calendario`** - Scarica il PDF del calendario aggiornato
- **`/info`** - Mostra l'aiuto con tutti i comandi

### Comandi Amministratore (Gruppo)
- **`/attiva <link_sheet>`** - Attiva il bot nel gruppo (richiede link Google Sheets)
- **`/disattiva`** - Disattiva il bot nel gruppo
- **`/genera`** - Corregge il ciclo corrente e lo rigenera da zero
- **`/genera nuovi`** - Crea una nuova turnazione partendo dalla fine del ciclo attuale

### Comandi Superadmin (Chat Privata)
- **`/config <link_gruppo> <link_sheet>`** - Configura il bot via link
- **`/config_check`** - Lista tutte le configurazioni attive
- **`/config_reset <numero>`** - Rimuove una configurazione
- **`/db_reset`** - Pulisce e ricrea il database

## 🔧 Come Installare

### ⚡ Installazione Rapida (Consigliata)

**Prerequisiti:**
- Home Assistant OS in esecuzione
- File `credentials.json` da Google Cloud Console

**Passi:**

[![Open your Home Assistant instance and show the add-on store.](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/)

1. Clicca il badge sopra per aprire l'Add-on Store in H.A.
2. Click su **Repositories** (in alto)
3. Aggiungi il repository: `https://github.com/vladbragoi/garbage-bot`
4. Cerca **WhatsApp Garbage Bot**
5. Clicca **Install**
6. Configura il file `credentials.json` (vedi [INSTALL_HOMEASSISTANT.md](garbage_bot/INSTALL_HOMEASSISTANT.md))
7. Clicca **Start**

**Per approfondimenti:** Consulta la [guida di installazione completa](garbage_bot/INSTALL_HOMEASSISTANT.md).

## ⚙️ Come Funziona

1. **Configurazione Iniziale**: Un amministratore usa `/attiva <link_sheet>` per collegare un Google Sheets al gruppo
2. **Cicli Automatici**: Il bot gestisce automaticamente cicli di turnazioni settimanali
3. **Promemoria**: Ogni giorno alle 09:00 invia un promemoria WhatsApp al condomino di turno
4. **Regenerazione**: Quando un ciclo scade (<30 giorni), crea automaticamente `NuovoCalendario`
5. **Gestione Manuale**: Usa `/genera` per correggere o `/genera nuovi` per rigenerare

### Struttura Google Sheets Richiesta

- **Fogli**: `Calendario` (attuale), `NuovoCalendario` (prossimo, opzionale), `Impostazioni` (elenco condomini), `Regole` (regolamento)
- **Colonne Calendario**: Data, Bidone, Condomino, Telefono
- **Formato Data**: DD/MM/YYYY

## 📚 Documentazione Completa

| Documento | Descrizione |
|-----------|-------------|
| [📌 INSTALL_HOMEASSISTANT.md](garbage_bot/INSTALL_HOMEASSISTANT.md) | **[CONSIGLIATO]** Guida di installazione come add-on HA |
| [📋 SETUP_CALENDARIO.md](garbage_bot/SETUP_CALENDARIO.md) | Configurazione e struttura Google Sheets |
| [🤖 README.md](garbage_bot/README.md) | Descrizione features e comandi disponibili |
| [🐧 INSTALL_LOCAL.md](garbage_bot/INSTALL_LOCAL.md) | Installazione alternativa per Linux/Raspberry Pi |

⚠️ **Nota:** Se installi localmente (non su HA), il bot richiede Python 3.10+ e configurazione manuale dei servizi systemd.

## �️ Architettura del Bot

- **Runtime Principale:** Home Assistant Container (Docker)
- **Backend:** Python 3.12 + asyncio
- **Chat WhatsApp:** Neonize (Go Bridge)
- **Database:** SQLite (persistente in `/data/`)
- **API Google:** Google Sheets + Service Account Auth
- **Notifiche:** Telegram (per alerting errori)

## 📄 Licenza

MIT License - Libero da usare e modificare nel tuo ambiente HA

---

**Domande? Apri un [issue](../../issues) nel repository! 🎉**