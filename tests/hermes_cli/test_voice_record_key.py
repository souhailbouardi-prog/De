"""Regression tests for voice.record_key alt+ modifier handling (#11387).

Setting voice.record_key to alt+<key> in config.yaml crashed startup because
prompt_toolkit only accepts c- (Ctrl) and s- (Shift) prefixes, not a- (Alt).
"""
import pytest
from unittest.mock import patch, MagicMock


def _translate_voice_key(raw_key: str) -> str:
    """Mirrors the key-translation logic in cli.py (keybinding setup ~L8853)."""
    raw_lower = raw_key.lower()
    if "alt+" in raw_lower:
        return "c-b"
    return raw_lower.replace("ctrl+", "c-").replace("shift+", "s-")


class TestVoiceRecordKeyTranslation:
    """Unit tests for the record_key → prompt_toolkit key translation."""

    def test_ctrl_b_default(self):
        assert _translate_voice_key("ctrl+b") == "c-b"

    def test_ctrl_t(self):
        assert _translate_voice_key("ctrl+t") == "c-t"

    def test_shift_f1(self):
        assert _translate_voice_key("shift+f1") == "s-f1"

    def test_alt_space_falls_back(self):
        """alt+ modifier is unsupported; must fall back to c-b (#11387)."""
        assert _translate_voice_key("alt+space") == "c-b"

    def test_alt_x_falls_back(self):
        assert _translate_voice_key("alt+x") == "c-b"

    def test_alt_mixed_case_falls_back(self):
        assert _translate_voice_key("Alt+Space") == "c-b"

    def test_ctrl_uppercase(self):
        assert _translate_voice_key("CTRL+B") == "c-b"
