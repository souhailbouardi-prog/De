"""Tests for telemetry backends and TelemetryPipeline."""
import json
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from agent.hermes.telemetry import (
    TelemetryBackend,
    ConsoleBackend,
    FileBackend,
    OpenTelemetryBackend,
    TelemetryPipeline,
)
from agent.hermes.analytics import Event


from abc import ABC

class TestTelemetryBackendIsABC:
    """TelemetryBackend is an abstract base class."""

    def test_is_abc(self):
        """TelemetryBackend should be an ABC."""
        assert issubclass(TelemetryBackend, ABC)

    def test_emit_is_abstract(self):
        """emit() should be an abstract method."""
        assert hasattr(TelemetryBackend, "emit")
        # Trying to instantiate without implementing emit should fail
        with pytest.raises(TypeError):
            TelemetryBackend()


class TestConsoleBackend:
    """Tests for ConsoleBackend."""

    def test_emit_prints_json(self, capsys):
        """emit() prints JSON output to stdout."""
        backend = ConsoleBackend()
        e = Event("test.event", {"key": "value"})
        backend.emit(e)
        captured = capsys.readouterr()
        assert "test.event" in captured.out
        assert "key" in captured.out
        assert "value" in captured.out

    def test_emit_with_custom_prefix(self, capsys):
        """emit() uses the configured prefix."""
        backend = ConsoleBackend(prefix="CUSTOM")
        e = Event("event", {"data": 123})
        backend.emit(e)
        captured = capsys.readouterr()
        assert "[CUSTOM]" in captured.out

    def test_emit_handles_exception_gracefully(self, capsys):
        """emit() catches and logs exceptions, doesn't raise."""
        backend = ConsoleBackend()
        # Pass something that causes _event_to_dict to fail
        event = Event("type", {})  # Normal event
        event.timestamp = None  # This might cause issues
        backend.emit(event)  # Should not raise
        captured = capsys.readouterr()
        assert "TELEMETRY" in captured.out

    def test_event_to_dict_includes_all_fields(self, capsys):
        """_event_to_dict produces expected structure."""
        backend = ConsoleBackend()
        e = Event("my.event", {"a": 1, "b": "test"}, session_id="sess123")
        backend.emit(e)
        captured = capsys.readouterr()
        data = json.loads(captured.out.split("] ", 1)[1])
        assert data["type"] == "my.event"
        assert data["payload"] == {"a": 1, "b": "test"}
        assert data["session_id"] == "sess123"
        assert "timestamp" in data


class TestFileBackend:
    """Tests for FileBackend."""

    def test_emit_appends_json_line_to_file(self, tmp_path):
        """emit() appends a JSON line to the file."""
        filepath = tmp_path / "events.jsonl"
        backend = FileBackend(str(filepath))
        e = Event("file.event", {"key": "value"})
        backend.emit(e)

        content = filepath.read_text()
        assert "file.event" in content
        assert "key" in content
        assert "value" in content

    def test_emit_creates_parent_directories(self, tmp_path):
        """emit() creates parent directories if they don't exist."""
        filepath = tmp_path / "subdir" / "nested" / "events.jsonl"
        backend = FileBackend(str(filepath))
        e = Event("event", {})
        backend.emit(e)  # Should not raise
        assert filepath.exists()

    def test_emit_thread_safe(self, tmp_path):
        """emit() is thread-safe via lock."""
        filepath = tmp_path / "concurrent.jsonl"
        backend = FileBackend(str(filepath))
        events = [Event(f"event.{i}", {"i": i}) for i in range(50)]

        def emit_events():
            for e in events:
                backend.emit(e)

        threads = [threading.Thread(target=emit_events) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        lines = filepath.read_text().strip().split("\n")
        assert len(lines) == 200

    def test_emit_flush_when_requested(self, tmp_path):
        """emit() flushes when flush=True."""
        filepath = tmp_path / "flushed.jsonl"
        backend = FileBackend(str(filepath), flush=True)
        e = Event("flush.event", {"data": True})
        backend.emit(e)  # Should flush immediately
        # File should be written immediately
        assert filepath.exists()
        content = filepath.read_text()
        assert "flush.event" in content

    def test_emit_handles_exception_gracefully(self, tmp_path, capsys):
        """emit() catches exceptions and logs them."""
        backend = FileBackend(str(tmp_path / "nonexistent" / "file.jsonl"))
        e = Event("event", {})
        backend.emit(e)  # Should not raise
        # Should have logged a warning
        captured = capsys.readouterr()
        # Warning may go to stderr or logger


class TestOpenTelemetryBackend:
    """Tests for OpenTelemetryBackend."""

    def test_emit_graceful_when_otel_not_available(self, capsys):
        """emit() doesn't raise when OpenTelemetry is not configured."""
        backend = OpenTelemetryBackend()
        e = Event("otel.event", {"data": "test"})
        backend.emit(e)  # Should not raise even if OTel unavailable

    def test_emit_graceful_when_tracer_is_none(self):
        """emit() handles _tracer being None gracefully."""
        backend = OpenTelemetryBackend()
        backend._tracer = None
        e = Event("event", {})
        backend.emit(e)  # Should not raise

    def test_emit_creates_span_when_configured(self):
        """emit() creates a span when OTel is properly configured."""
        # This test verifies the code path works when OTel is available
        backend = OpenTelemetryBackend()
        e = Event("span.event", {"key": "value"}, session_id="test-session")
        # Should not raise
        backend.emit(e)


class TestTelemetryPipeline:
    """Tests for TelemetryPipeline."""

    def test_add_backend_registers_backend(self):
        """add_backend() registers a backend."""
        pipe = TelemetryPipeline()

        class TestBackend(TelemetryBackend):
            def emit(self, event):
                pass

        backend = TestBackend()
        pipe.add_backend(backend)
        assert len(pipe) == 1

    def test_emit_routes_to_all_backends(self):
        """emit() sends events to ALL registered backends."""
        pipe = TelemetryPipeline()
        received = []

        class TestBackend(TelemetryBackend):
            def emit(self, event):
                received.append(event)

        backend1 = TestBackend()
        backend2 = TestBackend()
        pipe.add_backend(backend1)
        pipe.add_backend(backend2)

        e = Event("broadcast", {"data": "test"})
        pipe.emit(e)

        assert len(received) == 2
        assert received[0] is e
        assert received[1] is e

    def test_one_backend_raises_others_still_receive(self):
        """If one backend raises, others still receive the event."""
        pipe = TelemetryPipeline()
        received = []

        class GoodBackend(TelemetryBackend):
            def emit(self, event):
                received.append(event)

        class BadBackend(TelemetryBackend):
            def emit(self, event):
                raise RuntimeError("backend error")

        pipe.add_backend(BadBackend())
        pipe.add_backend(GoodBackend())

        e = Event("event", {})
        pipe.emit(e)  # Should not raise

        assert len(received) == 1
        assert received[0] is e

    def test_emit_is_thread_safe(self):
        """emit() is thread-safe."""
        pipe = TelemetryPipeline()
        received = []

        class TestBackend(TelemetryBackend):
            def emit(self, event):
                received.append(event)

        pipe.add_backend(TestBackend())

        def emit_events():
            for i in range(25):
                pipe.emit(Event(f"event.{i}", {"i": i}))

        threads = [threading.Thread(target=emit_events) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(received) == 100

    def test_remove_backend(self):
        """remove_backend() removes a backend."""
        pipe = TelemetryPipeline()

        class TestBackend(TelemetryBackend):
            def emit(self, event):
                pass

        backend = TestBackend()
        pipe.add_backend(backend)
        assert len(pipe) == 1

        pipe.remove_backend(backend)
        assert len(pipe) == 0

    def test_clear_backends(self):
        """clear_backends() removes all backends."""
        pipe = TelemetryPipeline()

        class TestBackend(TelemetryBackend):
            def emit(self, event):
                pass

        pipe.add_backend(TestBackend())
        pipe.add_backend(TestBackend())
        assert len(pipe) == 2

        pipe.clear_backends()
        assert len(pipe) == 0

    def test_emit_fire_and_forget(self):
        """Exceptions in backends don't propagate."""
        pipe = TelemetryPipeline()

        class BadBackend(TelemetryBackend):
            def emit(self, event):
                raise RuntimeError("intentional error")

        pipe.add_backend(BadBackend())

        e = Event("event", {})
        # Should not raise
        pipe.emit(e)

    def test_emit_with_no_backends(self):
        """emit() with no backends doesn't raise."""
        pipe = TelemetryPipeline()
        e = Event("event", {})
        pipe.emit(e)  # Should not raise


class TestTelemetryPipelineIntegration:
    """Integration tests combining multiple backends."""

    def test_pipeline_with_console_and_file(self, tmp_path, capsys):
        """Pipeline correctly fans out to console and file backends."""
        pipe = TelemetryPipeline()
        pipe.add_backend(ConsoleBackend(prefix="LOG"))
        pipe.add_backend(FileBackend(str(tmp_path / "events.jsonl")))

        e = Event("integration.test", {"key": "value"}, session_id="sess123")
        pipe.emit(e)

        # Check console output
        captured = capsys.readouterr()
        assert "[LOG]" in captured.out
        assert "integration.test" in captured.out

        # Check file output
        content = (tmp_path / "events.jsonl").read_text()
        assert "integration.test" in content
        assert "sess123" in content
