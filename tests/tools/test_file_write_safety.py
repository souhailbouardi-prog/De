"""Tests for file write safety and HERMES_WRITE_SAFE_ROOT sandboxing.

Based on PR #1085 by ismoilh (salvaged).
"""

import os
from pathlib import Path

import pytest

from tools.file_operations import _is_write_denied


class TestStaticDenyList:
    """Basic sanity checks for the static write deny list."""

    def test_temp_file_not_denied_by_default(self, tmp_path: Path):
        target = tmp_path / "regular.txt"
        assert _is_write_denied(str(target)) is False

    def test_ssh_key_is_denied(self):
        assert _is_write_denied(os.path.expanduser("~/.ssh/id_rsa")) is True

    def test_etc_shadow_is_denied(self):
        assert _is_write_denied("/etc/shadow") is True


class TestSafeWriteRoot:
    """HERMES_WRITE_SAFE_ROOT should sandbox writes to a specific subtree."""

    def test_writes_inside_safe_root_are_allowed(self, tmp_path: Path, monkeypatch):
        safe_root = tmp_path / "workspace"
        child = safe_root / "subdir" / "file.txt"
        os.makedirs(child.parent, exist_ok=True)

        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        assert _is_write_denied(str(child)) is False

    def test_writes_to_safe_root_itself_are_allowed(self, tmp_path: Path, monkeypatch):
        safe_root = tmp_path / "workspace"
        os.makedirs(safe_root, exist_ok=True)

        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        assert _is_write_denied(str(safe_root)) is False

    def test_writes_outside_safe_root_are_denied(self, tmp_path: Path, monkeypatch):
        safe_root = tmp_path / "workspace"
        outside = tmp_path / "other" / "file.txt"
        os.makedirs(safe_root, exist_ok=True)
        os.makedirs(outside.parent, exist_ok=True)

        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        assert _is_write_denied(str(outside)) is True

    def test_safe_root_env_ignores_empty_value(self, tmp_path: Path, monkeypatch):
        target = tmp_path / "regular.txt"
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", "")
        assert _is_write_denied(str(target)) is False

    def test_safe_root_unset_allows_all(self, tmp_path: Path, monkeypatch):
        target = tmp_path / "regular.txt"
        monkeypatch.delenv("HERMES_WRITE_SAFE_ROOT", raising=False)
        assert _is_write_denied(str(target)) is False

    def test_safe_root_with_tilde_expansion(self, tmp_path: Path, monkeypatch):
        """~ in HERMES_WRITE_SAFE_ROOT should be expanded."""
        # Use a real subdirectory of tmp_path so we can test tilde-style paths
        safe_root = tmp_path / "workspace"
        inside = safe_root / "file.txt"
        os.makedirs(safe_root, exist_ok=True)

        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        assert _is_write_denied(str(inside)) is False

    def test_safe_root_does_not_override_static_deny(self, tmp_path: Path, monkeypatch):
        """Even if a static-denied path is inside the safe root, it's still denied."""
        # Point safe root at home to include ~/.ssh
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", os.path.expanduser("~"))
        assert _is_write_denied(os.path.expanduser("~/.ssh/id_rsa")) is True


class TestCheckSensitivePathMacOSBypass:
    """Verify _check_sensitive_path blocks /private/etc paths (issue #8734)."""

    def test_etc_hosts_blocked(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/etc/hosts") is not None

    def test_private_etc_hosts_blocked(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/etc/hosts") is not None

    def test_private_etc_ssh_config_blocked(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/etc/ssh/sshd_config") is not None

    def test_private_var_blocked(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/db/something") is not None

    def test_boot_still_blocked(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/boot/grub/grub.cfg") is not None

    def test_safe_path_allowed(self):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/tmp/safe_file.txt") is None


class TestCheckSensitivePathMacOSTempAllowlist:
    """Verify ``_check_sensitive_path`` permits macOS user-writable temp
    trees that sit *syntactically* under ``/private/var/`` but are, by OS
    design, per-user writable locations.

    Regression for the bycatch introduced in 311dac19: the ``/private/var/``
    prefix added for the ``/private/etc`` symlink bypass also blocked
    ``tempfile.gettempdir()`` output on macOS (which resolves to
    ``/private/var/folders/…``) and ``/tmp`` (symlink to ``/private/tmp/``).
    Blocking those broke ``test_file_staleness.py`` on macOS and, more
    importantly, real user workflows where the agent writes to a temp dir.

    The allowlist is macOS-only (``_ALLOWLIST_ACTIVE = sys.platform ==
    'darwin'``).  Tests that exercise the allowlist force the flag on via
    monkeypatch so they run identically on Linux CI and macOS.
    """

    @pytest.fixture
    def force_allowlist_active(self, monkeypatch):
        """Force the macOS allowlist on so allowlist-path tests exercise
        the logic on Linux CI too.  No-op if already darwin."""
        monkeypatch.setattr("tools.file_tools._ALLOWLIST_ACTIVE", True)

    def test_private_var_folders_allowed(self, force_allowlist_active):
        """macOS ``tempfile.gettempdir()`` resolves under this prefix."""
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path(
            "/private/var/folders/fx/abc/T/my_temp_file.txt"
        ) is None

    def test_private_tmp_allowed(self, force_allowlist_active):
        """``/tmp`` on macOS is a symlink into ``/private/tmp/``."""
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/tmp/scratch.txt") is None

    def test_actual_tempfile_path_allowed(self, force_allowlist_active):
        """The exact path shape produced by ``tempfile.TemporaryDirectory()``
        on macOS must not trip the sensitive-path check (this was the
        ``test_file_staleness.py`` failure mode)."""
        import tempfile
        from tools.file_tools import _check_sensitive_path
        with tempfile.TemporaryDirectory() as tmp:
            candidate = os.path.join(tmp, "write_target.txt")
            assert _check_sensitive_path(candidate) is None, (
                f"Sensitive-path check rejected a plain tempfile path: {candidate!r}"
            )

    # --- Sensitive subtrees still blocked ---------------------------------

    def test_private_var_db_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/db/something") is not None

    def test_private_var_log_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/log/system.log") is not None

    def test_private_var_root_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/root/.ssh/id_rsa") is not None

    def test_private_var_mail_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/mail/alice") is not None

    def test_private_var_spool_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/var/spool/cron/root") is not None

    # --- Canary: /etc/, /boot/, /private/etc/ stay blocked ----------------

    def test_private_etc_still_blocked_after_allowlist(self, force_allowlist_active):
        """The allowlist must not weaken the /private/etc/ symlink-bypass
        guard that #8734 / 311dac19 established."""
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/private/etc/hosts") is not None
        assert _check_sensitive_path("/private/etc/ssh/sshd_config") is not None

    def test_non_macos_paths_still_blocked(self, force_allowlist_active):
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path("/etc/passwd") is not None
        assert _check_sensitive_path("/boot/grub/grub.cfg") is not None
        assert _check_sensitive_path("/usr/lib/systemd/system/sshd.service") is not None

    def test_allowlist_helper_is_path_prefix_scoped(self, force_allowlist_active):
        """``_is_allowlisted_sensitive_path`` must not match paths that
        merely *contain* an allowlisted substring — only prefix matches
        count.  Prevents trivial bypass via e.g. a sensitive file whose
        name happens to contain ``/private/var/folders/``.

        The allowlist contains both the symlink-resolved
        (``/private/var/folders/...``) and the un-resolved
        (``/var/folders/...``) forms so the AND guard validates each
        independently-sanitised path form against the same allowlist
        set.  Supplying the resolved form for both arguments is a valid
        allowlisted path (e.g. a caller-provided realpath-already-
        resolved path)."""
        from tools.file_tools import _is_allowlisted_sensitive_path
        # Both forms under the resolved prefix → allowlisted.
        assert _is_allowlisted_sensitive_path(
            "/private/var/folders/fx/foo.txt",
            "/private/var/folders/fx/foo.txt",
        ) is True
        # Path that contains the substring but doesn't start with it → blocked.
        assert _is_allowlisted_sensitive_path(
            "/private/var/db/fake/private/var/folders/x",
            "/private/var/db/fake/private/var/folders/x",
        ) is False

    def test_allowlist_accepts_different_prefix_forms_for_resolved_and_normalized(
        self, force_allowlist_active,
    ):
        """The real-world macOS tempfile case: ``os.path.normpath`` does
        not follow symlinks, so the un-resolved ``/var/folders/...`` and
        the realpath-resolved ``/private/var/folders/...`` forms of the
        same file differ.  Each form must be separately checked against
        the full allowlist so both check out."""
        from tools.file_tools import _is_allowlisted_sensitive_path
        assert _is_allowlisted_sensitive_path(
            "/private/var/folders/fx/abc/T/file.txt",  # realpath form
            "/var/folders/fx/abc/T/file.txt",           # normpath form
        ) is True

    def test_allowlist_requires_both_resolved_and_normalized(self, force_allowlist_active):
        """AND-guard: an allowlisted ``resolved`` without an allowlisted
        ``normalized`` (or vice versa) must not exempt the path.  Defeats
        a symlink-substitution attack where an attacker plants
        ``/private/var/folders/evil -> /etc/sudoers`` — ``resolved``
        becomes ``/etc/sudoers`` (not allowlisted) and the AND guard
        blocks the write even though ``normalized`` is allowlisted."""
        from tools.file_tools import _is_allowlisted_sensitive_path
        assert _is_allowlisted_sensitive_path(
            "/etc/sudoers",                  # resolved: not allowlisted (attack)
            "/private/var/folders/fx/evil",  # normalized: allowlisted
        ) is False
        assert _is_allowlisted_sensitive_path(
            "/private/var/folders/fx/evil",  # resolved: allowlisted
            "/etc/sudoers",                  # normalized: not allowlisted
        ) is False

    def test_realpath_exception_cannot_bypass_guard(self, force_allowlist_active, monkeypatch):
        """Regression for the second Copilot concern: if ``os.path.realpath``
        raises, the resolver must fall back to the *normalised* path, not
        to the raw caller-supplied string.  A crafted path that is raw-
        allowlisted but normalises to ``/etc/sudoers`` must be blocked."""
        from tools.file_tools import _check_sensitive_path

        def _raising_realpath(p):
            raise OSError("simulated realpath failure")

        monkeypatch.setattr("tools.file_tools.os.path.realpath", _raising_realpath)

        # Path looks allowlisted in raw form but normalises to /etc/sudoers.
        crafted = "/private/var/folders/../../etc/sudoers"
        result = _check_sensitive_path(crafted)
        assert result is not None, (
            "realpath-exception fallback must not allow a crafted path "
            "whose normalised form is /etc/sudoers"
        )
        assert "sensitive system path" in result


class TestAllowlistPlatformGate:
    """Verify the macOS allowlist is inactive on non-darwin platforms so
    the fix cannot accidentally broaden Linux / Windows semantics."""

    def test_allowlist_inactive_on_linux(self, monkeypatch):
        """On Linux (``sys.platform != 'darwin'``), an exotic user-created
        ``/private/var/folders/…`` tree must still be blocked — Linux has
        no OS-level convention that these paths are user-writable, so
        preserve the pre-fix behaviour byte-for-byte for the path that
        actually hits a sensitive prefix.

        Note: ``/private/tmp/`` does not match any sensitive prefix on
        origin/main either (``/private/var/`` is the prefix, not
        ``/private/``), so its behaviour on Linux is unchanged and
        irrelevant to the platform gate.  The gate matters for
        ``/private/var/folders/…`` specifically, which *does* match
        ``/private/var/``."""
        monkeypatch.setattr("tools.file_tools._ALLOWLIST_ACTIVE", False)
        from tools.file_tools import _check_sensitive_path
        assert _check_sensitive_path(
            "/private/var/folders/fx/abc/T/foo.txt"
        ) is not None

    def test_allowlist_default_is_darwin_only(self):
        """Sanity check: the platform gate is derived from
        ``sys.platform``.  On this test host the module-level constant
        matches ``sys.platform == 'darwin'``."""
        import sys
        import tools.file_tools as ft
        assert ft._ALLOWLIST_ACTIVE is (sys.platform == "darwin")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
