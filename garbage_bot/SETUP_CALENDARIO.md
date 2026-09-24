# Configurazione Google Sheets - Calendario Turni

Questo documento illustra la struttura richiesta per il foglio Google Sheet affinche GarbageBot possa leggere, verificare e generare automaticamente i calendari delle turnazioni.

---

## Struttura del Google Sheet

Lo spreadsheet deve contenere i seguenti fogli di lavoro:

### 1. Foglio "Impostazioni"

Contiene l'anagrafica dei condomini e l'ordine stabilito per la rotazione dei turni.

| Cella | Contenuto | Esempio |
|---|---|---|
| A1 | Intestazione fissa | Nome |
| B1 | Intestazione fissa | Telefono |
| A2:A1000 | Nome condomino | Mario Rossi |
| B2:B1000 | Telefono (opzionale) | +39 333 1234567 |

**Specifiche:**
- I dati partono dalla riga 2 (range `A2:B1000`).
- L'ordine delle righe stabilisce la sequenza di turnazione.
- Se l'elenco dei condomini viene modificato, il bot calcola il nuovo hash e rigenera la pianificazione.

**Esempio foglio "Impostazioni":**

```text
Nome              | Telefono
------------------+------------------
Mario Rossi       | +39 333 1234567
Paola Bianchi     | +39 334 2345678
Franco Verdi      | +39 335 3456789
Lucia Neri        | 
```

---

### 2. Foglio "Calendario"

Il foglio in cui il bot scrive e mantiene i turni attivi.

**Riga 1 (Intestazioni fisse):**

| Colonna | Intestazione |
|---|---|
| A1 | Data |
| B1 | Bidone |
| C1 | Condomino |
| D1 | Telefono |

**Righe 2+ (Turni generati automaticamente):**

```text
Data       | Bidone   | Condomino     | Telefono
-----------+----------+---------------+------------------
13/04/2026 | plastica | Mario Rossi   | +39 333 1234567
14/04/2026 | carta    | Mario Rossi   | +39 333 1234567
20/04/2026 | plastica | Paola Bianchi | +39 334 2345678
21/04/2026 | carta    | Paola Bianchi | +39 334 2345678
```

**Regola di turnazione predefinita:**
- Ogni turno settimanale prevede:
  - Lunedi: esposizione bidone Plastica
  - Martedi: esposizione bidone Carta
- Al termine della coppia di turni, la responsabilita passa al condomino successivo nella lista.
- Un ciclo completo e composto da `numero condomini * 2` righe.

---

### 3. Foglio "NuovoCalendario" (Generato Automaticamente)

Quando nel foglio "Calendario" restano 30 o meno giorni prima dell'ultimo turno pianificato, il bot:
1. Crea automaticamente il foglio `NuovoCalendario`.
2. Calcola la data del lunedi successivo all'ultimo turno programmato.
3. Individua il prossimo condomino in sequenza.
4. Genera il documento PDF del nuovo ciclo e lo invia sul canale Telegram configurato.
5. Quando il ciclo corrente giunge a scadenza, il foglio precedente viene archiviato e `NuovoCalendario` viene promosso a `Calendario`.

---

### 4. Foglio "Regole" (Opzionale)

Contiene il regolamento o le indicazioni per lo smaltimento dei rifiuti nel condominio.
Il testo presente in questo foglio viene inviato nella chat quando un condomino usa il comando `/regole`.

---

## Comandi Correlati al Calendario

| Comando | Destinatario | Descrizione |
|---|---|---|
| `/oggi` | Gruppo | Indica chi e di turno nella data corrente e quale bidone esporre |
| `/prossimi` | Gruppo | Elenca i successivi 10 turni programmati |
| `/calendario` | Gruppo | Invia il file PDF del calendario corrente nel gruppo WhatsApp |
| `/regole` | Gruppo | Mostra il testo presente nel foglio "Regole" |
| `/genera` | Admin Gruppo | Tronca i turni futuri ed esegue il reset del ciclo dal lunedi successivo |
| `/genera nuovi` | Admin Gruppo | Forza la creazione anticipata del foglio "NuovoCalendario" e genera il PDF |

---

## Linee Guida per la Manutenzione

### Operazioni Corrette:
- Mantenere l'ordine desiderato dei condomini nel foglio "Impostazioni".
- Inserire i numeri di telefono con prefisso internazionale per consentire la menzione nel promemoria giornaliero.
- Verificare periodicamente il PDF generato.

### Operazioni da Evitare:
- Non modificare manualmente le righe generate nel foglio "Calendario".
- Non rinominare le colonne A1:D1 nei fogli "Calendario" e "NuovoCalendario".
- Non eliminare il foglio "Impostazioni".
