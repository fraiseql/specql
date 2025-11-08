"""
PostgreSQL COMMENT Generator
Generates descriptive COMMENT ON statements for FraiseQL autodiscovery
"""

from typing import List, Dict, Optional
from src.core.ast_models import Entity, FieldDefinition
from src.core.type_registry import get_type_registry


class CommentGenerator:
    """Generates PostgreSQL COMMENT statements for rich types"""

    def __init__(self) -> None:
        self.type_registry = get_type_registry()
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
        """Generate COMMENT ON COLUMN for a field"""

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Use custom description if provided, otherwise get type-based description
        if custom_description:
            description = custom_description
        else:
            description = self._get_field_description(field)

        # Add nullable info if relevant
        if not field.nullable:
            description += " (required)"

        return f"COMMENT ON COLUMN {table_name}.{field.name} IS '{description}';"

    def _get_field_description(self, field: FieldDefinition) -> str:
        """Get human-readable description for field"""

        # Use type description from registry
        description = self._type_descriptions.get(field.type, "")

        if not description:
            # Fallback for unknown types
            description = f"{field.type.capitalize()} value"

        # Add special notes for specific types
        if field.type == "enum" and field.values:
            description += f" (options: {', '.join(field.values)})"

        elif field.type == "ref" and field.target_entity:
            description += f" → {field.target_entity}"

        elif field.type == "money" and field.type_metadata:
            currency = field.type_metadata.get("currency")
            if currency:
                description += f" ({currency})"

        return description

    def generate_all_field_comments(self, entity: Entity) -> List[str]:
        """Generate COMMENT statements for all fields"""
        comments = []

        for field_name, field_def in entity.fields.items():
            # For ref() fields, use actual database column name (fk_*)
            if field_def.type == "ref":
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
        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        description = entity.description or f"{entity.name} entity"

        return f"COMMENT ON TABLE {table_name} IS '{description}';"
