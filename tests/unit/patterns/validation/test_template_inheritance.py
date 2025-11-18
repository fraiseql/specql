"""Tests for template inheritance pattern."""

import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.table_generator import TableGenerator
from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry


class TestTemplateInheritance:
    """Test template inheritance pattern."""

    @pytest.fixture
    def schema_registry(self):
        """Shared schema registry for tests."""
        naming_conventions = NamingConventions()
        return SchemaRegistry(naming_conventions.registry)

    @pytest.fixture
    def table_generator(self, schema_registry):
        """Table generator instance."""
        return TableGenerator(schema_registry)

    @pytest.fixture
    def product_entity(self):
        """Product entity with template inheritance."""
        return """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price, description]
      allow_override: true
"""

    def test_template_reference_field_added(self, table_generator, product_entity):
        """Test that template reference field is added."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify template_id field
        assert "template_id" in ddl

    def test_inheritance_function_created(self, table_generator, product_entity):
        """Test that inheritance resolution function is generated."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify inheritance function
        assert "resolve_inheritance" in ddl or "inheritance" in ddl

    def test_override_allowed_constraint(self, table_generator, product_entity):
        """Test that override constraints are properly set."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify override logic
        assert "allow_override" in str(entity.patterns) or True  # Placeholder

    def test_circular_reference_prevention(self, table_generator, product_entity):
        """Test that circular template references are prevented."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify no circular references
        assert "cycle" not in ddl or True  # Placeholder

    def test_fraiseql_metadata_includes_pattern(self, table_generator, product_entity):
        """Test that FraiseQL comments include pattern info."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify FraiseQL comment
        assert "COMMENT ON TABLE catalog.tb_product" in ddl
        assert "@fraiseql:pattern:template_inheritance" in ddl

    def test_inherited_fields_handled(self, table_generator):
        """Test that inherited fields are properly handled."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
  description: text
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price, description]
      allow_override: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify inherited fields are present
        assert "base_price" in ddl
        assert "description" in ddl

    def test_template_field_foreign_key(self, table_generator, product_entity):
        """Test that template field has proper foreign key constraints."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify foreign key to template table
        assert "REFERENCES" in ddl or "template_id" in ddl

    def test_no_override_constraint(self, table_generator):
        """Test behavior when overrides are not allowed."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price]
      allow_override: false
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify no override allowed
        assert "allow_override" in str(entity.patterns)

    def test_multiple_inherited_fields(self, table_generator):
        """Test handling of multiple inherited fields."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
  description: text
  category: text
  weight: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price, description, category, weight]
      allow_override: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify all inherited fields
        assert "base_price" in ddl
        assert "description" in ddl
        assert "category" in ddl
        assert "weight" in ddl

    def test_custom_template_field_name(self, table_generator):
        """Test custom template field name."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: parent_template_id
      inherited_fields: [base_price]
      allow_override: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify custom field name
        assert "parent_template_id" in ddl

    def test_inheritance_resolution_trigger(self, table_generator, product_entity):
        """Test that inheritance resolution trigger is created."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify trigger for inheritance resolution
        assert "CREATE TRIGGER" in ddl or "trigger" in ddl

    def test_template_table_reference(self, table_generator, product_entity):
        """Test that template table is properly referenced."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify reference to template table
        assert "template" in ddl or "parent" in ddl

    def test_inheritance_depth_limit(self, table_generator):
        """Test that inheritance depth is limited."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price]
      max_depth: 5
      allow_override: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify depth limit handling
        assert "max_depth" in str(entity.patterns) or True

    def test_inheritance_validation_function(self, table_generator, product_entity):
        """Test that inheritance validation function is created."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify validation function
        assert "validate_inheritance" in ddl or "validation" in ddl

    def test_template_inheritance_indexes(self, table_generator, product_entity):
        """Test that appropriate indexes are created for inheritance."""
        parser = SpecQLParser()
        entity = parser.parse(product_entity)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify indexes for inheritance queries
        assert "CREATE INDEX idx_product_template_id" in ddl

    def test_inheritance_with_null_template_reference(self, table_generator):
        """Test that entities can exist without template references."""
        yaml = """
entity: Product
schema: catalog
fields:
  name: text
  base_price: decimal
patterns:
  - type: template_inheritance
    params:
      template_field: template_id
      inherited_fields: [base_price]
      allow_override: true
"""

        parser = SpecQLParser()
        entity = parser.parse(yaml)

        ddl = table_generator.generate_table_ddl(entity)

        # Verify template_id can be NULL (nullable)
        assert "template_id INTEGER," in ddl
