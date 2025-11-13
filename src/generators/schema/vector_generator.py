"""Vector embedding generator for semantic search"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import Entity


class VectorGenerator:
    """Generates vector embedding columns and similarity search functions"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("vector_features.sql.j2")

    def generate(self, entity: Entity) -> str:
        """
        Generate vector features if entity has semantic_search enabled

        Args:
            entity: Entity to generate vector features for

        Returns:
            SQL for vector columns, indexes, and search functions
        """
        # For now, always generate vector features (in a real implementation,
        # this would check entity features)
        return self.template.render(
            entity=entity,
            schema=entity.schema
        )

    def generate_column(self, entity: Entity) -> str:
        """Generate ALTER TABLE to add embedding column"""
        return f"ALTER TABLE {entity.schema}.tb_{entity.name.lower()} ADD COLUMN embedding vector(384);"

    def generate_index(self, entity: Entity) -> str:
        """Generate HNSW index for vector similarity"""
        return f"""CREATE INDEX idx_tb_{entity.name.lower()}_embedding_hnsw
ON {entity.schema}.tb_{entity.name.lower()}
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);"""

    def generate_tv_column(self, entity: Entity) -> str:
        """Generate ALTER TABLE for table view embedding"""
        return f"ALTER TABLE {entity.schema}.tv_{entity.name.lower()} ADD COLUMN embedding vector(384);"

    def generate_search_function(self, entity: Entity) -> str:
        """Generate similarity search function"""
        return self.generate(entity)