"""Tests for agent/skill_commands.py — skill scan disk cache."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent.skill_commands import (
    _build_skills_cmd_manifest,
    _load_skills_cmd_snapshot,
    _write_skills_cmd_snapshot,
    _skills_cmd_snapshot_path,
    _SKILLS_CMD_SNAPSHOT_VERSION,
)


@pytest.fixture
def skills_dir(tmp_path):
    """Create a temp skills directory with a few test skills."""
    skills = tmp_path / "skills"
    skills.mkdir()
    for name in ("alpha", "beta", "gamma"):
        skill_dir = skills / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\n---\n\n# {name}\n\nBody."
        )
    return skills


@pytest.fixture
def snapshot_env(tmp_path, monkeypatch):
    """Set up HERMES_HOME so snapshot path resolves to tmp."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    return hermes_home


class TestBuildManifest:
    def test_manifest_contains_all_skills(self, skills_dir):
        manifest = _build_skills_cmd_manifest([skills_dir])
        assert len(manifest) == 3
        for name in ("alpha/SKILL.md", "beta/SKILL.md", "gamma/SKILL.md"):
            assert name in manifest
            assert isinstance(manifest[name], list)
            assert len(manifest[name]) == 2  # [mtime_ns, size]

    def test_manifest_skips_git_dirs(self, tmp_path):
        skills = tmp_path / "skills"
        skills.mkdir()
        git_skill = skills / ".git" / "hooks" / "test"
        git_skill.mkdir(parents=True)
        (git_skill / "SKILL.md").write_text("---\nname: git\n---\n")
        real_skill = skills / "real"
        real_skill.mkdir()
        (real_skill / "SKILL.md").write_text("---\nname: real\n---\n")
        manifest = _build_skills_cmd_manifest([skills])
        assert "real/SKILL.md" in manifest
        assert all(".git" not in k for k in manifest)

    def test_manifest_empty_dir(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        manifest = _build_skills_cmd_manifest([empty])
        assert manifest == {}

    def test_manifest_nonexistent_dir(self, tmp_path):
        manifest = _build_skills_cmd_manifest([tmp_path / "nope"])
        assert manifest == {}


class TestSnapshotRoundTrip:
    def test_write_and_load(self, skills_dir, snapshot_env):
        commands = {"/alpha": {"name": "alpha", "description": "A"}}
        _write_skills_cmd_snapshot([skills_dir], commands)
        loaded = _load_skills_cmd_snapshot([skills_dir])
        assert loaded is not None
        assert loaded["commands"] == commands
        assert loaded["version"] == _SKILLS_CMD_SNAPSHOT_VERSION

    def test_load_returns_none_when_missing(self, skills_dir, snapshot_env):
        assert _load_skills_cmd_snapshot([skills_dir]) is None

    def test_load_returns_none_when_stale(self, skills_dir, snapshot_env):
        commands = {"/alpha": {"name": "alpha"}}
        _write_skills_cmd_snapshot([skills_dir], commands)
        # Modify a skill file to bust the manifest
        (skills_dir / "alpha" / "SKILL.md").write_text("---\nname: alpha-changed\n---\n")
        assert _load_skills_cmd_snapshot([skills_dir]) is None

    def test_load_returns_none_wrong_version(self, skills_dir, snapshot_env):
        path = _skills_cmd_snapshot_path()
        manifest = _build_skills_cmd_manifest([skills_dir])
        path.write_text(json.dumps({"version": 999, "manifest": manifest, "commands": {}}))
        assert _load_skills_cmd_snapshot([skills_dir]) is None

    def test_snapshot_path_under_hermes_home(self, snapshot_env):
        path = _skills_cmd_snapshot_path()
        assert path == snapshot_env / ".skill_commands_snapshot.json"


class TestScanWithMockedSkillsDir:
    """Test scan_skill_commands with a mocked SKILLS_DIR pointing to temp."""

    def _make_mock_skills_tool(self, skills_dir):
        """Create a mock module for tools.skills_tool imports."""
        import tools.skills_tool as real_mod
        mock_mod = MagicMock()
        mock_mod.SKILLS_DIR = skills_dir
        mock_mod._parse_frontmatter = real_mod._parse_frontmatter
        mock_mod.skill_matches_platform = real_mod.skill_matches_platform
        mock_mod._get_disabled_skill_names = lambda: set()
        return mock_mod

    def test_finds_all_skills(self, skills_dir, snapshot_env):
        mock_mod = self._make_mock_skills_tool(skills_dir)
        import agent.skill_commands as sc

        with patch.dict("sys.modules", {"tools.skills_tool": mock_mod}), \
             patch("agent.skill_commands._skills_cmd_snapshot_path",
                   return_value=snapshot_env / ".skill_commands_snapshot.json"):
            sc._skill_commands = {}
            result = sc.scan_skill_commands()

        names = {v["name"] for v in result.values()}
        assert "alpha" in names
        assert "beta" in names
        assert "gamma" in names

    def test_writes_snapshot_after_cold_scan(self, skills_dir, snapshot_env):
        mock_mod = self._make_mock_skills_tool(skills_dir)
        import agent.skill_commands as sc
        snap_path = snapshot_env / ".skill_commands_snapshot.json"

        with patch.dict("sys.modules", {"tools.skills_tool": mock_mod}), \
             patch("agent.skill_commands._skills_cmd_snapshot_path", return_value=snap_path):
            sc._skill_commands = {}
            sc.scan_skill_commands()

        assert snap_path.exists()
        data = json.loads(snap_path.read_text())
        assert data["version"] == _SKILLS_CMD_SNAPSHOT_VERSION
        assert len(data["commands"]) == 3

    def test_reads_from_snapshot_on_warm_start(self, skills_dir, snapshot_env):
        mock_mod = self._make_mock_skills_tool(skills_dir)
        import agent.skill_commands as sc
        snap_path = snapshot_env / ".skill_commands_snapshot.json"

        # Pre-write a snapshot with fake data
        fake_commands = {"/fake": {"name": "fake", "description": "cached"}}
        snap_path.write_text(json.dumps({
            "version": _SKILLS_CMD_SNAPSHOT_VERSION,
            "manifest": _build_skills_cmd_manifest([skills_dir]),
            "commands": fake_commands,
        }))

        with patch.dict("sys.modules", {"tools.skills_tool": mock_mod}), \
             patch("agent.skill_commands._skills_cmd_snapshot_path", return_value=snap_path):
            sc._skill_commands = {}
            result = sc.scan_skill_commands()

        assert result == fake_commands
