"""Test SchemaGenerator produces explicit validation pattern."""

from core.ast_models import EntityDefinition, FieldDefinition, FieldTier
from generators.schema.schema_generator import SchemaGenerator


class TestSchemaGeneratorExplicitPattern:
    """Test schema generator uses explicit pattern (no triggers)."""

    def test_no_validation_triggers_generated(self):
        """Should NOT generate validation triggers."""
        entity = EntityDefinition(
            name="Location",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="text", nullable=False),
                "fk_parent_location": FieldDefinition(
                    name="fk_parent_location",
                    type_name="ref",
                    nullable=True,
                    tier=FieldTier.REFERENCE,
                    reference_entity="Location",
                    reference_schema="tenant",
                ),
            },
        )

        generator = SchemaGenerator()
        sql = generator.generate_table(entity)

        # Should NOT contain trigger definitions
        assert "CREATE TRIGGER" not in sql
        assert "prevent_cycle" not in sql
        assert "check_sequence_limit" not in sql
        assert "check_depth_limit" not in sql

    def test_includes_validation_function_references(self):
        """Should reference core validation functions in comments."""
        entity = EntityDefinition(
            name="Location",
            schema="tenant",
            fields={
                "name": FieldDefinition(name="name", type_name="text", nullable=False),
                "fk_parent_location": FieldDefinition(
                    name="fk_parent_location",
                    type_name="ref",
                    nullable=True,
                    tier=FieldTier.REFERENCE,
                    reference_entity="Location",
                    reference_schema="tenant",
                ),
            },
        )

        generator = SchemaGenerator()
        sql = generator.generate_table(entity)

        # Should mention validation functions in comments
        assert "validate_hierarchy_change" in sql
        assert "recalculate_tree_path" in sql
        assert "recalculate_identifier" in sql

    def test_generates_audit_fields(self):
        """Should generate audit fields for recalculation tracking."""
        entity = EntityDefinition(
            name="Location",
            schema="tenant",
            fields={
                "fk_parent_location": FieldDefinition(
                    name="fk_parent_location",
                    type_name="ref",
                    nullable=True,
                    tier=FieldTier.REFERENCE,
                    reference_entity="Location",
                    reference_schema="tenant",
                ),
            },
        )

        generator = SchemaGenerator()
        sql = generator.generate_table(entity)

        # Should include recalculation audit fields
        assert "path_updated_at" in sql
        assert "path_updated_by" in sql
        assert "identifier_recalculated_at" in sql
        assert "identifier_recalculated_by" in sql
