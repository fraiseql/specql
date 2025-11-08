"""
Tests for Database Operation Compilation
Phase 3: Insert/Update/Delete Operations
"""

import pytest
from src.core.ast_models import ActionStep, Entity, FieldDefinition
from src.generators.actions.database_operation_compiler import DatabaseOperationCompiler


class TestDatabaseOperations:
    """Test database operation compilation to PL/pgSQL"""

    @pytest.fixture
    def compiler(self):
        """Create database operation compiler instance"""
        return DatabaseOperationCompiler()

    @pytest.fixture
    def contact_entity(self):
        """Create test Contact entity"""
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type="text"),
                "status": FieldDefinition(name="status", type="text"),
                "company": FieldDefinition(name="company", type="ref", target_entity="Company"),
            },
        )

    def test_insert_operation(self, compiler, contact_entity):
        """Test: Generate INSERT statement with RETURNING"""
        step = ActionStep(type="insert", entity="Contact")

        sql = compiler.compile_insert(step, contact_entity)

        # Expected: INSERT with all fields + RETURNING
        assert "INSERT INTO crm.tb_contact" in sql
        assert "email, status, fk_company" in sql
        assert "p_email, p_status, crm.company_pk(p_company_id)" in sql
        assert "RETURNING pk_contact INTO v_pk" in sql

    def test_update_operation_with_audit(self, compiler, contact_entity):
        """Test: Generate UPDATE with auto-audit fields"""
        step = ActionStep(type="update", entity="Contact", fields={"status": "qualified"})

        sql = compiler.compile_update(step, contact_entity)

        # Expected: UPDATE with audit fields
        assert "UPDATE crm.tb_contact" in sql
        assert "SET status = 'qualified'" in sql
        assert "updated_at = now()" in sql
        assert "updated_by = p_caller_id" in sql
        assert "WHERE pk_contact = v_pk" in sql

    def test_full_object_return_with_relationships(self, compiler, contact_entity):
        """Test: Generate full object query with relationships"""
        step = ActionStep(type="insert", entity="Contact")
        impact = type(
            "MockImpact",
            (),
            {"primary": type("MockPrimary", (), {"include_relations": ["company"]})()},
        )()

        sql = compiler.generate_object_return(step, contact_entity, impact)

        # Expected: Full object with company relationship
        assert "SELECT jsonb_build_object(" in sql
        assert "'__typename', 'Contact'" in sql
        assert "'id', c.pk_contact" in sql
        assert "'email', c.email" in sql
        assert "'company', jsonb_build_object(" in sql
        assert "'__typename', 'Company'" in sql
        assert "LEFT JOIN management.tb_company co ON co.pk_company = c.fk_company" in sql
