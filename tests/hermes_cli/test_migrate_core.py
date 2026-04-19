"""Tests for hermes_cli.migrate_core module."""

import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from hermes_cli.migrate_core import (
    BUNDLE_VERSION,
    MigrationReport,
    _EXCLUDE_ALWAYS,
    _EXTERNAL_TOOLS,
    _PLATFORM_SKIP,
    _SECRET_FILES,
    _is_secret,
    _is_text_file,
    _remap_content,
    _should_skip_dir,
    _should_skip_file,
    create_manifest,
    detect_platform,
)


# ---------------------------------------------------------------------------
# Shared fixture: isolated HERMES_HOME
# ---------------------------------------------------------------------------

@pytest.fixture
def migrate_env(tmp_path, monkeypatch):
    """Redirect HERMES_HOME to tmp_path for all migrate tests."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    # Re-import to pick up the new HERMES_HOME
    # (HERMES_HOME is cached at module import time, so we patch get_hermes_home)
    with patch("hermes_cli.migrate_core.get_hermes_home", return_value=hermes_home):
        yield hermes_home


# ===========================================================================
# MigrationReport
# ===========================================================================

class TestMigrationReport:
    def test_is_empty_true_when_no_items(self):
        report = MigrationReport()
        assert report.is_empty() is True

    def test_is_empty_false_when_migrated(self):
        report = MigrationReport(migrated=["config.yaml"])
        assert report.is_empty() is False

    def test_is_empty_false_when_skipped(self):
        report = MigrationReport(skipped=[".env"])
        assert report.is_empty() is False

    def test_is_empty_false_when_needs_reauth(self):
        report = MigrationReport(needs_reauth=["provider 'openai'"])
        assert report.is_empty() is False

    def test_is_empty_false_when_incompatible(self):
        report = MigrationReport(incompatible=["alias 'llm' uses 'docker' which is not installed"])
        assert report.is_empty() is False


# ===========================================================================
# detect_platform
# ===========================================================================

class TestDetectPlatform:
    def test_detects_linux(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(platform, "release", lambda: "5.15.0-generic")
        monkeypatch.delenv("USERPROFILE", raising=False)
        monkeypatch.setenv("HOME", "/home/user")

        # Patch get_home to return our test home
        with patch("hermes_cli.migrate_core.get_home", return_value=Path("/home/user")):
            result = detect_platform()
        assert result["os"] == "linux"
        assert result["home"] == Path("/home/user")

    def test_detects_macos(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Darwin")
        monkeypatch.setattr(platform, "release", lambda: "21.0.0")
        monkeypatch.setenv("HOME", "/Users/user")

        with patch("hermes_cli.migrate_core.get_home", return_value=Path("/Users/user")):
            result = detect_platform()
        assert result["os"] == "macos"
        assert result["home"] == Path("/Users/user")

    def test_detects_wsl(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(platform, "release", lambda: "5.15.0-microsoft-standard-WSL2")
        monkeypatch.setenv("HOME", "/home/user")

        with patch("hermes_cli.migrate_core.get_home", return_value=Path("/home/user")):
            result = detect_platform()
        assert result["os"] == "wsl"

    def test_detects_windows(self, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(platform, "release", lambda: "10")
        monkeypatch.setenv("USERPROFILE", "C:\\Users\\user")

        result = detect_platform()
        assert result["os"] == "windows"
        assert result["home"] == Path("C:\\Users\\user")


# ===========================================================================
# create_manifest
# ===========================================================================

class TestCreateManifest:
    def test_manifest_keys(self):
        src = {"os": "linux", "home": Path("/home/user")}
        m = create_manifest("safe", src)
        assert "version" in m
        assert "bundle_created_at" in m
        assert "hermes_version" in m
        assert "source_os" in m
        assert "source_home" in m
        assert "preset" in m
        assert "includes_secrets" in m

    def test_includes_secrets_true_for_full_preset(self):
        src = {"os": "linux", "home": Path("/home/user")}
        m = create_manifest("full", src)
        assert m["includes_secrets"] is True
        assert m["preset"] == "full"

    def test_includes_secrets_false_for_safe_preset(self):
        src = {"os": "linux", "home": Path("/home/user")}
        m = create_manifest("safe", src)
        assert m["includes_secrets"] is False
        assert m["preset"] == "safe"

    def test_version_matches_bundle_version(self):
        src = {"os": "linux", "home": Path("/home/user")}
        m = create_manifest("safe", src)
        assert m["version"] == BUNDLE_VERSION


# ===========================================================================
# _is_secret
# ===========================================================================

class TestIsSecret:
    def test_env_is_secret_in_safe_preset(self):
        assert _is_secret(".env", "safe") is True
        assert _is_secret("subdir/.env", "safe") is True

    def test_auth_json_is_secret_in_safe_preset(self):
        assert _is_secret("auth.json", "safe") is True
        assert _is_secret("deep/nested/auth.json", "safe") is True

    def test_other_files_not_secret_in_safe_preset(self):
        assert _is_secret("config.yaml", "safe") is False
        assert _is_secret(".bashrc", "safe") is False
        assert _is_secret("memories/", "safe") is False

    def test_nothing_secret_in_full_preset(self):
        assert _is_secret(".env", "full") is False
        assert _is_secret("auth.json", "full") is False


# ===========================================================================
# _is_text_file
# ===========================================================================

class TestIsTextFile:
    @pytest.mark.parametrize("ext", [".yaml", ".yml", ".json", ".md", ".txt", ".sh", ".env", ".toml", ".ini", ".cfg"])
    def test_text_extensions(self, ext):
        assert _is_text_file(f"file{ext}") is True

    @pytest.mark.parametrize("ext", [".py", ".png", ".jpg", ".zip", ".db", ".bin"])
    def test_binary_extensions(self, ext):
        assert _is_text_file(f"file{ext}") is False

    def test_named_files(self):
        assert _is_text_file(".env") is True
        assert _is_text_file("config.yaml") is True
        assert _is_text_file("SOUL.md") is True


# ===========================================================================
# _should_skip_dir
# ===========================================================================

class TestShouldSkipDir:
    @pytest.mark.parametrize("name", ["__pycache__", ".git", "node_modules", "hermes-agent", "state.db"])
    def test_always_skipped(self, name):
        assert _should_skip_dir(name, "linux") is True

    def test_normal_dirs_not_skipped(self):
        assert _should_skip_dir("memories", "linux") is False
        assert _should_skip_dir("sessions", "linux") is False


# ===========================================================================
# _should_skip_file
# ===========================================================================

class TestShouldSkipFile:
    @pytest.mark.parametrize("name", ["hermes-agent", ".git", "node_modules", "state.db", "errors.log"])
    def test_always_skipped(self, name):
        assert _should_skip_file(name, "linux") is True

    def test_dot_files_skipped_except_secrets(self):
        # .bashrc should be skipped (hidden but not a secret)
        assert _should_skip_file(".bashrc", "linux") is True
        # But .env is not skipped here — it's handled by _is_secret
        assert _should_skip_file(".env", "linux") is False

    @pytest.mark.parametrize("ext", [".ps1", ".bat", ".cmd"])
    def test_windows_scripts_skipped_on_linux(self, ext):
        assert _should_skip_file(f"setup{ext}", "linux") is True

    @pytest.mark.parametrize("ext", [".ps1", ".bat", ".cmd"])
    def test_windows_scripts_not_skipped_on_windows(self, ext):
        assert _should_skip_file(f"setup{ext}", "windows") is False

    def test_config_yaml_not_skipped(self):
        assert _should_skip_file("config.yaml", "linux") is False


# ===========================================================================
# _remap_content
# ===========================================================================

class TestRemapContent:
    def test_no_remap_when_same_home(self):
        home = Path("/home/user")
        result = _remap_content("some text", home, home)
        assert result == "some text"

    def test_no_remap_when_source_not_in_content(self):
        result = _remap_content("hello world", Path("/home/A"), Path("/home/B"))
        assert result == "hello world"

    def test_remaps_absolute_path(self):
        result = _remap_content(
            "/home/user/.hermes/config.yaml",
            Path("/home/user"),
            Path("/Users/user"),
        )
        assert "/Users/user/.hermes/config.yaml" in result
        assert "/home/user" not in result

    def test_remap_preserves_suffix(self):
        result = _remap_content(
            'shell: "/home/user/.bashrc"',
            Path("/home/user"),
            Path("/home/user2"),
        )
        assert "/home/user2/.bashrc" in result

    def test_remap_does_not_corrupt_mid_string(self):
        # The boundary regex should not match /home/user inside a path like /home/userx
        result = _remap_content(
            "HOME=/home/userx",
            Path("/home/user"),
            Path("/home/user2"),
        )
        assert "HOME=/home/userx" in result  # embedded /home/userx preserved

    def test_remap_windows_style_paths_normalized(self):
        """Windows paths are normalized to forward slashes during remapping."""
        result = _remap_content(
            "C:\\Users\\user\\config.yaml",
            Path("C:\\Users\\user"),
            Path("C:\\Users\\user2"),
        )
        # Forward-slash result (code normalizes Windows backslashes internally)
        assert "C:/Users/user2/config.yaml" in result
