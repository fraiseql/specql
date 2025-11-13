"""
Trinity Helper Function Generator

Generates utility functions for UUID ↔ INTEGER conversion in the Trinity pattern:
- {entity}_pk(): Convert UUID or TEXT identifier to INTEGER primary key
- {entity}_id(): Convert INTEGER primary key to UUID
"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import Entity


class TrinityHelperGenerator:
    """Generates Trinity pattern helper functions for UUID ↔ INTEGER conversion"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("trinity_helpers.sql.j2")

    def generate(self, entity: Entity) -> str:
        """
        Generate Trinity helper functions for entity

        Args:
            entity: Entity to generate helpers for

        Returns:
            SQL with {entity}_pk() and {entity}_id() functions
        """
        # Generate both pk and id functions
        pk_function = self.template.render(
            entity=type('Entity', (), {
                'schema': entity.schema,
                'name': entity.name,
                'pk_column': f'pk_{entity.name.lower()}',
                'table_name': f'tb_{entity.name.lower()}'
            })(),
            function_type="pk",
            is_tenant_specific=False
        )

        id_function = self.template.render(
            entity=type('Entity', (), {
                'schema': entity.schema,
                'name': entity.name,
                'pk_column': f'pk_{entity.name.lower()}',
                'table_name': f'tb_{entity.name.lower()}'
            })(),
            function_type="id",
            is_tenant_specific=False
        )

        return pk_function + "\n\n" + id_function