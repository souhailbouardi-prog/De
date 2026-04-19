#!/usr/bin/env python3
"""Hermes Memory MCP Server — exposes Hermes memory stores to any MCP client (Claude Code, Cursor, etc.) via stdio."""
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp[cli]>=1.2.0"]
# ///

from __future__ import annotations

import os
import re
import sqlite3
import tempfile
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]  # Windows

try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore[assignment]  # Unix

from mcp.server.fastmcp import FastMCP

def _hermes_home() -> Path:
    """Resolve HERMES_HOME, respecting profiles and custom deployments."""
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


CHAR_LIMIT_MEMORY = 2_200
CHAR_LIMIT_USER = 1_375
SECTION_SEP = "\n§\n"


def _memory_file() -> Path:
    return _hermes_home() / "memories" / "MEMORY.md"


def _user_file() -> Path:
    return _hermes_home() / "memories" / "USER.md"


def _state_db() -> Path:
    return _hermes_home() / "state.db"


def _file_map() -> dict[str, Path]:
    return {"memory": _memory_file(), "user": _user_file()}


def _limit_map() -> dict[str, int]:
    return {"memory": CHAR_LIMIT_MEMORY, "user": CHAR_LIMIT_USER}

# Prompt-injection patterns (aligned with Hermes built-in memory_tool.py)
_INJECTION_RE = re.compile(
    r"(?i)"
    r"(you are now|ignore previous|ignore all|forget (all|everything|your)|"
    r"new instructions|override (your|all|system)|system:\s|<\|im_start\|>|"
    r"\[INST\]|\[/INST\]|<\|system\|>|<\|user\|>|<\|assistant\|>|"
    r"pretend you|act as if|role:\s*system)",
)
_INVISIBLE_RE = re.compile(r"[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]")

mcp = FastMCP("hermes-memory")


# ---------------------------------------------------------------------------
# File I/O — atomic writes with file locking (matches Hermes MemoryStore)
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except PermissionError:
        return f"[Error] Permission denied: {path}"


def _atomic_write(path: Path, content: str) -> None:
    """Write via temp file + os.replace + fsync for crash safety."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _locked_read_modify_write(path: Path, modifier):
    """Acquire file lock, read, apply modifier, write atomically.

    modifier(current_content) -> (new_content, result_message)
    Returns the result_message from modifier.

    Uses fcntl.flock on Unix and msvcrt.locking on Windows (matching
    Hermes MemoryStore cross-platform locking strategy).
    """
    lock_path = path.with_suffix(path.suffix + ".lock")

    if fcntl is not None:
        # Unix: fcntl file locking (matching Hermes MemoryStore._file_lock)
        lock_fd = open(lock_path, "a+")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            current = _read_file(path)
            new_content, result = modifier(current)
            if new_content is not None:
                _atomic_write(path, new_content)
            return result
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
    elif msvcrt is not None:
        # Windows: msvcrt file locking (matching Hermes MemoryStore._file_lock)
        lock_fd = open(lock_path, "a+")
        try:
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
            current = _read_file(path)
            new_content, result = modifier(current)
            if new_content is not None:
                _atomic_write(path, new_content)
            return result
        finally:
            lock_fd.seek(0)
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            lock_fd.close()
    else:
        # Fallback: no locking available
        current = _read_file(path)
        new_content, result = modifier(current)
        if new_content is not None:
            _atomic_write(path, new_content)
        return result


# ---------------------------------------------------------------------------
# Security scanning
# ---------------------------------------------------------------------------


def _scan_content(text: str) -> str | None:
    """Return error message if content contains injection, invisible chars, or delimiter."""
    if _INJECTION_RE.search(text):
        return "[Error] Content rejected: contains prompt-injection patterns."
    if _INVISIBLE_RE.search(text):
        return "[Error] Content rejected: contains invisible Unicode characters."
    if SECTION_SEP in text:
        return "[Error] Content rejected: contains section delimiter (§). This would corrupt memory structure on reload."
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def read_memory(store: str = "all") -> str:
    """Read Hermes memory content.

    Args:
        store: Which store to read — "memory", "user", or "all" (default).
    """
    parts: list[str] = []
    if store in ("all", "memory"):
        content = _read_file(_memory_file())
        parts.append(f"=== MEMORY.md ({len(content)} chars) ===\n{content}")
    if store in ("all", "user"):
        content = _read_file(_user_file())
        parts.append(f"=== USER.md ({len(content)} chars) ===\n{content}")
    if not parts:
        return f"[Error] Unknown store '{store}'. Use 'memory', 'user', or 'all'."
    return "\n\n".join(parts)


@mcp.tool()
def add_memory_entry(
    store: str,
    entry: str,
    old_text: str | None = None,
) -> str:
    """Add or replace an entry in a Hermes memory store.

    Args:
        store: Target store — "memory" or "user".
        entry: The new text to insert.
        old_text: If provided, find this substring and replace it with `entry`.
                  If not provided, append `entry` as a new section (§-separated).
    """
    fmap = _file_map()
    if store not in fmap:
        return f"[Error] Unknown store '{store}'. Use 'memory' or 'user'."

    scan_err = _scan_content(entry)
    if scan_err:
        return scan_err

    path = fmap[store]
    limit = _limit_map()[store]

    def _modify(current: str):
        if old_text:
            if old_text not in current:
                return None, f"[Error] old_text not found in {path.name}. No changes made."
            new_content = current.replace(old_text, entry, 1)
        else:
            if current and not current.endswith("\n"):
                new_content = current + SECTION_SEP + entry
            elif current:
                new_content = current.rstrip("\n") + SECTION_SEP + entry
            else:
                new_content = entry

        if len(new_content) > limit:
            return None, (
                f"[Error] Would exceed char limit: {len(new_content)}/{limit}. "
                f"Current: {len(current)} chars. Entry: {len(entry)} chars. "
                "Remove old entries first or shorten the new entry."
            )
        return new_content, f"OK — {path.name} updated. Now {len(new_content)} chars ({limit - len(new_content)} remaining)."

    try:
        return _locked_read_modify_write(path, _modify)
    except PermissionError:
        return f"[Error] Permission denied writing to {path}"
    except OSError as exc:
        return f"[Error] Failed to write {path}: {exc}"


@mcp.tool()
def remove_memory_entry(store: str, old_text: str) -> str:
    """Remove an entry (or substring) from a Hermes memory store.

    Args:
        store: Target store — "memory" or "user".
        old_text: The exact text to remove. If it matches an entire §-section,
                  the section and its separator are removed cleanly.
    """
    fmap = _file_map()
    if store not in fmap:
        return f"[Error] Unknown store '{store}'. Use 'memory' or 'user'."

    path = fmap[store]

    def _modify(current: str):
        if old_text not in current:
            return None, f"[Error] old_text not found in {path.name}. No changes made."

        sections = current.split(SECTION_SEP)
        remaining = [s for s in sections if s.strip() != old_text.strip()]

        if len(remaining) < len(sections):
            new_content = SECTION_SEP.join(remaining)
        else:
            new_content = current.replace(old_text, "", 1)
            new_content = re.sub(r"(\n§\n){2,}", SECTION_SEP, new_content)
            new_content = new_content.strip(SECTION_SEP.strip()).strip()

        return new_content, f"OK — {path.name} updated. Now {len(new_content)} chars."

    try:
        return _locked_read_modify_write(path, _modify)
    except PermissionError:
        return f"[Error] Permission denied writing to {path}"
    except OSError as exc:
        return f"[Error] Failed to write {path}: {exc}"


@mcp.tool()
def memory_status() -> str:
    """Return current memory usage (char count / limit) for all stores."""
    lines: list[str] = []
    for label, path, limit in [
        ("MEMORY.md", _memory_file(), CHAR_LIMIT_MEMORY),
        ("USER.md", _user_file(), CHAR_LIMIT_USER),
    ]:
        content = _read_file(path)
        chars = len(content)
        sections = content.count("§") + 1 if content else 0
        pct = chars / limit * 100 if limit else 0
        lines.append(
            f"{label}: {chars:,}/{limit:,} chars ({pct:.1f}%) — {sections} sections"
        )

    sdb = _state_db()
    if sdb.exists():
        try:
            conn = sqlite3.connect(f"file:{sdb}?mode=ro", uri=True, timeout=3)
            row = conn.execute(
                "SELECT COUNT(*) AS cnt, MAX(started_at) AS latest FROM sessions"
            ).fetchone()
            conn.close()
            lines.append(f"state.db: {row[0]} sessions (searchable via session_search)")
        except (sqlite3.Error, OSError):
            lines.append("state.db: present but unreadable")
    else:
        lines.append("state.db: not found")

    return "\n".join(lines)


@mcp.tool()
def session_search(
    query: str,
    limit: int = 20,
    source: str | None = None,
) -> str:
    """Search past Hermes sessions using FTS5 full-text search.

    Args:
        query: FTS5 search query (supports AND, OR, NOT, phrases in quotes).
        limit: Max results to return (default 20, max 100).
        source: Optional filter by session source (e.g. "claude-code", "hermes").
    """
    sdb = _state_db()
    if not sdb.exists():
        return f"[Error] state.db not found at {sdb}"

    limit = min(max(1, limit), 100)

    sql = """
        SELECT
            s.id,
            s.source,
            s.model,
            s.title,
            datetime(s.started_at, 'unixepoch', 'localtime') AS started,
            s.message_count,
            s.estimated_cost_usd,
            snippet(messages_fts, 0, '>>>', '<<<', '...', 48) AS snippet
        FROM messages_fts
        JOIN messages m ON m.id = messages_fts.rowid
        JOIN sessions s ON s.id = m.session_id
        WHERE messages_fts MATCH ?
    """
    params: list = [query]

    if source:
        sql += " AND s.source = ?"
        params.append(source)

    sql += " ORDER BY s.started_at DESC LIMIT ?"
    params.append(limit)

    try:
        conn = sqlite3.connect(
            f"file:{sdb}?mode=ro",
            uri=True,
            timeout=5,
        )
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
    except sqlite3.OperationalError as exc:
        if "database is locked" in str(exc):
            return "[Error] state.db is locked by another process. Try again shortly."
        return f"[Error] SQLite error: {exc}"
    except sqlite3.DatabaseError as exc:
        return f"[Error] Database error: {exc}"

    if not rows:
        return f"No results for query: {query}"

    parts: list[str] = [f"Found {len(rows)} result(s) for '{query}':\n"]
    for r in rows:
        cost = f"${r['estimated_cost_usd']:.4f}" if r["estimated_cost_usd"] else "n/a"
        parts.append(
            f"- [{r['started']}] {r['title'] or '(untitled)'}\n"
            f"  source={r['source']} model={r['model']} msgs={r['message_count']} cost={cost}\n"
            f"  id={r['id']}\n"
            f"  > {r['snippet']}"
        )
    return "\n".join(parts)


@mcp.tool()
def session_read(session_id: str, last_n: int = 50) -> str:
    """Read the message transcript of a specific Hermes session.

    Args:
        session_id: The session ID (e.g. "20260416_131733_2bd683").
        last_n: Number of most recent messages to return (default 50, max 200).
    """
    sdb = _state_db()
    if not sdb.exists():
        return f"[Error] state.db not found at {sdb}"

    last_n = min(max(1, last_n), 200)

    try:
        conn = sqlite3.connect(f"file:{sdb}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row

        session = conn.execute(
            "SELECT id, title, source, model, message_count, "
            "datetime(started_at, 'unixepoch', 'localtime') AS started "
            "FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not session:
            conn.close()
            return f"[Error] Session '{session_id}' not found."

        rows = conn.execute(
            "SELECT role, content, datetime(timestamp, 'unixepoch', 'localtime') AS ts "
            "FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, last_n),
        ).fetchall()
        conn.close()
    except sqlite3.Error as exc:
        return f"[Error] SQLite error: {exc}"

    rows = list(reversed(rows))

    header = (
        f"Session: {session['title'] or '(untitled)'}\n"
        f"ID: {session['id']} | source={session['source']} model={session['model']}\n"
        f"Started: {session['started']} | {session['message_count']} messages total\n"
        f"--- Showing last {len(rows)} messages ---\n"
    )

    msgs: list[str] = []
    for r in rows:
        content = r["content"] or ""
        if len(content) > 2000:
            content = content[:2000] + "... [truncated]"
        msgs.append(f"[{r['ts']}] {r['role'].upper()}:\n{content}")

    return header + "\n\n".join(msgs)


@mcp.tool()
def recent_sessions(limit: int = 10, source: str | None = None) -> str:
    """List recent Hermes sessions.

    Args:
        limit: Number of sessions to return (default 10, max 50).
        source: Optional filter by source (e.g. "cli", "telegram", "discord").
    """
    sdb = _state_db()
    if not sdb.exists():
        return f"[Error] state.db not found at {sdb}"

    limit = min(max(1, limit), 50)

    sql = """
        SELECT
            id, title, source, model, message_count,
            estimated_cost_usd,
            datetime(started_at, 'unixepoch', 'localtime') AS started,
            datetime(ended_at, 'unixepoch', 'localtime') AS ended
        FROM sessions
    """
    params: list = []

    if source:
        sql += " WHERE source = ?"
        params.append(source)

    sql += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)

    try:
        conn = sqlite3.connect(f"file:{sdb}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
    except sqlite3.Error as exc:
        return f"[Error] SQLite error: {exc}"

    if not rows:
        return "No sessions found."

    parts: list[str] = [f"Recent {len(rows)} session(s):\n"]
    for r in rows:
        cost = f"${r['estimated_cost_usd']:.4f}" if r["estimated_cost_usd"] else "n/a"
        parts.append(
            f"- {r['title'] or '(untitled)'}\n"
            f"  id={r['id']} source={r['source']} model={r['model']}\n"
            f"  {r['started']} → {r['ended'] or 'ongoing'} | {r['message_count']} msgs | cost={cost}"
        )
    return "\n".join(parts)


if __name__ == "__main__":
    mcp.run(transport="stdio")
