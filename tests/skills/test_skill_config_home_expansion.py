"""Tests that skill config ~ expansion uses subprocess HOME, not process HOME."""

from unittest.mock import patch

from agent.skill_utils import _expand_home, resolve_skill_config_values


class TestExpandHome:
    def test_uses_subprocess_home_when_available(self):
        with patch("agent.skill_utils.get_subprocess_home", return_value="/hermes/home"):
            assert _expand_home("~/foo/bar") == "/hermes/home/foo/bar"

    def test_falls_back_to_expanduser_when_no_subprocess_home(self):
        with patch("agent.skill_utils.get_subprocess_home", return_value=None):
            result = _expand_home("~/foo")
            assert "~" not in result
            assert result.endswith("/foo")

    def test_no_tilde_unchanged(self):
        with patch("agent.skill_utils.get_subprocess_home", return_value="/hermes/home"):
            assert _expand_home("/absolute/path") == "/absolute/path"


class TestResolveSkillConfigValues:
    def test_tilde_in_default_expands_to_subprocess_home(self, tmp_path):
        config_vars = [{"key": "output_dir", "default": "~/outputs"}]
        with (
            patch("agent.skill_utils.get_config_path", return_value=tmp_path / "config.yaml"),
            patch("agent.skill_utils.get_subprocess_home", return_value="/hermes/home"),
        ):
            result = resolve_skill_config_values(config_vars)
            assert result["output_dir"] == "/hermes/home/outputs"

    def test_tilde_in_stored_value_expands_to_subprocess_home(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("skills:\n  config:\n    data_dir: ~/data\n")
        config_vars = [{"key": "data_dir", "default": ""}]
        with (
            patch("agent.skill_utils.get_config_path", return_value=config_file),
            patch("agent.skill_utils.get_subprocess_home", return_value="/sub/home"),
        ):
            result = resolve_skill_config_values(config_vars)
            assert result["data_dir"] == "/sub/home/data"
