# 🤖 WhatsApp Garbage Bot

**Bot WhatsApp intelligente per la gestione automatica di turni spazzatura e calendario con integrazione Google Sheets**

Monitora 24/7, genera calendari automaticamente, e mantiene il tuo condominio organizzato via WhatsApp.

> ⭐ **Consigliato per Home Assistant OS**. Supporta anche installazione locale su Linux/Raspberry Pi.

---

## ✨ Caratteristiche Principali

- 🏠 **Ottimizzato per Home Assistant**: Funziona come add-on nativo con container Docker
- 📅 **Calendario intelligente**: Monitoraggio continuo con generazione automatica di cicli
- 📱 **Comandi WhatsApp**: Interroga il calendario dal gruppo in tempo reale
- 🔔 **Promemoria giornalieri**: Notifica automatica chi è di turno ogni mattina
- 📊 **Google Sheets integrato**: Gestione dati su foglio condiviso
- 🚀 **Multi-ambiente**: Supporto per Home Assistant OS, Raspberry Pi e Linux
- 🔐 **Sicuro**: Autenticazione Google con credenziali dedicate
- 📨 **Notifiche Telegram**: Allerta istantanea per errori e QR code

---

## 📋 Comandi Disponibili

### Per Tutti
```
/oggi              Chi è di turno oggi
/prossimi          Prossimi 10 turni in programma
/regole            Regole e buone norme del condominio
/calendario        Invia PDF calendario (utenti) / Rigeneran completo (admin)
/help              Elenco completo comandi
```

### Solo Admin
```
/config            Collega un nuovo gruppo a Sheet
/config_check      Mostra configurazioni attuali
/config_reset      Rimuovi configurazione
/db_reset          Ricrea i database
```

---

## 🚀 Quick Start

### 1️⃣ Scegli il tuo ambiente

**🏠 [Home Assistant OS](INSTALL_HOMEASSISTANT.md) (Consigliato)**
- Installazione come add-on nativo
- Zero configurazione dei servizi
- Gestione interfaccia web integrata
- Aggiornamenti automatici

**🐧 [Linux / Raspberry Pi](INSTALL_LOCAL.md)**
- Installazione manuale con Python
- Perfetto se hai già un server Linux
- Richiede configurazione systemd

_Se non sai quale scegliere, usa **Home Assistant OS**!_

### 2️⃣ Configura Google Sheets

1. Prepara un Google Sheet con la struttura indicata in [SETUP_CALENDARIO.md](SETUP_CALENDARIO.md)
2. Ottieni le credenziali Google (Service Account JSON)
3. Carica il file nel bot (vedi guida installazione)

### 3️⃣ Configura il Primo Gruppo

Invia il comando nel gruppo WhatsApp:
```
/config https://chat.whatsapp.com/xxxxx https://docs.google.com/spreadsheets/d/xxxxx
```

✅ Fatto! Il bot è pronto a gestire i turni!

---

## 📚 Documentazione Completa

| Documento | Descrizione |
|-----------|-------------|
| **[📌 INSTALL_HOMEASSISTANT.md](INSTALL_HOMEASSISTANT.md)** | **[CONSIGLIATO]** Guida di installazione come add-on HA - Segui questa se non sai da dove iniziare |
| [📋 SETUP_CALENDARIO.md](SETUP_CALENDARIO.md) | Struttura Google Sheets + configurazione calendario turni |
| [🐧 INSTALL_LOCAL.md](INSTALL_LOCAL.md) | Installazione alternativa per Linux/Raspberry Pi |
| [⬅️ README principale](../README.md) | Repository e overview generale del progetto |

---

## 🎯 Come Funziona

```
┌─────────────────────────────────────┐
│  Google Sheets (Impostazioni)       │
│  Lista condomini (A2:B1000)         │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  WhatsApp Bot (Monitora)            │
│  • Ogni 5 min: controlla modifiche  │
│  • Ogni mattina: promemoria turni   │
│  • Auto-genera: cicli quando serve  │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Google Sheets (Calendario)         │
│  Turni generati automaticamente     │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  WhatsApp Messages                  │
│  /oggi, /prossimi, /calendario      │
└─────────────────────────────────────┘
```

### Monitoraggio Automatico

Il bot controlla il calendario **ogni 5 minuti** e:

1. **Se i dati cambiano** (es: modifica ordine condomini)
   - Genera PDF e invia in privata al numero del bot

2. **Se rimangono ≤30 giorni** nel ciclo attuale
   - Genera automaticamente il nuovo ciclo
   - Invia PDF in privata

3. **Ogni mattina alle 09:00**
   - Invia promemoria al gruppo (chi è di turno oggi)

---

## 🔧 Requisiti

### Necessario
- **Python 3.10+** (per installazione locale)
- **Google Account** con accesso a Google Cloud
- **Numero WhatsApp** per il bot
- **Google Sheet** per gestire i dati

### Opzionale
- **Raspberry Pi** o simile (per esecuzione continua)
- **Home Assistant** (per integrazione domotica)

---

## 📁 Struttura del Progetto

```
whatsapp_garbage_bot/
├── garbage_bot.py              # Bot principale
├── requirements.txt            # Dipendenze Python
├── config.json                 # Metadata Home Assistant
├── Dockerfile                  # Container Docker
├── run.sh                       # Script di avvio
│
├── 📖 Documentazione
├── README.md                   # Questo file
├── SETUP_CALENDARIO.md         # Configurazione Sheets
├── INSTALL_LOCAL.md            # Setup locale
├── INSTALL_HOMEASSISTANT.md    # Setup Home Assistant
│
└── 📋 Reference
    ├── calendar.gs             # Google Apps Script originale
    ├── garbage_bot.service     # Unit file systemd
    └── setup.sh                # Script setup iniziale
```

---

## 💡 Scenari di Utilizzo

### Scenario 1: Condominio piccolo (2-3 persone)
```
Lunedì:  Mario -> Plastica
Martedì: Mario -> Carta
Mercoledì: Paola -> Plastica
...
```

### Scenario 2: Condominio medio-grande (10+ persone)
```
Lunedì:  Condomino 1 -> Plastica
Martedì: Condomino 1 -> Carta
Mercoledì: Condomino 2 -> Plastica
...
```

Il bot **gestisce automaticamente** per quanti condomini vuoi.

---

## 🐛 Troubleshooting Rapido

### "Bot non risponde"
```bash
# Controlla i log
sudo journalctl -u whatsapp_bot -f  # Linux
# oppure consulta i log in Home Assistant
```

### "PDF non generato"
- Verifica che la struttura Google Sheets sia corretta
- Controlla che il foglio si chiami esattamente "Calendario"

### "Credenziali non valide"
- Scarica di nuovo `credentials.json` da Google Cloud
- Verifica che il Service Account abbia accesso allo Sheet

---

## 🤝 Contributi e Issues

- Segnala bug: [Issues](../../issues)
- Discussioni e feature request: [Discussions](../../discussions)

---

## 📄 Licenza

MIT License - Libero da usare e modificare

---

## 👤 Supporto

Per domande o problemi:
1. Leggi la [documentazione](SETUP_CALENDARIO.md)
2. Controlla i [log di errore](#troubleshooting-rapido)
3. Apri un [issue](../../issues)

---

**Lasciato un ⭐ se ti è stato utile!**
