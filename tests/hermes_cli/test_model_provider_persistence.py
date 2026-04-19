"""Tests that provider selection via `hermes model` always persists correctly.

Regression tests for the bug where _save_model_choice could save config.model
as a plain string, causing subsequent provider writes (which check
isinstance(model, dict)) to silently fail — leaving the provider unset and
falling back to auto-detection.
"""

import os
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    """Isolated HERMES_HOME with a minimal string-format config."""
    home = tmp_path / "hermes"
    home.mkdir()
    config_yaml = home / "config.yaml"
    # Start with model as a plain string — the format that triggered the bug
    config_yaml.write_text("model: some-old-model\n")
    env_file = home / ".env"
    env_file.write_text("")
    monkeypatch.setenv("HERMES_HOME", str(home))
    # Clear env vars that could interfere
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("HERMES_INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    return home


class TestSaveModelChoiceAlwaysDict:
    def test_string_model_becomes_dict(self, config_home):
        """When config.model is a plain string, _save_model_choice must
        convert it to a dict so provider can be set afterwards."""
        from hermes_cli.auth import _save_model_choice

        _save_model_choice("kimi-k2.5")

        import yaml
        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict), (
            f"Expected model to be a dict after save, got {type(model)}: {model}"
        )
        assert model["default"] == "kimi-k2.5"

    def test_dict_model_stays_dict(self, config_home):
        """When config.model is already a dict, _save_model_choice preserves it."""
        import yaml
        (config_home / "config.yaml").write_text(
            "model:\n  default: old-model\n  provider: openrouter\n"
        )
        from hermes_cli.auth import _save_model_choice

        _save_model_choice("new-model")

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model["default"] == "new-model"
        assert model["provider"] == "openrouter"  # preserved


class TestProviderPersistsAfterModelSave:
    def test_api_key_provider_saved_when_model_was_string(self, config_home, monkeypatch):
        """_model_flow_api_key_provider must persist the provider even when
        config.model started as a plain string."""
        from hermes_cli.auth import PROVIDER_REGISTRY

        pconfig = PROVIDER_REGISTRY.get("kimi-coding")
        if not pconfig:
            pytest.skip("kimi-coding not in PROVIDER_REGISTRY")

        # Simulate: user has a Kimi API key, model was a string
        monkeypatch.setenv("KIMI_API_KEY", "sk-kimi-test-key")

        from hermes_cli.main import _model_flow_api_key_provider
        from hermes_cli.config import load_config

        # Mock the model selection prompt to return "kimi-k2.5"
        # Also mock input() for the base URL prompt and builtins.input
        with patch("hermes_cli.auth._prompt_model_selection", return_value="kimi-k2.5"), \
             patch("hermes_cli.auth.deactivate_provider"), \
             patch("builtins.input", return_value=""):
            _model_flow_api_key_provider(load_config(), "kimi-coding", "old-model")

        import yaml
        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict), f"model should be dict, got {type(model)}"
        assert model.get("provider") == "kimi-coding", (
            f"provider should be 'kimi-coding', got {model.get('provider')}"
        )
        assert model.get("default") == "kimi-k2.5"

    def test_copilot_provider_saved_when_selected(self, config_home):
        """_model_flow_copilot should persist provider/base_url/model together."""
        from hermes_cli.main import _model_flow_copilot
        from hermes_cli.config import load_config

        with patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={
                "provider": "copilot",
                "api_key": "gh-cli-token",
                "base_url": "https://api.githubcopilot.com",
                "source": "gh auth token",
            },
        ), patch(
            "hermes_cli.models.fetch_github_model_catalog",
            return_value=[
                {
                    "id": "gpt-4.1",
                    "capabilities": {"type": "chat", "supports": {}},
                    "supported_endpoints": ["/chat/completions"],
                },
                {
                    "id": "gpt-5.4",
                    "capabilities": {"type": "chat", "supports": {"reasoning_effort": ["low", "medium", "high"]}},
                    "supported_endpoints": ["/responses"],
                },
            ],
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="gpt-5.4",
        ), patch(
            "hermes_cli.main._prompt_reasoning_effort_selection",
            return_value="high",
        ), patch(
            "hermes_cli.auth.deactivate_provider",
        ):
            _model_flow_copilot(load_config(), "old-model")

        import yaml

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict), f"model should be dict, got {type(model)}"
        assert model.get("provider") == "copilot"
        assert model.get("base_url") == "https://api.githubcopilot.com"
        assert model.get("default") == "gpt-5.4"
        assert model.get("api_mode") == "codex_responses"
        assert config["agent"]["reasoning_effort"] == "high"

    def test_copilot_acp_provider_saved_when_selected(self, config_home):
        """_model_flow_copilot_acp should persist provider/base_url/model together."""
        from hermes_cli.main import _model_flow_copilot_acp
        from hermes_cli.config import load_config

        with patch(
            "hermes_cli.auth.get_external_process_provider_status",
            return_value={
                "resolved_command": "/usr/local/bin/copilot",
                "command": "copilot",
                "base_url": "acp://copilot",
            },
        ), patch(
            "hermes_cli.auth.resolve_external_process_provider_credentials",
            return_value={
                "provider": "copilot-acp",
                "api_key": "copilot-acp",
                "base_url": "acp://copilot",
                "command": "/usr/local/bin/copilot",
                "args": ["--acp", "--stdio"],
                "source": "process",
            },
        ), patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={
                "provider": "copilot",
                "api_key": "gh-cli-token",
                "base_url": "https://api.githubcopilot.com",
                "source": "gh auth token",
            },
        ), patch(
            "hermes_cli.models.fetch_github_model_catalog",
            return_value=[
                {
                    "id": "gpt-4.1",
                    "capabilities": {"type": "chat", "supports": {}},
                    "supported_endpoints": ["/chat/completions"],
                },
                {
                    "id": "gpt-5.4",
                    "capabilities": {"type": "chat", "supports": {"reasoning_effort": ["low", "medium", "high"]}},
                    "supported_endpoints": ["/responses"],
                },
            ],
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="gpt-5.4",
        ), patch(
            "hermes_cli.auth.deactivate_provider",
        ):
            _model_flow_copilot_acp(load_config(), "old-model")

        import yaml

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict), f"model should be dict, got {type(model)}"
        assert model.get("provider") == "copilot-acp"
        assert model.get("base_url") == "acp://copilot"
        assert model.get("default") == "gpt-5.4"
        assert model.get("api_mode") == "chat_completions"

    def test_opencode_go_models_are_selectable_and_persist_normalized(self, config_home, monkeypatch):
        from hermes_cli.main import _model_flow_api_key_provider
        from hermes_cli.config import load_config

        monkeypatch.setenv("OPENCODE_GO_API_KEY", "test-key")

        with patch("hermes_cli.models.fetch_api_models", return_value=["opencode-go/kimi-k2.5", "opencode-go/minimax-m2.7"]), \
             patch("hermes_cli.auth._prompt_model_selection", return_value="kimi-k2.5"), \
             patch("hermes_cli.auth.deactivate_provider"), \
             patch("builtins.input", return_value=""):
            _model_flow_api_key_provider(load_config(), "opencode-go", "opencode-go/kimi-k2.5")

        import yaml
        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model.get("provider") == "opencode-go"
        assert model.get("default") == "kimi-k2.5"
        assert model.get("api_mode") == "chat_completions"

    def test_opencode_go_same_provider_switch_recomputes_api_mode(self, config_home, monkeypatch):
        from hermes_cli.main import _model_flow_api_key_provider
        from hermes_cli.config import load_config

        monkeypatch.setenv("OPENCODE_GO_API_KEY", "test-key")
        (config_home / "config.yaml").write_text(
            "model:\n"
            "  default: kimi-k2.5\n"
            "  provider: opencode-go\n"
            "  base_url: https://opencode.ai/zen/go/v1\n"
            "  api_mode: chat_completions\n"
        )

        with patch("hermes_cli.models.fetch_api_models", return_value=["opencode-go/kimi-k2.5", "opencode-go/minimax-m2.5"]), \
             patch("hermes_cli.auth._prompt_model_selection", return_value="minimax-m2.5"), \
             patch("hermes_cli.auth.deactivate_provider"), \
             patch("builtins.input", return_value=""):
            _model_flow_api_key_provider(load_config(), "opencode-go", "kimi-k2.5")

        import yaml
        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model.get("provider") == "opencode-go"
        assert model.get("default") == "minimax-m2.5"
        assert model.get("api_mode") == "anthropic_messages"


class TestBaseUrlOverrideManagement:
    def test_configure_base_url_override_accepts_manual_override(self, config_home, monkeypatch):
        from hermes_cli.main import _configure_base_url_override
        from hermes_cli.config import get_env_value

        monkeypatch.setattr("builtins.input", lambda prompt='': "https://custom.example/v4")

        effective = _configure_base_url_override(
            provider_name="Example Provider",
            base_url_env="EXAMPLE_BASE_URL",
            auto_base="https://auto.example/v4",
        )

        assert effective == "https://custom.example/v4"
        assert get_env_value("EXAMPLE_BASE_URL") == "https://custom.example/v4"

    def test_configure_base_url_override_can_clear_existing_override(self, config_home, monkeypatch):
        from hermes_cli.main import _configure_base_url_override
        from hermes_cli.config import get_env_value, save_env_value

        save_env_value("EXAMPLE_BASE_URL", "https://stale.example/v4")
        monkeypatch.setattr("builtins.input", lambda prompt='': "c")

        effective = _configure_base_url_override(
            provider_name="Example Provider",
            base_url_env="EXAMPLE_BASE_URL",
            auto_base="https://auto.example/v4",
        )

        assert effective == "https://auto.example/v4"
        assert get_env_value("EXAMPLE_BASE_URL") in ("", None)


class TestZaiSetupAutodetect:
    def test_zai_setup_uses_resolved_endpoint_without_manual_override(self, config_home, monkeypatch):
        monkeypatch.setenv("GLM_API_KEY", "test-key")

        from hermes_cli.main import _model_flow_zai
        from hermes_cli.config import load_config, get_env_value

        with patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={
                "provider": "zai",
                "api_key": "***",
                "base_url": "https://api.z.ai/api/coding/paas/v4",
                "source": "GLM_API_KEY",
            },
        ), patch(
            "hermes_cli.models.fetch_api_models",
            return_value=["glm-5.1", "glm-5"],
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="glm-5.1",
        ), patch(
            "hermes_cli.auth.deactivate_provider",
        ), patch(
            "builtins.input",
            return_value="",
        ):
            _model_flow_zai(load_config(), "old-model")

        import yaml

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model.get("provider") == "zai"
        assert model.get("default") == "glm-5.1"
        assert model.get("base_url") == "https://api.z.ai/api/coding/paas/v4"
        assert get_env_value("GLM_BASE_URL") in ("", None)

    def test_zai_setup_can_set_manual_base_url_override(self, config_home, monkeypatch):
        monkeypatch.setenv("GLM_API_KEY", "test-key")

        from hermes_cli.main import _model_flow_zai
        from hermes_cli.config import load_config, get_env_value

        with patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={
                "provider": "zai",
                "api_key": "***",
                "base_url": "https://api.z.ai/api/coding/paas/v4",
                "source": "GLM_API_KEY",
            },
        ), patch(
            "hermes_cli.models.fetch_api_models",
            return_value=["glm-5", "glm-4.7"],
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="glm-5",
        ), patch(
            "hermes_cli.auth.deactivate_provider",
        ), patch(
            "builtins.input",
            return_value="https://manual.example/v4",
        ):
            _model_flow_zai(load_config(), "old-model")

        import yaml

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model.get("provider") == "zai"
        assert model.get("default") == "glm-5"
        assert model.get("base_url") == "https://manual.example/v4"
        assert get_env_value("GLM_BASE_URL") == "https://manual.example/v4"

    def test_zai_setup_can_clear_explicit_base_url_override(self, config_home, monkeypatch):
        monkeypatch.setenv("GLM_API_KEY", "test-key")
        monkeypatch.setenv("GLM_BASE_URL", "https://stale.example/v4")

        from hermes_cli.main import _model_flow_zai
        from hermes_cli.config import load_config, get_env_value

        def _resolve(provider_id, ignore_env_base_url=False):
            assert provider_id == "zai"
            if ignore_env_base_url:
                return {
                    "provider": "zai",
                    "api_key": "***",
                    "base_url": "https://api.z.ai/api/coding/paas/v4",
                    "source": "GLM_API_KEY",
                }
            return {
                "provider": "zai",
                "api_key": "***",
                "base_url": "https://stale.example/v4",
                "source": "GLM_API_KEY",
            }

        with patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            side_effect=_resolve,
        ), patch(
            "hermes_cli.models.fetch_api_models",
            return_value=["glm-5", "glm-4.7"],
        ), patch(
            "hermes_cli.auth._prompt_model_selection",
            return_value="glm-5",
        ), patch(
            "hermes_cli.auth.deactivate_provider",
        ), patch(
            "builtins.input",
            return_value="c",
        ):
            _model_flow_zai(load_config(), "old-model")

        import yaml

        config = yaml.safe_load((config_home / "config.yaml").read_text()) or {}
        model = config.get("model")
        assert isinstance(model, dict)
        assert model.get("provider") == "zai"
        assert model.get("default") == "glm-5"
        assert model.get("base_url") == "https://api.z.ai/api/coding/paas/v4"
        assert get_env_value("GLM_BASE_URL") in ("", None)


class TestProviderDispatch:
    def test_select_provider_and_model_routes_zai_to_dedicated_flow(self, config_home, monkeypatch):
        from types import SimpleNamespace
        from hermes_cli.main import select_provider_and_model

        monkeypatch.setattr("hermes_cli.auth.resolve_provider", lambda value: None)
        monkeypatch.setattr(
            "hermes_cli.models.CANONICAL_PROVIDERS",
            [SimpleNamespace(slug="zai", tui_desc="Z.AI")],
        )
        monkeypatch.setattr(
            "hermes_cli.models._PROVIDER_LABELS",
            {"zai": "Z.AI"},
        )
        monkeypatch.setattr("hermes_cli.main._prompt_provider_choice", lambda labels, default=0: 0)

        seen = {}
        monkeypatch.setattr(
            "hermes_cli.main._model_flow_zai",
            lambda config, current_model="": seen.setdefault("called", ("zai", current_model)),
        )
        monkeypatch.setattr(
            "hermes_cli.main._model_flow_api_key_provider",
            lambda config, provider_id, current_model="": seen.setdefault("called", ("generic", provider_id, current_model)),
        )
        monkeypatch.setattr("hermes_cli.main._clear_stale_openai_base_url", lambda: None)

        select_provider_and_model()

        assert seen.get("called") == ("zai", "some-old-model")

    def test_select_provider_and_model_keeps_neighboring_api_key_providers_generic(self, config_home, monkeypatch):
        from types import SimpleNamespace
        from hermes_cli.main import select_provider_and_model

        monkeypatch.setattr("hermes_cli.auth.resolve_provider", lambda value: None)
        monkeypatch.setattr(
            "hermes_cli.models.CANONICAL_PROVIDERS",
            [SimpleNamespace(slug="nvidia", tui_desc="NVIDIA")],
        )
        monkeypatch.setattr(
            "hermes_cli.models._PROVIDER_LABELS",
            {"nvidia": "NVIDIA"},
        )
        monkeypatch.setattr("hermes_cli.main._prompt_provider_choice", lambda labels, default=0: 0)

        seen = {}
        monkeypatch.setattr(
            "hermes_cli.main._model_flow_zai",
            lambda config, current_model="": seen.setdefault("called", ("zai", current_model)),
        )
        monkeypatch.setattr(
            "hermes_cli.main._model_flow_api_key_provider",
            lambda config, provider_id, current_model="": seen.setdefault("called", ("generic", provider_id, current_model)),
        )
        monkeypatch.setattr("hermes_cli.main._clear_stale_openai_base_url", lambda: None)

        select_provider_and_model()

        assert seen.get("called") == ("generic", "nvidia", "some-old-model")
