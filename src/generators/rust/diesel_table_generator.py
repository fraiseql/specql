"""
Diesel Table Generator

Generates Diesel table! macro definitions from SpecQL entity definitions.
"""

from typing import List
from src.core.ast_models import Entity, FieldDefinition
from src.generators.rust.diesel_type_mapper import DieselTypeMapper
from src.generators.naming_utils import camel_to_snake


class DieselTableGenerator:
    """
    Generates Diesel table! macro definitions

    Example output:
        diesel::table! {
            crm.tb_contact (pk_contact) {
                pk_contact -> Int4,
                id -> Uuid,
                email -> Varchar,
                fk_company -> Nullable<Int4>,
                created_at -> Timestamptz,
                // ... more fields
            }
        }
    """

    def __init__(self):
        self.type_mapper = DieselTypeMapper()

    def generate_table(self, entity: Entity) -> str:
        """
        Generate Diesel table! macro for entity

        Args:
            entity: SpecQL entity definition

        Returns:
            Complete table! macro as string
        """
        table_name = self._get_table_name(entity)
        pk_field = self._get_pk_field_name(entity)

        # Generate field lines
        fields = self._generate_fields(entity)
        field_lines = "\n".join(f"        {f}" for f in fields)

        return f"""diesel::table! {{
    {entity.schema}.{table_name} ({pk_field}) {{
{field_lines}
    }}
}}"""

    def _get_table_name(self, entity: Entity) -> str:
        """Get Diesel table name (tb_entity_name)"""
        snake_name = camel_to_snake(entity.name)
        return f"tb_{snake_name}"

    def _get_pk_field_name(self, entity: Entity) -> str:
        """Get primary key field name"""
        snake_name = camel_to_snake(entity.name)
        return f"pk_{snake_name}"

    def _generate_fields(self, entity: Entity) -> List[str]:
        """
        Generate all field definitions in correct order

        Order:
        1. Primary key (pk_*)
        2. UUID identifier (id)
        3. User-defined fields
        4. Audit fields (created_at, updated_at, etc.)

        Returns:
            List of field definition strings
        """
        fields = []

        # 1. Primary key
        pk_field = self._get_pk_field_name(entity)
        fields.append(f"{pk_field} -> Int4,")

        # 2. UUID identifier
        fields.append("id -> Uuid,")

        # 3. User-defined fields
        for field in entity.fields.values():
            field_line = self._generate_field(field)
            fields.append(field_line)

        # 4. Audit fields (Trinity pattern)
        fields.extend(self._generate_audit_fields())

        return fields

    def _generate_field(self, field: FieldDefinition) -> str:
        """
        Generate single field definition

        Args:
            field: SpecQL field definition

        Returns:
            Field line like "email -> Varchar,"
        """
        # Handle foreign key references
        # Strip nullable syntax first
        base_type = field.type_name
        if base_type.endswith("?"):
            base_type = base_type[:-1]

        if base_type.startswith("ref(") and base_type.endswith(")"):
            # Extract entity name from ref(EntityName) syntax
            ref_entity = base_type[4:-1]
            field_name = f"fk_{camel_to_snake(ref_entity)}"
        elif base_type == "ref" and field.reference_entity:
            field_name = f"fk_{camel_to_snake(field.reference_entity)}"
        else:
            field_name = camel_to_snake(field.name)

        # Map type
        diesel_type = self.type_mapper.map_field_type(
            field.type_name,
            required=not field.nullable,
            ref_entity=field.reference_entity if field.type_name == "ref" else None,
        )

        type_str = diesel_type.to_rust_string()

        return f"{field_name} -> {type_str},"

    def _generate_audit_fields(self) -> List[str]:
        """
        Generate Trinity pattern audit fields

        Returns:
            List of 6 audit field definitions
        """
        return [
            "created_at -> Timestamptz,",
            "created_by -> Nullable<Uuid>,",
            "updated_at -> Timestamptz,",
            "updated_by -> Nullable<Uuid>,",
            "deleted_at -> Nullable<Timestamptz>,",
            "deleted_by -> Nullable<Uuid>,",
        ]

    def generate_schema_file(self, entities: List[Entity]) -> str:
        """
        Generate complete schema.rs file with all tables

        Args:
            entities: List of SpecQL entities

        Returns:
            Complete schema.rs file content
        """
        # Generate table! macros for all entities
        tables = [self.generate_table(entity) for entity in entities]

        # Generate joinable! declarations for foreign keys
        joinables = self._generate_joinables(entities)

        # Generate allow_tables_to_appear_in_same_query!
        allow_tables = self._generate_allow_tables(entities)

        # Combine all parts
        parts = (
            ["// Generated by SpecQL", "// DO NOT EDIT MANUALLY", ""]
            + tables
            + [""]
            + joinables
            + [""]
            + [allow_tables]
        )

        # Diesel expects allow_tables_to_appear_in_same_query! to come after joinable!
        # So we need to reorder if joinables exist
        if joinables:
            # Find the joinables and allow_tables in the parts
            result = "\n".join(parts)
            # The order is already correct, so this should work
        else:
            result = "\n".join(parts)

        return result

        return "\n".join(parts)

    def _generate_joinables(self, entities: List[Entity]) -> List[str]:
        """
        Generate diesel::joinable! declarations

        Example:
            diesel::joinable!(tb_contact -> tb_company (fk_company));
        """
        joinables = []

        for entity in entities:
            table_name = self._get_table_name(entity)

            # Find all ref fields
            for field in entity.fields.values():
                # Strip nullable syntax first
                base_type = field.type_name
                if base_type.endswith("?"):
                    base_type = base_type[:-1]

                if base_type.startswith("ref(") and base_type.endswith(")"):
                    ref_entity = base_type[4:-1]
                    ref_table = f"tb_{camel_to_snake(ref_entity)}"
                    fk_field = f"fk_{camel_to_snake(ref_entity)}"

                    joinable = (
                        f"diesel::joinable!({table_name} -> {ref_table} ({fk_field}));"
                    )
                    joinables.append(joinable)
                elif base_type == "ref" and field.reference_entity:
                    ref_table = f"tb_{camel_to_snake(field.reference_entity)}"
                    fk_field = f"fk_{camel_to_snake(field.reference_entity)}"

                    joinable = (
                        f"diesel::joinable!({table_name} -> {ref_table} ({fk_field}));"
                    )
                    joinables.append(joinable)

        return joinables

    def _generate_allow_tables(self, entities: List[Entity]) -> str:
        """
        Generate allow_tables_to_appear_in_same_query! macro

        Example:
            diesel::allow_tables_to_appear_in_same_query!(
                tb_contact,
                tb_company,
            );
        """
        table_names = [self._get_table_name(e) for e in entities]
        tables_list = ",\n    ".join(table_names)

        return f"""diesel::allow_tables_to_appear_in_same_query!(
    {tables_list},
);"""
