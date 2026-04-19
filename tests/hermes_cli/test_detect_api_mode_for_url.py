"""Tests for _detect_api_mode_for_url in runtime_provider."""

from hermes_cli.runtime_provider import _detect_api_mode_for_url


# --- OpenAI / Codex Responses ---


def test_openai_direct_returns_codex_responses():
    assert _detect_api_mode_for_url("https://api.openai.com/v1") == "codex_responses"


def test_openai_direct_case_insensitive():
    assert _detect_api_mode_for_url("https://API.OPENAI.COM/v1") == "codex_responses"


def test_openrouter_excluded():
    """OpenRouter proxies OpenAI but uses chat_completions."""
    assert _detect_api_mode_for_url("https://openrouter.ai/api.openai.com") is None


# --- Anthropic-compatible endpoints ---


def test_anthropic_direct():
    assert _detect_api_mode_for_url("https://api.anthropic.com") == "anthropic_messages"


def test_minimax_global_anthropic():
    assert _detect_api_mode_for_url("https://api.minimax.io/anthropic") == "anthropic_messages"


def test_minimax_cn_anthropic():
    assert _detect_api_mode_for_url("https://api.minimaxi.com/anthropic") == "anthropic_messages"


def test_zhipu_glm_anthropic():
    assert _detect_api_mode_for_url("https://open.bigmodel.cn/api/anthropic") == "anthropic_messages"


def test_trailing_slash_stripped():
    assert _detect_api_mode_for_url("https://api.minimax.io/anthropic/") == "anthropic_messages"


def test_litellm_proxy_anthropic():
    """LiteLLM and similar proxies commonly expose /anthropic."""
    assert _detect_api_mode_for_url("https://my-proxy.internal/anthropic") == "anthropic_messages"


# --- Unrecognised URLs fall through ---


def test_unknown_url_returns_none():
    assert _detect_api_mode_for_url("https://api.together.xyz/v1") is None


def test_empty_string_returns_none():
    assert _detect_api_mode_for_url("") is None


def test_none_returns_none():
    assert _detect_api_mode_for_url(None) is None
