"""
FraiseQL Annotator

Generates comprehensive FraiseQL annotations for all database objects:
- Base tables (tb_*) - entity definitions
- Table views (tv_*) - GraphQL types
- Helper functions - utility functions
- Search functions - query resolvers
"""

from typing import Optional
from src.core.ast_models import EntityDefinition, FieldDefinition


class FraiseQLAnnotator:
    """Generates FraiseQL annotations for database objects"""

    def annotate_table(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotation for base table"""
        return f"""COMMENT ON TABLE {entity.schema}.tb_{entity.name.lower()} IS '{entity.description}

Trinity Pattern: Normalized base table
- pk_{entity.name.lower()}: INTEGER primary key for performance
- id: UUID for stable external references
- Full audit trail (created_at, updated_at, deleted_at + by fields)

@fraiseql:entity
name: {entity.name}
trinity: base_table';"""

    def annotate_table_view(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotation for table view"""
        return f"""COMMENT ON TABLE {entity.schema}.tv_{entity.name.lower()} IS '{entity.description}

Table View: Denormalized JSONB for GraphQL
- Synced automatically from tb_{entity.name.lower()} via trigger
- data: Complete entity as JSONB for flexible querying
- refreshed_at: Last sync timestamp

@fraiseql:type
name: {entity.name}
trinity: table_view
query: true';"""

    def annotate_fields(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotations for all fields"""
        annotations = []

        for field_name, field_def in entity.fields.items():
            annotation = self._annotate_field(entity, field_name, field_def)
            if annotation:
                annotations.append(annotation)

        return "\n\n".join(annotations)

    def _annotate_field(self, entity: EntityDefinition, field_name: str, field_def: FieldDefinition) -> Optional[str]:
        """Generate FraiseQL annotation for a single field"""
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        fraiseql_type = self._map_to_fraiseql_type(field_def)

        comment_parts = [field_def.description or ""]

        if field_def.type_name == "ref":
            comment_parts.append(f"""
@fraiseql:field
name: {field_name}
type: {field_def.reference_entity}!
relation: many_to_one""")
        else:
            comment_parts.append(f"""
@fraiseql:field
name: {field_name}
type: {fraiseql_type}""")

        return f"""COMMENT ON COLUMN {table_name}.{field_name} IS '{''.join(comment_parts)}';"""

    def _map_to_fraiseql_type(self, field_def: FieldDefinition) -> str:
        """Map SpecQL field type to FraiseQL GraphQL type"""
        type_map = {
            "text": "String",
            "integer": "Int",
            "decimal": "Float",
            "boolean": "Boolean",
            "date": "Date",
            "timestamp": "DateTime",
            "json": "JSON",
            "list": "[String]",
        }

        base_type = type_map.get(field_def.type_name, "String")
        return f"{base_type}!" if not field_def.nullable else base_type

    def annotate_helper_functions(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotations for Trinity helper functions"""
        schema = entity.schema
        entity_lower = entity.name.lower()

        return f"""COMMENT ON FUNCTION {schema}.{entity_lower}_pk(TEXT) IS
'Convert {entity.name} UUID or INTEGER (as TEXT) to INTEGER primary key.

Trinity Pattern Helper: Resolves external identifiers to internal pk_{entity_lower}.

@fraiseql:helper
entity: {entity.name}
converts: UUID|INTEGER -> INTEGER';

COMMENT ON FUNCTION {schema}.{entity_lower}_id(INTEGER) IS
'Convert {entity.name} INTEGER primary key to UUID.

Trinity Pattern Helper: Resolves internal pk_{entity_lower} to external UUID.

@fraiseql:helper
entity: {entity.name}
converts: INTEGER -> UUID';"""

    def annotate_vector_column(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotation for vector column"""
        entity_lower = entity.name.lower()

        return f"""
COMMENT ON COLUMN {entity.schema}.tv_{entity_lower}.embedding IS
'Vector embedding for semantic similarity search.

@fraiseql:field
name: embedding
type: [Float!]
description: Vector embedding (384 dimensions) for similarity queries
operators: cosine_distance, l2_distance, inner_product';
"""

    def annotate_fulltext_column(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotation for full-text search column"""
        entity_lower = entity.name.lower()

        return f"""
COMMENT ON COLUMN {entity.schema}.tv_{entity_lower}.search_vector IS
'Full-text search vector (tsvector) for text queries.

@fraiseql:field
name: searchVector
type: String
description: Full-text search vector (auto-generated from text fields)
operators: matches, plain_query, phrase_query, websearch_query';
"""

    def annotate_custom_search_function(self, entity: EntityDefinition) -> str:
        """
        Annotate custom search function (only when search_functions=true)

        Note: This is legacy support. FraiseQL native operators are preferred.
        """
        entity_lower = entity.name.lower()

        return f"""
COMMENT ON FUNCTION {entity.schema}.search_{entity_lower}_by_embedding IS
'[LEGACY] Custom similarity search function.

NOTE: This function is provided for direct SQL access. For GraphQL queries,
use FraiseQL''s native vector operators instead:

  query {{
    documents(
      where: {{ embedding: {{ cosine_distance: [...] }} }}
      orderBy: {{ embedding: {{ cosine_distance: [...] }} }}
    ) {{ id, title }}
  }}

@fraiseql:query
name: search{entity.name}ByEmbedding
type: [{entity.name}!]!
deprecated: Use native vector operators instead';
"""

    def generate_annotations(self, entity: EntityDefinition) -> str:
        """Generate all FraiseQL annotations for an entity"""
        annotations = []

        # Table annotations
        annotations.append(self.annotate_table(entity))
        annotations.append(self.annotate_table_view(entity))

        # Field annotations
        annotations.append(self.annotate_fields(entity))

        # Vector column annotations (if semantic search enabled)
        if "semantic_search" in (entity.features or []):
            annotations.append(self.annotate_vector_column(entity))

        # Full-text column annotations (if full-text search enabled)
        if "full_text_search" in (entity.features or []):
            annotations.append(self.annotate_fulltext_column(entity))

        # Helper functions
        annotations.append(self.annotate_helper_functions(entity))

        # Search functions (only if enabled)
        if getattr(entity, 'search_functions', True):  # Default True
            annotations.append(self.annotate_search_functions(entity))

        return "\n\n".join(filter(None, annotations))

    def annotate_search_functions(self, entity: EntityDefinition) -> str:
        """Generate FraiseQL annotations for search functions"""
        annotations = []

        # Vector search function
        vector_annotation = f"""COMMENT ON FUNCTION {entity.schema}.search_{entity.name.lower()}_by_embedding(vector(384), INTEGER, FLOAT) IS
'Semantic similarity search for {entity.name} using vector embeddings.

Args:
- p_query_embedding: Query vector (384 dimensions)
- p_limit: Maximum results to return
- p_min_similarity: Minimum similarity threshold (0.0 - 1.0)

Returns:
- Matching entities with similarity scores, ordered by relevance

@fraiseql:query
name: search{entity.name}ByEmbedding
type: [{entity.name}!]!
args:
  - queryEmbedding: [Float!]!
  - limit: Int
  - minSimilarity: Float';"""

        annotations.append(vector_annotation)

        # Full-text search function
        text_annotation = f"""COMMENT ON FUNCTION {entity.schema}.search_{entity.name.lower()}_by_text(TEXT, INTEGER) IS
'Full-text search for {entity.name} using PostgreSQL tsvector.

Args:
- p_query: Search query (websearch syntax supported)
- p_limit: Maximum results

Returns:
- Matching entities with relevance rank

@fraiseql:query
name: search{entity.name}ByText
type: [{entity.name}!]!
args:
  - query: String!
  - limit: Int';"""

        annotations.append(text_annotation)

        return "\n\n".join(annotations)