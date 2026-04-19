"""Tests for gateway/session.py — SessionManager."""

import os
import tempfile
from pathlib import Path

import pytest

from gateway.session_manager import SessionManager


@pytest.fixture
def sm(tmp_path):
    """SessionManager with temp DB."""
    db = tmp_path / "test_sessions.db"
    return SessionManager(db_path=db)


class TestTouch:
    def test_basic_touch(self, sm):
        result = sm.touch("discord_12345", topic_guess="test")
        assert result["thread_id"] == "discord_12345"
        assert result["platform"] == "discord"
        assert result["topic"] == "test"

    def test_touch_increments_count(self, sm):
        sm.touch("discord_12345")
        sm.touch("discord_12345")
        ctx = sm.get_context("discord_12345")
        assert ctx["message_count"] == 2

    def test_touch_does_not_overwrite_topic_with_empty(self, sm):
        sm.touch("discord_12345", topic_guess="original")
        sm.touch("discord_12345", topic_guess="")
        ctx = sm.get_context("discord_12345")
        assert ctx["topic"] == "original"

    def test_touch_overwrites_topic_with_new(self, sm):
        sm.touch("discord_12345", topic_guess="original")
        sm.touch("discord_12345", topic_guess="updated")
        ctx = sm.get_context("discord_12345")
        assert ctx["topic"] == "updated"

    def test_touch_tracks_user(self, sm):
        sm.touch("discord_12345", user_id="user_abc")
        ctx = sm.get_context("discord_12345")
        assert ctx["user_id"] == "user_abc"

    def test_touch_empty_thread_id(self, sm):
        result = sm.touch("")
        assert result == {}


class TestLoad:
    def test_load_from_sources(self, sm):
        sources = [
            {"thread_id": "discord_111", "topic": "one"},
            {"thread_id": "telegram_222", "topic": "two"},
        ]
        result = sm.load(sources)
        assert result["imported"] == 2

        ctx = sm.get_context("discord_111")
        assert ctx["exists"] is True
        assert ctx["topic"] == "one"

    def test_load_empty(self, sm):
        result = sm.load()
        assert result["imported"] == 0


class TestGetContext:
    def test_nonexistent_thread(self, sm):
        ctx = sm.get_context("discord_doesnotexist")
        assert ctx["exists"] is False

    def test_context_fields(self, sm):
        sm.touch("discord_12345", topic_guess="test",
                 user_id="user_abc", platform="discord")
        ctx = sm.get_context("discord_12345")
        assert ctx["thread_id"] == "discord_12345"
        assert ctx["user_id"] == "user_abc"
        assert ctx["platform"] == "discord"
        assert ctx["topic"] == "test"
        assert ctx["message_count"] == 1
        assert ctx["age"] == "just now"
        assert isinstance(ctx["related_threads"], list)

    def test_related_threads(self, sm):
        sm.touch("discord_111", topic_guess="one", user_id="user_abc")
        sm.touch("discord_222", topic_guess="two", user_id="user_abc")
        ctx = sm.get_context("discord_111")
        related_ids = [r["thread_id"] for r in ctx["related_threads"]]
        assert "discord_222" in related_ids

    def test_deep_context_with_provider(self, sm):
        sm.touch("discord_12345", topic_guess="python")
        sm.set_memory_provider(lambda topic: f"memory for {topic}")
        ctx = sm.get_context("discord_12345", deep=True)
        assert ctx.get("memory_hint") == "memory for python"

    def test_deep_context_no_provider(self, sm):
        sm.touch("discord_12345", topic_guess="python")
        ctx = sm.get_context("discord_12345", deep=True)
        assert "memory_hint" not in ctx


class TestUserThreads:
    def test_get_user_threads(self, sm):
        sm.touch("discord_111", user_id="user_abc")
        sm.touch("discord_222", user_id="user_abc")
        threads = sm.get_user_threads("user_abc")
        assert len(threads) == 2
        ids = [t["thread_id"] for t in threads]
        assert "discord_111" in ids
        assert "discord_222" in ids


class TestStats:
    def test_stats(self, sm):
        sm.touch("discord_111", user_id="u1")
        sm.touch("telegram_222", user_id="u2")
        stats = sm.stats()
        assert stats["total_sessions"] == 2
        assert stats["active_24h"] == 2
        assert stats["unique_users"] == 2
        assert stats["by_platform"]["discord"] == 1
        assert stats["by_platform"]["telegram"] == 1
