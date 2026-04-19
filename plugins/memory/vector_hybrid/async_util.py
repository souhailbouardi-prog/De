"""Dedicated asyncio loop for optional async vector backends."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine, TypeVar

_T = TypeVar("_T")

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_loop_lock = threading.Lock()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _loop, _loop_thread
    with _loop_lock:
        if _loop is not None and _loop.is_running():
            return _loop
        _loop = asyncio.new_event_loop()

        def _run() -> None:
            asyncio.set_event_loop(_loop)
            assert _loop is not None
            _loop.run_forever()

        _loop_thread = threading.Thread(target=_run, daemon=True, name="vector-hybrid-loop")
        _loop_thread.start()
        return _loop


def run_async(coro: Coroutine[Any, Any, _T], *, timeout: float = 120.0) -> _T:
    """Run *coro* on the shared loop from a sync caller."""
    loop = _ensure_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout=timeout)
