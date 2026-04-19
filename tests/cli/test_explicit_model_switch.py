"""Tests for the _explicit_model_switch flag in HermesCLI.

Bug: After switching models via /model, the runtime credential resolver
and model normalizer would overwrite the user's choice on the next turn,
reverting the status bar and actual model back to the provider's default.

Fix: Added _explicit_model_switch flag. Once set True (by /model handlers),
_ensure_runtime_credentials() skips its model override and
_normalize_model_for_provider() returns False, preserving the user's choice.
"""

import importlib
import sys
import types
from contextlib import nullcontext

import pytest


# ---------------------------------------------------------------------------
# Module isolation helpers (same pattern as test_cli_provider_resolution.py)
# ---------------------------------------------------------------------------

def _reset_modules(prefixes: tuple[str, ...]):
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            sys.modules.pop(name, None)


@pytest.fixture(autouse=True)
def _restore_cli_and_tool_modules():
    """Save and restore tools/cli/run_agent modules around every test."""
    prefixes = ("tools", "cli", "run_agent")
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if any(name == p or name.startswith(p + ".") for p in prefixes)
    }
    try:
        yield
    finally:
        _reset_modules(prefixes)
        sys.modules.update(original_modules)


def _install_prompt_toolkit_stubs():
    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

    class _Condition:
        def __init__(self, func):
            self.func = func

        def __bool__(self):
            return bool(self.func())

    class _ANSI(str):
        pass

    root = types.ModuleType("prompt_toolkit")
    history = types.ModuleType("prompt_toolkit.history")
    styles = types.ModuleType("prompt_toolkit.styles")
    patch_stdout = types.ModuleType("prompt_toolkit.patch_stdout")
    application = types.ModuleType("prompt_toolkit.application")
    layout = types.ModuleType("prompt_toolkit.layout")
    processors = types.ModuleType("prompt_toolkit.layout.processors")
    filters = types.ModuleType("prompt_toolkit.filters")
    dimension = types.ModuleType("prompt_toolkit.layout.dimension")
    menus = types.ModuleType("prompt_toolkit.layout.menus")
    widgets = types.ModuleType("prompt_toolkit.widgets")
    key_binding = types.ModuleType("prompt_toolkit.key_binding")
    completion = types.ModuleType("prompt_toolkit.completion")
    formatted_text = types.ModuleType("prompt_toolkit.formatted_text")

    history.FileHistory = _Dummy
    styles.Style = _Dummy
    patch_stdout.patch_stdout = lambda *args, **kwargs: nullcontext()
    application.Application = _Dummy
    layout.Layout = _Dummy
    layout.HSplit = _Dummy
    layout.Window = _Dummy
    layout.FormattedTextControl = _Dummy
    layout.ConditionalContainer = _Dummy
    processors.Processor = _Dummy
    processors.Transformation = _Dummy
    processors.PasswordProcessor = _Dummy
    processors.ConditionalProcessor = _Dummy
    filters.Condition = _Condition
    dimension.Dimension = _Dummy
    menus.CompletionsMenu = _Dummy
    widgets.TextArea = _Dummy
    key_binding.KeyBindings = _Dummy
    completion.Completer = _Dummy
    completion.Completion = _Dummy
    formatted_text.ANSI = _ANSI
    root.print_formatted_text = lambda *args, **kwargs: None

    sys.modules.setdefault("prompt_toolkit", root)
    sys.modules.setdefault("prompt_toolkit.history", history)
    sys.modules.setdefault("prompt_toolkit.styles", styles)
    sys.modules.setdefault("prompt_toolkit.patch_stdout", patch_stdout)
    sys.modules.setdefault("prompt_toolkit.application", application)
    sys.modules.setdefault("prompt_toolkit.layout", layout)
    sys.modules.setdefault("prompt_toolkit.layout.processors", processors)
    sys.modules.setdefault("prompt_toolkit.filters", filters)
    sys.modules.setdefault("prompt_toolkit.layout.dimension", dimension)
    sys.modules.setdefault("prompt_toolkit.layout.menus", menus)
    sys.modules.setdefault("prompt_toolkit.widgets", widgets)
    sys.modules.setdefault("prompt_toolkit.key_binding", key_binding)
    sys.modules.setdefault("prompt_toolkit.completion", completion)
    sys.modules.setdefault("prompt_toolkit.formatted_text", formatted_text)


def _import_cli():
    for name in list(sys.modules):
        if name == "cli" or name == "run_agent" or name == "tools" or name.startswith("tools."):
            sys.modules.pop(name, None)

    if "firecrawl" not in sys.modules:
        sys.modules["firecrawl"] = types.SimpleNamespace(Firecrawl=object)

    try:
        importlib.import_module("prompt_toolkit")
    except ModuleNotFoundError:
        _install_prompt_toolkit_stubs()
    return importlib.import_module("cli")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_explicit_model_switch_defaults_to_false(monkeypatch):
    """_explicit_model_switch must be False on a fresh HermesCLI instance."""
    cli = _import_cli()
    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider",
                        lambda **kw: {"provider": "openrouter", "api_mode": "chat_completions",
                                      "base_url": "https://openrouter.ai/api/v1",
                                      "api_key": "***", "source": "env/config"})
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))

    shell = cli.HermesCLI(model="gpt-5", compact=True, max_turns=1)
    assert shell._explicit_model_switch is False


def test_runtime_resolver_does_not_overwrite_explicit_model_switch(monkeypatch):
    """When _explicit_model_switch is True, _ensure_runtime_credentials()
    must NOT replace self.model with the runtime's configured default model.

    This is the core bug: before the fix, the runtime resolver unconditionally
    overwrote self.model on every turn, reverting the user's /model choice.
    """
    cli = _import_cli()

    def _runtime_resolve(**kwargs):
        return {
            "provider": "openrouter",
            "api_mode": "chat_completions",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "***",
            "source": "env/config",
            "model": "anthropic/claude-opus-4-6",  # default model that should NOT overwrite
        }

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", _runtime_resolve)
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))

    shell = cli.HermesCLI(model="anthropic/claude-sonnet-4", compact=True, max_turns=1)

    # Set the flag as if the user used /model to switch
    shell._explicit_model_switch = True
    shell.model = "google/gemini-3-pro"

    # _ensure_runtime_credentials should preserve the explicit model
    shell._ensure_runtime_credentials()
    assert shell.model == "google/gemini-3-pro", (
        "Runtime resolver overwrote the user's explicit model choice"
    )
    assert shell._explicit_model_switch is True


def test_runtime_resolver_overwrites_when_no_explicit_switch(monkeypatch):
    """When _explicit_model_switch is False (the default), the runtime
    resolver SHOULD update self.model from the runtime config's model field.
    This is the normal startup/credential-refresh path."""
    cli = _import_cli()

    def _runtime_resolve(**kwargs):
        return {
            "provider": "openrouter",
            "api_mode": "chat_completions",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "***",
            "source": "env/config",
            "model": "anthropic/claude-opus-4-6",
        }

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", _runtime_resolve)
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))

    shell = cli.HermesCLI(model="some-model", compact=True, max_turns=1)
    shell.provider = "openrouter"
    shell.api_mode = "chat_completions"
    shell.base_url = "https://openrouter.ai/api/v1"
    shell.api_key = "existing-key"

    assert shell._explicit_model_switch is False
    shell._ensure_runtime_credentials()
    # Model should be updated to the runtime default since no explicit switch
    assert shell.model == "anthropic/claude-opus-4-6"


def test_normalize_model_skips_when_explicit_switch(monkeypatch):
    """_normalize_model_for_provider() must return False and NOT modify
    self.model when _explicit_model_switch is True."""
    cli = _import_cli()
    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider",
                        lambda **kw: {"provider": "openrouter", "api_mode": "chat_completions",
                                      "base_url": "https://openrouter.ai/api/v1",
                                      "api_key": "***", "source": "env/config"})
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))

    shell = cli.HermesCLI(model="custom/weird-model-name", compact=True, max_turns=1)
    shell._explicit_model_switch = True

    changed = shell._normalize_model_for_provider("openrouter")
    assert changed is False
    assert shell.model == "custom/weird-model-name", (
        "Normalizer modified model despite explicit switch flag"
    )


def test_normalize_model_works_when_no_explicit_switch(monkeypatch):
    """_normalize_model_for_provider() should still function normally
    when _explicit_model_switch is False."""
    cli = _import_cli()
    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider",
                        lambda **kw: {"provider": "openai-codex", "api_mode": "codex_responses",
                                      "base_url": "https://chatgpt.com/backend-api/codex",
                                      "api_key": "***", "source": "env/config"})
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))
    monkeypatch.setattr("hermes_cli.codex_models.get_codex_model_ids",
                        lambda access_token=None: ["gpt-5.2-codex"])

    shell = cli.HermesCLI(model="openai/gpt-5.3-codex", compact=True, max_turns=1)
    shell._explicit_model_switch = False

    # This should strip the "openai/" prefix via normalization
    shell._normalize_model_for_provider("openai-codex")
    assert shell.model == "gpt-5.3-codex", (
        "Normalizer didn't process model when flag was False"
    )


def test_explicit_model_switch_survives_multiple_runtime_resolves(monkeypatch):
    """The flag must persist across multiple calls to _ensure_runtime_credentials(),
    ensuring the user's model choice survives turn after turn."""
    cli = _import_cli()

    def _runtime_resolve(**kwargs):
        return {
            "provider": "openrouter",
            "api_mode": "chat_completions",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "***",
            "source": "env/config",
            "model": "anthropic/claude-opus-4-6",
        }

    monkeypatch.setattr("hermes_cli.runtime_provider.resolve_runtime_provider", _runtime_resolve)
    monkeypatch.setattr("hermes_cli.runtime_provider.format_runtime_provider_error",
                        lambda exc: str(exc))

    shell = cli.HermesCLI(model="gpt-5", compact=True, max_turns=1)
    shell._explicit_model_switch = True
    shell.model = "google/gemini-3-pro"

    # Simulate multiple turns — each calls _ensure_runtime_credentials()
    for _ in range(5):
        shell._ensure_runtime_credentials()
        assert shell.model == "google/gemini-3-pro", (
            "Model reverted after multiple runtime resolves"
        )