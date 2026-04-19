"""Tests for WhatsApp native audio sending.

Regression guard: WhatsAppAdapter must override send_voice() so audio files are
sent via the bridge as native media, not downgraded to a text message with the
local file path.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import Platform


class _AsyncCM:
    """Minimal async context manager returning a fixed value."""

    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *exc):
        return False


def _make_adapter():
    """Create a WhatsAppAdapter with test attributes (bypass __init__)."""
    from gateway.platforms.whatsapp import WhatsAppAdapter

    adapter = WhatsAppAdapter.__new__(WhatsAppAdapter)
    adapter.platform = Platform.WHATSAPP
    adapter.config = MagicMock()
    adapter.config.extra = {}
    adapter._bridge_port = 3000
    adapter._bridge_script = "/tmp/test-bridge.js"
    adapter._session_path = MagicMock()
    adapter._bridge_log_fh = None
    adapter._bridge_log = None
    adapter._bridge_process = None
    adapter._reply_prefix = None
    adapter._running = True
    adapter._message_handler = None
    adapter._fatal_error_code = None
    adapter._fatal_error_message = None
    adapter._fatal_error_retryable = True
    adapter._fatal_error_handler = None
    adapter._active_sessions = {}
    adapter._pending_messages = {}
    adapter._background_tasks = set()
    adapter._auto_tts_disabled_chats = set()
    adapter._message_queue = asyncio.Queue()
    adapter._http_session = MagicMock()
    adapter._mention_patterns = []
    return adapter


class TestSendVoice:
    """WhatsApp should deliver voice/audio files via bridge media upload."""

    @pytest.mark.asyncio
    async def test_send_voice_uses_bridge_audio_media(self, monkeypatch):
        adapter = _make_adapter()
        monkeypatch.setattr("gateway.platforms.whatsapp.os.path.exists", lambda path: True)

        resp = MagicMock(status=200)
        resp.json = AsyncMock(return_value={"messageId": "voice1"})
        adapter._http_session.post = MagicMock(return_value=_AsyncCM(resp))

        result = await adapter.send_voice("chat1", "/tmp/test-voice.mp3")

        assert result.success is True
        call_args = adapter._http_session.post.call_args
        assert call_args.args[0] == "http://127.0.0.1:3000/send-media"
        payload = call_args.kwargs["json"]
        assert payload == {
            "chatId": "chat1",
            "filePath": "/tmp/test-voice.mp3",
            "mediaType": "audio",
        }

    @pytest.mark.asyncio
    async def test_send_voice_preserves_caption(self, monkeypatch):
        adapter = _make_adapter()
        monkeypatch.setattr("gateway.platforms.whatsapp.os.path.exists", lambda path: True)

        resp = MagicMock(status=200)
        resp.json = AsyncMock(return_value={"messageId": "voice2"})
        adapter._http_session.post = MagicMock(return_value=_AsyncCM(resp))

        result = await adapter.send_voice("chat1", "/tmp/test-voice.ogg", caption="hola")

        assert result.success is True
        payload = adapter._http_session.post.call_args.kwargs["json"]
        assert payload["caption"] == "hola"
        assert payload["mediaType"] == "audio"
