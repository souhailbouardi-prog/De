"""
session.py — Standalone session tracker for Hermes gateway.

Dead simple: a map with timestamps that optionally talks to memory providers.
No hooks. No lifecycle events. No provider interface changes.

Architecture:
    gateway/session.py
    └ SessionManager
      ├ thread_id → {user_id, platform, last_topic, updated_at}
      ├ user_id → [discord_12345, telegram_67890, ...]
      └ memory_provider.bar() ← calls IN, not integrated

Entry points:
    1. On message in      → session.touch(thread_id, topic_guess)
    2. On gateway restart → session.load()
    3. Need context?      → session.get_context(thread_id)

Usage:
    from gateway.session import SessionManager

    sm = SessionManager()

    # Gateway restart — load existing state
    sm.load()

    # Message arrives
    sm.touch("discord_1492844793817202709", topic_guess="video generation")

    # Need context?
    ctx = sm.get_context("discord_1492844793817202709")
    # Returns: {thread_id, user_id, platform, topic, age, related_threads}

    # With memory provider (optional)
    sm.set_memory_provider(lambda topic: memory_store.recall(topic))
    ctx = sm.get_context("discord_...", deep=True)
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
DB_PATH = HERMES_HOME / "session_manager.db"

SM_SCHEMA = """
CREATE TABLE IF NOT EXISTS sm_sessions (
    thread_id TEXT PRIMARY KEY,
    user_id TEXT DEFAULT '',
    platform TEXT DEFAULT 'unknown',
    topic TEXT DEFAULT '',
    message_count INTEGER DEFAULT 0,
    last_message_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sm_user_threads (
    user_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    platform TEXT DEFAULT 'unknown',
    first_seen TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, thread_id)
);

CREATE INDEX IF NOT EXISTS idx_sm_user ON sm_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sm_platform ON sm_sessions(platform);
CREATE INDEX IF NOT EXISTS idx_sm_updated ON sm_sessions(updated_at);
"""


def _get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SM_SCHEMA)
    return conn


def _parse_platform(thread_id: str) -> str:
    if thread_id.startswith("discord_"):
        return "discord"
    elif thread_id.startswith("telegram_"):
        return "telegram"
    return "unknown"


def _snowflake_to_iso(snowflake_str: str) -> Optional[str]:
    try:
        ts = ((int(snowflake_str) >> 22) + 1420070400000) / 1000
        return datetime.fromtimestamp(ts).isoformat()
    except (ValueError, OSError):
        return None


class SessionManager:
    """
    Standalone session tracker. Map with timestamps.

    Calls memory providers IN — never the other way around.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._memory_provider: Optional[Callable[[str], Any]] = None

    def set_memory_provider(self, provider: Callable[[str], Any]):
        """Set optional memory provider callback. provider(topic) → context."""
        self._memory_provider = provider

    def touch(self, thread_id: str, topic_guess: str = "",
              user_id: str = "", platform: str = "") -> Dict:
        """
        Called on every message in. Updates timestamp + topic.

        Dead simple: upsert one row.
        """
        if not thread_id:
            return {}

        conn = _get_db(self.db_path)
        now = datetime.now().isoformat()

        if not platform:
            platform = _parse_platform(thread_id)

        conn.execute("""
            INSERT INTO sm_sessions
                (thread_id, user_id, platform, topic, message_count,
                 last_message_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET
                user_id = COALESCE(NULLIF(excluded.user_id, ''), sm_sessions.user_id),
                platform = COALESCE(
                    NULLIF(excluded.platform, 'unknown'), sm_sessions.platform),
                topic = CASE
                    WHEN excluded.topic != '' THEN excluded.topic
                    ELSE sm_sessions.topic END,
                message_count = sm_sessions.message_count + 1,
                last_message_at = excluded.last_message_at,
                updated_at = excluded.updated_at
        """, (thread_id, user_id, platform, topic_guess, now, now, now))

        if user_id:
            conn.execute("""
                INSERT INTO sm_user_threads (user_id, thread_id, platform, first_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, thread_id) DO NOTHING
            """, (user_id, thread_id, platform, now))

        conn.commit()
        conn.close()

        return {
            "thread_id": thread_id, "user_id": user_id,
            "platform": platform, "topic": topic_guess,
            "updated_at": now,
        }

    def load(self, sources: Optional[List[Dict]] = None) -> Dict:
        """
        Called on gateway restart. Import sessions from provided sources.

        sources: list of {thread_id, user_id?, platform?, topic?, last_message_at?}
                 If None, just ensures DB schema exists.
        """
        conn = _get_db(self.db_path)
        now = datetime.now().isoformat()
        imported = 0

        if sources:
            for s in sources:
                tid = s.get("thread_id", "")
                if not tid:
                    continue
                conn.execute("""
                    INSERT INTO sm_sessions
                        (thread_id, user_id, platform, topic,
                         last_message_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(thread_id) DO UPDATE SET
                        user_id = COALESCE(
                            NULLIF(excluded.user_id, ''), sm_sessions.user_id),
                        platform = COALESCE(
                            NULLIF(excluded.platform, 'unknown'),
                            sm_sessions.platform),
                        topic = CASE
                            WHEN excluded.topic != ''
                            AND sm_sessions.topic = ''
                            THEN excluded.topic
                            ELSE sm_sessions.topic END,
                        last_message_at = MAX(
                            sm_sessions.last_message_at,
                            excluded.last_message_at),
                        updated_at = ?
                """, (
                    tid,
                    s.get("user_id", ""),
                    s.get("platform", _parse_platform(tid)),
                    s.get("topic", ""),
                    s.get("last_message_at", now),
                    now, now,
                ))
                imported += 1

        conn.commit()
        conn.close()
        return {"imported": imported}

    def get_context(self, thread_id: str, deep: bool = False) -> Dict:
        """
        Returns cheap session context.

        deep=False: just metadata — fast, no external calls.
        deep=True: also calls memory_provider(topic).
        """
        conn = _get_db(self.db_path)

        row = conn.execute("""
            SELECT thread_id, user_id, platform, topic, message_count,
                   last_message_at, created_at, updated_at
            FROM sm_sessions WHERE thread_id = ?
        """, (thread_id,)).fetchone()

        if not row:
            conn.close()
            return {"thread_id": thread_id, "exists": False}

        (tid, uid, platform, topic, msg_count,
         last_msg, created, updated) = row

        # Age string
        age_str = "unknown"
        if last_msg:
            try:
                delta = datetime.now() - datetime.fromisoformat(last_msg)
                if delta < timedelta(minutes=5):
                    age_str = "just now"
                elif delta < timedelta(hours=1):
                    age_str = f"{int(delta.total_seconds() / 60)}m ago"
                elif delta < timedelta(days=1):
                    age_str = f"{int(delta.total_seconds() / 3600)}h ago"
                else:
                    age_str = f"{delta.days}d ago"
            except ValueError:
                pass

        # Related threads (same user)
        related = []
        if uid:
            rows = conn.execute("""
                SELECT thread_id, platform, topic, last_message_at
                FROM sm_sessions
                WHERE user_id = ? AND thread_id != ?
                ORDER BY last_message_at DESC LIMIT 5
            """, (uid, thread_id)).fetchall()
            related = [
                {"thread_id": r[0], "platform": r[1],
                 "topic": r[2], "last_message_at": r[3]}
                for r in rows
            ]

        conn.close()

        ctx = {
            "thread_id": tid, "exists": True,
            "user_id": uid, "platform": platform,
            "topic": topic, "message_count": msg_count,
            "age": age_str, "last_message_at": last_msg,
            "created_at": created, "related_threads": related,
        }

        if deep and self._memory_provider and topic:
            try:
                ctx["memory_hint"] = self._memory_provider(topic)
            except Exception as e:
                ctx["memory_hint_error"] = str(e)

        return ctx

    def get_user_threads(self, user_id: str) -> List[Dict]:
        """List all threads for a user, newest first."""
        conn = _get_db(self.db_path)
        rows = conn.execute("""
            SELECT s.thread_id, s.platform, s.topic,
                   s.message_count, s.last_message_at, ut.first_seen
            FROM sm_user_threads ut
            JOIN sm_sessions s ON s.thread_id = ut.thread_id
            WHERE ut.user_id = ?
            ORDER BY s.last_message_at DESC
        """, (user_id,)).fetchall()
        conn.close()
        return [
            {"thread_id": r[0], "platform": r[1], "topic": r[2],
             "message_count": r[3], "last_message_at": r[4],
             "first_seen": r[5]}
            for r in rows
        ]

    def stats(self) -> Dict:
        """Overview of session manager state."""
        conn = _get_db(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM sm_sessions").fetchone()[0]
        by_platform = dict(conn.execute(
            "SELECT platform, COUNT(*) FROM sm_sessions GROUP BY platform"
        ).fetchall())
        cutoff_24h = (datetime.now() - timedelta(hours=24)).isoformat()
        active_24h = conn.execute(
            "SELECT COUNT(*) FROM sm_sessions WHERE last_message_at >= ?",
            (cutoff_24h,)).fetchone()[0]
        users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM sm_user_threads "
            "WHERE user_id != ''").fetchone()[0]
        conn.close()
        return {
            "total_sessions": total, "active_24h": active_24h,
            "unique_users": users, "by_platform": by_platform,
        }
