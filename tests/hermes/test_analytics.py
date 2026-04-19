import pytest
import threading
import time
from datetime import datetime
from agent.hermes.analytics import Event, EventBus, EventType


class TestEvent:
    def test_fields(self):
        """Event has required fields: type, payload, timestamp, session_id."""
        event = Event(type="test.type", payload={"key": "value"}, session_id="session123")
        assert event.type == "test.type"
        assert event.payload == {"key": "value"}
        assert event.session_id == "session123"
        assert isinstance(event.timestamp, datetime)

    def test_default_timestamp_is_set(self):
        """Default timestamp is automatically set via default_factory."""
        before = datetime.utcnow()
        event = Event(type="test.type", payload={})
        after = datetime.utcnow()
        assert before <= event.timestamp <= after

    def test_default_session_id_empty_string(self):
        """Default session_id is empty string."""
        event = Event(type="test.type", payload={})
        assert event.session_id == ""

    def test_timestamp_can_be_customized(self):
        """Timestamp can be explicitly provided."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        event = Event(type="test.type", payload={}, timestamp=custom_time)
        assert event.timestamp == custom_time

    def test_payload_can_be_empty(self):
        """Payload can be an empty dict."""
        event = Event(type="test.type", payload={})
        assert event.payload == {}

    def test_payload_with_nested_data(self):
        """Payload can contain nested structures."""
        payload = {
            "user": {"id": 1, "name": "test"},
            "items": [1, 2, 3],
            "nested": {"a": {"b": "c"}}
        }
        event = Event(type="test.type", payload=payload)
        assert event.payload == payload


class TestEventBusSubscribeUnsubscribe:
    def test_subscribe_adds_handler(self):
        """subscribe() adds a handler to the event type."""
        bus = EventBus()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe("test.type", handler)
        assert bus.get_handler_count("test.type") == 1

    def test_unsubscribe_removes_handler(self):
        """unsubscribe() removes a handler from the event type."""
        bus = EventBus()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe("test.type", handler)
        bus.unsubscribe("test.type", handler)
        assert bus.get_handler_count("test.type") == 0

    def test_unsubscribe_non_existent_no_error(self):
        """unsubscribe() for non-existent handler does not error."""
        bus = EventBus()

        def handler(event):
            pass

        bus.unsubscribe("test.type", handler)  # Should not raise

    def test_multiple_handlers_same_event(self):
        """Multiple handlers can be subscribed to the same event."""
        bus = EventBus()
        calls1 = []
        calls2 = []

        def handler1(event):
            calls1.append(event)

        def handler2(event):
            calls2.append(event)

        bus.subscribe("test.type", handler1)
        bus.subscribe("test.type", handler2)
        bus.emit(Event(type="test.type", payload={}))

        assert len(calls1) == 1
        assert len(calls2) == 1


class TestEventBusEmit:
    def test_emit_delivers_to_subscribed_handlers(self):
        """emit() delivers events to subscribed handlers."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test.type", handler)
        event = Event(type="test.type", payload={"data": 123})
        bus.emit(event)

        assert len(received) == 1
        assert received[0] is event
        assert received[0].payload["data"] == 123

    def test_same_thread_synchronous_delivery(self):
        """emit() delivers events synchronously in the same thread."""
        bus = EventBus()
        call_thread = None

        def handler(event):
            nonlocal call_thread
            call_thread = threading.current_thread()

        main_thread = threading.current_thread()
        bus.subscribe("test.type", handler)
        bus.emit(Event(type="test.type", payload={}))

        assert call_thread is main_thread

    def test_handler_raises_other_handlers_still_run(self):
        """If a handler raises, other handlers still receive the event."""
        bus = EventBus()
        results = []

        def failing_handler(event):
            results.append("failing")
            raise RuntimeError("handler failed")

        def success_handler(event):
            results.append("success")

        bus.subscribe("test.type", failing_handler)
        bus.subscribe("test.type", success_handler)
        bus.emit(Event(type="test.type", payload={}))

        assert "failing" in results
        assert "success" in results
        assert results.index("failing") < results.index("success")

    def test_unsubscribed_handler_does_not_fire(self):
        """An unsubscribed handler does not receive events."""
        bus = EventBus()
        calls = []

        def handler(event):
            calls.append(event)

        bus.subscribe("test.type", handler)
        bus.emit(Event(type="test.type", payload={}))
        assert len(calls) == 1

        bus.unsubscribe("test.type", handler)
        bus.emit(Event(type="test.type", payload={}))
        assert len(calls) == 1  # Still 1, not 2

    def test_empty_event_type_still_works(self):
        """Events with empty string type can still be emitted."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("", handler)
        bus.emit(Event(type="", payload={}))
        assert len(received) == 1

    def test_multiple_handlers_all_called(self):
        """When multiple handlers subscribe to same event, all are called."""
        bus = EventBus()
        results = []

        def handler1(event):
            results.append("handler1")

        def handler2(event):
            results.append("handler2")

        def handler3(event):
            results.append("handler3")

        bus.subscribe("test.type", handler1)
        bus.subscribe("test.type", handler2)
        bus.subscribe("test.type", handler3)
        bus.emit(Event(type="test.type", payload={}))

        assert len(results) == 3
        assert set(results) == {"handler1", "handler2", "handler3"}

    def test_emit_to_event_type_with_no_handlers(self):
        """emit() to event type with no handlers does nothing."""
        bus = EventBus()
        bus.emit(Event(type="nonexistent.type", payload={}))  # Should not raise

    def test_emit_event_convenience_method(self):
        """emit_event() is a convenience method to emit by type and payload."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("my.type", handler)
        bus.emit_event("my.type", {"key": "value"}, "session456")

        assert len(received) == 1
        assert received[0].type == "my.type"
        assert received[0].payload == {"key": "value"}
        assert received[0].session_id == "session456"


class TestEventBusThreadSafety:
    def test_concurrent_emit_from_multiple_threads(self):
        """Concurrent emit() calls from 10 threads are safe."""
        bus = EventBus()
        barrier = threading.Barrier(10)
        results = []

        def handler(event):
            results.append(event)

        bus.subscribe("test.type", handler)

        def emit_events():
            barrier.wait()
            for _ in range(100):
                bus.emit(Event(type="test.type", payload={}))

        threads = [threading.Thread(target=emit_events) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 1000

    def test_concurrent_subscribe_unsubscribe(self):
        """Concurrent subscribe/unsubscribe are safe."""
        bus = EventBus()
        barrier = threading.Barrier(10)
        errors = []

        def toggle_handler():
            def handler(event):
                pass

            barrier.wait()
            for _ in range(100):
                bus.subscribe("test.type", handler)
                bus.unsubscribe("test.type", handler)

        threads = [threading.Thread(target=toggle_handler) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no errors and consistent handler count
        assert len(errors) == 0


class TestEventBusClearHandlers:
    def test_clear_handlers_specific_event_type(self):
        """clear_handlers(event_type) clears only that event type."""
        bus = EventBus()

        def handler1(event):
            pass

        def handler2(event):
            pass

        bus.subscribe("type1", handler1)
        bus.subscribe("type2", handler2)
        bus.clear_handlers("type1")

        assert bus.get_handler_count("type1") == 0
        assert bus.get_handler_count("type2") == 1

    def test_clear_handlers_all_when_none_specified(self):
        """clear_handlers(None) clears all handlers."""
        bus = EventBus()

        def handler(event):
            pass

        bus.subscribe("type1", handler)
        bus.subscribe("type2", handler)
        bus.clear_handlers()

        assert bus.get_handler_count() == 0


class TestEventType:
    def test_event_type_constants_exist(self):
        """EventType class has expected constants."""
        assert EventType.TOOL_CALL == "tool.call"
        assert EventType.TOOL_RESULT == "tool.result"
        assert EventType.LLM_CALL == "llm.call"
        assert EventType.LLM_RESPONSE == "llm.response"
        assert EventType.SESSION_START == "session.start"
        assert EventType.SESSION_END == "session.end"
        assert EventType.ERROR == "error"
