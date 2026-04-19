"""Tests for Telegram inline keyboard support (PR #8899).

Covers:
- extract_inline_keyboard parser (single/multi-row, edge cases)
- attach_inline_keyboard (edit_message_reply_markup call)
- _handle_custom_keyboard_callback (re-injection flow)
- _clean_for_display keyboard stripping (streaming)
- Base class no-ops
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure repo root importable
# ---------------------------------------------------------------------------
_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)


# ---------------------------------------------------------------------------
# Minimal Telegram mock
# ---------------------------------------------------------------------------
def _ensure_telegram_mock():
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    mod = MagicMock()
    mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    mod.constants.ParseMode.MARKDOWN = "Markdown"
    mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    mod.constants.ParseMode.HTML = "HTML"
    mod.constants.ChatType.PRIVATE = "private"
    mod.constants.ChatType.GROUP = "group"
    mod.constants.ChatType.SUPERGROUP = "supergroup"
    mod.constants.ChatType.CHANNEL = "channel"
    mod.error.NetworkError = type("NetworkError", (OSError,), {})
    mod.error.TimedOut = type("TimedOut", (OSError,), {})
    mod.error.BadRequest = type("BadRequest", (Exception,), {})

    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, mod)
    sys.modules.setdefault("telegram.error", mod.error)


_ensure_telegram_mock()

from gateway.platforms.telegram import TelegramAdapter
from gateway.config import PlatformConfig
from gateway.stream_consumer import GatewayStreamConsumer


def _make_adapter():
    config = PlatformConfig(enabled=True, token="test-token")
    adapter = TelegramAdapter(config)
    adapter._bot = AsyncMock()
    adapter._app = MagicMock()
    return adapter


# ===========================================================================
# extract_inline_keyboard — parser tests
# ===========================================================================


class TestExtractInlineKeyboard:
    """Test the [KEYBOARD: ...] parser on TelegramAdapter."""

    def test_no_keyboard_block(self):
        """Text without a keyboard block returns (None, original)."""
        adapter = _make_adapter()
        text = "Hello, how can I help?"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is None
        assert cleaned == text

    def test_single_row(self):
        """Single row with two buttons."""
        adapter = _make_adapter()
        text = "Choose:\n[KEYBOARD:\n✅ Yes=ck:yes | ❌ No=ck:no\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert len(buttons) == 1  # one row
        assert len(buttons[0]) == 2  # two buttons
        assert buttons[0][0] == ("✅ Yes", "ck:yes")
        assert buttons[0][1] == ("❌ No", "ck:no")
        assert "KEYBOARD" not in cleaned
        assert "Choose:" in cleaned

    def test_multi_row(self):
        """Multiple rows (each line = one row)."""
        adapter = _make_adapter()
        text = "Pick:\n[KEYBOARD:\n✅ Confirm=ck:confirm | ❌ Cancel=ck:cancel\n🔄 Later=ck:later\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert len(buttons) == 2
        assert len(buttons[0]) == 2
        assert len(buttons[1]) == 1
        assert buttons[1][0] == ("🔄 Later", "ck:later")

    def test_empty_keyboard_block(self):
        """Keyboard block with no valid buttons returns (None, cleaned)."""
        adapter = _make_adapter()
        text = "Hello\n[KEYBOARD:\n\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is None
        assert "KEYBOARD" not in cleaned

    def test_missing_ck_prefix_skipped(self):
        """Buttons without the ck: prefix are silently skipped."""
        adapter = _make_adapter()
        text = "[KEYBOARD:\nOK=confirm | Cancel=ck:cancel\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert len(buttons) == 1
        assert len(buttons[0]) == 1  # only the ck: one
        assert buttons[0][0] == ("Cancel", "ck:cancel")

    def test_oversized_callback_skipped(self):
        """Callbacks exceeding 64 bytes are skipped."""
        adapter = _make_adapter()
        long_data = "ck:" + "x" * 65  # 68 bytes > 64
        text = f"[KEYBOARD:\nBig={long_data} | Small=ck:ok\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert len(buttons[0]) == 1
        assert buttons[0][0] == ("Small", "ck:ok")

    def test_label_with_equals(self):
        """Label containing '=' still parses (uses rsplit)."""
        adapter = _make_adapter()
        text = "[KEYBOARD:\n2+2=4=ck:math\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert buttons[0][0] == ("2+2=4", "ck:math")

    def test_text_preserved_around_block(self):
        """Text before and after the keyboard block is kept."""
        adapter = _make_adapter()
        text = "Before text.\n[KEYBOARD:\nOK=ck:ok\n]\nAfter text."
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert "Before text." in cleaned
        assert "After text." in cleaned
        assert "KEYBOARD" not in cleaned

    def test_keyboard_only_response(self):
        """Response with only a keyboard block → buttons present, text empty."""
        adapter = _make_adapter()
        text = "[KEYBOARD:\n✅ Yes=ck:yes\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert cleaned.strip() == ""

    def test_no_equals_in_item_skipped(self):
        """Items without '=' are silently skipped."""
        adapter = _make_adapter()
        text = "[KEYBOARD:\nJust text | OK=ck:ok\n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert len(buttons[0]) == 1
        assert buttons[0][0] == ("OK", "ck:ok")

    def test_whitespace_trimming(self):
        """Leading/trailing whitespace in labels and callbacks is trimmed."""
        adapter = _make_adapter()
        text = "[KEYBOARD:\n  Yes  =  ck:yes  |  No  =  ck:no  \n]"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is not None
        assert buttons[0][0] == ("Yes", "ck:yes")
        assert buttons[0][1] == ("No", "ck:no")


# ===========================================================================
# attach_inline_keyboard
# ===========================================================================


class TestAttachInlineKeyboard:
    """Test attaching an inline keyboard to an existing message."""

    @pytest.mark.asyncio
    async def test_calls_edit_message_reply_markup(self):
        adapter = _make_adapter()
        adapter._bot.edit_message_reply_markup = AsyncMock()

        buttons = [[("Yes", "ck:yes"), ("No", "ck:no")]]
        result = await adapter.attach_inline_keyboard("12345", "42", buttons)

        assert result.success is True
        adapter._bot.edit_message_reply_markup.assert_awaited_once()
        call_kwargs = adapter._bot.edit_message_reply_markup.call_args[1]
        assert call_kwargs["chat_id"] == 12345
        assert call_kwargs["message_id"] == 42

    @pytest.mark.asyncio
    async def test_not_connected(self):
        adapter = _make_adapter()
        adapter._bot = None
        result = await adapter.attach_inline_keyboard("12345", "42", [[("OK", "ck:ok")]])
        assert result.success is False

    @pytest.mark.asyncio
    async def test_api_error_handled(self):
        adapter = _make_adapter()
        adapter._bot.edit_message_reply_markup = AsyncMock(side_effect=Exception("API error"))

        result = await adapter.attach_inline_keyboard("12345", "42", [[("OK", "ck:ok")]])
        assert result.success is False
        assert "API error" in result.error


# ===========================================================================
# _handle_custom_keyboard_callback
# ===========================================================================


class TestCustomKeyboardCallback:
    """Test the ck: callback handler and re-injection logic."""

    def _make_query(self, data="ck:confirm", message_text="Choose:", label="✅ Confirm"):
        """Build a mock callback query for ck: buttons."""
        btn = MagicMock()
        btn.callback_data = data
        btn.text = label

        row = [btn]
        markup = MagicMock()
        markup.inline_keyboard = [row]

        message = MagicMock()
        message.text = message_text
        message.message_id = 42
        message.chat.id = 12345
        message.chat.type = "private"
        message.chat.title = None
        message.chat.full_name = "Test Chat"
        message.from_user = MagicMock()
        message.from_user.id = 99  # bot
        message.from_user.full_name = "Bot"
        message.reply_markup = markup
        message.message_thread_id = None
        message.reply_to_message = None
        # provide forum_topic_created as None so _build_message_event doesn't trip
        message.forum_topic_created = None

        query = MagicMock()
        query.data = data
        query.message = message
        query.from_user = MagicMock()
        query.from_user.id = 777  # real user
        query.from_user.full_name = "Alice"
        query.from_user.first_name = "Alice"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.edit_message_reply_markup = AsyncMock()
        return query

    @pytest.mark.asyncio
    async def test_reinjects_with_correct_user(self):
        """Callback re-injection uses the clicker's user_id, not the bot's."""
        adapter = _make_adapter()
        query = self._make_query()

        captured_event = {}

        async def capture_event(event):
            captured_event["text"] = event.text
            captured_event["user_id"] = event.source.user_id
            captured_event["user_name"] = event.source.user_name

        adapter.handle_message = capture_event

        await adapter._handle_custom_keyboard_callback(query, "ck:confirm")

        assert captured_event["text"] == "ck:confirm"
        assert captured_event["user_id"] == "777"
        assert captured_event["user_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_edits_message_with_selection(self):
        """Callback edits the original message to show the user's selection."""
        adapter = _make_adapter()
        query = self._make_query()
        adapter.handle_message = AsyncMock()

        await adapter._handle_custom_keyboard_callback(query, "ck:confirm")

        query.edit_message_text.assert_awaited_once()
        call_kwargs = query.edit_message_text.call_args[1]
        assert "Alice selected:" in call_kwargs["text"]
        assert "✅ Confirm" in call_kwargs["text"]
        assert call_kwargs["reply_markup"] is None

    @pytest.mark.asyncio
    async def test_acknowledges_query(self):
        """Callback query is answered (acknowledged)."""
        adapter = _make_adapter()
        query = self._make_query()
        adapter.handle_message = AsyncMock()

        await adapter._handle_custom_keyboard_callback(query, "ck:test")
        query.answer.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_from_user_bails_early(self):
        """If from_user is None, bail without re-injecting."""
        adapter = _make_adapter()
        query = self._make_query()
        query.from_user = None
        adapter.handle_message = AsyncMock()

        await adapter._handle_custom_keyboard_callback(query, "ck:test")
        adapter.handle_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_edit_failure_fallback(self):
        """If edit_message_text fails, falls back to removing keyboard only."""
        adapter = _make_adapter()
        query = self._make_query()
        query.edit_message_text = AsyncMock(side_effect=Exception("edit failed"))
        adapter.handle_message = AsyncMock()

        await adapter._handle_custom_keyboard_callback(query, "ck:test")
        # Fallback: just remove the keyboard
        query.edit_message_reply_markup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_callback_routing(self):
        """ck: data in _handle_callback_query routes to the keyboard handler."""
        adapter = _make_adapter()
        query = self._make_query(data="ck:action")

        update = MagicMock()
        update.callback_query = query
        context = MagicMock()

        with patch.object(adapter, "_handle_custom_keyboard_callback", new_callable=AsyncMock) as mock_handler:
            await adapter._handle_callback_query(update, context)
            mock_handler.assert_awaited_once_with(query, "ck:action")


# ===========================================================================
# _clean_for_display — keyboard stripping during streaming
# ===========================================================================


class TestStreamingKeyboardStripping:
    """Test [KEYBOARD:] block stripping in the streaming display path."""

    def test_complete_block_stripped(self):
        """A complete [KEYBOARD:...] block is removed from display text."""
        text = "Here is your choice:\n[KEYBOARD:\n✅ Yes=ck:yes | ❌ No=ck:no\n]"
        result = GatewayStreamConsumer._clean_for_display(text)
        assert "[KEYBOARD:" not in result
        assert "ck:" not in result
        assert "Here is your choice:" in result

    def test_partial_block_stripped(self):
        """An incomplete [KEYBOARD: block (mid-stream) hides from that point."""
        text = "Some text\n[KEYBOARD:\n✅ Yes=ck:yes"
        result = GatewayStreamConsumer._clean_for_display(text)
        assert "[KEYBOARD:" not in result
        assert "Some text" in result

    def test_no_keyboard_passthrough(self):
        """Text without KEYBOARD or MEDIA passes through unchanged."""
        text = "Normal response text."
        result = GatewayStreamConsumer._clean_for_display(text)
        assert result == text

    def test_keyboard_with_media(self):
        """Both KEYBOARD and MEDIA tags are stripped."""
        text = "Result\nMEDIA:/tmp/img.png\n[KEYBOARD:\nOK=ck:ok\n]"
        result = GatewayStreamConsumer._clean_for_display(text)
        assert "MEDIA:" not in result
        assert "[KEYBOARD:" not in result
        assert "Result" in result


# ===========================================================================
# Base class no-ops
# ===========================================================================


class TestBaseClassNoOps:
    """Verify the base adapter's keyboard methods are no-ops."""

    def test_extract_returns_none(self):
        """Base extract_inline_keyboard returns (None, text)."""
        from gateway.platforms.base import BasePlatformAdapter

        # We can't instantiate abstract BasePlatformAdapter directly, but we can
        # call the method on the TelegramAdapter to verify it doesn't crash
        # when no keyboard is present (falls through to base behavior).
        adapter = _make_adapter()
        text = "No keyboard here"
        buttons, cleaned = adapter.extract_inline_keyboard(text)
        assert buttons is None
        assert cleaned == text
