# tests/unit/adapters/test_postgresql_adapter.py
from src.adapters.postgresql_adapter import PostgreSQLAdapter
from src.core.universal_ast import (
    UniversalEntity,
    UniversalField,
    FieldType,
    UniversalAction,
    UniversalStep,
    StepType,
)


def test_postgresql_adapter_generates_entity():
    """PostgreSQL adapter generates valid DDL"""
    entity = UniversalEntity(
        name="Contact",
        schema="crm",
        fields=[
            UniversalField(name="email", type=FieldType.TEXT, required=True),
            UniversalField(
                name="company", type=FieldType.REFERENCE, references="Company"
            ),
            UniversalField(
                name="status", type=FieldType.ENUM, enum_values=["lead", "qualified"]
            ),
        ],
        actions=[],
        is_multi_tenant=True,
    )

    adapter = PostgreSQLAdapter()
    result = adapter.generate_entity(entity)

    assert len(result) == 1
    assert result[0].file_path == "db/schema/10_tables/contact.sql"
    assert result[0].language == "sql"

    ddl = result[0].content
    assert "CREATE TABLE tb_contact" in ddl
    assert "pk_contact SERIAL PRIMARY KEY" in ddl
    assert "id UUID NOT NULL DEFAULT gen_random_uuid()" in ddl
    assert "identifier VARCHAR(255) NOT NULL" in ddl
    assert "tenant_id UUID NOT NULL" in ddl
    assert "email TEXT NOT NULL" in ddl
    assert "company INTEGER REFERENCES tb_company(pk_company)" in ddl
    assert "status TEXT" in ddl
    assert "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in ddl
    assert "CREATE INDEX idx_tb_contact_tenant ON tb_contact(tenant_id)" in ddl


def test_postgresql_adapter_generates_action():
    """PostgreSQL adapter generates valid PL/pgSQL"""
    action = UniversalAction(
        name="qualify_lead",
        entity="Contact",
        steps=[
            UniversalStep(type=StepType.VALIDATE, expression="status = 'lead'"),
            UniversalStep(
                type=StepType.UPDATE, entity="Contact", fields={"status": "qualified"}
            ),
        ],
        impacts=["Contact"],
    )

    entity = UniversalEntity(name="Contact", schema="crm", fields=[], actions=[action])

    adapter = PostgreSQLAdapter()
    result = adapter.generate_action(action, entity)

    assert len(result) == 1
    assert result[0].file_path == "db/schema/06_functions/crm/qualify_lead.sql"
    assert result[0].language == "sql"

    plpgsql = result[0].content
    assert "CREATE OR REPLACE FUNCTION crm.qualify_lead()" in plpgsql
    assert "RETURNS JSONB" in plpgsql
    assert "LANGUAGE plpgsql" in plpgsql
    assert "-- Validate: status = 'lead'" in plpgsql
    assert "RAISE EXCEPTION 'Validation failed:" in plpgsql
    assert "-- Update Contact" in plpgsql
    assert "UPDATE tb_contact SET" in plpgsql


def test_postgresql_adapter_get_conventions():
    """PostgreSQL adapter returns correct conventions"""
    adapter = PostgreSQLAdapter()
    conventions = adapter.get_conventions()

    assert conventions.naming_case == "snake_case"
    assert conventions.primary_key_name == "pk_{entity}"
    assert conventions.foreign_key_pattern == "fk_{entity}"
    assert conventions.timestamp_fields == ["created_at", "updated_at", "deleted_at"]
    assert conventions.supports_multi_tenancy is True


def test_postgresql_adapter_get_framework_name():
    """PostgreSQL adapter returns correct framework name"""
    adapter = PostgreSQLAdapter()
    assert adapter.get_framework_name() == "postgresql"


def test_postgresql_adapter_generate_relationship():
    """PostgreSQL adapter generates foreign key relationships"""
    adapter = PostgreSQLAdapter()

    # Reference field
    ref_field = UniversalField(
        name="company", type=FieldType.REFERENCE, references="Company"
    )
    entity = UniversalEntity(name="Contact", schema="crm", fields=[], actions=[])

    relationship = adapter.generate_relationship(ref_field, entity)
    assert relationship == "REFERENCES tb_company(pk_company)"

    # Non-reference field
    text_field = UniversalField(name="email", type=FieldType.TEXT)
    relationship = adapter.generate_relationship(text_field, entity)
    assert relationship == ""
