"""Tests for audit field generation with recalculation tracking."""

import pytest
from src.generators.schema.audit_fields import (
    generate_audit_fields,
    generate_business_audit_update,
    generate_identifier_recalculation_audit,
    generate_path_recalculation_audit,
)


class TestGenerateAuditFields:
    """Test audit field generation."""

    def test_non_hierarchical_entity_audit_fields(self):
        """Test audit fields for non-hierarchical entity."""
        result = generate_audit_fields(is_hierarchical=False)

        expected = """    -- Business Data Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Identifier Recalculation Audit (separate from business changes)
    identifier_recalculated_at TIMESTAMPTZ,
    identifier_recalculated_by UUID"""

        assert result == expected

    def test_hierarchical_entity_audit_fields(self):
        """Test audit fields for hierarchical entity."""
        result = generate_audit_fields(is_hierarchical=True)

        expected = """    -- Business Data Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Identifier Recalculation Audit (separate from business changes)
    identifier_recalculated_at TIMESTAMPTZ,
    identifier_recalculated_by UUID,

    -- Path Recalculation Audit (for hierarchical entities)
    path_updated_at TIMESTAMPTZ,
    path_updated_by UUID"""

        assert result == expected

    def test_default_parameters(self):
        """Test default parameters (non-hierarchical)."""
        result = generate_audit_fields()

        # Should be same as non-hierarchical
        expected = """    -- Business Data Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- Identifier Recalculation Audit (separate from business changes)
    identifier_recalculated_at TIMESTAMPTZ,
    identifier_recalculated_by UUID"""

        assert result == expected


class TestAuditUpdateSnippets:
    """Test audit update SQL snippet generation."""

    def test_business_audit_update_default(self):
        """Test business audit update with default user field."""
        result = generate_business_audit_update()

        expected = """updated_at = now(),
    updated_by = current_user_id"""

        assert result == expected

    def test_business_audit_update_custom_field(self):
        """Test business audit update with custom user field."""
        result = generate_business_audit_update("p_caller_id")

        expected = """updated_at = now(),
    updated_by = p_caller_id"""

        assert result == expected

    def test_identifier_recalculation_audit_default(self):
        """Test identifier recalculation audit with default system user."""
        result = generate_identifier_recalculation_audit()

        expected = """identifier_recalculated_at = now(),
    identifier_recalculated_by = system_user_id"""

        assert result == expected

    def test_identifier_recalculation_audit_custom_field(self):
        """Test identifier recalculation audit with custom system user."""
        result = generate_identifier_recalculation_audit("p_system_user")

        expected = """identifier_recalculated_at = now(),
    identifier_recalculated_by = p_system_user"""

        assert result == expected

    def test_path_recalculation_audit_default(self):
        """Test path recalculation audit with default system user."""
        result = generate_path_recalculation_audit()

        expected = """path_updated_at = now(),
    path_updated_by = system_user_id"""

        assert result == expected

    def test_path_recalculation_audit_custom_field(self):
        """Test path recalculation audit with custom system user."""
        result = generate_path_recalculation_audit("p_system_user")

        expected = """path_updated_at = now(),
    path_updated_by = p_system_user"""

        assert result == expected


class TestAuditFieldsIntegration:
    """Test audit fields work together in realistic scenarios."""

    def test_business_update_example(self):
        """Test complete business update SQL example."""
        audit_snippet = generate_business_audit_update("p_caller_id")

        sql = f"""UPDATE tb_location SET
    name = 'New Name',
    {audit_snippet}
WHERE pk_location = 123;"""

        expected = """UPDATE tb_location SET
    name = 'New Name',
    updated_at = now(),
    updated_by = p_caller_id
WHERE pk_location = 123;"""

        assert sql == expected

    def test_identifier_recalculation_example(self):
        """Test complete identifier recalculation SQL example."""
        audit_snippet = generate_identifier_recalculation_audit("p_system_user")

        sql = f"""UPDATE tb_location SET
    identifier = new_identifier,
    {audit_snippet}
WHERE pk_location = 123;"""

        expected = """UPDATE tb_location SET
    identifier = new_identifier,
    identifier_recalculated_at = now(),
    identifier_recalculated_by = p_system_user
WHERE pk_location = 123;"""

        assert sql == expected

    def test_path_recalculation_example(self):
        """Test complete path recalculation SQL example."""
        audit_snippet = generate_path_recalculation_audit("p_system_user")

        sql = f"""UPDATE tb_location SET
    path = new_path,
    {audit_snippet}
WHERE pk_location = 123;"""

        expected = """UPDATE tb_location SET
    path = new_path,
    path_updated_at = now(),
    path_updated_by = p_system_user
WHERE pk_location = 123;"""

        assert sql == expected
