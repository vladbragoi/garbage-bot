import asyncio
import logging
import sys
import signal
import sqlite3
import gspread
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import json

from oauth2client.service_account import ServiceAccountCredentials
from neonize.aioze.client import NewAClient
from neonize.aioze.events import ConnectedEv, MessageEv
from neonize.proto.Neonize_pb2 import JID
from xhtml2pdf.document import pisaDocument

# --- CLASSE CONFIGURAZIONE GLOBALE ---
class Config:
    DB_PATH_NEONIZE = "/data/garbage_bot.sqlite"
    DB_PATH_CONFIG = "/data/garbage_bot_config.sqlite"
    CREDENTIALS_FILE = "/data/credentials.json"
    DATE_FORMAT = "%d/%m/%Y"
    LOG_LEVEL = logging.DEBUG

# --- GESTIONE DATABASE CONFIGURAZIONI (SQLite) ---
class BotConfigDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Schema aggiornato con jid_data (BLOB)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_configs (
                    jid TEXT PRIMARY KEY,
                    sheet_url TEXT NOT NULL,
                    group_name TEXT,
                    jid_data BLOB
                )
            ''')
            conn.commit()
    
    def recreate_tables(self):
        """Distrugge e ricrea la tabella (Utile per aggiornamenti schema)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS group_configs')
            conn.commit()
            # Richiama la creazione
            self._init_db()

    def set_config(self, jid_obj: JID, sheet_url: str, group_name: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            jid_str = jid_obj.User
            # Serializza l'oggetto JID in binario
            jid_bytes = jid_obj.SerializeToString()
            
            cursor.execute('''
                INSERT INTO group_configs (jid, sheet_url, group_name, jid_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(jid) DO UPDATE SET 
                    sheet_url=excluded.sheet_url, 
                    group_name=excluded.group_name,
                    jid_data=excluded.jid_data
            ''', (jid_str, sheet_url, group_name, jid_bytes))
            conn.commit()

    def delete_config(self, jid: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM group_configs WHERE jid = ?', (jid,))
            conn.commit()
            return cursor.rowcount > 0

    def get_sheet_url(self, jid: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT sheet_url FROM group_configs WHERE jid = ?', (jid,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_configs(self) -> List[tuple]:
        """Restituisce (jid_str, sheet_url, group_name, jid_data_blob)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT jid, sheet_url, group_name, jid_data FROM group_configs')
            return cursor.fetchall()

# --- CLASSE GESTIONE DATI (Google Sheets) ---
class GoogleSheetClient:
    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.log = logging.getLogger("GoogleSheetClient")

    def _get_client(self):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
        return gspread.authorize(creds)

    def _fetch_calendar_sync(self, sheet_url: str) -> List[Dict[str, Any]]:
        self.log.info(f"📥 Download dati da URL: {sheet_url[:30]}...")
        try:
            gc = self._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Calendario")
            data = sheet.get_all_records()
            self.log.info(f"✅ Dati scaricati: {len(data)} record.")
            return data
        except Exception as e:
            self.log.error(f"❌ Errore download Calendario: {e}")
            return []

    def _fetch_rules_sync(self, sheet_url: str) -> str:
        self.log.info(f"📥 Download Regole da URL: {sheet_url[:30]}...")
        try:
            gc = self._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Regole")
            rows = sheet.get_all_values()
            
            lines = []
            for row in rows:
                text_row = " ".join([c for c in row if c.strip()])
                if text_row:
                    lines.append(text_row)
            
            return "\n".join(lines)
        except Exception as e:
            self.log.error(f"❌ Errore download Regole: {e}")
            return "⚠️ Impossibile recuperare le regole."

    async def get_records(self, sheet_url: str) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_calendar_sync, sheet_url)

    async def get_rules_text(self, sheet_url: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_rules_sync, sheet_url)

    def read_cell(self, sheet_url: str, sheet_name: str, cell: str) -> Any:
        """Legge una singola cella da un foglio"""
        self.log.info(f"📖 Leggo cella {sheet_name}!{cell}")
        try:
            gc = self._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet(sheet_name)
            value = sheet.acell(cell).value
            self.log.info(f"✅ Valore letto: {value}")
            return value
        except Exception as e:
            self.log.error(f"❌ Errore lettura cella: {e}")
            return None

    def write_cell(self, sheet_url: str, sheet_name: str, cell: str, value: Any) -> bool:
        """Scrive una singola cella su un foglio"""
        self.log.info(f"✍️ Scrivo {value} in {sheet_name}!{cell}")
        try:
            gc = self._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet(sheet_name)
            sheet.update_acell(cell, value)
            self.log.info(f"✅ Cella aggiornata")
            return True
        except Exception as e:
            self.log.error(f"❌ Errore scrittura cella: {e}")
            return False

# --- GENERATORE PDF E GESTORE EMAIL ---
class CalendarManager:
    def __init__(self, credentials_file: str, sheet_client: GoogleSheetClient):
        self.credentials_file = credentials_file
        self.sheet_client = sheet_client
        self.log = logging.getLogger("CalendarManager")
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Dict[str, Any]:
        """Carica le credenziali Google dal file"""
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log.error(f"Errore caricamento credenziali: {e}")
            return {}

    def _get_gmail_client(self):
        """Ottiene il client Gmail API"""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            scopes = ['https://www.googleapis.com/auth/gmail.send']
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            return build('gmail', 'v1', credentials=creds)
        except ImportError:
            self.log.warning("Google API client non disponibile, uso SMTP")
            return None

    def _generate_pdf_from_html(self, html_content: str) -> Optional[bytes]:
        """Converte HTML a PDF"""
        try:
            self.log.info("📄 Generazione PDF...")
            pdf_buffer = BytesIO()
            pisaStatus = pisaDocument(
                BytesIO(html_content.encode('utf-8')),
                pdf_buffer
            )
            if pisaStatus.err:
                self.log.error(f"Errore PDF: {pisaStatus.err}")
                return None
            return pdf_buffer.getvalue()
        except Exception as e:
            self.log.error(f"Errore generazione PDF: {e}")
            return None

    async def check_and_send_calendar(self, impostazioni_url: str) -> bool:
        """
        Controlla D2 in Impostazioni. Se TRUE:
        - Genera PDF dal calendario
        - Invia email
        - Resetta D2 a FALSE
        """
        try:
            # 1. Leggi D2 dal foglio Impostazioni
            loop = asyncio.get_running_loop()
            checkbox_value = await loop.run_in_executor(
                None, 
                self.sheet_client.read_cell,
                impostazioni_url,
                "Impostazioni",
                "D2"
            )
            
            self.log.info(f"🔍 Checkbox D2 = {checkbox_value}")
            
            if checkbox_value != True and checkbox_value != "TRUE" and checkbox_value != 1:
                return False
            
            self.log.info("✅ Checkbox attivata! Inizio generazione PDF...")
            
            # 2. Scarica i dati del calendario
            calendario_data = await self.sheet_client.get_records(impostazioni_url)
            if not calendario_data:
                self.log.warning("⚠️ Nessun dato calendario")
                return False
            
            # 3. Genera HTML
            html_content = self._generate_html_table(calendario_data)
            
            # 4. Converti in PDF
            pdf_bytes = self._generate_pdf_from_html(html_content)
            if not pdf_bytes:
                self.log.error("Errore conversione PDF")
                return False
            
            # 5. Invia email
            email_sent = await loop.run_in_executor(
                None,
                self._send_email_with_pdf,
                pdf_bytes
            )
            
            if email_sent:
                # 6. Resetta D2 a FALSE
                await loop.run_in_executor(
                    None,
                    self.sheet_client.write_cell,
                    impostazioni_url,
                    "Impostazioni",
                    "D2",
                    False
                )
                self.log.info("✅ Ciclo completato: checkbox resettata")
                return True
            else:
                self.log.error("Errore invio email")
                return False
                
        except Exception as e:
            self.log.error(f"❌ Errore in check_and_send_calendar: {e}")
            return False

    def _generate_html_table(self, dati: List[Dict]) -> str:
        """Genera HTML stilizzato del calendario"""
        colore_principale = "#356854"
        colore_alternato = "#f2f2f2"
        data_generazione = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        html = f"""<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 20px; font-family: Arial, sans-serif; }}
  h2 {{ color: {colore_principale}; text-align: center; }}
  p {{ text-align: center; color: #666; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
  th {{ background-color: {colore_principale}; color: white; font-weight: bold; }}
  tr:nth-child(even) {{ background-color: {colore_alternato}; }}
</style>
</head>
<body>
<h2>Calendario Turni Raccolta Differenziata</h2>
<p>Scala C</p>
<table>
<thead>
<tr>
<th>Data</th>
<th>Bidone</th>
<th>Condomino</th>
</tr>
</thead>
<tbody>
"""
        
        for row in dati:
            if 'Data' in row and row['Data']:
                data = str(row.get('Data', ''))
                bidone = str(row.get('Bidone', ''))
                condomino = str(row.get('Condomino', ''))
                html += f"<tr><td>{data}</td><td>{bidone}</td><td>{condomino}</td></tr>\n"
        
        html += f"""</tbody>
</table>
<p style="font-size: 10px; color: #999; text-align: right; margin-top: 20px;">
Aggiornato al: {data_generazione}
</p>
</body>
</html>"""
        return html

    def _send_email_with_pdf(self, pdf_bytes: bytes) -> bool:
        """Invia email con allegato PDF via Gmail o SMTP"""
        try:
            email_dest = "vlad.bragoi@gmail.com"
            
            # Tenta con Gmail API
            gmail_client = self._get_gmail_client()
            if gmail_client:
                return self._send_via_gmail_api(gmail_client, email_dest, pdf_bytes)
            else:
                # Fallback: SMTP
                return self._send_via_smtp(email_dest, pdf_bytes)
                
        except Exception as e:
            self.log.error(f"Errore invio email: {e}")
            return False

    def _send_via_gmail_api(self, gmail_client, email_dest: str, pdf_bytes: bytes) -> bool:
        """Invia email tramite Gmail API"""
        try:
            import base64
            
            msg = MIMEMultipart()
            msg['to'] = email_dest
            msg['subject'] = "Aggiornamento Calendario Turni: PDF pronto per la stampa"
            
            body = "Il calendario è stato aggiornato con il nuovo ciclo di turni. In allegato trovi il PDF stilizzato pronto per la stampa."
            msg.attach(MIMEText(body, 'plain'))
            
            part = MIMEApplication(pdf_bytes, Name='Calendario_Turni.pdf')
            part['Content-Disposition'] = 'attachment; filename="Calendario_Turni.pdf"'
            msg.attach(part)
            
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            gmail_client.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.log.info(f"✅ Email inviata via Gmail API a {email_dest}")
            return True
            
        except Exception as e:
            self.log.error(f"Errore Gmail API: {e}")
            return False

    def _send_via_smtp(self, email_dest: str, pdf_bytes: bytes) -> bool:
        """Fallback: invia via SMTP (richiede credenziali SMTP)"""
        try:
            # Carica config SMTP dal file credenziali o variabili ambiente
            smtp_host = self.credentials.get("smtp_host", "smtp.gmail.com")
            smtp_port = self.credentials.get("smtp_port", 587)
            smtp_user = self.credentials.get("client_email")
            
            # Nota: Per Gmail, genera una "App Password" se hai 2FA
            # O usa credenziali di posta diversa
            self.log.warning("⚠️ Configurazione SMTP non disponibile in credentials.json")
            return False
            
        except Exception as e:
            self.log.error(f"Errore SMTP: {e}")
            return False

# --- GENERATORE CALENDARIO (da Google Apps Script) ---
class CalendarGenerator:
    """Replica la logica di generaNuovoCiclo() da Google Apps Script"""
    
    def __init__(self, sheet_client: GoogleSheetClient):
        self.sheet_client = sheet_client
        self.log = logging.getLogger("CalendarGenerator")
        self.color_principale = "#356854"
        self.color_alternato = "#f2f2f2"
        self.start_date_default = datetime(2026, 1, 5)

    def _check_calendar_needs_generation(self, calendario_data: List[Dict]) -> bool:
        """
        Controlla se è necessario generare il nuovo ciclo.
        Ritorna True se mancano <= 30 giorni dalla fine del ciclo attuale
        """
        if not calendario_data or len(calendario_data) < 2:
            return True
        
        try:
            # Prendi l'ultima data del calendario
            last_date_str = str(calendario_data[-1].get('Data', ''))
            if not last_date_str:
                return True
            
            last_date = datetime.strptime(last_date_str, "%d/%m/%Y").date()
            oggi = datetime.now().date()
            diff_days = (last_date - oggi).days
            
            self.log.info(f"📅 Giorni rimanenti nel ciclo: {diff_days}")
            
            return diff_days <= 30
            
        except Exception as e:
            self.log.error(f"Errore verifica ciclo: {e}")
            return False

    async def generate_calendar(self, sheet_url: str) -> bool:
        """
        Genera il calendario (replicando generaNuovoCiclo da Apps Script).
        Ritorna True se è stato generato un nuovo ciclo
        """
        try:
            loop = asyncio.get_running_loop()
            
            # 1. Leggi i condomini da Impostazioni
            condomini = await loop.run_in_executor(
                None,
                self._get_condomini,
                sheet_url
            )
            
            if not condomini:
                self.log.warning("⚠️ Nessun condomino trovato")
                return False
            
            self.log.info(f"📍 Condomini trovati: {len(condomini)}")
            
            # 2. Leggi il calendario attuale
            calendario_data = await self.sheet_client.get_records(sheet_url)
            
            # 3. Controlla se serve generare il nuovo ciclo
            if not self._check_calendar_needs_generation(calendario_data):
                self.log.info("✅ Calendario ancora valido (>30 giorni)")
                return False
            
            self.log.info("🆕 Generazione nuovo ciclo in corso...")
            
            # 4. Genera i nuovi turni
            nuovi_turni = await loop.run_in_executor(
                None,
                self._generate_shifts,
                condomini,
                calendario_data
            )
            
            if not nuovi_turni:
                self.log.warning("⚠️ Nessun turno generato")
                return False
            
            # 5. Scrivi i nuovi turni nel foglio
            success = await loop.run_in_executor(
                None,
                self._write_shifts_to_sheet,
                sheet_url,
                calendario_data,
                nuovi_turni
            )
            
            if success:
                self.log.info("✅ Calendario generato e scritto su Sheets")
                # Applica formattazione
                await loop.run_in_executor(
                    None,
                    self._format_calendar,
                    sheet_url
                )
            
            return success
            
        except Exception as e:
            self.log.error(f"❌ Errore generazione calendario: {e}")
            return False

    async def reset_and_generate_calendar(self, sheet_url: str) -> bool:
        """
        Resetta il calendario e lo rigeneran completamente da zero.
        Usato quando cambia la lista dei condomini.
        Ritorna True se l'operazione è andata a buon fine
        """
        try:
            loop = asyncio.get_running_loop()
            
            # 1. Leggi i condomini da Impostazioni
            condomini = await loop.run_in_executor(
                None,
                self._get_condomini,
                sheet_url
            )
            
            if not condomini:
                self.log.warning("⚠️ Nessun condomino trovato")
                return False
            
            self.log.info(f"🔄 Reset e rigenerazione: {len(condomini)} condomini")
            
            # 2. Pulisci il foglio Calendario (mantenendo header)
            await loop.run_in_executor(
                None,
                self._reset_calendar_sheet,
                sheet_url
            )
            
            # 3. Genera i turni da zero, partendo dalla data di default (lunedì prossimo)
            nuovi_turni = await loop.run_in_executor(
                None,
                self._generate_shifts_from_scratch,
                condomini
            )
            
            if not nuovi_turni:
                self.log.warning("⚠️ Nessun turno generato")
                return False
            
            # 4. Scrivi i turni nel foglio pulito
            success = await loop.run_in_executor(
                None,
                self._write_new_shifts_to_sheet,
                sheet_url,
                nuovi_turni
            )
            
            if success:
                self.log.info("✅ Calendario rigenerato da zero")
                await loop.run_in_executor(
                    None,
                    self._format_calendar,
                    sheet_url
                )
                # Resetta l'hash del monitor
                return True
            
            return False
            
        except Exception as e:
            self.log.error(f"❌ Errore reset/rigenerazione: {e}")
            return False

    def _get_condomini(self, sheet_url: str) -> List[tuple]:
        """Legge la lista condomini da Impostazioni A2:B1000"""
        try:
            gc = self.sheet_client._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Impostazioni")
            dati = sheet.get("A2:B1000")
            
            condomini = []
            for row in dati:
                if row and row[0].strip():  # Se prima colonna non vuota
                    condomini.append((row[0], row[1] if len(row) > 1 else ""))
            
            return condomini
        except Exception as e:
            self.log.error(f"Errore lettura condomini: {e}")
            return []

    def _generate_shifts(self, condomini: List[tuple], calendario_data: List[Dict]) -> List[Dict]:
        """Genera la lista dei nuovi turni (replicando la logica di generaNuovoCiclo)"""
        try:
            nuovi_turni = []
            
            # Determina la data di inizio
            if not calendario_data or len(calendario_data) < 2:
                start_date = self.start_date_default
            else:
                last_date_str = str(calendario_data[-1].get('Data', ''))
                try:
                    last_date = datetime.strptime(last_date_str, "%d/%m/%Y")
                    start_date = last_date + timedelta(days=6)
                except:
                    start_date = self.start_date_default
            
            # Genera i turni
            for nome, telefono in condomini:
                lunedi = start_date
                martedi = start_date + timedelta(days=1)
                
                nuovi_turni.append({
                    'Data': lunedi.strftime("%d/%m/%Y"),
                    'Bidone': 'plastica',
                    'Condomino': nome,
                    'Telefono': telefono
                })
                
                nuovi_turni.append({
                    'Data': martedi.strftime("%d/%m/%Y"),
                    'Bidone': 'carta',
                    'Condomino': nome,
                    'Telefono': telefono
                })
                
                start_date += timedelta(days=7)
            
            self.log.info(f"✅ Generati {len(nuovi_turni)} nuovi turni")
            return nuovi_turni
            
        except Exception as e:
            self.log.error(f"Errore generazione turni: {e}")
            return []

    def _write_shifts_to_sheet(self, sheet_url: str, calendario_data: List[Dict], nuovi_turni: List[Dict]) -> bool:
        """Scrive i nuovi turni nel foglio Calendario"""
        try:
            gc = self.sheet_client._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Calendario")
            
            # Calcola le righe da mantenere (max 2 cicli)
            righe_per_ciclo = len(set(t['Condomino'] for t in nuovi_turni)) * 2
            max_righe_consentite = righe_per_ciclo * 2
            
            # Se il calendario è pieno, rimuovi le righe più vecchie
            current_rows = len(calendario_data) - 1  # Escludi header
            if current_rows > 0:
                rows_to_delete = current_rows + len(nuovi_turni) - max_righe_consentite
                if rows_to_delete > 0:
                    sheet.delete_rows(2, rows_to_delete)
            
            # Scrivi i nuovi turni
            values = [[t['Data'], t['Bidone'], t['Condomino'], t.get('Telefono', '')] for t in nuovi_turni]
            last_row = max(len(calendario_data), 1)
            if last_row == 1:  # Solo header
                last_row = 2
            
            sheet.insert_rows(values, last_row)
            
            self.log.info(f"✅ Scritti {len(values)} turni nel foglio")
            return True
            
        except Exception as e:
            self.log.error(f"Errore scrittura foglio: {e}")
            return False

    def _format_calendar(self, sheet_url: str) -> bool:
        """Applica la formattazione al calendario (righe alternate, header verde)"""
        try:
            gc = self.sheet_client._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Calendario")
            
            # Assicura header
            sheet.update("A1:D1", [["Data", "Bidone", "Condomino", "Telefono"]])
            
            self.log.info("✅ Calendario formattato")
            return True
            
        except Exception as e:
            self.log.error(f"Errore formattazione: {e}")
            return False

    def _reset_calendar_sheet(self, sheet_url: str) -> bool:
        """Pulisce il foglio Calendario mantenendo l'header"""
        try:
            gc = self.sheet_client._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Calendario")
            
            # Assicura header
            sheet.update("A1:D1", [["Data", "Bidone", "Condomino", "Telefono"]])
            
            # Cancella tutti i dati sotto l'header
            # Leggi il numero di righe
            all_data = sheet.get_all_values()
            if len(all_data) > 1:
                # Cancella le righe dal secondo in poi
                sheet.delete_rows(2, len(all_data) - 1)
            
            self.log.info("✅ Foglio Calendario ripulito")
            return True
            
        except Exception as e:
            self.log.error(f"Errore reset foglio: {e}")
            return False

    def _generate_shifts_from_scratch(self, condomini: List[tuple]) -> List[Dict]:
        """Genera i turni da zero partendo da una data di default (lunedì prossimo)"""
        try:
            nuovi_turni = []
            
            # Calcola il prossimo lunedì
            today = datetime.now().date()
            days_until_monday = (0 - today.weekday()) % 7  # 0 = lunedì
            if days_until_monday == 0:  # Se è già lunedì, partenza oggi
                days_until_monday = 0
            else:
                days_until_monday = (7 - today.weekday()) % 7  # Prossimo lunedì
                if days_until_monday == 0:
                    days_until_monday = 7
            
            start_date = today + timedelta(days=days_until_monday)
            
            self.log.info(f"📅 Generazione da data inizio: {start_date.strftime('%d/%m/%Y')}")
            
            # Genera i turni
            for nome, telefono in condomini:
                lunedi = start_date
                martedi = start_date + timedelta(days=1)
                
                nuovi_turni.append({
                    'Data': lunedi.strftime("%d/%m/%Y"),
                    'Bidone': 'plastica',
                    'Condomino': nome,
                    'Telefono': telefono
                })
                
                nuovi_turni.append({
                    'Data': martedi.strftime("%d/%m/%Y"),
                    'Bidone': 'carta',
                    'Condomino': nome,
                    'Telefono': telefono
                })
                
                start_date += timedelta(days=7)
            
            self.log.info(f"✅ Generati {len(nuovi_turni)} nuovi turni")
            return nuovi_turni
            
        except Exception as e:
            self.log.error(f"Errore generazione turni: {e}")
            return []

    def _write_new_shifts_to_sheet(self, sheet_url: str, nuovi_turni: List[Dict]) -> bool:
        """Scrive i nuovi turni nel foglio (assumendo sia già pulito)"""
        try:
            gc = self.sheet_client._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Calendario")
            
            # Scrivi i nuovi turni (inizia da riga 2, dopo l'header)
            values = [[t['Data'], t['Bidone'], t['Condomino'], t.get('Telefono', '')] for t in nuovi_turni]
            
            sheet.insert_rows(values, 2)
            
            self.log.info(f"✅ Scritti {len(values)} turni nel foglio")
            return True
            
        except Exception as e:
            self.log.error(f"Errore scrittura foglio: {e}")
            return False

    async def generate_pdf(self, sheet_url: str) -> Optional[bytes]:
        """Genera il PDF del calendario"""
        try:
            loop = asyncio.get_running_loop()
            calendario_data = await self.sheet_client.get_records(sheet_url)
            
            if not calendario_data or len(calendario_data) < 2:
                self.log.warning("⚠️ Nessun dato calendario per PDF")
                return None
            
            html_content = await loop.run_in_executor(
                None,
                self._generate_html,
                calendario_data
            )
            
            # Converti in PDF con pisaDocument
            pdf_buffer = BytesIO()
            pisaStatus = pisaDocument(
                BytesIO(html_content.encode('utf-8')),
                pdf_buffer
            )
            
            if pisaStatus.err:
                self.log.error(f"Errore PDF generation: {pisaStatus.err}")
                return None
            
            return pdf_buffer.getvalue()
                
        except Exception as e:
            self.log.error(f"Errore generazione PDF: {e}")
            return None

    def _generate_html(self, dati: List[Dict]) -> str:
        """Genera HTML stilizzato del calendario"""
        data_gen = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        html = f"""<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 20px; font-family: Arial, sans-serif; }}
  h2 {{ color: {self.color_principale}; text-align: center; }}
  p {{ text-align: center; color: #666; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
  th {{ background-color: {self.color_principale} !important; color: white !important; font-weight: bold; }}
  tr:nth-child(even) {{ background-color: {self.color_alternato}; }}
  tr:nth-child(odd) {{ background-color: white; }}
</style>
</head>
<body>
<h2>Calendario Turni Raccolta Differenziata</h2>
<p>Scala C</p>
<table>
<thead>
<tr>
<th>Data</th>
<th>Bidone</th>
<th>Condomino</th>
</tr>
</thead>
<tbody>
"""
        
        for i, row in enumerate(dati[1:], 1):  # Salta header
            data = str(row.get('Data', ''))
            bidone = str(row.get('Bidone', ''))
            condomino = str(row.get('Condomino', ''))
            html += f"<tr><td>{data}</td><td>{bidone}</td><td>{condomino}</td></tr>\n"
        
        html += f"""</tbody>
</table>
<p style="font-size: 10px; color: #999; text-align: right; margin-top: 20px;">
Aggiornato al: {data_gen}
</p>
</body>
</html>"""
        return html

# --- CLASSE BOT PRINCIPALE ---
class GarbageBot:
    def __init__(self):
        self.log = logging.getLogger("GarbageBot")
        self.client = NewAClient(Config.DB_PATH_NEONIZE)
        self.sheet_client = GoogleSheetClient(Config.CREDENTIALS_FILE)
        self.config_db = BotConfigDB(Config.DB_PATH_CONFIG)
        self.calendar_manager = CalendarManager(Config.CREDENTIALS_FILE, self.sheet_client)
        self.calendar_gen = CalendarGenerator(self.sheet_client)
        
        # Tracking per monitoraggio calendario
        self.calendar_hash = None
        self.last_calendar_check = None
        
        self.me_user = None 
        self.me_lid = None
        
        self._register_events()

    def _register_events(self):
        self.client.event(ConnectedEv)(self.on_connected)
        self.client.event(MessageEv)(self.on_message)

    # --- HELPER ---
    async def _safe_reply(self, text: str, message: MessageEv, context: str):
        self.log.info(f"📤 [{context}] Risposta in corso...")
        try:
            await self.client.reply_message(text, message)
        except Exception as e:
            self.log.error(f"❌ [{context}] Errore invio: {e}")

    async def _safe_send(self, jid: JID, text: str, context: str):
        self.log.info(f"📤 [{context}] Invio diretto a {jid.User}...")
        try:
            await self.client.send_message(jid, text)
        except Exception as e:
            self.log.error(f"❌ [{context}] Errore invio: {e}")

    # --- RISOLUZIONE JID E NOME GRUPPO ---
    async def _resolve_group_data(self, group_link: str) -> tuple[Optional[JID], str]:
        try:
            invite_code = group_link.split("/")[-1]
            link_info = await self.client.get_group_info_from_link(invite_code)
            
            target_jid_obj = link_info.JID

            name = None
            try:
                metadata = await self.client.get_group_info(target_jid_obj)
                if hasattr(metadata, 'Subject'):
                    name = metadata.Subject
            except Exception as e:
                self.log.warning(f"Metadata fetch fallito: {e}")

            if not name:
                if hasattr(link_info, 'GroupName') and hasattr(link_info.GroupName, 'Name'):
                    name = link_info.GroupName.Name
            
            if isinstance(name, bytes):
                name = name.decode('utf-8')

            if not name:
                name = f"Gruppo {target_jid_obj.User}"

            self.log.info(f"🔎 Risolto: {target_jid_obj.User} - Nome: {name}")
            return target_jid_obj, str(name)

        except Exception as e:
            self.log.error(f"❌ Errore critico risoluzione link: {e}")
            return None, "Errore"

    # --- VERIFICA ADMIN ---
    def _is_owner_chat(self, message: MessageEv) -> bool:
        try:
            if not self.me_user:
                return False
            if message.Info.MessageSource.IsGroup:
                return False

            chat_jid = message.Info.MessageSource.Chat.User
            sender = message.Info.MessageSource.Sender
            sender_jid = sender.User if sender else chat_jid

            is_me = (sender_jid == self.me_user) or (self.me_lid and sender_jid == self.me_lid)
            return is_me and (chat_jid == sender_jid)

        except Exception as e:
            self.log.error(f"Errore check owner: {e}")
            return False

    def _get_commands_text(self, is_admin: bool = False) -> str:
        base = (
            "🤖 *Comandi Disponibili:*\n\n"
            "```\n"
            "/oggi      - Chi è di turno oggi\n"
            "/prossimi  - Prossimi turni\n"
            "/regole    - Regole e buone norme\n"
            "/calendario - Invia PDF calendario\n"
            "/info      - Mostra questo messaggio\n"
            "```"
        )
        if is_admin:
            admin_cmds = (
                "\n⚙️ *Amministrazione (Proprietario):*\n"
                "```\n"
                "/config              - Collega link gruppo/sheet\n"
                "/config_check        - Lista configurazioni\n"
                "/config_reset        - Rimuovi per ID (vedi check)\n"
                "/db_reset            - Pulisci e ricrea Database\n"
                "```"
            )
            return base + admin_cmds
        return base

    # --- EVENTI ---
    async def on_connected(self, client: NewAClient, __: ConnectedEv):
        self.log.info("⚡ Bot Connesso!")
        try:
            me_obj = await client.get_me()
            if hasattr(me_obj, 'JID'):
                self.me_user = me_obj.JID.User
                self.log.info(f"👤 Identità JID (Tel): {self.me_user}")
            if hasattr(me_obj, 'LID'):
                self.me_lid = me_obj.LID.User
                self.log.info(f"👤 Identità LID (ID): {self.me_lid}")
        except Exception as e:
            self.log.error(f"⚠️ Impossibile recuperare identità bot: {e}")

    async def on_message(self, client: NewAClient, message: MessageEv):
        text = (message.Message.conversation or message.Message.extendedTextMessage.text or "").strip()
        chat = message.Info.MessageSource.Chat
        is_group = message.Info.MessageSource.IsGroup
        
        if not text.startswith("/"):
            return

        command_parts = text.split()
        cmd = command_parts[0].lower()
        args = command_parts[1:]

        self.log.info(f"📨 Comando: '{cmd}' | Group: {is_group}")

        # --- 1. COMANDI AMMINISTRAZIONE ---
        admin_commands = ["/config", "/config_check", "/config_reset", "/db_reset"]

        if cmd in admin_commands:
            if not self._is_owner_chat(message):
                return

            if cmd == "/config":
                await self.handle_config(message, args)
            elif cmd == "/config_check":
                await self.handle_check_config(message)
            elif cmd == "/config_reset":
                await self.handle_reset_config(message, args)
            elif cmd == "/db_reset":
                await self.handle_db_reset(message)
            return

        # --- 2. COMANDI PUBBLICI ---
        if cmd == "/stato":
            await self._safe_reply("✅ Bot Operativo!", message, "/stato")

        elif cmd in ["/info", "/help"]:
            is_admin = self._is_owner_chat(message)
            await self.handle_help(message, is_admin)
        
        elif cmd == "/comandi":
             is_admin = self._is_owner_chat(message)
             await self._safe_reply(self._get_commands_text(is_admin), message, "/comandi")

        # --- 3. COMANDI TURNI ---
        elif cmd == "/oggi":
            await self.handle_oggi(message, chat.User, is_group)

        elif cmd == "/prossimi":
            await self.handle_prossimi(message, chat.User, is_group)
            
        elif cmd == "/regole":
            await self.handle_regole(message, chat.User, is_group)
        
        elif cmd == "/calendario":
            await self.handle_calendario(message, chat.User, is_group)

    # --- LOGICHE COMANDI ADMIN ---

    async def handle_db_reset(self, message: MessageEv):
        """Ricrea le tabelle del database (per aggiornamento schema)"""
        try:
            self.config_db.recreate_tables()
            await self._safe_reply("☢️ *Database Ricreato*\nTabelle pulite e schema aggiornato.\nLe configurazioni precedenti sono state cancellate.", message, "/db_reset")
        except Exception as e:
            self.log.error(f"DB Reset Error: {e}")
            await self._safe_reply("❌ Errore durante il reset del DB.", message, "/db_reset")

    async def handle_config(self, message: MessageEv, args: List[str]):
        if len(args) < 2:
            await self._safe_reply(
                "❌ *Sintassi Errata*\nUso: `/config <link_gruppo> <link_sheet>`", 
                message, "/config"
            )
            return

        group_link = args[0]
        sheet_url = args[1]

        if "chat.whatsapp.com" not in group_link:
             await self._safe_reply("⚠️ Il primo link deve essere un invito WhatsApp.", message, "/config")
             return
        
        if "docs.google.com" not in sheet_url:
             await self._safe_reply("⚠️ Il secondo link deve essere un Google Sheet.", message, "/config")
             return

        await self._safe_reply("⏳ Verifica gruppo in corso...", message, "/config")
        
        group_jid_obj, group_name = await self._resolve_group_data(group_link)

        if not group_jid_obj:
            await self._safe_reply("❌ Impossibile trovare il gruppo.", message, "/config")
            return

        try:
            self.config_db.set_config(group_jid_obj, sheet_url, group_name)
            await self._safe_reply(
                f"✅ *Configurazione Attivata!*\n\n"
                f"📂 *Gruppo:* {group_name}\n"
                f"🔗 *Sheet:* Collegato",
                message, "/config"
            )
        except Exception as e:
            self.log.error(f"DB Error: {e}")
            await self._safe_reply("❌ Errore nel salvataggio.", message, "/config")

    async def handle_check_config(self, message: MessageEv):
        configs = self.config_db.get_all_configs()
        if not configs:
            await self._safe_reply("ℹ️ Nessuna configurazione attiva.", message, "/config_check")
            return

        msg = "📋 *Gruppi Configurati:*\n\n"
        for i, (jid_str, url, name, _) in enumerate(configs, 1):
            group_display = name if name else f"ID: {jid_str}"
            msg += f"{i}. 📂 *{group_display}*\n   🔗 {url}\n\n"
        
        await self._safe_reply(msg, message, "/config_check")

    async def handle_reset_config(self, message: MessageEv, args: List[str]):
        if not args:
             await self._safe_reply("❌ Uso: `/config_reset <numero>`\nEsempio: `/config_reset 1` (vedi /config_check)", message, "/config_reset")
             return

        try:
            target_idx = int(args[0])
        except ValueError:
            await self._safe_reply("❌ Devi specificare un numero valido.", message, "/config_reset")
            return

        configs = self.config_db.get_all_configs()
        
        if target_idx < 1 or target_idx > len(configs):
            await self._safe_reply(f"❌ Indice {target_idx} non trovato. Usa /config_check per vedere la lista.", message, "/config_reset")
            return

        target_config = configs[target_idx - 1]
        target_jid_str = target_config[0]
        target_name = target_config[2]

        if self.config_db.delete_config(target_jid_str):
            await self._safe_reply(f"🗑️ Configurazione rimossa per *{target_name}*.", message, "/config_reset")
        else:
            await self._safe_reply(f"⚠️ Errore durante la rimozione.", message, "/config_reset")

    # --- LOGICHE COMANDI UTENTE ---

    async def handle_help(self, message: MessageEv, is_admin: bool):
        intro = (
            "🚮 *GarbageBot - Assistente Turni Raccolta Differenziata*\n\n"
            "Questo bot automatizza la gestione dei turni per l'esposizione dei bidoni condominiali della raccolta porta a porta.\n\n"
            "⚙️ *Funzionalità:*\n"
            "🔔 *Notifiche Automatiche:* Il bot invia autonomamente un promemoria alla persona di turno alle ore 9:00 il giorno dell'esposizione.\n"
            "🔍 *Consultazione:* Puoi interrogare il bot in qualsiasi momento usando i comandi sottostanti per verificare il calendario e i turni.\n\n"
            "👇 *Comandi*\n\n"
        )
        await self._safe_reply(intro + self._get_commands_text(is_admin), message, "/help")

    async def _check_group_config(self, chat_jid, message, cmd_context):
        sheet_url = self.config_db.get_sheet_url(chat_jid)
        if not sheet_url:
            return None
        return sheet_url

    async def handle_oggi(self, message: MessageEv, chat_jid: str, is_group: bool):
        if not is_group:
             await self._safe_reply("ℹ️ Comando disponibile solo nei gruppi configurati.", message, "/oggi")
             return

        sheet_url = await self._check_group_config(chat_jid, message, "/oggi")
        if not sheet_url: return

        oggi = datetime.now().strftime(Config.DATE_FORMAT)
        records = await self.sheet_client.get_records(sheet_url)
        
        for row in records:
            if str(row['Data']) == oggi:
                tipo = row.get('Bidone', '')
                msg_text = f"📅 Oggi tocca a {row['Condomino']}"
                if tipo:
                    msg_text += f" - Bidone: {tipo}"
                await self._safe_reply(msg_text, message, "/oggi")
                return
        
        await self._safe_reply("ℹ️ Nessun turno previsto per oggi.", message, "/oggi")

    async def handle_prossimi(self, message: MessageEv, chat_jid: str, is_group: bool):
        if not is_group:
             await self._safe_reply("ℹ️ Comando disponibile solo nei gruppi configurati.", message, "/prossimi")
             return

        sheet_url = await self._check_group_config(chat_jid, message, "/prossimi")
        if not sheet_url: return

        records = await self.sheet_client.get_records(sheet_url)
        oggi_dt = datetime.now().date()
        futuri = []

        for row in records:
            try:
                data_row = datetime.strptime(str(row['Data']), Config.DATE_FORMAT).date()
                if data_row >= oggi_dt:
                    futuri.append(row)
            except ValueError:
                continue 

        if not futuri:
            await self._safe_reply("ℹ️ Non ci sono turni futuri.", message, "/prossimi")
            return

        prossimi = futuri[:10]
        messaggio = f"📅 *Prossimi Turni:* \n\n"
        for i, turno in enumerate(prossimi, 1):
            data_str = str(turno['Data'])
            tipo = turno.get('Bidone', '')
            try:
                dt_obj = datetime.strptime(data_str, Config.DATE_FORMAT)
                data_display = dt_obj.strftime("%d/%m")
            except ValueError:
                data_display = data_str

            messaggio += f"- {data_display}: *{turno['Condomino']}* ({tipo})\n"
        
        await self._safe_reply(messaggio, message, "/prossimi")

    async def handle_regole(self, message: MessageEv, chat_jid: str, is_group: bool):
        if not is_group:
             await self._safe_reply("ℹ️ Comando disponibile solo nei gruppi configurati.", message, "/regole")
             return

        sheet_url = await self._check_group_config(chat_jid, message, "/regole")
        if not sheet_url: return

        rules_text = await self.sheet_client.get_rules_text(sheet_url)
        header = "📋 *Regolamento Condominiale Rifiuti*\n\n"
        await self._safe_reply(header + rules_text, message, "/regole")

    async def handle_calendario(self, message: MessageEv, chat_jid: str, is_group: bool):
        """Invia il PDF del calendario aggiornato (comando manuale)
        - Admin: reset + regenerate calendar, invia PDF in privata
        - Utente: invia PDF attuale nel gruppo
        """
        is_admin = self._is_owner_chat(message)
        
        # Se admin, rigeneran il calendario da zero
        if is_admin:
            try:
                await self._safe_reply("⏳ Rigenerazione calendario in corso...", message, "/calendario")
                
                configs = self.config_db.get_all_configs()
                if not configs:
                    await self._safe_reply("❌ Nessuna configurazione trovata. Usa `/config` per collegare un foglio.", message, "/calendario")
                    return
                
                sheet_url = configs[0][1]
                
                # Rigeneran il calendario da zero
                success = await self.calendar_gen.reset_and_generate_calendar(sheet_url)
                
                if success:
                    # Genera e invia il PDF in privata
                    pdf_bytes = await self.calendar_gen.generate_pdf(sheet_url)
                    
                    if pdf_bytes:
                        # Invia sulla chat privata del bot
                        if self.me_user:
                            bot_jid = JID()
                            bot_jid.User = self.me_user
                            caption = "📅 *Calendario Rigenerato*\n\nNuovo calendario creato in base alle condomini attuali."
                            
                            # Costruisci il messaggio documento
                            doc_msg = self.client.build_document_message(
                                pdf_bytes,
                                filename="Calendario_Turni.pdf",
                                caption=caption,
                                mime_type="application/pdf"
                            )
                            
                            # Invia il documento
                            await self.client.send_message(bot_jid, message=doc_msg)
                            self.log.info("✅ PDF inviato sulla chat privata")
                        
                        await self._safe_reply("✅ *Calendario Rigenerato!*\n\nIl nuovo calendario è stato creato con i condomini attuali e il PDF è stato inviato in privata.", message, "/calendario")
                    else:
                        await self._safe_reply("⚠️ Calendario rigenerato ma errore nella generazione del PDF.", message, "/calendario")
                else:
                    await self._safe_reply("❌ Errore durante la rigenerazione del calendario.", message, "/calendario")
                    
            except Exception as e:
                self.log.error(f"Errore rigenerazione: {e}")
                await self._safe_reply(f"❌ Errore: {str(e)}", message, "/calendario")
        
        # Se utente normale, invia PDF nel gruppo
        else:
            if not is_group:
                 await self._safe_reply("ℹ️ Comando disponibile solo nei gruppi configurati.", message, "/calendario")
                 return

            sheet_url = await self._check_group_config(chat_jid, message, "/calendario")
            if not sheet_url: return
            
            # Avvisa che sta generando il PDF
            await self._safe_reply("⏳ Generazione PDF in corso...", message, "/calendario")
            
            try:
                # Genera il PDF
                pdf_bytes = await self.calendar_gen.generate_pdf(sheet_url)
                
                if not pdf_bytes:
                    await self._safe_reply("❌ Errore nella generazione del PDF.", message, "/calendario")
                    return
                
                # Costruisci il messaggio documento
                caption = "📅 *Calendario Turni - Stampa e Affiggere*"
                doc_msg = self.client.build_document_message(
                    pdf_bytes,
                    filename="Calendario_Turni.pdf",
                    caption=caption,
                    mime_type="application/pdf"
                )
                
                # Invia il PDF nel gruppo
                await self.client.send_message(
                    message.Info.MessageSource.Chat,
                    message=doc_msg
                )
                self.log.info(f"✅ PDF calendario inviato nel gruppo")
                        
            except Exception as e:
                self.log.error(f"❌ Errore invio PDF: {e}")
                await self._safe_reply(f"❌ Errore: {str(e)}", message, "/calendario")

    # --- SCHEDULER ---
    def _calculate_calendar_hash(self, calendario_data: List[Dict]) -> str:
        """Calcola l'hash del calendario per rilevare cambiamenti"""
        try:
            data_str = json.dumps(calendario_data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except:
            return ""

    async def monitor_and_send_calendar(self):
        """Monitora il calendario e invia PDF se:
        1. Il calendario è stato modificato (cambio ordine partecipanti)
        2. Mancano <= 30 giorni dalla fine del ciclo
        """
        self.log.info("📅 Monitor Calendario avviato")
        
        while True:
            try:
                configs = self.config_db.get_all_configs()
                if not configs:
                    await asyncio.sleep(300)  # Check ogni 5 minuti se nessun config
                    continue
                
                # Usa il primo config come foglio principale
                sheet_url = configs[0][1]
                
                # 1. Leggi il calendario
                calendario_data = await self.sheet_client.get_records(sheet_url)
                current_hash = self._calculate_calendar_hash(calendario_data)
                
                # 2. Verifica cambiamenti
                calendar_changed = (self.calendar_hash is None or 
                                   self.calendar_hash != current_hash)
                
                # 3. Controlla se serve generare nuovo ciclo
                calendar_needs_generation = self.calendar_gen._check_calendar_needs_generation(
                    calendario_data
                )
                
                if calendar_changed:
                    self.log.info("🔄 Calendario modificato!")
                    self.calendar_hash = current_hash
                
                # Traccia se è necessaria una generazione automatica (per notificare gruppo)
                automatic_cycle_generated = False
                
                if calendar_needs_generation:
                    self.log.info("⏰ Mancano <= 30 giorni, generazione nuovo ciclo...")
                    generated = await self.calendar_gen.generate_calendar(sheet_url)
                    
                    if generated:
                        # Rileggi dopo generazione
                        calendario_data = await self.sheet_client.get_records(sheet_url)
                        current_hash = self._calculate_calendar_hash(calendario_data)
                        self.calendar_hash = current_hash
                        automatic_cycle_generated = True
                
                # 4. Se nuovo ciclo generato automaticamente, invia notifica e PDF in privata
                if automatic_cycle_generated:
                    self.log.info("📤 Invio notifica e PDF in privata...")
                    await self._send_calendar_pdf(sheet_url)
                # Se solo cambio dati (non generazione), silent
                elif calendar_changed:
                    self.log.info("🔄 Cambio dati silenzioso (nessuna notifica)")
                    pass
                
                await asyncio.sleep(300)  # Check ogni 5 minuti
                
            except Exception as e:
                self.log.error(f"❌ Errore monitor calendario: {e}")
                await asyncio.sleep(300)

    async def _send_calendar_pdf(self, sheet_url: str):
        """Genera e invia il PDF del calendario su WhatsApp (chat privata bot) - NON nel gruppo"""
        try:
            # 1. Genera PDF
            pdf_bytes = await self.calendar_gen.generate_pdf(sheet_url)
            
            if not pdf_bytes:
                self.log.error("❌ PDF non generato")
                return
            
            # 2. Invia sulla chat privata del bot (usa me_user)
            if self.me_user:
                bot_jid = JID()
                bot_jid.User = self.me_user
                
                # Costruisci il messaggio documento con il PDF
                caption = "📅 *Calendario Turni Aggiornato*\n\nNuovo ciclo generato e pronto per la stampa."
                doc_msg = self.client.build_document_message(
                    pdf_bytes,
                    filename="Calendario_Turni.pdf",
                    caption=caption,
                    mime_type="application/pdf"
                )
                
                # Invia il documento
                await self.client.send_message(bot_jid, message=doc_msg)
                self.log.info(f"✅ PDF inviato sulla chat privata del bot")
            else:
                self.log.warning("⚠️ JID bot non disponibile")
                    
        except Exception as e:
            self.log.error(f"❌ Errore invio PDF: {e}")

    async def reminder_scheduler(self):
        self.log.info("⏰ Scheduler Multi-Gruppo avviato.")
        
        while True:
            try:
                # --- REMINDER A ORARIO FISSO (09:00) ---
                now_time = datetime.now().strftime("%H:%M")
                if now_time == "09:00":
                    self.log.info("🔔 ORARIO REMINDER (09:00)")
                    configs = self.config_db.get_all_configs()
                    oggi = datetime.now().strftime(Config.DATE_FORMAT)

                    for (jid_str, sheet_url, _, jid_blob) in configs:
                        self.log.info(f"🔄 Check gruppo {jid_str}...")
                        records = await self.sheet_client.get_records(sheet_url)
                        
                        try:
                            # Ricostruzione JID dal BLOB del database
                            target_jid = JID()
                            target_jid.ParseFromString(jid_blob)
                        except Exception as e:
                            self.log.error(f"Errore deserializzazione JID: {e}")
                            continue

                        for row in records:
                            if str(row['Data']) == oggi:
                                bidone = row.get('Bidone', 'rifiuti')
                                msg = f"Ciao @{row['Telefono']} 👋,\nricordati che stasera tocca a te esporre il bidone della {bidone}! 🗑️"
                                await self._safe_send(target_jid, msg, f"Reminder-{jid_str}")

                    await asyncio.sleep(61) 
                
                await asyncio.sleep(30)
            except Exception as e:
                self.log.error(f"❌ Errore Scheduler: {e}")
                await asyncio.sleep(60)

    async def start(self):
        asyncio.create_task(self.reminder_scheduler())
        asyncio.create_task(self.monitor_and_send_calendar())
        self.log.info("🚀 Avvio...")
        await self.client.connect()
        await self.client.idle()

if __name__ == "__main__":
    logging.basicConfig(level=Config.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    bot = GarbageBot()

    def handle_exit(*args):
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)

    try:
        bot.client.loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        pass