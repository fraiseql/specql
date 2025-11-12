"""Tests for service registry parsing and validation."""

from src.registry.service_registry import ServiceRegistry


def test_parse_service_registry():
    """Parse service registry YAML"""
    registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
    assert len(registry.services) > 0
    assert registry.get_service("sendgrid") is not None


def test_validate_operation_exists():
    """Validate service operation exists"""
    registry = ServiceRegistry.from_yaml("registry/service_registry.yaml")
    service = registry.get_service("sendgrid")
    assert service.has_operation("send_email")
