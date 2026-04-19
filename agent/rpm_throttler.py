"""Pre-emptive RPM throttling using x-ratelimit-* response headers.

Providers like Anthropic, OpenAI, and OpenRouter enforce RPM (requests per
minute) limits and return remaining-request counts in response headers.
This module reads the captured ``RateLimitState`` and, when the remaining
request count is critically low, sleeps until the window resets — preventing
429 errors before they happen.

Phase 2 of the rate-limit hardening work (Phase 1: concurrency semaphore
for z.ai/Kimi in #7479).
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from agent.rate_limit_tracker import RateLimitState

logger = logging.getLogger(__name__)

# Providers whose x-ratelimit-* headers are reliable enough to throttle on.
# Local/custom endpoints are excluded — their headers (if any) may not follow
# the same semantics.
RPM_THROTTLE_PROVIDERS: frozenset[str] = frozenset({
    "anthropic",
    "openai",
    "openrouter",
    "nous",
})

# Default: start sleeping when <= 2 requests remain in the minute window.
DEFAULT_RPM_THRESHOLD = 2

# Never sleep longer than this, even if the header says the window resets
# further out.  RPM windows are 60s; 65s gives a small buffer.
MAX_THROTTLE_SLEEP = 65.0

# Minimum sleep — avoids busy-spinning on near-zero reset times.
MIN_THROTTLE_SLEEP = 0.5


def maybe_throttle(
    state: Optional[RateLimitState],
    provider: str,
    *,
    threshold: int = DEFAULT_RPM_THRESHOLD,
) -> float:
    """Sleep if the RPM remaining count is at or below *threshold*.

    Args:
        state: Last captured rate-limit state (may be None if no headers
               have been seen yet).
        provider: Canonical provider name (e.g. "openai", "anthropic").
        threshold: Sleep when ``remaining_requests <= threshold``.  The
                   default (2) provides a small safety margin — waiting
                   until exactly 0 risks a race where a parallel request
                   lands before the sleep takes effect.

    Returns:
        The number of seconds actually slept (0.0 if no throttle was needed).
    """
    if state is None or not state.has_data:
        return 0.0

    # Only throttle providers with known-reliable headers.
    if provider.lower() not in RPM_THROTTLE_PROVIDERS:
        return 0.0

    bucket = state.requests_min
    if bucket.limit <= 0:
        return 0.0  # No RPM data in headers

    if bucket.remaining > threshold:
        return 0.0  # Plenty of headroom

    # How long until the minute window resets?  The bucket adjusts for
    # elapsed time since the header was captured.
    sleep_for = bucket.remaining_seconds_now
    if sleep_for < MIN_THROTTLE_SLEEP:
        # Window is about to reset anyway — don't bother sleeping.
        return 0.0

    sleep_for = min(sleep_for, MAX_THROTTLE_SLEEP)

    logger.info(
        "RPM throttle: %s has %d/%d requests remaining (threshold=%d), "
        "sleeping %.1fs until window resets",
        provider,
        bucket.remaining,
        bucket.limit,
        threshold,
        sleep_for,
    )
    # Sleep in 1s chunks so the calling thread remains responsive to
    # interrupts (Ctrl-C, agent timeout) during long throttle waits.
    slept = 0.0
    while slept < sleep_for:
        chunk = min(1.0, sleep_for - slept)
        time.sleep(chunk)
        slept += chunk
    return sleep_for
