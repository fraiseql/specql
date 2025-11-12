"""
Tests for QueryPatternGenerator - generates SQL views from query patterns in entity definitions.
"""

from unittest.mock import Mock

from src.generators.query_pattern_generator import QueryPatternGenerator


class TestQueryPatternGenerator:
    """Test the QueryPatternGenerator class."""

    def test_generate_from_entity(self):
        """Test generating SQL files from entity with query patterns."""
        # Mock pattern registry
        mock_registry = Mock()
        mock_pattern = Mock()
        mock_pattern.generate.return_value = "CREATE OR REPLACE VIEW tenant.v_test AS SELECT 1;"
        mock_registry.get_pattern.return_value = mock_pattern

        # Create generator
        generator = QueryPatternGenerator(mock_registry)

        # Mock entity with query patterns
        entity = {
            "name": "Location",
            "schema": "tenant",
            "query_patterns": [
                {
                    "name": "count_allocations_by_location",
                    "pattern": "aggregation/hierarchical_count",
                    "config": {
                        "counted_entity": "Allocation",
                        "grouped_by_entity": "Location",
                        "metrics": [
                            {"name": "direct", "direct": True},
                            {"name": "total", "hierarchical": True},
                        ],
                    },
                }
            ],
        }

        # Generate SQL files
        sql_files = generator.generate(entity)

        # Verify results
        assert len(sql_files) == 1
        assert sql_files[0].name == "v_count_allocations_by_location.sql"
        assert "CREATE OR REPLACE VIEW" in sql_files[0].content

        # Verify pattern was called correctly
        mock_registry.get_pattern.assert_called_once_with("aggregation/hierarchical_count")
        mock_pattern.generate.assert_called_once()

    def test_generate_entity_without_patterns(self):
        """Test generating from entity with no query patterns."""
        mock_registry = Mock()
        generator = QueryPatternGenerator(mock_registry)

        entity = {"name": "SimpleEntity", "schema": "tenant", "query_patterns": []}

        sql_files = generator.generate(entity)

        assert len(sql_files) == 0
        mock_registry.get_pattern.assert_not_called()

    def test_generate_multiple_patterns(self):
        """Test generating multiple patterns from one entity."""
        mock_registry = Mock()
        mock_pattern1 = Mock()
        mock_pattern1.generate.return_value = "CREATE VIEW v_pattern1 AS SELECT 1;"
        mock_pattern2 = Mock()
        mock_pattern2.generate.return_value = "CREATE VIEW v_pattern2 AS SELECT 2;"

        def mock_get_pattern(pattern_name):
            if pattern_name == "pattern1":
                return mock_pattern1
            elif pattern_name == "pattern2":
                return mock_pattern2
            else:
                raise ValueError(f"Unknown pattern: {pattern_name}")

        mock_registry.get_pattern.side_effect = mock_get_pattern

        generator = QueryPatternGenerator(mock_registry)

        entity = {
            "name": "ComplexEntity",
            "schema": "tenant",
            "query_patterns": [
                {"name": "view1", "pattern": "pattern1", "config": {}},
                {"name": "view2", "pattern": "pattern2", "config": {}},
            ],
        }

        sql_files = generator.generate(entity)

        assert len(sql_files) == 2
        assert sql_files[0].name == "v_view1.sql"
        assert sql_files[1].name == "v_view2.sql"

        assert mock_registry.get_pattern.call_count == 2

    def test_generate_with_dependencies(self):
        """Test generating patterns with dependencies in correct order."""
        mock_registry = Mock()
        mock_pattern1 = Mock()
        mock_pattern1.generate.return_value = "CREATE VIEW v_base AS SELECT 1;"
        mock_pattern2 = Mock()
        mock_pattern2.generate.return_value = "CREATE VIEW v_dependent AS SELECT * FROM v_base;"

        def mock_get_pattern(pattern_name):
            if pattern_name == "base":
                return mock_pattern1
            elif pattern_name == "dependent":
                return mock_pattern2
            else:
                raise ValueError(f"Unknown pattern: {pattern_name}")

        mock_registry.get_pattern.side_effect = mock_get_pattern

        generator = QueryPatternGenerator(mock_registry)

        entity = {
            "name": "EntityWithDeps",
            "schema": "tenant",
            "query_patterns": [
                {
                    "name": "dependent_view",
                    "pattern": "dependent",
                    "depends_on": ["v_base_view"],
                    "config": {},
                },
                {"name": "base_view", "pattern": "base", "config": {}},
            ],
        }

        sql_files = generator.generate(entity)

        # Should generate in dependency order: base first, then dependent
        assert len(sql_files) == 2
        assert sql_files[0].name == "v_base_view.sql"
        assert sql_files[1].name == "v_dependent_view.sql"

        # Verify patterns were called in correct order
        calls = mock_registry.get_pattern.call_args_list
        assert calls[0][0][0] == "base"  # First call should be for base pattern
        assert calls[1][0][0] == "dependent"  # Second call should be for dependent pattern

    def test_multi_tenant_entity_detection(self):
        """Test that multi-tenant entities are detected correctly."""
        mock_registry = Mock()
        mock_pattern = Mock()
        mock_pattern.generate.return_value = "CREATE VIEW v_test AS SELECT 1;"

        def mock_get_pattern(pattern_name):
            return mock_pattern

        mock_registry.get_pattern.side_effect = mock_get_pattern

        generator = QueryPatternGenerator(mock_registry)

        # Test multi-tenant entity (schema-based detection)
        entity_mt = {
            "name": "Location",
            "schema": "tenant",
            "query_patterns": [{"name": "test_view", "pattern": "test", "config": {}}],
        }

        sql_files = generator.generate(entity_mt)
        assert len(sql_files) == 1

        # Verify pattern.generate was called with multi-tenant entity
        call_args = mock_pattern.generate.call_args
        entity_arg = call_args[0][0]  # First positional argument (entity)
        assert entity_arg["schema"] == "tenant"

    def test_non_multi_tenant_entity_detection(self):
        """Test that non-multi-tenant entities are detected correctly."""
        mock_registry = Mock()
        mock_pattern = Mock()
        mock_pattern.generate.return_value = "CREATE VIEW v_test AS SELECT 1;"

        def mock_get_pattern(pattern_name):
            return mock_pattern

        mock_registry.get_pattern.side_effect = mock_get_pattern

        generator = QueryPatternGenerator(mock_registry)

        # Test non-multi-tenant entity
        entity_non_mt = {
            "name": "Product",
            "schema": "catalog",
            "query_patterns": [{"name": "test_view", "pattern": "test", "config": {}}],
        }

        sql_files = generator.generate(entity_non_mt)
        assert len(sql_files) == 1

        # Verify pattern.generate was called
        call_args = mock_pattern.generate.call_args
        entity_arg = call_args[0][0]
        assert entity_arg["schema"] == "catalog"

    def test_performance_optimization_materialized_view(self):
        """Test that performance configuration enables materialized views."""
        mock_registry = Mock()
        mock_pattern = Mock()

        # Mock pattern that supports performance config
        def mock_generate(entity, config):
            performance = config.get("performance", {})
            sql = "CREATE VIEW v_test AS SELECT 1;"
            if performance.get("materialized"):
                sql += "\nCREATE MATERIALIZED VIEW m_test AS SELECT * FROM v_test;"
            return sql

        mock_pattern.generate.side_effect = mock_generate
        mock_registry.get_pattern.return_value = mock_pattern

        generator = QueryPatternGenerator(mock_registry)

        # Test with performance.materialized = true
        entity = {
            "name": "TestEntity",
            "schema": "tenant",
            "query_patterns": [
                {
                    "name": "test_view",
                    "pattern": "test",
                    "performance": {
                        "materialized": True,
                        "indexes": [{"fields": ["pk_test"]}],
                        "refresh_strategy": "concurrent",
                    },
                    "config": {},
                }
            ],
        }

        sql_files = generator.generate(entity)
        assert len(sql_files) == 1

        # Verify materialized view SQL was generated
        sql_content = sql_files[0].content
        assert "CREATE MATERIALIZED VIEW" in sql_content
