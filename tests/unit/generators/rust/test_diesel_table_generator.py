"""
Tests for Diesel table! macro generation

The table! macro is Diesel's DSL for defining database tables.
"""

import pytest
from src.generators.rust.diesel_table_generator import DieselTableGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestDieselTableGenerator:
    """Test generation of Diesel table! macros"""

    @pytest.fixture
    def generator(self):
        return DieselTableGenerator()

    @pytest.fixture
    def simple_entity(self):
        """Simple entity with basic fields"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "phone": FieldDefinition(name="phone", type_name="text", nullable=True),
                "active": FieldDefinition(
                    name="active", type_name="boolean", nullable=False
                ),
            },
        )

    @pytest.fixture
    def entity_with_ref(self):
        """Entity with foreign key reference"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    nullable=True,
                    reference_entity="Company",
                ),
            },
        )

    def test_generate_table_macro_structure(self, generator, simple_entity):
        """Test basic table! macro structure"""
        result = generator.generate_table(simple_entity)

        # Assert macro structure
        assert "diesel::table! {" in result
        assert "crm.tb_contact (pk_contact) {" in result
        assert "}" in result

    def test_generate_primary_key(self, generator, simple_entity):
        """Test primary key field generation"""
        result = generator.generate_table(simple_entity)

        # Trinity pattern: pk_{entity_name} -> Int4
        assert "pk_contact -> Int4," in result

    def test_generate_uuid_field(self, generator, simple_entity):
        """Test UUID id field generation"""
        result = generator.generate_table(simple_entity)

        # Trinity pattern: id field
        assert "id -> Uuid," in result

    def test_generate_user_fields(self, generator, simple_entity):
        """Test user-defined fields"""
        result = generator.generate_table(simple_entity)

        assert "email -> Varchar," in result
        assert "phone -> Nullable<Varchar>," in result
        assert "active -> Bool," in result

    def test_generate_audit_fields(self, generator, simple_entity):
        """Test Trinity audit fields"""
        result = generator.generate_table(simple_entity)

        # All 6 audit fields
        assert "created_at -> Timestamptz," in result
        assert "created_by -> Nullable<Uuid>," in result
        assert "updated_at -> Timestamptz," in result
        assert "updated_by -> Nullable<Uuid>," in result
        assert "deleted_at -> Nullable<Timestamptz>," in result
        assert "deleted_by -> Nullable<Uuid>," in result

    def test_generate_foreign_key(self, generator, entity_with_ref):
        """Test foreign key field generation"""
        result = generator.generate_table(entity_with_ref)

        # Ref field becomes fk_*
        assert "fk_company -> Nullable<Int4>," in result

    def test_field_ordering(self, generator, simple_entity):
        """Test fields are in correct order"""
        result = generator.generate_table(simple_entity)
        lines = [line.strip() for line in result.split("\n") if "->" in line]

        # Expected order:
        # 1. pk_* (primary key)
        # 2. id (UUID)
        # 3. User fields
        # 4. Audit fields
        assert lines[0].startswith("pk_contact")
        assert lines[1].startswith("id")
        assert lines[-1].startswith("deleted_by")

    def test_schema_prefix(self, generator, simple_entity):
        """Test table name includes schema prefix"""
        result = generator.generate_table(simple_entity)

        # Schema.table format
        assert "crm.tb_contact" in result

    def test_table_name_convention(self, generator):
        """Test table naming follows tb_ convention"""
        entity = Entity(name="Company", schema="sales", fields={})
        result = generator.generate_table(entity)

        # tb_ prefix + snake_case
        assert "sales.tb_company" in result

    def test_generate_enum_field(self, generator):
        """Test enum field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "status": FieldDefinition(
                    name="status",
                    type_name="enum",
                    nullable=False,
                    values=["lead", "qualified", "customer"],
                ),
            },
        )

        result = generator.generate_table(entity)

        # Enums stored as Varchar in Diesel
        assert "status -> Varchar," in result

    def test_generate_array_field(self, generator):
        """Test array field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "tags": FieldDefinition(name="tags", type_name="text[]", nullable=True),
            },
        )

        result = generator.generate_table(entity)

        assert "tags -> Nullable<Array<Varchar>>," in result

    def test_generate_json_field(self, generator):
        """Test JSON field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "metadata": FieldDefinition(
                    name="metadata", type_name="json", nullable=True
                ),
            },
        )

        result = generator.generate_table(entity)

        assert "metadata -> Nullable<Jsonb>," in result

    def test_multiple_entities_generate_separately(self, generator):
        """Test generating multiple entities"""
        entity1 = Entity(name="Contact", schema="crm", fields={})
        entity2 = Entity(name="Company", schema="crm", fields={})

        result1 = generator.generate_table(entity1)
        result2 = generator.generate_table(entity2)

        assert "tb_contact" in result1
        assert "tb_company" in result2
        assert result1 != result2
