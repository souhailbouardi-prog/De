"""Regression tests for reaping backgrounded children in LocalEnvironment.

When a command backgrounds a long-lived process (``python3 -m http.server &``,
``node server.js &``, etc.), the child inherits the shell's stdout pipe.
After the shell itself exits, the drain thread in ``_wait_for_process``
stays blocked reading the pipe because the child still holds the write end.
Before the fix this manifested as:

* ``execute()`` returned promptly, but the child survived indefinitely,
  holding ports/fds and leaking across successive gateway iterations.
* ``LocalEnvironment._kill_process`` fallback (``proc.kill()``) was a
  no-op on the already-reaped shell leader, so nothing reached the
  backgrounded child.

The fix is twofold:

1. ``base.py`` — if the drain thread is still alive after the join grace
   period, call ``_kill_process(proc)`` to tear down the whole group.
2. ``local.py`` — signal the group via ``proc.pid`` directly (it was the
   setsid leader at spawn) instead of ``os.getpgid(proc.pid)``, which
   raises ``ProcessLookupError`` once the leader has been reaped.
"""
import os
import socket
import time

import pytest

from tools.environments.local import LocalEnvironment


@pytest.fixture(autouse=True)
def _isolate_hermes_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / "logs").mkdir(exist_ok=True)


def _pgid_still_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
        try:
            s.bind(("::", port))
        except OSError:
            return True
    return False


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group semantics only")
def test_execute_reaps_backgrounded_child_holding_stdout():
    """A command that backgrounds a long-lived process must not leave it
    running after execute() returns. The http.server child inherits the
    shell's stdout; without the fix it survives and keeps the port bound."""
    env = LocalEnvironment(cwd="/tmp")
    port = _free_port()
    try:
        t0 = time.monotonic()
        result = env.execute(f"python3 -m http.server {port} &", timeout=30)
        elapsed = time.monotonic() - t0

        # Shell itself exited normally; the reap happens in post-exit cleanup.
        assert result["returncode"] == 0, result
        # Drain-join grace is 5 s; reap adds another 2 s at most.
        assert elapsed < 15, (
            f"execute() took {elapsed:.1f}s — reap path likely didn't engage; "
            f"before the fix this would hang until the caller's timeout."
        )

        # Give SIGTERM a moment to be delivered and the socket torn down.
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if not _port_in_use(port):
                break
            time.sleep(0.1)

        assert not _port_in_use(port), (
            f"port {port} is still bound after execute() returned — the "
            f"backgrounded http.server child was not reaped."
        )
    finally:
        try:
            env.cleanup()
        except Exception:
            pass


@pytest.mark.skipif(os.name == "nt", reason="POSIX process-group semantics only")
def test_execute_does_not_regress_plain_commands():
    """Fast commands that don't background anything must still return
    quickly (well under the 5 s drain-join grace) and succeed."""
    env = LocalEnvironment(cwd="/tmp")
    try:
        for cmd in ("echo hermes", "pwd", "ls /tmp | head -1"):
            t0 = time.monotonic()
            result = env.execute(cmd, timeout=10)
            elapsed = time.monotonic() - t0
            assert result["returncode"] == 0, (cmd, result)
            assert elapsed < 3, (
                f"{cmd!r} took {elapsed:.2f}s — plain commands should not "
                f"hit the drain-join grace path."
            )
    finally:
        try:
            env.cleanup()
        except Exception:
            pass
