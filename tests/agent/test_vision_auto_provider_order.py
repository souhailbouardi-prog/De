from __future__ import annotations

from agent import auxiliary_client as ac


def test_available_vision_backends_includes_codex_when_active_provider_has_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "auth.json").write_text(
        '{"active_provider":"openai-codex","providers":{"openai-codex":{"tokens":{"access_token": "codex-...oken","refresh_token": "codex-...oken"}}}}',
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AUXILIARY_VISION_PROVIDER", raising=False)
    monkeypatch.delenv("CONTEXT_VISION_PROVIDER", raising=False)

    available = ac.get_available_vision_backends()

    assert "openai-codex" in available
