"""Full-text search generator"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.core.ast_models import Entity


class FullTextGenerator:
    """Generates full-text search columns and functions"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "sql"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("fulltext_features.sql.j2")

    def generate(self, entity: Entity) -> str:
        """Generate full-text search features if enabled"""
        # For now, always generate full-text features (in a real implementation,
        # this would check entity features)
        # Get text fields for indexing
        text_fields = [field for field in entity.fields.values() if field.type_name == "text"]

        if not text_fields:
            return ""

        return self.template.render(
            entity=entity,
            schema=entity.schema,
            text_fields=text_fields
        )

    def generate_column(self, entity: Entity) -> str:
        """Generate tsvector column"""
        text_fields = [field for field in entity.fields.values() if field.type_name == "text"]
        field_concat = " || ' ' || ".join(f"coalesce({field.name}, '')" for field in text_fields)

        return f"""ALTER TABLE {entity.schema}.tb_{entity.name.lower()}
ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
    to_tsvector('english', {field_concat})
) STORED;"""

    def generate_index(self, entity: Entity) -> str:
        """Generate GIN index"""
        return f"""CREATE INDEX idx_tb_{entity.name.lower()}_search
ON {entity.schema}.tb_{entity.name.lower()} USING gin (search_vector);"""

    def generate_search_function(self, entity: Entity) -> str:
        """Generate search function"""
        return self.generate(entity)