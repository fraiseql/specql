"""
TypeScript Types Generator

Generates TypeScript type definitions for entities, mutations, and GraphQL operations.
Creates interfaces for entities, input types for mutations, and result types.

Output: types.ts
"""

from pathlib import Path

from src.core.ast_models import Entity, FieldDefinition, FieldTier
from src.core.scalar_types import (
    ScalarTypeDef,
    get_composite_type,
    get_scalar_type,
    is_composite_type,
    is_scalar_type,
)


class TypeScriptTypesGenerator:
    """
    Generates TypeScript type definitions for frontend applications.

    This generator creates:
    - Entity interfaces
    - Mutation input types
    - Mutation result types
    - GraphQL operation types
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the types.ts file
        """
        self.output_dir = output_dir
        self.types: list[str] = []

    def generate_types(self, entities: list[Entity]) -> None:
        """
        Generate TypeScript types for all entities.

        Args:
            entities: List of parsed entity definitions
        """
        self.types = []

        # Add header
        self._add_header()

        # Generate entity types
        for entity in entities:
            self._generate_entity_types(entity)

        # Generate mutation types
        for entity in entities:
            self._generate_mutation_types(entity)

        # Write to file
        output_file = self.output_dir / "types.ts"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.types))

    def _add_header(self) -> None:
        """Add file header with imports and base types."""
        header = """/**
 * Auto-generated TypeScript types for GraphQL operations
 *
 * Generated from SpecQL entity definitions
 * Do not edit manually - regenerate when entities change
 */

import { gql } from '@apollo/client';

// Base scalar types
export type UUID = string;
export type DateTime = string;
export type Date = string;
export type Time = string;
export type Interval = string;
export type JSONValue = any;

// GraphQL operation result wrapper
export interface MutationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
}

// Pagination types
export interface PaginationInput {
  limit?: number;
  offset?: number;
  orderBy?: string;
  orderDirection?: 'ASC' | 'DESC';
}

export interface PaginatedResult<T> {
  items: T[];
  totalCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

"""
        self.types.append(header)

    def _generate_entity_types(self, entity: Entity) -> None:
        """
        Generate TypeScript interfaces for an entity.

        Args:
            entity: The entity to generate types for
        """
        entity_name = entity.name

        # Main entity interface
        self.types.append(f"// {entity_name} Entity")
        self.types.append(f"export interface {entity_name} {{")

        for field_name, field_def in entity.fields.items():
            ts_type = self._field_to_typescript_type(field_def)
            optional = "?" if field_def.nullable else ""
            self.types.append(f"  {field_name}{optional}: {ts_type};")

        self.types.append("}")
        self.types.append("")

        # Create input type (for mutations)
        self.types.append(f"export interface {entity_name}Input {{")

        for field_name, field_def in entity.fields.items():
            # For inputs, most fields are optional except required ones
            ts_type = self._field_to_typescript_type(field_def)
            # Primary keys and auto-generated fields are typically not in input
            if field_name not in ["id", "created_at", "updated_at", "created_by", "updated_by"]:
                optional = "?" if field_def.nullable or field_def.default is not None else ""
                self.types.append(f"  {field_name}{optional}: {ts_type};")

        self.types.append("}")
        self.types.append("")

        # Filter input type (for queries)
        self.types.append(f"export interface {entity_name}Filter {{")

        for field_name, field_def in entity.fields.items():
            ts_type = self._field_to_typescript_type(field_def)
            self.types.append(f"  {field_name}?: {ts_type};")
            # Add comparison operators for common types
            if field_def.type_name in [
                "text",
                "string",
                "integer",
                "bigint",
                "numeric",
                "date",
                "timestamptz",
            ]:
                self.types.append(f"  {field_name}_gt?: {ts_type};")
                self.types.append(f"  {field_name}_lt?: {ts_type};")
                self.types.append(f"  {field_name}_gte?: {ts_type};")
                self.types.append(f"  {field_name}_lte?: {ts_type};")
                if field_def.type_name in ["text", "string"]:
                    self.types.append(f"  {field_name}_like?: string;")
                    self.types.append(f"  {field_name}_ilike?: string;")

        self.types.append("}")
        self.types.append("")

    def _generate_mutation_types(self, entity: Entity) -> None:
        """
        Generate mutation input and result types for an entity.

        Args:
            entity: The entity to generate mutation types for
        """
        entity_name = entity.name

        for action in entity.actions:
            action_name = action.name
            pascal_name = self._to_pascal_case(action_name)

            # Create input type
            self.types.append(f"// {entity_name} {action_name} mutation types")
            self.types.append(f"export interface {pascal_name}Input {{")

            # Add basic fields based on action type
            if action_name.startswith("create_"):
                # For create, include most entity fields
                for field_name, field_def in entity.fields.items():
                    if field_name not in [
                        "id",
                        "created_at",
                        "updated_at",
                        "created_by",
                        "updated_by",
                    ]:
                        ts_type = self._field_to_typescript_type(field_def)
                        optional = (
                            "?" if field_def.nullable or field_def.default is not None else ""
                        )
                        self.types.append(f"  {field_name}{optional}: {ts_type};")

            elif action_name.startswith("update_"):
                # For update, include ID (required) and optional fields
                self.types.append("  id: UUID;")
                for field_name, field_def in entity.fields.items():
                    if field_name not in [
                        "id",
                        "created_at",
                        "updated_at",
                        "created_by",
                        "updated_by",
                    ]:
                        ts_type = self._field_to_typescript_type(field_def)
                        self.types.append(f"  {field_name}?: {ts_type};")

            elif action_name.startswith("delete_"):
                # For delete, only ID is needed
                self.types.append("  id: UUID;")

            self.types.append("}")
            self.types.append("")

            # Check if action contains call_service steps
            has_call_service = any(step.type == "call_service" for step in action.steps)

            # Success result type
            self.types.append(f"export interface {pascal_name}Success {{")

            if has_call_service:
                # For actions with call_service, include job_id
                if action_name.startswith("create_"):
                    self.types.append(f"  {entity_name.lower()}: {entity_name};")
                self.types.append("  job_id: UUID;")
                self.types.append("  message: string;")
            elif action_name.startswith("create_"):
                self.types.append(f"  {entity_name.lower()}: {entity_name};")
                self.types.append("  message: string;")
            elif action_name.startswith("update_"):
                self.types.append(f"  {entity_name.lower()}: {entity_name};")
                self.types.append("  message: string;")
            elif action_name.startswith("delete_"):
                self.types.append("  success: boolean;")
                self.types.append("  message: string;")
            else:
                self.types.append("  result: any;")
                self.types.append("  message: string;")

            self.types.append("}")
            self.types.append("")

            # Error result type
            self.types.append(f"export interface {pascal_name}Error {{")

            self.types.append("  code: string;")
            self.types.append("  message: string;")
            self.types.append("  details?: any;")

            self.types.append("}")
            self.types.append("")

            # Union result type
            self.types.append(
                f"export type {pascal_name}Result = {pascal_name}Success | {pascal_name}Error;"
            )
            self.types.append("")

    def _field_to_typescript_type(self, field: FieldDefinition) -> str:
        """
        Convert a field definition to TypeScript type.

        Args:
            field: The field definition

        Returns:
            TypeScript type string
        """
        type_name = field.type_name

        # Handle scalar types
        if is_scalar_type(type_name):
            scalar_def = get_scalar_type(type_name)
            if scalar_def:
                return self._scalar_to_typescript_type(scalar_def)

        # Handle composite types
        if is_composite_type(type_name):
            composite_def = get_composite_type(type_name)
            if composite_def:
                return composite_def.name

        # Handle references
        if field.tier == FieldTier.REFERENCE:
            # References are typically UUIDs pointing to other entities
            return "UUID"

        # Handle basic PostgreSQL types
        type_mapping = {
            "text": "string",
            "varchar": "string",
            "char": "string",
            "integer": "number",
            "bigint": "number",
            "smallint": "number",
            "numeric": "number",
            "real": "number",
            "double precision": "number",
            "boolean": "boolean",
            "date": "Date",
            "time": "Time",
            "timetz": "Time",
            "timestamp": "DateTime",
            "timestamptz": "DateTime",
            "interval": "Interval",
            "uuid": "UUID",
            "jsonb": "JSONValue",
            "json": "JSONValue",
            "inet": "string",
            "macaddr": "string",
            "point": "JSONValue",
        }

        return type_mapping.get(type_name, "any")

    def _scalar_to_typescript_type(self, scalar: ScalarTypeDef) -> str:
        """
        Convert a scalar type definition to TypeScript type.

        Args:
            scalar: The scalar type definition

        Returns:
            TypeScript type string
        """
        # Map PostgreSQL types to TypeScript
        pg_type = scalar.postgres_type.value

        if pg_type in ["TEXT", "VARCHAR", "CHAR"]:
            return "string"
        elif pg_type in ["INTEGER", "BIGINT", "SMALLINT", "NUMERIC", "REAL", "DOUBLE PRECISION"]:
            return "number"
        elif pg_type == "BOOLEAN":
            return "boolean"
        elif pg_type == "DATE":
            return "Date"
        elif pg_type == "TIME":
            return "Time"
        elif pg_type in ["TIMESTAMP", "TIMESTAMPTZ"]:
            return "DateTime"
        elif pg_type == "INTERVAL":
            return "Interval"
        elif pg_type == "UUID":
            return "UUID"
        elif pg_type == "JSONB":
            return "JSONValue"
        elif pg_type == "INET":
            return "string"
        elif pg_type == "MACADDR":
            return "string"
        elif pg_type == "POINT":
            return "JSONValue"
        else:
            return "any"

    def _to_pascal_case(self, snake_str: str) -> str:
        """
        Convert snake_case to PascalCase.

        Args:
            snake_str: String in snake_case format

        Returns:
            String in PascalCase format
        """
        components = snake_str.split("_")
        return "".join(x.capitalize() for x in components)
