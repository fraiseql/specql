"""
PostgreSQL Table Generator (Team B)
Generates DDL for Trinity pattern tables from Entity AST
"""

from typing import Any

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Entity
from src.generators.comment_generator import CommentGenerator
from src.generators.constraint_generator import ConstraintGenerator
from src.generators.index_generator import IndexGenerator
from src.generators.schema.schema_registry import SchemaRegistry
from src.utils.safe_slug import safe_slug, safe_table_name


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

    def generate_table_ddl(self, entity: Entity) -> str:
        """
        Generate complete CREATE TABLE DDL for entity

        Args:
            entity: Parsed Entity AST from Team A parser

        Returns:
            Complete PostgreSQL DDL as string
        """
        # Prepare template context
        context = self._prepare_template_context(entity)

        # Load and render template
        template = self.env.get_template("table.sql.j2")
        return template.render(**context)

    def _prepare_template_context(self, entity: Entity) -> dict[str, Any]:
        """Prepare context dictionary for Jinja2 template"""

        # Determine multi-tenancy requirements based on schema
        is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

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

        # Build context
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_code": (
                    entity.organization.table_code
                    if entity.organization
                    else entity.name[:3].upper()
                ),
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
            }
        }

        return context

    def _is_tenant_specific_schema(self, schema: str) -> bool:
        """
        Determine if schema is tenant-specific (needs tenant_id) or common (shared)

        Uses domain registry to check multi_tenant flag
        """
        return self.schema_registry.is_multi_tenant(schema)

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
        """
        Generate CREATE INDEX statements

        Args:
            entity: Parsed Entity AST

        Returns:
            Index DDL statements
        """
        indexes = []

        entity_name_slug = safe_slug(entity.name)

        # Index on UUID (for external API lookups)
        # Index naming follows table convention: idx_tb_{entity}_{field}
        indexes.append(
            f"""CREATE INDEX idx_tb_{entity_name_slug}_id
    ON {entity.schema}.{safe_table_name(entity.name)} USING btree (id);"""
        )

        # Index on foreign keys
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                fk_name = f"fk_{field_name}"
                indexes.append(
                    f"""CREATE INDEX idx_tb_{entity_name_slug}_{safe_slug(field_name)}
    ON {entity.schema}.{safe_table_name(entity.name)} USING btree ({fk_name});"""
                )

        # Index on enum fields (for filtering)
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "enum" and field_def.values:
                indexes.append(
                    f"""CREATE INDEX idx_tb_{entity_name_slug}_{safe_slug(field_name)}
    ON {entity.schema}.{safe_table_name(entity.name)} USING btree ({field_name});"""
                )

        return "\n\n".join(indexes)

    def generate_field_comments(self, entity: Entity) -> list[str]:
        """Generate COMMENT ON COLUMN statements for all fields"""
        return self.comment_generator.generate_all_field_comments(entity)

    def generate_indexes_for_rich_types(self, entity: Entity) -> list[str]:
        """Generate indexes for rich type fields"""
        return self.index_generator.generate_indexes_for_rich_types(entity)

    def generate_complete_ddl(self, entity: Entity) -> str:
        """Generate complete DDL including table, indexes, and comments"""

        ddl_parts = []

        # 1. CREATE TABLE
        ddl_parts.append(self.generate_table_ddl(entity))

        # 2. CREATE INDEX statements (standard indexes)
        indexes = self.generate_indexes_ddl(entity)
        if indexes:
            ddl_parts.append(indexes)

        # 3. CREATE INDEX statements (rich type indexes)
        rich_type_indexes = self.generate_indexes_for_rich_types(entity)
        if rich_type_indexes:
            ddl_parts.append("\n\n".join(rich_type_indexes))

        # 4. COMMENT ON statements
        comments = self.comment_generator.generate_all_field_comments(entity)
        if comments:
            ddl_parts.extend(comments)

        # 5. Table comment
        table_comment = self.comment_generator.generate_table_comment(entity)
        ddl_parts.append(table_comment)

        return "\n\n".join(ddl_parts)
