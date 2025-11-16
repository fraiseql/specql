"""Tests for count aggregation pattern."""

from src.patterns.aggregation.count_aggregation import generate_count_aggregation


class TestCountAggregation:
    """Test count aggregation pattern functionality."""

    def test_generate_count_aggregation_basic(self):
        """Test basic count aggregation generation."""
        config = {
            "name": "v_count_allocations_by_network",
            "pattern": "aggregation/count_aggregation",
            "config": {
                "counted_entity": "Allocation",
                "grouped_by_entity": "NetworkConfiguration",
                "metrics": [
                    {"name": "total_allocations", "condition": "TRUE"},
                    {
                        "name": "active_allocations",
                        "condition": "allocation.status = 'active'",
                    },
                ],
            },
        }

        sql = generate_count_aggregation(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW tenant.v_count_allocations_by_network AS" in sql
        assert "COUNT(CASE WHEN TRUE THEN 1 END) AS total_allocations" in sql
        assert (
            "COUNT(CASE WHEN allocation.status = 'active' THEN 1 END) AS active_allocations"
            in sql
        )
        assert "FROM tb_networkconfiguration networkconfiguration" in sql
        assert "LEFT JOIN tb_allocation allocation" in sql
        assert "GROUP BY networkconfiguration.pk_networkconfiguration" in sql
        assert "tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid" in sql

    def test_generate_count_aggregation_with_join(self):
        """Test count aggregation with custom JOIN conditions."""
        config = {
            "name": "v_count_contracts_by_location",
            "pattern": "aggregation/count_aggregation",
            "config": {
                "counted_entity": "Contract",
                "grouped_by_entity": "Location",
                "join_condition": "contract.location_id = location.pk_location",
                "metrics": [
                    {
                        "name": "contract_count",
                        "condition": "contract.status = 'active'",
                    }
                ],
            },
        }

        sql = generate_count_aggregation(config)

        # Verify custom join condition is used
        assert "ON contract.location_id = location.pk_location" in sql
        assert (
            "COUNT(CASE WHEN contract.status = 'active' THEN 1 END) AS contract_count"
            in sql
        )
        assert "FROM tb_location location" in sql
        assert "LEFT JOIN tb_contract contract" in sql

    def test_generate_count_aggregation_without_join(self):
        """Test count aggregation with default JOIN condition."""
        config = {
            "name": "v_count_items_by_contract",
            "pattern": "aggregation/count_aggregation",
            "config": {
                "counted_entity": "ContractItem",
                "grouped_by_entity": "Contract",
                "metrics": [{"name": "item_count", "condition": "TRUE"}],
            },
        }

        sql = generate_count_aggregation(config)

        # Verify default join condition
        assert "ON contractitem.contract_id = contract.pk_contract" in sql
        assert "FROM tb_contract contract" in sql
        assert "LEFT JOIN tb_contractitem contractitem" in sql

    def test_generate_count_aggregation_schema(self):
        """Test count aggregation with custom schema."""
        config = {
            "name": "v_count_users",
            "schema": "public",
            "pattern": "aggregation/count_aggregation",
            "config": {
                "counted_entity": "User",
                "grouped_by_entity": "Organization",
                "metrics": [{"name": "user_count", "condition": "TRUE"}],
            },
        }

        sql = generate_count_aggregation(config)

        # Verify custom schema
        assert "CREATE OR REPLACE VIEW public.v_count_users AS" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_count_users_organization" in sql
        assert "ON public.v_count_users" in sql
