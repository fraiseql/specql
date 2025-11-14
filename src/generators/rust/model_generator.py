"""
Rust Model Generator

Generates Rust struct definitions for Diesel ORM.
"""

from typing import List
from src.core.ast_models import Entity, FieldDefinition
from src.generators.rust.diesel_type_mapper import DieselTypeMapper
from src.generators.naming_utils import to_snake_case, to_pascal_case


class RustModelGenerator:
    """
    Generates Diesel model structs

    Creates three types of structs:
    1. Queryable: For reading from database
    2. Insertable: For inserting into database
    3. AsChangeset: For updating database

    Example:
        generator = RustModelGenerator()

        # Generate Queryable struct
        queryable = generator.generate_queryable_struct(entity)

        # Generate all structs
        models = generator.generate_all_models(entity)
    """

    def __init__(self):
        self.type_mapper = DieselTypeMapper()

    def generate_queryable_struct(
        self, entity: Entity, include_imports: bool = False
    ) -> str:
        """
        Generate Diesel Queryable struct

        This struct represents a complete row from the database.
        Includes all fields: primary key, UUID, user fields, audit fields.

        Args:
            entity: SpecQL entity definition
            include_imports: Whether to include use statements

        Returns:
            Complete Queryable struct definition
        """
        struct_name = to_pascal_case(entity.name)
        table_name = f"tb_{to_snake_case(entity.name)}"

        # Build parts
        parts = []

        # Imports (if requested)
        if include_imports:
            parts.append(self._generate_imports(entity))
            parts.append("")

        # Documentation
        if entity.description:
            parts.append(f"/// {entity.description}")
        parts.append(f"/// Queryable struct for {table_name} table")

        # Derives
        parts.append("#[derive(Debug, Clone, Queryable, Selectable)]")
        parts.append(f"#[diesel(table_name = {table_name})]")

        # Struct declaration
        parts.append(f"pub struct {struct_name} {{")

        # Fields
        field_lines = self._generate_queryable_fields(entity)
        for field_line in field_lines:
            parts.append(f"    {field_line}")

        parts.append("}")

        return "\n".join(parts)

    def _generate_imports(self, entity: Entity, with_serde: bool = False) -> str:
        """Generate use statements"""
        imports = [
            "use diesel::prelude::*;",
            "use uuid::Uuid;",
            "use chrono::NaiveDateTime;",
        ]

        # Schema import
        schema_path = f"super::schema::{entity.schema}::tb_{to_snake_case(entity.name)}"
        imports.append(f"use {schema_path};")

        # BigDecimal if needed
        if self._needs_bigdecimal(entity):
            imports.append("use bigdecimal::BigDecimal;")

        # serde_json if needed
        if self._needs_serde_json(entity):
            imports.append("use serde_json;")

        # Serde if needed
        if with_serde:
            imports.append("use serde::{Serialize, Deserialize};")

        return "\n".join(imports)

    def _needs_bigdecimal(self, entity: Entity) -> bool:
        """Check if entity has decimal fields"""
        return any(f.type_name.startswith("decimal") for f in entity.fields.values())

    def _needs_serde_json(self, entity: Entity) -> bool:
        """Check if entity has JSON fields"""
        return any(f.type_name == "json" for f in entity.fields.values())

    def _generate_queryable_fields(self, entity: Entity) -> List[str]:
        """
        Generate all field definitions for Queryable struct

        Order:
        1. Primary key (pk_*)
        2. UUID identifier (id)
        3. User-defined fields
        4. Audit fields

        Returns:
            List of field definition strings
        """
        fields = []

        # 1. Primary key
        pk_name = f"pk_{to_snake_case(entity.name)}"
        fields.append(f"pub {pk_name}: i32,")

        # 2. UUID identifier
        fields.append("pub id: Uuid,")

        # 3. User-defined fields
        for field in entity.fields.values():
            field_def = self._generate_queryable_field(field)
            fields.append(field_def)

        # 4. Audit fields
        fields.extend(self._generate_audit_fields())

        return fields

    def _generate_queryable_field(self, field: FieldDefinition) -> str:
        """
        Generate single field definition for Queryable struct

        Args:
            field: SpecQL field definition

        Returns:
            Field line like "pub email: String,"
        """
        # Handle foreign key references
        if field.type_name == "ref" and field.reference_entity:
            field_name = f"fk_{to_snake_case(field.reference_entity)}"
        else:
            field_name = to_snake_case(field.name)

        # Get Rust type
        diesel_type = self.type_mapper.map_field_type(
            field.type_name,
            required=not field.nullable,
            ref_entity=field.reference_entity if field.type_name == "ref" else None,
        )

        rust_type = self.type_mapper.get_rust_native_type(diesel_type)

        return f"pub {field_name}: {rust_type},"

    def generate_as_changeset_struct(
        self,
        entity: Entity,
        include_imports: bool = False,
        include_soft_delete: bool = False,
    ) -> str:
        """
        Generate Diesel AsChangeset struct

        This struct represents data for UPDATE operations.
        All fields are optional (Option<T>) since updates are partial.
        Excludes immutable fields (pk, id, created_at, created_by).

        Args:
            entity: SpecQL entity definition
            include_imports: Whether to include use statements
            include_soft_delete: Whether to include soft delete fields

        Returns:
            Complete AsChangeset struct definition
        """
        struct_name = f"Update{to_pascal_case(entity.name)}"
        table_name = f"tb_{to_snake_case(entity.name)}"

        parts = []

        # Imports (if requested)
        if include_imports:
            parts.append(self._generate_imports(entity))
            parts.append("")

        # Documentation
        parts.append(f"/// AsChangeset struct for {table_name} table")
        parts.append("/// Used for UPDATE operations")

        # Derives
        parts.append("#[derive(Debug, AsChangeset)]")
        parts.append(f"#[diesel(table_name = {table_name})]")

        # Struct declaration
        parts.append(f"pub struct {struct_name} {{")

        # Fields (all optional for partial updates)
        field_lines = self._generate_as_changeset_fields(entity, include_soft_delete)
        for field_line in field_lines:
            parts.append(f"    {field_line}")

        parts.append("}")

        return "\n".join(parts)

    def _generate_as_changeset_fields(
        self, entity: Entity, include_soft_delete: bool
    ) -> List[str]:
        """
        Generate fields for AsChangeset struct

        All fields are Option<T> since updates are partial.

        Includes:
        - User-defined fields (as Option<T>)
        - updated_at, updated_by (required for updates)
        - deleted_at, deleted_by (if soft delete enabled)

        Excludes:
        - pk_* (primary key, immutable)
        - id (UUID, immutable)
        - created_at, created_by (creation fields, immutable)

        Returns:
            List of field definition strings
        """
        fields = []

        # User-defined fields (all as Option<T>)
        for field in entity.fields.values():
            field_def = self._generate_as_changeset_field(field)
            fields.append(field_def)

        # Update tracking (required)
        fields.append("pub updated_at: NaiveDateTime,")
        fields.append("pub updated_by: Option<Uuid>,")

        # Soft delete (optional)
        if include_soft_delete:
            fields.append("pub deleted_at: Option<NaiveDateTime>,")
            fields.append("pub deleted_by: Option<Uuid>,")

        return fields

    def _generate_as_changeset_field(self, field: FieldDefinition) -> str:
        """
        Generate single field definition for AsChangeset struct

        All fields become Option<T> for partial updates.

        Args:
            field: SpecQL field definition

        Returns:
            Field line like "pub email: Option<String>,"
        """
        # Handle foreign key references
        if field.type_name == "ref" and field.reference_entity:
            field_name = f"fk_{to_snake_case(field.reference_entity)}"
        else:
            field_name = to_snake_case(field.name)

        # Get Rust type (always required=True since we want the base type for Option<T>)
        diesel_type = self.type_mapper.map_field_type(
            field.type_name,
            required=True,  # We want the base type, then wrap in Option
            ref_entity=field.reference_entity if field.type_name == "ref" else None,
        )

        rust_type = self.type_mapper.get_rust_native_type(diesel_type)

        # All fields are optional in updates
        return f"pub {field_name}: Option<{rust_type}>,"

    def generate_all_models(
        self,
        entity: Entity,
        include_imports: bool = True,
        with_serde: bool = False,
        include_soft_delete: bool = False,
    ) -> str:
        """
        Generate all three Diesel model structs for an entity

        Creates Queryable, Insertable, and AsChangeset structs in one file.

        Args:
            entity: SpecQL entity definition
            include_imports: Whether to include use statements
            with_serde: Whether Insertable should derive Serialize/Deserialize
            include_soft_delete: Whether AsChangeset should include soft delete fields

        Returns:
            Complete models.rs file content
        """
        parts = []

        # File header
        parts.append("// Generated by SpecQL")
        parts.append("// DO NOT EDIT MANUALLY")
        parts.append("")
        parts.append(f"// Models for {entity.name} entity")
        parts.append("")

        # Queryable struct
        parts.append(
            self.generate_queryable_struct(entity, include_imports=include_imports)
        )
        parts.append("")

        # Insertable struct
        parts.append(
            self.generate_insertable_struct(
                entity,
                include_imports=False,  # Imports already included
                with_serde=with_serde,
            )
        )
        parts.append("")

        # AsChangeset struct
        parts.append(
            self.generate_as_changeset_struct(
                entity,
                include_imports=False,  # Imports already included
                include_soft_delete=include_soft_delete,
            )
        )

        return "\n".join(parts)

    def _generate_audit_fields(self) -> List[str]:
        """Generate Trinity pattern audit fields"""
        return [
            "pub created_at: NaiveDateTime,",
            "pub created_by: Option<Uuid>,",
            "pub updated_at: NaiveDateTime,",
            "pub updated_by: Option<Uuid>,",
            "pub deleted_at: Option<NaiveDateTime>,",
            "pub deleted_by: Option<Uuid>,",
        ]

    def generate_insertable_struct(
        self, entity: Entity, include_imports: bool = False, with_serde: bool = False
    ) -> str:
        """
        Generate Diesel Insertable struct

        This struct represents data for INSERT operations.
        Excludes auto-generated fields (pk, id, timestamps).
        Includes user fields and creator tracking.

        Args:
            entity: SpecQL entity definition
            include_imports: Whether to include use statements
            with_serde: Whether to include Serialize/Deserialize derives

        Returns:
            Complete Insertable struct definition
        """
        struct_name = f"New{to_pascal_case(entity.name)}"
        table_name = f"tb_{to_snake_case(entity.name)}"

        parts = []

        # Imports (if requested)
        if include_imports:
            parts.append(self._generate_imports(entity, with_serde=with_serde))
            parts.append("")

        # Documentation
        parts.append(f"/// Insertable struct for {table_name} table")
        parts.append("/// Used for INSERT operations")

        # Derives
        derives = ["Debug", "Insertable"]
        if with_serde:
            derives.extend(["Serialize", "Deserialize"])

        parts.append(f"#[derive({', '.join(derives)})]")
        parts.append(f"#[diesel(table_name = {table_name})]")

        # Struct declaration
        parts.append(f"pub struct {struct_name} {{")

        # Fields (only user fields + creator tracking)
        field_lines = self._generate_insertable_fields(entity)
        for field_line in field_lines:
            parts.append(f"    {field_line}")

        parts.append("}")

        return "\n".join(parts)

    def _generate_insertable_fields(self, entity: Entity) -> List[str]:
        """
        Generate fields for Insertable struct

        Includes:
        - User-defined fields
        - created_by, updated_by (user tracking)

        Excludes:
        - pk_* (auto-generated)
        - id (auto-generated UUID)
        - created_at, updated_at (auto-generated timestamps)
        - deleted_at, deleted_by (soft delete fields)

        Returns:
            List of field definition strings
        """
        fields = []

        # User-defined fields
        for field in entity.fields.values():
            field_def = self._generate_queryable_field(field)  # Same logic
            fields.append(field_def)

        # Creator tracking
        fields.append("pub created_by: Option<Uuid>,")
        fields.append("pub updated_by: Option<Uuid>,")

        return fields
