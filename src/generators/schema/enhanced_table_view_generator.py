"""
Enhanced Table View (tv_) Generator

Generates denormalized table views with JSONB and auto-refresh capabilities:
- JSONB data column for flexible GraphQL queries
- Auto-refresh triggers from tb_ tables
- Trinity pattern compatibility
- GIN indexes for JSONB queries
"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import Entity


class EnhancedTableViewGenerator:
    """Generates enhanced table views (tv_) with JSONB and auto-refresh"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("table_view.sql.j2")

    def generate(self, entity: Entity) -> str:
        """
        Generate enhanced table view SQL with JSONB and auto-sync

        Args:
            entity: Entity to generate view for

        Returns:
            SQL DDL for table view with refresh function and trigger
        """
        table_name = f"tv_{entity.name.lower()}"

        return self.template.render(
            entity=entity,
            schema=entity.schema,
            table_name=table_name
        )