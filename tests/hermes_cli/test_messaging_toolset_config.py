"""Test for messaging toolset in CONFIGURABLE_TOOLSETS.

Issue: #8616 - messaging toolset missing from CONFIGURABLE_TOOLSETS
        causes send_message to be silently dropped for gateway platforms
"""

import pytest


class TestMessagingToolsetConfig:
    """Test that messaging toolset is properly configured."""

    def test_messaging_in_configurable_toolsets(self):
        """messaging should be in CONFIGURABLE_TOOLSETS."""
        from hermes_cli.tools_config import CONFIGURABLE_TOOLSETS
        
        toolset_keys = {ts[0] for ts in CONFIGURABLE_TOOLSETS}
        assert "messaging" in toolset_keys, "messaging toolset should be in CONFIGURABLE_TOOLSETS"

    def test_messaging_entry_format(self):
        """messaging entry should have correct format."""
        from hermes_cli.tools_config import CONFIGURABLE_TOOLSETS
        
        messaging_entry = None
        for entry in CONFIGURABLE_TOOLSETS:
            if entry[0] == "messaging":
                messaging_entry = entry
                break
        
        assert messaging_entry is not None, "messaging entry should exist"
        assert len(messaging_entry) == 3, "entry should have 3 elements (key, label, description)"
        assert messaging_entry[0] == "messaging"
        assert "Messaging" in messaging_entry[1] or "messaging" in messaging_entry[1].lower()
        assert "send_message" in messaging_entry[2]

    def test_send_message_in_messaging_toolset(self):
        """send_message should be in messaging toolset."""
        from toolsets import TOOLSETS
        
        assert "messaging" in TOOLSETS, "messaging toolset should exist in TOOLSETS"
        messaging_tools = TOOLSETS.get("messaging", {}).get("tools", [])
        assert "send_message" in messaging_tools, "send_message should be in messaging toolset"

    def test_messaging_in_platform_composites(self):
        """messaging should be included in platform composite toolsets."""
        from toolsets import TOOLSETS
        
        platform_composites = [
            "hermes-telegram",
            "hermes-discord",
            "hermes-slack",
            "hermes-whatsapp",
            "hermes-signal",
        ]
        
        for composite in platform_composites:
            if composite in TOOLSETS:
                # Composite should expand to include messaging
                composite_entry = TOOLSETS[composite]
                # Check if messaging is directly in the composite tools list
                composite_tools = composite_entry.get("tools", [])
                assert "messaging" in composite_tools, \
                    f"{composite} should include messaging in its tools list"

    def test_get_platform_tools_includes_messaging(self):
        """_get_platform_tools should include messaging for gateway platforms."""
        from hermes_cli.tools_config import _get_platform_tools
        from hermes_cli.config import load_config
        
        config = load_config()
        
        # Test for Telegram platform
        telegram_toolsets = _get_platform_tools(config, "telegram")
        telegram_keys = {ts for ts in telegram_toolsets if isinstance(ts, str)}
        
        # messaging should be in the enabled toolsets
        assert "messaging" in telegram_keys or "send_message" in telegram_keys, \
            "messaging/send_message should be available for Telegram gateway"

    def test_effective_configurable_toolsets_includes_messaging(self):
        """_get_effective_configurable_toolsets should include messaging."""
        from hermes_cli.tools_config import _get_effective_configurable_toolsets
        
        effective_toolsets = _get_effective_configurable_toolsets()
        toolset_keys = {ts[0] for ts in effective_toolsets}
        
        assert "messaging" in toolset_keys, \
            "messaging should be in effective configurable toolsets"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])