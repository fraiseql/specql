"""
Rust Query Generator

Generates Diesel query builder functions for CRUD operations.
"""

from typing import List
from src.core.ast_models import Entity
from src.generators.naming_utils import to_snake_case, to_pascal_case


class RustQueryGenerator:
    """
    Generates Diesel query builder functions

    Creates helper functions that encapsulate common CRUD patterns
    for database operations using Diesel's strongly-typed DSL.

    Example output:
        pub struct ContactQueries;

        impl ContactQueries {
            pub fn find_by_id(...) -> QueryResult<Contact> { ... }
            pub fn create(...) -> QueryResult<Contact> { ... }
            // ... more methods
        }
    """

    def generate_find_by_id(self, entity: Entity) -> str:
        """Generate find_by_id query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Find {snake_name} by UUID
    /// Returns the {snake_name} if found and not soft deleted
    pub fn find_by_id(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<{struct_name}> {{
        {table_name}::table
            .filter({table_name}::id.eq({id_param}))
            .filter({table_name}::deleted_at.is_null())
            .first::<{struct_name}>(conn)
    }}"""

    def generate_list_active(self, entity: Entity) -> str:
        """Generate list_active query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"

        return f"""    /// List all active {snake_name}s
    /// Returns all non-deleted {snake_name}s ordered by creation time
    pub fn list_active(
        conn: &mut PgConnection
    ) -> QueryResult<Vec<{struct_name}>> {{
        {table_name}::table
            .filter({table_name}::deleted_at.is_null())
            .order({table_name}::created_at.desc())
            .load::<{struct_name}>(conn)
    }}"""

    def generate_create(self, entity: Entity) -> str:
        """Generate create query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        new_struct = f"New{struct_name}"
        param_name = f"new_{snake_name}"

        return f"""    /// Create new {snake_name}
    /// Inserts a new {snake_name} and returns the created record
    pub fn create(
        conn: &mut PgConnection,
        {param_name}: {new_struct}
    ) -> QueryResult<{struct_name}> {{
        diesel::insert_into({table_name}::table)
            .values(&{param_name})
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_update(self, entity: Entity) -> str:
        """Generate update query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        update_struct = f"Update{struct_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Update {snake_name}
    /// Updates a {snake_name} by UUID with the provided changeset
    pub fn update(
        conn: &mut PgConnection,
        {id_param}: Uuid,
        changeset: {update_struct}
    ) -> QueryResult<{struct_name}> {{
        diesel::update({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .set(&changeset)
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_soft_delete(self, entity: Entity) -> str:
        """Generate soft delete query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Soft delete {snake_name}
    /// Marks a {snake_name} as deleted by setting deleted_at timestamp
    pub fn soft_delete(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<{struct_name}> {{
        use chrono::Utc;
        diesel::update({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .set({table_name}::deleted_at.eq(Utc::now().naive_utc()))
            .get_result::<{struct_name}>(conn)
    }}"""

    def generate_hard_delete(self, entity: Entity) -> str:
        """Generate hard delete query"""
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        id_param = f"{snake_name}_id"

        return f"""    /// Hard delete {snake_name}
    /// Permanently deletes a {snake_name} from the database
    /// WARNING: This action cannot be undone
    pub fn hard_delete(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<usize> {{
        diesel::delete({table_name}::table)
            .filter({table_name}::id.eq({id_param}))
            .execute(conn)
    }}"""

    def generate_query_struct(self, entity: Entity) -> str:
        """Generate complete query struct with all methods"""
        struct_name = to_pascal_case(entity.name)
        to_snake_case(entity.name)

        parts = [
            f"/// Query builders for {struct_name} entity",
            f"pub struct {struct_name}Queries;",
            "",
            f"impl {struct_name}Queries {{",
            self.generate_find_by_id(entity),
            "",
            self.generate_list_active(entity),
            "",
            self.generate_create(entity),
            "",
            self.generate_update(entity),
            "",
            self.generate_soft_delete(entity),
            "",
            self.generate_hard_delete(entity),
            "}",
        ]

        return "\n".join(parts)

    def generate_imports(self, entity: Entity) -> str:
        """Generate required imports for query file"""
        struct_name = to_pascal_case(entity.name)

        imports = [
            "use diesel::prelude::*;",
            "use diesel::result::QueryResult;",
            "use uuid::Uuid;",
            f"use super::models::{{{struct_name}, New{struct_name}, Update{struct_name}}};",
            f"use super::schema::{entity.schema}::tb_{to_snake_case(entity.name)};",
        ]

        return "\n".join(imports)

    def generate_find_by_foreign_key(
        self, entity: Entity, field_name: str, ref_entity: str
    ) -> str:
        """Generate find by foreign key query"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        table_name = f"tb_{snake_name}"
        ref_table = f"tb_{to_snake_case(ref_entity)}"
        fk_field = f"fk_{to_snake_case(ref_entity)}"
        id_param = f"{to_snake_case(ref_entity)}_id"

        return f"""    /// Find {snake_name}s by {ref_entity}
    /// Returns all {snake_name}s associated with the given {ref_entity}
    pub fn find_by_{to_snake_case(ref_entity)}(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<Vec<{struct_name}>> {{
        use super::schema::{entity.schema}::{ref_table};

        {table_name}::table
            .inner_join({ref_table}::table.on({table_name}::{fk_field}.eq({ref_table}::pk_{to_snake_case(ref_entity)})))
            .filter({ref_table}::id.eq({id_param}))
            .filter({table_name}::deleted_at.is_null())
            .select({struct_name}::as_select())
            .load::<{struct_name}>(conn)
    }}"""

    def generate_find_children(
        self, parent_entity: Entity, children_name: str, child_entity: str
    ) -> str:
        """Generate find children query for parent entity"""
        to_pascal_case(parent_entity.name)
        parent_snake = to_snake_case(parent_entity.name)
        parent_table = f"tb_{parent_snake}"
        child_table = f"tb_{to_snake_case(child_entity)}"
        fk_field = f"fk_{parent_snake}"
        id_param = f"{parent_snake}_id"

        return f"""    /// Find {children_name} for {parent_snake}
    /// Returns all {children_name} associated with this {parent_snake}
    pub fn find_{children_name}(
        conn: &mut PgConnection,
        {id_param}: Uuid
    ) -> QueryResult<Vec<{child_entity}>> {{
        use super::schema::{parent_entity.schema}::{child_table};

        {parent_table}::table
            .inner_join({child_table}::table.on({parent_table}::pk_{parent_snake}.eq({child_table}::{fk_field})))
            .filter({parent_table}::id.eq({id_param}))
            .filter({child_table}::deleted_at.is_null())
            .select({child_entity}::as_select())
            .load::<{child_entity}>(conn)
    }}"""

    def generate_relationship_imports(
        self, entity: Entity, related_entities: List[str]
    ) -> str:
        """Generate imports for relationship queries"""
        struct_name = to_pascal_case(entity.name)
        schema_name = entity.schema

        imports = [
            "use diesel::prelude::*;",
            "use diesel::result::QueryResult;",
            "use uuid::Uuid;",
            f"use super::models::{struct_name};",
        ]

        # Schema imports
        tables = [f"tb_{to_snake_case(entity.name)}"]
        tables.extend([f"tb_{to_snake_case(rel)}" for rel in related_entities])
        schema_import = f"use super::schema::{schema_name}::{{{', '.join(tables)}}};"
        imports.append(schema_import)

        return "\n".join(imports)

    def generate_relationship_queries(self, entity: Entity) -> str:
        """Generate relationship queries for entity"""
        methods = []

        # Generate find_by_* methods for each ref field
        for field_name, field_def in entity.fields.items():
            if field_def.type_name == "ref" and field_def.reference_entity:
                method = self.generate_find_by_foreign_key(
                    entity, field_name, field_def.reference_entity
                )
                methods.append(method)
                methods.append("")  # Add spacing

        if methods:
            methods.pop()  # Remove last empty string

        return "\n".join(methods)

    def generate_queries_file(self, entity: Entity) -> str:
        """Generate complete queries.rs file"""
        parts = [
            "// Generated by SpecQL",
            "// DO NOT EDIT MANUALLY",
            "",
            f"// Query builders for {entity.name} entity",
            "",
            self.generate_imports(entity),
            "",
            self.generate_query_struct(entity),
        ]

        # Add relationship queries if any exist
        relationship_queries = self.generate_relationship_queries(entity)
        if relationship_queries.strip():
            parts.extend(
                [
                    "",
                    "// Relationship queries",
                    relationship_queries,
                ]
            )

        return "\n".join(parts)
