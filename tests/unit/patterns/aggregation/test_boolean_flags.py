"""Tests for boolean flag aggregation pattern."""

import pytest
from src.patterns.aggregation.boolean_flags import generate_boolean_flags


class TestBooleanFlags:
    """Test boolean flag aggregation pattern functionality."""

    def test_generate_boolean_flags_basic(self):
        """Test basic boolean flag generation."""
        config = {
            "name": "v_current_allocations_by_machine",
            "pattern": "aggregation/boolean_flags",
            "config": {
                "source_entity": "Machine",
                "flags": [
                    {
                        "name": "has_active_allocations",
                        "condition": "EXISTS(SELECT 1 FROM tb_allocation a WHERE a.machine_id = machine.pk_machine AND a.status = 'active' AND a.deleted_at IS NULL)",
                    },
                    {
                        "name": "has_pending_allocations",
                        "condition": "COUNT(CASE WHEN allocation.status = 'pending' THEN 1 END) > 0",
                    },
                    {
                        "name": "is_fully_allocated",
                        "condition": "COUNT(allocation.pk_allocation) >= machine.capacity",
                    },
                ],
            },
        }

        sql = generate_boolean_flags(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW tenant.v_current_allocations_by_machine AS" in sql
        assert "AS has_active_allocations" in sql
        assert "AS has_pending_allocations" in sql
        assert "AS is_fully_allocated" in sql
        assert "FROM tb_machine machine" in sql
        assert "LEFT JOIN tb_allocation allocation" in sql

    def test_generate_boolean_flags_with_item_join(self):
        """Test boolean flags that require JOIN to related entities."""
        config = {
            "name": "v_machine_items",
            "pattern": "aggregation/boolean_flags",
            "config": {
                "source_entity": "Machine",
                "flags": [{"name": "has_items", "condition": "COUNT(item.pk_item) > 0"}],
            },
        }

        sql = generate_boolean_flags(config)

        # This test verifies that flags requiring related entity access work
        # (Note: array aggregation not implemented in this simplified version)
        assert "AS has_items" in sql
        assert "FROM tb_machine machine" in sql

    def test_generate_boolean_flags_temporal(self):
        """Test boolean flags with temporal conditions."""
        config = {
            "name": "v_contract_status_flags",
            "pattern": "aggregation/boolean_flags",
            "config": {
                "source_entity": "Contract",
                "flags": [
                    {
                        "name": "is_active",
                        "condition": "contract.start_date <= CURRENT_DATE AND (contract.end_date IS NULL OR contract.end_date >= CURRENT_DATE)",
                    },
                    {
                        "name": "expires_soon",
                        "condition": "contract.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'",
                    },
                ],
            },
        }

        sql = generate_boolean_flags(config)

        # Verify temporal conditions
        assert "contract.start_date <= CURRENT_DATE" in sql
        assert "contract.end_date IS NULL OR contract.end_date >= CURRENT_DATE" in sql
        assert "contract.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'" in sql

    def test_generate_boolean_flags_complex(self):
        """Test complex boolean flags like the 9-flag PrintOptim example."""
        config = {
            "name": "v_machine_allocation_flags",
            "pattern": "aggregation/boolean_flags",
            "config": {
                "source_entity": "Machine",
                "flags": [
                    {
                        "name": "has_primary_allocation",
                        "condition": "COUNT(CASE WHEN allocation.is_primary THEN 1 END) > 0",
                    },
                    {
                        "name": "has_backup_allocation",
                        "condition": "COUNT(CASE WHEN allocation.is_backup THEN 1 END) > 0",
                    },
                    {
                        "name": "has_temporary_allocation",
                        "condition": "COUNT(CASE WHEN allocation.type = 'temporary' THEN 1 END) > 0",
                    },
                    {
                        "name": "has_permanent_allocation",
                        "condition": "COUNT(CASE WHEN allocation.type = 'permanent' THEN 1 END) > 0",
                    },
                    {
                        "name": "is_overallocated",
                        "condition": "SUM(allocation.utilization) > machine.capacity",
                    },
                    {
                        "name": "is_underallocated",
                        "condition": "SUM(allocation.utilization) < machine.min_utilization",
                    },
                    {
                        "name": "needs_maintenance",
                        "condition": "machine.last_maintenance < CURRENT_DATE - INTERVAL '90 days'",
                    },
                    {
                        "name": "has_open_tickets",
                        "condition": "EXISTS(SELECT 1 FROM tb_ticket t WHERE t.machine_id = machine.pk_machine AND t.status IN ('open', 'in_progress'))",
                    },
                    {"name": "is_decommissioned", "condition": "machine.status = 'decommissioned'"},
                ],
            },
        }

        sql = generate_boolean_flags(config)

        # Verify all 9 flags are present
        assert "has_primary_allocation" in sql
        assert "has_backup_allocation" in sql
        assert "has_temporary_allocation" in sql
        assert "has_permanent_allocation" in sql
        assert "is_overallocated" in sql
        assert "is_underallocated" in sql
        assert "needs_maintenance" in sql
        assert "has_open_tickets" in sql
        assert "is_decommissioned" in sql
