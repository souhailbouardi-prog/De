#!/usr/bin/env python3
"""Tests for health_log SQLite event library."""
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "health" / "daily-health" / "scripts"))


class TestHealthLog(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_health.db")
        os.environ["HEALTH_DB_PATH"] = self.db_path
        import importlib
        import health_log
        importlib.reload(health_log)
        self.hl = health_log

    def tearDown(self):
        os.environ.pop("HEALTH_DB_PATH", None)

    def test_log_event_basic(self):
        self.hl.log_event(type="habit", subtype="walk", source="user", value=25, unit="min")
        events = self.hl.today_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "habit")
        self.assertEqual(events[0]["subtype"], "walk")
        self.assertEqual(events[0]["source"], "user")
        self.assertAlmostEqual(events[0]["value"], 25.0)

    def test_log_event_with_data_json(self):
        data = {"recovery": 95, "hrv": 94.8}
        self.hl.log_event(type="checkin", source="system", data=data)
        events = self.hl.today_events()
        self.assertEqual(len(events), 1)
        parsed = json.loads(events[0]["data"])
        self.assertEqual(parsed["recovery"], 95)

    def test_timestamps_are_utc(self):
        self.hl.log_event(type="habit", subtype="supplement", source="user")
        events = self.hl.today_events()
        ts = events[0]["ts"]
        self.assertTrue(ts.endswith("Z") or "+00:00" in ts, f"Timestamp not UTC: {ts}")

    def test_last_user_interaction_ignores_system(self):
        self.hl.log_event(type="checkin", source="system")
        result = self.hl.last_user_interaction()
        self.assertIsNone(result, "System events should not count as user interaction")
        self.hl.log_event(type="response", source="user")
        result = self.hl.last_user_interaction()
        self.assertIsNotNone(result)

    def test_check_morning_response_false(self):
        self.hl.log_event(type="checkin", source="system")
        self.assertFalse(self.hl.check_morning_response())

    def test_check_morning_response_true(self):
        self.hl.log_event(type="checkin", source="system")
        self.hl.log_event(type="response", source="user")
        self.assertTrue(self.hl.check_morning_response())

    def test_events_range(self):
        self.hl.log_event(type="habit", subtype="walk", source="user", value=20)
        events = self.hl.events_range(7)
        self.assertEqual(len(events), 1)

    def test_system_event_idempotency(self):
        self.hl.log_event(type="checkin", source="system", data={"recovery": 90})
        self.hl.log_event(type="checkin", source="system", data={"recovery": 95})
        events = self.hl.today_events()
        system_checkins = [e for e in events if e["type"] == "checkin" and e["source"] == "system"]
        self.assertEqual(len(system_checkins), 1, "Duplicate system checkin should be ignored")

    def test_wal_mode_enabled(self):
        import sqlite3
        # Trigger DB creation via the module so WAL is set
        self.hl.log_event(type="habit", subtype="walk", source="user")
        conn = sqlite3.connect(self.db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        self.assertEqual(mode, "wal")

    def test_concurrent_writes(self):
        errors = []
        def writer(source, n):
            try:
                for i in range(n):
                    self.hl.log_event(type="habit", subtype="walk", source=source, value=float(i), note=f"thread-{source}-{i}")
            except Exception as e:
                errors.append(e)
        t1 = threading.Thread(target=writer, args=("user", 20))
        t2 = threading.Thread(target=writer, args=("user", 20))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")
        events = self.hl.today_events()
        self.assertEqual(len(events), 40)

    # ---- Phase 2 Tests ----

    def test_new_types_valid(self):
        """mood, weight, bloodwork, summary types should not raise ValueError."""
        for t in ("mood", "weight", "bloodwork", "summary"):
            self.hl.log_event(type=t, source="user")

    def test_new_subtypes_valid(self):
        """weekly, appointment, result, photo subtypes should not raise ValueError."""
        for st in ("weekly", "appointment", "result", "photo"):
            self.hl.log_event(type="habit", subtype=st, source="user")

    def test_mobility_subtypes_valid(self):
        """stretch and mobility subtypes should not raise ValueError."""
        for st in ("stretch", "mobility"):
            self.hl.log_event(type="habit", subtype=st, source="user", note=f"{st}-note")

    def _init_db_and_connect(self):
        """Helper: ensure schema exists, return a raw sqlite3 connection for direct inserts."""
        import sqlite3
        # Trigger schema creation via the module
        init_conn = self.hl._get_conn()
        init_conn.close()
        return sqlite3.connect(self.db_path)

    def test_weight_trend_basic(self):
        """Log 3 weight events, verify trend returns them sorted + weekly averages."""
        conn = self._init_db_and_connect()
        conn.execute(
            "INSERT INTO health_events (ts, source, type, subtype, value, unit) VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-04-01T08:00:00Z", "user", "habit", "weight", 72.0, "kg"),
        )
        conn.execute(
            "INSERT INTO health_events (ts, source, type, subtype, value, unit) VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-04-03T08:00:00Z", "user", "habit", "weight", 71.5, "kg"),
        )
        conn.execute(
            "INSERT INTO health_events (ts, source, type, subtype, value, unit) VALUES (?, ?, ?, ?, ?, ?)",
            ("2026-04-05T08:00:00Z", "user", "habit", "weight", 71.0, "kg"),
        )
        conn.commit()
        conn.close()

        result = self.hl.weight_trend(days=30)
        self.assertEqual(len(result["entries"]), 3)
        # Sorted ascending by ts
        self.assertAlmostEqual(result["entries"][0]["value"], 72.0)
        self.assertAlmostEqual(result["entries"][2]["value"], 71.0)
        # Weekly averages present
        self.assertIn("weekly_averages", result)
        self.assertIsInstance(result["weekly_averages"], list)
        self.assertTrue(len(result["weekly_averages"]) > 0)

    def test_weight_trend_empty(self):
        """No weight events returns empty."""
        result = self.hl.weight_trend(days=30)
        self.assertEqual(result["entries"], [])
        self.assertEqual(result["weekly_averages"], [])

    def test_mood_trend_with_rolling_avg(self):
        """Log 10 mood events, verify 7-day rolling average computed."""
        conn = self._init_db_and_connect()
        for i in range(10):
            day = f"2026-04-{i+1:02d}"
            conn.execute(
                "INSERT INTO health_events (ts, source, type, value) VALUES (?, ?, ?, ?)",
                (f"{day}T20:00:00Z", "user", "mood", float(i + 1)),
            )
        conn.commit()
        conn.close()

        result = self.hl.mood_trend(days=30)
        self.assertEqual(len(result["entries"]), 10)
        self.assertIn("rolling_7day_avg", result)
        self.assertIsInstance(result["rolling_7day_avg"], list)
        # Rolling avg should have 10 entries (one per data point)
        self.assertEqual(len(result["rolling_7day_avg"]), 10)

    def test_mood_trend_includes_evening_values(self):
        """Evening events with values count as mood data."""
        conn = self._init_db_and_connect()
        conn.execute(
            "INSERT INTO health_events (ts, source, type, value) VALUES (?, ?, ?, ?)",
            ("2026-04-01T21:00:00Z", "user", "evening", 4.0),
        )
        conn.execute(
            "INSERT INTO health_events (ts, source, type, value) VALUES (?, ?, ?, ?)",
            ("2026-04-02T20:00:00Z", "user", "mood", 7.0),
        )
        conn.commit()
        conn.close()

        result = self.hl.mood_trend(days=30)
        self.assertEqual(len(result["entries"]), 2)
        self.assertAlmostEqual(result["entries"][0]["value"], 4.0)
        self.assertAlmostEqual(result["entries"][1]["value"], 7.0)

    def test_weekly_summary_aggregation(self):
        """Log mixed events, verify counts, averages."""
        conn = self._init_db_and_connect()
        # 3 walks, 2 supplements, 1 mood, 1 weight on different days
        for i, (t, st, v) in enumerate([
            ("habit", "walk", 25.0),
            ("habit", "walk", 30.0),
            ("habit", "walk", 20.0),
            ("habit", "supplement", None),
            ("habit", "supplement", None),
            ("mood", None, 7.0),
            ("habit", "weight", 71.5),
        ]):
            day = f"2026-04-{i+1:02d}"
            conn.execute(
                "INSERT INTO health_events (ts, source, type, subtype, value) VALUES (?, ?, ?, ?, ?)",
                (f"{day}T10:00:00Z", "user", t, st, v),
            )
        conn.commit()
        conn.close()

        result = self.hl.weekly_summary(days=30)
        self.assertEqual(result["habit_counts"]["walk"], 3)
        self.assertEqual(result["habit_counts"]["supplement"], 2)
        self.assertAlmostEqual(result["mood_avg"], 7.0)
        self.assertAlmostEqual(result["weight_latest"], 71.5)
        self.assertEqual(result["total_events"], 7)
        self.assertEqual(result["days_with_user_events"], 7)

    def test_weekly_summary_empty_week(self):
        """No events returns zero counts."""
        result = self.hl.weekly_summary(days=7)
        self.assertEqual(result["habit_counts"], {})
        self.assertIsNone(result["mood_avg"])
        self.assertIsNone(result["weight_latest"])
        self.assertEqual(result["total_events"], 0)
        self.assertEqual(result["days_with_user_events"], 0)

    def test_bloodwork_status_not_scheduled(self):
        """No bloodwork events returns not_scheduled."""
        result = self.hl.bloodwork_status()
        self.assertEqual(result["status"], "not_scheduled")

    def test_bloodwork_status_scheduled(self):
        """Appointment event exists returns scheduled."""
        self.hl.log_event(
            type="bloodwork", subtype="appointment", source="user",
            note="April 20",
        )
        result = self.hl.bloodwork_status()
        self.assertEqual(result["status"], "scheduled")
        self.assertEqual(result["date"], "April 20")

    def test_bloodwork_status_completed(self):
        """Result event exists returns completed."""
        self.hl.log_event(
            type="bloodwork", subtype="result", source="user",
            data={"TSH": 4.2, "FreeT4": 1.1},
        )
        result = self.hl.bloodwork_status()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["data"]["TSH"], 4.2)
