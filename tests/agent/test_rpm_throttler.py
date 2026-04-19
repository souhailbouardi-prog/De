"""Tests for agent.rpm_throttler — pre-emptive RPM throttling."""

import time
from unittest.mock import patch

import pytest
from agent.rate_limit_tracker import RateLimitBucket, RateLimitState
from agent.rpm_throttler import (
    DEFAULT_RPM_THRESHOLD,
    MAX_THROTTLE_SLEEP,
    MIN_THROTTLE_SLEEP,
    RPM_THROTTLE_PROVIDERS,
    maybe_throttle,
)


def _make_state(
    remaining: int = 100,
    limit: int = 800,
    reset_seconds: float = 45.0,
    provider: str = "openai",
) -> RateLimitState:
    """Build a RateLimitState with the given requests_min bucket."""
    now = time.time()
    return RateLimitState(
        requests_min=RateLimitBucket(
            limit=limit,
            remaining=remaining,
            reset_seconds=reset_seconds,
            captured_at=now,
        ),
        captured_at=now,
        provider=provider,
    )


# ── Provider filtering ────────────────────────────────────────────────────


class TestProviderFiltering:
    def test_throttle_providers_set(self):
        assert "anthropic" in RPM_THROTTLE_PROVIDERS
        assert "openai" in RPM_THROTTLE_PROVIDERS
        assert "openrouter" in RPM_THROTTLE_PROVIDERS
        assert "nous" in RPM_THROTTLE_PROVIDERS

    def test_skips_unknown_provider(self):
        state = _make_state(remaining=0, reset_seconds=30.0, provider="zai")
        slept = maybe_throttle(state, "zai")
        assert slept == 0.0

    def test_skips_local_provider(self):
        state = _make_state(remaining=0, reset_seconds=30.0, provider="ollama")
        slept = maybe_throttle(state, "ollama")
        assert slept == 0.0

    def test_case_insensitive_provider(self):
        state = _make_state(remaining=1, reset_seconds=10.0, provider="OpenAI")
        with patch("agent.rpm_throttler.time.sleep"):
            slept = maybe_throttle(state, "OpenAI")
            assert slept > 0.0


# ── No-op cases ───────────────────────────────────────────────────────────


class TestNoOp:
    def test_none_state(self):
        assert maybe_throttle(None, "openai") == 0.0

    def test_empty_state(self):
        state = RateLimitState()
        assert maybe_throttle(state, "openai") == 0.0

    def test_no_rpm_data(self):
        state = _make_state(limit=0, remaining=0, provider="openai")
        assert maybe_throttle(state, "openai") == 0.0

    def test_plenty_of_headroom(self):
        state = _make_state(remaining=100, limit=800, provider="openai")
        assert maybe_throttle(state, "openai") == 0.0

    def test_just_above_threshold(self):
        state = _make_state(
            remaining=DEFAULT_RPM_THRESHOLD + 1,
            limit=800,
            provider="openai",
        )
        assert maybe_throttle(state, "openai") == 0.0

    def test_near_zero_reset_skipped(self):
        """Don't sleep if the window is about to reset anyway."""
        state = _make_state(
            remaining=1, reset_seconds=0.1, provider="openai"
        )
        assert maybe_throttle(state, "openai") == 0.0


# ── Throttle fires ────────────────────────────────────────────────────────


class TestThrottleFires:
    @patch("agent.rpm_throttler.time.sleep")
    def test_sleeps_when_at_threshold(self, mock_sleep):
        state = _make_state(remaining=2, reset_seconds=30.0, provider="openai")
        slept = maybe_throttle(state, "openai")
        assert slept == pytest.approx(30.0, abs=1.0)
        assert mock_sleep.call_count > 0

    @patch("agent.rpm_throttler.time.sleep")
    def test_sleeps_when_zero_remaining(self, mock_sleep):
        state = _make_state(remaining=0, reset_seconds=45.0, provider="anthropic")
        slept = maybe_throttle(state, "anthropic")
        assert slept == pytest.approx(45.0, abs=1.0)
        assert mock_sleep.call_count > 0

    @patch("agent.rpm_throttler.time.sleep")
    def test_capped_at_max_sleep(self, mock_sleep):
        state = _make_state(remaining=0, reset_seconds=120.0, provider="openai")
        slept = maybe_throttle(state, "openai")
        assert slept == MAX_THROTTLE_SLEEP
        # Sleeps in 1s chunks; total call count should match ceil(MAX_THROTTLE_SLEEP)
        assert mock_sleep.call_count > 0

    @patch("agent.rpm_throttler.time.sleep")
    def test_respects_min_sleep(self, mock_sleep):
        """Reset time below MIN_THROTTLE_SLEEP should not trigger a sleep."""
        state = _make_state(
            remaining=1,
            reset_seconds=MIN_THROTTLE_SLEEP - 0.1,
            provider="openai",
        )
        slept = maybe_throttle(state, "openai")
        assert slept == 0.0
        mock_sleep.assert_not_called()


# ── Custom threshold ──────────────────────────────────────────────────────


class TestCustomThreshold:
    @patch("agent.rpm_throttler.time.sleep")
    def test_higher_threshold(self, mock_sleep):
        state = _make_state(remaining=5, reset_seconds=20.0, provider="openai")
        # Default threshold (2) would not trigger
        assert maybe_throttle(state, "openai", threshold=2) == 0.0
        # Threshold of 5 should trigger
        slept = maybe_throttle(state, "openai", threshold=5)
        assert slept > 0.0

    @patch("agent.rpm_throttler.time.sleep")
    def test_threshold_zero(self, mock_sleep):
        """Threshold 0 = only sleep when remaining is literally 0."""
        state = _make_state(remaining=1, reset_seconds=30.0, provider="openai")
        assert maybe_throttle(state, "openai", threshold=0) == 0.0

        state_zero = _make_state(remaining=0, reset_seconds=30.0, provider="openai")
        slept = maybe_throttle(state_zero, "openai", threshold=0)
        assert slept > 0.0


# ── Elapsed time adjustment ──────────────────────────────────────────────


class TestElapsedAdjustment:
    @patch("agent.rpm_throttler.time.sleep")
    def test_adjusts_for_elapsed_time(self, mock_sleep):
        """Sleep time should decrease as time passes since header capture."""
        state = _make_state(remaining=0, reset_seconds=30.0, provider="openai")
        # Simulate 20 seconds elapsed
        state.requests_min.captured_at -= 20.0
        slept = maybe_throttle(state, "openai")
        # Should sleep ~10s, not 30s
        assert slept == pytest.approx(10.0, abs=1.0)

    @patch("agent.rpm_throttler.time.sleep")
    def test_fully_elapsed_no_sleep(self, mock_sleep):
        """If the reset window has already passed, no sleep needed."""
        state = _make_state(remaining=0, reset_seconds=30.0, provider="openai")
        state.requests_min.captured_at -= 31.0
        slept = maybe_throttle(state, "openai")
        assert slept == 0.0
        mock_sleep.assert_not_called()


# ── Logging ───────────────────────────────────────────────────────────────


class TestLogging:
    @patch("agent.rpm_throttler.time.sleep")
    def test_logs_when_throttling(self, mock_sleep, caplog):
        import logging

        state = _make_state(remaining=1, reset_seconds=20.0, provider="openai")
        with caplog.at_level(logging.INFO, logger="agent.rpm_throttler"):
            maybe_throttle(state, "openai")
        assert "RPM throttle" in caplog.text
        assert "openai" in caplog.text
        assert "sleeping" in caplog.text

    def test_no_log_when_not_throttling(self, caplog):
        import logging

        state = _make_state(remaining=100, provider="openai")
        with caplog.at_level(logging.INFO, logger="agent.rpm_throttler"):
            maybe_throttle(state, "openai")
        assert "RPM throttle" not in caplog.text
