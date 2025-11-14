"""
Vector schema generator for FraiseQL 1.5 auto-discovery

Generates PostgreSQL vector columns and HNSW indexes.
FraiseQL 1.5 auto-discovers these and provides GraphQL vector operators.
"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import EntityDefinition


class VectorGenerator:
    """
    Generates vector schema (columns + indexes) for FraiseQL 1.5

    SpecQL creates the PostgreSQL schema with pgvector columns and HNSW indexes.
    FraiseQL 1.5 auto-discovers these columns and provides GraphQL operators.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = (
                Path(__file__).parent.parent.parent.parent / "templates" / "sql"
            )

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("vector_features.sql.j2")

    def generate(self, entity: EntityDefinition) -> str:
        """
        Generate vector schema (columns + indexes) for FraiseQL 1.5

        Creates PostgreSQL vector columns and HNSW indexes.
        FraiseQL 1.5 auto-discovers these and exposes GraphQL vector operators.

        Args:
            entity: Entity to generate vector features for

        Returns:
            SQL for vector columns and HNSW indexes
        """
        if "semantic_search" not in (entity.features or []):
            return ""

        # Generate schema only - FraiseQL 1.5 handles all queries and operations
        parts = [
            self._generate_columns(entity),
            self._generate_indexes(entity),
        ]

        return "\n\n".join(filter(None, parts))

    def _generate_columns(self, entity: EntityDefinition) -> str:
        """Generate ALTER TABLE statements for vector columns"""
        return self.template.render(
            entity=entity, schema=entity.schema, section="columns"
        )

    def _generate_indexes(self, entity: EntityDefinition) -> str:
        """Generate HNSW indexes for vector similarity search"""
        return self.template.render(
            entity=entity, schema=entity.schema, section="indexes"
        )
