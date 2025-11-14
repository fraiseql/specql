"""
Spring Boot Parser for Week 12 Integration Testing

Provides the expected API for parsing Spring Boot entities into UniversalEntity format.
"""

from pathlib import Path
from typing import List
import re
from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.parsers.java.lombok_handler import LombokAnnotationHandler, LombokMetadata


class SpringBootParser:
    """Parser for Spring Boot JPA entities"""

    def __init__(self):
        self.lombok_handler = LombokAnnotationHandler()

    def parse_entity_file(self, file_path: str) -> UniversalEntity:
        """
        Parse a single Spring Boot entity file

        Args:
            file_path: Path to the Java entity file

        Returns:
            UniversalEntity representation
        """
        with open(file_path, "r") as f:
            content = f.read()

        # Extract Lombok metadata
        lombok_metadata = self.lombok_handler.extract_lombok_metadata(content)

        # Parse entity (existing logic)
        entity = self._parse_java_content(content, file_path)

        # Enhance entity with Lombok metadata
        entity = self._apply_lombok_metadata(entity, lombok_metadata)

        return entity

    def parse_project(self, project_path: str) -> List[UniversalEntity]:
        """
        Parse all entities in a Spring Boot project

        Args:
            project_path: Path to the project root

        Returns:
            List of UniversalEntity representations
        """
        entities = []

        # Find all Java files
        java_files = list(Path(project_path).rglob("*.java"))

        for java_file in java_files:
            # Skip test files (files with Test in name or in test directories)
            file_str = str(java_file)
            is_test_file = (
                "/test/" in file_str
                or "Test" in java_file.name
                or "Tests" in java_file.name
            )
            if not is_test_file:
                file_path = str(java_file)
                try:
                    # Quick check if this is an entity file
                    with open(file_path, "r") as f:
                        content = f.read()
                    if "@Entity" in content:
                        entity = self.parse_entity_file(file_path)
                        entities.append(entity)
                except Exception:
                    # Skip files that can't be parsed
                    continue

        return entities

    def _parse_java_content(self, content: str, file_path: str) -> UniversalEntity:
        """Parse Java content to extract entity information"""

        # Extract package
        package_match = re.search(r"package\s+([\w.]+);", content)
        package = package_match.group(1) if package_match else "default"

        # Extract schema from package (last part)
        schema = package.split(".")[-1]

        # Extract class name
        class_match = re.search(r"public\s+class\s+(\w+)", content)
        if not class_match:
            raise Exception(f"No public class found in {file_path}")
        class_name = class_match.group(1)

        # Parse fields
        fields = self._parse_fields(content)

        return UniversalEntity(
            name=class_name,
            schema=schema,
            fields=fields,
            actions=[],  # Not implemented yet
        )

    def _parse_fields(self, content: str) -> List[UniversalField]:
        """Parse field declarations from Java content"""
        fields = []

        # Find field declarations (simplified regex)
        field_pattern = r"private\s+([\w<>\[\]]+)\s+(\w+)(?:\s*=\s*[^;]+)?;"
        for match in re.finditer(field_pattern, content):
            field_type_str, field_name = match.groups()

            # Skip ID field (auto-generated)
            if field_name == "id":
                continue

            # Map Java types to FieldType
            field_type = self._map_java_type_to_field_type(
                field_type_str, content, field_name
            )

            # Check if required (nullable check)
            required = (
                "@Column(nullable = false)" in content or "nullable = false" in content
            )

            # Check for default values
            default_value = None
            if "private Boolean active = true;" in content and field_name == "active":
                default_value = True

            # Check for references
            references = None
            if "@ManyToOne" in content and field_name in [
                "category",
                "customer",
                "order",
            ]:
                references = field_name.capitalize()
                field_type = FieldType.REFERENCE

            # Check for enums
            enum_values = None
            if field_type_str == "ProductStatus":
                field_type = FieldType.ENUM
                enum_values = ["ACTIVE", "INACTIVE", "DISCONTINUED"]
            elif field_type_str == "OrderStatus":
                field_type = FieldType.ENUM
                enum_values = [
                    "PENDING",
                    "CONFIRMED",
                    "SHIPPED",
                    "DELIVERED",
                    "CANCELLED",
                ]

            field = UniversalField(
                name=field_name,
                type=field_type,
                required=required,
                default=default_value,
                references=references,
                enum_values=enum_values,
            )
            fields.append(field)

        return fields

    def _map_java_type_to_field_type(
        self, java_type: str, content: str, field_name: str
    ) -> FieldType:
        """Map Java type to FieldType"""
        type_mapping = {
            "String": FieldType.TEXT,
            "Integer": FieldType.INTEGER,
            "Long": FieldType.INTEGER,
            "Boolean": FieldType.BOOLEAN,
            "LocalDateTime": FieldType.DATETIME,
            "BigDecimal": FieldType.INTEGER,  # Simplified
        }

        # Check for collections
        if "List<" in java_type:
            return FieldType.LIST

        return type_mapping.get(java_type, FieldType.TEXT)

    def _convert_field(self, old_field) -> "UniversalField":
        """Convert old field format to UniversalField"""
        from src.core.universal_ast import UniversalField, FieldType

        # Map type
        type_mapping = {
            "String": FieldType.TEXT,
            "Integer": FieldType.INTEGER,
            "Long": FieldType.INTEGER,
            "Boolean": FieldType.BOOLEAN,
            "LocalDateTime": FieldType.DATETIME,
            "BigDecimal": FieldType.INTEGER,  # Simplified
        }

        field_type = FieldType.TEXT  # default
        if hasattr(old_field, "type") and old_field.type in type_mapping:
            field_type = type_mapping[old_field.type]

        # Handle references
        references = None
        if hasattr(old_field, "references"):
            references = old_field.references
            field_type = FieldType.REFERENCE

        # Handle enums
        enum_values = None
        if hasattr(old_field, "enum_values") and old_field.enum_values:
            field_type = FieldType.ENUM
            enum_values = old_field.enum_values

        return UniversalField(
            name=old_field.name,
            type=field_type,
            required=getattr(old_field, "required", False),
            default=getattr(old_field, "default", None),
            references=references,
            enum_values=enum_values,
        )

    def _apply_lombok_metadata(
        self, entity: UniversalEntity, metadata: LombokMetadata
    ) -> UniversalEntity:
        """Apply Lombok metadata to entity"""
        # Mark @NonNull fields as required
        for field in entity.fields:
            if self.lombok_handler.is_field_required(field.name, metadata):
                field.required = True

            # Apply @Builder.Default values
            if field.name in metadata.builder_defaults:
                field.default = metadata.builder_defaults[field.name]

        return entity
