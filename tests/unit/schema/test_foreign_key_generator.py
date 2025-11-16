import pytest

from src.core.ast_models import FieldDefinition, FieldTier
from src.generators.schema.foreign_key_generator import (
    ForeignKeyDDL,
    ForeignKeyGenerator,
)


def test_map_reference_field():
    """Test mapping a reference field to foreign key DDL"""
    field = FieldDefinition(
        name="company",
        type_name="ref",
        nullable=False,
        tier=FieldTier.REFERENCE,
        reference_entity="Company",
        reference_schema="crm",
    )

    generator = ForeignKeyGenerator()
    fk_ddl = generator.map_field(field)

    assert fk_ddl.column_name == "fk_company"
    assert fk_ddl.postgres_type == "INTEGER"
    assert fk_ddl.nullable is False
    assert fk_ddl.references_schema == "crm"
    assert fk_ddl.references_table == "tb_company"
    assert fk_ddl.references_column == "pk_company"
    assert fk_ddl.on_delete == "RESTRICT"
    assert fk_ddl.on_update == "CASCADE"
    assert fk_ddl.comment == "Reference to Company"


def test_map_reference_field_default_schema():
    """Test mapping reference field with default schema"""
    field = FieldDefinition(
        name="organization",
        type_name="ref",
        nullable=True,
        tier=FieldTier.REFERENCE,
        reference_entity="Organization",
        # No reference_schema specified
    )

    generator = ForeignKeyGenerator()
    fk_ddl = generator.map_field(field)

    assert fk_ddl.references_schema == "public"


def test_map_non_reference_field_raises_error():
    """Test that mapping non-reference field raises error"""
    field = FieldDefinition(
        name="email", type_name="email", nullable=False, tier=FieldTier.SCALAR
    )

    generator = ForeignKeyGenerator()
    with pytest.raises(ValueError, match="not a reference type"):
        generator.map_field(field)


def test_generate_field_ddl_not_nullable():
    """Test field DDL generation for non-nullable FK"""
    fk_ddl = ForeignKeyDDL(
        column_name="fk_company",
        postgres_type="INTEGER",
        nullable=False,
        references_schema="crm",
        references_table="tb_company",
        references_column="pk_company",
        on_delete="RESTRICT",
        on_update="CASCADE",
    )

    generator = ForeignKeyGenerator()
    field_ddl = generator.generate_field_ddl(fk_ddl)

    expected = (
        "fk_company INTEGER NOT NULL "
        "REFERENCES crm.tb_company(pk_company) "
        "ON DELETE RESTRICT ON UPDATE CASCADE"
    )
    assert field_ddl == expected


def test_generate_field_ddl_nullable():
    """Test field DDL generation for nullable FK"""
    fk_ddl = ForeignKeyDDL(
        column_name="fk_manager",
        postgres_type="INTEGER",
        nullable=True,
        references_schema="crm",
        references_table="tb_user",
        references_column="pk_user",
        on_delete="SET NULL",
        on_update="CASCADE",
    )

    generator = ForeignKeyGenerator()
    field_ddl = generator.generate_field_ddl(fk_ddl)

    expected = "fk_manager INTEGER REFERENCES crm.tb_user(pk_user) ON DELETE SET NULL ON UPDATE CASCADE"
    assert field_ddl == expected


def test_generate_index():
    """Test B-tree index generation for FK column"""
    fk_ddl = ForeignKeyDDL(column_name="fk_company", references_table="tb_company")

    generator = ForeignKeyGenerator()
    index_sql = generator.generate_index("crm", "tb_contact", fk_ddl)

    expected = """CREATE INDEX idx_contact_company
    ON crm.tb_contact (fk_company)
    WHERE deleted_at IS NULL;"""
    assert index_sql == expected


def test_generate_index_with_complex_names():
    """Test index generation with complex entity/field names"""
    fk_ddl = ForeignKeyDDL(
        column_name="fk_organization_unit", references_table="tb_organization_unit"
    )

    generator = ForeignKeyGenerator()
    index_sql = generator.generate_index("auth", "tb_user", fk_ddl)

    expected = """CREATE INDEX idx_user_organization_unit
    ON auth.tb_user (fk_organization_unit)
    WHERE deleted_at IS NULL;"""
    assert index_sql == expected
