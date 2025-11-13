"""Vector embedding generator for semantic search"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import EntityDefinition


class VectorGenerator:
    """Generates vector embedding columns and similarity search functions"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("vector_features.sql.j2")

    def generate(self, entity: EntityDefinition) -> str:
        """
        Generate vector features if entity has semantic_search enabled

        Args:
            entity: Entity to generate vector features for

        Returns:
            SQL for vector columns, indexes, and search functions
        """
        if "semantic_search" not in (entity.features or []):
            return ""

        # Always generate columns and indexes
        parts = []
        parts.append(self._generate_columns(entity))
        parts.append(self._generate_indexes(entity))

        # Only generate search functions if enabled
        if getattr(entity, 'search_functions', True):  # Default True
            parts.append(self._generate_search_function(entity))

        return "\n\n".join(filter(None, parts))

    def _generate_columns(self, entity: EntityDefinition) -> str:
        """Generate ALTER TABLE statements for vector columns"""
        return self.template.render(
            entity=entity,
            schema=entity.schema,
            section="columns"
        )

    def _generate_indexes(self, entity: EntityDefinition) -> str:
        """Generate HNSW indexes"""
        return self.template.render(
            entity=entity,
            schema=entity.schema,
            section="indexes"
        )

    def _generate_search_function(self, entity: EntityDefinition) -> str:
        """Generate similarity search function"""
        return self.template.render(
            entity=entity,
            schema=entity.schema,
            section="function"
        )

    # Legacy methods for backward compatibility
    def generate_column(self, entity: EntityDefinition) -> str:
        """Generate ALTER TABLE to add embedding column"""
        return f"ALTER TABLE {entity.schema}.tb_{entity.name.lower()} ADD COLUMN embedding vector(384);"

    def generate_index(self, entity: EntityDefinition) -> str:
        """Generate HNSW index for vector similarity"""
        return f"""CREATE INDEX idx_tb_{entity.name.lower()}_embedding_hnsw
ON {entity.schema}.tb_{entity.name.lower()}
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);"""

    def generate_tv_column(self, entity: EntityDefinition) -> str:
        """Generate ALTER TABLE for table view embedding"""
        return f"ALTER TABLE {entity.schema}.tv_{entity.name.lower()} ADD COLUMN embedding vector(384);"

    def generate_search_function(self, entity: EntityDefinition) -> str:
        """Generate similarity search function"""
        return self._generate_search_function(entity)