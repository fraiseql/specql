"""Tests for hierarchical count aggregation pattern."""

from src.patterns.aggregation.hierarchical_count import generate_hierarchical_count


class TestHierarchicalCount:
    """Test hierarchical count aggregation pattern functionality."""

    def test_generate_hierarchical_count_basic(self):
        """Test basic hierarchical count generation."""
        config = {
            "name": "v_count_allocations_by_location",
            "pattern": "aggregation/hierarchical_count",
            "config": {
                "counted_entity": "Allocation",
                "grouped_by_entity": "Location",
                "metrics": [
                    {"name": "total_allocations", "direct": True, "hierarchical": True},
                    {"name": "active_allocations", "direct": True, "hierarchical": False},
                ],
            },
        }

        sql = generate_hierarchical_count(config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW tenant.v_count_allocations_by_location AS" in sql
        assert (
            "COUNT(CASE WHEN child.location_id = parent.pk_location THEN 1 END) AS total_allocations_direct"
            in sql
        )
        assert (
            "COUNT(CASE WHEN parent.path @> child.location_path THEN 1 END) AS total_allocations_total"
            in sql
        )
        assert (
            "COUNT(CASE WHEN child.location_id = parent.pk_location THEN 1 END) AS active_allocations_direct"
            in sql
        )
        assert "FROM tb_location parent" in sql
        assert "LEFT JOIN tb_allocation child" in sql
        assert "GROUP BY parent.pk_location, parent.path" in sql
        assert "parent.path" in sql

    def test_generate_hierarchical_count_ltree_only(self):
        """Test hierarchical count with only hierarchical metrics."""
        config = {
            "name": "v_count_descendants_only",
            "pattern": "aggregation/hierarchical_count",
            "config": {
                "counted_entity": "Contract",
                "grouped_by_entity": "Organization",
                "metrics": [{"name": "contract_count", "direct": False, "hierarchical": True}],
            },
        }

        sql = generate_hierarchical_count(config)

        # Should not have direct count
        assert "contract_count_direct" not in sql
        assert (
            "COUNT(CASE WHEN parent.path @> child.organization_path THEN 1 END) AS contract_count_total"
            in sql
        )

    def test_generate_hierarchical_count_direct_only(self):
        """Test hierarchical count with only direct metrics."""
        config = {
            "name": "v_count_direct_only",
            "pattern": "aggregation/hierarchical_count",
            "config": {
                "counted_entity": "User",
                "grouped_by_entity": "Department",
                "metrics": [{"name": "user_count", "direct": True, "hierarchical": False}],
            },
        }

        sql = generate_hierarchical_count(config)

        # Should not have hierarchical count
        assert "user_count_total" not in sql
        assert (
            "COUNT(CASE WHEN child.department_id = parent.pk_department THEN 1 END) AS user_count_direct"
            in sql
        )
        # Should not include path in GROUP BY since no hierarchical metrics
        assert "parent.path" not in sql

    def test_generate_hierarchical_count_custom_path_field(self):
        """Test hierarchical count with custom path field."""
        config = {
            "name": "v_count_custom_path",
            "pattern": "aggregation/hierarchical_count",
            "config": {
                "counted_entity": "Project",
                "grouped_by_entity": "Portfolio",
                "path_field": "hierarchy_path",  # Custom path field
                "metrics": [{"name": "project_count", "direct": False, "hierarchical": True}],
            },
        }

        sql = generate_hierarchical_count(config)

        # Should use custom path field
        assert "parent.hierarchy_path @> child.portfolio_hierarchy_path" in sql
