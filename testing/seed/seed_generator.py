"""Entity Seed Generator for SpecQL test data generation"""

from typing import Any

from .field_generators import FieldValueGenerator
from .fk_resolver import ForeignKeyResolver, GroupLeaderExecutor
from .uuid_generator import SpecQLUUIDGenerator


class EntitySeedGenerator:
    """Generate complete entity records with all fields"""

    def __init__(
        self,
        entity_config: dict[str, Any],
        field_mappings: list[dict[str, Any]],
        db_connection=None,
        seed: int | None = None,
    ):
        self.config = entity_config
        self.field_mappings = sorted(field_mappings, key=lambda x: x["priority_order"])

        self.uuid_gen = SpecQLUUIDGenerator.from_metadata(entity_config)
        self.field_gen = FieldValueGenerator(seed=seed)

        if db_connection:
            self.fk_resolver = ForeignKeyResolver(db_connection)
            self.group_leader = GroupLeaderExecutor(db_connection)
        else:
            self.fk_resolver = None
            self.group_leader = None

    def generate(
        self, scenario: int = 0, instance: int = 1, overrides: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate complete entity record

        Returns:
            Dict with all field values
        """
        entity_data = {}
        context = {"instance_num": instance}

        # Generate UUID first
        entity_data["id"] = self.uuid_gen.generate(scenario=scenario, instance=instance)
        context["id"] = entity_data["id"]

        # Add tenant context
        if self.config["is_tenant_scoped"]:
            entity_data["tenant_id"] = self.config["default_tenant_id"]
            context["tenant_id"] = entity_data["tenant_id"]

        # Process fields in dependency order
        for mapping in self.field_mappings:
            field_name = mapping["field_name"]

            # Skip if overridden
            if overrides and field_name in overrides:
                entity_data[field_name] = overrides[field_name]
                context[field_name] = overrides[field_name]
                continue

            # Skip group dependents (handled by leader)
            if mapping["generator_type"] == "group_dependent":
                continue

            # Generate value
            value = self._generate_field_value(mapping, context)

            # Group leader returns multiple values
            if isinstance(value, dict):
                entity_data.update(value)
                context.update(value)
            else:
                entity_data[field_name] = value
                context[field_name] = value

        return entity_data

    def _generate_field_value(self, mapping: dict[str, Any], context: dict[str, Any]) -> Any:
        """Generate value for single field"""

        gen_type = mapping["generator_type"]

        if gen_type in ("random", "fixed", "sequence"):
            return self.field_gen.generate(mapping, context)

        elif gen_type == "fk_resolve":
            if not self.fk_resolver:
                raise ValueError("FK resolution requires database connection")
            return self.fk_resolver.resolve(mapping, context)

        elif gen_type == "group_leader":
            if not self.group_leader:
                raise ValueError("Group leader requires database connection")
            return self.group_leader.execute(mapping, context)

        else:
            raise ValueError(f"Unknown generator type: {gen_type}")

    def generate_batch(
        self, count: int, scenario: int = 0, overrides: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Generate batch of entity records"""
        return [
            self.generate(scenario=scenario, instance=i + 1, overrides=overrides)
            for i in range(count)
        ]
