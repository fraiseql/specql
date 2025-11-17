"""
Rust AST Parser for SpecQL

Parses Rust structs and Diesel schema macros using subprocess and syn crate.
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.ast_models import Entity, FieldDefinition, FieldTier


class RustFieldInfo:
    """Represents a parsed Rust field."""

    def __init__(
        self,
        name: str,
        field_type: str,
        is_optional: bool = False,
        attributes: Optional[List[str]] = None,
    ):
        self.name = name
        self.field_type = field_type
        self.is_optional = is_optional
        self.attributes = attributes or []


class RustStructInfo:
    """Represents a parsed Rust struct."""

    def __init__(
        self,
        name: str,
        fields: List[RustFieldInfo],
        attributes: Optional[List[str]] = None,
    ):
        self.name = name
        self.fields = fields
        self.attributes = attributes or []


class DieselColumnInfo:
    """Represents a parsed Diesel column from table! macro."""

    def __init__(
        self,
        name: str,
        sql_type: str,
        is_nullable: bool = False,
    ):
        self.name = name
        self.sql_type = sql_type
        self.is_nullable = is_nullable


class DieselTableInfo:
    """Represents a parsed Diesel table from table! macro."""

    def __init__(
        self,
        name: str,
        primary_key: List[str],
        columns: List[DieselColumnInfo],
    ):
        self.name = name
        self.primary_key = primary_key
        self.columns = columns


class DieselDeriveInfo:
    """Represents Diesel derive macros on a struct."""

    def __init__(
        self,
        struct_name: str,
        derives: List[str],
        associations: List[str],
    ):
        self.struct_name = struct_name
        self.derives = derives
        self.associations = associations


class ImplMethodInfo:
    """Represents a method in an impl block."""

    def __init__(
        self,
        name: str,
        visibility: str,
        parameters: List[dict],
        return_type: str,
        is_async: bool,
    ):
        self.name = name
        self.visibility = visibility
        self.parameters = parameters
        self.return_type = return_type
        self.is_async = is_async


class ImplBlockInfo:
    """Represents an impl block."""

    def __init__(
        self,
        type_name: str,
        methods: List[ImplMethodInfo],
        trait_impl: Optional[str],
    ):
        self.type_name = type_name
        self.methods = methods
        self.trait_impl = trait_impl


@dataclass
class DieselTable:
    """Represents a parsed Diesel table! macro"""

    table_name: str
    primary_key: str
    columns: List[Dict[str, Any]]


class RustEnumInfo:
    """Represents a parsed Rust enum."""

    def __init__(
        self,
        name: str,
        variants: List["RustEnumVariantInfo"],
        attributes: Optional[List[str]] = None,
    ):
        self.name = name
        self.variants = variants
        self.attributes = attributes or []


class RustEnumVariantInfo:
    """Represents a variant in a Rust enum."""

    def __init__(
        self,
        name: str,
        fields: Optional[List[RustFieldInfo]] = None,
        discriminant: Optional[str] = None,
    ):
        self.name = name
        self.fields = fields
        self.discriminant = discriminant


class RouteHandlerInfo:
    """Represents a parsed route handler."""

    def __init__(
        self,
        method: str,
        path: str,
        function_name: str,
        is_async: bool,
        return_type: str,
        parameters: List[dict],
    ):
        self.method = method
        self.path = path
        self.function_name = function_name
        self.is_async = is_async
        self.return_type = return_type
        self.parameters = parameters


class RustParser:
    """Parser for Rust code using subprocess and syn crate."""

    def __init__(self):
        # Initialize type mappings
        self.type_mapping = RustTypeMapper().type_mapping
        self.type_mapper = RustTypeMapper()

    def parse_file(
        self, file_path: Path
    ) -> Tuple[
        List[RustStructInfo],
        List["RustEnumInfo"],
        List[DieselTableInfo],
        List[DieselDeriveInfo],
        List[ImplBlockInfo],
        List[RouteHandlerInfo],
    ]:
        """
        Parse a Rust source file and extract struct definitions, enums, Diesel tables, Diesel derives, impl blocks, and route handlers.

        Args:
            file_path: Path to the Rust file

        Returns:
            Tuple of (List of parsed struct information, List of enum information, List of Diesel table information, List of Diesel derive information, List of impl block information, List of route handler information)
        """
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Extract components using regex
        structs = []  # Not implemented yet
        enums = []    # Not implemented yet
        diesel_tables = []  # Not implemented yet
        diesel_derives = []  # Not implemented yet
        impl_blocks = self._extract_impl_blocks(source_code)
        route_handlers = self._extract_route_handlers(source_code)

        return structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers

    def parse_source(
        self, source_code: str
    ) -> Tuple[
        List[RustStructInfo],
        List[RustEnumInfo],
        List[DieselTableInfo],
        List[DieselDeriveInfo],
        List[ImplBlockInfo],
        List[RouteHandlerInfo],
    ]:
        """
        Parse Rust source code and extract struct definitions, enums, Diesel tables, Diesel derives, impl blocks, and route handlers.

        Args:
            source_code: Rust source code as string

        Returns:
            Tuple of (List of parsed struct information, List of enum information, List of Diesel table information, List of Diesel derive information, List of impl block information, List of route handler information)
        """
        # For now, create a temporary file and parse it
        # TODO: Modify Rust binary to accept source code via stdin
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(source_code)
            temp_path = f.name

        try:
            return self.parse_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def extract_derive_macros(self, rust_code: str) -> List[str]:
        """Extract derive macros from struct definition"""
        derive_pattern = r"#\[derive\(([^)]+)\)\]"
        matches = re.findall(derive_pattern, rust_code)
        derives = []
        for match in matches:
            derives.extend([d.strip() for d in match.split(",")])
        return derives

    def _parse_rust_type_with_generics(self, type_str: str) -> Dict[str, Any]:
        """Parse Rust types with complex generics"""
        type_str = re.sub(r"&'[a-z]\s+", "&", type_str)
        type_str = type_str.replace("&", "")

        if type_str.startswith("Option<"):
            inner_content = self._extract_inner_generic(type_str, "Option<")
            if inner_content:
                inner_type_info = self._parse_rust_type_with_generics(inner_content)
                return {"type": inner_type_info["type"], "required": False}

        if type_str.startswith("Vec<"):
            inner_content = self._extract_inner_generic(type_str, "Vec<")
            if inner_content:
                return {"type": "list", "element_type": self.type_mapper.map_type(inner_content)}

        if type_str.startswith("HashMap<"):
            return {"type": "json"}

        return {"type": self.type_mapper.map_type(type_str), "required": True}

    def _extract_inner_generic(self, type_str: str, prefix: str) -> Optional[str]:
        """Extract inner content of generic types"""
        if not type_str.startswith(prefix):
            return None
        start_idx = len(prefix)
        bracket_count = 1
        end_idx = start_idx
        for i in range(start_idx, len(type_str)):
            if type_str[i] == "<":
                bracket_count += 1
            elif type_str[i] == ">":
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i
                    break
        if bracket_count == 0:
            return type_str[start_idx:end_idx]
        return None

    def _detect_embedded_struct(self, field_type: str, rust_code: str) -> bool:
        """Check if field type is a custom struct"""
        struct_pattern = rf"pub\s+struct\s+{field_type}\s*\{{"
        return bool(re.search(struct_pattern, rust_code))

    def extract_associations(self, rust_code: str) -> List[Dict[str, Any]]:
        """Extract Diesel association macros"""
        associations = []
        belongs_pattern = r'#\[belongs_to\((\w+)(?:,\s*foreign_key\s*=\s*"(\w+)")?\)\]'
        matches = re.findall(belongs_pattern, rust_code)
        for entity, fk in matches:
            associations.append(
                {
                    "type": "belongs_to",
                    "entity": entity,
                    "foreign_key": fk or f"{entity.lower()}_id",
                }
            )
        return associations

    def _extract_route_handlers(self, source_code: str) -> List[RouteHandlerInfo]:
        """Extract Actix-web route handlers from source code"""
        route_handlers = []

        # Pattern for Actix-web route macros: #[get("/path")], #[post("/path")], etc.
        # Capture 'async' keyword if present
        route_pattern = r'#\[(get|post|put|delete|patch)\("([^"]+)"\)\]\s+pub\s+(async\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*->\s*([^{]+)'

        matches = re.finditer(route_pattern, source_code, re.MULTILINE)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            is_async_keyword = match.group(3)  # 'async ' or None
            function_name = match.group(4)
            params_str = match.group(5)
            return_type = match.group(6).strip()

            # Check if async
            is_async = is_async_keyword is not None

            # Parse parameters
            parameters = []
            if params_str.strip():
                # Simple parameter parsing (name: type)
                param_pairs = params_str.split(',')
                for param in param_pairs:
                    param = param.strip()
                    if ':' in param:
                        param_parts = param.split(':', 1)
                        param_name = param_parts[0].strip()
                        param_type = param_parts[1].strip()
                        parameters.append({
                            "name": param_name,
                            "param_type": param_type
                        })

            route_handlers.append(RouteHandlerInfo(
                method=method,
                path=path,
                function_name=function_name,
                parameters=parameters,
                return_type=return_type,
                is_async=is_async
            ))

        return route_handlers

    def _extract_impl_blocks(self, source_code: str) -> List[ImplBlockInfo]:
        """Extract impl blocks and their methods from source code"""
        impl_blocks = []

        # Pattern for impl blocks: impl StructName { ... }
        # We'll use a simpler approach: find impl keyword, then manually count braces
        impl_start_pattern = r'impl\s+(\w+)\s*\{'

        impl_start_matches = list(re.finditer(impl_start_pattern, source_code))

        for impl_start in impl_start_matches:
            struct_name = impl_start.group(1)
            start_pos = impl_start.end()  # Position after opening brace

            # Find matching closing brace
            brace_count = 1
            pos = start_pos
            while pos < len(source_code) and brace_count > 0:
                if source_code[pos] == '{':
                    brace_count += 1
                elif source_code[pos] == '}':
                    brace_count -= 1
                pos += 1

            if brace_count == 0:
                impl_body = source_code[start_pos:pos-1]
            else:
                continue  # Malformed impl block

            # Extract methods from impl block
            methods = []

            # Pattern for pub methods: pub fn method_name(params) -> return_type { ... }
            method_pattern = r'(pub(?:\(crate\))?)\s+(?:(async)\s+)?fn\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^{;]+))?'

            method_matches = re.finditer(method_pattern, impl_body, re.MULTILINE)

            for method_match in method_matches:
                visibility = method_match.group(1).strip()
                is_async = method_match.group(2) == 'async'
                method_name = method_match.group(3)
                params_str = method_match.group(4)
                return_type = method_match.group(5).strip() if method_match.group(5) else '()'

                # Only extract pub methods (not pub(crate))
                if visibility != 'pub':
                    continue

                # Parse parameters
                parameters = []
                if params_str.strip():
                    param_pairs = params_str.split(',')
                    for param in param_pairs:
                        param = param.strip()
                        if ':' in param:
                            param_parts = param.split(':', 1)
                            param_name = param_parts[0].strip()
                            param_type = param_parts[1].strip()
                            parameters.append({
                                "name": param_name,
                                "param_type": param_type
                            })

                methods.append(ImplMethodInfo(
                    name=method_name,
                    visibility=visibility,
                    parameters=parameters,
                    return_type=return_type,
                    is_async=is_async
                ))

            impl_blocks.append(ImplBlockInfo(
                type_name=struct_name,
                methods=methods,
                trait_impl=None  # We're not parsing trait impls yet
            ))

        return impl_blocks

    def parse_rust_struct(self, rust_code: str) -> Dict[str, Any]:
        """Parse Rust struct with Diesel derives"""
        struct_pattern = r"pub\s+struct\s+(\w+)\s*\{([^}]+)\}"
        struct_matches = list(re.finditer(struct_pattern, rust_code, re.DOTALL))

        if not struct_matches:
            raise ValueError("No struct definition found")

        # Prefer struct with table_name attribute
        target_match = None
        for match in struct_matches:
            struct_start = match.start()
            search_area = rust_code[max(0, struct_start - 200) : struct_start]
            if "#[table_name" in search_area:
                target_match = match
                break

        if not target_match:
            target_match = struct_matches[-1]

        struct_name = target_match.group(1)
        fields_block = target_match.group(2)

        # Extract table_name
        struct_start = target_match.start()
        search_area = rust_code[max(0, struct_start - 200) : struct_start]
        table_match = re.search(r'#\[table_name\s*=\s*"(\w+)"\]', search_area)
        table_name = table_match.group(1) if table_match else None

        derives = self.extract_derive_macros(rust_code)
        associations = self.extract_associations(rust_code)
        fields = self._parse_rust_struct_fields(fields_block, rust_code)

        # Apply associations
        for assoc in associations:
            if assoc["type"] == "belongs_to":
                fk_field_name = assoc["foreign_key"]
                for field in fields:
                    if field["name"] == fk_field_name:
                        field["type"] = f"ref({assoc['entity']})"
                        break

        return {
            "entity": struct_name,
            "fields": fields,
            "_metadata": {
                "source_language": "rust",
                "table_name": table_name,
                "derives": derives,
                "associations": associations,
            },
        }

    def _parse_rust_struct_fields(
        self, fields_block: str, rust_code: str = ""
    ) -> List[Dict[str, Any]]:
        """Parse Rust struct fields"""
        fields = []

        # Split by lines and parse each field individually
        lines = [line.strip() for line in fields_block.split("\n") if line.strip()]

        for line in lines:
            if not line.startswith("pub "):
                continue

            # Find the colon
            colon_idx = line.find(":")
            if colon_idx == -1:
                continue

            field_name = line[4:colon_idx].strip()  # Remove 'pub '
            field_type = line[colon_idx + 1 :].strip().rstrip(",")

            type_info = self._parse_rust_type_with_generics(field_type)
            specql_type = type_info["type"]
            required = type_info.get("required", True)

            if self._detect_embedded_struct(field_type, rust_code):
                specql_type = "composite"
                required = True

            if field_name.endswith("_id") and specql_type == "integer":
                ref_entity = field_name[:-3].capitalize()
                specql_type = f"ref({ref_entity})"

            fields.append(
                {
                    "name": field_name,
                    "type": specql_type,
                    "required": required,
                    "original_type": field_type,
                }
            )

        return fields

    def parse_diesel_schema(self, rust_code: str) -> DieselTable:
        """
        Parse Diesel table! macro

        Pattern:
        table! {
            table_name (primary_key) {
                column_name -> ColumnType,
                ...
            }
        }
        """
        # Extract table! macro content
        table_pattern = r"table!\s*\{\s*(\w+)\s*\((\w+)\)\s*\{([^}]+)\}\s*\}"
        match = re.search(table_pattern, rust_code, re.DOTALL)

        if not match:
            raise ValueError("No table! macro found in Rust code")

        table_name = match.group(1)
        primary_key = match.group(2)
        columns_block = match.group(3)

        # Parse columns
        columns = self._parse_diesel_columns(columns_block)

        return DieselTable(table_name=table_name, primary_key=primary_key, columns=columns)

    def _parse_diesel_columns(self, columns_block: str) -> List[Dict[str, Any]]:
        """
        Parse column definitions from Diesel table! macro

        Patterns:
        - id -> Int4,
        - email -> Varchar,
        - company_id -> Nullable<Int4>,
        - tags -> Array<Text>,
        """
        columns = []

        # Pattern: column_name -> ColumnType,
        column_pattern = r"(\w+)\s*->\s*([^,]+),?"
        matches = re.findall(column_pattern, columns_block)

        for col_name, col_type in matches:
            col_type = col_type.strip()

            # Check if nullable
            required = True
            if col_type.startswith("Nullable<"):
                required = False
                # Extract inner type: Nullable<Int4> -> Int4
                nullable_match = re.search(r"Nullable<(.+)>", col_type)
                if nullable_match:
                    col_type = nullable_match.group(1)

            # Map Diesel type to SpecQL type
            specql_type = self._map_diesel_type(col_type)

            columns.append(
                {
                    "name": col_name,
                    "type": specql_type,
                    "required": required,
                    "original_type": col_type,
                }
            )

        return columns

    def _map_diesel_type(self, diesel_type: str) -> str:
        """
        Map Diesel SQL types to SpecQL types

        Common Diesel types:
        - Int4, Int8, BigInt -> integer
        - Varchar, Text -> text
        - Timestamp, Timestamptz -> timestamp
        - Bool -> boolean
        - Numeric, Float4, Float8 -> float
        - Uuid -> uuid
        - Json, Jsonb -> json
        - Array<T> -> list
        """
        # Handle Array<T>
        if diesel_type.startswith("Array<"):
            return "list"

        # Direct mapping
        return self.type_mapper.map_diesel_type(diesel_type)


class RustToSpecQLMapper:
    """Maps parsed Rust structs to SpecQL entities."""

    def __init__(self):
        self.type_mapper = RustTypeMapper()

    def map_struct_to_entity(self, struct: RustStructInfo) -> Entity:
        """
        Convert a Rust struct to a SpecQL entity.

        Args:
            struct: Parsed Rust struct information

        Returns:
            SpecQL Entity
        """
        fields = {}
        for rust_field in struct.fields:
            field = self._map_field(rust_field)
            fields[field.name] = field

        return Entity(
            name=struct.name,
            schema="public",
            table=self._derive_table_name(struct.name),
            fields=fields,
            description=f"Rust struct {struct.name}",
        )

    def map_diesel_table_to_entity(self, table: DieselTableInfo) -> Entity:
        """
        Convert a Diesel table! macro to a SpecQL entity.

        Args:
            table: Parsed Diesel table information

        Returns:
            SpecQL Entity
        """
        fields = {}

        for diesel_col in table.columns:
            # Map Diesel SQL type to SpecQL type
            type_name = self.type_mapper.map_diesel_type(diesel_col.sql_type)

            # Create FieldDefinition
            field_def = FieldDefinition(
                name=diesel_col.name,
                type_name=type_name,
                nullable=diesel_col.is_nullable,
                description=f"Diesel column {diesel_col.name} of type {diesel_col.sql_type}",
            )

            # Mark primary key fields
            if diesel_col.name in table.primary_key:
                # Primary keys are typically not nullable
                field_def.nullable = False

            # Detect FK from naming convention in Diesel tables
            if diesel_col.name.endswith("_id"):
                # For Diesel tables, FK field user_id typically references users table
                singular_name = diesel_col.name[:-3]  # Remove '_id'
                # Simple pluralization: add 's' if not already plural
                if not singular_name.endswith("s"):
                    table_name = singular_name + "s"
                else:
                    table_name = singular_name
                field_def.reference_entity = table_name
                field_def.tier = FieldTier.REFERENCE

            fields[field_def.name] = field_def

        return Entity(
            name=self._snake_to_pascal(table.name),  # Convert table name to PascalCase
            schema="public",
            table=table.name,  # Use original table name
            fields=fields,
            description=f"Diesel table {table.name}",
        )

    def _snake_to_pascal(self, name: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("_"))

    def _map_field(self, rust_field: RustFieldInfo) -> FieldDefinition:
        """Map a Rust field to a SpecQL field."""
        type_name = self.type_mapper.map_type(rust_field.field_type)

        # Create FieldDefinition
        field_def = FieldDefinition(
            name=rust_field.name,
            type_name=type_name,
            nullable=rust_field.is_optional,
            description=f"Rust field {rust_field.name} of type {rust_field.field_type}",
        )

        # Parse attributes for additional metadata
        self._parse_field_attributes(field_def, rust_field.attributes)

        # Detect foreign keys from naming convention (if not already set by belongs_to)
        if not field_def.reference_entity and rust_field.name.endswith("_id"):
            # Extract entity name: user_id -> user
            entity_name = rust_field.name[:-3]  # Remove '_id'
            field_def.reference_entity = entity_name
            field_def.tier = FieldTier.REFERENCE

        return field_def

    def _parse_field_attributes(self, field_def: FieldDefinition, attributes: List[str]):
        """Parse Rust field attributes for SpecQL metadata."""
        for attr in attributes:
            attr = attr.strip()

            # Primary key attributes
            if "#[primary_key]" in attr:
                # Note: In SpecQL, primary keys are usually handled at entity level
                # This is just for reference
                pass

            # Diesel belongs_to relationships
            elif "belongs_to(" in attr.replace(" ", ""):
                # Parse belongs_to attribute: #[belongs_to(User)]
                # or #[belongs_to(user, foreign_key = "user_id")]
                self._parse_belongs_to_attribute(field_def, attr)

            # Column name override
            elif "#[column_name" in attr:
                # Parse #[column_name = "custom_column"]
                pass  # Could extract custom column name

            # Index attributes
            elif "#[index]" in attr:
                # Parse index information
                pass  # Could mark field as indexed

            # Unique constraints
            elif "#[unique]" in attr:
                # Parse unique constraints
                pass  # Could mark field as unique

    def _parse_belongs_to_attribute(self, field_def: FieldDefinition, attr: str):
        """Parse Diesel belongs_to attribute for foreign key relationships."""
        # Example: #[belongs_to(User)] or #[belongs_to(user, foreign_key = "user_id")]
        # Note: Rust parser may add spaces: "# [belongs_to (User)]"
        try:
            # Handle spaced version first
            attr = (
                attr.replace("# [", "#[").replace("] ", "]").replace(" (", "(").replace(") ", ")")
            )

            # Extract content inside belongs_to(...)
            start = attr.find("belongs_to(")
            if start == -1:
                return

            content = attr[start + 11 :]  # Skip 'belongs_to('
            end = content.find(")")
            if end == -1:
                return

            content = content[:end]

            # Parse the content - could be just "User" or "user, foreign_key = \"user_id\""
            parts = [p.strip() for p in content.split(",")]

            if parts:
                # First part is usually the related entity name
                related_entity = parts[0]

                # Remove quotes if present
                related_entity = related_entity.strip('"').strip("'")

                # Set reference entity (convert to snake_case for table name)
                field_def.reference_entity = self._camel_to_snake(related_entity)
                field_def.tier = FieldTier.REFERENCE

        except Exception:
            # If parsing fails, continue without relationship info
            pass

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _derive_table_name(self, struct_name: str) -> str:
        """Derive table name from struct name (snake_case conversion)."""
        import re

        # Convert CamelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", struct_name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class RustTypeMapper:
    """Maps Rust types to SpecQL field types."""

    def __init__(self):
        # Comprehensive Rust to SQL type mapping
        self.type_mapping = {
            # Integer types
            "i8": "smallint",
            "i16": "smallint",
            "i32": "integer",
            "i64": "bigint",
            "u8": "smallint",
            "u16": "smallint",
            "u32": "integer",
            "u64": "bigint",
            # Floating point types
            "f32": "real",
            "f64": "double_precision",
            # Boolean
            "bool": "boolean",
            # String types
            "String": "text",
            "str": "text",
            "&str": "text",
            # Time types (common in Rust)
            "NaiveDateTime": "timestamp",
            "DateTime": "timestamp with time zone",
            "NaiveDate": "date",
            "NaiveTime": "time",
            # UUID
            "Uuid": "uuid",
            # JSON/binary types
            "Vec": "jsonb",  # Arrays as JSONB
            "HashMap": "jsonb",  # Maps as JSONB
            "BTreeMap": "jsonb",
            "Value": "jsonb",  # serde_json::Value
            # Special types
            "Option": None,  # Handled at field level for nullability
        }

        # Diesel-specific type mappings
        self.diesel_type_mapping = {
            "Integer": "integer",
            "BigInt": "bigint",
            "SmallInt": "smallint",
            "Text": "text",
            "Varchar": "text",
            "Bool": "boolean",
            "Float": "real",
            "Double": "double_precision",
            "Timestamp": "timestamp",
            "Date": "date",
            "Time": "time",
            "Nullable": None,  # Handled for nullability
        }

    def map_type(self, rust_type: str) -> str:
        """
        Map a Rust type to a SpecQL field type.

        Args:
            rust_type: The Rust type name

        Returns:
            Corresponding SpecQL field type as string
        """
        # Handle generic types like Vec<T>, HashMap<K,V>, Option<T>
        if "<" in rust_type and ">" in rust_type:
            base_type = rust_type.split("<")[0].strip()
            inner_content = rust_type[rust_type.find("<") + 1 : rust_type.rfind(">")].strip()

            # Check for malformed generics (empty inner content)
            if not inner_content or inner_content.isspace():
                return "text"

            if base_type == "Option":
                # Option<T> - the inner type will be handled, nullability at field level
                return self.map_type(inner_content)
            elif base_type in ["Vec", "HashMap", "BTreeMap"]:
                # Collections map to jsonb
                return "jsonb"
            else:
                # For other generics, try to map the base type
                mapped = self.type_mapping.get(base_type)
                return mapped if mapped else "text"

        # Handle array syntax [T; N] or [T]
        if rust_type.startswith("[") and rust_type.endswith("]"):
            return "jsonb"  # Arrays as JSONB

        # Direct type mapping
        mapped = self.type_mapping.get(rust_type)
        if mapped:
            return mapped

        # Fallback to text for unknown types
        return "text"

    def map_diesel_type(self, diesel_type: str) -> str:
        """
        Map a Diesel SQL type to SpecQL field type.

        Args:
            diesel_type: Diesel type like 'Integer', 'Nullable<Text>'

        Returns:
            SpecQL field type
        """
        # Handle Nullable<T>
        if diesel_type.startswith("Nullable<") and diesel_type.endswith(">"):
            inner_type = diesel_type[9:-1]  # Remove 'Nullable<>' wrapper
            return self.map_diesel_type(inner_type)

        # Direct Diesel type mapping
        mapped = self.diesel_type_mapping.get(diesel_type)
        return mapped if mapped else "text"


class RustReverseEngineeringService:
    """Main service for Rust reverse engineering."""

    def __init__(self):
        self.parser = RustParser()
        self.mapper = RustToSpecQLMapper()

    def reverse_engineer_file(
        self, file_path: Path, include_diesel_tables: bool = True
    ) -> List[Entity]:
        """
        Reverse engineer a Rust file to SpecQL entities.

        Args:
            file_path: Path to the Rust file
            include_diesel_tables: Whether to include Diesel table! macros (default: True)

        Returns:
            List of SpecQL entities
        """
        # Now returns tuple
        structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers = (
            self.parser.parse_file(file_path)
        )
        entities = []

        # Process structs (existing behavior)
        for struct in structs:
            entity = self.mapper.map_struct_to_entity(struct)
            entities.append(entity)

        # Process Diesel tables (NEW)
        if include_diesel_tables:
            for table in diesel_tables:
                entity = self.mapper.map_diesel_table_to_entity(table)
                entities.append(entity)

        return entities

    def reverse_engineer_directory(
        self, directory_path: Path, include_diesel_tables: bool = True
    ) -> List[Entity]:
        """
        Reverse engineer all Rust files in a directory.

        Args:
            directory_path: Path to the directory containing Rust files
            include_diesel_tables: Whether to include Diesel table! macros (default: True)

        Returns:
            List of SpecQL entities
        """
        entities = []

        for rust_file in directory_path.rglob("*.rs"):
            try:
                file_entities = self.reverse_engineer_file(
                    rust_file, include_diesel_tables=include_diesel_tables
                )
                entities.extend(file_entities)
            except Exception as e:
                logger.warning(f"Failed to parse {rust_file}: {e}")
                continue

        return entities
