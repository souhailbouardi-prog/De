import pytest
import threading
import time
from agent.hermes.shutdown import ShutdownManager


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton before each test."""
    ShutdownManager._instance = None
    yield
    ShutdownManager._instance = None


class TestShutdownManagerSingleton:
    def test_get_instance_returns_same_instance(self):
        """get_instance() returns the same instance on multiple calls."""
        sm1 = ShutdownManager.get_instance()
        sm2 = ShutdownManager.get_instance()
        assert sm1 is sm2

    def test_get_instance_creates_instance(self):
        """get_instance() creates the instance if not exists."""
        ShutdownManager._instance = None
        sm = ShutdownManager.get_instance()
        assert sm is not None
        assert isinstance(sm, ShutdownManager)

    def test_singleton_isolation(self):
        """Multiple instances cannot be created via __init__."""
        sm1 = ShutdownManager.get_instance()
        sm2 = ShutdownManager.__new__(ShutdownManager)
        sm2.__init__()
        # sm2 should still reference the same singleton
        assert ShutdownManager.get_instance() is sm1


class TestShutdownManagerRegister:
    def test_register_adds_callback(self):
        """register() adds a callback to the hooks list."""
        sm = ShutdownManager.get_instance()
        called = []

        def my_callback():
            called.append(True)

        sm.register(my_callback)
        assert sm.hook_count == 1

    def test_register_with_priority(self):
        """register() accepts a priority parameter."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()

        def low_priority():
            pass

        def high_priority():
            pass

        sm.register(low_priority, priority=50)
        sm.register(high_priority, priority=10)
        assert sm.hook_count == 2

    def test_multiple_registrations(self):
        """Multiple callbacks can be registered."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()

        def cb1():
            pass

        def cb2():
            pass

        sm.register(cb1)
        sm.register(cb2)
        assert sm.hook_count == 2


class TestShutdownManagerExecute:
    def test_execute_runs_hooks_in_ascending_priority_order(self):
        """execute() runs callbacks in ASCENDING priority order (lower = first)."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        execution_order = []

        def cb_low():
            execution_order.append("low")

        def cb_high():
            execution_order.append("high")

        def cb_medium():
            execution_order.append("medium")

        sm.register(cb_high, priority=60)
        sm.register(cb_low, priority=40)
        sm.register(cb_medium, priority=50)

        sm.execute()

        assert execution_order == ["low", "medium", "high"]

    def test_execute_runs_hooks_once(self):
        """execute() runs hooks exactly once even if called multiple times."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        count = 0

        def my_callback():
            nonlocal count
            count += 1

        sm.register(my_callback)
        sm.execute()
        sm.execute()
        sm.execute()

        assert count == 1

    def test_empty_hooks_execute_does_nothing(self):
        """execute() with no hooks does nothing (no error)."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        sm.execute()  # Should not raise

    def test_callback_raises_other_callbacks_still_run(self):
        """If a callback raises, other callbacks still run."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        execution_order = []

        def failing_callback():
            execution_order.append("failing")
            raise RuntimeError("callback failed")

        def success_callback():
            execution_order.append("success")

        sm.register(success_callback, priority=50)
        sm.register(failing_callback, priority=40)
        sm.register(success_callback, priority=60)

        sm.execute()

        assert execution_order == ["failing", "success", "success"]

    def test_same_priority_fifo_order(self):
        """Same priority callbacks run in FIFO order."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        execution_order = []

        def cb1():
            execution_order.append(1)

        def cb2():
            execution_order.append(2)

        def cb3():
            execution_order.append(3)

        sm.register(cb1, priority=50)
        sm.register(cb2, priority=50)
        sm.register(cb3, priority=50)

        sm.execute()

        assert execution_order == [1, 2, 3]


class TestShutdownManagerThreadSafety:
    def test_concurrent_register_no_race(self):
        """Concurrent register() calls don't race."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()

        barrier = threading.Barrier(10)
        results = []

        def register_callback():
            def cb():
                results.append(threading.get_ident())
            barrier.wait()
            sm.register(cb, priority=threading.get_ident() % 100)
            return cb

        threads = [threading.Thread(target=register_callback) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All callbacks should be registered
        assert sm.hook_count == 10

    def test_concurrent_execute_is_safe(self):
        """Concurrent execute() calls are safe (hooks run once)."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        count = 0

        def my_callback():
            nonlocal count
            count += 1

        sm.register(my_callback)

        barrier = threading.Barrier(5)
        errors = []

        def call_execute():
            barrier.wait()
            try:
                sm.execute()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_execute) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert count == 1
        assert len(errors) == 0


class TestShutdownManagerHookCount:
    def test_hook_count_initial_zero(self):
        """hook_count is 0 initially."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()
        assert sm.hook_count == 0

    def test_hook_count_after_register(self):
        """hook_count reflects registered callbacks."""
        sm = ShutdownManager.get_instance()
        sm.clear_hooks()

        def cb1():
            pass

        def cb2():
            pass

        sm.register(cb1)
        assert sm.hook_count == 1
        sm.register(cb2)
        assert sm.hook_count == 2

    def test_clear_hooks_resets_count(self):
        """clear_hooks() resets the hook count to 0."""
        sm = ShutdownManager.get_instance()

        def cb():
            pass

        sm.register(cb)
        sm.clear_hooks()
        assert sm.hook_count == 0
