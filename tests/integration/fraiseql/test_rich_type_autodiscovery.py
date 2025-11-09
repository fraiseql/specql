"""
Integration tests for FraiseQL autodiscovery of SpecQL rich types
Tests that PostgreSQL comments → GraphQL descriptions automatically
"""

import pytest

# Mark all tests as requiring database
pytestmark = pytest.mark.database

from src.core.ast_models import Action, Entity
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator


def convert_entity_definition_to_entity(entity_def):
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )  # TODO: Convert impact dict to ActionImpact
        actions.append(action)

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )

    return entity


@pytest.fixture
def test_db_with_rich_types(test_db, isolated_schema):
    """Generate schema with rich types and apply to database"""
    # Parse the entity file
    parser = SpecQLParser()
    specql_content = open("entities/examples/contact_with_rich_types.yaml").read()
    entity_def = parser.parse(specql_content)

    # Convert to Entity
    entity = convert_entity_definition_to_entity(entity_def)

    # Generate migration
    orchestrator = SchemaOrchestrator()
    migration = orchestrator.generate_complete_schema(entity)

    # Replace schema references with isolated schema
    migration = migration.replace("CREATE SCHEMA crm", f"CREATE SCHEMA {isolated_schema}")
    migration = migration.replace("crm.", f"{isolated_schema}.")
    migration = migration.replace("CREATE SCHEMA app", f"CREATE SCHEMA {isolated_schema}")
    migration = migration.replace("app.", f"{isolated_schema}.")
    migration = migration.replace("CREATE SCHEMA catalog", f"CREATE SCHEMA {isolated_schema}")
    migration = migration.replace("catalog.", f"{isolated_schema}.")
    migration = migration.replace("CREATE SCHEMA core", f"CREATE SCHEMA {isolated_schema}")
    migration = migration.replace("core.", f"{isolated_schema}.")
    migration = migration.replace("CREATE SCHEMA management", f"CREATE SCHEMA {isolated_schema}")
    migration = migration.replace("management.", f"{isolated_schema}.")

    cursor = test_db.cursor()
    cursor.execute(migration)
    test_db.commit()

    return test_db, isolated_schema


class TestRichTypeAutodiscovery:
    """Test FraiseQL autodiscovery of rich types from PostgreSQL"""

    def test_email_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: email field has CHECK constraint for validation"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%email%check%'
        """)
        constraint = cursor.fetchone()
        assert constraint is not None
        assert "~*" in constraint[0]  # Regex validation present

    def test_email_field_has_comment(self, test_db_with_rich_types):
        """Test: email field has PostgreSQL comment (becomes GraphQL description)"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT col_description('{schema_name}.tb_contact'::regclass, attnum)
            FROM pg_attribute
            WHERE attrelid = '{schema_name}.tb_contact'::regclass
              AND attname = 'email'
        """)
        comment = cursor.fetchone()
        assert comment is not None
        assert "email" in comment[0].lower()
        assert "validated" in comment[0].lower()

    def test_url_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: url field has CHECK constraint"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%website%check%'
        """)
        constraint = cursor.fetchone()
        assert constraint is not None
        assert "~*" in constraint[0]  # URL regex validation

    def test_phone_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: phoneNumber field has CHECK constraint"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%phone%check%'
        """)
        constraint = cursor.fetchone()
        assert constraint is not None

    def test_money_field_uses_numeric_type(self, test_db_with_rich_types):
        """Test: money field uses NUMERIC(19,4)"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT data_type, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_product'
              AND column_name = 'price'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "numeric"
        assert result[1] == 19
        assert result[2] == 4

    def test_ipaddress_field_uses_inet_type(self, test_db_with_rich_types):
        """Test: ipAddress field uses INET PostgreSQL type"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_device'
              AND column_name = 'ip_address'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "inet"

    def test_coordinates_field_uses_point_type(self, test_db_with_rich_types):
        """Test: coordinates field uses POINT PostgreSQL type"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT udt_name
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_location'
              AND column_name = 'coordinates'
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "point"

    def test_all_rich_type_fields_have_comments(self, test_db_with_rich_types):
        """Test: All rich type fields have descriptive comments"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(f"""
            SELECT
                c.table_schema,
                c.table_name,
                c.column_name,
                col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as comment
            FROM information_schema.columns c
            WHERE c.table_schema = '{schema_name}'
              AND c.column_name IN ('email', 'website', 'phone', 'price', 'ip_address', 'coordinates')
        """)
        results = cursor.fetchall()

        # All rich type fields should have comments
        assert len(results) > 0
        for row in results:
            assert row[3] is not None, f"Missing comment for {row[1]}.{row[2]}"
            assert len(row[3]) > 0, f"Empty comment for {row[1]}.{row[2]}"


class TestFraiseQLCompatibility:
    """Test compatibility checker"""

    def test_compatibility_checker_confirms_all_types_work(self):
        """Test: Compatibility checker confirms all types are FraiseQL compatible"""
        from src.generators.fraiseql.compatibility_checker import CompatibilityChecker

        checker = CompatibilityChecker()
        assert checker.check_all_types_compatible()
        assert len(checker.get_incompatible_types()) == 0

    def test_no_types_need_manual_annotations(self):
        """Test: No rich types require manual @fraiseql:field annotations"""
        from src.generators.fraiseql.compatibility_checker import CompatibilityChecker

        checker = CompatibilityChecker()
        incompatible = checker.get_incompatible_types()

        # All types should be autodiscovered by FraiseQL
        assert len(incompatible) == 0, f"Unexpected manual annotations needed: {incompatible}"
