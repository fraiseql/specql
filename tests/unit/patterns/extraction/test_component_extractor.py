"""
Unit tests for extraction patterns (component and temporal).
"""

from src.patterns.pattern_registry import PatternRegistry


class TestComponentExtractor:
    """Test component extractor pattern generation."""

    def test_generate_location_coordinates_extraction(self):
        """Test generating v_location_coordinates view for efficient mapping queries."""
        registry = PatternRegistry()

        # Test that the pattern exists
        pattern = registry.get_pattern("extraction/component")
        assert pattern.name == "extraction/component"
        assert pattern.description == "Extract non-null components for efficient LEFT JOIN"

        # Test pattern configuration
        entity = {
            "name": "Location",
            "schema": "tenant",
            "table": "tb_location",
            "pk_field": "pk_location",
            "is_multi_tenant": True,
        }

        config = {
            "name": "location_coordinates",
            "pattern": "extraction/component",
            "config": {
                "source_entity": "Location",
                "extracted_fields": [{"name": "latitude"}, {"name": "longitude"}],
                "filter_condition": "latitude IS NOT NULL AND longitude IS NOT NULL",
                "purpose": "Extract locations with coordinates to avoid NULL values in LEFT JOINs for mapping features",
            },
        }

        # Generate SQL - this should work once pattern is implemented
        sql = pattern.generate(entity, config)

        # Verify generated SQL structure
        assert "CREATE OR REPLACE VIEW tenant.v_location_coordinates AS" in sql
        assert "SELECT" in sql
        assert "pk_location AS pk_location" in sql
        assert "latitude" in sql
        assert "longitude" in sql
        assert "FROM tenant.tb_location" in sql
        assert "WHERE deleted_at IS NULL" in sql
        assert "AND latitude IS NOT NULL AND longitude IS NOT NULL" in sql
        assert "AND tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_location_coordinates_pk_location" in sql

    def test_generate_machine_active_allocations_extraction(self):
        """Test generating v_machine_active_allocations view."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/component")

        entity = {
            "name": "Machine",
            "schema": "tenant",
            "table": "tb_machine",
            "pk_field": "pk_machine",
            "is_multi_tenant": True,
        }

        config = {
            "name": "machine_active_allocations",
            "pattern": "extraction/component",
            "config": {
                "source_entity": "Machine",
                "source_table": "tv_machine_allocation_view",  # Different table
                "extracted_fields": [
                    {"name": "allocation_id", "alias": "pk_allocation"},
                    {"name": "start_date"},
                    {"name": "end_date"},
                ],
                "filter_condition": "allocation.status = 'active' AND allocation.start_date <= CURRENT_DATE AND (allocation.end_date IS NULL OR allocation.end_date >= CURRENT_DATE)",
                "purpose": "Extract active machine allocations for dashboard performance",
            },
        }

        sql = pattern.generate(entity, config)

        # Verify generated SQL
        assert "CREATE OR REPLACE VIEW tenant.v_machine_active_allocations AS" in sql
        assert "pk_machine AS pk_machine" in sql
        assert "allocation_id AS pk_allocation" in sql
        assert "start_date" in sql
        assert "end_date" in sql
        assert "FROM tenant.tv_machine_allocation_view" in sql  # Uses source_table
        assert "allocation.status = 'active'" in sql

    def test_generate_without_filter_condition(self):
        """Test component extraction without filter condition."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/component")

        entity = {
            "name": "Contact",
            "schema": "tenant",
            "table": "tb_contact",
            "pk_field": "pk_contact",
            "is_multi_tenant": False,  # Non-multi-tenant
        }

        config = {
            "name": "contact_emails",
            "pattern": "extraction/component",
            "config": {
                "source_entity": "Contact",
                "extracted_fields": [{"name": "email"}],
                "purpose": "Extract contacts with email addresses",
            },
        }

        sql = pattern.generate(entity, config)

        # Should not include tenant filtering for non-multi-tenant entities
        assert "tenant_id = CURRENT_SETTING" not in sql
        assert "AND email" not in sql  # No filter condition

    def test_missing_extracted_fields_generates_empty_select(self):
        """Test that missing extracted_fields doesn't break generation."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/component")

        entity = {"name": "Test", "schema": "tenant", "table": "tb_test", "pk_field": "pk_test"}

        config = {
            "name": "test_view",
            "pattern": "extraction/component",
            "config": {
                "source_entity": "Test",
                "extracted_fields": [],  # Empty - should still work
            },
        }

        sql = pattern.generate(entity, config)

        # Should generate valid SQL even with empty fields
        assert "CREATE OR REPLACE VIEW tenant.v_test_view AS" in sql
        assert "SELECT" in sql
        assert "pk_test AS pk_test" in sql
        # No additional fields after pk_field


class TestTemporalExtractor:
    """Test temporal extractor pattern generation."""

    def test_generate_current_contracts_temporal_filter(self):
        """Test generating v_current_contracts view for active contracts."""
        registry = PatternRegistry()

        # Test that the pattern exists
        pattern = registry.get_pattern("extraction/temporal")
        assert pattern.name == "extraction/temporal"
        assert (
            pattern.description
            == "Extract temporally filtered entities (current, future, historical)"
        )

        # Test pattern configuration
        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "current_contracts",
            "pattern": "extraction/temporal",
            "config": {
                "source_entity": "Contract",
                "temporal_mode": "current",
                "date_field_start": "start_date",
                "date_field_end": "end_date",
                "reference_date": "CURRENT_DATE",
                "purpose": "Extract currently active contracts for dashboard and reporting",
            },
        }

        # Generate SQL
        sql = pattern.generate(entity, config)

        # Verify generated SQL structure
        assert "CREATE OR REPLACE VIEW tenant.v_current_contracts AS" in sql
        assert "SELECT *" in sql
        assert "FROM tenant.tb_contract" in sql
        assert "WHERE deleted_at IS NULL" in sql
        assert "AND start_date <= CURRENT_DATE" in sql
        assert "AND (end_date IS NULL OR end_date >= CURRENT_DATE)" in sql
        assert "AND tenant_id = CURRENT_SETTING('app.current_tenant_id')::uuid" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_v_current_contracts_start_date" in sql

    def test_generate_future_contracts_temporal_filter(self):
        """Test generating v_future_contracts view for upcoming contracts."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/temporal")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "future_contracts",
            "pattern": "extraction/temporal",
            "config": {
                "source_entity": "Contract",
                "temporal_mode": "future",
                "date_field_start": "start_date",
                "reference_date": "CURRENT_DATE",
                "purpose": "Extract upcoming contracts for planning and forecasting",
            },
        }

        sql = pattern.generate(entity, config)

        # Verify future mode filtering
        assert "CREATE OR REPLACE VIEW tenant.v_future_contracts AS" in sql
        assert "AND start_date > CURRENT_DATE" in sql
        # Should not include end_date condition for future mode
        assert "end_date" not in sql

    def test_generate_historical_contracts_temporal_filter(self):
        """Test generating v_historical_contracts view for expired contracts."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/temporal")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": False,  # Non-multi-tenant
        }

        config = {
            "name": "historical_contracts",
            "pattern": "extraction/temporal",
            "config": {
                "source_entity": "Contract",
                "temporal_mode": "historical",
                "date_field_start": "start_date",
                "date_field_end": "end_date",
                "reference_date": "CURRENT_DATE",
                "purpose": "Extract expired contracts for historical analysis",
            },
        }

        sql = pattern.generate(entity, config)

        # Verify historical mode filtering
        assert "CREATE OR REPLACE VIEW tenant.v_historical_contracts AS" in sql
        assert "AND end_date < CURRENT_DATE" in sql
        # Should not include tenant filtering for non-multi-tenant
        assert "tenant_id" not in sql

    def test_generate_with_custom_reference_date(self):
        """Test temporal extraction with custom reference date."""
        registry = PatternRegistry()

        pattern = registry.get_pattern("extraction/temporal")

        entity = {
            "name": "Contract",
            "schema": "tenant",
            "table": "tb_contract",
            "pk_field": "pk_contract",
            "is_multi_tenant": True,
        }

        config = {
            "name": "contracts_as_of_date",
            "pattern": "extraction/temporal",
            "config": {
                "source_entity": "Contract",
                "temporal_mode": "current",
                "date_field_start": "start_date",
                "date_field_end": "end_date",
                "reference_date": "'2024-01-01'::date",
                "purpose": "Extract contracts active as of specific date",
            },
        }

        sql = pattern.generate(entity, config)

        # Verify custom reference date
        assert "AND start_date <= '2024-01-01'::date" in sql
        assert "AND (end_date IS NULL OR end_date >= '2024-01-01'::date)" in sql
