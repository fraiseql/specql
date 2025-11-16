"""
Integration tests for FraiseQL autodiscovery of SpecQL rich types
Tests that PostgreSQL comments → GraphQL descriptions automatically
"""

import pytest

# Mark all tests as requiring database
pytestmark = pytest.mark.database

from src.core.ast_models import Action, Entity
from src.core.specql_parser import SpecQLParser


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
def test_db_with_rich_types(test_db, isolated_schema, table_generator):
    """Generate schema with rich types and apply to database"""
    parser = SpecQLParser()

    # Define entity YAMLs (without actions to avoid type conflicts)
    # Create in dependency order: independent tables first, then tables with FKs
    entity_yamls = [
        # Independent entities first
        f"""
entity: Company
schema: {isolated_schema}
description: "Company entity for testing"
fields:
  name: text!
  domain: domainName
""",
        f"""
entity: Product
schema: {isolated_schema}
description: "Product with money type"
fields:
  name: text!
  price: money
""",
        f"""
entity: Device
schema: {isolated_schema}
description: "Device with IP address"
fields:
  name: text!
  ip_address: ipAddress
""",
        f"""
entity: Location
schema: {isolated_schema}
description: "Location with coordinates"
fields:
  name: text!
  coordinates: coordinates
""",
        # Contact entity with rich types (depends on Company)
        f"""
entity: Contact
schema: {isolated_schema}
description: "Contact with FraiseQL rich types"
fields:
  # Rich types
  email: email!
  website: url
  phone: phoneNumber
  avatar: image

  # Basic types (backward compatibility)
  first_name: text!
  last_name: text!
  notes: text

  # Relationships
  company: ref(Company)

  # Enums
  status: enum(lead, qualified, customer)
""",
    ]

    cursor = test_db.cursor()

    # Create schema first
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {isolated_schema}")

    # Generate and execute table DDL for each entity
    for yaml_content in entity_yamls:
        entity_def = parser.parse(yaml_content)
        entity = convert_entity_definition_to_entity(entity_def)

        # Debug: print fields
        print(f"\n--- Fields for {entity.name} ---")
        for field_name, field_def in entity.fields.items():
            print(
                f"  {field_name}: type_name={field_def.type_name}, reference_entity={getattr(field_def, 'reference_entity', None)}"
            )

        table_ddl = table_generator.generate_complete_ddl(entity)

        # Debug: print the DDL
        print(f"\n--- DDL for {entity.name} ---")
        print(table_ddl)

        # Check if Contact table was created
        if entity.name == "Contact":
            cursor.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{isolated_schema}' AND table_name = 'tb_contact' AND column_name = 'fk_company'"
            )
            if not cursor.fetchone():
                print("ERROR: fk_company column not found in Contact table!")
                # Rollback and check what was actually created
                cursor.execute(
                    f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{isolated_schema}' AND table_name = 'tb_contact'"
                )
                columns = cursor.fetchall()
                print(f"Contact table columns: {[col[0] for col in columns]}")

        cursor.execute(table_ddl)

    test_db.commit()
    return test_db, isolated_schema


class TestRichTypeAutodiscovery:
    """Test FraiseQL autodiscovery of rich types from PostgreSQL"""

    def test_email_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: email field has CHECK constraint for validation"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%email%'
        """
        )
        constraint = cursor.fetchone()
        assert constraint is not None
        assert "~*" in constraint[0]  # Regex validation present

    def test_email_field_has_comment(self, test_db_with_rich_types):
        """Test: email field has PostgreSQL comment (becomes GraphQL description)"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT col_description('{schema_name}.tb_contact'::regclass, attnum)
            FROM pg_attribute
            WHERE attrelid = '{schema_name}.tb_contact'::regclass
              AND attname = 'email'
        """
        )
        comment = cursor.fetchone()
        assert comment is not None
        assert "email" in comment[0].lower()
        assert "rfc 5322" in comment[0].lower()

    def test_url_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: url field has CHECK constraint"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%website%'
        """
        )
        constraint = cursor.fetchone()
        assert constraint is not None
        assert "~*" in constraint[0]  # URL regex validation

    def test_phone_field_has_check_constraint(self, test_db_with_rich_types):
        """Test: phoneNumber field has CHECK constraint"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = '{schema_name}.tb_contact'::regclass
              AND conname LIKE '%phone%'
        """
        )
        constraint = cursor.fetchone()
        assert constraint is not None

    def test_money_field_uses_numeric_type(self, test_db_with_rich_types):
        """Test: money field uses NUMERIC(19,4)"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT data_type, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_product'
              AND column_name = 'price'
        """
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "numeric"
        assert result[1] == 19
        assert result[2] == 4

    def test_ipaddress_field_uses_inet_type(self, test_db_with_rich_types):
        """Test: ipAddress field uses INET PostgreSQL type"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_device'
              AND column_name = 'ip_address'
        """
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "inet"

    def test_coordinates_field_uses_point_type(self, test_db_with_rich_types):
        """Test: coordinates field uses POINT PostgreSQL type"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT udt_name
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
              AND table_name = 'tb_location'
              AND column_name = 'coordinates'
        """
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "point"

    def test_all_rich_type_fields_have_comments(self, test_db_with_rich_types):
        """Test: All rich type fields have descriptive comments"""
        test_db, schema_name = test_db_with_rich_types
        cursor = test_db.cursor()
        cursor.execute(
            f"""
            SELECT
                c.table_schema,
                c.table_name,
                c.column_name,
                col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as comment
            FROM information_schema.columns c
            WHERE c.table_schema = '{schema_name}'
              AND c.column_name IN ('email', 'website', 'phone', 'price', 'ip_address', 'coordinates')
        """
        )
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
        assert len(incompatible) == 0, (
            f"Unexpected manual annotations needed: {incompatible}"
        )


# ruff: noqa: E402
