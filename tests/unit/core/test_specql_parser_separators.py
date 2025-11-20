"""Test SpecQL parser separator configuration."""

from core.separators import Separators
from core.specql_parser import SpecQLParser


class TestParseIdentifierSeparators:
    """Test parsing of separator configuration."""

    def test_default_separators_when_not_specified(self):
        """Should use default separators if not specified."""
        yaml_content = """
entity: Location
hierarchical: true
fields:
  name: text
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Should use defaults (no explicit config)
        assert entity.identifier is None or entity.identifier.separator == Separators.HIERARCHY

    def test_parse_explicit_hierarchy_separator(self):
        """Should parse explicit hierarchy separator override."""
        yaml_content = """
entity: Location
hierarchical: true
identifier:
  separator: "_"  # Override to underscore
fields:
  name: text
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier is not None
        assert entity.identifier.separator == "_"

    def test_parse_composition_separator(self):
        """Should parse composition separator for composite strategy."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  composition_separator: "∘"
  components:
    - field: machine.identifier
      strip_tenant_prefix: true
    - field: location.identifier
      strip_tenant_prefix: true
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier.strategy == "composite_hierarchical"
        assert entity.identifier.composition_separator == "∘"
        assert len(entity.identifier.components) == 2
        assert entity.identifier.components[0].strip_tenant_prefix is True

    def test_parse_strip_tenant_prefix_option(self):
        """Should parse strip_tenant_prefix for components."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  components:
    - field: daterange
      strip_tenant_prefix: false
    - field: machine.identifier
      strip_tenant_prefix: true
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier.components[0].strip_tenant_prefix is False
        assert entity.identifier.components[1].strip_tenant_prefix is True

    def test_default_composition_separator(self):
        """Should default to ring operator for composition separator."""
        yaml_content = """
entity: Allocation
identifier:
  strategy: composite_hierarchical
  components:
    - field: machine.identifier
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        # Default composition separator
        assert (
            entity.identifier.composition_separator == Separators.COMPOSITION
            or entity.identifier.composition_separator is None
        )  # Will use default

    def test_parse_internal_separator(self):
        """Should parse internal separator for intra-entity components."""
        yaml_content = """
entity: NetworkDevice
identifier:
  strategy: internal_components
  internal_separator: "—"
  components:
    - field: router_name
    - field: gateway
    - field: ip_address
"""
        parser = SpecQLParser()
        entity = parser.parse(yaml_content)

        assert entity.identifier.strategy == "internal_components"
        assert entity.identifier.internal_separator == "—"
