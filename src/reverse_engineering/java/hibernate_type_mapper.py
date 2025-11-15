"""
Hibernate Type Mapper

Maps Hibernate/JPA Java types to SpecQL types.
"""

from typing import Optional


class HibernateTypeMapper:
    """Map Hibernate/JPA types to SpecQL types"""

    # Java primitive and wrapper types → SpecQL
    TYPE_MAPPING = {
        # Primitives
        "int": "integer",
        "long": "integer",
        "short": "integer",
        "byte": "integer",
        "float": "decimal",
        "double": "decimal",
        "boolean": "boolean",
        # Wrappers
        "Integer": "integer",
        "Long": "integer",
        "Short": "integer",
        "Byte": "integer",
        "Float": "decimal",
        "Double": "decimal",
        "Boolean": "boolean",
        # String
        "String": "text",
        "char": "text",
        "Character": "text",
        # Date/Time (java.time)
        "LocalDate": "date",
        "LocalDateTime": "timestamp",
        "LocalTime": "time",
        "Instant": "timestamp",
        "ZonedDateTime": "timestamp",
        # Date/Time (legacy java.util)
        "Date": "timestamp",
        "Timestamp": "timestamp",
        # Binary
        "byte[]": "blob",
        "Byte[]": "blob",
        # UUID
        "UUID": "uuid",
        # JSON
        "JsonNode": "json",
        "Map": "json",
    }

    def map_type(self, java_type: str, jpa_field) -> str:
        """
        Map Java/JPA type to SpecQL type string

        Args:
            java_type: Java type string (e.g., "String", "Long")
            jpa_field: JPAField with annotation metadata

        Returns:
            SpecQL type string
        """
        # Handle relationships
        if jpa_field.is_relationship:
            if jpa_field.relationship_type == "ManyToOne":
                return f"ref({jpa_field.target_entity})"
            elif jpa_field.relationship_type == "OneToMany":
                return f"list({jpa_field.target_entity})"

        # Handle enums
        if jpa_field.is_enum:
            return "text"  # Enums stored as text in database

        # Handle collections
        if java_type.startswith("List<") or java_type.startswith("Set<"):
            inner_type = self._extract_generic_type(java_type)
            if inner_type:
                return f"list({inner_type})"
            return "list"

        # Map simple types
        return self.TYPE_MAPPING.get(java_type, "text")

    def _extract_generic_type(self, type_str: str) -> Optional[str]:
        """Extract generic type from List<Entity>"""
        if "<" in type_str and ">" in type_str:
            start = type_str.index("<") + 1
            end = type_str.index(">")
            return type_str[start:end].strip()
        return None
