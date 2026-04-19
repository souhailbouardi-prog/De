#!/usr/bin/env python3
"""SQLite-backed health event logging and queries.

This is a library module — import it from wrapper scripts or tests.
DB location: HEALTH_DB_PATH env var, or ~/.hermes/health/health.db
"""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

_lock = threading.Lock()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS health_events (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'user',
    type TEXT NOT NULL,
    subtype TEXT,
    value REAL,
    unit TEXT,
    data TEXT,
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_ts ON health_events(ts);
CREATE INDEX IF NOT EXISTS idx_type ON health_events(type);
CREATE INDEX IF NOT EXISTS idx_type_ts ON health_events(type, ts);
CREATE INDEX IF NOT EXISTS idx_source_ts ON health_events(source, ts);
CREATE UNIQUE INDEX IF NOT EXISTS idx_system_daily ON health_events(date(ts), type, source)
    WHERE source = 'system' AND type IN ('checkin', 'evening', 'nudge');
"""


def _db_path() -> Path:
    override = os.environ.get("HEALTH_DB_PATH")
    if override:
        return Path(override)
    hermes_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    return hermes_home / "health" / "health.db"


def _get_conn() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(path),
        check_same_thread=False,
        timeout=5.0,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA_SQL)
    return conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_utc_start() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")


VALID_TYPES = {
    "checkin", "response", "habit", "evening", "symptom", "nudge",
    "mood", "weight", "bloodwork", "summary",
}
VALID_SUBTYPES = {
    "walk", "meal", "supplement", "smoke", "nebulize", "weight",
    "sighing", "sunlight", "gita", "noon", "miss2",
    "weekly", "appointment", "result", "photo",
    "stretch", "mobility",
}
VALID_SOURCES = {"user", "system"}


def log_event(
    type: str,
    subtype: str = None,
    source: str = "user",
    value: float = None,
    unit: str = None,
    data: dict = None,
    note: str = None,
) -> None:
    """Insert a health event. System events are deduplicated per day.

    Validates type, subtype, and source against allowed values.
    Raises ValueError for invalid inputs.
    """
    if type not in VALID_TYPES:
        raise ValueError(f"Invalid type '{type}'. Must be one of: {sorted(VALID_TYPES)}")
    if subtype is not None and subtype not in VALID_SUBTYPES:
        raise ValueError(f"Invalid subtype '{subtype}'. Must be one of: {sorted(VALID_SUBTYPES)}")
    if source not in VALID_SOURCES:
        raise ValueError(f"Invalid source '{source}'. Must be one of: {sorted(VALID_SOURCES)}")
    ts = _utc_now()
    data_str = json.dumps(data) if data else None
    with _lock:
        conn = _get_conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO health_events (ts, source, type, subtype, value, unit, data, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, source, type, subtype, value, unit, data_str, note),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            if source == "system":
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    "UPDATE health_events SET ts=?, data=?, note=? "
                    "WHERE date(ts)=date(?) AND type=? AND source='system'",
                    (ts, data_str, note, ts, type),
                )
                conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conn.close()


def last_user_interaction() -> str | None:
    """Return UTC ISO timestamp of the most recent source='user' event, or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT ts FROM health_events WHERE source='user' ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        return row["ts"] if row else None
    finally:
        conn.close()


def today_events() -> list[dict]:
    """Return all events for today (UTC day boundary)."""
    start = _today_utc_start()
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM health_events WHERE ts >= ? ORDER BY ts", (start,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def check_morning_response() -> bool:
    """Return True if today's system checkin has a subsequent user response."""
    start = _today_utc_start()
    conn = _get_conn()
    try:
        checkin = conn.execute(
            "SELECT id FROM health_events WHERE ts >= ? AND type='checkin' AND source='system' LIMIT 1",
            (start,),
        ).fetchone()
        if not checkin:
            return False
        response = conn.execute(
            "SELECT 1 FROM health_events WHERE id > ? AND source='user' LIMIT 1",
            (checkin["id"],),
        ).fetchone()
        return response is not None
    finally:
        conn.close()


def events_range(days: int) -> list[dict]:
    """Return all events from the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM health_events WHERE ts >= ? ORDER BY ts", (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def weight_trend(days: int = 30) -> dict:
    """Query weight events, return entries sorted by ts + weekly averages grouped by ISO week."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT ts, value FROM health_events "
            "WHERE type='habit' AND subtype='weight' AND ts >= ? "
            "ORDER BY ts",
            (cutoff,),
        ).fetchall()
        entries = [{"ts": r["ts"], "value": r["value"]} for r in rows]

        # Group by ISO week
        week_buckets: dict[str, list[float]] = {}
        for e in entries:
            dt = datetime.strptime(e["ts"], "%Y-%m-%dT%H:%M:%SZ")
            iso_year, iso_week, _ = dt.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            week_buckets.setdefault(key, []).append(e["value"])

        weekly_averages = [
            {"week": k, "avg": sum(v) / len(v)}
            for k, v in sorted(week_buckets.items())
        ]

        return {"entries": entries, "weekly_averages": weekly_averages}
    finally:
        conn.close()


def mood_trend(days: int = 30) -> dict:
    """Query mood and evening-with-value events, return entries + rolling 7-day average."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT ts, value FROM health_events "
            "WHERE ((type='mood') OR (type='evening' AND value IS NOT NULL)) "
            "AND ts >= ? ORDER BY ts",
            (cutoff,),
        ).fetchall()
        entries = [{"ts": r["ts"], "value": r["value"]} for r in rows]

        # Compute rolling 7-day average for each data point
        rolling_7day_avg = []
        for i, e in enumerate(entries):
            dt_current = datetime.strptime(e["ts"], "%Y-%m-%dT%H:%M:%SZ")
            window_start = dt_current - timedelta(days=7)
            window_vals = [
                entries[j]["value"]
                for j in range(i + 1)
                if datetime.strptime(entries[j]["ts"], "%Y-%m-%dT%H:%M:%SZ") > window_start
            ]
            avg = sum(window_vals) / len(window_vals) if window_vals else None
            rolling_7day_avg.append({"ts": e["ts"], "avg": avg})

        return {"entries": entries, "rolling_7day_avg": rolling_7day_avg}
    finally:
        conn.close()


def weekly_summary(days: int = 7) -> dict:
    """Aggregate events over the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT00:00:00Z"
    )
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM health_events WHERE ts >= ? ORDER BY ts", (cutoff,)
        ).fetchall()
        events = [dict(r) for r in rows]

        # habit_counts
        habit_counts: dict[str, int] = {}
        for e in events:
            if e["type"] == "habit" and e["subtype"]:
                habit_counts[e["subtype"]] = habit_counts.get(e["subtype"], 0) + 1

        # mood_avg from mood events and evening events with value
        mood_vals = [
            e["value"]
            for e in events
            if (e["type"] == "mood" or (e["type"] == "evening" and e["value"] is not None))
            and e["value"] is not None
        ]
        mood_avg = sum(mood_vals) / len(mood_vals) if mood_vals else None

        # weight_latest
        weight_events = [
            e for e in events
            if e["type"] == "habit" and e["subtype"] == "weight" and e["value"] is not None
        ]
        weight_latest = weight_events[-1]["value"] if weight_events else None

        # total_events
        total_events = len(events)

        # days_with_user_events
        user_days = set()
        for e in events:
            if e["source"] == "user":
                day = e["ts"][:10]  # YYYY-MM-DD
                user_days.add(day)
        days_with_user_events = len(user_days)

        return {
            "habit_counts": habit_counts,
            "mood_avg": mood_avg,
            "weight_latest": weight_latest,
            "total_events": total_events,
            "days_with_user_events": days_with_user_events,
        }
    finally:
        conn.close()


def bloodwork_status() -> dict:
    """Return most recent bloodwork event status."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM health_events WHERE type='bloodwork' ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"status": "not_scheduled"}
        e = dict(row)
        if e["subtype"] == "appointment":
            return {"status": "scheduled", "date": e["note"] or (json.loads(e["data"]) if e["data"] else {}).get("date")}
        if e["subtype"] == "result":
            data = json.loads(e["data"]) if e["data"] else {}
            return {"status": "completed", "data": data}
        return {"status": "not_scheduled"}
    finally:
        conn.close()
