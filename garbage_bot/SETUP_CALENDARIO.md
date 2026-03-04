# 📅 Configurazione Google Sheets - Calendario Turni

Questo documento spiega come strutturare il tuo Google Sheet affinché il bot lo legga e gestisca correttamente il calendario dei turni.

---

## 📊 Struttura del Google Sheet

Il tuo spreadsheet deve contenere **3 fogli**:

### 1. Foglio "Impostazioni"

Contiene la **lista dei condomini** e i loro dati.

| Colonna | Contenuto | Esempio |
|---------|-----------|---------|
| A1 | Header (fisso) | "Nome" |
| B1 | Header (fisso) | "Telefono" |
| A2:A∞ | Nome condomino | Mario Rossi |
| B2:B∞ | Telefono (opzionale) | +39 3XX XXXXXXX |

**Importante:**
- La lista inizia da **A2** e continua fino a **B1000** (range massimo)
- L'ordine in questa colonna determina l'ordine dei turni nel calendario
- Se modifichi l'ordine, il bot rileva il cambio e invia una notifica

**Esempio della pagina "Impostazioni":**

```
Nome              | Telefono
-----------------+------------------
Mario Rossi       | +39 333 1234567
Paola Bianchi     | +39 334 2345678
Franco Verdi      | +39 335 3456789
Lucia Rossi       |
...
```

---

### 2. Foglio "Calendario"

Il bot **genera automaticamente** i turni in questo foglio.

**Header (riga 1) - Fisso:**

| Colonna | Contenuto |
|---------|-----------|
| A1 | "Data" |
| B1 | "Bidone" |
| C1 | "Condomino" |
| D1 | "Telefono" |

**Dati (righe 2+) - Generati dal bot:**

```
Data      | Bidone   | Condomino    | Telefono
----------|----------|--------------|------------------
13/02/2026| plastica | Mario Rossi  | +39 333 1234567
14/02/2026| carta    | Mario Rossi  |
15/02/2026| plastica | Paola Bianchi| +39 334 2345678
16/02/2026| carta    | Paola Bianchi|
...
```

**Algoritmo di generazione:**

Per ogni condomino:
- **Lunedì**: Plastica
- **Martedì**: Carta
- Poi passa al condomino successivo

Se hai 3 condomini:
```
Lunedì   1: Mario -> Plastica
Martedì  1: Mario -> Carta
Mercoledì 2: Paola -> Plastica
Giovedì  2: Paola -> Carta
Venerdì  3: Franco -> Plastica
Sabato   3: Franco -> Carta
Domenica 1: Mario -> Plastica  (ricomincia il ciclo)
```

**Cicli:**
- Ogni ciclo = (numero condomini × 2) righe
- Il bot mantiene **max 2 cicli** contemporaneamente
- Quando rimangono ≤30 giorni nel ciclo attuale, ne genera uno nuovo

---

### 3. Foglio "Regole" (Opzionale)

Contiene il regolamento del condominio. Mostrato con il comando `/regole`.

Formato libero - può essere:
- Una colonna di testo
- Elenco puntato
- Qualsiasi formato tu preferisca

**Esempio:**

```
REGOLE CONDOMINIALI - GESTIONE SPAZZATURA

✅ CORRETTO:
• Cumuli ben contenuti in appositi bidoni
• Plastica ben separata in sacchi
• Differenziazione accurata

❌ VIETATO:
• Lasciare i cumuli per strada
• Mescolare i bidoni
• Utilizzare per rifiuti speciali
```

Quando qualcuno scrive `/regole`, il bot restituisce tutto il contenuto di questo foglio.

---

## 🔄 Flusso di Generazione Automatica

```
┌─────────────────────────────────┐
│  Bot monitora ogni 5 minuti     │
└────────────┬────────────────────┘
             │
             ├→ Calcola HASH del calendario
             │
             └→ Se HASH è diverso O rimangono ≤30 giorni
                 │
                 └→ Genera nuovo ciclo
                    │
                    ├→ Legge condomini da A2:B1000
                    ├→ Crea turni (lunedì=plastica, martedì=carta)
                    ├→ Scrive in "Calendario" mantenendo max 2 cicli
                    ├→ Genera PDF formattato
                    └→ Invia PDF in privata al bot
```

**Trigger automatici:**
1. ✅ Modifica dei dati di calendario → PDF inviato
2. ✅ Rimangono ≤30 giorni nel ciclo → Ciclo generato + PDF inviato

---

## 📝 Dettagli Tecnici

### Hash SHA256

Il bot usa un **hash SHA256** del contenuto del calendario per rilevare modifiche:

```python
hash = SHA256(calendario_data)
```

Se qualcuno **modifica l'ordine dei condomini** o cambia dati nella "Impostazioni", il bot lo rileva automaticamente entro 5 minuti.

### Formattazione PDF

Il PDF del calendario include:

- **Intestazione verde** (#356854 - verde bosco)
- **Righe alternate** (bianco / #f2f2f2)
- **Tabella**: Data | Bidone | Condomino | Telefono
- **Data di generazione** in calce

### Timezone

Il bot usa **timezone Europe/Rome**. Le date e i promemoria seguono questo fuso orario.

Se hai necessità diverse, contatta l'admin.

---

## ⚡ Comandi Disponibili per il Calendario

| Comando | Effetto | Dove |
|---------|---------|------|
| `/calendario` | **Utente**: Invia PDF attuale | Nel gruppo |
| `/calendario` | **Admin**: Rigenera da capo | Privata del bot |
| `/oggi` | Chi è di turno oggi | Nel gruppo |
| `/prossimi` | Prossimi 10 turni | Nel gruppo |

---

## 🎯 Esempi Pratici

### Esempio 1: Primo ciclo di 3 condomini

**Impostazioni:**
```
Mario Rossi
Paola Bianchi
Franco Verdi
```

**Calendario Generato (Ciclo 1):**
```
Data       | Bidone    | Condomino     | Telefono
-----------|-----------|---------------|------------------
13/02/2026 | plastica  | Mario Rossi   | +39 333 XXXX
14/02/2026 | carta     | Mario Rossi   |
15/02/2026 | plastica  | Paola Bianchi | +39 334 XXXX
16/02/2026 | carta     | Paola Bianchi |
17/02/2026 | plastica  | Franco Verdi  |
18/02/2026 | carta     | Franco Verdi  |
19/02/2026 | plastica  | Mario Rossi   | (ricomincia)
...
```

### Esempio 2: Cambio ordine condomini

Se modifichi l'ordine in "Impostazioni" da:
```
Mario, Paola, Franco
```

a:
```
Franco, Mario, Paola
```

Il bot:
1. **Entro 5 minuti**: Rileva il cambio via hash
2. **Genera**: Un pdf con il calendario aggiornato
3. **Invia**: Il PDF in privata

### Esempio 3: Ciclo quasi terminato

Se il primo ciclo finisce il 5 aprile e oggi è 10 marzo (<30 giorni):

1. Bot rileva: "Rimangono 26 giorni"
2. **Genera**: Nuovo ciclo partendo dall'8 aprile
3. **Mantiene**: Ciclo vecchio + ciclo nuovo (2 cicli totali)
4. **Elimina**: Cicli più vecchi (max 2)

---

## 🔍 Debugging

### Come verificare che il foglio sia configurato correttamente

1. **Controlla i nomi dei fogli:**
   ```
   Impostazioni  ← Esatto, con accento
   Calendario    ← Esatto
   Regole        ← Opzionale
   ```

2. **Verifica la lista condomini:**
   - Sono in A2:B1000?
   - Nomi non vuoti?

3. **Verifica il calendario:**
   - Header è presente (A1:D1)?
   - Il bot scrive i dati partendo da A2?

### Se il bot non genera il calendario

Controlla:

1. **Credenziali Google**: Sono valide?
2. **Permessi**: Il bot ha accesso in lettura/scrittura allo sheet?
3. **Nomi fogli**: Sono esatti? (Case-sensitive per alcuni)
4. **Range condomini**: A2:B1000 è corretto?

---

## 💡 Best Practices

✅ **Fai così:**

- Mantieni l'ordine dei condomini ordine di rotazione che vuoi
- Aggiungi i telefoni nella colonna B per riferimento
- Controlla il PDF regolarmente per verificare che sia corretto
- Usa `/regole` per comunicare norme condominiali

❌ **Non fare così:**

- Non modificare manualmente il foglio "Calendario" (il bot lo rigenera)
- Non cambiare i nomi dei fogli (devono essere esatti)
- Non eliminare il header in row 1
- Non aggiungere colonne extra (il bot usa solo A:D)

---

## 📞 Support

Se hai problemi:

1. Leggi [README.md](README.md) - Overview del progetto
2. Seleziona il tuo ambiente:
   - [INSTALL_LOCAL.md](INSTALL_LOCAL.md) - Setup locale/Raspberry Pi
   - [INSTALL_HOMEASSISTANT.md](INSTALL_HOMEASSISTANT.md) - Setup Home Assistant
3. Controlla i log per errori

---

**Ora il tuo Google Sheet è pronto! 🎉**
