from core.ast_models import EntityDefinition, FieldDefinition, TranslationConfig
from generators.schema.translation_helper_generator import TranslationHelperGenerator


def test_generate_translation_helpers():
    """Generate helper functions for translated fields"""
    entity = EntityDefinition(
        name="Manufacturer",
        schema="catalog",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "description": FieldDefinition(name="description", type_name="text"),
        },
        translations=TranslationConfig(enabled=True, fields=["name", "description"]),
    )

    generator = TranslationHelperGenerator()
    helpers = generator.generate(entity)

    # Should generate 2 helper functions
    assert "CREATE OR REPLACE FUNCTION catalog.get_manufacturer_name" in helpers
    assert "CREATE OR REPLACE FUNCTION catalog.get_manufacturer_description" in helpers
    assert "p_manufacturer_pk UUID" in helpers
    assert "p_locale_pk UUID DEFAULT NULL" in helpers
    assert "COALESCE(p_locale_pk, catalog.get_default_locale())" in helpers
