#!/usr/bin/env python3
"""Tests for health_insights — Phase 3 smart insights and phase transition detection."""
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "health" / "daily-health" / "scripts"))


def _insert_checkin(conn, day_offset, recovery, hrv, rhr, spo2, sleep_hours):
    """Insert a synthetic WHOOP checkin event N days ago."""
    ts = (datetime.now(timezone.utc) - timedelta(days=day_offset)).strftime(
        "%Y-%m-%dT10:00:00Z"
    )
    data = json.dumps({
        "recovery": recovery,
        "hrv": hrv,
        "rhr": rhr,
        "spo2": spo2,
        "sleep_hours": sleep_hours,
    })
    conn.execute(
        "INSERT INTO health_events (ts, source, type, data) VALUES (?, ?, ?, ?)",
        (ts, "system", "checkin", data),
    )


def _insert_habit(conn, day_offset, subtype, value=None, unit=None):
    """Insert a synthetic habit event N days ago."""
    ts = (datetime.now(timezone.utc) - timedelta(days=day_offset)).strftime(
        "%Y-%m-%dT12:00:00Z"
    )
    conn.execute(
        "INSERT INTO health_events (ts, source, type, subtype, value, unit) VALUES (?, ?, ?, ?, ?, ?)",
        (ts, "user", "habit", subtype, value, unit),
    )


class TestHealthInsights(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_health.db")
        os.environ["HEALTH_DB_PATH"] = self.db_path
        import importlib
        import health_log
        importlib.reload(health_log)
        self.hl = health_log
        # Ensure schema exists
        init_conn = self.hl._get_conn()
        init_conn.close()
        # Raw connection for inserting test data
        self.conn = sqlite3.connect(self.db_path)
        # Now import health_insights (after health_log is set up)
        import health_insights
        importlib.reload(health_insights)
        self.hi = health_insights

    def tearDown(self):
        self.conn.close()
        os.environ.pop("HEALTH_DB_PATH", None)

    # ---- sleep_recovery_correlation ----

    def test_sleep_recovery_correlation_basic(self):
        """Insert 10 checkins with varying sleep/recovery, verify correlation computed."""
        # 5 nights with >7.5h sleep, high recovery
        for i in range(5):
            _insert_checkin(self.conn, day_offset=i + 1, recovery=80 + i,
                            hrv=60, rhr=55, spo2=97, sleep_hours=8.0 + i * 0.1)
        # 5 nights with <7.5h sleep, lower recovery
        for i in range(5):
            _insert_checkin(self.conn, day_offset=i + 6, recovery=40 + i,
                            hrv=50, rhr=60, spo2=96, sleep_hours=6.0 + i * 0.1)
        self.conn.commit()

        result = self.hi.sleep_recovery_correlation(days=30)
        self.assertEqual(result["above_threshold"]["count"], 5)
        self.assertEqual(result["below_threshold"]["count"], 5)
        # Avg recovery above should be higher than below
        self.assertGreater(
            result["above_threshold"]["avg_recovery"],
            result["below_threshold"]["avg_recovery"],
        )
        self.assertEqual(result["threshold_hours"], 7.5)
        self.assertIn("insight", result)
        self.assertIn("recover", result["insight"].lower())

    def test_sleep_recovery_correlation_empty(self):
        """No data returns zeros."""
        result = self.hi.sleep_recovery_correlation(days=30)
        self.assertEqual(result["above_threshold"]["count"], 0)
        self.assertEqual(result["above_threshold"]["avg_recovery"], 0)
        self.assertEqual(result["below_threshold"]["count"], 0)
        self.assertEqual(result["below_threshold"]["avg_recovery"], 0)

    # ---- hrv_trend_analysis ----

    def test_hrv_trend_up(self):
        """Insert ascending HRV values, verify direction='up'."""
        # 14 days of ascending HRV
        for i in range(14):
            _insert_checkin(self.conn, day_offset=14 - i, recovery=60,
                            hrv=40 + i * 3, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        result = self.hi.hrv_trend_analysis(days=30)
        self.assertEqual(result["direction"], "up")
        self.assertGreater(result["current_7day_avg"], result["previous_7day_avg"])
        self.assertIsInstance(result["values"], list)

    def test_hrv_trend_down(self):
        """Insert descending HRV values, verify direction='down'."""
        # 14 days of descending HRV
        for i in range(14):
            _insert_checkin(self.conn, day_offset=14 - i, recovery=60,
                            hrv=80 - i * 3, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        result = self.hi.hrv_trend_analysis(days=30)
        self.assertEqual(result["direction"], "down")
        self.assertLess(result["current_7day_avg"], result["previous_7day_avg"])

    def test_hrv_trend_stable(self):
        """Insert flat HRV values, verify direction='stable'."""
        # 14 days of nearly identical HRV
        for i in range(14):
            _insert_checkin(self.conn, day_offset=14 - i, recovery=60,
                            hrv=60.0, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        result = self.hi.hrv_trend_analysis(days=30)
        self.assertEqual(result["direction"], "stable")

    # ---- detect_illness_signals ----

    def test_detect_illness_no_alert(self):
        """Normal values, alert=False."""
        # 10 baseline days (day 3-12 ago)
        for i in range(10):
            _insert_checkin(self.conn, day_offset=i + 3, recovery=70,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        # 3 recent normal days
        for i in range(3):
            _insert_checkin(self.conn, day_offset=i, recovery=70,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        result = self.hi.detect_illness_signals(days=3)
        self.assertFalse(result["alert"])
        self.assertEqual(result["signals"], [])

    def test_detect_illness_rhr_spike(self):
        """Elevated RHR triggers alert."""
        # 7 baseline days (day 3-9 ago) with RHR=55
        for i in range(7):
            _insert_checkin(self.conn, day_offset=i + 3, recovery=70,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        # Recent 3 days with RHR spike > 10% (55 * 1.1 = 60.5, use 63)
        for i in range(3):
            _insert_checkin(self.conn, day_offset=i, recovery=50,
                            hrv=55, rhr=63, spo2=97, sleep_hours=7.0)
        self.conn.commit()

        result = self.hi.detect_illness_signals(days=3)
        self.assertTrue(result["alert"])
        self.assertIn("rhr_spike", result["signals"])

    def test_detect_illness_hrv_drop(self):
        """HRV crash triggers alert."""
        # 7 baseline days (day 3-9 ago) with HRV=60
        for i in range(7):
            _insert_checkin(self.conn, day_offset=i + 3, recovery=70,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        # Recent 3 days with HRV drop > 20% (60 * 0.8 = 48, use 45)
        for i in range(3):
            _insert_checkin(self.conn, day_offset=i, recovery=40,
                            hrv=45, rhr=55, spo2=97, sleep_hours=7.0)
        self.conn.commit()

        result = self.hi.detect_illness_signals(days=3)
        self.assertTrue(result["alert"])
        self.assertIn("hrv_drop", result["signals"])

    # ---- habit_recovery_correlation ----

    def test_habit_recovery_correlation(self):
        """Log walks on some days with checkins, verify correlation."""
        # Days 1-5: checkin + walk habit → higher recovery
        for i in range(5):
            _insert_checkin(self.conn, day_offset=i + 1, recovery=75 + i,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
            _insert_habit(self.conn, day_offset=i + 1, subtype="walk", value=25, unit="min")
        # Days 6-10: checkin, no walk → lower recovery
        for i in range(5):
            _insert_checkin(self.conn, day_offset=i + 6, recovery=50 + i,
                            hrv=55, rhr=58, spo2=96, sleep_hours=7.0)
        self.conn.commit()

        result = self.hi.habit_recovery_correlation(days=30)
        self.assertIn("walk", result["correlations"])
        walk = result["correlations"]["walk"]
        self.assertEqual(walk["with_count"], 5)
        self.assertEqual(walk["without_count"], 5)
        # Days with walk had higher recovery
        self.assertGreater(walk["with"], walk["without"])
        self.assertGreater(walk["delta"], 0)

    # ---- check_phase_transition ----

    def test_phase_transition_1to2_ready(self):
        """All Phase 1->2 criteria met."""
        # Last 7 days: good sleep (>7.5h), walk, supplement each day
        for i in range(7):
            _insert_checkin(self.conn, day_offset=i, recovery=70,
                            hrv=60 + i, rhr=55, spo2=97, sleep_hours=8.0)
            _insert_habit(self.conn, day_offset=i, subtype="walk", value=25, unit="min")
            _insert_habit(self.conn, day_offset=i, subtype="supplement")
        # Also need 7 more days of ascending HRV for trend to be "up"
        for i in range(7, 14):
            _insert_checkin(self.conn, day_offset=i, recovery=65,
                            hrv=50 + (i - 7), rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        # Schedule bloodwork
        self.hl.log_event(type="bloodwork", subtype="appointment", source="user", note="April 20")

        result = self.hi.check_phase_transition(current_phase=1)
        self.assertEqual(result["phase"], "1->2")
        self.assertTrue(result["ready"])
        self.assertTrue(result["criteria"]["sleep_consistent"])
        self.assertTrue(result["criteria"]["walking_regular"])
        self.assertTrue(result["criteria"]["supplements_regular"])
        self.assertTrue(result["criteria"]["bloodwork_scheduled"])
        self.assertEqual(result["blockers"], [])

    def test_phase_transition_1to2_blocked(self):
        """Some criteria missing, verify blockers list."""
        # Only 3 days with walk (need 5/7)
        for i in range(7):
            _insert_checkin(self.conn, day_offset=i, recovery=70,
                            hrv=60, rhr=55, spo2=97, sleep_hours=8.0)
            # Only walk on first 3 days
            if i < 3:
                _insert_habit(self.conn, day_offset=i, subtype="walk", value=25, unit="min")
            _insert_habit(self.conn, day_offset=i, subtype="supplement")
        # Add older data for HRV trend
        for i in range(7, 14):
            _insert_checkin(self.conn, day_offset=i, recovery=65,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        # No bloodwork scheduled
        result = self.hi.check_phase_transition(current_phase=1)
        self.assertFalse(result["ready"])
        self.assertIn("walking_regular", result["blockers"])
        self.assertIn("bloodwork_scheduled", result["blockers"])

    def test_phase_transition_2to3_ready(self):
        """All Phase 2->3 criteria met."""
        # 14 days of recovery > 50%
        for i in range(14):
            _insert_checkin(self.conn, day_offset=i, recovery=65,
                            hrv=60, rhr=55, spo2=97, sleep_hours=7.5)
        self.conn.commit()

        # Weight gain ~0.35 kg/week over 4 weeks (within 0.25-0.5)
        # Week 1: 70.0, Week 2: 70.35, Week 3: 70.70, Week 4: 71.05
        raw = sqlite3.connect(self.db_path)
        for week_idx in range(4):
            for day_idx in range(3):  # 3 measurements per week
                day_offset = 28 - (week_idx * 7 + day_idx)
                ts = (datetime.now(timezone.utc) - timedelta(days=day_offset)).strftime(
                    "%Y-%m-%dT08:00:00Z"
                )
                w = 70.0 + week_idx * 0.35
                raw.execute(
                    "INSERT INTO health_events (ts, source, type, subtype, value, unit) VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, "user", "habit", "weight", w, "kg"),
                )
        raw.commit()
        raw.close()

        # Mark bloodwork completed
        self.hl.log_event(type="bloodwork", subtype="result", source="user",
                          data={"TSH": 4.2, "FreeT4": 1.1})

        result = self.hi.check_phase_transition(current_phase=2)
        self.assertEqual(result["phase"], "2->3")
        self.assertTrue(result["criteria"]["recovery_consistent"])
        self.assertTrue(result["criteria"]["labs_completed"])
        self.assertEqual(result["blockers"], [])


if __name__ == "__main__":
    unittest.main()
