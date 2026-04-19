import pytest
import threading
import time
from datetime import datetime
from agent.hermes.mailbox import Mailbox, MailboxMessage


class TestMailboxMessage:
    def test_fields(self):
        """MailboxMessage has required fields: priority, content, timestamp, id."""
        msg = MailboxMessage(priority=5, content="hello world", id="msg-123")
        assert msg.priority == 5
        assert msg.content == "hello world"
        assert msg.id == "msg-123"
        assert isinstance(msg.timestamp, datetime)

    def test_default_timestamp_is_set(self):
        """Default timestamp is automatically set."""
        before = datetime.utcnow()
        msg = MailboxMessage(priority=0, content="test")
        after = datetime.utcnow()
        assert before <= msg.timestamp <= after

    def test_priority_comparison(self):
        """Messages are compared by priority (lower = higher priority)."""
        low_priority = MailboxMessage(priority=10, content="low")
        high_priority = MailboxMessage(priority=1, content="high")
        assert high_priority < low_priority

    def test_same_priority_fifo_by_timestamp(self):
        """When priorities are equal, earlier timestamp comes first."""
        earlier_time = datetime(2023, 1, 1, 10, 0, 0)
        later_time = datetime(2023, 1, 1, 10, 0, 1)

        msg1 = MailboxMessage(priority=5, content="first", timestamp=earlier_time)
        msg2 = MailboxMessage(priority=5, content="second", timestamp=later_time)

        assert msg1 < msg2  # earlier timestamp is "less than"

    def test_id_can_be_empty(self):
        """id field can be empty string."""
        msg = MailboxMessage(priority=0, content="test", id="")
        assert msg.id == ""

    def test_content_can_be_any_type(self):
        """content can be any type (dict, list, object, etc)."""
        msg_dict = MailboxMessage(priority=0, content={"key": "value"})
        msg_list = MailboxMessage(priority=0, content=[1, 2, 3])
        msg_none = MailboxMessage(priority=0, content=None)

        assert msg_dict.content == {"key": "value"}
        assert msg_list.content == [1, 2, 3]
        assert msg_none.content is None


class TestMailbox:
    def test_enqueue_dequeue_basic(self):
        """enqueue() and dequeue() work for basic operation."""
        mailbox = Mailbox(max_size=100)
        assert mailbox.is_empty

        mailbox.enqueue("hello", priority=0)
        assert not mailbox.is_empty
        assert mailbox.size() == 1

        msg = mailbox.dequeue()
        assert msg.content == "hello"
        assert mailbox.is_empty

    def test_priority_ordering_lower_number_dequeued_first(self):
        """Lower priority number is dequeued first."""
        mailbox = Mailbox(max_size=100)

        mailbox.enqueue("low priority", priority=10)
        mailbox.enqueue("high priority", priority=1)
        mailbox.enqueue("medium priority", priority=5)

        # Highest priority (lowest number) should come out first
        msg1 = mailbox.dequeue()
        msg2 = mailbox.dequeue()
        msg3 = mailbox.dequeue()

        assert msg1.content == "high priority"
        assert msg1.priority == 1
        assert msg2.content == "medium priority"
        assert msg2.priority == 5
        assert msg3.content == "low priority"
        assert msg3.priority == 10

    def test_dequeue_timeout_returns_none(self):
        """dequeue(timeout) returns None when timeout expires."""
        mailbox = Mailbox(max_size=100)
        start = time.time()
        result = mailbox.dequeue(timeout=0.1)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.1

    def test_dequeue_blocks_until_available(self):
        """dequeue() blocks until a message is available."""
        mailbox = Mailbox(max_size=100)

        def delayed_enqueue():
            time.sleep(0.1)
            mailbox.enqueue("delayed message", priority=0)

        thread = threading.Thread(target=delayed_enqueue)
        start = time.time()
        thread.start()

        msg = mailbox.dequeue(timeout=1.0)
        elapsed = time.time() - start

        thread.join()
        assert msg.content == "delayed message"
        assert elapsed >= 0.1

    def test_max_size_enqueue_returns_false_when_full(self):
        """enqueue() returns False when max_size is reached."""
        mailbox = Mailbox(max_size=3)

        assert mailbox.enqueue("msg1", priority=1) is True
        assert mailbox.enqueue("msg2", priority=2) is True
        assert mailbox.enqueue("msg3", priority=3) is True
        assert mailbox.is_full

        # Next enqueue should fail
        assert mailbox.enqueue("msg4", priority=4) is False

    def test_memory_bounded_after_max_size(self):
        """After max_size, subsequent enqueue returns False."""
        mailbox = Mailbox(max_size=5)

        for i in range(5):
            assert mailbox.enqueue(f"msg{i}", priority=i) is True

        assert mailbox.is_full
        assert mailbox.enqueue("overflow", priority=10) is False
        assert mailbox.size() == 5  # Size unchanged

    def test_fifo_for_same_priority(self):
        """FIFO ordering for same priority messages."""
        mailbox = Mailbox(max_size=100)

        mailbox.enqueue("first", priority=5)
        mailbox.enqueue("second", priority=5)
        mailbox.enqueue("third", priority=5)

        msg1 = mailbox.dequeue()
        msg2 = mailbox.dequeue()
        msg3 = mailbox.dequeue()

        assert msg1.content == "first"
        assert msg2.content == "second"
        assert msg3.content == "third"

    def test_empty_mailbox_dequeue_waits(self):
        """dequeue() on empty mailbox waits for timeout."""
        mailbox = Mailbox(max_size=100)
        start = time.time()
        result = mailbox.dequeue(timeout=0.2)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.2

    def test_close_wakes_waiters(self):
        """close() wakes all waiting dequeue threads."""
        mailbox = Mailbox(max_size=100)
        barrier = threading.Barrier(2)
        results = []

        def wait_for_message():
            barrier.wait()
            msg = mailbox.dequeue(timeout=1.0)
            results.append(msg)

        thread = threading.Thread(target=wait_for_message)
        thread.start()
        barrier.wait()

        time.sleep(0.05)  # Let thread start waiting
        mailbox.close()
        thread.join()

        assert results[0] is None  # close() causes dequeue to return None

    def test_size_reflects_queue_length(self):
        """size() returns the current number of messages."""
        mailbox = Mailbox(max_size=100)

        assert mailbox.size() == 0
        mailbox.enqueue("a", priority=1)
        assert mailbox.size() == 1
        mailbox.enqueue("b", priority=2)
        assert mailbox.size() == 2
        mailbox.dequeue()
        assert mailbox.size() == 1

    def test_is_empty_property(self):
        """is_empty returns True when no messages."""
        mailbox = Mailbox(max_size=100)
        assert mailbox.is_empty

        mailbox.enqueue("test", priority=0)
        assert not mailbox.is_empty

        mailbox.dequeue()
        assert mailbox.is_empty

    def test_is_full_property(self):
        """is_full returns True when at max capacity."""
        mailbox = Mailbox(max_size=2)
        assert not mailbox.is_full

        mailbox.enqueue("a", priority=1)
        assert not mailbox.is_full
        mailbox.enqueue("b", priority=2)
        assert mailbox.is_full

    def test_max_size_property(self):
        """max_size property returns the configured max size."""
        mailbox = Mailbox(max_size=500)
        assert mailbox.max_size == 500

        small_mailbox = Mailbox(max_size=10)
        assert small_mailbox.max_size == 10


class TestMailboxThreadSafety:
    def test_concurrent_enqueue(self):
        """Concurrent enqueue() from multiple threads is safe."""
        mailbox = Mailbox(max_size=10000)
        barrier = threading.Barrier(10)

        def enqueue_messages():
            barrier.wait()
            for i in range(100):
                mailbox.enqueue(f"msg-{threading.get_ident()}-{i}", priority=i % 10)

        threads = [threading.Thread(target=enqueue_messages) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert mailbox.size() == 1000

    def test_concurrent_dequeue(self):
        """Concurrent dequeue() from multiple threads is safe."""
        mailbox = Mailbox(max_size=100)

        # Fill the mailbox
        for i in range(50):
            mailbox.enqueue(f"msg{i}", priority=i % 10)

        results = []
        barrier = threading.Barrier(5)

        def dequeue_messages():
            barrier.wait()
            local_results = []
            for _ in range(10):
                msg = mailbox.dequeue(timeout=1.0)
                if msg:
                    local_results.append(msg)
            results.extend(local_results)

        threads = [threading.Thread(target=dequeue_messages) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All messages should have been dequeued (50 total)
        assert len(results) == 50

    def test_concurrent_enqueue_dequeue(self):
        """Concurrent enqueue and dequeue are safe."""
        mailbox = Mailbox(max_size=1000)
        produced = []
        consumed = []
        count = 100

        def producer():
            for i in range(count):
                msg = f"msg-{i}"
                mailbox.enqueue(msg, priority=i % 10)
                produced.append(msg)
                time.sleep(0.001)

        def consumer():
            local_consumed = []
            for _ in range(count):
                msg = mailbox.dequeue(timeout=1.0)
                if msg:
                    local_consumed.append(msg.content)
                time.sleep(0.001)
            consumed.extend(local_consumed)

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)

        producer_thread.start()
        time.sleep(0.05)  # Let producer get ahead
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()

        assert len(consumed) == count
        assert set(consumed) == set(produced)


class TestMailboxClear:
    def test_clear_removes_all_messages(self):
        """clear() removes all messages from the queue."""
        mailbox = Mailbox(max_size=100)

        mailbox.enqueue("a", priority=1)
        mailbox.enqueue("b", priority=2)
        mailbox.enqueue("c", priority=3)

        assert mailbox.size() == 3
        mailbox.clear()
        assert mailbox.size() == 0
        assert mailbox.is_empty

    def test_clear_while_waiting_dequeue(self):
        """clear() wakes waiting dequeue threads."""
        mailbox = Mailbox(max_size=100)
        barrier = threading.Barrier(2)
        results = []

        def wait_dequeue():
            barrier.wait()
            msg = mailbox.dequeue(timeout=1.0)
            results.append(msg)

        thread = threading.Thread(target=wait_dequeue)
        thread.start()
        barrier.wait()

        time.sleep(0.05)
        mailbox.clear()
        thread.join()

        assert results[0] is None
