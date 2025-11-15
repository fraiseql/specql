# tests/unit/core/test_universal_ast.py
from src.core.universal_ast import (
    FieldType,
    StepType,
    UniversalField,
    UniversalEntity,
    UniversalAction,
    UniversalStep,
    UniversalSchema,
)


def test_universal_entity_has_no_sql_specifics():
    """Universal entity should not reference SQL concepts"""
    entity = UniversalEntity(
        name="Contact",
        schema="app",
        fields=[
            UniversalField(name="email", type=FieldType.TEXT),
            UniversalField(name="company", type=FieldType.REFERENCE, references="Company"),
        ],
        actions=[],
    )

    # Should NOT have SQL-specific attributes
    assert not hasattr(entity, "table_name")
    assert not hasattr(entity, "sql_type")

    # SHOULD have universal attributes
    assert entity.name == "Contact"
    assert len(entity.fields) == 2
    assert entity.fields[0].type == FieldType.TEXT
    assert entity.fields[1].type == FieldType.REFERENCE


def test_universal_action_has_no_plpgsql_specifics():
    """Universal action should not reference PL/pgSQL concepts"""
    action = UniversalAction(
        name="qualify_lead",
        entity="Contact",
        steps=[
            UniversalStep(type=StepType.VALIDATE, expression="status = 'lead'"),
            UniversalStep(type=StepType.UPDATE, entity="Contact", fields={"status": "qualified"}),
        ],
        impacts=["Contact"],
    )

    # Should have framework-agnostic representation
    assert action.steps[0].type == StepType.VALIDATE
    assert action.steps[1].type == StepType.UPDATE
    assert action.steps[1].entity == "Contact"


def test_universal_field_types():
    """Test all universal field types are defined"""
    # Basic types
    assert FieldType.TEXT.value == "text"
    assert FieldType.INTEGER.value == "integer"
    assert FieldType.BOOLEAN.value == "boolean"
    assert FieldType.DATETIME.value == "datetime"

    # Advanced types
    assert FieldType.REFERENCE.value == "reference"
    assert FieldType.ENUM.value == "enum"
    assert FieldType.LIST.value == "list"
    assert FieldType.RICH.value == "rich"


def test_universal_step_types():
    """Test all universal step types are defined"""
    assert StepType.VALIDATE.value == "validate"
    assert StepType.IF.value == "if"
    assert StepType.INSERT.value == "insert"
    assert StepType.UPDATE.value == "update"
    assert StepType.DELETE.value == "delete"
    assert StepType.CALL.value == "call"
    assert StepType.NOTIFY.value == "notify"
    assert StepType.FOREACH.value == "foreach"


def test_universal_field_with_enum():
    """Test universal field with enum values"""
    field = UniversalField(
        name="status", type=FieldType.ENUM, enum_values=["lead", "qualified", "customer"]
    )

    assert field.type == FieldType.ENUM
    assert field.enum_values == ["lead", "qualified", "customer"]


def test_universal_field_with_reference():
    """Test universal field with reference"""
    field = UniversalField(name="company", type=FieldType.REFERENCE, references="Company")

    assert field.type == FieldType.REFERENCE
    assert field.references == "Company"


def test_universal_entity_with_actions():
    """Test universal entity with actions"""
    action = UniversalAction(
        name="create_contact",
        entity="Contact",
        steps=[UniversalStep(type=StepType.INSERT, entity="Contact")],
        impacts=["Contact"],
    )

    entity = UniversalEntity(name="Contact", schema="crm", fields=[], actions=[action])

    assert len(entity.actions) == 1
    assert entity.actions[0].name == "create_contact"


def test_universal_schema():
    """Test universal schema containing multiple entities"""
    entity1 = UniversalEntity(name="Contact", schema="crm", fields=[], actions=[])
    entity2 = UniversalEntity(name="Company", schema="crm", fields=[], actions=[])

    schema = UniversalSchema(
        entities=[entity1, entity2], composite_types={}, tenant_mode="multi_tenant"
    )

    assert len(schema.entities) == 2
    assert schema.tenant_mode == "multi_tenant"


def test_parser_produces_universal_ast():
    """Test that SpecQLParser can parse YAML to Universal AST"""
    from src.core.specql_parser import SpecQLParser

    yaml_content = """
    entity: Contact
    schema: crm
    fields:
      email: text!
      company: ref(Company)
      status: enum(lead, qualified, customer)
    actions:
      - name: qualify_lead
        steps:
          - validate: status = 'lead'
          - update: Contact SET status = 'qualified'
    """

    parser = SpecQLParser()
    entity = parser.parse_universal(yaml_content)

    assert entity.name == "Contact"
    assert entity.schema == "crm"
    assert len(entity.fields) == 3
    assert len(entity.actions) == 1

    # Check fields
    email_field = entity.fields[0]
    assert email_field.name == "email"
    assert email_field.type == FieldType.TEXT
    assert email_field.required  is True

    company_field = entity.fields[1]
    assert company_field.name == "company"
    assert company_field.type == FieldType.REFERENCE
    assert company_field.references == "Company"

    status_field = entity.fields[2]
    assert status_field.name == "status"
    assert status_field.type == FieldType.ENUM
    assert status_field.enum_values == ["lead", "qualified", "customer"]

    # Check actions
    action = entity.actions[0]
    assert action.name == "qualify_lead"
    assert action.entity == "Contact"
    assert len(action.steps) == 2
    assert action.steps[0].type == StepType.VALIDATE
    assert action.steps[1].type == StepType.UPDATE
