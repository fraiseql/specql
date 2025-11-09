"""Tests for safety constraint triggers generation."""

import pytest
from src.generators.schema.safety_constraints import (
    generate_safety_constraints,
    generate_circular_reference_check,
    generate_sequence_limit_check,
    generate_depth_limit_check,
)
from src.core.ast_models import EntityDefinition, FieldDefinition, FieldTier


class TestGenerateSafetyConstraints:
    """Test safety constraint generation."""

    def test_hierarchical_entity_gets_all_constraints(self):
        """Test that hierarchical entities get all 3 safety constraints."""
        entity = EntityDefinition(
            name="department",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(
                    name="parent",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="department",
                ),
            },
        )

        result = generate_safety_constraints(entity, "tenant")

        assert len(result) == 3
        # Check that all three constraint types are present
        assert any("prevent_department_cycle" in constraint for constraint in result)
        assert any("check_department_sequence_limit" in constraint for constraint in result)
        assert any("check_department_depth_limit" in constraint for constraint in result)

    def test_non_hierarchical_entity_gets_no_constraints(self):
        """Test that non-hierarchical entities get no safety constraints."""
        entity = EntityDefinition(
            name="contact",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="company",
                ),
            },
        )

        result = generate_safety_constraints(entity, "tenant")

        assert result == []

    def test_catalog_schema_constraints(self):
        """Test constraints for catalog schema."""
        entity = EntityDefinition(
            name="category",
            schema="catalog",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(
                    name="parent",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="category",
                ),
            },
        )

        result = generate_safety_constraints(entity, "catalog")

        assert len(result) == 3
        # Check schema names in generated SQL
        for constraint in result:
            assert "catalog." in constraint


class TestIndividualConstraintFunctions:
    """Test individual constraint generation functions."""

    def test_circular_reference_check(self):
        """Test circular reference prevention trigger generation."""
        entity = EntityDefinition(
            name="location",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(
                    name="parent",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="location",
                ),
            },
        )

        result = generate_circular_reference_check(entity, "tenant")

        assert "CREATE OR REPLACE FUNCTION tenant.prevent_location_cycle" in result
        assert "CREATE TRIGGER trg_prevent_location_cycle" in result
        assert "fk_parent_location" in result
        assert "path <@ NEW.path" in result

    def test_circular_reference_check_non_hierarchical(self):
        """Test that non-hierarchical entities don't get circular reference checks."""
        entity = EntityDefinition(
            name="product",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_circular_reference_check(entity, "tenant")

        assert result == ""

    def test_sequence_limit_check(self):
        """Test identifier sequence limit check trigger generation."""
        entity = EntityDefinition(
            name="item",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_sequence_limit_check(entity, "tenant")

        assert "CREATE OR REPLACE FUNCTION tenant.check_item_sequence_limit" in result
        assert "CREATE TRIGGER trg_check_item_sequence_limit" in result
        assert "v_max_duplicates INTEGER := 100" in result
        assert "sequence_number > v_max_duplicates" in result

    def test_depth_limit_check(self):
        """Test hierarchy depth limit check trigger generation."""
        entity = EntityDefinition(
            name="department",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(
                    name="parent",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="department",
                ),
            },
        )

        result = generate_depth_limit_check(entity, "tenant")

        assert "CREATE OR REPLACE FUNCTION tenant.check_department_depth_limit" in result
        assert "CREATE TRIGGER trg_check_department_depth_limit" in result
        assert "v_max_depth INTEGER := 20" in result
        assert "nlevel(NEW.path)" in result

    def test_depth_limit_check_non_hierarchical(self):
        """Test that non-hierarchical entities don't get depth limit checks."""
        entity = EntityDefinition(
            name="user",
            schema="tenant",
            fields={"name": FieldDefinition(name="name", type_name="string")},
        )

        result = generate_depth_limit_check(entity, "tenant")

        assert result == ""


class TestConstraintIntegration:
    """Test that safety constraints integrate properly with schema generation."""

    def test_explicit_validation_pattern_in_schema_ddl(self):
        """Test that explicit validation pattern replaces safety constraint triggers."""
        from src.generators.schema.schema_generator import SchemaGenerator
        from src.core.ast_models import EntityDefinition, FieldDefinition, FieldTier

        entity = EntityDefinition(
            name="category",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "parent": FieldDefinition(
                    name="parent",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="category",
                ),
            },
        )

        generator = SchemaGenerator()
        ddl = generator.generate_table(entity)

        # Check that explicit validation pattern is used (NO triggers)
        assert "VALIDATION PATTERN: Explicit over Implicit (NO TRIGGERS!)" in ddl
        assert "validate_hierarchy_change" in ddl
        assert "recalculate_tree_path" in ddl
        assert "recalculate_identifier" in ddl

        # Check that old trigger-based constraints are NOT included
        assert "prevent_category_cycle" not in ddl
        assert "check_category_sequence_limit" not in ddl
        assert "check_category_depth_limit" not in ddl
        assert "CREATE TRIGGER" not in ddl

    def test_no_safety_constraints_for_non_hierarchical(self):
        """Test that non-hierarchical entities don't get safety constraints."""
        from src.generators.schema.schema_generator import SchemaGenerator

        entity = EntityDefinition(
            name="product",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="string"),
                "category": FieldDefinition(
                    name="category",
                    type_name="ref",
                    tier=FieldTier.REFERENCE,
                    reference_entity="category",
                ),
            },
        )

        generator = SchemaGenerator()
        ddl = generator.generate_table(entity)

        # Check that no safety constraints are included
        assert "prevent_product_cycle" not in ddl
        assert "check_product_sequence_limit" not in ddl
        assert "check_product_depth_limit" not in ddl
