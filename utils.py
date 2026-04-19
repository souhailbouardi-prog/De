"""Shared utility functions for hermes-agent."""

import json
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Union

import yaml

logger = logging.getLogger(__name__)


TRUTHY_STRINGS = frozenset({"1", "true", "yes", "on"})


def is_truthy_value(value: Any, default: bool = False) -> bool:
    """Coerce bool-ish values using the project's shared truthy string set."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_STRINGS
    return bool(value)


def env_var_enabled(name: str, default: str = "") -> bool:
    """Return True when an environment variable is set to a truthy value."""
    return is_truthy_value(os.getenv(name, default), default=False)


def _preserve_file_mode(path: Path) -> "int | None":
    """Capture the permission bits of *path* if it exists, else ``None``."""
    try:
        return stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    except OSError:
        return None


def _restore_file_mode(path: Path, mode: "int | None") -> None:
    """Re-apply *mode* to *path* after an atomic replace.

    ``tempfile.mkstemp`` creates files with 0o600 (owner-only).  After
    ``os.replace`` swaps the temp file into place the target inherits
    those restrictive permissions, breaking Docker / NAS volume mounts
    that rely on broader permissions set by the user.  Calling this
    right after ``os.replace`` restores the original permissions.
    """
    if mode is None:
        return
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def atomic_json_write(
    path: Union[str, Path],
    data: Any,
    *,
    indent: int = 2,
    **dump_kwargs: Any,
) -> None:
    """Write JSON data to a file atomically.

    Uses temp file + fsync + os.replace to ensure the target file is never
    left in a partially-written state. If the process crashes mid-write,
    the previous version of the file remains intact.

    Args:
        path: Target file path (will be created or overwritten).
        data: JSON-serializable data to write.
        indent: JSON indentation (default 2).
        **dump_kwargs: Additional keyword args forwarded to json.dump(), such
            as default=str for non-native types.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    original_mode = _preserve_file_mode(path)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=indent,
                ensure_ascii=False,
                **dump_kwargs,
            )
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        _restore_file_mode(path, original_mode)
    except BaseException:
        # Intentionally catch BaseException so temp-file cleanup still runs for
        # KeyboardInterrupt/SystemExit before re-raising the original signal.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_yaml_write(
    path: Union[str, Path],
    data: Any,
    *,
    default_flow_style: bool = False,
    sort_keys: bool = False,
    extra_content: str | None = None,
) -> None:
    """Write YAML data to a file atomically.

    Uses temp file + fsync + os.replace to ensure the target file is never
    left in a partially-written state.  If the process crashes mid-write,
    the previous version of the file remains intact.

    Args:
        path: Target file path (will be created or overwritten).
        data: YAML-serializable data to write.
        default_flow_style: YAML flow style (default False).
        sort_keys: Whether to sort dict keys (default False).
        extra_content: Optional string to append after the YAML dump
            (e.g. commented-out sections for user reference).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    original_mode = _preserve_file_mode(path)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=default_flow_style, sort_keys=sort_keys)
            if extra_content:
                f.write(extra_content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        _restore_file_mode(path, original_mode)
    except BaseException:
        # Match atomic_json_write: cleanup must also happen for process-level
        # interruptions before we re-raise them.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ─── JSON Helpers ─────────────────────────────────────────────────────────────


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Parse JSON, returning *default* on any parse error.

    Replaces the ``try: json.loads(x) except (JSONDecodeError, TypeError)``
    pattern duplicated across display.py, anthropic_adapter.py,
    auxiliary_client.py, and others.
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


# ─── Environment Variable Helpers ─────────────────────────────────────────────


def env_int(key: str, default: int = 0) -> int:
    """Read an environment variable as an integer, with fallback."""
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def env_bool(key: str, default: bool = False) -> bool:
    """Read an environment variable as a boolean."""
    return is_truthy_value(os.getenv(key, ""), default=default)


# ---------------------------------------------------------------------------
# Invisible-unicode injection detection (shared by prompt_builder, memory_tool,
# cronjob_tools, skills_guard). ZWJ inside emoji grapheme clusters (e.g. 🧙‍♂️)
# is legitimate and must not be flagged; ZWJ between non-pictographic chars is
# the classic injection shape and IS flagged.
# ---------------------------------------------------------------------------

# Default blocklist of invisible unicode characters commonly used in
# prompt-injection attacks. ZWJ (U+200D) is included here but has a context
# check applied — see find_unsafe_invisibles().
BLOCKLIST_INVISIBLES = frozenset({
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
})


def _is_pictographic(cp: int) -> bool:
    """True if codepoint is in a range that emoji sequences draw from.

    Used to distinguish legitimate ZWJ inside emoji grapheme clusters
    (e.g. 🧙‍♂️ = 🧙 + ZWJ + ♂ + VS16) from ZWJ used for injection.

    Not an exhaustive Unicode emoji-property table — covers the ranges that
    carry nearly all real emoji codepoints. False negatives here mean a
    legitimate emoji ZWJ sequence gets flagged; false positives would let an
    injection past. Prefer false-negative-side errors.
    """
    return (
        0x1F000 <= cp <= 0x1FFFF  # emoji planes
        or 0x2600 <= cp <= 0x27BF  # Misc Symbols, Dingbats
        or 0x2300 <= cp <= 0x23FF  # Misc Technical (⌚, ⏰)
        or 0x2B00 <= cp <= 0x2BFF  # Misc Symbols and Arrows (⭐, ⬅)
        or cp in (0x00A9, 0x00AE, 0x2122, 0x2139)  # ©, ®, ™, ℹ
        or cp in (0x3030, 0x303D, 0x3297, 0x3299)  # CJK symbols used as emoji
    )


def _zwj_in_emoji_context(content: str, idx: int) -> bool:
    """True if the ZWJ at content[idx] sits between two pictographic chars
    (skipping variation selectors), i.e. is part of a real emoji sequence.
    """
    if idx <= 0 or idx >= len(content) - 1:
        return False
    left = idx - 1
    while left >= 0 and content[left] in ('\ufe0f', '\ufe0e'):
        left -= 1
    if left < 0 or not _is_pictographic(ord(content[left])):
        return False
    right = idx + 1
    while right < len(content) and content[right] in ('\ufe0f', '\ufe0e'):
        right += 1
    if right >= len(content) or not _is_pictographic(ord(content[right])):
        return False
    return True


def find_unsafe_invisibles(content, blocklist=BLOCKLIST_INVISIBLES):
    """Return the set of blocklisted invisible chars occurring in content
    in positions that are NOT legitimate emoji ZWJ sequences.

    ZWJ (U+200D) inside an emoji sequence is allowed; all other invisibles in
    the blocklist are flagged on any occurrence. Callers can pass a wider
    blocklist (e.g. skills_guard scans extra bidi-isolate chars); the ZWJ
    emoji-context check still applies.
    """
    flagged = set()
    for char in blocklist:
        if char not in content:
            continue
        if char != '\u200d':
            flagged.add(char)
            continue
        for i, ch in enumerate(content):
            if ch == '\u200d' and not _zwj_in_emoji_context(content, i):
                flagged.add(char)
                break
    return flagged
