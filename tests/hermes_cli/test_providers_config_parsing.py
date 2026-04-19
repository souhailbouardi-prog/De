"""Tests for providers: config parsing — camelCase aliases and URL validation.

Regression tests for #9332:
- camelCase keys (apiKey, baseUrl, keyEnv) are silently dropped
- Non-URL strings in base_url/api are silently accepted

Run: pytest tests/hermes_cli/test_providers_config_parsing.py -v
"""
import logging
import pytest


def _resolve(name: str, providers_dict: dict):
    """Thin wrapper to call resolve_user_provider."""
    from hermes_cli.providers import resolve_user_provider
    return resolve_user_provider(name, providers_dict)


# ---------------------------------------------------------------------------
# snake_case keys (always worked)
# ---------------------------------------------------------------------------

class TestSnakeCaseKeys:
    """Verify existing snake_case behavior is preserved."""

    def test_base_url_snake_case(self):
        pdef = _resolve("myprovider", {
            "myprovider": {
                "base_url": "https://api.example.com/v1",
            }
        })
        assert pdef is not None
        assert pdef.base_url == "https://api.example.com/v1"

    def test_key_env_snake_case(self):
        pdef = _resolve("myprovider", {
            "myprovider": {
                "base_url": "https://api.example.com/v1",
                "key_env": "MY_API_KEY",
            }
        })
        assert pdef is not None
        assert "MY_API_KEY" in pdef.api_key_env_vars

    def test_legacy_api_field_still_works(self):
        """Legacy 'api' field (first in lookup order) still accepted as URL."""
        pdef = _resolve("myprovider", {
            "myprovider": {"api": "https://api.example.com/v1"}
        })
        assert pdef is not None
        assert pdef.base_url == "https://api.example.com/v1"

    def test_legacy_url_field_still_works(self):
        pdef = _resolve("myprovider", {
            "myprovider": {"url": "https://api.example.com/v1"}
        })
        assert pdef is not None
        assert pdef.base_url == "https://api.example.com/v1"


# ---------------------------------------------------------------------------
# camelCase aliases (#9332 fix)
# ---------------------------------------------------------------------------

class TestCamelCaseAliases:
    """camelCase keys must now be recognized (#9332)."""

    def test_baseUrl_camelcase_accepted(self):
        """baseUrl must be treated as an alias for base_url."""
        pdef = _resolve("myprovider", {
            "myprovider": {"baseUrl": "https://api.example.com/v1"}
        })
        assert pdef is not None, "Provider with camelCase baseUrl should be resolved"
        assert pdef.base_url == "https://api.example.com/v1"

    def test_apiKey_camelcase_silently_ignored_before_fix(self):
        """Before fix: apiKey was silently dropped.  After fix: keyEnv alias works.

        Note: 'apiKey' maps to an API key value, not an env var name — config.yaml
        uses key_env (an env var name).  We test the keyEnv alias for key_env.
        """
        pdef = _resolve("myprovider", {
            "myprovider": {
                "baseUrl": "https://api.example.com/v1",
                "keyEnv": "MY_PROVIDER_KEY",
            }
        })
        assert pdef is not None
        assert pdef.base_url == "https://api.example.com/v1"
        assert "MY_PROVIDER_KEY" in pdef.api_key_env_vars

    def test_snakecase_takes_precedence_over_camelcase(self):
        """When both snake_case and camelCase are present, snake_case wins."""
        pdef = _resolve("myprovider", {
            "myprovider": {
                "base_url": "https://snake.example.com/v1",
                "baseUrl": "https://camel.example.com/v1",
            }
        })
        assert pdef is not None
        assert pdef.base_url == "https://snake.example.com/v1", \
            "snake_case base_url should take precedence over camelCase baseUrl"

    def test_camelcase_key_env_alias(self):
        """keyEnv is recognized as an alias for key_env."""
        pdef = _resolve("myprovider", {
            "myprovider": {
                "base_url": "https://api.example.com/v1",
                "keyEnv": "CAMEL_KEY_ENV",
            }
        })
        assert pdef is not None
        assert "CAMEL_KEY_ENV" in pdef.api_key_env_vars

    def test_both_camelcase_fields_together(self):
        """A fully camelCase config entry works end-to-end."""
        pdef = _resolve("myproxy", {
            "myproxy": {
                "baseUrl": "https://proxy.example.com/openai",
                "keyEnv": "PROXY_API_KEY",
            }
        })
        assert pdef is not None
        assert pdef.base_url == "https://proxy.example.com/openai"
        assert "PROXY_API_KEY" in pdef.api_key_env_vars


# ---------------------------------------------------------------------------
# URL validation (#9332 fix)
# ---------------------------------------------------------------------------

class TestURLValidation:
    """Non-URL strings in url fields must produce a warning and be ignored."""

    def test_non_url_string_in_api_field_rejected(self, caplog):
        """A bare string like 'openai-reverse-proxy' in 'api' is not a URL."""
        with caplog.at_level(logging.WARNING, logger="hermes_cli.providers"):
            pdef = _resolve("myprovider", {
                "myprovider": {"api": "openai-reverse-proxy"}
            })
        # The invalid URL should be cleared (empty base_url)
        if pdef:
            assert pdef.base_url == "", \
                f"Non-URL 'openai-reverse-proxy' should not be used as base_url, got: {pdef.base_url!r}"
        # A warning should have been emitted
        assert any("does not look like a URL" in r.message or "scheme" in r.message
                   for r in caplog.records), \
            "Expected a warning about missing URL scheme"

    def test_non_url_string_in_base_url_rejected(self, caplog):
        """A string without scheme in base_url is rejected with warning."""
        with caplog.at_level(logging.WARNING, logger="hermes_cli.providers"):
            pdef = _resolve("myprovider", {
                "myprovider": {"base_url": "my-custom-proxy-endpoint"}
            })
        if pdef:
            assert pdef.base_url == ""
        assert any("does not look like a URL" in r.message or "scheme" in r.message
                   for r in caplog.records)

    def test_valid_https_url_accepted_without_warning(self, caplog):
        """Valid https:// URL should pass without warning."""
        with caplog.at_level(logging.WARNING, logger="hermes_cli.providers"):
            pdef = _resolve("myprovider", {
                "myprovider": {"base_url": "https://api.openai.com/v1"}
            })
        assert pdef is not None
        assert pdef.base_url == "https://api.openai.com/v1"
        assert not any("does not look like" in r.message for r in caplog.records)

    def test_valid_http_url_accepted(self, caplog):
        """Local/HTTP endpoints (e.g. Ollama) must also be accepted."""
        with caplog.at_level(logging.WARNING, logger="hermes_cli.providers"):
            pdef = _resolve("ollama-local", {
                "ollama-local": {"base_url": "http://localhost:11434/v1"}
            })
        assert pdef is not None
        assert pdef.base_url == "http://localhost:11434/v1"
        assert not any("does not look like" in r.message for r in caplog.records)

    def test_empty_base_url_no_warning(self, caplog):
        """Empty / missing base_url should NOT warn."""
        with caplog.at_level(logging.WARNING, logger="hermes_cli.providers"):
            pdef = _resolve("myprovider", {
                "myprovider": {}  # no url fields at all
            })
        # No warning about URL scheme
        assert not any("does not look like" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_none_entry_returns_none(self):
        pdef = _resolve("myprovider", {"myprovider": None})
        assert pdef is None

    def test_empty_providers_dict_returns_none(self):
        pdef = _resolve("myprovider", {})
        assert pdef is None

    def test_missing_provider_returns_none(self):
        pdef = _resolve("myprovider", {"otherprovider": {"base_url": "https://x.com"}})
        assert pdef is None

    def test_name_field_used_as_display_name(self):
        pdef = _resolve("myprovider", {
            "myprovider": {
                "name": "My Custom Provider",
                "base_url": "https://api.example.com/v1",
            }
        })
        assert pdef is not None
        assert pdef.name == "My Custom Provider"

    def test_provider_id_used_when_no_name(self):
        pdef = _resolve("myprovider", {
            "myprovider": {"base_url": "https://api.example.com/v1"}
        })
        assert pdef is not None
        assert pdef.id == "myprovider"

    def test_transport_field_respected(self):
        pdef = _resolve("myprovider", {
            "myprovider": {
                "base_url": "https://api.example.com/v1",
                "transport": "anthropic",
            }
        })
        assert pdef is not None
        assert pdef.transport == "anthropic"
