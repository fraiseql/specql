"""
Tests for junction/resolver pattern.
"""

from src.patterns.pattern_registry import PatternRegistry


class TestJunctionResolver:
    """Test the junction resolver pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PatternRegistry()

    def test_junction_resolver_discovered(self):
        """Test that junction resolver pattern is discovered."""
        assert "junction/resolver" in self.registry.patterns
        pattern = self.registry.patterns["junction/resolver"]
        assert pattern.name == "junction/resolver"
        assert "Resolve N-to-N relationships" in pattern.description

    def test_two_hop_junction_generation(self):
        """Test generating SQL for a 2-hop junction (A → B → C)."""
        pattern = self.registry.patterns["junction/resolver"]

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "alias": "src",
            "is_multi_tenant": True,
        }

        config = {
            "name": "financing_condition_and_model_by_contract",
            "pattern": "junction/resolver",
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
                },
                {
                    "table": "tb_financing_condition_model",
                    "schema": "tenant",
                    "left_key": "fk_financing_condition",
                    "right_key": "fk_model",
                    "alias": "j2",
                },
            ],
            "target_entity": {
                "name": "Model",
                "schema": "tenant",
                "table": "tb_model",
                "pk_field": "pk_model",
                "alias": "tgt",
            },
            "output_fields": ["src.pk_contract", "tgt.pk_model", "src.tenant_id"],
        }

        sql = pattern.generate(entity, config)

        # Verify basic structure
        assert "CREATE OR REPLACE VIEW tenant.v_financing_condition_and_model_by_contract AS" in sql
        assert "SELECT DISTINCT" in sql
        assert "FROM tenant.tb_contract src" in sql
        assert "INNER JOIN tenant.tb_contract_financing_condition j1" in sql
        assert "INNER JOIN tenant.tb_financing_condition_model j2" in sql
        assert "WHERE src.deleted_at IS NULL" in sql
        assert "AND j1.deleted_at IS NULL" in sql
        assert "AND j2.deleted_at IS NULL" in sql
        assert "CURRENT_SETTING('app.current_tenant_id')" in sql

        # Verify indexes are created
        assert (
            "CREATE INDEX IF NOT EXISTS idx_v_financing_condition_and_model_by_contract_contract"
            in sql
        )
        assert (
            "CREATE INDEX IF NOT EXISTS idx_v_financing_condition_and_model_by_contract_model"
            in sql
        )

    def test_three_hop_junction_generation(self):
        """Test generating SQL for a 3-hop junction (A → B → C → D)."""
        pattern = self.registry.patterns["junction/resolver"]

        entity = {
            "name": "Location",
            "schema": "tenant",
            "table": "tb_location",
            "pk_field": "pk_location",
            "alias": "src",
            "is_multi_tenant": True,
        }

        config = {
            "name": "deep_hierarchy_by_location",
            "pattern": "junction/resolver",
            "schema": "tenant",
            "source_entity": {
                "name": "Location",
                "schema": "tenant",
                "table": "tb_location",
                "pk_field": "pk_location",
                "alias": "src",
                "is_multi_tenant": True,
            },
            "junction_tables": [
                {
                    "table": "tb_location_allocation",
                    "schema": "tenant",
                    "left_key": "fk_location",
                    "right_key": "fk_allocation",
                    "alias": "j1",
                },
                {
                    "table": "tb_allocation_machine",
                    "schema": "tenant",
                    "left_key": "fk_allocation",
                    "right_key": "fk_machine",
                    "alias": "j2",
                },
                {
                    "table": "tb_machine_software",
                    "schema": "tenant",
                    "left_key": "fk_machine",
                    "right_key": "fk_software",
                    "alias": "j3",
                },
            ],
            "target_entity": {
                "name": "Software",
                "schema": "tenant",
                "table": "tb_software",
                "pk_field": "pk_software",
                "alias": "tgt",
            },
            "output_fields": ["src.pk_location", "tgt.pk_software", "src.tenant_id"],
        }

        sql = pattern.generate(entity, config)

        # Verify 3 joins are present
        assert sql.count("INNER JOIN") == 3
        assert "tb_location_allocation j1" in sql
        assert "tb_allocation_machine j2" in sql
        assert "tb_machine_software j3" in sql

        # Verify all junction tables have deleted_at checks
        assert sql.count("AND j1.deleted_at IS NULL") == 1
        assert sql.count("AND j2.deleted_at IS NULL") == 1
        assert sql.count("AND j3.deleted_at IS NULL") == 1

    def test_single_tenant_junction_generation(self):
        """Test junction generation for single-tenant entities."""
        pattern = self.registry.patterns["junction/resolver"]

        entity = {
            "name": "GlobalConfig",
            "schema": "global",
            "table": "tb_global_config",
            "pk_field": "pk_config",
            "alias": "src",
            "is_multi_tenant": False,
        }

        config = {
            "name": "global_settings_by_config",
            "pattern": "junction/resolver",
            "schema": "global",
            "source_entity": entity,
            "junction_tables": [
                {
                    "table": "tb_config_setting",
                    "schema": "global",
                    "left_key": "fk_config",
                    "right_key": "fk_setting",
                    "alias": "j1",
                }
            ],
            "target_entity": {
                "name": "Setting",
                "schema": "global",
                "table": "tb_setting",
                "pk_field": "pk_setting",
                "alias": "tgt",
            },
            "output_fields": ["src.pk_config", "tgt.pk_setting"],
        }

        sql = pattern.generate(entity, config)

        # Verify no tenant filtering for single-tenant
        assert "CURRENT_SETTING('app.current_tenant_id')" not in sql
        assert "global.tb_global_config src" in sql
