"""Tests for the unified fetch_thread_context() hook in BasePlatformAdapter."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, MessageEvent, ProcessingOutcome, SendResult
from gateway.session import SessionSource, build_session_key


# ---------------------------------------------------------------------------
# Minimal DummyAdapter for base class tests
# ---------------------------------------------------------------------------

class DummyAdapter(BasePlatformAdapter):
    """Minimal adapter for testing base class behavior."""

    def __init__(self, platform: Platform = Platform.TELEGRAM):
        super().__init__(PlatformConfig(enabled=True, token="fake"), platform)
        self.sent = []

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        return None

    async def send(self, chat_id, content, reply_to=None, metadata=None) -> SendResult:
        self.sent.append(content)
        return SendResult(success=True, message_id="1")

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        return None

    async def get_chat_info(self, chat_id: str):
        return {"id": chat_id}

    async def on_processing_start(self, event: MessageEvent) -> None:
        pass

    async def on_processing_complete(self, event: MessageEvent, outcome: ProcessingOutcome) -> None:
        pass


class ContextDummyAdapter(DummyAdapter):
    """DummyAdapter that returns context from fetch_thread_context()."""

    def __init__(self, context_to_return: Optional[str] = None):
        super().__init__()
        self.context_to_return = context_to_return

    async def fetch_thread_context(self, event: MessageEvent) -> Optional[str]:
        return self.context_to_return


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_event(
    chat_id: str = "chat1",
    thread_id: Optional[str] = None,
    text: str = "hello",
    platform: Platform = Platform.TELEGRAM,
    user_id: Optional[str] = None,
    raw_message: object = None,
) -> MessageEvent:
    return MessageEvent(
        text=text,
        source=SessionSource(
            platform=platform,
            chat_id=chat_id,
            chat_type="group",
            thread_id=thread_id,
            user_id=user_id,
        ),
        message_id="msg1",
        raw_message=raw_message,
    )


def _make_session_store(entries: dict = None, gspu: bool = True, tspu: bool = False, should_reset=None):
    store = MagicMock()
    store._entries = entries or {}
    store._ensure_loaded = MagicMock()
    store.config = MagicMock()
    store.config.group_sessions_per_user = gspu
    store.config.thread_sessions_per_user = tspu
    # _should_reset returns a reason string if the session should be reset, else None
    store._should_reset = MagicMock(return_value=should_reset)
    return store


# ===========================================================================
# has_active_session_for_event
# ===========================================================================

class TestHasActiveSessionForEvent:
    """Test the base class session-check helper."""

    def test_returns_false_without_session_store(self):
        adapter = DummyAdapter()
        event = _make_event(thread_id="t1")
        assert adapter.has_active_session_for_event(event) is False

    def test_returns_true_when_session_exists(self):
        adapter = DummyAdapter()
        event = _make_event(chat_id="C1", thread_id="1000.0", platform=Platform.TELEGRAM)
        key = build_session_key(event.source, group_sessions_per_user=False, thread_sessions_per_user=False)
        adapter.set_session_store(_make_session_store(entries={key: MagicMock()}, gspu=False))
        assert adapter.has_active_session_for_event(event) is True

    def test_returns_false_when_no_session(self):
        adapter = DummyAdapter()
        event = _make_event(chat_id="C1", thread_id="1000.0")
        adapter.set_session_store(_make_session_store(entries={}))
        assert adapter.has_active_session_for_event(event) is False

    def test_returns_false_on_exception(self):
        adapter = DummyAdapter()
        event = _make_event(thread_id="t1")
        store = MagicMock()
        store._ensure_loaded = MagicMock(side_effect=RuntimeError("broken"))
        store.config = MagicMock()
        store.config.group_sessions_per_user = True
        store.config.thread_sessions_per_user = False
        adapter.set_session_store(store)
        assert adapter.has_active_session_for_event(event) is False

    def test_returns_false_when_session_would_be_reset(self):
        """A session that exists but would be auto-reset (idle/daily) is treated as absent."""
        adapter = DummyAdapter()
        event = _make_event(chat_id="C1", thread_id="1000.0", platform=Platform.TELEGRAM)
        key = build_session_key(event.source, group_sessions_per_user=False, thread_sessions_per_user=False)
        entry = MagicMock()
        store = _make_session_store(entries={key: entry}, gspu=False, should_reset="idle")
        adapter.set_session_store(store)

        assert adapter.has_active_session_for_event(event) is False
        store._should_reset.assert_called_once_with(entry, event.source)

    def test_returns_true_when_session_not_expired(self):
        """A session that exists and is NOT expired is treated as present."""
        adapter = DummyAdapter()
        event = _make_event(chat_id="C1", thread_id="1000.0", platform=Platform.TELEGRAM)
        key = build_session_key(event.source, group_sessions_per_user=False, thread_sessions_per_user=False)
        entry = MagicMock()
        store = _make_session_store(entries={key: entry}, gspu=False, should_reset=None)
        adapter.set_session_store(store)

        assert adapter.has_active_session_for_event(event) is True


# ===========================================================================
# fetch_thread_context — base default
# ===========================================================================

class TestFetchThreadContextBase:
    """Test the base class default (returns None)."""

    @pytest.mark.asyncio
    async def test_default_returns_none(self):
        adapter = DummyAdapter()
        event = _make_event(thread_id="t1")
        result = await adapter.fetch_thread_context(event)
        assert result is None


# ===========================================================================
# _process_message_background integration — context prepended
# ===========================================================================

class TestThreadContextIntegration:
    """Test that _process_message_background prepends thread context."""

    @pytest.mark.asyncio
    async def test_context_prepended_to_event_text(self):
        adapter = ContextDummyAdapter(context_to_return="[Thread context]\nAlice: hi\n[End]\n\n")
        captured_text = []

        async def mock_handler(event):
            captured_text.append(event.text)
            return "ok"

        adapter.set_message_handler(mock_handler)
        event = _make_event(text="my question", thread_id="t1")

        adapter._active_sessions["test_key"] = asyncio.Event()
        await adapter._process_message_background(event, "test_key")

        assert len(captured_text) == 1
        assert captured_text[0].startswith("[Thread context]")
        assert "my question" in captured_text[0]

    @pytest.mark.asyncio
    async def test_no_context_when_none_returned(self):
        adapter = ContextDummyAdapter(context_to_return=None)
        captured_text = []

        async def mock_handler(event):
            captured_text.append(event.text)
            return "ok"

        adapter.set_message_handler(mock_handler)
        event = _make_event(text="my question", thread_id="t1")

        adapter._active_sessions["test_key"] = asyncio.Event()
        await adapter._process_message_background(event, "test_key")

        assert len(captured_text) == 1
        assert captured_text[0] == "my question"

    @pytest.mark.asyncio
    async def test_command_not_prefixed_with_context(self):
        """Commands like /reset should not have thread context prepended."""
        adapter = ContextDummyAdapter(context_to_return="[Thread context]\nAlice: hi\n[End]\n\n")
        captured_text = []

        async def mock_handler(event):
            captured_text.append(event.text)
            return "ok"

        adapter.set_message_handler(mock_handler)
        event = _make_event(text="/reset", thread_id="t1")

        adapter._active_sessions["test_key"] = asyncio.Event()
        await adapter._process_message_background(event, "test_key")

        assert len(captured_text) == 1
        assert captured_text[0] == "/reset"
        assert "[Thread context]" not in captured_text[0]

    @pytest.mark.asyncio
    async def test_command_with_args_not_prefixed(self):
        """Commands with arguments should also be left alone."""
        adapter = ContextDummyAdapter(context_to_return="[Thread context]\n[End]\n\n")
        captured_text = []

        async def mock_handler(event):
            captured_text.append(event.text)
            return "ok"

        adapter.set_message_handler(mock_handler)
        event = _make_event(text="/model claude-sonnet-4-20250514", thread_id="t1")

        adapter._active_sessions["test_key"] = asyncio.Event()
        await adapter._process_message_background(event, "test_key")

        assert len(captured_text) == 1
        assert captured_text[0].startswith("/model")


# ===========================================================================
# Discord fetch_thread_context
# ===========================================================================

def _ensure_discord_mock():
    """Wire up minimal discord.py mocks so DiscordAdapter can be imported."""
    if "discord" in sys.modules and hasattr(sys.modules["discord"], "__file__"):
        return
    discord_mod = MagicMock()
    discord_mod.Thread = type("Thread", (), {})
    discord_mod.DMChannel = type("DMChannel", (), {})
    discord_mod.ForumChannel = type("ForumChannel", (), {})
    discord_mod.Intents.default.return_value = MagicMock()
    discord_mod.Intents.default.return_value.message_content = True
    for name in [
        "discord", "discord.ext", "discord.ext.commands",
        "discord.opus", "discord.sinks",
    ]:
        sys.modules.setdefault(name, discord_mod)


_ensure_discord_mock()

import discord
from gateway.platforms.discord import DiscordAdapter


def _make_discord_adapter():
    config = PlatformConfig(enabled=True, token="fake-discord-token")
    adapter = DiscordAdapter(config)
    adapter._client = MagicMock()
    adapter._client.user = MagicMock()
    adapter._client.user.id = 999
    return adapter


def _make_discord_thread_message(messages, msg_id=100, author_name="Caller", author_id=1):
    """Create a mock Discord message in a thread with history."""
    thread = MagicMock(spec=discord.Thread)

    async def mock_history(limit=30, oldest_first=True):
        for m in messages:
            yield m

    thread.history = mock_history

    message = MagicMock()
    message.id = msg_id
    message.channel = thread
    message.author = MagicMock()
    message.author.id = author_id
    message.author.display_name = author_name
    message.author.name = author_name
    return message


def _make_discord_msg(msg_id, author_id, author_name, content):
    msg = MagicMock()
    msg.id = msg_id
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.author.display_name = author_name
    msg.author.name = author_name
    msg.content = content
    return msg


class TestDiscordFetchThreadContext:
    """Test the Discord adapter's fetch_thread_context() override."""

    @pytest.mark.asyncio
    async def test_fetches_and_formats_context(self):
        adapter = _make_discord_adapter()
        thread_msgs = [
            _make_discord_msg(1, 10, "Alice", "This is the original question"),
            _make_discord_msg(2, 20, "Bob", "I think we should refactor"),
            _make_discord_msg(100, 1, "Caller", "Current message"),  # triggering msg
        ]
        raw_message = _make_discord_thread_message(thread_msgs)
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey bot",
            platform=Platform.DISCORD, raw_message=raw_message,
        )
        adapter.set_session_store(_make_session_store(entries={}))

        context = await adapter.fetch_thread_context(event)

        assert context is not None
        assert "[Thread context" in context
        assert "Alice: This is the original question" in context
        assert "Bob: I think we should refactor" in context
        # Triggering message should be excluded
        assert "Current message" not in context

    @pytest.mark.asyncio
    async def test_skips_bot_messages(self):
        adapter = _make_discord_adapter()
        bot_id = adapter._client.user.id
        thread_msgs = [
            _make_discord_msg(1, 10, "Alice", "Question"),
            _make_discord_msg(2, bot_id, "Bot", "Bot reply (should be skipped)"),
            _make_discord_msg(100, 1, "Caller", "Current"),
        ]
        raw_message = _make_discord_thread_message(thread_msgs)
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey",
            platform=Platform.DISCORD, raw_message=raw_message,
        )
        adapter.set_session_store(_make_session_store(entries={}))

        context = await adapter.fetch_thread_context(event)

        assert context is not None
        assert "Bot reply" not in context
        assert "Alice: Question" in context

    @pytest.mark.asyncio
    async def test_returns_none_when_session_exists(self):
        adapter = _make_discord_adapter()
        thread_msgs = [_make_discord_msg(1, 10, "Alice", "Question")]
        raw_message = _make_discord_thread_message(thread_msgs)
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey",
            platform=Platform.DISCORD, raw_message=raw_message,
        )

        key = build_session_key(event.source, group_sessions_per_user=False, thread_sessions_per_user=False)
        adapter.set_session_store(_make_session_store(entries={key: MagicMock()}, gspu=False))

        context = await adapter.fetch_thread_context(event)
        assert context is None

    @pytest.mark.asyncio
    async def test_returns_none_for_non_thread(self):
        adapter = _make_discord_adapter()
        message = MagicMock()
        message.channel = MagicMock()  # Not a discord.Thread
        event = _make_event(
            chat_id="chan1", text="hey",
            platform=Platform.DISCORD, raw_message=message,
        )

        context = await adapter.fetch_thread_context(event)
        assert context is None

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_thread(self):
        adapter = _make_discord_adapter()
        raw_message = _make_discord_thread_message(
            [_make_discord_msg(100, 1, "Caller", "Current")],
        )
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey",
            platform=Platform.DISCORD, raw_message=raw_message,
        )
        adapter.set_session_store(_make_session_store(entries={}))

        context = await adapter.fetch_thread_context(event)
        # Only the triggering message exists, which is excluded
        assert context is None

    @pytest.mark.asyncio
    async def test_strips_bot_mentions(self):
        adapter = _make_discord_adapter()
        bot_id = adapter._client.user.id
        thread_msgs = [
            _make_discord_msg(1, 10, "Alice", f"hey <@{bot_id}> what do you think?"),
            _make_discord_msg(100, 1, "Caller", "Current"),
        ]
        raw_message = _make_discord_thread_message(thread_msgs)
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey",
            platform=Platform.DISCORD, raw_message=raw_message,
        )
        adapter.set_session_store(_make_session_store(entries={}))

        context = await adapter.fetch_thread_context(event)

        assert context is not None
        assert f"<@{bot_id}>" not in context
        assert "what do you think?" in context

    @pytest.mark.asyncio
    async def test_api_failure_returns_none(self):
        adapter = _make_discord_adapter()
        thread = MagicMock(spec=discord.Thread)

        async def broken_history(**kwargs):
            raise RuntimeError("API error")
            # Make it an async generator that raises
            yield  # pragma: no cover

        thread.history = broken_history
        message = MagicMock()
        message.id = 100
        message.channel = thread
        event = _make_event(
            chat_id="chan1", thread_id="thread1", text="hey",
            platform=Platform.DISCORD, raw_message=message,
        )
        adapter.set_session_store(_make_session_store(entries={}))

        context = await adapter.fetch_thread_context(event)
        assert context is None
