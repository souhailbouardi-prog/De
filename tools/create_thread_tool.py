"""Create Discord Thread Tool -- REST-based thread creation without a running gateway.

Creates a Discord thread in a specified channel using the Discord REST API.
Works identically to send_message (aiohttp + bot token) — no discord.js client
or slash-command interaction required.

Supports two creation modes:
  1. Standalone thread (no parent message) — POST /channels/{id}/threads
  2. Thread from a message — POST /channels/{id}/messages/{msg_id}/threads

Optionally sends an initial message into the newly created thread.
"""

import json
import logging
import os

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_VALID_AUTO_ARCHIVE = {60, 1440, 4320, 10080}

CREATE_THREAD_SCHEMA = {
    "name": "create_thread",
    "description": (
        "Create a Discord thread in a channel. Returns the thread ID and name. "
        "Optionally posts an initial message into the new thread. "
        "Requires DISCORD_BOT_TOKEN to be configured."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "The Discord channel ID where the thread will be created.",
            },
            "name": {
                "type": "string",
                "description": "Name for the new thread (max 100 characters).",
            },
            "message": {
                "type": "string",
                "description": "Optional initial message to send into the new thread after creation.",
            },
            "message_id": {
                "type": "string",
                "description": "Optional message ID to create the thread from. If omitted, creates a standalone thread.",
            },
            "auto_archive_duration": {
                "type": "integer",
                "description": "Auto-archive duration in minutes. One of: 60, 1440 (default), 4320, 10080.",
                "enum": [60, 1440, 4320, 10080],
            },
        },
        "required": ["channel_id", "name"],
    },
}


def _get_discord_token() -> str | None:
    """Retrieve the Discord bot token from config or env."""
    # Try env first
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if token:
        return token

    # Fall back to gateway config
    try:
        from gateway.config import load_gateway_config, Platform
        config = load_gateway_config()
        pconfig = config.platforms.get(Platform.DISCORD)
        if pconfig and pconfig.token:
            return pconfig.token
    except Exception:
        pass

    return None


async def _create_discord_thread(
    token: str,
    channel_id: str,
    name: str,
    message_id: str | None = None,
    auto_archive_duration: int = 1440,
) -> dict:
    """Create a Discord thread via REST API.

    Returns a dict with thread_id, thread_name on success, or error on failure.
    """
    try:
        import aiohttp
    except ImportError:
        return {"error": "aiohttp not installed. Run: pip install aiohttp"}

    from gateway.platforms.base import resolve_proxy_url, proxy_kwargs_for_aiohttp

    _proxy = resolve_proxy_url(platform_env_var="DISCORD_PROXY")
    _sess_kw, _req_kw = proxy_kwargs_for_aiohttp(_proxy)

    headers = {"Authorization": f"Bot {token}"}

    # Build the endpoint URL
    if message_id:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/threads"
    else:
        url = f"https://discord.com/api/v10/channels/{channel_id}/threads"

    body = {
        "name": name[:100],
        "auto_archive_duration": auto_archive_duration,
        "type": 11,  # Public thread (type 12 = private thread)
    }

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30), **_sess_kw
    ) as session:
        # Create the thread
        async with session.post(
            url, headers={**headers, "Content-Type": "application/json"},
            json=body, **_req_kw,
        ) as resp:
            if resp.status not in (200, 201):
                error_body = await resp.text()
                return {"error": f"Discord API error ({resp.status}): {error_body}"}
            thread_data = await resp.json()

    thread_id = thread_data.get("id")
    thread_name = thread_data.get("name", name)

    if not thread_id:
        return {"error": "Discord API returned thread data without an ID"}

    return {
        "success": True,
        "thread_id": str(thread_id),
        "thread_name": thread_name,
    }


async def _send_discord_message_to_thread(
    token: str,
    thread_id: str,
    message: str,
) -> dict:
    """Send a message to a Discord thread via REST API."""
    try:
        import aiohttp
    except ImportError:
        return {"error": "aiohttp not installed. Run: pip install aiohttp"}

    from gateway.platforms.base import resolve_proxy_url, proxy_kwargs_for_aiohttp

    _proxy = resolve_proxy_url(platform_env_var="DISCORD_PROXY")
    _sess_kw, _req_kw = proxy_kwargs_for_aiohttp(_proxy)

    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    headers = {**{"Authorization": f"Bot {token}"}, "Content-Type": "application/json"}

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30), **_sess_kw
    ) as session:
        async with session.post(
            url, headers=headers, json={"content": message}, **_req_kw,
        ) as resp:
            if resp.status not in (200, 201):
                error_body = await resp.text()
                return {"error": f"Failed to send message ({resp.status}): {error_body}"}
            msg_data = await resp.json()

    return {"success": True, "message_id": msg_data.get("id")}


def create_thread_tool(args, **kw) -> str:
    """Handle create_thread tool calls."""
    channel_id = args.get("channel_id", "").strip()
    name = args.get("name", "").strip()
    message = args.get("message", "").strip() or None
    message_id = args.get("message_id", "").strip() or None
    auto_archive_duration = args.get("auto_archive_duration", 1440)

    if not channel_id:
        return tool_error("channel_id is required")
    if not name:
        return tool_error("Thread name is required")
    if auto_archive_duration not in _VALID_AUTO_ARCHIVE:
        allowed = ", ".join(str(v) for v in sorted(_VALID_AUTO_ARCHIVE))
        return tool_error(f"auto_archive_duration must be one of: {allowed}")

    token = _get_discord_token()
    if not token:
        return tool_error(
            "Discord bot token not found. Set DISCORD_BOT_TOKEN env var "
            "or configure Discord in ~/.hermes/config.yaml"
        )

    try:
        from model_tools import _run_async

        # Step 1: Create the thread
        result = _run_async(
            _create_discord_thread(
                token,
                channel_id,
                name,
                message_id=message_id,
                auto_archive_duration=auto_archive_duration,
            )
        )
        result_dict = json.loads(result) if isinstance(result, str) else result

        if not result_dict.get("success"):
            return json.dumps(result_dict)

        thread_id = result_dict["thread_id"]

        # Step 2: Send initial message if provided
        if message:
            msg_result = _run_async(
                _send_discord_message_to_thread(token, thread_id, message)
            )
            msg_dict = json.loads(msg_result) if isinstance(msg_result, str) else msg_result
            if msg_dict.get("success"):
                result_dict["initial_message_id"] = msg_dict.get("message_id")
            else:
                result_dict["message_warning"] = msg_dict.get("error", "Failed to send initial message")

        return json.dumps(result_dict)

    except Exception as e:
        return tool_error(f"Thread creation failed: {e}")


def _check_create_thread():
    """Gate create_thread on Discord being configured."""
    token = _get_discord_token()
    return bool(token)


# --- Registry ---
registry.register(
    name="create_thread",
    toolset="messaging",
    schema=CREATE_THREAD_SCHEMA,
    handler=create_thread_tool,
    check_fn=_check_create_thread,
    emoji="🧵",
)
