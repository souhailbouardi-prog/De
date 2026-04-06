import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from plugins.memory.honcho import HonchoMemoryProvider


def _make_ready_provider(manager=None):
    provider = HonchoMemoryProvider()
    provider._manager = manager or MagicMock()
    provider._session_key = "honcho-test-session"
    provider._session_initialized = True
    return provider


class FakeHonchoError(Exception):
    def __init__(self, message: str, *, status: int = 0, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code


def _make_cfg(recall_mode: str = "hybrid", *, init_on_session_start: bool = False):
    return SimpleNamespace(
        enabled=True,
        api_key="test-key",
        base_url="https://api.honcho.dev",
        recall_mode=recall_mode,
        raw={},
        context_tokens=None,
        init_on_session_start=init_on_session_start,
        resolve_session_name=lambda **kwargs: "honcho-test-session",
    )


def _wire_provider(monkeypatch, provider, cfg, manager):
    import plugins.memory.honcho as honcho_provider_mod
    import plugins.memory.honcho.client as honcho_client_mod
    import plugins.memory.honcho.session as honcho_session_mod

    monkeypatch.setattr(honcho_provider_mod.time, "sleep", lambda _: None)
    monkeypatch.setattr(honcho_client_mod.HonchoClientConfig, "from_global_config", lambda: cfg)
    monkeypatch.setattr(honcho_client_mod, "get_honcho_client", lambda _cfg=None: object())
    monkeypatch.setattr(honcho_session_mod, "HonchoSessionManager", lambda **kwargs: manager)


def test_eager_init_failure_surfaces_real_bootstrap_error(monkeypatch):
    provider = HonchoMemoryProvider()
    cfg = _make_cfg("hybrid")

    manager = MagicMock()
    manager.get_or_create.side_effect = [
        FakeHonchoError("workspace bootstrap exploded", status=500),
        FakeHonchoError("workspace bootstrap exploded", status=500),
    ]

    _wire_provider(monkeypatch, provider, cfg, manager)

    provider.initialize("session-1")
    result = json.loads(provider.handle_tool_call("honcho_profile", {}))

    assert result == {
        "error": "Honcho memory unavailable for this operation: session bootstrap failed: workspace bootstrap exploded (HTTP 500)."
    }
    assert manager.get_or_create.call_count == 2



def test_tools_mode_lazy_init_failure_surfaces_timeout_detail(monkeypatch):
    provider = HonchoMemoryProvider()
    cfg = _make_cfg("tools")

    manager = MagicMock()
    manager.get_or_create.side_effect = [
        FakeHonchoError("Request timed out", code="timeout"),
        FakeHonchoError("Request timed out", code="timeout"),
    ]

    _wire_provider(monkeypatch, provider, cfg, manager)

    provider.initialize("session-2")
    result = json.loads(provider.handle_tool_call("honcho_profile", {}))

    assert result == {
        "error": "Honcho memory unavailable for this operation: session bootstrap timed out (FakeHonchoError)."
    }
    assert manager.get_or_create.call_count == 2



def test_session_init_retries_once_on_transient_error_and_recovers(monkeypatch):
    provider = HonchoMemoryProvider()
    cfg = _make_cfg("hybrid")

    fake_session = SimpleNamespace(messages=[])
    manager = MagicMock(
        get_or_create=MagicMock(
            side_effect=[FakeHonchoError("server busy", status=500), fake_session]
        ),
        migrate_memory_files=MagicMock(),
        prefetch_context=MagicMock(),
        prefetch_dialectic=MagicMock(),
    )

    _wire_provider(monkeypatch, provider, cfg, manager)

    provider.initialize("session-3")

    assert provider._session_initialized is True
    assert provider._last_init_error == ""
    assert manager.get_or_create.call_count == 2
    manager.migrate_memory_files.assert_called_once()
    manager.prefetch_context.assert_called_once_with("honcho-test-session")
    manager.prefetch_dialectic.assert_called_once_with(
        "honcho-test-session", "What should I know about this user?"
    )



def test_honcho_profile_returns_card(monkeypatch):
    manager = MagicMock(get_peer_card=MagicMock(return_value=["Name: Alice", "Role: Dev"]))
    provider = _make_ready_provider(manager)

    result = json.loads(provider.handle_tool_call("honcho_profile", {}))

    assert result == {"result": ["Name: Alice", "Role: Dev"]}
    manager.get_peer_card.assert_called_once_with("honcho-test-session")



def test_honcho_search_requires_query():
    provider = _make_ready_provider()

    result = json.loads(provider.handle_tool_call("honcho_search", {}))

    assert result == {"error": "Missing required parameter: query"}



def test_honcho_search_returns_no_context_message():
    manager = MagicMock(search_context=MagicMock(return_value=""))
    provider = _make_ready_provider(manager)

    result = json.loads(provider.handle_tool_call("honcho_search", {"query": "alice"}))

    assert result == {"result": "No relevant context found."}
    manager.search_context.assert_called_once_with(
        "honcho-test-session", "alice", max_tokens=800
    )



def test_honcho_search_caps_max_tokens():
    manager = MagicMock(search_context=MagicMock(return_value="ctx"))
    provider = _make_ready_provider(manager)

    result = json.loads(
        provider.handle_tool_call("honcho_search", {"query": "alice", "max_tokens": 9000})
    )

    assert result == {"result": "ctx"}
    manager.search_context.assert_called_once_with(
        "honcho-test-session", "alice", max_tokens=2000
    )



def test_honcho_context_requires_query():
    provider = _make_ready_provider()

    result = json.loads(provider.handle_tool_call("honcho_context", {}))

    assert result == {"error": "Missing required parameter: query"}



def test_honcho_context_returns_result_and_default_peer():
    manager = MagicMock(dialectic_query=MagicMock(return_value="Alice prefers pt-BR"))
    provider = _make_ready_provider(manager)

    result = json.loads(provider.handle_tool_call("honcho_context", {"query": "prefs?"}))

    assert result == {"result": "Alice prefers pt-BR"}
    manager.dialectic_query.assert_called_once_with(
        "honcho-test-session", "prefs?", peer="user"
    )



def test_honcho_conclude_requires_conclusion():
    provider = _make_ready_provider()

    result = json.loads(provider.handle_tool_call("honcho_conclude", {}))

    assert result == {"error": "Missing required parameter: conclusion"}



def test_honcho_conclude_returns_failure_message_when_write_fails():
    manager = MagicMock(create_conclusion=MagicMock(return_value=False))
    provider = _make_ready_provider(manager)

    result = json.loads(
        provider.handle_tool_call("honcho_conclude", {"conclusion": "User prefers uv"})
    )

    assert result == {"error": "Failed to save conclusion."}
    manager.create_conclusion.assert_called_once_with(
        "honcho-test-session", "User prefers uv"
    )



def test_honcho_conclude_returns_success_message():
    manager = MagicMock(create_conclusion=MagicMock(return_value=True))
    provider = _make_ready_provider(manager)

    result = json.loads(
        provider.handle_tool_call("honcho_conclude", {"conclusion": "User prefers uv"})
    )

    assert result == {"result": "Conclusion saved: User prefers uv"}



def test_honcho_tool_failure_is_scoped_to_operation():
    manager = MagicMock(
        search_context=MagicMock(side_effect=RuntimeError("peer search broke")),
        get_peer_card=MagicMock(return_value=["Name: Alice"]),
    )
    provider = _make_ready_provider(manager)

    result = json.loads(provider.handle_tool_call("honcho_search", {"query": "alice"}))
    follow_up = json.loads(provider.handle_tool_call("honcho_profile", {}))

    assert result == {"error": "Honcho honcho_search failed: peer search broke"}
    assert follow_up == {"result": ["Name: Alice"]}
