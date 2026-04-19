import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class _FakeAgent:
    def __init__(self, result=None):
        self.quiet_mode = False
        self.suppress_status_output = False
        self.stream_delta_callback = object()
        self.tool_gen_callback = object()
        self.calls = []
        self.result = result or {"final_response": "hello once", "failed": False}

    def run_conversation(self, user_message, conversation_history):
        self.calls.append(
            {
                "user_message": user_message,
                "conversation_history": conversation_history,
            }
        )
        return self.result


class _FakeCLI:
    def __init__(self, result=None):
        self._app = None
        self._result = result
        self.agent = _FakeAgent(result=result)
        self.session_id = "sess_test"
        self.conversation_history = []
        self.tool_progress_mode = "all"
        self._active_agent_route_signature = None
        self.provider = "openai-codex"

    def _ensure_runtime_credentials(self):
        return True

    def _preprocess_images_with_vision(self, query, images, announce=False):
        return query

    def _resolve_turn_agent_config(self, effective_query):
        return {
            "signature": ("sig",),
            "model": "gpt-5.4",
            "runtime": {"provider": "openai-codex"},
            "label": "default",
            "request_overrides": None,
        }

    def _init_agent(self, **kwargs):
        if self.agent is None:
            self.agent = _FakeAgent(result=self._result)
        return True


def test_quiet_single_query_disables_stream_callbacks_and_prints_once(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI()
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True)

    assert exc.value.code == 0
    assert fake_cli.agent.stream_delta_callback is None
    assert fake_cli.agent.tool_gen_callback is None
    assert fake_cli.agent.calls == [
        {
            "user_message": "test",
            "conversation_history": [],
        }
    ]

    out = capsys.readouterr().out
    assert out == "hello once\nsession_id: sess_test\n"


def test_quiet_single_query_failed_result_is_single_block_and_exit_1(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI(result={"final_response": "Error: boom", "failed": True})
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True)

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert out == "Error: boom\nsession_id: sess_test\n"


def test_quiet_single_query_failed_result_without_final_response_uses_error_field(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI(result={"failed": True, "error": "rate limited"})
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True)

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert out == "Error: rate limited\nsession_id: sess_test\n"


def test_quiet_single_query_json_success(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI()
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True, output_format="json")

    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": True,
        "response": "hello once",
        "session_id": "sess_test",
    }


def test_quiet_single_query_json_failure(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI(result={"failed": True, "error": "rate limited"})
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True, output_format="json")

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": False,
        "response": "Error: rate limited",
        "session_id": "sess_test",
        "error": "rate limited",
    }


def test_quiet_single_query_json_with_metadata(monkeypatch, capsys):
    import cli as cli_module

    fake_cli = _FakeCLI()
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)
    monkeypatch.setattr(cli_module, "_collect_query_images", lambda query, image: (query, []))

    with pytest.raises(SystemExit) as exc:
        cli_module.main(query="test", quiet=True, output_format="json", include_metadata=True)

    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "ok": True,
        "response": "hello once",
        "session_id": "sess_test",
        "metadata": {
            "format": "json",
            "failed": False,
            "model": "gpt-5.4",
            "provider": "openai-codex",
        },
    }


def test_json_format_requires_quiet(monkeypatch):
    import cli as cli_module

    fake_cli = _FakeCLI()
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)

    with pytest.raises(ValueError, match="requires --quiet"):
        cli_module.main(query="test", quiet=False, output_format="json")


def test_include_metadata_requires_json(monkeypatch):
    import cli as cli_module

    fake_cli = _FakeCLI()
    monkeypatch.setattr(cli_module, "HermesCLI", lambda *args, **kwargs: fake_cli)

    with pytest.raises(ValueError, match="requires --format json"):
        cli_module.main(query="test", quiet=True, output_format="text", include_metadata=True)


import pytest
