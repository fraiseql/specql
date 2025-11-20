"""SQL File Generator for SpecQL seed data generation"""

from datetime import datetime
from typing import Any

from .uuid_generator import SpecQLUUID


class SeedSQLGenerator:
    """Generate SQL INSERT statements from entity data"""

    def __init__(self, entity_config: dict[str, Any]):
        self.config = entity_config
        self.schema = entity_config["schema_name"]
        self.table = entity_config["table_name"]

    def generate_insert(self, entity_data: dict[str, Any]) -> str:
        """Generate single INSERT statement"""
        columns = []
        values = []

        for field, value in entity_data.items():
            columns.append(field)
            values.append(self._format_value(value))

        cols_str = ", ".join(columns)
        vals_str = ", ".join(values)

        return f"INSERT INTO {self.schema}.{self.table} ({cols_str}) VALUES ({vals_str});"

    def generate_file(
        self, entities: list[dict[str, Any]], scenario: int = 0, description: str | None = None
    ) -> str:
        """Generate complete SQL file with multiple INSERTs"""
        lines = [
            f"-- Seed data for {self.config['entity_name']}",
            f"-- Schema: {self.schema}",
            f"-- Scenario: {scenario} ({description or 'default'})",
            f"-- Generated: {datetime.now().isoformat()}",
            f"-- Record count: {len(entities)}",
            "",
        ]

        for entity_data in entities:
            lines.append(self.generate_insert(entity_data))

        lines.append("")  # Trailing newline

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format Python value as SQL literal"""
        if value is None:
            return "NULL"
        elif isinstance(value, SpecQLUUID):
            return f"'{value}'"
        elif isinstance(value, str):
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, int | float):
            return str(value)
        elif isinstance(value, datetime):
            return f"'{value.isoformat()}'"
        else:
            # Fallback for unknown types
            return f"'{value}'"
