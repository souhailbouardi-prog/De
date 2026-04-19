"""Regression test: background review agent must inherit full runtime config.

The background memory/skill review agent must receive base_url and api_key
from the parent agent so it hits the same provider endpoint. Without these,
custom provider users get model_not_supported errors from the review path
even though the primary request succeeded.
"""

import threading
from unittest.mock import MagicMock, patch

import pytest


def _make_parent_agent():
    """Build a minimal AIAgent-like object with the fields _run_review reads."""
    from run_agent import AIAgent

    # Use object.__new__ to skip the heavy __init__.
    agent = object.__new__(AIAgent)
    agent.model = "gpt-5.4"
    agent._base_url = "http://192.168.66.12:4000/v1/"
    agent.api_key = "sk-test-key-123"
    agent.platform = "telegram"
    agent.provider = "custom-provider"
    agent._memory_store = MagicMock()
    agent._memory_enabled = True
    agent._user_profile_enabled = False
    agent._memory_nudge_interval = 0
    agent._skill_nudge_interval = 0
    agent.background_review_callback = None
    agent._safe_print = MagicMock()
    agent._MEMORY_REVIEW_PROMPT = "review memory"
    agent._SKILL_REVIEW_PROMPT = "review skills"
    agent._COMBINED_REVIEW_PROMPT = "review both"
    return agent


def test_review_agent_inherits_base_url_and_api_key():
    """The review agent must receive base_url and api_key from the parent."""
    parent = _make_parent_agent()

    captured = {}

    def spy_init(self, **kwargs):
        captured.update(kwargs)
        # Don't actually run the full init — just record what was passed.
        raise RuntimeError("spy: stop here")

    with patch.object(parent.__class__, "__init__", spy_init):
        started_target = None
        original_thread_init = threading.Thread.__init__

        def capture_thread_init(self_thread, *args, **kwargs):
            nonlocal started_target
            started_target = kwargs.get("target")
            original_thread_init(self_thread, *args, **kwargs)

        with patch.object(threading.Thread, "__init__", capture_thread_init), \
             patch.object(threading.Thread, "start", lambda self: None):
            parent._spawn_background_review(
                messages_snapshot=[],
                review_memory=True,
                review_skills=False,
            )

        # Now call the captured target (the _run_review closure) directly
        assert started_target is not None, "_run_review thread target not captured"
        started_target()

    assert captured.get("base_url") == "http://192.168.66.12:4000/v1/", \
        f"base_url not passed to review agent: {captured}"
    assert captured.get("api_key") == "sk-test-key-123", \
        f"api_key not passed to review agent: {captured}"
    assert captured.get("model") == "gpt-5.4"
    assert captured.get("provider") == "custom-provider"
