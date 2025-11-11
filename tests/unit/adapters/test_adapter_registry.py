# tests/unit/adapters/test_adapter_registry.py
import pytest
from src.adapters.registry import AdapterRegistry
from src.adapters.postgresql_adapter import PostgreSQLAdapter


def test_adapter_registry_can_register_adapter():
    """Registry can register new adapters"""
    registry = AdapterRegistry()

    registry.register(PostgreSQLAdapter)

    assert registry.has_adapter("postgresql")
    assert isinstance(registry.get_adapter("postgresql"), PostgreSQLAdapter)


def test_adapter_registry_lists_available_adapters():
    """Registry can list all available adapters"""
    registry = AdapterRegistry()
    registry.register(PostgreSQLAdapter)

    adapters = registry.list_adapters()

    assert "postgresql" in adapters


def test_adapter_registry_get_adapter_with_config():
    """Registry can create adapters with configuration"""
    registry = AdapterRegistry()

    config = {"some_setting": "value"}
    registry.register(PostgreSQLAdapter)

    adapter = registry.get_adapter("postgresql", config)
    assert isinstance(adapter, PostgreSQLAdapter)
    assert adapter.config == config


def test_adapter_registry_unknown_adapter_raises_error():
    """Registry raises error for unknown adapters"""
    registry = AdapterRegistry()

    with pytest.raises(ValueError, match="Unknown framework: unknown"):
        registry.get_adapter("unknown")


def test_adapter_registry_has_adapter():
    """Registry correctly reports adapter availability"""
    registry = AdapterRegistry()

    assert not registry.has_adapter("postgresql")

    registry.register(PostgreSQLAdapter)
    assert registry.has_adapter("postgresql")


def test_adapter_registry_auto_discover():
    """Registry can auto-discover adapters from the adapters package"""
    registry = AdapterRegistry()

    # Before auto-discovery
    assert not registry.has_adapter("postgresql")

    # Auto-discover adapters
    registry.auto_discover()

    # After auto-discovery
    assert registry.has_adapter("postgresql")
    assert isinstance(registry.get_adapter("postgresql"), PostgreSQLAdapter)
