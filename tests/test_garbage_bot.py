"""Unit tests for GarbageBot services and configuration."""
import unittest
import os
import tempfile
import sqlite3
from datetime import date
from unittest.mock import MagicMock, AsyncMock, patch

import neonize
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "garbage_bot")))

from garbage_bot import (
    AppConfig,
    ConfigRepository,
    CalendarService,
    SheetService,
    GarbageBot,
)
from neonize.proto.Neonize_pb2 import JID


class TestNeonizeDependency(unittest.TestCase):
    """Verify Neonize library is available and exports required interfaces."""

    def test_neonize_interfaces(self):
        """Verify Neonize exports client and protobuf definitions."""
        from neonize.aioze.client import NewAClient
        from neonize.aioze.events import ConnectedEv, MessageEv, LoggedOutEv
        self.assertIsNotNone(NewAClient)
        self.assertIsNotNone(ConnectedEv)
        self.assertIsNotNone(MessageEv)
        self.assertIsNotNone(LoggedOutEv)


class TestConfigRepository(unittest.TestCase):
    """Verify ConfigRepository database operations."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
        self.temp_db.close()
        self.repo = ConfigRepository(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_init_and_upsert_and_retrieve(self):
        """Test database table creation and upserting group configuration."""
        mock_jid = JID(User="123456789", Server="g.us", Device=0, Integrator=0, RawAgent=0)
        sheet_url = "https://docs.google.com/spreadsheets/d/test"
        group_link = "https://chat.whatsapp.com/test"
        group_name = "Condominio Test"

        self.repo.upsert_config(mock_jid, sheet_url, group_link, group_name)

        url = self.repo.get_sheet_url("123456789")
        self.assertEqual(url, sheet_url)

        all_confs = self.repo.get_all_configs()
        self.assertEqual(len(all_confs), 1)
        self.assertEqual(all_confs[0][0], "123456789")
        self.assertEqual(all_confs[0][1], sheet_url)
        self.assertEqual(all_confs[0][2], group_link)
        self.assertEqual(all_confs[0][3], group_name)

    def test_delete_config(self):
        """Test deleting a configuration by JID."""
        mock_jid = JID(User="987654321", Server="g.us", Device=0, Integrator=0, RawAgent=0)
        self.repo.upsert_config(mock_jid, "https://sheet", "https://link", "Name")
        deleted = self.repo.delete_config("987654321")
        self.assertTrue(deleted)
        self.assertIsNone(self.repo.get_sheet_url("987654321"))


class TestCalendarService(unittest.TestCase):
    """Verify CalendarService shift calculations and date utilities."""

    def setUp(self):
        self.mock_sheet_service = MagicMock(spec=SheetService)
        self.calendar = CalendarService(self.mock_sheet_service)

    def test_date_helpers(self):
        """Test date calculation helpers."""
        first_mon = self.calendar._get_first_monday_of_year(2026)
        self.assertEqual(first_mon.weekday(), 0)
        self.assertEqual(first_mon.year, 2026)

        next_mon = self.calendar._get_next_monday(date(2026, 9, 22))  # Tuesday
        self.assertEqual(next_mon, date(2026, 9, 28))  # Following Monday
        self.assertEqual(next_mon.weekday(), 0)

    def test_calculate_shifts_cycle(self):
        """Test shift calculation cycle generation."""
        condomini = [("Mario", "333111"), ("Luigi", "333222")]
        start_date = date(2026, 9, 28)
        turni = self.calendar._calculate_shifts_cycle(condomini, start_date, start_idx=0)

        # 2 condomini * 2 shifts each = 4 rows
        self.assertEqual(len(turni), 4)

        # Shift 1: Mario, plastica on Monday 28/09/2026
        self.assertEqual(turni[0], ["28/09/2026", "plastica", "Mario", "333111"])
        # Shift 2: Mario, carta on Tuesday 29/09/2026
        self.assertEqual(turni[1], ["29/09/2026", "carta", "Mario", "333111"])
        # Shift 3: Luigi, plastica on Monday 05/10/2026
        self.assertEqual(turni[2], ["05/10/2026", "plastica", "Luigi", "333222"])
        # Shift 4: Luigi, carta on Tuesday 06/10/2026
        self.assertEqual(turni[3], ["06/10/2026", "carta", "Luigi", "333222"])

    def test_find_next_condomino_index(self):
        """Test next condomino index calculation."""
        condomini = [("Mario", "333"), ("Luigi", "444"), ("Anna", "555")]
        self.assertEqual(self.calendar._find_next_condomino_index("Mario", condomini), 1)
        self.assertEqual(self.calendar._find_next_condomino_index("Anna", condomini), 0)
        self.assertEqual(self.calendar._find_next_condomino_index("Unknown", condomini), 0)


class TestGarbageBotInitialization(unittest.TestCase):
    """Verify GarbageBot client initialization lifecycle."""

    @patch("garbage_bot.SheetService")
    @patch("garbage_bot.ConfigRepository")
    @patch("garbage_bot.NewAClient")
    def test_single_client_instantiation(self, mock_client_cls, mock_repo_cls, mock_sheet_cls):
        """Verify NewAClient is instantiated only once during bot initialization."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        bot = GarbageBot()

        # Ensure NewAClient was only called once, avoiding duplicate FFI allocations
        self.assertEqual(mock_client_cls.call_count, 1)
        self.assertIsNotNone(bot.client)
        self.assertTrue(mock_client.event.qr.called)


if __name__ == "__main__":
    unittest.main()
