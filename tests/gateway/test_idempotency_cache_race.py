"""Tests for IdempotencyCache async reentrancy safety.

Verifies that concurrent requests with the same idempotency key
do not both execute the compute callable (idempotency guarantee).
"""
import asyncio

import pytest


class TestIdempotencyCacheRace:
    """IdempotencyCache should prevent duplicate computation for same key."""

    @pytest.mark.asyncio
    async def test_concurrent_same_key_only_computes_once(self):
        """Two concurrent requests with same idempotency key should only compute once."""
        from gateway.platforms.api_server import _IdempotencyCache

        cache = _IdempotencyCache(max_items=10, ttl_seconds=60)
        compute_count = 0

        async def slow_compute():
            nonlocal compute_count
            compute_count += 1
            await asyncio.sleep(0.1)
            return {"result": "computed"}

        # Launch two concurrent get_or_set with same key
        results = await asyncio.gather(
            cache.get_or_set("key_a", "fp_1", slow_compute),
            cache.get_or_set("key_a", "fp_1", slow_compute),
        )

        # Both should return the same result
        assert results[0] == {"result": "computed"}
        assert results[1] == {"result": "computed"}
        # But compute should only have been called ONCE
        assert compute_count == 1, f"Expected 1 computation, got {compute_count}"

    @pytest.mark.asyncio
    async def test_different_keys_compute_independently(self):
        """Different idempotency keys should compute independently."""
        from gateway.platforms.api_server import _IdempotencyCache

        cache = _IdempotencyCache(max_items=10, ttl_seconds=60)
        compute_count = 0

        async def compute():
            nonlocal compute_count
            compute_count += 1
            return {"result": compute_count}

        results = await asyncio.gather(
            cache.get_or_set("key_a", "fp_1", compute),
            cache.get_or_set("key_b", "fp_1", compute),
        )

        assert compute_count == 2, "Different keys should each trigger computation"
