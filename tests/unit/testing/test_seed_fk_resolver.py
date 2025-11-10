"""Tests for FK Resolver and Group Leader components"""

from unittest.mock import Mock

import pytest

from src.testing.seed.fk_resolver import ForeignKeyResolver, GroupLeaderExecutor


class TestForeignKeyResolver:
    """Test FK resolution functionality"""

    def test_resolve_with_custom_query(self):
        """Test FK resolution with custom query"""
        # Mock database connection
        mock_db = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (42,)
        mock_db.execute.return_value = mock_result

        resolver = ForeignKeyResolver(mock_db)

        field_mapping = {
            "fk_target_schema": "crm",
            "fk_target_table": "tb_company",
            "fk_target_pk_field": "id",
            "fk_resolution_query": "SELECT id FROM crm.tb_company WHERE name = $company_name LIMIT 1",
        }

        context = {"company_name": "Acme Corp"}

        result = resolver.resolve(field_mapping, context)

        assert result == 42
        mock_db.execute.assert_called_once_with(
            "SELECT id FROM crm.tb_company WHERE name = 'Acme Corp' LIMIT 1"
        )

    def test_resolve_with_dependencies_not_satisfied(self):
        """Test FK resolution fails when dependencies not satisfied"""
        mock_db = Mock()
        resolver = ForeignKeyResolver(mock_db)

        field_mapping = {
            "fk_dependencies": ["company_name"],
            "fk_target_schema": "crm",
            "fk_target_table": "tb_company",
        }

        context = {}  # Missing company_name

        with pytest.raises(ValueError, match="FK dependency not satisfied: company_name"):
            resolver.resolve(field_mapping, context)

    def test_resolve_default_query(self):
        """Test FK resolution with default query"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (123,)
        mock_db.execute.return_value = mock_result

        resolver = ForeignKeyResolver(mock_db)

        field_mapping = {
            "fk_target_schema": "crm",
            "fk_target_table": "tb_company",
            "fk_target_pk_field": "id",
        }

        context = {"tenant_id": "tenant-123"}

        result = resolver.resolve(field_mapping, context)

        assert result == 123
        expected_query = "SELECT id FROM crm.tb_company WHERE deleted_at IS NULL AND tenant_id = 'tenant-123' ORDER BY RANDOM() LIMIT 1"
        mock_db.execute.assert_called_once_with(expected_query)

    def test_resolve_default_query_no_tenant(self):
        """Test FK resolution default query without tenant"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (456,)
        mock_db.execute.return_value = mock_result

        resolver = ForeignKeyResolver(mock_db)

        field_mapping = {
            "fk_target_schema": "crm",
            "fk_target_table": "tb_company",
            "fk_target_pk_field": "id",
        }

        context = {}  # No tenant

        result = resolver.resolve(field_mapping, context)

        assert result == 456
        expected_query = (
            "SELECT id FROM crm.tb_company WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1"
        )
        mock_db.execute.assert_called_once_with(expected_query)

    def test_resolve_with_filter_conditions(self):
        """Test FK resolution with custom filter conditions"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (789,)
        mock_db.execute.return_value = mock_result

        resolver = ForeignKeyResolver(mock_db)

        field_mapping = {
            "fk_target_schema": "crm",
            "fk_target_table": "tb_company",
            "fk_target_pk_field": "id",
            "fk_filter_conditions": "status = 'active'",
        }

        context = {}

        result = resolver.resolve(field_mapping, context)

        assert result == 789
        expected_query = "SELECT id FROM crm.tb_company WHERE deleted_at IS NULL AND status = 'active' ORDER BY RANDOM() LIMIT 1"
        mock_db.execute.assert_called_once_with(expected_query)


class TestGroupLeaderExecutor:
    """Test Group Leader execution functionality"""

    def test_execute_group_leader(self):
        """Test group leader query execution"""
        mock_db = Mock()
        mock_result = Mock()
        # Mock result as tuple: (country_code, postal_code, city_code)
        mock_result.fetchone.return_value = ("FR", "75001", "PAR")
        mock_db.execute.return_value = mock_result

        executor = GroupLeaderExecutor(mock_db)

        leader_mapping = {
            "generator_params": {
                "leader_query": "SELECT country_code, postal_code, city_code FROM crm.tb_city WHERE id = 1"
            },
            "group_dependency_fields": ["country_code", "postal_code", "city_code"],
        }

        context = {}

        result = executor.execute(leader_mapping, context)

        assert result == {"country_code": "FR", "postal_code": "75001", "city_code": "PAR"}
        mock_db.execute.assert_called_once_with(
            "SELECT country_code, postal_code, city_code FROM crm.tb_city WHERE id = 1"
        )

    def test_execute_group_leader_no_results(self):
        """Test group leader query with no results"""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        executor = GroupLeaderExecutor(mock_db)

        leader_mapping = {
            "generator_params": {"leader_query": "SELECT * FROM non_existent_table"},
            "group_dependency_fields": ["field1", "field2"],
        }

        context = {}

        with pytest.raises(ValueError, match="Group leader query returned no results"):
            executor.execute(leader_mapping, context)
