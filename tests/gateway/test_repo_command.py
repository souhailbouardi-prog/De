"""Tests for /repo gateway command and repo-pinned status output."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent
from gateway.session import SessionEntry, SessionSource


def _make_event(text="/repo", platform=Platform.TELEGRAM, user_id="12345", chat_id="67890"):
    source = SessionSource(
        platform=platform,
        user_id=user_id,
        chat_id=chat_id,
        user_name="testuser",
    )
    return MessageEvent(text=text, source=source)


def _make_session_entry():
    return SessionEntry(
        session_key="telegram:12345:67890",
        session_id="test_session_123",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        platform=Platform.TELEGRAM,
        chat_type="dm",
    )


def _make_runner(session_entry=None, session_db=None):
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, token="***")}
    )
    runner.adapters = {}
    runner._voice_mode = {}
    runner._session_db = session_db
    runner._running_agents = {}
    runner._pending_messages = {}
    runner._pending_approvals = {}
    runner._evict_cached_agent = MagicMock()

    if session_entry is None:
        session_entry = _make_session_entry()

    mock_store = MagicMock()
    mock_store.get_or_create_session.return_value = session_entry
    mock_store.set_session_repo.return_value = True
    runner.session_store = mock_store
    return runner


class TestHandleRepoCommand:
    @pytest.mark.asyncio
    async def test_show_repo_when_not_set(self):
        runner = _make_runner()
        result = await runner._handle_repo_command(_make_event("/repo"))
        assert "No repo pinned" in result
        assert "/repo /path/to/repo" in result

    @pytest.mark.asyncio
    async def test_show_repo_when_set(self):
        entry = _make_session_entry()
        entry.repo_root = "/tmp/project"
        entry.repo_name = "project"
        runner = _make_runner(session_entry=entry)
        result = await runner._handle_repo_command(_make_event("/repo"))
        assert "Repo pin: **project**" in result
        assert "/tmp/project" in result

    @pytest.mark.asyncio
    async def test_clear_repo(self):
        entry = _make_session_entry()
        entry.repo_root = "/tmp/project"
        entry.repo_name = "project"
        runner = _make_runner(session_entry=entry)
        result = await runner._handle_repo_command(_make_event("/repo clear"))
        runner.session_store.set_session_repo.assert_called_once_with(entry.session_key, None, None)
        runner._evict_cached_agent.assert_called_once_with(entry.session_key)
        assert "Cleared repo pin" in result

    @pytest.mark.asyncio
    async def test_set_repo(self, monkeypatch):
        runner = _make_runner()
        monkeypatch.setattr(
            "agent.repo_context.resolve_repo_target",
            lambda arg, base_dir=None: ("/tmp/project", "project", True),
        )
        result = await runner._handle_repo_command(_make_event("/repo ~/code/project"))
        runner.session_store.set_session_repo.assert_called_once_with(
            "telegram:12345:67890", "/tmp/project", "project"
        )
        runner._evict_cached_agent.assert_called_once_with("telegram:12345:67890")
        assert "Pinned this session to repository **project**" in result

    @pytest.mark.asyncio
    async def test_invalid_repo_path_returns_error(self, monkeypatch):
        from agent.repo_context import RepoContextError

        runner = _make_runner()
        monkeypatch.setattr(
            "agent.repo_context.resolve_repo_target",
            lambda arg, base_dir=None: (_ for _ in ()).throw(RepoContextError("bad path")),
        )
        result = await runner._handle_repo_command(_make_event("/repo nope"))
        assert "bad path" in result


@pytest.mark.asyncio
async def test_status_command_includes_repo_pin():
    from gateway.run import GatewayRunner

    entry = _make_session_entry()
    entry.repo_root = "/tmp/project"
    entry.repo_name = "project"
    runner = _make_runner(session_entry=entry, session_db=MagicMock())
    runner._session_db.get_session_title.return_value = None
    result = await GatewayRunner._handle_status_command(runner, _make_event("/status"))
    assert "**Repo:** `project` — `/tmp/project`" in result


@pytest.mark.asyncio
async def test_branch_inherits_repo_pin_to_new_session():
    from gateway.run import GatewayRunner

    entry = _make_session_entry()
    entry.repo_root = "/tmp/project"
    entry.repo_name = "project"

    session_db = MagicMock()
    session_db.get_session_title.return_value = "Current Work"
    session_db.get_next_title_in_lineage.return_value = "Current Work #2"

    runner = _make_runner(session_entry=entry, session_db=session_db)
    runner.session_store.load_transcript.return_value = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    runner.session_store.switch_session.return_value = entry
    runner._session_key_for_source = MagicMock(return_value=entry.session_key)

    result = await GatewayRunner._handle_branch_command(runner, _make_event("/branch"))

    assert "Branched to" in result
    session_db.create_session.assert_called_once()
    kwargs = session_db.create_session.call_args.kwargs
    assert kwargs["repo_root"] == "/tmp/project"
    assert kwargs["repo_name"] == "project"
