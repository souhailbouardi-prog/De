"""WhatsApp Ultimate tools — extended WhatsApp features via the local Baileys bridge.

These tools expose group management, polls, reactions, search, and other advanced
WhatsApp features that go beyond basic send/receive.
"""

import aiohttp
import logging
import os
from typing import Any, Dict, List, Optional

from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

_BRIDGE_PORT = int(os.getenv("WHATSAPP_BRIDGE_PORT", "3000"))
_BRIDGE_URL = f"http://127.0.0.1:{_BRIDGE_PORT}"


def _error(msg: str) -> Dict[str, Any]:
    return {"error": msg}


async def _bridge_get(path: str, params: Optional[Dict] = None, timeout: float = 15) -> Dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{_BRIDGE_URL}{path}",
                params=params or {},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                return await resp.json()
    except Exception as e:
        return _error(str(e))


async def _bridge_post(path: str, json: Dict, timeout: float = 15) -> Dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{_BRIDGE_URL}{path}",
                json=json,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                return await resp.json()
    except Exception as e:
        return _error(str(e))


async def _bridge_delete(path: str, json: Dict, timeout: float = 10) -> Dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{_BRIDGE_URL}{path}",
                json=json,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                return await resp.json()
    except Exception as e:
        return _error(str(e))


# -----------------------------------------------------------------------
# Tool functions
# -----------------------------------------------------------------------

async def whatsapp_search(query: str, chat_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Search WhatsApp messages using full-text search.
    
    Searches the local message history (stored in SQLite with FTS5) for messages
    matching the query string. Optionally filter to a specific chat.
    
    Args:
        query: Search term (supports FTS5 query syntax)
        chat_id: Optional — restrict search to this WhatsApp chat
        limit: Maximum results to return (default 50)
    """
    params = {"q": query, "limit": str(limit)}
    if chat_id:
        params["chat_id"] = chat_id
    return await _bridge_get("/search", params)


async def whatsapp_backfill(chat_id: str, limit: int = 50) -> Dict[str, Any]:
    """Backfill historical messages from WhatsApp into local storage.
    
    Fetches old messages from WhatsApp servers and stores them in the local
    SQLite database for search and history access.
    
    Args:
        chat_id: WhatsApp chat ID to backfill (e.g. "123456789@s.whatsapp.net" or group JID)
        limit: Maximum messages to fetch (default 50, max 10000)
    """
    return await _bridge_post("/backfill", {"chat_id": chat_id, "limit": limit}, timeout=60)


async def whatsapp_list_groups() -> Dict[str, Any]:
    """List all WhatsApp groups the account participates in.
    
    Returns group JIDs, names, descriptions, participant counts, and settings.
    """
    return await _bridge_get("/groups")


async def whatsapp_create_group(name: str, participants: List[str]) -> Dict[str, Any]:
    """Create a new WhatsApp group.
    
    Args:
        name: Group subject/title
        participants: List of phone numbers or WhatsApp IDs to add initially
    """
    return await _bridge_post("/group/create", {"name": name, "participants": participants})


async def whatsapp_group_rename(chat_id: str, name: str) -> Dict[str, Any]:
    """Rename a WhatsApp group (change the subject/title).
    
    Args:
        chat_id: The group JID
        name: New group subject
    """
    return await _bridge_post("/group/rename", {"chat_id": chat_id, "name": name})


async def whatsapp_group_description(chat_id: str, description: str) -> Dict[str, Any]:
    """Set a WhatsApp group's description.
    
    Args:
        chat_id: The group JID
        description: New group description (can be empty to clear)
    """
    return await _bridge_post("/group/description", {"chat_id": chat_id, "description": description})


async def whatsapp_group_participants_add(chat_id: str, participants: List[str]) -> Dict[str, Any]:
    """Add participants to a WhatsApp group.
    
    Args:
        chat_id: The group JID
        participants: List of phone numbers or WhatsApp IDs to add
    """
    return await _bridge_post("/group/participants/add", {"chat_id": chat_id, "participants": participants})


async def whatsapp_group_participants_remove(chat_id: str, participants: List[str]) -> Dict[str, Any]:
    """Remove participants from a WhatsApp group.
    
    Args:
        chat_id: The group JID
        participants: List of phone numbers or WhatsApp IDs to remove
    """
    return await _bridge_post("/group/participants/remove", {"chat_id": chat_id, "participants": participants})


async def whatsapp_group_participants_promote(chat_id: str, participants: List[str]) -> Dict[str, Any]:
    """Promote participants to admin in a WhatsApp group.
    
    Args:
        chat_id: The group JID
        participants: List of phone numbers or WhatsApp IDs to promote
    """
    return await _bridge_post("/group/participants/promote", {"chat_id": chat_id, "participants": participants})


async def whatsapp_group_invite_link(chat_id: str) -> Dict[str, Any]:
    """Get the invite link for a WhatsApp group.
    
    Args:
        chat_id: The group JID
    
    Returns:
        invite_link: The group invite URL
    """
    return await _bridge_get("/group/invite-link", {"chat_id": chat_id})


async def whatsapp_group_invite_link_revoke(chat_id: str) -> Dict[str, Any]:
    """Revoke the current invite link and generate a new one for a WhatsApp group.
    
    Args:
        chat_id: The group JID
    
    Returns:
        invite_link: The new group invite URL
    """
    return await _bridge_post("/group/invite-link/revoke", {"chat_id": chat_id})


async def whatsapp_group_leave(chat_id: str) -> Dict[str, Any]:
    """Leave a WhatsApp group.
    
    Args:
        chat_id: The group JID to leave
    """
    return await _bridge_post("/group/leave", {"chat_id": chat_id})


async def whatsapp_send_reaction(chat_id: str, message_id: str, emoji: str) -> Dict[str, Any]:
    """Send an emoji reaction to a specific message.
    
    Args:
        chat_id: The chat JID where the message is
        message_id: The message ID to react to
        emoji: Single emoji character (e.g. "👍", "❤️", "😂")
    """
    return await _bridge_post("/react", {"chat_id": chat_id, "message_id": message_id, "emoji": emoji})


async def whatsapp_send_poll(chat_id: str, question: str, options: List[str], multiple_answers: bool = False) -> Dict[str, Any]:
    """Send a poll to a WhatsApp chat.
    
    Args:
        chat_id: The chat JID
        question: Poll question/title
        options: List of poll options (minimum 2, maximum 10)
        multiple_answers: Allow multiple selections per voter (default False)
    """
    return await _bridge_post("/poll", {
        "chat_id": chat_id,
        "question": question,
        "options": options,
        "multiple_answers": multiple_answers,
    })


async def whatsapp_send_sticker(chat_id: str, file_path: str) -> Dict[str, Any]:
    """Send a .webp sticker to a WhatsApp chat.
    
    Args:
        chat_id: The chat JID
        file_path: Absolute path to a .webp sticker file
    """
    return await _bridge_post("/sticker", {"chat_id": chat_id, "file_path": file_path})


async def whatsapp_unsend_message(chat_id: str, message_id: str) -> Dict[str, Any]:
    """Unsend (delete for everyone) a message you sent.
    
    Args:
        chat_id: The chat JID where the message is
        message_id: The message ID to delete
    """
    return await _bridge_delete("/message", {"chat_id": chat_id, "message_id": message_id})


# -----------------------------------------------------------------------
# Schema definitions
# -----------------------------------------------------------------------

_WHATSAPP_SCHEMAS = [
    {
        "name": "whatsapp_search",
        "description": "Search WhatsApp messages using full-text search. Searches the local message history stored in SQLite with FTS5. Optionally filter to a specific chat.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term (supports FTS5 query syntax)"},
                "chat_id": {"type": "string", "description": "Optional — restrict search to this WhatsApp chat ID"},
                "limit": {"type": "integer", "description": "Maximum results to return (default 50)", "default": 50},
            },
            "required": ["query"],
        },
    },
    {
        "name": "whatsapp_backfill",
        "description": "Backfill historical messages from WhatsApp into local SQLite storage for search and history access.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "WhatsApp chat ID to backfill"},
                "limit": {"type": "integer", "description": "Maximum messages to fetch (default 50)", "default": 50},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "whatsapp_list_groups",
        "description": "List all WhatsApp groups the account participates in. Returns group JIDs, names, descriptions, and participant counts.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "whatsapp_create_group",
        "description": "Create a new WhatsApp group with a name and optional initial participants.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Group subject/title"},
                "participants": {"type": "array", "items": {"type": "string"}, "description": "List of phone numbers or WhatsApp IDs to add initially"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "whatsapp_group_rename",
        "description": "Rename a WhatsApp group (change the subject/title).",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
                "name": {"type": "string", "description": "New group subject"},
            },
            "required": ["chat_id", "name"],
        },
    },
    {
        "name": "whatsapp_group_description",
        "description": "Set or update a WhatsApp group's description.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
                "description": {"type": "string", "description": "New group description (can be empty to clear)"},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "whatsapp_group_participants_add",
        "description": "Add participants to a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
                "participants": {"type": "array", "items": {"type": "string"}, "description": "List of phone numbers or WhatsApp IDs to add"},
            },
            "required": ["chat_id", "participants"],
        },
    },
    {
        "name": "whatsapp_group_participants_remove",
        "description": "Remove participants from a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
                "participants": {"type": "array", "items": {"type": "string"}, "description": "List of phone numbers or WhatsApp IDs to remove"},
            },
            "required": ["chat_id", "participants"],
        },
    },
    {
        "name": "whatsapp_group_participants_promote",
        "description": "Promote participants to admin in a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
                "participants": {"type": "array", "items": {"type": "string"}, "description": "List of phone numbers or WhatsApp IDs to promote to admin"},
            },
            "required": ["chat_id", "participants"],
        },
    },
    {
        "name": "whatsapp_group_invite_link",
        "description": "Get the invite link for a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "whatsapp_group_invite_link_revoke",
        "description": "Revoke the current invite link and generate a new one for a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID"},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "whatsapp_group_leave",
        "description": "Leave a WhatsApp group.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The group JID to leave"},
            },
            "required": ["chat_id"],
        },
    },
    {
        "name": "whatsapp_send_reaction",
        "description": "Send an emoji reaction to a specific message.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat JID where the message is"},
                "message_id": {"type": "string", "description": "The message ID to react to"},
                "emoji": {"type": "string", "description": "Single emoji character (e.g. '👍', '❤️', '😂')"},
            },
            "required": ["chat_id", "message_id", "emoji"],
        },
    },
    {
        "name": "whatsapp_send_poll",
        "description": "Send a poll to a WhatsApp chat where group members can vote.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat JID"},
                "question": {"type": "string", "description": "Poll question/title"},
                "options": {"type": "array", "items": {"type": "string"}, "description": "List of poll options (minimum 2, maximum 10)"},
                "multiple_answers": {"type": "boolean", "description": "Allow multiple selections per voter", "default": False},
            },
            "required": ["chat_id", "question", "options"],
        },
    },
    {
        "name": "whatsapp_send_sticker",
        "description": "Send a .webp sticker to a WhatsApp chat.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat JID"},
                "file_path": {"type": "string", "description": "Absolute path to a .webp sticker file"},
            },
            "required": ["chat_id", "file_path"],
        },
    },
    {
        "name": "whatsapp_unsend_message",
        "description": "Unsend (delete for everyone) a message you sent. Only works for your own messages.",
        "parameters": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "The chat JID where the message is"},
                "message_id": {"type": "string", "description": "The message ID to delete"},
            },
            "required": ["chat_id", "message_id"],
        },
    },
]

_WHATSAPP_SCHEMA_MAP = {s["name"]: s for s in _WHATSAPP_SCHEMAS}

# -----------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------

registry.register(
    name="whatsapp_search",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_search"],
    handler=lambda args, **kw: whatsapp_search(
        query=args.get("query"),
        chat_id=args.get("chat_id"),
        limit=args.get("limit", 50),
    ),
    emoji="🔍",
)

registry.register(
    name="whatsapp_backfill",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_backfill"],
    handler=lambda args, **kw: whatsapp_backfill(
        chat_id=args.get("chat_id"),
        limit=args.get("limit", 50),
    ),
    emoji="📥",
)

registry.register(
    name="whatsapp_list_groups",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_list_groups"],
    handler=lambda args, **kw: whatsapp_list_groups(),
    emoji="👥",
)

registry.register(
    name="whatsapp_create_group",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_create_group"],
    handler=lambda args, **kw: whatsapp_create_group(
        name=args.get("name"),
        participants=args.get("participants", []),
    ),
    emoji="🆕",
)

registry.register(
    name="whatsapp_group_rename",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_rename"],
    handler=lambda args, **kw: whatsapp_group_rename(
        chat_id=args.get("chat_id"),
        name=args.get("name"),
    ),
    emoji="✏️",
)

registry.register(
    name="whatsapp_group_description",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_description"],
    handler=lambda args, **kw: whatsapp_group_description(
        chat_id=args.get("chat_id"),
        description=args.get("description", ""),
    ),
    emoji="📝",
)

registry.register(
    name="whatsapp_group_participants_add",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_participants_add"],
    handler=lambda args, **kw: whatsapp_group_participants_add(
        chat_id=args.get("chat_id"),
        participants=args.get("participants", []),
    ),
    emoji="➕",
)

registry.register(
    name="whatsapp_group_participants_remove",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_participants_remove"],
    handler=lambda args, **kw: whatsapp_group_participants_remove(
        chat_id=args.get("chat_id"),
        participants=args.get("participants", []),
    ),
    emoji="➖",
)

registry.register(
    name="whatsapp_group_participants_promote",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_participants_promote"],
    handler=lambda args, **kw: whatsapp_group_participants_promote(
        chat_id=args.get("chat_id"),
        participants=args.get("participants", []),
    ),
    emoji="⬆️",
)

registry.register(
    name="whatsapp_group_invite_link",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_invite_link"],
    handler=lambda args, **kw: whatsapp_group_invite_link(chat_id=args.get("chat_id")),
    emoji="🔗",
)

registry.register(
    name="whatsapp_group_invite_link_revoke",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_invite_link_revoke"],
    handler=lambda args, **kw: whatsapp_group_invite_link_revoke(chat_id=args.get("chat_id")),
    emoji="🔄",
)

registry.register(
    name="whatsapp_group_leave",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_group_leave"],
    handler=lambda args, **kw: whatsapp_group_leave(chat_id=args.get("chat_id")),
    emoji="🚪",
)

registry.register(
    name="whatsapp_send_reaction",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_send_reaction"],
    handler=lambda args, **kw: whatsapp_send_reaction(
        chat_id=args.get("chat_id"),
        message_id=args.get("message_id"),
        emoji=args.get("emoji"),
    ),
    emoji="😀",
)

registry.register(
    name="whatsapp_send_poll",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_send_poll"],
    handler=lambda args, **kw: whatsapp_send_poll(
        chat_id=args.get("chat_id"),
        question=args.get("question"),
        options=args.get("options", []),
        multiple_answers=args.get("multiple_answers", False),
    ),
    emoji="📊",
)

registry.register(
    name="whatsapp_send_sticker",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_send_sticker"],
    handler=lambda args, **kw: whatsapp_send_sticker(
        chat_id=args.get("chat_id"),
        file_path=args.get("file_path"),
    ),
    emoji="🎨",
)

registry.register(
    name="whatsapp_unsend_message",
    toolset="hermes-whatsapp",
    schema=_WHATSAPP_SCHEMA_MAP["whatsapp_unsend_message"],
    handler=lambda args, **kw: whatsapp_unsend_message(
        chat_id=args.get("chat_id"),
        message_id=args.get("message_id"),
    ),
    emoji="🗑️",
)
