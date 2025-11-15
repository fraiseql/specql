"""
Diesel Parser for SpecQL

Parses Diesel models and schema files to extract entity definitions.
"""

import logging
from pathlib import Path
from typing import List

from src.core.universal_ast import UniversalEntity, UniversalField, FieldType
from src.core.ast_models import Entity, FieldDefinition
from src.reverse_engineering.rust_parser import RustReverseEngineeringService
from src.parsers.rust.advanced_patterns import (
    AdvancedRustPatternHandler,
    RustAdvancedMetadata,
)

logger = logging.getLogger(__name__)


class DieselParser:
    """Parser for Diesel ORM models and schema files."""

    def __init__(self):
        self.service = RustReverseEngineeringService()
        self.advanced_handler = AdvancedRustPatternHandler()

    def parse_model_file(
        self, model_file_path: str, schema_file_path: str
    ) -> UniversalEntity:
        """
        Parse a single Diesel model file along with its schema.

        Args:
            model_file_path: Path to the model .rs file
            schema_file_path: Path to the schema.rs file

        Returns:
            UniversalEntity representing the parsed model
        """
        model_path = Path(model_file_path)
        schema_path = Path(schema_file_path) if schema_file_path else None

        # Parse model file
        model_entities = self._parse_file(model_path, include_diesel_tables=False)

        # Parse schema file if provided
        schema_entities = []
        if schema_path and schema_path.exists():
            schema_entities = self._parse_file(schema_path, include_diesel_tables=True)

        # Find the model entity (should be the one with derive macros)
        model_entity = None
        for entity in model_entities:
            if self._is_diesel_model(entity):
                model_entity = entity
                break

        if not model_entity:
            raise ValueError(f"No Diesel model found in {model_file_path}")

        # Extract advanced pattern metadata
        with open(model_path) as f:
            rust_code = f.read()
        advanced_metadata = self.advanced_handler.extract_advanced_metadata(rust_code)

        # Find corresponding schema entity
        schema_entity = None
        for entity in schema_entities:
            if entity.name.lower() == model_entity.name.lower():
                schema_entity = entity
                break

        if schema_entity:
            # Merge schema information into model
            self._merge_schema_info(model_entity, schema_entity)

        # Enhance entity with advanced metadata
        model_entity = self._apply_advanced_metadata(model_entity, advanced_metadata)

        return model_entity

    def _apply_advanced_metadata(
        self, entity: UniversalEntity, metadata: RustAdvancedMetadata
    ) -> UniversalEntity:
        """Apply advanced pattern metadata to entity"""
        # Build description of advanced patterns
        advanced_features = []

        if metadata.has_lifetimes and metadata.lifetime_params:
            advanced_features.append(
                f"Lifetimes: {', '.join(metadata.lifetime_params)}"
            )

        if metadata.has_generics and metadata.generic_params:
            advanced_features.append(f"Generics: {', '.join(metadata.generic_params)}")

        if metadata.is_async:
            advanced_features.append("Async support")

        if metadata.advanced_types:
            type_list = [
                f"{field}: {diesel_type}"
                for field, diesel_type in metadata.advanced_types.items()
            ]
            advanced_features.append(f"Advanced types: {', '.join(type_list)}")

        # Update field types based on advanced types
        for field in entity.fields:
            if field.name in metadata.advanced_types:
                diesel_type = metadata.advanced_types[field.name]
                if diesel_type == "Array":
                    field.type = FieldType.LIST
                elif diesel_type == "Jsonb":
                    field.type = FieldType.RICH
                elif diesel_type == "Uuid":
                    field.type = FieldType.TEXT  # UUIDs are typically stored as text
                # Range could be handled as RICH or custom type

        # Update entity description
        if advanced_features:
            current_desc = entity.description or ""
            advanced_desc = f"Advanced Rust patterns: {'; '.join(advanced_features)}"
            entity.description = f"{current_desc}\n{advanced_desc}".strip()

            logger.info(f"Applied advanced metadata to {entity.name}: {advanced_desc}")

        return entity

    def parse_project(self, models_dir: str, schema_file: str) -> List[UniversalEntity]:
        """
        Parse all models in a project directory.

        Args:
            models_dir: Directory containing model .rs files
            schema_file: Path to the schema.rs file

        Returns:
            List of UniversalEntity objects
        """
        models_path = Path(models_dir)
        schema_path = Path(schema_file)

        entities = []

        # Parse schema first
        schema_entities = self._parse_file(schema_path, include_diesel_tables=True)

        # Parse each model file
        for model_file in models_path.glob("*.rs"):
            try:
                model_entities = self._parse_file(
                    model_file, include_diesel_tables=False
                )

                for model_entity in model_entities:
                    if self._is_diesel_model(model_entity):
                        # Find corresponding schema entity
                        schema_entity = None
                        for se in schema_entities:
                            if se.name.lower() == model_entity.name.lower():
                                schema_entity = se
                                break

                        if schema_entity:
                            self._merge_schema_info(model_entity, schema_entity)

                        entities.append(model_entity)

            except Exception as e:
                logger.warning(f"Failed to parse {model_file}: {e}")
                continue

        return entities

    def _parse_file(
        self, file_path: Path, include_diesel_tables: bool = True
    ) -> List[UniversalEntity]:
        """Parse a single Rust file and return entities."""
        entities = self.service.reverse_engineer_file(
            file_path, include_diesel_tables=include_diesel_tables
        )
        # Convert Entity to UniversalEntity
        universal_entities = [
            self._convert_to_universal_entity(entity) for entity in entities
        ]

        # Get struct information to update field types based on Rust types
        structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers = (
            self.service.parser.parse_file(file_path)
        )
        enum_names = {enum.name for enum in enums}

        # Update field types based on Rust struct information
        for entity in universal_entities:
            # Find corresponding struct
            struct_info = None
            for struct in structs:
                if struct.name == entity.name:
                    struct_info = struct
                    break

            if struct_info:
                for field in entity.fields:
                    # Find corresponding Rust field
                    rust_field = None
                    for rf in struct_info.fields:
                        if rf.name == field.name:
                            rust_field = rf
                            break

                    if rust_field and rust_field.field_type in enum_names:
                        field.type = FieldType.ENUM

        return universal_entities

    def _convert_to_universal_entity(self, entity: Entity) -> UniversalEntity:
        """Convert Entity to UniversalEntity."""
        fields = []
        for field_name, field_def in entity.fields.items():
            # Convert FieldDefinition to UniversalField
            field_type = self._convert_field_type(field_def)
            universal_field = UniversalField(
                name=field_name,
                type=field_type,
                required=not field_def.nullable,
                default=field_def.default,
            )
            if field_def.reference_entity:
                universal_field.references = field_def.reference_entity
            fields.append(universal_field)

        return UniversalEntity(
            name=entity.name,
            schema=entity.schema,
            fields=fields,
            actions=[],  # TODO: convert actions if needed
        )

    def _convert_field_type(self, field_def: FieldDefinition) -> FieldType:
        """Convert FieldDefinition type to FieldType."""
        type_name = field_def.type_name.lower()

        if type_name in ["text", "varchar", "string"]:
            return FieldType.TEXT
        elif type_name in ["integer", "int", "i32", "i64"]:
            return FieldType.INTEGER
        elif type_name in ["boolean", "bool"]:
            return FieldType.BOOLEAN
        elif type_name in ["timestamp", "datetime", "naivedatetime"]:
            return FieldType.DATETIME
        elif field_def.reference_entity:
            return FieldType.REFERENCE
        elif type_name == "enum":
            return FieldType.ENUM
        else:
            return FieldType.TEXT  # Default fallback

    def _is_diesel_model(self, entity: UniversalEntity) -> bool:
        """Check if an entity represents a Diesel model."""
        # Check if it has Diesel derive attributes
        # This is a simplified check - in practice we'd look at the raw Rust code
        return (
            len(entity.fields) > 0
        )  # For now, assume any entity with fields is a model

    def _merge_schema_info(
        self, model_entity: UniversalEntity, schema_entity: UniversalEntity
    ):
        """Merge schema information into the model entity."""
        # For each field in the model, find corresponding schema field
        for model_field in model_entity.fields:
            schema_field = None
            for sf in schema_entity.fields:
                if sf.name == model_field.name:
                    schema_field = sf
                    break

            if schema_field:
                # Update field type based on schema if needed
                # This is where we'd handle type mappings from Diesel schema to Rust types
                pass
