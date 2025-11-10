"""
Tests for junction/aggregated_resolver pattern.
"""

import pytest
from src.patterns.pattern_registry import PatternRegistry


class TestJunctionAggregatedResolver:
    """Test the junction aggregated resolver pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PatternRegistry()

    def test_aggregated_resolver_discovered(self):
        """Test that aggregated resolver pattern is discovered."""
        assert "junction/aggregated_resolver" in self.registry.patterns
        pattern = self.registry.patterns["junction/aggregated_resolver"]
        assert pattern.name == "junction/aggregated_resolver"
        assert "JSONB array aggregation" in pattern.description

    def test_machine_items_aggregation(self):
        """Test generating SQL for machine items aggregation (v_machine_items example)."""
        pattern = self.registry.patterns["junction/aggregated_resolver"]

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "alias": "src",
            "is_multi_tenant": True,
        }

        config = {
            "name": "machine_items",
            "pattern": "junction/aggregated_resolver",
            "schema": "tenant",
            "source_entity": {
                "name": "Machine",
                "schema": "tenant",
                "table": "tb_machine",
                "pk_field": "pk_machine",
                "alias": "src",
                "is_multi_tenant": True,
            },
            "junction_tables": [
                {
                    "table": "tb_machine_allocation",
                    "schema": "tenant",
                    "left_key": "fk_machine",
                    "right_key": "fk_allocation",
                    "alias": "j1",
                }
            ],
            "target_entity": {
                "name": "Allocation",
                "schema": "tenant",
                "table": "tb_allocation",
                "pk_field": "pk_allocation",
                "alias": "tgt",
            },
            "aggregate_into": "allocations",
            "aggregation_fields": [
                {"name": "id", "expression": "tgt.pk_allocation"},
                {"name": "location_id", "expression": "tgt.fk_location"},
                {"name": "start_date", "expression": "tgt.start_date"},
                {"name": "end_date", "expression": "tgt.end_date"},
            ],
            "order_by": ["tgt.start_date"],
        }

        sql = pattern.generate(entity, config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW tenant.v_machine_items AS" in sql
        assert "SELECT" in sql
        assert "src.pk_machine" in sql
        assert "jsonb_agg(" in sql
        assert "jsonb_build_object(" in sql
        assert "'id', tgt.pk_allocation" in sql
        assert "'location_id', tgt.fk_location" in sql
        assert "AS allocations" in sql
        assert "FROM tenant.tb_machine src" in sql
        assert "INNER JOIN tenant.tb_machine_allocation j1" in sql
        assert "INNER JOIN tenant.tb_allocation tgt" in sql
        assert "GROUP BY src.pk_machine" in sql

        # Verify ordering
        assert "ORDER BY tgt.start_date" in sql

        # Verify tenant filtering
        assert "CURRENT_SETTING('app.current_tenant_id')" in sql

        # Verify index creation
        assert "CREATE INDEX IF NOT EXISTS idx_v_machine_items_machine" in sql

    def test_contract_financing_conditions_aggregation(self):
        """Test generating SQL for contract financing conditions aggregation."""
        pattern = self.registry.patterns["junction/aggregated_resolver"]

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "src",
            "is_multi_tenant": True,
        }

        config = {
            "name": "contract_financing_conditions",
            "pattern": "junction/aggregated_resolver",
            "schema": "tenant",
            "source_entity": {
                "name": "Contract",
                "schema": "tenant",
                "table": "tb_contract",
                "pk_field": "pk_contract",
                "alias": "src",
                "is_multi_tenant": True,
            },
            "junction_tables": [
                {
                    "table": "tb_contract_financing_condition",
                    "schema": "tenant",
                    "left_key": "fk_contract",
                    "right_key": "fk_financing_condition",
                    "alias": "j1",
                }
            ],
            "target_entity": {
                "name": "FinancingCondition",
                "schema": "tenant",
                "table": "tb_financing_condition",
                "pk_field": "pk_financing_condition",
                "alias": "tgt",
            },
            "aggregate_into": "financing_conditions",
            "aggregation_fields": [
                {"name": "id", "expression": "tgt.pk_financing_condition"},
                {"name": "name", "expression": "tgt.name"},
                {"name": "rate", "expression": "tgt.interest_rate"},
                {"name": "term_months", "expression": "tgt.term_months"},
            ],
        }

        sql = pattern.generate(entity, config)

        # Verify aggregation field mapping
        assert "'id', tgt.pk_financing_condition" in sql
        assert "'name', tgt.name" in sql
        assert "'rate', tgt.interest_rate" in sql
        assert "'term_months', tgt.term_months" in sql

        # No ordering specified
        assert "ORDER BY" not in sql

    def test_no_ordering_specified(self):
        """Test aggregation without ordering."""
        pattern = self.registry.patterns["junction/aggregated_resolver"]

        entity = {
            "name": "Location",
            "schema": "tenant",
            "table": "tb_location",
            "pk_field": "pk_location",
            "alias": "src",
            "is_multi_tenant": False,
        }

        config = {
            "name": "location_machines",
            "pattern": "junction/aggregated_resolver",
            "schema": "tenant",
            "source_entity": entity,
            "junction_tables": [
                {
                    "table": "tb_allocation",
                    "schema": "tenant",
                    "left_key": "fk_location",
                    "right_key": "fk_machine",
                    "alias": "j1",
                }
            ],
            "target_entity": {
                "name": "Machine",
                "schema": "tenant",
                "table": "tb_machine",
                "pk_field": "pk_machine",
                "alias": "tgt",
            },
            "aggregate_into": "machines",
            "aggregation_fields": [
                {"name": "id", "expression": "tgt.pk_machine"},
                {"name": "name", "expression": "tgt.name"},
            ],
            # No order_by specified
        }

        sql = pattern.generate(entity, config)

        # Verify no ORDER BY clause
        assert "ORDER BY" not in sql

        # Verify no tenant filtering for single-tenant
        assert "CURRENT_SETTING('app.current_tenant_id')" not in sql
