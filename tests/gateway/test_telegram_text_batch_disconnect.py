"""Tests for Telegram text batch cleanup on disconnect.

When the Telegram adapter disconnects, it must cancel and clear
_pending_text_batch_tasks and _pending_text_batches in addition to
the already-handled photo batch cleanup.  Otherwise, orphaned asyncio
tasks remain in memory after disconnect.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import MessageEvent, MessageType, SessionSource


def _make_adapter():
    """Create a minimal TelegramAdapter for testing disconnect cleanup."""
    from gateway.platforms.telegram import TelegramAdapter

    config = PlatformConfig(enabled=True, token="test-token")
    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter.config = config
    adapter._pending_text_batches = {}
    adapter._pending_text_batch_tasks = {}
    adapter._text_batch_delay_seconds = 0.1
    adapter._pending_photo_batches = {}
    adapter._pending_photo_batch_tasks = {}
    adapter._media_group_tasks = {}
    adapter._media_group_events = {}
    adapter._pending_photo_batches = {}
    adapter._pending_photo_batch_tasks = {}
    adapter._media_group_tasks = {}
    adapter._media_group_events = {}
    adapter._active_sessions = {}
    adapter._pending_messages = {}
    adapter._message_handler = AsyncMock()
    adapter.handle_message = AsyncMock()
    adapter._app = None
    adapter._bot = None
    adapter._fatal_error_message = None
    adapter._connected = True
    adapter._platform_lock = MagicMock()
    return adapter


def _make_event(text: str, chat_id: str = "12345") -> MessageEvent:
    return MessageEvent(
        text=text,
        message_type=MessageType.TEXT,
        source=SessionSource(platform=Platform.TELEGRAM, chat_id=chat_id, chat_type="dm"),
    )


class TestTextBatchDisconnectCleanup:
    @pytest.mark.asyncio
    async def test_disconnect_cancels_pending_text_batch_tasks(self):
        """disconnect() must cancel and clear _pending_text_batch_tasks."""
        adapter = _make_adapter()

        # Enqueue a text batch so a task is created
        adapter._enqueue_text_event(_make_event("hello"))
        await asyncio.sleep(0.01)  # let task be scheduled

        assert len(adapter._pending_text_batch_tasks) > 0, "Precondition: task should exist"
        task = list(adapter._pending_text_batch_tasks.values())[0]
        assert not task.done(), "Precondition: task should be pending"

        await adapter.disconnect()

        # Task should have been cancelled (may need an event loop tick to complete)
        await asyncio.sleep(0)
        assert task.cancelled() or task.done(), "Task should be cancelled after disconnect"
        # Dicts should be cleared
        assert len(adapter._pending_text_batch_tasks) == 0, (
            "_pending_text_batch_tasks should be empty after disconnect"
        )
        assert len(adapter._pending_text_batches) == 0, (
            "_pending_text_batches should be empty after disconnect"
        )

    @pytest.mark.asyncio
    async def test_disconnect_clears_text_batches_without_tasks(self):
        """disconnect() must clear _pending_text_batches even if no tasks exist."""
        adapter = _make_adapter()

        # Put a batch entry without a corresponding task
        adapter._pending_text_batches["test_key"] = _make_event("orphaned")

        await adapter.disconnect()

        assert len(adapter._pending_text_batches) == 0, (
            "_pending_text_batches should be cleared even without tasks"
        )

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_both_text_and_photo_batches(self):
        """disconnect() must clean up both text AND photo batch state."""
        adapter = _make_adapter()

        # Set up text batches
        adapter._enqueue_text_event(_make_event("text msg"))
        await asyncio.sleep(0.01)

        # Set up photo batches
        adapter._pending_photo_batches["photo_key"] = _make_event("photo")
        photo_task = asyncio.create_task(asyncio.sleep(100))
        adapter._pending_photo_batch_tasks["photo_key"] = photo_task

        await adapter.disconnect()

        # Both should be cleaned
        assert len(adapter._pending_text_batch_tasks) == 0
        assert len(adapter._pending_text_batches) == 0
        assert len(adapter._pending_photo_batch_tasks) == 0
        assert len(adapter._pending_photo_batches) == 0
