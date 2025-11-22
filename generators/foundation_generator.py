# Foundation SQL Generator
"""Generate foundation SQL from project configuration."""

from pathlib import Path
from core.project_config import ProjectConfig


class FoundationGenerator:
    """Generate project foundation SQL from ProjectConfig."""

    def generate(self, config: ProjectConfig) -> str:
        """Generate foundation SQL with extensions and schemas."""
        lines = [
            f"-- Auto-generated from project.yaml",
            f"-- Project: {config.name}",
            "",
        ]

        # Extensions
        if config.extensions:
            lines.append("-- Extensions")
            for ext in config.extensions:
                lines.append(f'CREATE EXTENSION IF NOT EXISTS "{ext}";')
            lines.append("")

        # Schemas
        lines.append("-- Schemas")
        for schema in config.schemas:
            lines.append(f"CREATE SCHEMA IF NOT EXISTS {schema.name};")
            if schema.description:
                lines.append(f"COMMENT ON SCHEMA {schema.name} IS '{schema.description}';")
            lines.append("")

        return "\n".join(lines)
