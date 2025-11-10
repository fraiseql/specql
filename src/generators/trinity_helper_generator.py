"""
Trinity Helper Function Generator (Team B)
Generates entity_pk() and entity_id() helper functions for UUID ↔ INTEGER resolution
"""

from jinja2 import Environment, FileSystemLoader

from src.core.ast_models import Entity
from src.generators.schema.schema_registry import SchemaRegistry
from src.utils.safe_slug import safe_slug, safe_table_name


class TrinityHelperGenerator:
    """Generates Trinity helper functions for entity resolution"""

    def __init__(self, schema_registry: SchemaRegistry, templates_dir: str = "templates/sql"):
        """Initialize with Jinja2 templates and schema registry"""
        self.schema_registry = schema_registry
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=False, lstrip_blocks=False
        )

    def generate_entity_pk_function(self, entity: Entity) -> str:
        """
        Generate entity_pk(TEXT) → INTEGER function

        Accepts UUID, identifier, or pk as text and returns INTEGER pk
        For tenant-specific schemas, also accepts tenant_id for security
        """
        is_tenant_specific = self._is_tenant_specific_schema(entity.schema)

        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
                "pk_column": f"pk_{safe_slug(entity.name)}",
            },
            "is_tenant_specific": is_tenant_specific,
        }

        template = self.env.get_template("trinity_helpers.sql.j2")
        return template.render(function_type="pk", **context)

    def generate_entity_id_function(self, entity: Entity) -> str:
        """
        Generate entity_id(INTEGER) → UUID function

        Converts pk INTEGER to UUID
        """
        context = {
            "entity": {
                "name": entity.name,
                "schema": entity.schema,
                "table_name": safe_table_name(entity.name),
                "pk_column": f"pk_{safe_slug(entity.name)}",
            }
        }

        template = self.env.get_template("trinity_helpers.sql.j2")
        return template.render(function_type="id", **context)

    def _is_tenant_specific_schema(self, schema: str) -> bool:
        """
        Determine if schema is tenant-specific (needs tenant_id filtering)

        Uses schema registry to check multi_tenant flag
        """
        return self.schema_registry.is_multi_tenant(schema)

    def generate_all_helpers(self, entity: Entity) -> str:
        """
        Generate both pk and id helper functions for entity
        """
        pk_function = self.generate_entity_pk_function(entity)
        id_function = self.generate_entity_id_function(entity)

        return f"{pk_function}\n\n{id_function}"
