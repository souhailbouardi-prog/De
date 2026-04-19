"""Regression tests for the stale-generation dequeue guard in _run_agent.

When /new (or any other command that invalidates the session run generation)
fires while an old _run_agent is still unwinding, the old run used to
dequeue pending messages from ``adapter._pending_messages`` and recurse
with its already-stale ``run_generation``.  The recursive result was
then discarded at ``_handle_message_with_agent``'s stale check, so the
user's follow-up messages were silently swallowed — busy-ack fired but
no reply was ever produced.

The fix at ``gateway/run.py`` post-run dequeue guards the pop with
``_is_session_run_current``: on stale, leave the queue intact so
``base.py``'s late-arrival drain re-enters via
``_process_message_background`` → ``_message_handler`` → ``handle_message``
→ ``_begin_session_run_generation`` — i.e. with a fresh generation.

This test follows the pattern in ``test_pending_event_none.py``:
re-derive the fixed check-and-branch logic in a small helper and
exercise both paths (stale + current) without having to drive the
full _run_agent body.
"""

from types import SimpleNamespace


def _consume_pending_if_current(runner, adapter, session_key, run_generation):
    """Mirror the post-run dequeue guard at ``gateway/run.py``.

    Returns the popped event only when ``run_generation`` is still
    current for ``session_key``; when stale, leaves
    ``adapter._pending_messages[session_key]`` intact so the drain
    at ``gateway/platforms/base.py`` can re-process the message with
    a fresh generation.
    """
    if not runner._is_session_run_current(session_key, run_generation):
        return None
    return adapter._pending_messages.pop(session_key, None)


class _Runner:
    """Minimal runner exposing ``_is_session_run_current``.

    Mirrors the method on ``GatewayRunner`` so tests don't need to
    instantiate the full runner (which pulls in every platform adapter).
    """

    def __init__(self, generations):
        self._session_run_generation = dict(generations)

    def _is_session_run_current(self, session_key, generation):
        if not session_key:
            return True
        current = int(self._session_run_generation.get(session_key, 0))
        return current == int(generation)


class _Adapter:
    def __init__(self):
        self._pending_messages = {}


class TestStaleDequeueGuard:
    def test_stale_generation_leaves_pending_in_adapter(self):
        """/new bumped current gen=4; old run at stale gen=2 must NOT pop."""
        session_key = "telegram:user:1"
        runner = _Runner({session_key: 4})
        adapter = _Adapter()
        event = SimpleNamespace(text="你认识我吗")
        adapter._pending_messages[session_key] = event

        result = _consume_pending_if_current(runner, adapter, session_key, 2)

        assert result is None, "stale run must not dequeue"
        assert session_key in adapter._pending_messages, (
            "pending must remain for base.py late-arrival drain to reprocess"
        )
        assert adapter._pending_messages[session_key] is event

    def test_current_generation_still_consumes_pending(self):
        """Non-stale runs must still pop normally."""
        session_key = "telegram:user:2"
        runner = _Runner({session_key: 3})
        adapter = _Adapter()
        event = SimpleNamespace(text="hello")
        adapter._pending_messages[session_key] = event

        result = _consume_pending_if_current(runner, adapter, session_key, 3)

        assert result is event
        assert session_key not in adapter._pending_messages

    def test_stale_with_empty_queue_still_returns_none(self):
        """Stale generation with no pending must not blow up."""
        session_key = "telegram:user:3"
        runner = _Runner({session_key: 10})
        adapter = _Adapter()

        result = _consume_pending_if_current(runner, adapter, session_key, 1)

        assert result is None
        assert session_key not in adapter._pending_messages

    def test_current_with_empty_queue_returns_none(self):
        """Current generation with no pending returns None harmlessly."""
        session_key = "telegram:user:4"
        runner = _Runner({session_key: 2})
        adapter = _Adapter()

        result = _consume_pending_if_current(runner, adapter, session_key, 2)

        assert result is None

    def test_empty_session_key_treated_as_current(self):
        """Empty session_key short-circuits to current (matches runner behavior)."""
        runner = _Runner({})
        adapter = _Adapter()

        result = _consume_pending_if_current(runner, adapter, "", 5)

        assert result is None

    def test_no_prior_generation_treats_gen_zero_as_current(self):
        """A session that never had a generation defaults to 0; gen=0 is current."""
        session_key = "fresh:user:99"
        runner = _Runner({})
        adapter = _Adapter()
        event = SimpleNamespace(text="new chat")
        adapter._pending_messages[session_key] = event

        result = _consume_pending_if_current(runner, adapter, session_key, 0)

        assert result is event
        assert session_key not in adapter._pending_messages
