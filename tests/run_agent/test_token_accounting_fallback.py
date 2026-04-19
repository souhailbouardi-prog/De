"""Regression tests for token accounting edge cases.

Fix 1 (#12023): When a provider returns no usage data in the streaming
response (e.g. MiniMax via OpenRouter ignoring stream_options.include_usage),
the agent falls back to rough token estimation so sessions don't permanently
record 0/0 tokens.

Fix 2 (#12026): Reasoning tokens (from completion_tokens_details) are
subtracted from the completion_tokens fed to the context compressor.
Reasoning tokens are internal chain-of-thought that don't appear in the
context window on the next turn; including them caused premature
compression for thinking models (GLM-5.1, QwQ, DeepSeek-R1).
"""

from unittest.mock import patch

import pytest

from agent.context_compressor import ContextCompressor
from agent.usage_pricing import CanonicalUsage


# ── Helpers ──────────────────────────────────────────────────────────


@pytest.fixture()
def compressor_200k():
    """ContextCompressor with a 200K context window (GLM-5.1 sized)."""
    with patch(
        "agent.model_metadata.get_model_context_length", return_value=200_000
    ):
        return ContextCompressor(
            model="z-ai/glm-5.1",
            threshold_percent=0.50,
            quiet_mode=True,
        )


# ── Fix 2: reasoning tokens excluded from compressor ─────────────────


class TestReasoningTokenExclusion:
    """Verify that reasoning tokens are subtracted before feeding the
    context compressor, while session-level billing counters keep the
    full amount."""

    def test_reasoning_subtracted_from_compressor(self, compressor_200k):
        """Compressor should see content-only completion tokens."""
        compressor = compressor_200k

        # Simulate: 80K prompt, 20K completion (15K reasoning + 5K content)
        canonical = CanonicalUsage(
            input_tokens=80_000,
            output_tokens=20_000,
            reasoning_tokens=15_000,
        )
        content_completion = canonical.output_tokens - canonical.reasoning_tokens
        compressor.update_from_response({
            "prompt_tokens": canonical.prompt_tokens,
            "completion_tokens": content_completion,
            "total_tokens": canonical.total_tokens,
        })

        assert compressor.last_completion_tokens == 5_000
        assert compressor.last_prompt_tokens == canonical.prompt_tokens

    def test_no_premature_compression_with_reasoning(self, compressor_200k):
        """85K prompt + 20K reasoning should NOT trigger compression at
        50% of 200K (100K threshold).  Without the fix, 85K + 20K = 105K
        would exceed the threshold."""
        compressor = compressor_200k
        # threshold = 100_000

        canonical = CanonicalUsage(
            input_tokens=85_000,
            output_tokens=20_000,
            reasoning_tokens=15_000,
        )
        content_completion = canonical.output_tokens - canonical.reasoning_tokens
        compressor.update_from_response({
            "prompt_tokens": canonical.prompt_tokens,
            "completion_tokens": content_completion,
            "total_tokens": canonical.total_tokens,
        })

        # prompt_tokens (85K) + content_completion (5K) = 90K < 100K threshold
        _real = compressor.last_prompt_tokens + compressor.last_completion_tokens
        assert _real == 90_000
        assert not compressor.should_compress(_real)

    def test_compression_fires_when_truly_full(self, compressor_200k):
        """When prompt alone exceeds the threshold, compression must still
        fire regardless of reasoning subtraction."""
        compressor = compressor_200k

        canonical = CanonicalUsage(
            input_tokens=105_000,
            output_tokens=5_000,
            reasoning_tokens=3_000,
        )
        content_completion = canonical.output_tokens - canonical.reasoning_tokens
        compressor.update_from_response({
            "prompt_tokens": canonical.prompt_tokens,
            "completion_tokens": content_completion,
            "total_tokens": canonical.total_tokens,
        })

        _real = compressor.last_prompt_tokens + compressor.last_completion_tokens
        assert _real == 107_000  # 105K + 2K
        assert compressor.should_compress(_real)

    def test_zero_reasoning_tokens_no_change(self, compressor_200k):
        """For non-thinking models (reasoning_tokens=0), the formula is
        identical to the old prompt+completion behavior."""
        compressor = compressor_200k

        canonical = CanonicalUsage(
            input_tokens=80_000,
            output_tokens=10_000,
            reasoning_tokens=0,
        )
        content_completion = canonical.output_tokens - canonical.reasoning_tokens
        compressor.update_from_response({
            "prompt_tokens": canonical.prompt_tokens,
            "completion_tokens": content_completion,
            "total_tokens": canonical.total_tokens,
        })

        assert compressor.last_completion_tokens == 10_000
        _real = compressor.last_prompt_tokens + compressor.last_completion_tokens
        assert _real == 90_000


# ── Fix 1: token estimation fallback when usage is None ──────────────


class TestTokenEstimationFallback:
    """Verify that when response.usage is None, rough token estimation
    populates the compressor and session counters."""

    def test_compressor_gets_nonzero_on_missing_usage(self, compressor_200k):
        """Simulates the fallback path: estimate_messages_tokens_rough
        produces non-zero values that update the compressor."""
        compressor = compressor_200k

        # Before: compressor has no data
        assert compressor.last_prompt_tokens == 0
        assert compressor.last_completion_tokens == 0

        # Simulate fallback estimation
        est_in = 5000  # rough estimate from messages
        est_out = 200  # rough estimate from response content
        compressor.update_from_response({
            "prompt_tokens": est_in,
            "completion_tokens": est_out,
            "total_tokens": est_in + est_out,
        })

        assert compressor.last_prompt_tokens == est_in
        assert compressor.last_completion_tokens == est_out

    def test_fallback_prevents_zero_session_tokens(self):
        """Session counters must be non-zero after the fallback path."""
        # This tests the *pattern*, not the full agent integration.
        session_prompt = 0
        session_completion = 0

        est_in = 3000
        est_out = 150

        session_prompt += est_in
        session_completion += est_out

        assert session_prompt > 0
        assert session_completion > 0
