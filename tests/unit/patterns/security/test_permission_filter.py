"""Unit tests for security permission filter pattern."""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestPermissionFilterPattern:
    """Test security permission filter pattern generation."""

    def test_permission_filter_ownership(self):
        """Test: Generate permission filter with ownership check"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/permission_filter")

        # This should fail initially - pattern doesn't exist yet
        assert pattern is not None

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "c",
        }

        config = {
            "name": "v_contract_accessible",
            "schema": "tenant",
            "pattern": "security/permission_filter",
            "config": {
                "base_entity": entity,
                "permission_checks": [{"type": "ownership", "field": "created_by"}],
                "user_context_source": "CURRENT_SETTING('app.current_user_id')",
                "deny_by_default": True,
            },
        }

        sql = pattern.generate(entity, config)

        # Validate SQL structure
        assert "CREATE OR REPLACE VIEW" in sql
        assert "security/permission_filter" in sql
        assert "app.current_user_id" in sql
        assert "created_by" in sql
        assert "AND (" in sql  # deny_by_default creates AND condition

    def test_permission_filter_role_based(self):
        """Test: Generate permission filter with role-based access"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/permission_filter")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "c",
        }

        config = {
            "name": "v_contract_admin",
            "schema": "tenant",
            "pattern": "security/permission_filter",
            "config": {
                "base_entity": entity,
                "permission_checks": [
                    {"type": "role_based", "allowed_roles": ["admin", "contract_manager"]}
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate role-based logic
        assert "tb_user_role" in sql
        assert "admin" in sql
        assert "contract_manager" in sql
        assert "EXISTS" in sql

    def test_permission_filter_organizational_hierarchy(self):
        """Test: Generate permission filter with organizational hierarchy"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/permission_filter")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "c",
        }

        config = {
            "name": "v_contract_org",
            "schema": "tenant",
            "pattern": "security/permission_filter",
            "config": {
                "base_entity": entity,
                "permission_checks": [
                    {"type": "organizational_hierarchy", "field": "organization_id"}
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate organizational hierarchy logic
        assert "tb_organizational_unit" in sql
        assert "path <@" in sql  # PostgreSQL ltree operator
        assert "organizational_unit_path" in sql

    def test_permission_filter_multiple_checks(self):
        """Test: Generate permission filter with multiple permission checks"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/permission_filter")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "c",
        }

        config = {
            "name": "v_contract_multi",
            "schema": "tenant",
            "pattern": "security/permission_filter",
            "config": {
                "base_entity": entity,
                "permission_checks": [
                    {"type": "ownership", "field": "created_by"},
                    {"type": "role_based", "allowed_roles": ["admin"]},
                ],
                "deny_by_default": True,
            },
        }

        sql = pattern.generate(entity, config)

        # Validate multiple conditions with OR logic
        assert sql.count("OR") >= 1  # Should have OR between conditions

    def test_permission_filter_custom_condition(self):
        """Test: Generate permission filter with custom condition"""
        registry = PatternRegistry()
        pattern = registry.get_pattern("security/permission_filter")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "c",
        }

        config = {
            "name": "v_contract_custom",
            "schema": "tenant",
            "pattern": "security/permission_filter",
            "config": {
                "base_entity": entity,
                "permission_checks": [
                    {
                        "type": "custom",
                        "custom_condition": "contract.status = 'active' AND contract.amount > 1000",
                    }
                ],
            },
        }

        sql = pattern.generate(entity, config)

        # Validate custom condition is included
        assert "contract.status = 'active'" in sql
        assert "contract.amount > 1000" in sql
