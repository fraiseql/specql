"""Tests for Entity Seed Generator component"""

from unittest.mock import Mock

from src.testing.seed.seed_generator import EntitySeedGenerator
from src.testing.seed.uuid_generator import SpecQLUUID


class TestEntitySeedGenerator:
    """Test Entity Seed Generator functionality"""

    def test_generate_basic_entity(self):
        """Test generating a basic entity record"""
        # Mock components
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()
        mock_field_gen.generate.side_effect = ["John", "Doe", "john@example.com"]

        # Entity config
        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        # Field mappings
        field_mappings = [
            {"field_name": "first_name", "generator_type": "random", "priority_order": 1},
            {"field_name": "last_name", "generator_type": "random", "priority_order": 2},
            {"field_name": "email", "generator_type": "random", "priority_order": 3},
        ]

        generator = EntitySeedGenerator(entity_config=entity_config, field_mappings=field_mappings)

        # Mock the internal generators
        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen

        result = generator.generate(scenario=0, instance=1)

        expected = {
            "id": SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }

        assert result == expected
        mock_uuid_gen.generate.assert_called_once_with(scenario=0, instance=1)
        assert mock_field_gen.generate.call_count == 3

    def test_generate_tenant_scoped_entity(self):
        """Test generating entity with tenant scoping"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()
        mock_field_gen.generate.return_value = "test@example.com"

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": True,
            "default_tenant_id": "22222222-2222-2222-2222-222222222222",
        }

        field_mappings = [{"field_name": "email", "generator_type": "random", "priority_order": 1}]

        generator = EntitySeedGenerator(entity_config=entity_config, field_mappings=field_mappings)

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen

        result = generator.generate(scenario=0, instance=1)

        assert result["tenant_id"] == "22222222-2222-2222-2222-222222222222"
        assert result["id"] == SpecQLUUID("01232121-0000-0000-0001-000000000001")
        assert result["email"] == "test@example.com"

    def test_generate_with_fk_resolution(self):
        """Test generating entity with FK field resolution"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()
        mock_fk_resolver = Mock()
        mock_fk_resolver.resolve.return_value = 42

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [
            {"field_name": "email", "generator_type": "random", "priority_order": 1},
            {
                "field_name": "fk_company",
                "generator_type": "fk_resolve",
                "fk_target_schema": "crm",
                "fk_target_table": "tb_company",
                "fk_target_pk_field": "id",
                "priority_order": 2,
            },
        ]

        generator = EntitySeedGenerator(
            entity_config=entity_config,
            field_mappings=field_mappings,
            db_connection=Mock(),  # Enable FK resolution
        )

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen
        generator.fk_resolver = mock_fk_resolver

        result = generator.generate(scenario=0, instance=1)

        assert result["fk_company"] == 42
        mock_fk_resolver.resolve.assert_called_once()

    def test_generate_with_group_leader(self):
        """Test generating entity with group leader field"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_group_leader = Mock()
        mock_group_leader.execute.return_value = {
            "country_code": "FR",
            "postal_code": "75001",
            "city_code": "PAR",
        }

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [
            {"field_name": "email", "generator_type": "random", "priority_order": 1},
            {
                "field_name": "country_code",
                "generator_type": "group_leader",
                "group_dependency_fields": ["country_code", "postal_code", "city_code"],
                "generator_params": {"leader_query": "SELECT * FROM crm.tb_city WHERE id = 1"},
                "priority_order": 2,
            },
            {"field_name": "postal_code", "generator_type": "group_dependent", "priority_order": 3},
            {"field_name": "city_code", "generator_type": "group_dependent", "priority_order": 4},
        ]

        generator = EntitySeedGenerator(
            entity_config=entity_config,
            field_mappings=field_mappings,
            db_connection=Mock(),  # Enable group leader
        )

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = Mock()
        generator.group_leader = mock_group_leader

        result = generator.generate(scenario=0, instance=1)

        assert result["country_code"] == "FR"
        assert result["postal_code"] == "75001"
        assert result["city_code"] == "PAR"
        mock_group_leader.execute.assert_called_once()

    def test_generate_with_overrides(self):
        """Test generating entity with field overrides"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()
        mock_field_gen.generate.return_value = "generated@example.com"

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [
            {"field_name": "email", "generator_type": "random", "priority_order": 1},
            {"field_name": "first_name", "generator_type": "random", "priority_order": 2},
        ]

        generator = EntitySeedGenerator(entity_config=entity_config, field_mappings=field_mappings)

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen

        overrides = {"email": "override@example.com"}
        result = generator.generate(scenario=0, instance=1, overrides=overrides)

        assert result["email"] == "override@example.com"  # Should use override
        assert result["first_name"] == "generated@example.com"  # Should use generated value

    def test_generate_batch(self):
        """Test generating batch of entity records"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.side_effect = [
            SpecQLUUID("01232121-0000-0000-0001-000000000001"),
            SpecQLUUID("01232121-0000-0000-0002-000000000002"),
            SpecQLUUID("01232121-0000-0000-0003-000000000003"),
        ]

        mock_field_gen = Mock()
        mock_field_gen.generate.side_effect = [
            "email1@example.com",
            "email2@example.com",
            "email3@example.com",
        ]

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [{"field_name": "email", "generator_type": "random", "priority_order": 1}]

        generator = EntitySeedGenerator(entity_config=entity_config, field_mappings=field_mappings)

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen

        result = generator.generate_batch(count=3, scenario=0)

        assert len(result) == 3
        assert result[0]["email"] == "email1@example.com"
        assert result[1]["email"] == "email2@example.com"
        assert result[2]["email"] == "email3@example.com"

        assert result[0]["id"] == SpecQLUUID("01232121-0000-0000-0001-000000000001")
        assert result[1]["id"] == SpecQLUUID("01232121-0000-0000-0002-000000000002")
        assert result[2]["id"] == SpecQLUUID("01232121-0000-0000-0003-000000000003")

    def test_generate_with_sequence_context(self):
        """Test that instance_num is passed to field generators for sequences"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()
        mock_field_gen.generate.return_value = 42

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [
            {"field_name": "sequence_field", "generator_type": "sequence", "priority_order": 1}
        ]

        generator = EntitySeedGenerator(entity_config=entity_config, field_mappings=field_mappings)

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen

        result = generator.generate(scenario=0, instance=5)

        # Check that context includes instance_num
        mock_field_gen.generate.assert_called_once()
        call_args = mock_field_gen.generate.call_args
        context = call_args[0][1]  # Second positional argument
        assert context["instance_num"] == 5

    def test_skip_group_dependent_fields(self):
        """Test that group_dependent fields are skipped (handled by group leader)"""
        mock_uuid_gen = Mock()
        mock_uuid_gen.generate.return_value = SpecQLUUID("01232121-0000-0000-0001-000000000001")

        mock_field_gen = Mock()

        entity_config = {
            "entity_name": "Contact",
            "schema_name": "crm",
            "table_name": "tb_contact",
            "base_uuid_prefix": "012321",
            "is_tenant_scoped": False,
        }

        field_mappings = [
            {"field_name": "country_code", "generator_type": "group_leader", "priority_order": 1},
            {"field_name": "postal_code", "generator_type": "group_dependent", "priority_order": 2},
            {"field_name": "city_code", "generator_type": "group_dependent", "priority_order": 3},
        ]

        generator = EntitySeedGenerator(
            entity_config=entity_config, field_mappings=field_mappings, db_connection=Mock()
        )

        generator.uuid_gen = mock_uuid_gen
        generator.field_gen = mock_field_gen
        generator.group_leader = Mock()

        result = generator.generate(scenario=0, instance=1)

        # group_dependent fields should not be processed individually
        # (they're handled by the group leader)
        assert "postal_code" not in result
        assert "city_code" not in result
        # Only the group leader field should be in result (but we mocked it to return dict)
        mock_field_gen.generate.assert_not_called()
