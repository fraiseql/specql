"""FK Resolver and Group Leader components for SpecQL seed data generation"""

from typing import Any

import psycopg


class ForeignKeyResolver:
    """Resolve foreign key values by querying database"""

    def __init__(self, db_connection: psycopg.Connection):
        self.db = db_connection

    def resolve(self, field_mapping: dict[str, Any], context: dict[str, Any]) -> int | None:
        """
        Resolve FK value by querying target table

        Returns:
            INTEGER pk value from target table
        """
        # Check dependencies satisfied
        dependencies = field_mapping.get("fk_dependencies", [])
        for dep in dependencies:
            if dep not in context:
                raise ValueError(f"FK dependency not satisfied: {dep}")

        # Use custom query if provided
        if field_mapping.get("fk_resolution_query"):
            query = field_mapping["fk_resolution_query"]
            # Replace placeholders
            for key, value in context.items():
                if isinstance(value, str):
                    query = query.replace(f"${key}", f"'{value}'")
                else:
                    query = query.replace(f"${key}", str(value))
        else:
            # Default: random selection from target table
            query = self._build_default_query(field_mapping, context)

        result = self.db.execute(query).fetchone()
        return result[0] if result else None

    def _build_default_query(self, mapping: dict, context: dict) -> str:
        """Build default FK resolution query"""
        schema = mapping["fk_target_schema"]
        table = mapping["fk_target_table"]
        pk_field = mapping["fk_target_pk_field"]

        query = f"SELECT {pk_field} FROM {schema}.{table} WHERE deleted_at IS NULL"

        # Add tenant filter if tenant-scoped
        if "tenant_id" in context:
            query += f" AND tenant_id = '{context['tenant_id']}'"

        # Add custom filter conditions
        if mapping.get("fk_filter_conditions"):
            query += f" AND {mapping['fk_filter_conditions']}"

        query += " ORDER BY RANDOM() LIMIT 1"

        return query


class GroupLeaderExecutor:
    """Execute group leader queries to get multiple related field values"""

    def __init__(self, db_connection: psycopg.Connection):
        self.db = db_connection

    def execute(self, leader_mapping: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute group leader query, return all dependent field values

        Returns:
            Dict mapping field names to values
            Example: {'country_code': 'FR', 'postal_code': '75001', 'city_code': 'PAR'}
        """
        query = leader_mapping["generator_params"]["leader_query"]
        dependent_fields = leader_mapping["group_dependency_fields"]

        result = self.db.execute(query).fetchone()

        if not result:
            raise ValueError(f"Group leader query returned no results: {query}")

        # Map result columns to dependent field names
        return dict(zip(dependent_fields, result))
