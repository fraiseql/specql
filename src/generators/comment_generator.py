"""
PostgreSQL COMMENT Generator
Generates descriptive COMMENT ON statements for FraiseQL autodiscovery
"""

from typing import List, Dict, Optional
from src.core.ast_models import Entity, FieldDefinition
from src.utils.safe_slug import safe_table_name


class CommentGenerator:
    """Generates PostgreSQL COMMENT statements for rich types"""

    # Field type mappings: SpecQL → PostgreSQL composite type fields
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

    def __init__(self) -> None:
        self._type_descriptions = self._build_type_descriptions()

    def _build_type_descriptions(self) -> Dict[str, str]:
        """Build human-readable descriptions for rich types"""
        return {
            # String-based
            "email": "Email address (validated format)",
            "url": "URL/website address (validated format)",
            "phone": "Phone number in E.164 format",
            "phoneNumber": "Phone number in E.164 format",
            "ipAddress": "IP address (IPv4 or IPv6)",
            "macAddress": "MAC address (hardware identifier)",
            "markdown": "Markdown-formatted text content",
            "html": "HTML content",
            "slug": "URL-friendly identifier (lowercase with hyphens)",
            "color": "Color hex code (e.g., #FF5733)",
            # Numeric
            "money": "Monetary value (precise decimal)",
            "percentage": "Percentage value (0-100)",
            # Date/Time
            "date": "Date (YYYY-MM-DD format)",
            "datetime": "Date and time with timezone",
            "time": "Time of day",
            "duration": "Time duration/interval",
            # Geographic
            "coordinates": "Geographic coordinates (latitude, longitude)",
            "latitude": "Latitude (-90 to 90 degrees)",
            "longitude": "Longitude (-180 to 180 degrees)",
            # Media
            "image": "Image URL or file path",
            "file": "File URL or file path",
            # Identifiers
            "uuid": "Universally unique identifier (UUID)",
            # Structured
            "json": "JSON object data",
            # Basic types
            "text": "Text string",
            "integer": "Integer number",
            "boolean": "True or false value",
            "jsonb": "JSON object (binary format)",
        }

    def generate_field_comment(
        self, field: FieldDefinition, entity: Entity, custom_description: Optional[str] = None
    ) -> str:
        """Generate COMMENT ON COLUMN for a field with FraiseQL YAML annotations"""

        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"

        # Use custom description if provided, otherwise get type-based description
        if custom_description:
            description = custom_description
        else:
            description = self._get_field_description(field)

        # Determine GraphQL type for FraiseQL
        graphql_type = self._map_to_graphql_type(field)

        # Build YAML annotation
        yaml_parts = [
            f"name: {field.name}",
            f"type: {graphql_type}{'' if field.nullable else '!'}",
            f"required: {str(not field.nullable).lower()}",
        ]

        if field.type_name == "ref":
            yaml_parts.append(f"references: {field.reference_entity}")
        elif field.type_name == "enum" and field.values:
            values_str = ", ".join(field.values)
            yaml_parts.append(f"enumValues: {values_str}")

        yaml_content = "\n".join(yaml_parts)

        comment = f"""COMMENT ON COLUMN {table_name}.{field.name} IS
'{description}

@fraiseql:field
{yaml_content}';"""

        return comment

    def _get_field_description(self, field: FieldDefinition) -> str:
        """Get human-readable description for field"""

        # Use type description from registry
        description = self._type_descriptions.get(field.type_name, "")

        if not description:
            # Fallback for unknown types
            description = f"{field.type_name.capitalize()} value"

        # Add special notes for specific types
        if field.type_name == "enum" and field.values:
            description += f" (options: {', '.join(field.values)})"

        elif field.type_name == "ref" and field.reference_entity:
            description += f" → {field.reference_entity}"

        return description

    def _map_to_graphql_type(self, field: FieldDefinition) -> str:
        """Map SpecQL field type to GraphQL type for FraiseQL"""
        if field.type_name == "ref":
            # References become UUID in GraphQL (external API contract)
            return "UUID"
        elif field.type_name == "enum":
            return "String"  # Enums are strings in GraphQL
        elif field.type_name == "list":
            base_type = self.TYPE_MAPPINGS.get(field.item_type or "text", "String")
            return f"[{base_type}]"
        else:
            # Map PostgreSQL types to GraphQL types
            pg_type = self.TYPE_MAPPINGS.get(field.type_name, "String")
            graphql_mappings = {
                "TEXT": "String",
                "INTEGER": "Int",
                "BOOLEAN": "Boolean",
                "DATE": "String",  # ISO date string
                "TIMESTAMPTZ": "String",  # ISO datetime string
                "UUID": "UUID",
                "JSONB": "JSON",
                "DECIMAL": "Float",
            }
            return graphql_mappings.get(pg_type, "String")

    def generate_all_field_comments(self, entity: Entity) -> List[str]:
        """Generate COMMENT statements for all fields"""
        comments = []

        for field_name, field_def in entity.fields.items():
            # For ref() fields, use actual database column name (fk_*)
            if field_def.type_name == "ref":
                # Create temp field with correct column name
                from dataclasses import replace

                actual_field = replace(field_def, name=f"fk_{field_name}")
                comment = self.generate_field_comment(actual_field, entity)
            else:
                comment = self.generate_field_comment(field_def, entity)

            comments.append(comment)

        return comments

    def generate_table_comment(self, entity: Entity) -> str:
        """Generate COMMENT ON TABLE"""
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"

        description = entity.description or f"{entity.name} entity"

        return f"COMMENT ON TABLE {table_name} IS '{description}';"
