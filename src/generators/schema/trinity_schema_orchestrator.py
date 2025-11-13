"""
Trinity Schema Orchestrator

Integrates all Trinity pattern generators for complete schema generation:
- Base tables (tb_*) with enhanced type system
- Table views (tv_*) with JSONB and auto-refresh
- Trinity helper functions (UUID ↔ INTEGER conversion)
- Vector embeddings with HNSW indexes
- Full-text search with GIN indexes
- FraiseQL annotations for all objects
"""

from dataclasses import dataclass
from typing import List
from src.core.ast_models import Entity
from src.generators.schema.base_table_generator import BaseTableGenerator
from src.generators.schema.enhanced_table_view_generator import EnhancedTableViewGenerator
from src.generators.schema.trinity_helper_generator import TrinityHelperGenerator
from src.generators.schema.vector_generator import VectorGenerator
from src.generators.schema.fulltext_generator import FullTextGenerator
from src.generators.fraiseql.fraiseql_annotator import FraiseQLAnnotator


@dataclass
class FileSpec:
    """Specification for a generated file"""
    code: str
    name: str
    content: str
    layer: str  # "write_side", "read_side", "helpers", "search"


class TrinitySchemaOrchestrator:
    """Orchestrates complete Trinity pattern schema generation"""

    def __init__(self):
        self.base_table_gen = BaseTableGenerator()
        self.table_view_gen = EnhancedTableViewGenerator()
        self.trinity_helper_gen = TrinityHelperGenerator()
        self.vector_gen = VectorGenerator()
        self.fulltext_gen = FullTextGenerator()
        self.fraiseql_annotator = FraiseQLAnnotator()

    def generate_schema(self, entities: List[Entity]) -> List[FileSpec]:
        """
        Generate complete Trinity schema for all entities

        Args:
            entities: List of entities to generate schema for

        Returns:
            List of file specifications for all generated SQL files
        """
        files = []

        for entity in entities:
            # 1. Base table (write-side)
            base_table_sql = self.base_table_gen.generate(entity)
            base_table_annotations = self.fraiseql_annotator.annotate_table(entity)
            base_field_annotations = self.fraiseql_annotator.annotate_fields(entity)

            full_base_table_sql = base_table_sql + "\n\n" + base_table_annotations + "\n\n" + base_field_annotations

            files.append(FileSpec(
                code=f"tb_{entity.name.lower()}",
                name=f"tb_{entity.name.lower()}",
                content=full_base_table_sql,
                layer="write_side"
            ))

            # 2. Table view (read-side)
            table_view_sql = self.table_view_gen.generate(entity)
            table_view_annotations = self.fraiseql_annotator.annotate_table_view(entity)

            full_table_view_sql = table_view_sql + "\n\n" + table_view_annotations

            files.append(FileSpec(
                code=f"tv_{entity.name.lower()}",
                name=f"tv_{entity.name.lower()}",
                content=full_table_view_sql,
                layer="read_side"
            ))

            # 3. Trinity helper functions
            helper_sql = self.trinity_helper_gen.generate(entity)
            helper_annotations = self.fraiseql_annotator.annotate_helper_functions(entity)

            full_helper_sql = helper_sql + "\n\n" + helper_annotations

            files.append(FileSpec(
                code=f"{entity.name.lower()}_helpers",
                name=f"{entity.name.lower()}_helpers",
                content=full_helper_sql,
                layer="helpers"
            ))

            # 4. Vector search features
            vector_sql = self.vector_gen.generate(entity)

            if vector_sql:
                files.append(FileSpec(
                    code=f"{entity.name.lower()}_vector_search",
                    name=f"{entity.name.lower()}_vector_search",
                    content=vector_sql,
                    layer="search"
                ))

            # 5. Full-text search features
            fulltext_sql = self.fulltext_gen.generate(entity)

            if fulltext_sql:
                search_annotations = self.fraiseql_annotator.annotate_search_functions(entity)
                full_search_sql = fulltext_sql + "\n\n" + search_annotations

                files.append(FileSpec(
                    code=f"{entity.name.lower()}_text_search",
                    name=f"{entity.name.lower()}_text_search",
                    content=full_search_sql,
                    layer="search"
                ))

        return files