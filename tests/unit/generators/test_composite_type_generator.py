"""Tests for composite type generation (Team B)"""

import pytest

from src.core.ast_models import Action, Entity, FieldDefinition
from src.generators.composite_type_generator import CompositeTypeGenerator
from src.generators.schema_orchestrator import SchemaOrchestrator


class TestCompositeTypeGenerator:
    """Test composite type generation for app/core pattern"""

    @pytest.fixture
    def generator(self):
        """Create composite type generator"""
        return CompositeTypeGenerator()

    def test_generate_basic_composite_type(self, generator):
        """Generate composite type from action with simple fields"""
        # Given: Entity with create action
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
                "company": FieldDefinition(
                    name="company", type_name="ref", reference_entity="Company", nullable=True
                ),
                "status": FieldDefinition(
                    name="status", type_name="enum", values=["lead", "qualified"], nullable=False
                ),
            },
            actions=[Action(name="create_contact", steps=[])],
        )

        # When: Generate composite type
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: Composite type includes all fields
        assert "CREATE TYPE app.type_create_contact_input AS (" in sql
        assert "email TEXT" in sql
        assert "company_id UUID" in sql  # ✅ FK is UUID (external API contract)
        assert "status TEXT" in sql
        # FraiseQL annotation
        assert "COMMENT ON TYPE app.type_create_contact_input IS" in sql
        assert "@fraiseql:composite" in sql
        assert "name: CreateContactInput" in sql
        assert "tier: 2" in sql

    def test_generate_composite_type_with_nullable_fields(self, generator):
        """Nullable fields in composite types"""
        # Given: Action with nullable fields
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
                "company": FieldDefinition(
                    name="company", type_name="ref", reference_entity="Company", nullable=True
                ),
                "status": FieldDefinition(
                    name="status", type_name="enum", values=["lead", "qualified"], nullable=False
                ),
            },
            actions=[Action(name="create_contact", steps=[])],
        )

        # When: Generate
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: FraiseQL annotations include required/optional info
        assert "@fraiseql:field" in sql
        assert "name: email" in sql
        assert "type: String!" in sql
        assert "required: true" in sql
        assert "references: Company" in sql
        assert "enumValues: lead, qualified" in sql

    def test_generate_composite_type_with_nested_fields(self, generator):
        """Handle complex field types (arrays, lists)"""
        # Given: Entity with list field
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={"tags": FieldDefinition(name="tags", type_name="list", item_type="text")},
            actions=[Action(name="create_contact", steps=[])],
        )

        # When: Generate
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: Array type used
        assert "tags TEXT[]" in sql

    def test_generate_input_composite_with_yaml_comments(self, generator):
        """Generated input composites should have YAML comments"""
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="email", nullable=False),
            },
        )
        action = Action(name="create_contact", steps=[])

        generator = CompositeTypeGenerator()
        sql = generator.generate_input_type(entity, action)

        # Should have type-level comment
        expected_type_comment = """COMMENT ON TYPE app.type_create_contact_input IS
'Input parameters for Create Contact.

@fraiseql:composite
name: CreateContactInput
tier: 2';"""
        assert expected_type_comment in sql

        # Should have field-level comments
        expected_field_comment = """COMMENT ON COLUMN app.type_create_contact_input.email IS
'Email address (required).

@fraiseql:field
name: email
type: String!
required: true';"""
        assert expected_field_comment in sql

    def test_delete_action_generates_input_type_with_id(self, generator):
        """Delete actions generate input types with ID field"""
        # Given: Delete action (needs ID for record identification)
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={},
            actions=[Action(name="delete_contact", steps=[])],
        )

        # When: Generate
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: Generates input type with ID field
        assert "CREATE TYPE app.type_delete_contact_input AS (" in sql
        assert "id UUID" in sql
        assert "COMMENT ON COLUMN app.type_delete_contact_input.id" in sql

    def test_generate_mutation_result_type(self, generator):
        """Generate standard mutation_result composite type"""
        # When: Generate
        sql = generator.generate_mutation_result_type()

        # Then: Standard structure
        assert "CREATE TYPE app.mutation_result AS (" in sql
        assert "id UUID" in sql
        assert "updated_fields TEXT[]" in sql
        assert "status TEXT" in sql
        assert "message TEXT" in sql
        assert "object_data JSONB" in sql
        assert "extra_metadata JSONB" in sql
        assert "@fraiseql:composite" in sql
        assert "name: MutationResult" in sql

    def test_mutation_result_generated_only_once(self, generator):
        """Ensure mutation_result is not duplicated"""
        # When: Generate multiple times
        sql1 = generator.generate_mutation_result_type()
        sql2 = generator.generate_mutation_result_type()

        # Then: Only first call returns SQL, others return empty
        assert sql1 != ""
        assert sql2 == ""

    def test_generate_common_types(self, generator):
        """Generate all common types needed across schema"""
        # When: Generate common types
        sql = generator.generate_common_types()

        # Then: Contains mutation_result
        assert "CREATE TYPE app.mutation_result AS (" in sql
        assert "@fraiseql:composite" in sql
        assert "name: MutationResult" in sql

    def test_mutation_result_supports_impact_metadata(self, generator):
        """Test that mutation_result type supports mutation impact metadata pattern"""
        # When: Generate mutation result type
        sql = generator.generate_mutation_result_type()

        # Then: Supports mutation impact metadata requirements
        # 1. updated_fields exposed for change tracking
        assert "updated_fields TEXT[]" in sql
        assert "@fraiseql:field" in sql
        assert "name: updatedFields" in sql
        assert "type: [String]" in sql

        # 2. extra_metadata JSONB supports _meta field for impact metadata
        assert "extra_metadata JSONB" in sql
        assert "name: extra" in sql
        assert "type: JSON" in sql

        # 3. FraiseQL type annotation for GraphQL mapping
        assert "@fraiseql:composite" in sql
        assert "name: MutationResult" in sql

        # 4. Status field for success/error indication
        assert "status TEXT" in sql

        # 5. Message field for human-readable feedback
        assert "message TEXT" in sql
        assert "name: message" in sql
        assert "type: String" in sql

        # 6. object_data JSONB for full entity data
        assert "object_data JSONB" in sql
        assert "@fraiseql:field" in sql
        assert "name: object" in sql
        assert "type: JSON" in sql

        # 7. id UUID for entity identifier
        assert "id UUID" in sql
        assert "@fraiseql:field" in sql
        assert "name: id" in sql
        assert "type: UUID!" in sql


class TestSchemaOrchestrator:
    """Test schema orchestration (tables + types)"""

    @pytest.fixture
    def orchestrator(self):
        """Create schema orchestrator"""
        from src.generators.schema.naming_conventions import NamingConventions

        naming_conventions = NamingConventions()
        return SchemaOrchestrator(naming_conventions)

    @pytest.fixture
    def generator(self):
        """Create composite type generator"""
        return CompositeTypeGenerator()

    def test_generate_complete_schema(self, orchestrator):
        """Generate complete schema: tables + types"""
        # Given: Entity with actions
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
                "company": FieldDefinition(
                    name="company", type_name="ref", reference_entity="Company", nullable=True
                ),
                "status": FieldDefinition(
                    name="status", type_name="enum", values=["lead", "qualified"], nullable=False
                ),
            },
            actions=[Action(name="create_contact", steps=[])],
        )

        # When: Generate complete schema
        sql = orchestrator.generate_complete_schema(entity)

        # Then: Contains tables + types
        assert "CREATE TABLE crm.tb_contact" in sql
        assert "CREATE TYPE app.type_create_contact_input" in sql
        assert "CREATE TYPE app.mutation_result" in sql
        assert "CREATE INDEX" in sql or "ADD CONSTRAINT" in sql  # indexes or constraints

    def test_schema_summary(self, orchestrator):
        """Generate schema summary"""
        # Given: Entity with fields
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
            },
            actions=[Action(name="create_contact", steps=[])],
        )

        # When: Generate summary
        summary = orchestrator.generate_schema_summary(entity)

        # Then: Contains expected structure
        assert summary["entity"] == "Contact"
        assert summary["table"] == "crm.tb_contact"
        assert "app.type_create_contact_input" in summary["types"]

    def test_fraiseql_annotations_comprehensive(self, generator):
        """Test comprehensive FraiseQL annotations for different field types"""
        # Given: Entity with various field types
        entity = Entity(
            name="Product",
            schema="catalog",
            fields={
                "name": FieldDefinition(name="name", type_name="text", nullable=False),
                "price": FieldDefinition(name="price", type_name="decimal", nullable=False),
                "in_stock": FieldDefinition(name="in_stock", type_name="boolean", nullable=False),
                "category": FieldDefinition(
                    name="category", type_name="ref", reference_entity="Category", nullable=True
                ),
                "tags": FieldDefinition(
                    name="tags", type_name="list", item_type="text", nullable=True
                ),
                "status": FieldDefinition(
                    name="status",
                    type_name="enum",
                    values=["active", "inactive", "discontinued"],
                    nullable=False,
                ),
            },
            actions=[Action(name="create_product", steps=[])],
        )

        # When: Generate composite type
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: FraiseQL annotations are comprehensive
        assert "@fraiseql:field" in sql
        assert "name: name" in sql
        assert "type: String!" in sql
        assert "name: price" in sql
        assert "type: Float!" in sql
        assert "name: in_stock" in sql
        assert "type: Boolean!" in sql
        assert "name: category_id" in sql
        assert "references: Category" in sql
        assert "name: tags" in sql
        assert "type: [TEXT]" in sql
        assert "name: status" in sql
        assert "enumValues: active, inactive, discontinued" in sql

    def test_update_action_field_filtering(self, generator):
        """Test that update actions exclude audit fields"""
        # Given: Entity with audit fields
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
                "created_at": FieldDefinition(
                    name="created_at", type_name="timestamp", nullable=False
                ),
                "created_by": FieldDefinition(name="created_by", type_name="uuid", nullable=True),
                "updated_at": FieldDefinition(
                    name="updated_at", type_name="timestamp", nullable=False
                ),
                "updated_by": FieldDefinition(name="updated_by", type_name="uuid", nullable=True),
            },
            actions=[Action(name="update_contact", steps=[])],
        )

        # When: Generate for update action
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: Only non-audit fields included
        assert "email TEXT" in sql
        assert "created_at" not in sql
        assert "created_by" not in sql
        assert "updated_at" not in sql
        assert "updated_by" not in sql

    def test_custom_action_field_analysis(self, generator):
        """Test custom actions include id field by default"""
        # Given: Custom action
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
            },
            actions=[Action(name="custom_action", steps=[])],
        )

        # When: Generate for custom action
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: ID field included by default (TODO: implement step analysis to include referenced fields)
        assert "id UUID" in sql
        assert "type_custom_action_input" in sql

    def test_empty_entity_no_types_generated(self, generator):
        """Test that entities with no fields don't generate types"""
        # Given: Entity with no fields
        entity = Entity(
            name="Empty", schema="test", fields={}, actions=[Action(name="create_empty", steps=[])]
        )

        # When: Generate
        sql = generator.generate_input_type(entity, entity.actions[0])

        # Then: No type generated
        assert sql == ""

    def test_multiple_actions_generate_multiple_types(self, generator):
        """Test multiple actions generate multiple input types"""
        # Given: Entity with multiple actions
        entity = Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text", nullable=False),
            },
            actions=[
                Action(name="create_contact", steps=[]),
                Action(name="update_contact", steps=[]),
                Action(name="delete_contact", steps=[]),  # Should not generate type
            ],
        )

        # When: Generate all types
        create_sql = generator.generate_input_type(entity, entity.actions[0])
        update_sql = generator.generate_input_type(entity, entity.actions[1])
        delete_sql = generator.generate_input_type(entity, entity.actions[2])

        # Then: All actions generate types (delete has ID field)
        assert "type_create_contact_input" in create_sql
        assert "type_update_contact_input" in update_sql
        assert "type_delete_contact_input" in delete_sql
