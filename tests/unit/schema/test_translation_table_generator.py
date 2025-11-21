import pytest

from core.ast_models import EntityDefinition, FieldDefinition, TranslationConfig
from generators.schema.translation_table_generator import TranslationTableGenerator


def test_generate_translation_table_basic():
    """Generate basic translation table DDL"""
    entity = EntityDefinition(
        name="Manufacturer",
        schema="catalog",
        fields={
            "code": FieldDefinition(name="code", type_name="text"),
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
        },
        translations=TranslationConfig(enabled=True, fields=["name"]),
    )

    generator = TranslationTableGenerator()
    ddl = generator.generate(entity)

    assert "CREATE TABLE catalog.tl_manufacturer" in ddl
    # Hybrid Trinity pattern (2 fields: pk + id, no identifier)
    assert "pk_manufacturer_translation INTEGER PRIMARY KEY" in ddl
    assert "id UUID UNIQUE NOT NULL" in ddl
    # Should NOT have identifier field
    assert "identifier TEXT" not in ddl
    # Foreign keys
    assert "fk_manufacturer UUID" in ddl
    assert "fk_locale UUID" in ddl
    # Translatable fields
    assert "name TEXT NOT NULL" in ddl
    # Unique constraint
    assert "CONSTRAINT tl_manufacturer_uniq UNIQUE (fk_manufacturer, fk_locale)" in ddl


def test_generate_translation_table_nullable_fields():
    """Generate translation table with nullable fields"""
    entity = EntityDefinition(
        name="Manufacturer",
        schema="catalog",
        fields={
            "code": FieldDefinition(name="code", type_name="text"),
            "name": FieldDefinition(name="name", type_name="text", nullable=True),
            "description": FieldDefinition(name="description", type_name="text", nullable=False),
        },
        translations=TranslationConfig(enabled=True, fields=["name", "description"]),
    )

    generator = TranslationTableGenerator()
    ddl = generator.generate(entity)

    # Nullable field should be NULL
    assert "name TEXT NULL" in ddl
    # Non-nullable field should be NOT NULL
    assert "description TEXT NOT NULL" in ddl


def test_generate_translation_table_custom_table_name():
    """Generate translation table with custom table name"""
    entity = EntityDefinition(
        name="Manufacturer",
        schema="catalog",
        fields={
            "name": FieldDefinition(name="name", type_name="text"),
        },
        translations=TranslationConfig(
            enabled=True, table_name="custom_translations", fields=["name"]
        ),
    )

    generator = TranslationTableGenerator()
    ddl = generator.generate(entity)

    assert "CREATE TABLE catalog.custom_translations" in ddl
    assert "CONSTRAINT custom_translations_uniq UNIQUE" in ddl


def test_generate_translation_table_validation_errors():
    """Test validation errors for translation table generation"""
    generator = TranslationTableGenerator()

    # Test missing field
    entity_missing = EntityDefinition(
        name="Test",
        schema="catalog",
        fields={"code": FieldDefinition(name="code", type_name="text")},
        translations=TranslationConfig(enabled=True, fields=["missing_field"]),
    )

    with pytest.raises(ValueError, match="missing fields: \\['missing_field'\\]"):
        generator.generate(entity_missing)

    # Test non-text field
    entity_non_text = EntityDefinition(
        name="Test",
        schema="catalog",
        fields={"count": FieldDefinition(name="count", type_name="integer")},
        translations=TranslationConfig(enabled=True, fields=["count"]),
    )

    with pytest.raises(ValueError, match="non-text fields: \\['count \\(integer\\)'\\]"):
        generator.generate(entity_non_text)
