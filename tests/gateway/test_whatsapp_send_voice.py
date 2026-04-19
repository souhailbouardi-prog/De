"""Tests that WhatsApp adapter has send_voice() override.

Issue #9236: WhatsApp was the only platform adapter missing a
send_voice() override, causing voice messages to fall back to
plain text instead of native media attachments.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.platforms.base import BasePlatformAdapter


class TestWhatsAppSendVoice:
    """Verify send_voice is overridden and routes through bridge."""

    def test_send_voice_method_exists(self):
        """WhatsApp adapter must have its own send_voice override."""
        from gateway.platforms.whatsapp import WhatsAppAdapter
        # The method should NOT be the base class fallback
        assert hasattr(WhatsAppAdapter, "send_voice")
        assert WhatsAppAdapter.send_voice is not BasePlatformAdapter.send_voice

    def test_send_voice_signature_matches_base(self):
        """send_voice signature should match the base class interface."""
        import inspect
        from gateway.platforms.whatsapp import WhatsAppAdapter

        base_sig = inspect.signature(BasePlatformAdapter.send_voice)
        wa_sig = inspect.signature(WhatsAppAdapter.send_voice)

        # Both should accept: self, chat_id, audio_path, caption, reply_to, **kwargs
        base_params = list(base_sig.parameters.keys())
        wa_params = list(wa_sig.parameters.keys())
        assert base_params == wa_params

    @pytest.mark.asyncio
    async def test_send_voice_calls_bridge(self):
        """send_voice should route through _send_media_to_bridge with type 'audio'."""
        from gateway.platforms.whatsapp import WhatsAppAdapter

        adapter = object.__new__(WhatsAppAdapter)
        adapter._send_media_to_bridge = AsyncMock(
            return_value=MagicMock(success=True, message_id="msg123")
        )

        result = await adapter.send_voice(
            chat_id="12345@s.whatsapp.net",
            audio_path="/tmp/voice.mp3",
            caption="Hello",
        )

        adapter._send_media_to_bridge.assert_called_once_with(
            "12345@s.whatsapp.net", "/tmp/voice.mp3", "audio", "Hello"
        )
        assert result.success is True

    def test_all_media_methods_present(self):
        """WhatsApp adapter should have all media send methods."""
        from gateway.platforms.whatsapp import WhatsAppAdapter

        for method_name in ("send_image", "send_image_file", "send_video",
                            "send_document", "send_voice"):
            method = getattr(WhatsAppAdapter, method_name, None)
            assert method is not None, f"Missing method: {method_name}"
            base_method = getattr(BasePlatformAdapter, method_name, None)
            assert method is not base_method, (
                f"{method_name} is not overridden (still using base class)"
            )
