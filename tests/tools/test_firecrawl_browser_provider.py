from __future__ import annotations

from unittest.mock import patch

import pytest

from tools.browser_providers.firecrawl import FirecrawlProvider


@pytest.fixture(autouse=True)
def _clear_firecrawl_env(monkeypatch):
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    monkeypatch.delenv("FIRECRAWL_API_URL", raising=False)
    monkeypatch.delenv("FIRECRAWL_BROWSER_TTL", raising=False)


def test_firecrawl_provider_self_hosted_url_only_counts_as_configured(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_URL", "http://localhost:3002")

    provider = FirecrawlProvider()

    assert provider.is_configured() is True
    assert provider._api_url() == "http://localhost:3002"
    assert provider._headers() == {"Content-Type": "application/json"}


def test_firecrawl_provider_cloud_without_key_raises_helpful_error():
    provider = FirecrawlProvider()

    with pytest.raises(ValueError, match="FIRECRAWL_API_KEY.*self-hosted Firecrawl"):
        provider._headers()


def test_firecrawl_provider_self_hosted_create_session_omits_auth_and_uses_ttl(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_URL", "http://localhost:3002/")
    monkeypatch.setenv("FIRECRAWL_BROWSER_TTL", "600")

    class _Response:
        ok = True
        status_code = 200
        text = ""

        def json(self):
            return {"id": "fc-session-1", "cdpUrl": "wss://localhost:3002/devtools/browser/123"}

    with patch("tools.browser_providers.firecrawl.requests.post", return_value=_Response()) as post:
        provider = FirecrawlProvider()
        session = provider.create_session("task-firecrawl-selfhosted")

    assert session["bb_session_id"] == "fc-session-1"
    assert session["cdp_url"] == "wss://localhost:3002/devtools/browser/123"
    assert session["features"] == {"firecrawl": True}

    call = post.call_args
    assert call.args[0] == "http://localhost:3002/v2/browser"
    assert call.kwargs["headers"] == {"Content-Type": "application/json"}
    assert call.kwargs["json"] == {"ttl": 600}


def test_firecrawl_provider_cloud_create_session_sends_bearer_token(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test-key")

    class _Response:
        ok = True
        status_code = 200
        text = ""

        def json(self):
            return {"id": "fc-session-2", "cdpUrl": "wss://api.firecrawl.dev/devtools/browser/456"}

    with patch("tools.browser_providers.firecrawl.requests.post", return_value=_Response()) as post:
        provider = FirecrawlProvider()
        provider.create_session("task-firecrawl-cloud")

    assert post.call_args.kwargs["headers"] == {
        "Content-Type": "application/json",
        "Authorization": "Bearer fc-test-key",
    }


def test_firecrawl_provider_self_hosted_missing_v2_browser_endpoint_raises_explicit_error(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_URL", "http://localhost:3002")

    class _Response:
        ok = False
        status_code = 404
        text = "not found"

    with patch("tools.browser_providers.firecrawl.requests.post", return_value=_Response()):
        provider = FirecrawlProvider()
        with pytest.raises(RuntimeError, match="v2 browser API|/v2/browser|v1-only"):
            provider.create_session("task-firecrawl-selfhosted")
