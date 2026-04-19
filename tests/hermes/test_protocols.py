"""Tests for protocol interfaces (IAgent, IToolRegistry, IMemoryProvider, IEventBus)."""
from abc import ABC

import pytest

from agent.protocols import IAgent, IToolRegistry, IMemoryProvider, IEventBus


class TestIAgentIsABC:
    """IAgent is an abstract base class."""

    def test_is_abc(self):
        """IAgent should be an ABC."""
        assert issubclass(IAgent, ABC)

    def test_has_run_conversation_abstractmethod(self):
        """IAgent has run_conversation as an abstractmethod."""
        assert hasattr(IAgent, "run_conversation")
        # Check it's abstract
        assert IAgent.run_conversation.__isabstractmethod__ is True

    def test_has_get_session_id_abstractmethod(self):
        """IAgent has get_session_id as an abstractmethod."""
        assert hasattr(IAgent, "get_session_id")
        assert IAgent.get_session_id.__isabstractmethod__ is True

    def test_cannot_instantiate_directly(self):
        """IAgent cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            IAgent()


class TestIToolRegistryIsABC:
    """IToolRegistry is an abstract base class."""

    def test_is_abc(self):
        """IToolRegistry should be an ABC."""
        assert issubclass(IToolRegistry, ABC)

    def test_has_register_abstractmethod(self):
        """IToolRegistry has register as an abstractmethod."""
        assert hasattr(IToolRegistry, "register")
        assert IToolRegistry.register.__isabstractmethod__ is True

    def test_has_get_definitions_abstractmethod(self):
        """IToolRegistry has get_definitions as an abstractmethod."""
        assert hasattr(IToolRegistry, "get_definitions")
        assert IToolRegistry.get_definitions.__isabstractmethod__ is True

    def test_has_dispatch_abstractmethod(self):
        """IToolRegistry has dispatch as an abstractmethod."""
        assert hasattr(IToolRegistry, "dispatch")
        assert IToolRegistry.dispatch.__isabstractmethod__ is True

    def test_cannot_instantiate_directly(self):
        """IToolRegistry cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            IToolRegistry()


class TestIMemoryProviderIsABC:
    """IMemoryProvider is an abstract base class."""

    def test_is_abc(self):
        """IMemoryProvider should be an ABC."""
        assert issubclass(IMemoryProvider, ABC)

    def test_has_name_abstractmethod(self):
        """IMemoryProvider has name as an abstract property."""
        assert hasattr(IMemoryProvider, "name")
        # It's a property, check it's abstract
        assert getattr(IMemoryProvider.name, "__isabstractmethod__", False) is True

    def test_has_is_available_abstractmethod(self):
        """IMemoryProvider has is_available as an abstractmethod."""
        assert hasattr(IMemoryProvider, "is_available")
        assert IMemoryProvider.is_available.__isabstractmethod__ is True

    def test_has_initialize_abstractmethod(self):
        """IMemoryProvider has initialize as an abstractmethod."""
        assert hasattr(IMemoryProvider, "initialize")
        assert IMemoryProvider.initialize.__isabstractmethod__ is True

    def test_has_get_tool_schemas_abstractmethod(self):
        """IMemoryProvider has get_tool_schemas as an abstractmethod."""
        assert hasattr(IMemoryProvider, "get_tool_schemas")
        assert IMemoryProvider.get_tool_schemas.__isabstractmethod__ is True

    def test_has_default_hooks(self):
        """IMemoryProvider has optional hook methods with defaults."""
        # These should exist but not be abstract
        assert hasattr(IMemoryProvider, "system_prompt_block")
        assert hasattr(IMemoryProvider, "prefetch")
        assert hasattr(IMemoryProvider, "queue_prefetch")
        assert hasattr(IMemoryProvider, "sync_turn")
        assert hasattr(IMemoryProvider, "handle_tool_call")
        assert hasattr(IMemoryProvider, "shutdown")
        assert hasattr(IMemoryProvider, "on_turn_start")
        assert hasattr(IMemoryProvider, "on_session_end")

    def test_cannot_instantiate_directly(self):
        """IMemoryProvider cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            IMemoryProvider()


class TestIEventBusIsABC:
    """IEventBus is an abstract base class."""

    def test_is_abc(self):
        """IEventBus should be an ABC."""
        assert issubclass(IEventBus, ABC)

    def test_has_subscribe_abstractmethod(self):
        """IEventBus has subscribe as an abstractmethod."""
        assert hasattr(IEventBus, "subscribe")
        assert IEventBus.subscribe.__isabstractmethod__ is True

    def test_has_emit_abstractmethod(self):
        """IEventBus has emit as an abstractmethod."""
        assert hasattr(IEventBus, "emit")
        assert IEventBus.emit.__isabstractmethod__ is True

    def test_cannot_instantiate_directly(self):
        """IEventBus cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            IEventBus()


class TestConcreteClassesSatisfyProtocols:
    """Concrete classes can satisfy protocols via duck typing."""

    def test_concrete_agent_satisfies_iaagent(self):
        """A concrete class with run_conversation and get_session_id satisfies IAgent."""
        from agent.protocols import IAgent

        class ConcreteAgent:
            def run_conversation(self, message, **kwargs):
                return "response"

            def get_session_id(self):
                return "session-123"

        agent = ConcreteAgent()
        # Duck typing: has required methods
        assert hasattr(agent, "run_conversation")
        assert hasattr(agent, "get_session_id")
        assert callable(agent.run_conversation)
        assert callable(agent.get_session_id)

    def test_concrete_registry_satisfies_itoolregistry(self):
        """A concrete class with register, get_definitions, dispatch satisfies IToolRegistry."""
        from agent.protocols import IToolRegistry

        class ConcreteRegistry:
            def register(self, name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, description="", emoji=""):
                pass

            def get_definitions(self, tool_names, quiet=False):
                return []

            def dispatch(self, name, args, **kwargs):
                return "{}"

        registry = ConcreteRegistry()
        assert hasattr(registry, "register")
        assert hasattr(registry, "get_definitions")
        assert hasattr(registry, "dispatch")

    def test_concrete_memory_satisfies_imemoryprovider(self):
        """A concrete class with required IMemoryProvider methods satisfies the protocol."""
        from agent.protocols import IMemoryProvider

        class ConcreteMemoryProvider:
            @property
            def name(self):
                return "test"

            def is_available(self):
                return True

            def initialize(self, session_id, **kwargs):
                pass

            def get_tool_schemas(self):
                return []

        provider = ConcreteMemoryProvider()
        assert hasattr(provider, "name")
        assert hasattr(provider, "is_available")
        assert hasattr(provider, "initialize")
        assert hasattr(provider, "get_tool_schemas")

    def test_concrete_eventbus_satisfifies_ieventbus(self):
        """A concrete class with subscribe and emit satisfies IEventBus."""
        from agent.protocols import IEventBus

        class ConcreteEventBus:
            def subscribe(self, event_type, handler):
                pass

            def emit(self, event):
                pass

        bus = ConcreteEventBus()
        assert hasattr(bus, "subscribe")
        assert hasattr(bus, "emit")
        assert callable(bus.subscribe)
        assert callable(bus.emit)


class TestABCSubclassability:
    """Protocol ABCs can be subclassed."""

    def test_can_subclass_iaagent(self):
        """IAgent can be subclassed."""

        class MyAgent(IAgent):
            def run_conversation(self, message, **kwargs):
                return "response"

            def get_session_id(self):
                return "session-123"

        agent = MyAgent()
        assert isinstance(agent, IAgent)

    def test_can_subclass_itoolregistry(self):
        """IToolRegistry can be subclassed."""

        class MyRegistry(IToolRegistry):
            def register(self, name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, description="", emoji=""):
                pass

            def get_definitions(self, tool_names, quiet=False):
                return []

            def dispatch(self, name, args, **kwargs):
                return "{}"

        registry = MyRegistry()
        assert isinstance(registry, IToolRegistry)

    def test_can_subclass_imemoryprovider(self):
        """IMemoryProvider can be subclassed."""

        class MyMemoryProvider(IMemoryProvider):
            @property
            def name(self):
                return "test"

            def is_available(self):
                return True

            def initialize(self, session_id, **kwargs):
                pass

            def get_tool_schemas(self):
                return []

        provider = MyMemoryProvider()
        assert isinstance(provider, IMemoryProvider)

    def test_can_subclass_ieventbus(self):
        """IEventBus can be subclassed."""

        class MyEventBus(IEventBus):
            def subscribe(self, event_type, handler):
                pass

            def emit(self, event):
                pass

        bus = MyEventBus()
        assert isinstance(bus, IEventBus)
