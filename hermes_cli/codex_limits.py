"""Fetch and format ChatGPT/Codex plan usage limits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Optional

import httpx

from hermes_cli.auth import AuthError, resolve_codex_runtime_credentials

_LIMITS_URL = "https://chatgpt.com/backend-api/wham/usage"


@dataclass
class LimitWindow:
    label: str
    remaining_percent: int
    reset_after_seconds: int
    reset_at: Optional[int] = None
    window_seconds: int = 0


class CodexLimitsError(RuntimeError):
    """Raised when Codex limits cannot be fetched or parsed."""


def fetch_codex_limits_payload() -> dict[str, Any]:
    """Fetch raw plan usage data from the ChatGPT/Codex backend."""
    try:
        creds = resolve_codex_runtime_credentials(refresh_if_expiring=True)
    except AuthError as exc:
        raise CodexLimitsError(str(exc)) from exc

    access_token = str(creds.get("api_key") or "").strip()
    if not access_token:
        raise CodexLimitsError("Could not resolve a Codex access token.")

    try:
        response = httpx.get(
            _LIMITS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "Hermes-Agent/1.0",
            },
            timeout=15,
        )
    except Exception as exc:
        raise CodexLimitsError(f"Could not fetch Codex limits: {exc}") from exc

    if response.status_code == 401:
        raise CodexLimitsError("Codex OAuth is expired or invalid. Run hermes auth to re-authenticate.")
    if response.status_code == 403:
        raise CodexLimitsError("Access to the Codex limits endpoint is forbidden for this account.")
    if response.status_code == 404:
        raise CodexLimitsError("The Codex limits endpoint was not found. OpenAI may have changed the API again.")
    if response.status_code != 200:
        detail = response.text.strip()
        if len(detail) > 300:
            detail = detail[:300] + "…"
        raise CodexLimitsError(
            f"Codex limits endpoint returned HTTP {response.status_code}: {detail or 'empty response body'}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise CodexLimitsError(f"Codex limits endpoint returned a non-JSON response: {exc}") from exc

    if not isinstance(data, dict):
        raise CodexLimitsError("Codex limits endpoint returned an unexpected response format.")
    return data


def _window_label(window_seconds: Any) -> str:
    try:
        seconds = int(window_seconds)
    except (TypeError, ValueError):
        return "Unknown window"

    mapping = {
        60: "1 minute",
        300: "5 minutes",
        3600: "1 hour",
        18000: "5 hours",
        21600: "6 hours",
        43200: "12 hours",
        86400: "1 day",
        604800: "Weekly",
        2592000: "Monthly",
    }
    if seconds in mapping:
        return mapping[seconds]
    if seconds % 86400 == 0 and seconds >= 86400:
        days = seconds // 86400
        return f"{days} days" if days != 1 else "1 day"
    if seconds % 3600 == 0 and seconds >= 3600:
        hours = seconds // 3600
        return f"{hours} hours" if hours != 1 else "1 hour"
    return f"{seconds} seconds"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_window(raw: Any, *, fallback_label: Optional[str] = None) -> Optional[LimitWindow]:
    if not isinstance(raw, dict):
        return None
    limit_window_seconds = _safe_int(raw.get("limit_window_seconds"))
    used_percent = max(0, min(100, _safe_int(raw.get("used_percent"))))
    remaining_percent = max(0, 100 - used_percent)
    reset_after_seconds = max(0, _safe_int(raw.get("reset_after_seconds")))
    reset_at = raw.get("reset_at")
    reset_at_int = _safe_int(reset_at, 0) or None
    label = fallback_label or _window_label(limit_window_seconds)
    return LimitWindow(
        label=label,
        remaining_percent=remaining_percent,
        reset_after_seconds=reset_after_seconds,
        reset_at=reset_at_int,
        window_seconds=limit_window_seconds,
    )


def _extract_named_windows(limit_block: Any, *, name_prefix: str = "") -> List[LimitWindow]:
    if not isinstance(limit_block, dict):
        return []

    windows: List[LimitWindow] = []
    prefix = f"{name_prefix}: " if name_prefix else ""
    for key in ("primary_window", "secondary_window"):
        window = _normalize_window(limit_block.get(key))
        if window is not None:
            if prefix:
                window.label = prefix + window.label
            windows.append(window)
    return windows


def extract_codex_limit_windows(payload: dict[str, Any]) -> List[LimitWindow]:
    """Extract the limit windows that actually exist in the API response."""
    windows: List[LimitWindow] = []
    windows.extend(_extract_named_windows(payload.get("rate_limit")))

    code_review = payload.get("code_review_rate_limit")
    if isinstance(code_review, dict):
        windows.extend(_extract_named_windows(code_review, name_prefix="Code review"))

    additional = payload.get("additional_rate_limits")
    if isinstance(additional, list):
        for item in additional:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("label") or item.get("type") or "Additional limit").strip()
            windows.extend(_extract_named_windows(item, name_prefix=name))
    elif isinstance(additional, dict):
        for key, value in additional.items():
            title = str(key).strip() or "Additional limit"
            windows.extend(_extract_named_windows(value, name_prefix=title))

    deduped: List[LimitWindow] = []
    seen: set[tuple[str, int, int, Optional[int], int]] = set()
    for window in windows:
        sig = (window.label, window.remaining_percent, window.reset_after_seconds, window.reset_at, window.window_seconds)
        if sig not in seen:
            deduped.append(window)
            seen.add(sig)
    return deduped


def _format_duration_hms(total_seconds: int) -> str:
    seconds = max(0, int(total_seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_codex_limits(payload: dict[str, Any]) -> str:
    """Render the limits response in concise English text."""
    windows = extract_codex_limit_windows(payload)
    if not windows:
        return "Limits:\nNo limit windows were found in the API response."

    lines = ["Limits:"]
    for index, window in enumerate(windows):
        lines.append(f"{window.label}: {window.remaining_percent}% remaining.")
        if window.reset_at and window.window_seconds >= 604800:
            dt = datetime.fromtimestamp(window.reset_at, tz=timezone.utc)
            lines.append(f"Reset {dt.strftime('%b %d at %H:%M GMT')}")
        else:
            lines.append(f"Resets in {_format_duration_hms(window.reset_after_seconds)}.")
        if index != len(windows) - 1:
            lines.append("")
    return "\n".join(lines)


def should_show_codex_limits(provider: Any = None, base_url: Any = None) -> bool:
    """Return True when the current session is using the ChatGPT/Codex backend."""
    provider_text = str(provider or "").strip().lower()
    base_url_text = str(base_url or "").strip().lower()
    return provider_text == "openai-codex" or "chatgpt.com/backend-api/codex" in base_url_text


def get_codex_limits_text() -> str:
    """Fetch and format the current Codex limits in one call."""
    payload = fetch_codex_limits_payload()
    return format_codex_limits(payload)
