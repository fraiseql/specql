"""Group Leader Pattern Detection

Detects field groups that should use the group leader pattern for correlated data generation.
"""

from typing import Any

from src.core.ast_models import Entity


class GroupLeaderDetector:
    """Detect field groups that should use group leader pattern"""

    # Known field group patterns
    ADDRESS_FIELDS = {"country_code", "postal_code", "city_code", "country", "postal", "city"}
    LOCATION_FIELDS = {"latitude", "longitude", "elevation"}
    PERSON_FIELDS = {"first_name", "last_name", "gender", "birth_date", "age"}

    # Default group configurations
    DEFAULT_GROUPS = {
        "address_group": {
            "fields": ADDRESS_FIELDS,
            "leader_priority": ["country_code", "country"],
            "table": "dim.tb_address",
            "query_template": "SELECT {fields} FROM dim.tb_address WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1",
        },
        "location_group": {
            "fields": LOCATION_FIELDS,
            "leader_priority": ["latitude"],
            "table": "dim.tb_location",
            "query_template": "SELECT {fields} FROM dim.tb_location WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1",
        },
        "person_group": {
            "fields": PERSON_FIELDS,
            "leader_priority": ["first_name"],
            "table": "dim.tb_person",
            "query_template": "SELECT {fields} FROM dim.tb_person WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1",
        },
    }

    def detect_groups(self, entity: Entity) -> dict[str, dict[str, Any]]:
        """Detect field groups in entity"""
        groups = {}

        # Check for custom groups defined in entity metadata
        custom_groups = self._detect_custom_groups(entity)
        groups.update(custom_groups)

        # Detect built-in groups
        builtin_groups = self._detect_builtin_groups(entity)
        groups.update(builtin_groups)

        return groups

    def _detect_custom_groups(self, entity: Entity) -> dict[str, dict[str, Any]]:
        """Detect custom groups defined in entity metadata"""
        groups = {}

        # Check if entity has custom group definitions
        # This would be added to Entity model in future - for now return empty
        # TODO: Add metadata support to Entity model for custom test groups
        return groups

    def _detect_builtin_groups(self, entity: Entity) -> dict[str, dict[str, Any]]:
        """Detect built-in field groups"""
        groups = {}

        for group_name, config in self.DEFAULT_GROUPS.items():
            available_fields = set(entity.fields.keys()) & config["fields"]
            if len(available_fields) >= 2:
                leader = self._pick_leader(available_fields, config["leader_priority"])
                groups[group_name] = {
                    "leader": leader,
                    "dependents": [f for f in available_fields if f != leader],
                    "query_template": self._build_optimized_query_template(
                        config, available_fields
                    ),
                    "table": config["table"],
                    "builtin": True,
                }

        return groups

    def _build_optimized_query_template(
        self, config: dict[str, Any], available_fields: set[str]
    ) -> str:
        """Build optimized query template for available fields"""
        field_list = ", ".join(sorted(available_fields))
        base_template = config["query_template"]
        return base_template.replace("{fields}", field_list)

    def _build_custom_query_template(
        self, config: dict[str, Any], available_fields: set[str]
    ) -> str:
        """Build custom query template"""
        # For custom groups, use provided template or build default
        template = config.get(
            "query_template",
            "SELECT {fields} FROM {table} WHERE deleted_at IS NULL ORDER BY RANDOM() LIMIT 1",
        )
        field_list = ", ".join(sorted(available_fields))
        table = config.get("table", "dim.tb_custom")
        return template.replace("{fields}", field_list).replace("{table}", table)

    def _pick_leader(self, fields: set[str], priority: list[str]) -> str:
        """Pick group leader based on priority"""
        for candidate in priority:
            if candidate in fields:
                return candidate
        # If no priority match, pick the first alphabetically
        return sorted(fields)[0]

    def _get_address_query_template(self) -> str:
        """Get SQL query template for address group (legacy method)"""
        config = self.DEFAULT_GROUPS["address_group"]
        fields = {"country_code", "postal_code", "city_code"}
        return self._build_optimized_query_template(config, fields)

    def _get_location_query_template(self) -> str:
        """Get SQL query template for location group (legacy method)"""
        config = self.DEFAULT_GROUPS["location_group"]
        fields = {"latitude", "longitude", "elevation"}
        return self._build_optimized_query_template(config, fields)
