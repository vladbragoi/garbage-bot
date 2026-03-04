# WhatsApp Garbage Bot - Home Assistant Add-ons Repository

Repository ufficiale di custom add-ons per [Home Assistant](https://www.home-assistant.io/).

## 📦 Add-ons Disponibili

### WhatsApp Garbage Bot
Bot WhatsApp per gestione automatica turni spazzatura e calendario condominiale.

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

1. Home Assistant → Settings → Add-ons → **Create add-on repository**
2. Inserisci l'URL di questo repository
3. Cerca "WhatsApp Garbage Bot"
4. Clicca **Install**

Per ulteriori informazioni, vedi la [documentazione completa](whatsapp_garbage_bot/INSTALL_HOMEASSISTANT.md).

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

## 📚 Documentazione

- [Installazione in Home Assistant](whatsapp_garbage_bot/INSTALL_HOMEASSISTANT.md)
- [Installazione Locale (Linux/Raspberry Pi)](whatsapp_garbage_bot/INSTALL_LOCAL.md)
- [Configurazione Google Sheets](whatsapp_garbage_bot/SETUP_CALENDARIO.md)
- [Demo e Comandi](whatsapp_garbage_bot/README.md)

## 📄 License

MIT License