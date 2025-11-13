"""
Table View Generator

Generates tv_ (table view) tables for CQRS read-optimized pattern.
These denormalized tables expose data to FraiseQL for auto-GraphQL generation.

Key Innovation: JSONB composition from related tv_ tables (not tb_ tables)
"""

from src.core.ast_models import EntityDefinition, ExtraFilterColumn, IncludeRelation


class TableViewGenerator:
    """Generate tv_ table schema and refresh functions."""

    def __init__(self, entity: EntityDefinition, all_entities: dict[str, EntityDefinition]):
        self.entity = entity
        self.all_entities = all_entities  # For resolving references

    def should_generate(self) -> bool:
        """Determine if tv_ should be generated."""
        return self.entity.should_generate_table_view

    def _has_vector_search(self) -> bool:
        """Check if entity has semantic search enabled"""
        return "semantic_search" in (self.entity.features or [])

    def _has_fulltext_search(self) -> bool:
        """Check if entity has full-text search enabled"""
        return "full_text_search" in (self.entity.features or [])

    def generate_schema(self) -> str:
        """Generate complete tv_ table DDL."""
        if not self.should_generate():
            return ""

        parts = []

        # Table creation
        parts.append(self._generate_table_ddl())

        # Indexes
        parts.append(self._generate_indexes())

        # Refresh function
        parts.append(self._generate_refresh_function())

        return "\n\n".join(parts)

    def _generate_table_ddl(self) -> str:
        """Generate CREATE TABLE statement for tv_."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        columns = []

        # Trinity pattern
        columns.append(f"pk_{entity_lower} INTEGER PRIMARY KEY")
        columns.append("id UUID NOT NULL UNIQUE")
        columns.append("tenant_id UUID NOT NULL")

        # Foreign keys (INTEGER + UUID)
        for field_name, field in self.entity.fields.items():
            if field.is_reference():
                # Use field name for FK column (e.g., author -> fk_author)
                # This supports multiple refs to the same entity
                field_lower = field_name.lower()

                # INTEGER FK for JOINs
                columns.append(f"fk_{field_lower} INTEGER")

                # UUID FK for filtering
                columns.append(f"{field_lower}_id UUID")

        # Hierarchy path (if hierarchical)
        if self._is_entity_hierarchical():
            columns.append("path LTREE NOT NULL")

        # Extra filter columns
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                col_type = self._infer_column_type(col)
                columns.append(f"{col.name} {col_type}")

        # 🆕 Vector embedding column (if semantic search enabled)
        if self._has_vector_search():
            columns.append("embedding vector(384)")

        # 🆕 Full-text search vector (if full-text search enabled)
        if self._has_fulltext_search():
            columns.append("search_vector tsvector")

        # JSONB data column
        columns.append("data JSONB NOT NULL")

        # Metadata
        columns.append("refreshed_at TIMESTAMPTZ DEFAULT now()")

        column_defs = ",\n    ".join(columns)
        return f"""
-- Table view for {self.entity.name} (read-optimized, denormalized)
CREATE TABLE {schema}.tv_{entity_lower} (
    {column_defs}
);
""".strip()

    def _generate_indexes(self) -> str:
        """Generate indexes for tv_ table."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema
        indexes = []

        # Tenant index (always)
        indexes.append(
            f"CREATE INDEX idx_tv_{entity_lower}_tenant ON {schema}.tv_{entity_lower}(tenant_id);"
        )

        # UUID foreign key indexes (auto-inferred)
        for field_name, field in self.entity.fields.items():
            if field.is_reference():
                field_lower = field_name.lower()

                indexes.append(
                    f"CREATE INDEX idx_tv_{entity_lower}_{field_lower}_id "
                    f"ON {schema}.tv_{entity_lower}({field_lower}_id);"
                )

        # Path index (if hierarchical)
        if self._is_entity_hierarchical():
            indexes.append(
                f"CREATE INDEX idx_tv_{entity_lower}_path "
                f"ON {schema}.tv_{entity_lower} USING GIST(path);"
            )

        # Extra filter column indexes
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                index_type = col.index_type.upper()

                if index_type == "GIN_TRGM":
                    # Trigram index for partial text matching
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIN({col.name} gin_trgm_ops);"
                    )
                elif index_type == "GIN":
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIN({col.name});"
                    )
                elif index_type == "GIST":
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower} "
                        f"USING GIST({col.name});"
                    )
                else:  # BTREE (default)
                    indexes.append(
                        f"CREATE INDEX idx_tv_{entity_lower}_{col.name} "
                        f"ON {schema}.tv_{entity_lower}({col.name});"
                    )

        # 🆕 Vector embedding index (HNSW for similarity search)
        if self._has_vector_search():
            indexes.append(
                f"CREATE INDEX idx_tv_{entity_lower}_embedding_hnsw "
                f"ON {schema}.tv_{entity_lower} "
                f"USING hnsw (embedding vector_cosine_ops);"
            )

        # 🆕 Full-text search index (GIN)
        if self._has_fulltext_search():
            indexes.append(
                f"CREATE INDEX idx_tv_{entity_lower}_search_vector "
                f"ON {schema}.tv_{entity_lower} "
                f"USING gin (search_vector);"
            )

        # GIN index for JSONB queries (always)
        indexes.append(
            f"CREATE INDEX idx_tv_{entity_lower}_data "
            f"ON {schema}.tv_{entity_lower} USING GIN(data);"
        )

        return "\n".join(indexes)

    def _generate_refresh_function(self) -> str:
        """Generate refresh_tv_{entity}() function with JSONB composition."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        # Build SELECT columns
        select_columns = self._build_select_columns()

        # Build FROM clause with JOINs to tv_ tables
        from_clause = self._build_from_clause_with_tv_joins()

        # Build SELECT values
        select_values = self._build_select_values()

        return f"""
-- Refresh function for tv_{entity_lower}
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION {schema}.refresh_tv_{entity_lower}(
    p_pk_{entity_lower} INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM {schema}.tv_{entity_lower}
    WHERE p_pk_{entity_lower} IS NULL OR pk_{entity_lower} = p_pk_{entity_lower};

    -- Insert refreshed data
    INSERT INTO {schema}.tv_{entity_lower} (
        {", ".join(select_columns)}
    )
    SELECT
        {select_values}
    {from_clause}
    WHERE base.deleted_at IS NULL
      AND (p_pk_{entity_lower} IS NULL OR base.pk_{entity_lower} = p_pk_{entity_lower});
END;
$$ LANGUAGE plpgsql;
""".strip()

    def _infer_column_type(self, col: ExtraFilterColumn) -> str:
        """Infer SQL type for extra filter column."""
        if col.type:
            # Explicit type provided
            return col.type.upper()

        # Infer from source field if available
        if col.source:
            # Source like "author.name" - need to resolve type
            # For now, default to TEXT
            return "TEXT"

        # Try to find field in entity
        if col.name in self.entity.fields:
            field = self.entity.fields[col.name]
            return self._map_field_type_to_sql(field.type_name)

        # Default
        return "TEXT"

    def _map_field_type_to_sql(self, field_type: str) -> str:
        """Map SpecQL type to SQL type."""
        mapping = {
            "text": "TEXT",
            "integer": "INTEGER",
            "decimal": "DECIMAL",
            "boolean": "BOOLEAN",
            "timestamp": "TIMESTAMPTZ",
            "date": "DATE",
            "jsonb": "JSONB",
        }
        return mapping.get(field_type.lower(), "TEXT")

    def _extract_ref_entity(self, type_name: str) -> str:
        """Extract entity name from ref(Entity) type."""
        # ref(User) -> User
        if type_name.startswith("ref(") and type_name.endswith(")"):
            return type_name[4:-1]
        return type_name  # fallback

    def _is_entity_hierarchical(self) -> bool:
        """Determine if an entity is hierarchical by checking for self-referencing parent fields."""
        for field_name, field_def in self.entity.fields.items():
            if field_def.is_reference():
                # Check if this field references the same entity (parent relationship)
                ref_entity = self._extract_ref_entity(field_def.type_name)
                if ref_entity == self.entity.name:
                    return True
        return False

    def _build_select_columns(self) -> list[str]:
        """Build list of columns for INSERT."""
        entity_lower = self.entity.name.lower()
        columns = [f"pk_{entity_lower}", "id", "tenant_id"]

        # FK columns (INTEGER + UUID)
        for field_name, field in self.entity.fields.items():
            if field.is_reference():
                # Use field name for FK columns
                field_lower = field_name.lower()
                columns.append(f"fk_{field_lower}")
                columns.append(f"{field_lower}_id")

        # Path (if hierarchical)
        if self._is_entity_hierarchical():
            columns.append("path")

        # Extra filter columns
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                columns.append(col.name)

        # 🆕 Vector columns
        if self._has_vector_search():
            columns.append("embedding")

        if self._has_fulltext_search():
            columns.append("search_vector")

        # Data column
        columns.append("data")

        return columns

    def _build_from_clause_with_tv_joins(self) -> str:
        """Build FROM clause with JOINs to tv_ tables (composition!)."""
        entity_lower = self.entity.name.lower()
        schema = self.entity.schema

        lines = [f"FROM {schema}.tb_{entity_lower} base"]

        # Join to tv_ tables (composition!)
        for field_name, field in self.entity.fields.items():
            if field.is_reference():
                # Get referenced entity (prefer field.reference_entity, fallback to parsing type_name)
                ref_entity = field.reference_entity or self._extract_ref_entity(field.type_name)
                ref_lower = ref_entity.lower()
                field_lower = field_name.lower()

                # Get referenced entity schema (use field.reference_schema for cross-schema refs)
                # Fallback to _get_entity_schema if reference_schema not set
                ref_schema = field.reference_schema or self._get_entity_schema(ref_entity)

                # Join to tv_ table (composition!)
                join_type = "INNER" if not field.nullable else "LEFT"
                lines.append(
                    f"{join_type} JOIN {ref_schema}.tv_{ref_lower} tv_{ref_lower} "
                    f"ON tv_{ref_lower}.pk_{ref_lower} = base.fk_{field_lower}"
                )

        return "\n    ".join(lines)

    def _build_select_values(self) -> str:
        """Build SELECT values for INSERT."""
        entity_lower = self.entity.name.lower()
        values = [f"base.pk_{entity_lower}", "base.id", "base.tenant_id"]

        # FK values
        for field_name, field in self.entity.fields.items():
            if field.is_reference():
                # Get referenced entity (prefer field.reference_entity, fallback to parsing type_name)
                ref_entity = field.reference_entity or self._extract_ref_entity(field.type_name)
                ref_lower = ref_entity.lower()
                field_lower = field_name.lower()

                # INTEGER FK
                values.append(f"base.fk_{field_lower}")

                # UUID FK (from tv_ table)
                values.append(f"tv_{ref_lower}.id AS {field_lower}_id")

        # Path (if hierarchical)
        if self._is_entity_hierarchical():
            values.append("base.path")

        # Extra filter columns
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                if col.source:
                    # Nested extraction (e.g., author.name)
                    parts = col.source.split(".")
                    if len(parts) == 2:
                        entity_name, field_name = parts
                        values.append(
                            f"tv_{entity_name.lower()}.data->>'{field_name}' AS {col.name}"
                        )
                    else:
                        values.append(f"base.{col.name}")
                else:
                    # Direct field from base table
                    values.append(f"base.{col.name}")

        # 🆕 Vector columns (copied from tb_)
        if self._has_vector_search():
            values.append("base.embedding")

        if self._has_fulltext_search():
            values.append("base.search_vector")

        # JSONB data
        values.append(f"{self._build_jsonb_data()} AS data")

        return ",\n        ".join(values)

    def _build_jsonb_data(self) -> str:
        """Build JSONB data construction."""
        parts = []

        # Add related entities first (compose from tv_.data)
        # This ensures wildcard tv_.data appears before jsonb_build_object in SQL
        config = self.entity.table_views
        if config and config.include_relations:
            for rel in config.include_relations:
                parts.append(self._build_relation_jsonb(rel))
        else:
            # No explicit config - include all ref fields with all data
            for field_name, field in self.entity.fields.items():
                if field.is_reference():
                    # Get referenced entity (prefer field.reference_entity, fallback to parsing type_name)
                    ref_entity = field.reference_entity or self._extract_ref_entity(field.type_name)
                    ref_lower = ref_entity.lower()

                    # Include full tv_.data
                    parts.append(f"'{field_name}', tv_{ref_lower}.data")

        # Add entity's own fields after relations
        for field_name, field in self.entity.fields.items():
            if not field.is_reference():
                # Scalar field
                parts.append(f"'{field_name}', base.{field_name}")

        return f"jsonb_build_object({', '.join(parts)})"

    def _build_relation_jsonb(self, rel: "IncludeRelation") -> str:
        """Build JSONB for a single relation (explicit field selection)."""
        # Find the matching field - support both field name and entity type matching
        field_name_for_json = None
        ref_entity = None

        # Try exact field name match first
        for fname, field in self.entity.fields.items():
            if field.is_reference() and fname == rel.entity_name:
                field_name_for_json = fname
                # Get referenced entity (prefer field.reference_entity, fallback to parsing type_name)
                ref_entity = field.reference_entity or self._extract_ref_entity(field.type_name)
                break

        # If no exact match, try matching by entity type (e.g., "User" matches "author: ref(User)")
        if ref_entity is None:
            for fname, field in self.entity.fields.items():
                if field.is_reference():
                    # Get referenced entity (prefer field.reference_entity, fallback to parsing type_name)
                    entity_type = field.reference_entity or self._extract_ref_entity(field.type_name)
                    if entity_type == rel.entity_name:
                        field_name_for_json = fname
                        ref_entity = entity_type
                        break

        # Fallback to relation entity_name
        if ref_entity is None:
            ref_entity = rel.entity_name
            field_name_for_json = rel.entity_name

        table_alias = f"tv_{ref_entity.lower()}"

        if rel.fields == ["*"]:
            # Include all fields from tv_.data
            return f"'{field_name_for_json}', {table_alias}.data"
        else:
            # Extract specific fields from tv_.data
            field_extractions = []
            for field in rel.fields:
                field_extractions.append(f"'{field}', {table_alias}.data->'{field}'")

            # Handle nested relations
            if rel.include_relations:
                for nested in rel.include_relations:
                    # Nested relations are already composed in parent tv_.data
                    field_extractions.append(
                        f"'{nested.entity_name}', {table_alias}.data->'{nested.entity_name}'"
                    )

            return f"""'{field_name_for_json}', jsonb_build_object({", ".join(field_extractions)})"""

    def _get_entity_schema(self, entity_name: str) -> str:
        """Get schema for referenced entity."""
        if entity_name in self.all_entities:
            return self.all_entities[entity_name].schema
        # Default to same schema
        return self.entity.schema
