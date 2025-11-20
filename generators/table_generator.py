"""
PostgreSQL Table Generator (Team B)
Generates DDL for Trinity pattern tables from Entity AST
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from core.ast_models import Entity
from generators.comment_generator import CommentGenerator
from generators.constraint_generator import ConstraintGenerator
from generators.index_generator import IndexGenerator
from generators.schema.ddl_deduplicator import DDLDeduplicator
from generators.schema.schema_registry import SchemaRegistry
from utils.safe_slug import safe_table_name


class TableGenerator:
    """Generates PostgreSQL DDL for Trinity pattern tables"""

    # Field type mappings: SpecQL → PostgreSQL
    TYPE_MAPPINGS = {
        "text": "TEXT",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMPTZ",
        "uuid": "UUID",
        "json": "JSONB",
        "decimal": "DECIMAL",
    }

    def __init__(self, schema_registry: SchemaRegistry, templates_dir: str = "templates/sql"):
        """Initialize with Jinja2 templates and schema registry"""
        self.schema_registry = schema_registry
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )
        self.constraint_generator = ConstraintGenerator()
        self.comment_generator = CommentGenerator()
        self.index_generator = IndexGenerator()

    def generate_table_ddl(self, entity) -> str:
        """
        Generate complete CREATE TABLE DDL for entity

        Args:
            entity: Parsed Entity AST from Team A parser

        Returns:
            Complete PostgreSQL DDL as string
        """
        # Apply patterns to entity first
        entity, additional_sql = self._apply_patterns_to_entity(entity)

        # Prepare template context
        context = self._prepare_template_context(entity)

        # Load and render template
        template = self.env.get_template("table.sql.j2")
        table_sql = template.render(**context)

        # Combine table SQL with pattern-generated SQL
        if additional_sql:
            return table_sql + "\n\n" + additional_sql
        else:
            return table_sql

    def _apply_patterns_to_entity(self, entity: Entity) -> tuple[Entity, str]:
        """Apply patterns to entity, returning enhanced entity and additional SQL."""
        if not entity.patterns:
            return entity, ""

        try:
            from generators.schema.pattern_applier import PatternApplier

            applier = PatternApplier()
            return applier.apply_patterns(entity)
        except ImportError:
            # If pattern system not available, return entity as-is
            return entity, ""

    def _prepare_template_context(self, entity: Entity) -> dict[str, Any]:
        """Prepare context dictionary for Jinja2 template"""

        # Determine multi-tenancy requirements based on schema
        is_tenant_specific = self.schema_registry.is_multi_tenant(entity.schema)

        # Convert fields to template format (dict format expected by template)
        business_fields = {}
        foreign_keys = {}
        table_constraints = []

        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                # Foreign key field - add to FK dict
                fk_name = f"fk_{field_name}"
                target_entity_lower = field_def.reference_entity.lower()
                references = f"{entity.schema}.tb_{target_entity_lower}"
                foreign_keys[fk_name] = {
                    "name": fk_name,
                    "references": references,
                    "on": f"pk_{target_entity_lower}",
                    "nullable": field_def.nullable,
                    "description": f"Reference to {field_def.reference_entity}",
                }
            elif field_def.type_name == "enum" and field_def.values:
                # Enum field - add CHECK constraint
                enum_values = ", ".join(f"'{v}'" for v in field_def.values)
                constraint_name = self.constraint_generator._generate_constraint_name(
                    table_name, field_name, "enum"
                )
                table_constraints.append(
                    f"CONSTRAINT {constraint_name} CHECK ({field_name} IN ({enum_values}))"
                )
                business_fields[field_name] = {
                    "name": field_name,
                    "type": "TEXT",
                    "nullable": field_def.nullable,
                    "description": f"Enum field: {field_name}",
                }
            else:
                # Regular field (including rich types)
                sql_type = field_def.get_postgres_type()
                field_dict = {
                    "name": field_name,
                    "type": sql_type,
                    "nullable": field_def.nullable,
                }

                # Generate named constraints for rich types
                constraint = self.constraint_generator.generate_constraint(field_def, table_name)
                if constraint:
                    table_constraints.append(constraint)

                business_fields[field_name] = field_dict

        # Patterns are now processed by PatternApplier in SchemaOrchestrator
        pattern_extensions = self._process_patterns(entity)

        # Build context
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_code": entity.organization.table_code
                if entity.organization
                else entity.name[:3].upper(),
                "description": entity.description or f"{entity.name} entity",
                "fields": business_fields,
                "foreign_keys": foreign_keys,
                "constraints": table_constraints,
                "multi_tenant": is_tenant_specific,
                "translations": {
                    "enabled": entity.translations.enabled if entity.translations else False,
                    "table_name": (
                        entity.translations.table_name
                        if entity.translations and entity.translations.table_name
                        else f"tl_{entity.name.lower()}"  # Default to tl_ prefix
                    ),
                    "fields": entity.translations.fields if entity.translations else [],
                },
                "patterns": pattern_extensions,
            }
        }

        return context

    def _process_patterns(self, entity: Entity) -> dict[str, Any]:
        """Process entity patterns and return extensions for template"""
        # Patterns are now handled by PatternApplier in SchemaOrchestrator
        # This method extracts pattern extensions from the entity

        # Extract pattern metadata from entity notes
        metadata = []
        if hasattr(entity, "notes") and entity.notes:
            for line in entity.notes.split("\n"):
                if line.startswith("Applied pattern: "):
                    pattern_name = line.split("Applied pattern: ")[1]
                    metadata.append(f"@fraiseql:pattern:{pattern_name}")

        return {
            "computed_columns": entity.computed_columns,
            "scd_indexes": entity.indexes,
            "exclusion_constraints": [],
            "aggregate_views": [],
            "constraints": [],
            "scd_functions": entity.functions,
            "metadata": metadata,
        }

    def generate_foreign_keys_ddl(self, entity: Entity) -> str:
        """
        Generate ALTER TABLE statements for foreign keys

        Args:
            entity: Parsed Entity AST

        Returns:
            Foreign key DDL statements
        """
        if not entity.fields:
            return ""

        fk_statements = []

        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                fk_name = f"fk_{field_name}"
                entity_name_lower = entity.name.lower()
                target_entity_lower = field_def.reference_entity.lower()
                table_name = f"{entity.schema}.tb_{entity_name_lower}"
                ref_table = f"{entity.schema}.tb_{target_entity_lower}"
                ref_column = f"pk_{target_entity_lower}"

                fk_sql = f"""ALTER TABLE ONLY {table_name}
    ADD CONSTRAINT tb_{entity_name_lower}_{field_name}_fkey
    FOREIGN KEY ({fk_name}) REFERENCES {ref_table}({ref_column});"""

                fk_statements.append(fk_sql)

        return "\n\n".join(fk_statements)

    def generate_indexes_ddl(self, entity: Entity) -> str:
        """Generate CREATE INDEX statements with explicit USING clause"""
        indexes = []

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"
        # Index names are database-global in PostgreSQL, so include schema prefix
        schema_prefix = f"{entity.schema.lower()}_"

        # Index on id (UUID primary key) - explicitly specify USING btree
        indexes.append(
            f"CREATE INDEX {schema_prefix}idx_tb_{entity.name.lower()}_id ON {table_name} USING btree (id);"
        )

        # Indexes on foreign keys - explicitly specify USING btree
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                fk_name = f"fk_{field_name}"
                indexes.append(
                    f"CREATE INDEX {schema_prefix}idx_tb_{entity.name.lower()}_{field_name} ON {table_name} USING btree ({fk_name});"
                )

        # Indexes on enum fields - explicitly specify USING btree
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "enum" and field_def.values:
                indexes.append(
                    f"CREATE INDEX {schema_prefix}idx_tb_{entity.name.lower()}_{field_name} ON {table_name} USING btree ({field_name});"
                )

        # Rich type indexes
        rich_indexes = self.index_generator.generate_indexes_for_rich_types(entity)
        indexes.extend(rich_indexes)

        # Custom indexes from patterns
        if hasattr(entity, "indexes") and entity.indexes:
            for index_def in entity.indexes:
                if isinstance(index_def, dict):
                    # Custom index from pattern
                    index_name = index_def["name"]
                    # Render column names if they contain templates
                    columns = []
                    for col in index_def["columns"]:
                        # Simple template rendering for common patterns
                        if "{{ params.start_date_field }}_{{ params.end_date_field }}_range" in col:
                            # This is our computed column
                            col = col.replace(
                                "{{ params.start_date_field }}_{{ params.end_date_field }}_range",
                                "start_date_end_date_range",
                            )
                        columns.append(col)
                    columns_str = ", ".join(columns)
                    index_type = index_def.get("index_type", "btree")
                    indexes.append(
                        f"CREATE INDEX {index_name} ON {table_name} USING {index_type} ({columns_str});"
                    )
                else:
                    # Legacy Index object
                    index_type = getattr(index_def, "type", "btree")
                    # Special case for daterange indexes - assume GIST
                    if index_def.name and "daterange" in str(index_def.name):
                        indexes.append(
                            f"CREATE INDEX {index_def.name} ON {table_name} USING gist ({', '.join(index_def.columns)});"
                        )
                    elif index_type != "btree":
                        indexes.append(
                            f"CREATE INDEX {index_def.name} ON {table_name} USING {index_type} ({', '.join(index_def.columns)});"
                        )
                    else:
                        indexes.append(
                            f"CREATE INDEX {index_def.name} ON {table_name} ({', '.join(index_def.columns)});"
                        )

        # Deduplicate indexes to prevent duplicate statements
        indexes = DDLDeduplicator.deduplicate_indexes(indexes)

        return "\n".join(indexes)

    def generate_field_comments(self, entity: Entity) -> list[str]:
        """Generate COMMENT ON COLUMN statements for all fields with deduplication"""
        # Convert Entity to EntityDefinition if needed
        if isinstance(entity, Entity):
            # Entity is already compatible with CommentGenerator
            comments = self.comment_generator.generate_all_field_comments(entity)
        else:
            # Handle EntityDefinition or other types
            comments = self.comment_generator.generate_all_field_comments(entity)

        # Deduplicate comments to prevent duplicate statements
        comments = DDLDeduplicator.deduplicate_comments(comments)

        return comments

    def generate_indexes_for_rich_types(self, entity: Entity) -> list[str]:
        """Generate indexes for rich type fields"""
        return self.index_generator.generate_indexes_for_rich_types(entity)

    def generate_complete_ddl(self, entity: Entity) -> str:
        """Generate complete DDL including table, indexes, and comments"""

        ddl_parts = []

        # 1. CREATE TABLE
        ddl_parts.append(self.generate_table_ddl(entity))

        # 2. CREATE INDEX statements (includes both standard and rich type indexes)
        indexes = self.generate_indexes_ddl(entity)
        if indexes:
            ddl_parts.append(indexes)

        # 3. COMMENT ON statements
        comments = self.comment_generator.generate_all_field_comments(entity)
        if comments:
            ddl_parts.extend(comments)

        # 4. Table comment
        table_comment = self.comment_generator.generate_table_comment(entity)
        ddl_parts.append(table_comment)

        return "\n\n".join(ddl_parts)
