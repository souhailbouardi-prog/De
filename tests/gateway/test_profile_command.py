"""Tests for gateway /profile command output."""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_profile_command_nested_under_std_profiles(tmp_path, monkeypatch):
    """HERMES_HOME under ~/.hermes/profiles/<name>/... shows top-level profile name."""
    from gateway.run import GatewayRunner

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    profile_home = tmp_path / ".hermes" / "profiles" / "coder" / "nested"
    profile_home.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(profile_home))

    runner = object.__new__(GatewayRunner)
    with patch(
        "hermes_constants.display_hermes_home",
        return_value="~/.hermes/profiles/coder",
    ):
        result = await runner._handle_profile_command(event=None)

    assert "**Profile:** `coder`" in result
    assert "**Home:** `~/.hermes/profiles/coder`" in result
