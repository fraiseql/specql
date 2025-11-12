"""
Table View Annotator (Team D)
Generates FraiseQL annotations for tv_ tables (CQRS read-optimized views)

Purpose:
- Tell FraiseQL how to introspect tv_ tables
- Mark internal columns (pk_*, fk_*) as not exposed in GraphQL
- Annotate filter columns for efficient WHERE clauses
- Mark JSONB data column for auto-type extraction
"""

from src.core.ast_models import EntityDefinition


class TableViewAnnotator:
    """Generate FraiseQL annotations for tv_ tables"""

    def __init__(self, entity: EntityDefinition):
        self.entity = entity
        self.entity_lower = entity.name.lower()
        self.schema = entity.schema

    def generate_annotations(self) -> str:
        """
        Generate all FraiseQL annotations for tv_ table

        Returns:
            SQL COMMENT statements with @fraiseql:* annotations
        """
        if not self.entity.table_views:
            return ""  # No table views for this entity

        parts = [
            self._annotate_table(),
            self._annotate_internal_columns(),
            self._annotate_filter_columns(),
            self._annotate_data_column(),
        ]

        return "\n\n".join(filter(None, parts))

    def _annotate_table(self) -> str:
        """
        Generate table-level annotation

        Tells FraiseQL:
        - This is a materialized view (not a regular table)
        - Refreshed explicitly in mutations (not automatic)
        - This is the primary GraphQL type (not tb_* table)
        """
        return f"""-- FraiseQL table annotation
COMMENT ON TABLE {self.schema}.tv_{self.entity_lower} IS
  '@fraiseql:table source=materialized,refresh=explicit,primary=true,description=Read-optimized {self.entity.name} with denormalized relations';"""

    def _annotate_internal_columns(self) -> str:
        """
        Mark internal columns that should NOT be exposed in GraphQL

        Internal columns:
        - pk_* (INTEGER primary key - internal database ID)
        - fk_* (INTEGER foreign keys - for JOINs only)
        - refreshed_at (TIMESTAMPTZ - refresh tracking)

        Why internal:
        - GraphQL uses UUID (not INTEGER) for references
        - pk_*/fk_* are database implementation details
        - Frontend never needs to see these
        """
        lines = ["-- Internal columns (not exposed in GraphQL)"]

        # Primary key (pk_*)
        lines.append(
            f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.pk_{self.entity_lower} IS"
        )
        lines.append("  '@fraiseql:field internal=true,description=Internal primary key';")

        # Foreign key columns (fk_*)
        for field_name, field in self.entity.fields.items():
            if field.type_name.startswith("ref("):
                ref_entity = self._extract_ref_entity(field.type_name)
                field_lower = field_name.lower()

                lines.append("")
                lines.append(
                    f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.fk_{field_lower} IS"
                )
                lines.append(
                    f"  '@fraiseql:field internal=true,description=Internal FK for {ref_entity}';"
                )

        # Refresh timestamp
        lines.append("")
        lines.append(f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.refreshed_at IS")
        lines.append("  '@fraiseql:field internal=true,description=Last refresh timestamp';")

        return "\n".join(lines)

    def _annotate_filter_columns(self) -> str:
        """
        Annotate filter columns for efficient WHERE clauses

        Filter columns (UUID, indexed):
        - tenant_id - Multi-tenant isolation
        - {entity}_id - Foreign key filters (for relations)
        - Extra promoted scalars (rating, created_at, etc.)

        Why annotate:
        - FraiseQL generates WHERE clause filters
        - Index type determines query performance
        - btree = fast equality/range, gist = specialized (ltree)
        """
        lines = ["-- Filter columns (for efficient WHERE clauses)"]

        # Tenant ID (always present)
        lines.append(f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.tenant_id IS")
        lines.append(
            "  '@fraiseql:filter type=UUID,index=btree,performance=optimized,description=Multi-tenant filter';"
        )

        # UUID foreign key filters
        for field_name, field in self.entity.fields.items():
            if field.type_name.startswith("ref("):
                ref_entity = self._extract_ref_entity(field.type_name)
                field_lower = field_name.lower()

                lines.append("")
                lines.append(
                    f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.{field_lower}_id IS"
                )
                lines.append(
                    f"  '@fraiseql:filter type=UUID,relation={ref_entity},index=btree,performance=optimized,description=Filter by {ref_entity}';"
                )

        # Hierarchical path (if applicable)
        if getattr(self.entity, "hierarchical", False):
            lines.append("")
            lines.append(f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.path IS")
            lines.append(
                "  '@fraiseql:filter type=String,index=gist,format=ltree_integer,performance=optimized,description=Hierarchical path (INTEGER-based)';"
            )

        # Extra filter columns (promoted scalars)
        if self.entity.table_views and self.entity.table_views.extra_filter_columns:
            for col in self.entity.table_views.extra_filter_columns:
                graphql_type = self._map_sql_type_to_graphql(col.type or "TEXT")
                performance = "optimized" if col.index_type == "btree" else "acceptable"

                lines.append("")
                lines.append(
                    f"COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.{col.name} IS"
                )
                lines.append(
                    f"  '@fraiseql:filter type={graphql_type},index={col.index_type},performance={performance},description=Filter by {col.name}';"
                )

        return "\n".join(lines)

    def _annotate_data_column(self) -> str:
        """
        Annotate JSONB data column for type extraction

        The data column contains:
        - All entity fields (scalars, enums, etc.)
        - Denormalized relations (nested objects)
        - Complete entity representation

        expand=true tells FraiseQL:
        - Introspect JSONB structure
        - Extract field types from sample data
        - Generate nested GraphQL types
        """
        return f"""-- JSONB data column (FraiseQL extracts GraphQL types from structure)
COMMENT ON COLUMN {self.schema}.tv_{self.entity_lower}.data IS
  '@fraiseql:jsonb expand=true,description=Denormalized {self.entity.name} data with nested relations';"""

    def _extract_ref_entity(self, field_type: str) -> str:
        """Extract entity name from ref(Entity)"""
        return field_type[4:-1]

    def _map_sql_type_to_graphql(self, sql_type: str) -> str:
        """
        Map SQL type to GraphQL type

        Standard mappings:
        - TEXT → String
        - INTEGER → Int
        - NUMERIC → Float
        - BOOLEAN → Boolean
        - TIMESTAMPTZ → DateTime
        - DATE → Date
        - UUID → UUID
        - JSONB → JSON
        """
        mapping = {
            "TEXT": "String",
            "INTEGER": "Int",
            "NUMERIC": "Float",
            "DECIMAL": "Float",
            "BOOLEAN": "Boolean",
            "TIMESTAMPTZ": "DateTime",
            "DATE": "Date",
            "UUID": "UUID",
            "JSONB": "JSON",
        }
        return mapping.get(sql_type.upper(), "String")
