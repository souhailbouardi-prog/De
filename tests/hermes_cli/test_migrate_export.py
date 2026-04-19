"""Tests for hermes_cli.migrate_export module."""

import json
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hermes_cli.migrate_export import export_bundle


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def migrate_env(tmp_path, monkeypatch):
    """Set up an isolated HERMES_HOME for export tests.

    Both migrate_export and migrate_core now call get_hermes_home() at runtime
    rather than using a cached module-level constant, so we patch the function
    in both modules. The env var is set as a fallback for any other consumers.
    """
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    # Patch get_hermes_home() in both modules so that at runtime, when
    # export_bundle() and _collect_migration_items() call get_hermes_home(),
    # they get our isolated temp directory instead of the real ~/.hermes/.
    for module_name in ("hermes_cli.migrate_export", "hermes_cli.migrate_core"):
        monkeypatch.setattr(f"{module_name}.get_hermes_home", lambda: hermes_home)
    # Set the env var as a fallback for any code that reads HERMES_HOME directly
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home


# ===========================================================================
# export_bundle
# ===========================================================================

class TestExportBundle:
    def test_raises_when_hermes_home_missing(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent"
        # Patch get_hermes_home() so export_bundle() gets the missing path at runtime
        with patch("hermes_cli.migrate_export.get_hermes_home", return_value=missing):
            with pytest.raises(FileNotFoundError, match="Hermes home not found"):
                export_bundle(None, "safe")

    def test_creates_tarball_with_manifest(self, migrate_env, monkeypatch):
        # Create minimal directory structure
        (migrate_env / "config.yaml").write_text("providers: {}")
        (migrate_env / "sessions").mkdir()

        output = export_bundle(None, "safe")

        try:
            assert output.exists()
            assert str(output).endswith(".tar.gz")

            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert "manifest.json" in names

                manifest_bytes = tf.extractfile("manifest.json").read()
                manifest = json.loads(manifest_bytes.decode("utf-8"))

                assert manifest["preset"] == "safe"
                assert manifest["includes_secrets"] is False
                assert "version" in manifest
                assert "source_os" in manifest
                assert "source_home" in manifest
        finally:
            output.unlink(missing_ok=True)

    def test_safe_preset_excludes_secrets(self, migrate_env, monkeypatch):
        """Safe preset should NOT include .env or auth.json."""
        (migrate_env / "config.yaml").write_text("providers: {}")
        (migrate_env / ".env").write_text("API_KEY=secret")
        (migrate_env / "auth.json").write_text('{"key": "val"}')

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert ".env" not in names
                assert "auth.json" not in names
        finally:
            output.unlink(missing_ok=True)

    def test_full_preset_includes_secrets(self, migrate_env, monkeypatch):
        """Full preset SHOULD include .env and auth.json."""
        (migrate_env / "config.yaml").write_text("providers: {}")
        (migrate_env / ".env").write_text("API_KEY=secret")
        (migrate_env / "auth.json").write_text('{"key": "val"}')

        output = export_bundle(None, "full")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert ".env" in names
                assert "auth.json" in names
        finally:
            output.unlink(missing_ok=True)

    def test_includes_config_yaml(self, migrate_env, monkeypatch):
        (migrate_env / "config.yaml").write_text("providers: {}")

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                assert "config.yaml" in tf.getnames()
        finally:
            output.unlink(missing_ok=True)

    def test_includes_directories(self, migrate_env, monkeypatch):
        (migrate_env / "sessions").mkdir()
        (migrate_env / "sessions" / "001.json").write_text('{"id": "1"}')

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert "sessions" in names or any(n.startswith("sessions/") for n in names)
        finally:
            output.unlink(missing_ok=True)

    def test_skips_always_excluded_files(self, migrate_env, monkeypatch):
        """Files in _EXCLUDE_ALWAYS should never appear in bundle."""
        (migrate_env / "config.yaml").write_text("providers: {}")
        (migrate_env / ".git").mkdir()
        (migrate_env / ".git" / "config").write_text("git data")
        (migrate_env / "state.db").write_bytes(b"sqlite db")
        (migrate_env / "__pycache__").mkdir()
        (migrate_env / "__pycache__" / "mod.pyc").write_bytes(b"pyc")

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert not any(n == "state.db" or n.startswith("state.db") for n in names)
                assert not any(n == ".git" or n.startswith(".git/") for n in names)
                assert not any(n == "__pycache__" or n.startswith("__pycache__/") for n in names)
        finally:
            output.unlink(missing_ok=True)

    def test_skips_platform_incompatible_files(self, migrate_env, monkeypatch):
        """Windows scripts (.ps1, .bat, .cmd) should not be included on linux."""
        (migrate_env / "config.yaml").write_text("providers: {}")
        (migrate_env / "setup.ps1").write_text("$ps1 script")
        (migrate_env / "run.bat").write_text("bat script")

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert "setup.ps1" not in names
                assert "run.bat" not in names
        finally:
            output.unlink(missing_ok=True)

    def test_respects_custom_output_path(self, migrate_env, monkeypatch):
        (migrate_env / "config.yaml").write_text("providers: {}")
        custom_path = migrate_env / "my-backup.tar.gz"

        output = export_bundle(str(custom_path), "safe")

        try:
            assert output == custom_path
            assert output.exists()
        finally:
            output.unlink(missing_ok=True)

    def test_nested_files_included(self, migrate_env, monkeypatch):
        """Files nested inside migrated directories should be included."""
        (migrate_env / "config.yaml").write_text("providers: {}")
        nested_dir = migrate_env / "sessions"
        nested_dir.mkdir()
        (nested_dir / "session1.json").write_text('{"msgs": []}')
        (nested_dir / "subdir").mkdir()
        (nested_dir / "subdir" / "session2.json").write_text('{"msgs": []}')

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                names = tf.getnames()
                assert any("session1.json" in n for n in names)
                assert any("session2.json" in n for n in names)
        finally:
            output.unlink(missing_ok=True)


class TestExportBundleIntegration:
    """Integration tests: export_bundle via full CLI flow."""

    def test_manifest_has_expected_keys(self, migrate_env, monkeypatch):
        (migrate_env / "config.yaml").write_text("providers: {}")

        output = export_bundle(None, "safe")

        try:
            with tarfile.open(output, "r:gz") as tf:
                manifest_bytes = tf.extractfile("manifest.json").read()
                m = json.loads(manifest_bytes.decode("utf-8"))

                assert m["version"] == "1.0"
                assert m["preset"] == "safe"
                assert m["includes_secrets"] is False
                assert m["source_os"] in ("linux", "macos", "windows", "wsl")
                assert "source_home" in m
                # source_home may point to real HOME if env var not fully isolated
                assert len(m["source_home"]) > 0
        finally:
            output.unlink(missing_ok=True)
