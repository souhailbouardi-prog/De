from __future__ import annotations

import re
import time
from typing import Any

from hermes_constants import get_hermes_home
from hermes_state import SessionDB


class SessionQueryService:
    """Shared session-query helpers for dashboard and future API surfaces."""

    def __init__(self, db: SessionDB | None = None):
        self._db = db or SessionDB()
        self._owns_db = db is None

    def close(self) -> None:
        if self._owns_db:
            self._db.close()

    def list_sessions(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """Return the current dashboard session list payload."""
        sessions = self._db.list_sessions_rich(limit=limit, offset=offset)
        total = self._db.session_count()
        now = time.time()

        for session in sessions:
            session["is_active"] = (
                session.get("ended_at") is None
                and (now - session.get("last_active", session.get("started_at", 0))) < 300
            )

        return {
            "sessions": sessions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def search_sessions(self, q: str = "", limit: int = 20) -> dict[str, Any]:
        """Return the current dashboard session-search payload."""
        if not q or not q.strip():
            return {"results": []}

        terms = []
        for token in re.findall(r'"[^"]*"|\S+', q.strip()):
            if token.startswith('"') or token.endswith("*"):
                terms.append(token)
            else:
                terms.append(token + "*")
        prefix_query = " ".join(terms)

        matches = self._db.search_messages(query=prefix_query, limit=limit)

        seen: dict[str, dict[str, Any]] = {}
        for match in matches:
            session_id = match["session_id"]
            if session_id not in seen:
                seen[session_id] = {
                    "session_id": session_id,
                    "snippet": match.get("snippet", ""),
                    "role": match.get("role"),
                    "source": match.get("source"),
                    "model": match.get("model"),
                    "session_started": match.get("session_started"),
                }

        return {"results": list(seen.values())}

    def get_session_detail(self, session_id: str) -> dict[str, Any] | None:
        """Resolve a session ID/prefix and return the canonical session detail payload."""
        sid = self._db.resolve_session_id(session_id)
        if not sid:
            return None
        return self._db.get_session(sid)

    def get_session_messages(self, session_id: str) -> dict[str, Any] | None:
        """Resolve a session ID/prefix and return the canonical session messages payload."""
        sid = self._db.resolve_session_id(session_id)
        if not sid:
            return None
        return {
            "session_id": sid,
            "messages": self._db.get_messages(sid),
        }

    def get_root_task_snapshots(self) -> dict[str, Any]:
        """Return root task snapshots shaped for the dashboard session-query API."""
        snapshots: list[dict[str, Any]] = []
        profile_id = self._current_profile_id()

        for root_session in self._fetch_root_session_descriptors():
            root_session_id = root_session["session_id"]
            current_session_id = self._fetch_latest_descendant_session_id(root_session_id) or root_session_id
            current_session = self._fetch_session_descriptor(current_session_id) or root_session
            lineage = self._fetch_lineage(current_session_id)
            lineage_ids = [descriptor["session_id"] for descriptor in lineage]
            last_activity_at = self._fetch_last_activity_at(lineage_ids)

            snapshots.append(
                {
                    "profile_id": profile_id,
                    "root_session_id": root_session_id,
                    "current_session_id": current_session_id,
                    "root_session": root_session,
                    "current_session": current_session,
                    "lineage": lineage,
                    "initial_user_message": self._fetch_initial_user_message(root_session_id),
                    "latest_conversation_message": self._fetch_latest_conversation_message(lineage_ids),
                    "last_activity_at": (
                        last_activity_at
                        if last_activity_at is not None
                        else current_session.get("ended_at")
                        or current_session.get("started_at")
                        or root_session.get("started_at")
                    ),
                }
            )

        snapshots.sort(key=lambda snapshot: snapshot.get("last_activity_at") or float("-inf"), reverse=True)
        return {"root_tasks": snapshots}

    def get_session_messages_page(
        self,
        session_id: str,
        limit: int = 24,
        before_id: int | None = None,
        before_ts: float | None = None,
    ) -> dict[str, Any] | None:
        """Return one transcript page using the Desk-compatible cursor semantics."""
        if (before_id is None) != (before_ts is None):
            raise ValueError("before_id and before_ts must be provided together")
        if limit <= 0:
            raise ValueError("limit must be positive")

        sid = self._db.resolve_session_id(session_id)
        if not sid:
            return None

        page_size = min(limit, 100)
        parameters: list[Any] = [sid]
        cursor_clause = ""
        if before_id is not None and before_ts is not None:
            cursor_clause = """
              AND (
                    timestamp < ?
                    OR (timestamp = ? AND id < ?)
              )
            """
            parameters.extend([before_ts, before_ts, before_id])
        parameters.append(page_size + 1)

        with self._db._lock:
            cursor = self._db._conn.execute(
                f"""
                SELECT id, session_id, role, content, tool_name, reasoning, timestamp
                FROM messages
                WHERE session_id = ?
                {cursor_clause}
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                parameters,
            )
            rows = cursor.fetchall()

        has_more_before = len(rows) > page_size
        page_rows = rows[:page_size]
        messages = [self._row_to_message_page_item(row) for row in reversed(page_rows)]
        return {
            "messages": messages,
            "has_more_before": has_more_before,
        }

    def get_session_binding(
        self,
        session_id: str,
        root_session_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Return the Desk-compatible root/current binding for a session lineage."""
        preferred_session_id = self._db.resolve_session_id(session_id)
        if preferred_session_id is None:
            return None

        anchor_session_id = self._resolve_optional_session_id(root_session_id)
        if root_session_id is not None and anchor_session_id is None:
            return None

        current_session_id = self._fetch_latest_descendant_session_id(preferred_session_id)
        if current_session_id is None:
            current_session_id = preferred_session_id

        current_descriptor = self._fetch_session_descriptor(current_session_id)
        if current_descriptor is None:
            return None

        lineage = self._fetch_lineage(current_descriptor["session_id"])
        if not lineage:
            return None

        resolved_root_session_id = lineage[0]["session_id"]
        if anchor_session_id is not None and resolved_root_session_id != anchor_session_id:
            return None

        return {
            "root_session_id": resolved_root_session_id,
            "current_session_id": current_descriptor["session_id"],
            "lineage": lineage,
        }

    def _current_profile_id(self) -> str:
        hermes_home = get_hermes_home()
        if hermes_home.parent.name == "profiles":
            return hermes_home.name
        return "default"

    def _fetch_root_session_descriptors(self) -> list[dict[str, Any]]:
        with self._db._lock:
            cursor = self._db._conn.execute(
                """
                SELECT id, parent_session_id, title, source, started_at, ended_at
                FROM sessions
                WHERE parent_session_id IS NULL
                ORDER BY started_at DESC, id DESC
                """
            )
            rows = cursor.fetchall()
        return [self._row_to_session_descriptor(row) for row in rows]

    def _fetch_session_descriptor(self, session_id: str) -> dict[str, Any] | None:
        with self._db._lock:
            cursor = self._db._conn.execute(
                """
                SELECT id, parent_session_id, title, source, started_at, ended_at
                FROM sessions
                WHERE id = ?
                LIMIT 1
                """,
                (session_id,),
            )
            row = cursor.fetchone()
        return self._row_to_session_descriptor(row) if row else None

    def _fetch_lineage(self, session_id: str) -> list[dict[str, Any]]:
        lineage: list[dict[str, Any]] = []
        cursor = session_id
        seen: set[str] = set()

        while cursor not in seen:
            descriptor = self._fetch_session_descriptor(cursor)
            if not descriptor:
                break
            lineage.append(descriptor)
            seen.add(cursor)
            parent_session_id = descriptor.get("parent_session_id")
            if not parent_session_id:
                break
            cursor = parent_session_id

        return list(reversed(lineage))

    def _fetch_latest_descendant_session_id(self, anchor_session_id: str) -> str | None:
        with self._db._lock:
            cursor = self._db._conn.execute(
                """
                WITH RECURSIVE subtree(id, parent_session_id, started_at, depth) AS (
                    SELECT id, parent_session_id, started_at, 0
                    FROM sessions
                    WHERE id = ?
                    UNION ALL
                    SELECT s.id, s.parent_session_id, s.started_at, subtree.depth + 1
                    FROM sessions s
                    JOIN subtree ON s.parent_session_id = subtree.id
                )
                SELECT subtree.id
                FROM subtree
                LEFT JOIN sessions child ON child.parent_session_id = subtree.id
                WHERE child.id IS NULL
                ORDER BY subtree.depth DESC, subtree.started_at DESC, subtree.id DESC
                LIMIT 1
                """,
                (anchor_session_id,),
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def _fetch_initial_user_message(self, root_session_id: str) -> str | None:
        return self._fetch_single_string(
            """
            SELECT COALESCE(content, '')
            FROM messages
            WHERE session_id = ? AND role = 'user'
            ORDER BY timestamp ASC, id ASC
            LIMIT 1
            """,
            [root_session_id],
        )

    def _fetch_latest_conversation_message(self, session_ids: list[str]) -> str | None:
        if not session_ids:
            return None
        placeholders = ",".join("?" for _ in session_ids)
        return self._fetch_single_string(
            f"""
            SELECT COALESCE(content, '')
            FROM messages
            WHERE session_id IN ({placeholders})
              AND role IN ('user', 'assistant')
              AND TRIM(COALESCE(content, '')) != ''
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
            session_ids,
        )

    def _fetch_last_activity_at(self, session_ids: list[str]) -> float | None:
        if not session_ids:
            return None
        placeholders = ",".join("?" for _ in session_ids)
        with self._db._lock:
            cursor = self._db._conn.execute(
                f"""
                SELECT MAX(timestamp)
                FROM messages
                WHERE session_id IN ({placeholders})
                """,
                session_ids,
            )
            row = cursor.fetchone()
        if not row or row[0] is None:
            return None
        return float(row[0])

    def _resolve_optional_session_id(self, session_id: str | None) -> str | None:
        if session_id is None:
            return None
        normalized = session_id.strip()
        if not normalized:
            return None
        return self._db.resolve_session_id(normalized)

    def _fetch_single_string(self, sql: str, parameters: list[Any]) -> str | None:
        with self._db._lock:
            cursor = self._db._conn.execute(sql, parameters)
            row = cursor.fetchone()
        if not row:
            return None
        return self._normalize_optional_text(row[0])

    @staticmethod
    def _normalize_optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _row_to_session_descriptor(row: Any) -> dict[str, Any]:
        return {
            "session_id": row["id"],
            "parent_session_id": row["parent_session_id"],
            "title": row["title"],
            "source": row["source"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
        }

    @staticmethod
    def _row_to_message_page_item(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "tool_name": row["tool_name"],
            "reasoning": row["reasoning"],
            "timestamp": row["timestamp"],
        }
