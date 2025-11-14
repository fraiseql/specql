"""
Tests for Rust model struct generation

Tests the generation of Queryable, Insertable, and AsChangeset structs.
"""

import pytest
from src.generators.rust.model_generator import RustModelGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestQueryableStructGeneration:
    """Test generation of Diesel Queryable structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
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

    def test_generate_queryable_struct_declaration(self, generator, simple_entity):
        """Test basic struct declaration with derives"""
        result = generator.generate_queryable_struct(simple_entity)

        # Struct declaration
        assert "#[derive(Debug, Clone, Queryable, Selectable)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct Contact {" in result

    def test_queryable_includes_primary_key(self, generator, simple_entity):
        """Test primary key field is included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub pk_contact: i32," in result

    def test_queryable_includes_uuid_id(self, generator, simple_entity):
        """Test UUID id field is included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub id: Uuid," in result

    def test_queryable_includes_user_fields(self, generator, simple_entity):
        """Test user-defined fields are included with correct types"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub email: String," in result
        assert "pub phone: Option<String>," in result  # Optional field
        assert "pub active: bool," in result

    def test_queryable_includes_audit_fields(self, generator, simple_entity):
        """Test Trinity audit fields are included"""
        result = generator.generate_queryable_struct(simple_entity)

        assert "pub created_at: NaiveDateTime," in result
        assert "pub created_by: Option<Uuid>," in result
        assert "pub updated_at: NaiveDateTime," in result
        assert "pub updated_by: Option<Uuid>," in result
        assert "pub deleted_at: Option<NaiveDateTime>," in result
        assert "pub deleted_by: Option<Uuid>," in result

    def test_queryable_field_ordering(self, generator, simple_entity):
        """Test fields are in correct order"""
        result = generator.generate_queryable_struct(simple_entity)

        # Extract field lines (exclude struct declaration)
        lines = [
            line.strip()
            for line in result.split("\n")
            if line.strip().startswith("pub ") and ":" in line
        ]

        # Expected order: pk, id, user fields, audit fields
        assert lines[0].startswith("pub pk_contact")
        assert lines[1].startswith("pub id")
        assert lines[-1].startswith("pub deleted_by")

    def test_queryable_with_foreign_key(self, generator):
        """Test foreign key field generation"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=True,
                ),
            },
        )

        result = generator.generate_queryable_struct(entity)

        # Foreign keys are i32 (or Option<i32>)
        assert "pub fk_company: Option<i32>," in result

    def test_queryable_with_enum_field(self, generator):
        """Test enum field becomes String"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "status": FieldDefinition(
                    name="status",
                    type_name="enum",
                    values=["lead", "qualified"],
                    nullable=False,
                ),
            },
        )

        result = generator.generate_queryable_struct(entity)

        # Enums stored as String
        assert "pub status: String," in result

    def test_queryable_with_integer_subtypes(self, generator):
        """Test integer subtypes map to correct Rust types"""
        entity = Entity(
            name="Stats",
            schema="analytics",
            fields={
                "small_count": FieldDefinition(
                    name="small_count", type_name="integer:small", nullable=False
                ),
                "regular_count": FieldDefinition(
                    name="regular_count", type_name="integer", nullable=False
                ),
                "big_count": FieldDefinition(
                    name="big_count", type_name="integer:big", nullable=False
                ),
            },
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub small_count: i16," in result
        assert "pub regular_count: i32," in result
        assert "pub big_count: i64," in result

    def test_queryable_with_decimal_field(self, generator):
        """Test decimal fields use BigDecimal"""
        entity = Entity(
            name="Product",
            schema="sales",
            fields={
                "price": FieldDefinition(
                    name="price", type_name="decimal:money", nullable=False
                ),
            },
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub price: BigDecimal," in result

    def test_queryable_with_json_field(self, generator):
        """Test JSON fields use serde_json::Value"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "metadata": FieldDefinition(
                    name="metadata", type_name="json", nullable=True
                ),
            },
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub metadata: Option<serde_json::Value>," in result

    def test_queryable_with_array_field(self, generator):
        """Test array fields use Vec<T>"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "tags": FieldDefinition(name="tags", type_name="text[]", nullable=True),
            },
        )

        result = generator.generate_queryable_struct(entity)

        assert "pub tags: Option<Vec<String>>," in result

    def test_queryable_imports(self, generator, simple_entity):
        """Test required imports are included"""
        result = generator.generate_queryable_struct(
            simple_entity, include_imports=True
        )

        assert "use diesel::prelude::*;" in result
        assert "use uuid::Uuid;" in result
        assert "use chrono::NaiveDateTime;" in result
        assert "use super::schema::crm::tb_contact;" in result

    def test_queryable_documentation(self, generator, simple_entity):
        """Test documentation comment is generated"""
        simple_entity.description = "Represents a contact in the CRM"
        result = generator.generate_queryable_struct(simple_entity)

        assert "/// Represents a contact in the CRM" in result
        assert "/// Queryable struct for tb_contact table" in result


class TestInsertableStructGeneration:
    """Test generation of Diesel Insertable structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "phone": FieldDefinition(name="phone", type_name="text", nullable=True),
            },
        )

    def test_generate_insertable_struct_declaration(self, generator, simple_entity):
        """Test basic Insertable struct declaration"""
        result = generator.generate_insertable_struct(simple_entity)

        assert "#[derive(Debug, Insertable)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct NewContact {" in result

    def test_insertable_excludes_generated_fields(self, generator, simple_entity):
        """Test Insertable excludes auto-generated fields"""
        result = generator.generate_insertable_struct(simple_entity)

        # Should NOT include:
        assert "pk_contact" not in result  # Auto-generated
        assert "id:" not in result or "id: Uuid," not in result  # Auto-generated UUID
        assert "created_at:" not in result  # Auto-generated timestamp
        assert "updated_at:" not in result  # Auto-generated timestamp
        assert "deleted_at:" not in result  # For soft delete, not insert

    def test_insertable_includes_user_fields(self, generator, simple_entity):
        """Test Insertable includes user-defined fields"""
        result = generator.generate_insertable_struct(simple_entity)

        assert "pub email: String," in result
        assert "pub phone: Option<String>," in result

    def test_insertable_includes_creator_fields(self, generator, simple_entity):
        """Test Insertable includes created_by and updated_by"""
        result = generator.generate_insertable_struct(simple_entity)

        # User who created/updated (not timestamps)
        assert "pub created_by: Option<Uuid>," in result
        assert "pub updated_by: Option<Uuid>," in result

    def test_insertable_with_required_foreign_key(self, generator):
        """Test required foreign key in Insertable"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=False,  # Required FK
                ),
            },
        )

        result = generator.generate_insertable_struct(entity)

        # Required FK is not Option
        assert "pub fk_company: i32," in result

    def test_insertable_with_optional_foreign_key(self, generator):
        """Test optional foreign key in Insertable"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=True,  # Optional FK
                ),
            },
        )

        result = generator.generate_insertable_struct(entity)

        # Optional FK is Option
        assert "pub fk_company: Option<i32>," in result

    def test_insertable_with_default_values(self, generator):
        """Test fields with defaults are still included"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "active": FieldDefinition(
                    name="active", type_name="boolean", nullable=False, default="true"
                ),
            },
        )

        result = generator.generate_insertable_struct(entity)

        # Field still included (defaults handled at DB level)
        assert "pub active: bool," in result

    def test_insertable_derives_serialization(self, generator, simple_entity):
        """Test Insertable can optionally derive Serialize/Deserialize"""
        result = generator.generate_insertable_struct(simple_entity, with_serde=True)

        assert "#[derive(Debug, Insertable, Serialize, Deserialize)]" in result

    def test_insertable_validation_attributes(self, generator):
        """Test validation attributes for required fields"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email",
                    type_name="text",
                    nullable=False,
                    validation_pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                ),
            },
        )

        result = generator.generate_insertable_struct(entity)

        # Validation via custom trait (future enhancement)
        # For now, just ensure field is correct type
        assert "pub email: String," in result


class TestAsChangesetStructGeneration:
    """Test generation of Diesel AsChangeset structs"""

    @pytest.fixture
    def generator(self):
        return RustModelGenerator()

    @pytest.fixture
    def simple_entity(self):
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

    def test_generate_as_changeset_struct_declaration(self, generator, simple_entity):
        """Test basic AsChangeset struct declaration"""
        result = generator.generate_as_changeset_struct(simple_entity)

        assert "#[derive(Debug, AsChangeset)]" in result
        assert "#[diesel(table_name = tb_contact)]" in result
        assert "pub struct UpdateContact {" in result

    def test_as_changeset_excludes_immutable_fields(self, generator, simple_entity):
        """Test AsChangeset excludes immutable fields"""
        result = generator.generate_as_changeset_struct(simple_entity)

        # Should NOT include:
        assert "pk_contact" not in result  # Primary key (immutable)
        assert "id:" not in result or "id: Uuid," not in result  # UUID (immutable)
        assert "created_at:" not in result  # Creation timestamp (immutable)
        assert "created_by:" not in result  # Creator (immutable)

    def test_as_changeset_includes_updatable_fields(self, generator, simple_entity):
        """Test AsChangeset includes fields that can be updated"""
        result = generator.generate_as_changeset_struct(simple_entity)

        # Should include updatable user fields
        assert "pub email: Option<String>," in result
        assert "pub phone: Option<String>," in result  # Optional field becomes Option
        assert "pub active: Option<bool>," in result

    def test_as_changeset_includes_update_tracking(self, generator, simple_entity):
        """Test AsChangeset includes update tracking fields"""
        result = generator.generate_as_changeset_struct(simple_entity)

        # Required update tracking
        assert "pub updated_at: NaiveDateTime," in result
        assert "pub updated_by: Option<Uuid>," in result

    def test_as_changeset_with_foreign_key(self, generator):
        """Test foreign key in AsChangeset"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=True,
                ),
            },
        )

        result = generator.generate_as_changeset_struct(entity)

        # Foreign keys are optional in updates
        assert "pub fk_company: Option<i32>," in result

    def test_as_changeset_with_required_foreign_key(self, generator):
        """Test required foreign key in AsChangeset"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=False,  # Required FK
                ),
            },
        )

        result = generator.generate_as_changeset_struct(entity)

        # Even required FKs are Option in updates (can be set to None to not update)
        assert "pub fk_company: Option<i32>," in result

    def test_as_changeset_with_enum_field(self, generator):
        """Test enum field in AsChangeset"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "status": FieldDefinition(
                    name="status",
                    type_name="enum",
                    values=["lead", "qualified"],
                    nullable=False,
                ),
            },
        )

        result = generator.generate_as_changeset_struct(entity)

        # Enums become Option<String> in updates
        assert "pub status: Option<String>," in result

    def test_as_changeset_with_array_field(self, generator):
        """Test array field in AsChangeset"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "tags": FieldDefinition(name="tags", type_name="text[]", nullable=True),
            },
        )

        result = generator.generate_as_changeset_struct(entity)

        # Arrays become Option<Vec<T>> in updates
        assert "pub tags: Option<Vec<String>>," in result

    def test_as_changeset_soft_delete_support(self, generator, simple_entity):
        """Test AsChangeset can include soft delete fields"""
        result = generator.generate_as_changeset_struct(
            simple_entity, include_soft_delete=True
        )

        # Soft delete fields
        assert "pub deleted_at: Option<NaiveDateTime>," in result
        assert "pub deleted_by: Option<Uuid>," in result

    def test_as_changeset_documentation(self, generator, simple_entity):
        """Test documentation comment is generated"""
        result = generator.generate_as_changeset_struct(simple_entity)

        assert "/// AsChangeset struct for tb_contact table" in result
        assert "/// Used for UPDATE operations" in result
