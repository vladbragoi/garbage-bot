import asyncio
import logging
import sys
import signal
import sqlite3
import json
import socket
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple, Callable
from io import BytesIO
from dataclasses import dataclass

# Librerie Esterne
import gspread
from google.oauth2.service_account import Credentials
from xhtml2pdf.document import pisaDocument
from neonize.aioze.client import NewAClient
from neonize.aioze.events import ConnectedEv, MessageEv
from neonize.proto.Neonize_pb2 import JID

# --- NETWORK FIX ---
socket.setdefaulttimeout(60)

# --- CONFIGURAZIONE ---
@dataclass
class AppConfig:
    DB_PATH_NEONIZE: str = "/data/garbage_bot.sqlite"
    DB_PATH_CONFIG: str = "/data/garbage_bot_config.sqlite"
    CREDENTIALS_FILE: str = "/data/credentials.json"
    DATE_FORMAT: str = "%d/%m/%Y"
    LOG_LEVEL: int = logging.INFO
    COLOR_PRIMARY: str = "#356854"
    COLOR_ALTERNATE: str = "#f2f2f2"
    ADMIN_NUMBERS: Tuple[str, ...] = ("393508950370", "117584041140339")

config = AppConfig()

# --- REPOSITORY ---
class ConfigRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS group_configs (
                    jid TEXT PRIMARY KEY,
                    sheet_url TEXT NOT NULL,
                    group_link TEXT,
                    group_name TEXT,
                    jid_data BLOB
                )
            ''')

    def recreate_tables(self):
        with self._get_connection() as conn:
            conn.execute('DROP TABLE IF EXISTS group_configs')
        self._init_db()

    def upsert_config(self, jid_obj: JID, sheet_url: str, group_link: str, group_name: str = ""):
        jid_str = jid_obj.User
        jid_bytes = jid_obj.SerializeToString()
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO group_configs (jid, sheet_url, group_link, group_name, jid_data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(jid) DO UPDATE SET 
                    sheet_url=excluded.sheet_url, 
                    group_link=excluded.group_link,
                    group_name=excluded.group_name,
                    jid_data=excluded.jid_data
            ''', (jid_str, sheet_url, group_link, group_name, jid_bytes))

    def delete_config(self, jid: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute('DELETE FROM group_configs WHERE jid = ?', (jid,))
            return cur.rowcount > 0

    def get_sheet_url(self, jid: str) -> Optional[str]:
        with self._get_connection() as conn:
            cur = conn.execute('SELECT sheet_url FROM group_configs WHERE jid = ?', (jid,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_all_configs(self) -> List[Tuple]:
        with self._get_connection() as conn:
            cur = conn.execute('SELECT jid, sheet_url, group_link, group_name, jid_data FROM group_configs')
            return cur.fetchall()

# --- SHEET SERVICE ---
class SheetService:
    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.log = logging.getLogger("SheetService")
        self._scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

    def _get_client(self):
        creds = Credentials.from_service_account_file(
            self.credentials_file, 
            scopes=self._scope
        )
        return gspread.authorize(creds)

    async def get_records(self, sheet_url: str, worksheet_name: str = "Calendario") -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_records_sync, sheet_url, worksheet_name)

    def _get_records_sync(self, sheet_url: str, worksheet_name: str) -> List[Dict[str, Any]]:
        try:
            gc = self._get_client()
            ws = gc.open_by_url(sheet_url).worksheet(worksheet_name)
            return ws.get_all_records()
        except Exception as e:
            self.log.error(f"Errore download dati: {e}")
            return []

    async def get_rules(self, sheet_url: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._get_rules_sync, sheet_url)

    def _get_rules_sync(self, sheet_url: str) -> str:
        try:
            gc = self._get_client()
            sheet = gc.open_by_url(sheet_url).worksheet("Regole")
            rows = sheet.get_all_values()
            return "\n".join([" ".join([c for c in row if c.strip()]) for row in rows if any(row)])
        except Exception:
            return "⚠️ Impossibile recuperare le regole."

# --- CALENDAR SERVICE ---
class CalendarService:
    def __init__(self, sheet_service: SheetService):
        self.sheet = sheet_service
        self.log = logging.getLogger("CalendarService")

    # --- PDF ---
    def _generate_html_template(self, dati: List[Dict], title: str = "Calendario Turni") -> str:
        data_gen = datetime.now().strftime("%d/%m/%Y %H:%M")
        rows_html = ""
        for i, row in enumerate(dati):
            d = str(row.get('Data', '')).strip()
            b = str(row.get('Bidone', '')).strip()
            c = str(row.get('Condomino', '')).strip()
            if not d or not c: continue
            bg_color = config.COLOR_ALTERNATE if i % 2 == 0 else "#ffffff"
            style_td = f"background-color: {bg_color}; text-align: center; vertical-align: middle; padding-top: 4px; padding-bottom: 4px;"
            rows_html += f'<tr><td style="{style_td}">{d}</td><td style="{style_td}">{b}</td><td style="{style_td}">{c}</td></tr>\n'
        return f"""<html><head><meta charset="UTF-8"><style>@page {{ size: a4; margin: 1cm; }} table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #dddddd; padding: 4px; text-align: center; vertical-align: middle; font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.2; }} th {{ background-color: {config.COLOR_PRIMARY} !important; color: white !important; padding-top: 6px; padding-bottom: 6px; }}</style></head><body><h1 style="color: {config.COLOR_PRIMARY}; text-align: center; font-family: Arial; font-size: 14pt;">{title}</h1><table><thead><tr><th style="width: 22%;">Data</th><th style="width: 25%;">Bidone</th><th style="width: 53%;">Condomino</th></tr></thead><tbody>{rows_html}</tbody></table><p style="font-family: Arial; font-size: 7pt; color: #999; text-align: right; margin-top: 10px;">Aggiornato al: {data_gen}</p></body></html>"""

    async def generate_pdf(self, sheet_url: str, worksheet_name: str = "Calendario") -> Optional[bytes]:
        try:
            records = await self.sheet.get_records(sheet_url, worksheet_name)
            if len(records) < 1: return None
            
            title_text = "Calendario Turni"
            html = self._generate_html_template(records, title=title_text)
            
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._convert_html_to_pdf, html)
        except Exception as e:
            self.log.error(f"PDF Gen Error: {e}")
            return None

    def _convert_html_to_pdf(self, html: str) -> Optional[bytes]:
        buffer = BytesIO()
        pisa_status = pisaDocument(BytesIO(html.encode('utf-8')), buffer)
        return None if pisa_status.err else buffer.getvalue()

    # --- HELPERS DATA ---
    def _get_first_monday_of_year(self, year: int) -> date:
        jan_1 = date(year, 1, 1)
        days_to_monday = (0 - jan_1.weekday()) % 7
        return jan_1 + timedelta(days=days_to_monday)

    def _get_next_monday(self, from_date: date) -> date:
        next_date = from_date + timedelta(days=1)
        while next_date.weekday() != 0:
            next_date += timedelta(days=1)
        return next_date

    # --- LIFECYCLE (Scheduler) ---
    async def manage_lifecycle(self, sheet_url: str) -> str:
        loop = asyncio.get_running_loop()
        try:
            records = await self.sheet.get_records(sheet_url)
            
            if not records:
                self.log.info("⚠️ Calendario vuoto. Inizializzo.")
                start_dt = self._get_first_monday_of_year(datetime.now().year)
                await self.create_next_cycle_sheet(sheet_url, "Calendario", start_dt)
                return "Inizializzato"

            last_row = records[-1]
            try:
                last_dt = datetime.strptime(str(last_row['Data']), config.DATE_FORMAT).date()
            except:
                return "Errore Data ultima riga"

            today = datetime.now().date()
            days_left = (last_dt - today).days

            if days_left < 0:
                self.log.info("🔴 Ciclo scaduto. Ruoto fogli.")
                await loop.run_in_executor(None, self._rotate_sheets_sync, sheet_url, records)
                return "Ruotato (Archiviato -> Promosso)"

            elif days_left <= 30:
                exists = await loop.run_in_executor(None, self._check_sheet_exists_sync, sheet_url, "NuovoCalendario")
                
                if not exists:
                    self.log.info(f"🟠 Scadenza vicina ({days_left}gg). Creo NuovoCalendario.")
                    
                    condomini = await loop.run_in_executor(None, self._fetch_condomini_sync, sheet_url)
                    last_name = str(last_row['Condomino'])
                    next_idx = self._find_next_condomino_index(last_name, condomini)
                    next_start = self._get_next_monday(last_dt)
                    
                    await self.create_next_cycle_sheet(sheet_url, "NuovoCalendario", next_start, next_idx)
                    return "Creato NuovoCalendario"
                else:
                    return "NuovoCalendario già presente (Skip)"
            
            return f"Attivo ({days_left}gg mancanti)"

        except Exception as e:
            self.log.exception(f"Errore Lifecycle: {e}")
            return "Errore"

    # --- MANUTENZIONE MANUALE (/genera) ---
    async def manual_fix_current_cycle(self, sheet_url: str) -> bool:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._truncate_future_sync, sheet_url)
            condomini = await loop.run_in_executor(None, self._fetch_condomini_sync, sheet_url)
            
            start_date = self._get_next_monday(datetime.now().date())
            next_idx = 0 
            
            turni = self._calculate_shifts_cycle(condomini, start_date, next_idx)
            
            await loop.run_in_executor(None, self._append_shifts_sync, sheet_url, "Calendario", turni)
            await loop.run_in_executor(None, self._format_sheet_sync, sheet_url, "Calendario")

            await loop.run_in_executor(None, self._delete_sheet_sync, sheet_url, "NuovoCalendario")
            
            return True
        except Exception as e:
            self.log.error(f"Manual Fix Error: {e}")
            return False

    # --- MANUTENZIONE MANUALE (/genera nuovi) ---
    async def manual_regenerate_new_cycle(self, sheet_url: str) -> bool:
        loop = asyncio.get_running_loop()
        try:
            records = await self.sheet.get_records(sheet_url)
            condomini = await loop.run_in_executor(None, self._fetch_condomini_sync, sheet_url)

            if not condomini:
                self.log.error("Nessun condomino trovato in Impostazioni.")
                return False

            start_date = self._get_next_monday(datetime.now().date())
            next_idx = 0

            if records:
                last_row = records[-1]
                try:
                    last_dt = datetime.strptime(str(last_row['Data']), config.DATE_FORMAT).date()
                    start_date = self._get_next_monday(last_dt)
                    next_idx = self._find_next_condomino_index(str(last_row['Condomino']), condomini)
                except Exception as e:
                    self.log.warning(f"Impossibile leggere ultima riga Calendario: {e}")

            await self.create_next_cycle_sheet(sheet_url, "NuovoCalendario", start_date, next_idx)
            return True
        except Exception as e:
            self.log.error(f"Manual Regenerate New Cycle Error: {e}")
            return False

    async def create_next_cycle_sheet(self, sheet_url: str, target_sheet: str, start_date: date, start_idx: int = 0):
        loop = asyncio.get_running_loop()
        condomini = await loop.run_in_executor(None, self._fetch_condomini_sync, sheet_url)
        if not condomini: return

        turni = self._calculate_shifts_cycle(condomini, start_date, start_idx)
        
        await loop.run_in_executor(None, self._overwrite_sheet_sync, sheet_url, target_sheet, turni)
        await loop.run_in_executor(None, self._format_sheet_sync, sheet_url, target_sheet)

    def _calculate_shifts_cycle(self, condomini: List[tuple], start_date: date, start_idx: int) -> List[List[str]]:
        turni = []
        curr_date = start_date
        num = len(condomini)
        
        for i in range(num):
            idx = (start_idx + i) % num
            name, phone = condomini[idx]
            turni.append([curr_date.strftime(config.DATE_FORMAT), 'plastica', name, phone])
            turni.append([(curr_date + timedelta(days=1)).strftime(config.DATE_FORMAT), 'carta', name, phone])
            curr_date += timedelta(days=7)
        return turni

    def _find_next_condomino_index(self, last_name: str, condomini: List[tuple]) -> int:
        try:
            curr_idx = next(i for i, v in enumerate(condomini) if v[0].lower().strip() == last_name.lower().strip())
            return (curr_idx + 1) % len(condomini)
        except StopIteration:
            return 0

    # --- GSPREAD SYNC METHODS ---
    def _fetch_condomini_sync(self, sheet_url: str) -> List[tuple]:
        gc = self.sheet._get_client()
        ws = gc.open_by_url(sheet_url).worksheet("Impostazioni")
        raw = ws.get("A2:B1000")
        return [(r[0], r[1] if len(r) > 1 else "") for r in raw if r and r[0].strip()]

    def _rotate_sheets_sync(self, sheet_url: str, current_records: List[Dict]):
        gc = self.sheet._get_client()
        ss = gc.open_by_url(sheet_url)
        try:
            start = current_records[0]['Data'].replace('/', '-')
            end = current_records[-1]['Data'].replace('/', '-')
            archive_name = f"Archivio_{start}_{end}"
        except:
            archive_name = f"Archivio_{datetime.now().strftime('%Y%m%d')}"

        try:
            ws_cal = ss.worksheet("Calendario")
            ws_cal.update_title(archive_name)
        except: pass

        try:
            ws_new = ss.worksheet("NuovoCalendario")
            ws_new.update_title("Calendario")
        except gspread.WorksheetNotFound:
            ss.add_worksheet("Calendario", 1000, 4)

    def _truncate_future_sync(self, sheet_url: str) -> Optional[Dict]:
        gc = self.sheet._get_client()
        ws = gc.open_by_url(sheet_url).worksheet("Calendario")
        all_values = ws.get_all_records()
        today = datetime.now().date()
        keep = []
        for row in all_values:
            try:
                if datetime.strptime(str(row['Data']), config.DATE_FORMAT).date() <= today:
                    keep.append(row)
            except: pass
        ws.clear()
        ws.append_row(["Data", "Bidone", "Condomino", "Telefono"])
        rows = [[r['Data'], r['Bidone'], r['Condomino'], r['Telefono']] for r in keep]
        if rows:
            ws.append_rows(rows)
            return keep[-1]
        return None

    def _overwrite_sheet_sync(self, sheet_url: str, title: str, rows: List[List[str]]):
        gc = self.sheet._get_client()
        ss = gc.open_by_url(sheet_url)
        try:
            ws = ss.worksheet(title)
            ws.clear()
        except:
            ws = ss.add_worksheet(title, 1000, 4)
        ws.update(values=[["Data", "Bidone", "Condomino", "Telefono"]], range_name="A1:D1")
        if rows: ws.append_rows(rows)

    def _append_shifts_sync(self, sheet_url: str, title: str, rows: List[List[str]]):
        gc = self.sheet._get_client()
        ws = gc.open_by_url(sheet_url).worksheet(title)
        ws.append_rows(rows)

    def _format_sheet_sync(self, sheet_url: str, title: str):
        gc = self.sheet._get_client()
        ss = gc.open_by_url(sheet_url)
        ws = ss.worksheet(title)
        sid = ws._properties['sheetId']
        reqs = [
            {"updateCells": {"range": {"sheetId": sid, "startRowIndex": 0, "endColumnIndex": 4}, "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)", "rows": [{"values": [{"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 11}}} for _ in range(4)]} for _ in range(len(ws.get_all_values()))]}},
            {"autoResizeDimensions": {"dimensions": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 4}}},
            {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"addBanding": {"bandedRange": {"range": {"sheetId": sid, "startRowIndex": 1, "endColumnIndex": 4}, "rowProperties": {"firstBandColor": {"red": 1, "green": 1, "blue": 1}, "secondBandColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}}}}
        ]
        try:
            ss.batch_update({"requests": reqs})
        except Exception: pass 

    def _check_sheet_exists_sync(self, sheet_url: str, title: str) -> bool:
        gc = self.sheet._get_client()
        ss = gc.open_by_url(sheet_url)
        try:
            ss.worksheet(title)
            return True
        except: return False

    def _delete_sheet_sync(self, sheet_url: str, title: str):
        gc = self.sheet._get_client()
        ss = gc.open_by_url(sheet_url)
        try:
            ws = ss.worksheet(title)
            ss.del_worksheet(ws)
        except: pass

# --- MAIN BOT CLASS ---
# --- MAIN BOT CLASS ---
class GarbageBot:
    def __init__(self):
        self.log = logging.getLogger("GarbageBot")
        self.client = NewAClient(config.DB_PATH_NEONIZE)
        self.repo = ConfigRepository(config.DB_PATH_CONFIG)
        self.sheet_service = SheetService(config.CREDENTIALS_FILE)
        self.calendar_service = CalendarService(self.sheet_service)
        self.me: Optional[JID] = None
        self.command_handlers: Dict[str, Callable] = {
            '/oggi': self.cmd_oggi,
            '/prossimi': self.cmd_prossimi,
            '/regole': self.cmd_regole,
            '/calendario': self.cmd_calendario,
            '/genera': self.cmd_genera,
            '/info': self.cmd_help,
            '/help': self.cmd_help,
            '/comandi': self.cmd_help,
            '/attiva': self.cmd_attiva,
            '/disattiva': self.cmd_disattiva,        # NUOVO COMANDO
            '/config': self.cmd_admin_config,
            '/config_check': self.cmd_admin_check,
            '/config_reset': self.cmd_admin_reset,
            '/db_reset': self.cmd_admin_db_reset,
        }
        self._register_events()

    def _register_events(self):
        self.client.event(ConnectedEv)(self.on_connected)
        self.client.event(MessageEv)(self.on_message)

    async def on_connected(self, client: NewAClient, __: ConnectedEv):
        self.log.info("⚡ Bot Connesso!")
        me_obj = await client.get_me()
        if hasattr(me_obj, 'JID'):
            self.me = me_obj.JID
            self.log.info(f"👤 Bot JID: {self.me.User}")

    async def on_message(self, client: NewAClient, message: MessageEv):
        try:
            txt = (message.Message.conversation or message.Message.extendedTextMessage.text or "").strip()
            if not txt.startswith("/"): return
            args = txt.split()
            cmd = args[0].lower()
            handler = self.command_handlers.get(cmd)
            if handler:
                self.log.info(f"📨 Executing {cmd}")
                await handler(message, args[1:])
        except Exception as e:
            self.log.exception(f"❌ CRITICAL ERROR in on_message: {e}")

    async def _reply(self, text: str, msg: MessageEv):
        try:
            await self.client.reply_message(text, msg)
        except Exception as e:
            self.log.error(f"Reply error: {e}")

    async def _send_private(self, jid: JID, text: str = None, doc: bytes = None, filename: str = None):
        clean_jid = JID(User=jid.User, Server=jid.Server, Device=0, Integrator=0, RawAgent=0)
        try:
            if doc:
                msg = await self.client.build_document_message(doc, filename, text, "application/pdf")
                await self.client.send_message(clean_jid, message=msg)
            else:
                await self.client.send_message(clean_jid, text)
        except Exception as e:
            self.log.error(f"Send error: {e}")

    async def _is_group_admin(self, group_jid: JID, user_phone: str) -> bool:
        try:
            group_info = await self.client.get_group_info(group_jid)
            for participant in group_info.Participants:
                if participant.JID.User == user_phone:
                    return participant.IsSuperAdmin or participant.IsAdmin
            return False
        except Exception as e:
            self.log.error(f"Errore verifica admin gruppo: {e}")
            return False

    def _is_admin(self, msg: MessageEv) -> bool:
        try:
            if msg.Info.MessageSource.IsGroup:
                sender = msg.Info.MessageSource.Sender.User
            else:
                sender = msg.Info.MessageSource.Chat.User
            if sender in config.ADMIN_NUMBERS: return True
            if self.me and sender == self.me.User: return True
            self.log.warning(f"Tentativo accesso admin negato da: {sender}")
            return False
        except Exception: return False

    async def _get_sheet_context(self, msg: MessageEv) -> Optional[str]:
        if not msg.Info.MessageSource.IsGroup:
            await self._reply("ℹ️ Comando disponibile solo nei gruppi.", msg)
            return None
        chat_jid = msg.Info.MessageSource.Chat.User
        url = self.repo.get_sheet_url(chat_jid)
        if not url:
            self.log.warning(f"Gruppo {chat_jid} non configurato.")
            await self._reply("⚠️ Gruppo non configurato. Chiedi a un amministratore di usare `/attiva <link_sheet>`.", msg)
            return None
        return url

    async def _check_genera_permission(self, msg: MessageEv) -> bool:
        sender_phone = msg.Info.MessageSource.Sender.User
        group_jid = msg.Info.MessageSource.Chat
        is_group_admin = await self._is_group_admin(group_jid, sender_phone)
        is_bot_owner = self._is_admin(msg)
        if not is_group_admin and not is_bot_owner:
            await self._reply(
                "⛔ *Accesso Negato*\nSolo gli amministratori del gruppo possono usare questo comando.",
                msg
            )
            return False
        return True

    def _get_detailed_help(self, is_admin: bool, is_grp_admin: bool) -> str:
        base = (
            "🚮 *GarbageBot - Assistente Turni*\n\n"
            "Gestione automatizzata dei turni per l'esposizione dei bidoni.\n\n"
            "👇 *Comandi Disponibili*\n\n"
            "📅 */oggi*\n_Mostra chi è di turno oggi_\n\n"
            "🔜 */prossimi*\n_Visualizza i prossimi 10 turni_\n\n"
            "📜 */regole*\n_Leggi il regolamento rifiuti_\n\n"
            "📥 */calendario*\n_Scarica il PDF aggiornato_\n\n"
            "🔧 */genera*\n_Corregge il futuro dell'attuale ciclo dei turni (solo per amministratori del gruppo)_\n\n"
            "🆕 */genera nuovi*\n_Crea una nuova turnazione partendo dalla fine del ciclo attuale (solo per amministratori del gruppo)_\n\n"
            "ℹ️ */info*\n_Mostra questo messaggio_"
        )
        if is_grp_admin:
            base += (
                "\n\n⚙️ *Comandi Amministratore*\n──────────────────\n"
                "🔗 */attiva* `<link_sheet>`\n_Attiva il bot per il gruppo corrente (da usare nel gruppo)_\n\n"
                "🚫 */disattiva*\n_Disattiva il bot nel gruppo corrente (da usare nel gruppo)_"
            )
        if is_admin: 
            base += (
                "\n\n🔗 */config* `<link_gruppo>` `<link_sheet>`\n_Configura il bot via link (da usare in chat privata col bot)_\n\n"
                "📋 */config_check*\n_Lista delle configurazioni attive_\n\n"
                "🗑️ */config_reset* `numero`\n_Rimuove una configurazione specifica_\n\n"
                "☢️ */db_reset*\n_Pulisce e ricrea il database_"
            )
        return base

    async def cmd_oggi(self, msg: MessageEv, _):
        url = await self._get_sheet_context(msg)
        if not url: return
        oggi = datetime.now().strftime(config.DATE_FORMAT)
        records = await self.sheet_service.get_records(url)
        found = next((r for r in records if str(r['Data']) == oggi), None)
        if found: await self._reply(f"📅 *Oggi ({oggi})*\n👤 {found['Condomino']}\n🗑️ {found.get('Bidone','')}", msg)
        else: await self._reply("ℹ️ Nessun turno oggi.", msg)

    async def cmd_prossimi(self, msg: MessageEv, _):
        url = await self._get_sheet_context(msg)
        if not url: return
        records = await self.sheet_service.get_records(url)
        oggi = datetime.now().date()
        futuri = []
        for r in records:
            try:
                if datetime.strptime(str(r['Data']), config.DATE_FORMAT).date() >= oggi:
                    futuri.append(r)
            except: continue
        if not futuri:
            await self._reply("ℹ️ Fine calendario.", msg)
            return
        txt = "📅 *Prossimi Turni:*\n" + "\n".join([f"- {r['Data'][:5]}: *{r['Condomino']}* ({r['Bidone']})" for r in futuri[:10]])
        await self._reply(txt, msg)

    async def cmd_regole(self, msg: MessageEv, _):
        url = await self._get_sheet_context(msg)
        if not url: return
        regole = await self.sheet_service.get_rules(url)
        await self._reply(f"📋 *Regolamento*\n\n{regole}", msg)

    async def cmd_calendario(self, msg: MessageEv, args: List[str]):
        """Gestisce /calendario [pdf|scarica|download]."""
        if not msg.Info.MessageSource.IsGroup:
            await self._reply("❌ Comando disponibile solo nei gruppi.", msg)
            return
        url = await self._get_sheet_context(msg)
        if not url: return

        action = args[0].lower() if args else "pdf"
        if action in ["nuovo", "new", "reset", "rigenera"]:
            await self._reply(
                "ℹ️ Questo sotto-comando è stato spostato.\n"
                "• Usa */genera* per correggere il ciclo corrente.\n"
                "• Usa */genera nuovi* per generare un nuovo ciclo successivo al corrente.",
                msg
            )
            return

        if action in ["pdf", "scarica", "download"]:
            await self._reply("⏳ Generazione PDF...", msg)
            pdf = await self.calendar_service.generate_pdf(url)
            if pdf:
                doc_msg = await self.client.build_document_message(pdf, "CalendarioTurni.pdf", "📅 *Calendario Turni*", "application/pdf")
                await self.client.send_message(msg.Info.MessageSource.Chat, message=doc_msg)
            else:
                await self._reply("❌ Impossibile generare il PDF.", msg)
        else:
            await self._reply("❓ Sotto-comando non riconosciuto. Usa `/calendario` per il PDF.", msg)

    async def cmd_genera(self, msg: MessageEv, args: List[str]):
        """
        /genera          → Corregge il ciclo corrente, rigenera da 0 il prossimo lunedì e invia il PDF.
        /genera nuovi    → Crea o sovrascrive NuovoCalendario partendo dall'ultimo turno e invia il PDF.
        """
        if not msg.Info.MessageSource.IsGroup:
            await self._reply("❌ Comando disponibile solo nei gruppi.", msg)
            return
        url = await self._get_sheet_context(msg)
        if not url: return

        if not await self._check_genera_permission(msg):
            return

        sub = args[0].lower() if args else ""
        group_jid = msg.Info.MessageSource.Chat

        if sub == "nuovi":
            await self._reply(
                "🆕 *Creazione NuovoCalendario*\n"
                "Sto calcolando il nuovo ciclo delle turnazioni partendo dalla fine dell'attuale...",
                msg
            )
            try:
                success = await asyncio.wait_for(
                    self.calendar_service.manual_regenerate_new_cycle(url),
                    timeout=60.0
                )
                if success:
                    pdf = await self.calendar_service.generate_pdf(url, worksheet_name="NuovoCalendario")
                    if pdf:
                        caption = (
                            "✅ *Nuovo ciclo generato*\n"
                            "Il nuovo ciclo è stato creato correttamente in base all'attuale fine ciclo."
                        )
                        doc_msg = await self.client.build_document_message(
                            pdf, "NuovoCalendario.pdf", caption, "application/pdf"
                        )
                        await self.client.send_message(group_jid, message=doc_msg)
                    else:
                        await self._reply("✅ Nuovo ciclo generato, ma si è verificato un errore nella creazione del PDF.", msg)
                else:
                    await self._reply("❌ Errore durante la creazione del nuovo ciclo.", msg)
            except asyncio.TimeoutError:
                self.log.error("❌ TIMEOUT Google Sheets (/genera nuovi)")
                await self._reply("❌ Errore di timeout durante la connessione a Google Sheets.", msg)
            except Exception as e:
                self.log.exception(f"❌ ECCEZIONE /genera nuovi: {e}")
                await self._reply(f"❌ Errore critico: {str(e)}", msg)

        else:
            await self._reply(
                "🔧 *Rigenerazione Ciclo Corrente*\n"
                "Sto troncando i turni futuri. Il nuovo ciclo ripartirà da zero (dal primo condomino in lista) a partire dal prossimo lunedì...",
                msg
            )
            try:
                success = await asyncio.wait_for(
                    self.calendar_service.manual_fix_current_cycle(url),
                    timeout=60.0
                )
                if success:
                    pdf = await self.calendar_service.generate_pdf(url, worksheet_name="Calendario")
                    if pdf:
                        caption = (
                            "✅ *Calendario Aggiornato e Resettato*\n\n"
                            "I turni futuri sono stati eliminati e la lista è ripartita dal primo condomino a partire dal prossimo lunedì.\n\n"
                            "_Se era presente una bozza in NuovoCalendario, è stata eliminata._"
                        )
                        doc_msg = await self.client.build_document_message(
                            pdf, "CalendarioTurni.pdf", caption, "application/pdf"
                        )
                        await self.client.send_message(group_jid, message=doc_msg)
                    else:
                        await self._reply("⚠️ Ciclo riavviato ma errore nella generazione del PDF.", msg)
                else:
                    await self._reply("❌ Errore durante il riavvio del ciclo corrente.", msg)
            except asyncio.TimeoutError:
                self.log.error("❌ TIMEOUT Google Sheets (/genera)")
                await self._reply("❌ Errore di timeout durante la connessione a Google Sheets.", msg)
            except Exception as e:
                self.log.exception(f"❌ ECCEZIONE /genera: {e}")
                await self._reply(f"❌ Errore critico: {str(e)}", msg)

    async def cmd_help(self, msg: MessageEv, _):
        chat_jid = msg.Info.MessageSource.Chat
        sender = msg.Info.MessageSource.Sender.User

        if msg.Info.MessageSource.IsGroup:
            is_admin = False
            is_grp_admin = await self._is_group_admin(chat_jid, sender)
        else:
            is_admin = sender == self.me.User or sender in config.ADMIN_NUMBERS
            is_grp_admin = True

        txt = self._get_detailed_help(is_admin, is_grp_admin)
        await self._reply(txt, msg)

    # --- NUOVO COMANDO: /attiva (Solo per i gruppi) ---
    async def cmd_attiva(self, msg: MessageEv, args: List[str]):
        if not msg.Info.MessageSource.IsGroup:
            await self._reply("⚠️ Questo comando si usa solo all'interno di un gruppo. In chat privata usa `/config <link_gruppo> <link_sheet>`.", msg)
            return

        chat_jid = msg.Info.MessageSource.Chat
        sender = msg.Info.MessageSource.Sender.User
        
        is_grp_admin = await self._is_group_admin(chat_jid, sender)
        is_global_admin = self._is_admin(msg)

        if not (is_grp_admin or is_global_admin):
            await self._reply("⛔ Solo gli amministratori del gruppo possono attivare il bot.", msg)
            return

        if len(args) != 1:
            await self._reply("⚠️ Uso corretto: `/attiva <link_sheet>`", msg)
            return

        link_sheet = args[0]
        try:
            info = await self.client.get_group_info(chat_jid)
            
            # 1. Recupero Nome Gruppo sicuro
            gname = "Gruppo Sconosciuto"
            if hasattr(info, 'GroupName') and hasattr(info.GroupName, 'Name') and info.GroupName.Name:
                gname = info.GroupName.Name
            elif hasattr(info, 'Name') and info.Name:
                gname = info.Name
                
            if isinstance(gname, bytes):
                gname = gname.decode('utf-8')
                
            # 2. Tentativo di recupero Link d'invito (se permesso)
            link_grp = "Attivato internamente (Link N/D)"
            try:
                invite = await self.client.get_group_invite_link(chat_jid)
                if isinstance(invite, str) and invite:
                    link_grp = invite if "chat.whatsapp.com" in invite else f"https://chat.whatsapp.com/{invite}"
            except Exception:
                pass # Ignoriamo se il bot non ha permessi per leggere il link d'invito
            
            self.repo.upsert_config(chat_jid, link_sheet, str(link_grp), str(gname))
            await self._reply(f"✅ Bot attivato con successo per il gruppo: *{gname}*", msg)
        except Exception as e:
            await self._reply(f"❌ Errore durante l'attivazione: {e}", msg)

    # --- NUOVO COMANDO: /disattiva (Solo per i gruppi) ---
    async def cmd_disattiva(self, msg: MessageEv, _):
        if not msg.Info.MessageSource.IsGroup:
            await self._reply("⚠️ Questo comando si usa solo all'interno di un gruppo configurato. In chat privata usa `/config_reset <numero>`.", msg)
            return

        chat_jid = msg.Info.MessageSource.Chat
        sender = msg.Info.MessageSource.Sender.User
        
        # Verifica permessi: admin del gruppo o admin globale del bot
        is_grp_admin = await self._is_group_admin(chat_jid, sender)
        is_global_admin = self._is_admin(msg)

        if not (is_grp_admin or is_global_admin):
            await self._reply("⛔ Solo gli amministratori del gruppo possono disattivare il bot.", msg)
            return

        # Rimuove la configurazione dal database usando il JID del gruppo corrente
        success = self.repo.delete_config(chat_jid.User)
        
        if success:
            await self._reply("🚫 Configurazione rimossa con successo. Il bot è stato disattivato per questo gruppo.", msg)
        else:
            await self._reply("⚠️ Il bot non era configurato per questo gruppo.", msg)

    # --- COMANDO: /config (Solo per chat privata) ---
    async def cmd_admin_config(self, msg: MessageEv, args: List[str]):
        # Blocca l'esecuzione nei gruppi
        if msg.Info.MessageSource.IsGroup:
            await self._reply("⚠️ Il comando `/config` funziona solo in chat privata. Nei gruppi usa `/attiva <link_sheet>`.", msg)
            return
            
        if not self._is_admin(msg): 
            return

        if len(args) < 2:
            await self._reply("⚠️ Uso in chat privata: `/config <link_gruppo> <link_sheet>`", msg)
            return

        link_grp, link_sheet = args[0], args[1]
        try:
            code = link_grp.split("/")[-1]
            info = await self.client.get_group_info_from_link(code)
            gname = "Gruppo"
            if hasattr(info, 'GroupName') and hasattr(info.GroupName, 'Name'):
                gname = info.GroupName.Name.decode('utf-8') if isinstance(info.GroupName.Name, bytes) else info.GroupName.Name
            
            self.repo.upsert_config(info.JID, link_sheet, link_grp, str(gname))
            await self._reply(f"✅ Configurato: {gname}", msg)
        except Exception as e:
            await self._reply(f"❌ Errore: {e}", msg)

    async def cmd_admin_check(self, msg: MessageEv, _):
        # Ignora se usato in un gruppo
        if msg.Info.MessageSource.IsGroup: return
        if not self._is_admin(msg): return
        
        confs = self.repo.get_all_configs()
        txt = ""
        for i, c in enumerate(confs):
            nome = c[3] if c[3] else "Gruppo Sconosciuto"
            link_g = c[2] if c[2] else "Attivato internamente"
            if link_g == "N/D": link_g = "Attivato internamente"
            
            txt += f"{i+1}. 📂 *{nome}*\n   🔗 Sheet: {c[1]}\n   🔗 Link Gruppo: {link_g}\n\n"
        await self._reply(f"📋 Configs:\n\n{txt}" if txt else "Nessuna configurazione attiva.", msg)

    async def cmd_admin_reset(self, msg: MessageEv, args: List[str]):
        # Ignora se usato in un gruppo
        if msg.Info.MessageSource.IsGroup: return
        if not self._is_admin(msg) or not args: return
        
        try:
            idx = int(args[0]) - 1
            confs = self.repo.get_all_configs()
            if 0 <= idx < len(confs):
                self.repo.delete_config(confs[idx][0])
                await self._reply("🗑️ Eliminato.", msg)
        except: pass

    async def cmd_admin_db_reset(self, msg: MessageEv, _):
        # Ignora se usato in un gruppo
        if msg.Info.MessageSource.IsGroup: return
        if not self._is_admin(msg): return
        
        self.repo.recreate_tables()
        await self._reply("☢️ DB Resettato e Schema aggiornato.", msg)

    async def scheduler_loop(self):
        self.log.info("⏰ Scheduler Avviato")
        
        self.log.info("🔍 Controllo stato iniziale...")
        await self._check_calendar_health()

        while True:
            try:
                now = datetime.now()
                if now.strftime("%H:%M") == "09:00":
                    await self._send_reminders(now.strftime(config.DATE_FORMAT))
                    await asyncio.sleep(61)
                
                if now.minute == 0:
                     await self._check_calendar_health()
                     await asyncio.sleep(61)
                await asyncio.sleep(20)
            except Exception as e:
                self.log.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _send_reminders(self, date_str: str):
        configs = self.repo.get_all_configs()
        for jid_str, url, _, _, jid_blob in configs:
            records = await self.sheet_service.get_records(url)
            for r in records:
                if str(r['Data']) == date_str:
                    try:
                        raw_jid = JID()
                        raw_jid.ParseFromString(jid_blob)
                        msg = f"🔔 *Reminder*\nCiao @{r['Telefono']}, ricordati che stasera tocca a te esporre il bidone della {r.get('Bidone','?')}"
                        await self._send_private(raw_jid, msg)
                    except Exception as e:
                        self.log.error(f"Reminder fail for {jid_str}: {e}")

    async def _check_calendar_health(self):
        configs = self.repo.get_all_configs()
        if not configs:
            self.log.info("⚠️ Nessun gruppo configurato.")
            return

        for jid_str, url, _, _, _ in configs:
            status = await self.calendar_service.manage_lifecycle(url)
            self.log.info(f"🔄 Stato {jid_str}: {status}")

    async def start(self):
        asyncio.create_task(self.scheduler_loop())
        await self.client.connect()
        await self.client.idle()

if __name__ == "__main__":
    logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    bot = GarbageBot()
    def handle_exit(*args): sys.exit(0)
    signal.signal(signal.SIGINT, handle_exit)
    try:
        bot.client.loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        pass