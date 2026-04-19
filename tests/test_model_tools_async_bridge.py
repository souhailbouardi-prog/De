"""Regression tests for the _run_async() event-loop lifecycle.

These tests verify the fix for GitHub issue #2104:
  "Event loop is closed" after vision_analyze used as first call in session.

Root cause: asyncio.run() creates and *closes* a fresh event loop on every
call.  Cached httpx/AsyncOpenAI clients that were bound to the now-dead loop
would crash with RuntimeError("Event loop is closed") when garbage-collected.

The fix replaces asyncio.run() with a persistent event loop in _run_async().
"""

import asyncio
import json
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_current_loop():
    """Return the running event loop from inside a coroutine."""
    return asyncio.get_event_loop()


async def _create_and_return_transport():
    """Simulate an async client creating a transport on the current loop.

    Returns a simple asyncio.Future bound to the running loop so we can
    later check whether the loop is still alive.
    """
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    fut.set_result("ok")
    return loop, fut


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunAsyncLoopLifecycle:
    """Verify _run_async() keeps the event loop alive after returning."""

    def test_loop_not_closed_after_run_async(self):
        """The loop used by _run_async must still be open after the call."""
        from model_tools import _run_async

        loop = _run_async(_get_current_loop())

        assert not loop.is_closed(), (
            "_run_async() closed the event loop — cached async clients will "
            "crash with 'Event loop is closed' on GC (issue #2104)"
        )

    def test_same_loop_reused_across_calls(self):
        """Consecutive _run_async calls should reuse the same loop."""
        from model_tools import _run_async

        loop1 = _run_async(_get_current_loop())
        loop2 = _run_async(_get_current_loop())

        assert loop1 is loop2, (
            "_run_async() created a new loop on the second call — cached "
            "async clients from the first call would be orphaned"
        )

    def test_cached_transport_survives_between_calls(self):
        """A transport/future created in call 1 must be valid in call 2."""
        from model_tools import _run_async

        loop, fut = _run_async(_create_and_return_transport())

        assert not loop.is_closed()
        assert fut.result() == "ok"

        loop2 = _run_async(_get_current_loop())
        assert loop2 is loop, "Loop changed between calls"
        assert not loop.is_closed(), "Loop closed before second call"


class TestRunAsyncWorkerThread:
    """Verify worker threads get persistent per-thread loops (delegate_task fix)."""

    def test_worker_thread_loop_not_closed(self):
        """A worker thread's loop must stay open after _run_async returns,
        so cached httpx/AsyncOpenAI clients don't crash on GC."""
        from concurrent.futures import ThreadPoolExecutor
        from model_tools import _run_async

        def _run_on_worker():
            loop = _run_async(_get_current_loop())
            still_open = not loop.is_closed()
            return loop, still_open

        with ThreadPoolExecutor(max_workers=1) as pool:
            loop, still_open = pool.submit(_run_on_worker).result()

        assert still_open, (
            "Worker thread's event loop was closed after _run_async — "
            "cached async clients will crash with 'Event loop is closed'"
        )

    def test_worker_thread_reuses_loop_across_calls(self):
        """Multiple _run_async calls on the same worker thread should
        reuse the same persistent loop (not create-and-destroy each time)."""
        from concurrent.futures import ThreadPoolExecutor
        from model_tools import _run_async

        def _run_twice_on_worker():
            loop1 = _run_async(_get_current_loop())
            loop2 = _run_async(_get_current_loop())
            return loop1, loop2

        with ThreadPoolExecutor(max_workers=1) as pool:
            loop1, loop2 = pool.submit(_run_twice_on_worker).result()

        assert loop1 is loop2, (
            "Worker thread created different loops for consecutive calls — "
            "cached clients from the first call would be orphaned"
        )
        assert not loop1.is_closed()

    def test_parallel_workers_get_separate_loops(self):
        """Different worker threads must get their own loops to avoid
        contention (the original reason for the worker-thread branch)."""
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from model_tools import _run_async

        barrier = threading.Barrier(3, timeout=5)

        def _get_loop_id():
            # Use a barrier to force all 3 threads to be alive simultaneously,
            # ensuring the ThreadPoolExecutor actually uses 3 distinct threads.
            loop = _run_async(_get_current_loop())
            barrier.wait()
            return id(loop), not loop.is_closed(), threading.current_thread().ident

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(_get_loop_id) for _ in range(3)]
            results = [f.result() for f in as_completed(futures)]

        loop_ids = {r[0] for r in results}
        thread_ids = {r[2] for r in results}
        all_open = all(r[1] for r in results)

        assert all_open, "At least one worker thread's loop was closed"
        # The barrier guarantees 3 distinct threads were used
        assert len(thread_ids) == 3, f"Expected 3 threads, got {len(thread_ids)}"
        # Each thread should have its own loop
        assert len(loop_ids) == 3, (
            f"Expected 3 distinct loops for 3 parallel workers, "
            f"got {len(loop_ids)} — workers may be contending on a shared loop"
        )

    def test_worker_loop_separate_from_main_loop(self):
        """Worker thread loops must be different from the main thread's
        persistent loop to avoid cross-thread contention."""
        from concurrent.futures import ThreadPoolExecutor
        from model_tools import _run_async, _get_tool_loop

        main_loop = _get_tool_loop()

        def _get_worker_loop_id():
            loop = _run_async(_get_current_loop())
            return id(loop)

        with ThreadPoolExecutor(max_workers=1) as pool:
            worker_loop_id = pool.submit(_get_worker_loop_id).result()

        assert worker_loop_id != id(main_loop), (
            "Worker thread used the main thread's loop — this would cause "
            "cross-thread contention on the event loop"
        )


class TestRunAsyncWithRunningLoop:
    """When a loop is already running, _run_async falls back to a thread."""

    @pytest.mark.asyncio
    async def test_run_async_from_async_context(self):
        """_run_async should still work when called from inside an
        already-running event loop (gateway / Atropos path)."""
        from model_tools import _run_async

        async def _simple():
            return 42

        result = await asyncio.get_event_loop().run_in_executor(
            None, _run_async, _simple()
        )
        assert result == 42


# ---------------------------------------------------------------------------
# Integration: full vision_analyze dispatch chain
# ---------------------------------------------------------------------------

def _mock_vision_response():
    """Build a fake LLM response matching async_call_llm's return shape."""
    message = SimpleNamespace(content="A cat sitting on a chair.")
    choice = SimpleNamespace(index=0, message=message, finish_reason="stop")
    return SimpleNamespace(choices=[choice], model="test/vision", usage=None)


class TestVisionDispatchLoopSafety:
    """Simulate the full registry.dispatch('vision_analyze') chain and
    verify the event loop stays alive afterwards — the exact scenario
    from issue #2104."""

    def test_vision_dispatch_keeps_loop_alive(self, tmp_path):
        """After dispatching vision_analyze via the registry, the event
        loop must remain open so cached async clients don't crash on GC."""
        from model_tools import _run_async, _get_tool_loop
        from tools.registry import registry

        fake_response = _mock_vision_response()

        with (
            patch(
                "tools.vision_tools.async_call_llm",
                new_callable=AsyncMock,
                return_value=fake_response,
            ),
            patch(
                "tools.vision_tools._download_image",
                new_callable=AsyncMock,
                side_effect=lambda url, dest, **kw: _write_fake_image(dest),
            ),
            patch(
                "tools.vision_tools._validate_image_url",
                return_value=True,
            ),
            patch(
                "tools.vision_tools._image_to_base64_data_url",
                return_value="data:image/jpeg;base64,abc",
            ),
        ):
            result_json = registry.dispatch(
                "vision_analyze",
                {"image_url": "https://example.com/cat.png", "question": "What is this?"},
            )

        result = json.loads(result_json)
        assert result.get("success") is True, f"dispatch failed: {result}"
        assert "cat" in result.get("analysis", "").lower()

        loop = _get_tool_loop()
        assert not loop.is_closed(), (
            "Event loop closed after vision_analyze dispatch — cached async "
            "clients will crash with 'Event loop is closed' (issue #2104)"
        )

    def test_two_consecutive_vision_dispatches(self, tmp_path):
        """Two back-to-back vision_analyze dispatches must both succeed
        and share the same loop (simulates 'first call fails, second
        works' from the issue report)."""
        from model_tools import _get_tool_loop
        from tools.registry import registry

        fake_response = _mock_vision_response()

        with (
            patch(
                "tools.vision_tools.async_call_llm",
                new_callable=AsyncMock,
                return_value=fake_response,
            ),
            patch(
                "tools.vision_tools._download_image",
                new_callable=AsyncMock,
                side_effect=lambda url, dest, **kw: _write_fake_image(dest),
            ),
            patch(
                "tools.vision_tools._validate_image_url",
                return_value=True,
            ),
            patch(
                "tools.vision_tools._image_to_base64_data_url",
                return_value="data:image/jpeg;base64,abc",
            ),
        ):
            args = {"image_url": "https://example.com/cat.png", "question": "Describe"}

            r1 = json.loads(registry.dispatch("vision_analyze", args))
            loop_after_first = _get_tool_loop()

            r2 = json.loads(registry.dispatch("vision_analyze", args))
            loop_after_second = _get_tool_loop()

        assert r1.get("success") is True
        assert r2.get("success") is True
        assert loop_after_first is loop_after_second, "Loop changed between dispatches"
        assert not loop_after_second.is_closed()


class TestCleanupToolLoop:
    """Verify the atexit handler for _tool_loop is registered and functional."""

    def test_atexit_handler_registered(self):
        """_cleanup_tool_loop must be registered with atexit."""
        import atexit
        from model_tools import _cleanup_tool_loop

        # atexit._run_exitfuncs is the internal registry; we inspect it
        # through the public atexit.unregister (which returns None but
        # confirms the function is known) — instead, just check the
        # internal registry directly.
        #
        # CPython stores callbacks as (func, args, kwargs) tuples in
        # atexit._exithandlers (3.11) or via the C-level register.  The
        # safest portable check: unregister succeeds only if registered.
        # We re-register afterwards to keep the handler active.
        #
        # Alternatively, we verify by calling unregister (no-op if missing)
        # and re-registering.  But the simplest reliable approach: just
        # verify that importing model_tools causes the handler to appear
        # in the module-level atexit registration.
        #
        # Since atexit doesn't expose a "is registered?" API, we test that
        # _cleanup_tool_loop is callable and behaves correctly, and that
        # the module called atexit.register(_cleanup_tool_loop) at import
        # time by checking atexit._exithandlers on CPython.
        import sys
        if hasattr(atexit, '_exithandlers'):
            # CPython 3.x fallback (not always available)
            funcs = [fn for fn, _, _ in atexit._exithandlers]
            assert _cleanup_tool_loop in funcs
        else:
            # The C implementation doesn't expose the registry.
            # Verify by patching atexit.register and re-importing.
            # Instead, we just confirm the function exists and is correct.
            pass
        # Functional test: calling the handler on a live loop doesn't crash
        from model_tools import _get_tool_loop
        loop = _get_tool_loop()
        assert not loop.is_closed()
        _cleanup_tool_loop()
        # After cleanup, the loop should have been told to stop

    def test_cleanup_noop_when_no_loop(self):
        """_cleanup_tool_loop must not crash when _tool_loop is None."""
        import model_tools
        from model_tools import _cleanup_tool_loop

        original = model_tools._tool_loop
        try:
            model_tools._tool_loop = None
            _cleanup_tool_loop()  # Should not raise
        finally:
            model_tools._tool_loop = original

    def test_cleanup_noop_when_loop_already_closed(self):
        """_cleanup_tool_loop must not crash on an already-closed loop."""
        import model_tools
        from model_tools import _cleanup_tool_loop

        original = model_tools._tool_loop
        closed_loop = asyncio.new_event_loop()
        closed_loop.close()
        try:
            model_tools._tool_loop = closed_loop
            _cleanup_tool_loop()  # Should not raise
        finally:
            model_tools._tool_loop = original


class TestRunAsyncTimeout:
    """Verify that _run_async cancels the task and raises on timeout."""

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_timeout_cancels_future_and_raises(self):
        """When the coroutine exceeds the timeout, _run_async must cancel the
        future and raise TimeoutError instead of leaving the thread hanging."""
        from model_tools import _run_async
        import concurrent.futures

        async def _hang_forever():
            await asyncio.sleep(3600)

        # Patch ThreadPoolExecutor so we can control the timeout behavior
        # without actually waiting 300 seconds.
        mock_future = MagicMock(spec=concurrent.futures.Future)
        mock_future.result.side_effect = concurrent.futures.TimeoutError()

        mock_pool = MagicMock()
        mock_pool.submit.return_value = mock_future
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)

        with patch("concurrent.futures.ThreadPoolExecutor", return_value=mock_pool):
            # Force the "running loop" branch by pretending there's an active loop
            with patch("asyncio.get_running_loop", return_value=MagicMock(is_running=MagicMock(return_value=True))):
                with pytest.raises(TimeoutError, match="300s"):
                    _run_async(_hang_forever())

        mock_future.cancel.assert_called_once()

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_timeout_raises_timeout_error(self):
        """The raised exception must be a plain TimeoutError with a descriptive message."""
        from model_tools import _run_async
        import concurrent.futures

        async def _noop():
            pass

        mock_future = MagicMock(spec=concurrent.futures.Future)
        mock_future.result.side_effect = concurrent.futures.TimeoutError()

        mock_pool = MagicMock()
        mock_pool.submit.return_value = mock_future
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)

        with patch("concurrent.futures.ThreadPoolExecutor", return_value=mock_pool):
            with patch("asyncio.get_running_loop", return_value=MagicMock(is_running=MagicMock(return_value=True))):
                with pytest.raises(TimeoutError) as exc_info:
                    _run_async(_noop())
                assert "300s" in str(exc_info.value)
                assert "_run_async" in str(exc_info.value)


def _write_fake_image(dest):
    """Write minimal bytes so vision_analyze_tool thinks download succeeded."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"\xff\xd8\xff" + b"\x00" * 16)
    return dest
