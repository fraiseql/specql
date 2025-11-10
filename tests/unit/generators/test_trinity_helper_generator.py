"""
Tests for Trinity Helper Generator (Team B)
"""

import pytest

from src.generators.schema.naming_conventions import NamingConventions
from src.generators.schema.schema_registry import SchemaRegistry
from src.generators.trinity_helper_generator import TrinityHelperGenerator
from tests.fixtures.mock_entities import mock_contact_entity


class TestTrinityHelperGenerator:
    """Test Trinity helper function generation"""

    @pytest.fixture
    def generator(self):
        """Create trinity helper generator instance"""
        naming_conventions = NamingConventions()
        schema_registry = SchemaRegistry(naming_conventions.registry)
        return TrinityHelperGenerator(schema_registry)

    def test_trinity_helper_comments(self, generator):
        """Trinity helper functions should have descriptive comments"""
        entity = mock_contact_entity()

        # Test pk function
        pk_sql = generator.generate_entity_pk_function(entity)
        expected_pk_comment = """COMMENT ON FUNCTION crm.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';"""
        assert expected_pk_comment in pk_sql

        # Test id function
        id_sql = generator.generate_entity_id_function(entity)
        expected_id_comment = """COMMENT ON FUNCTION crm.contact_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';"""
        assert expected_id_comment in id_sql
