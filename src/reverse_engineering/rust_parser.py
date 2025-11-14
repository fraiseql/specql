"""
Rust AST Parser for SpecQL

Parses Rust structs and Diesel schema macros using subprocess and syn crate.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from src.core.ast_models import Entity, FieldDefinition, FieldTier

logger = logging.getLogger(__name__)

# Path to the Rust parser binary
RUST_PARSER_BINARY = (
    Path(__file__).parent.parent.parent
    / "rust"
    / "target"
    / "release"
    / "specql_rust_parser"
)


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


class RustParser:
    """Parser for Rust code using subprocess and syn crate."""

    def __init__(self):
        if not RUST_PARSER_BINARY.exists():
            raise FileNotFoundError(
                f"Rust parser binary not found at {RUST_PARSER_BINARY}. "
                "Please build it by running: cd rust && cargo build --release"
            )

    def parse_file(
        self, file_path: Path
    ) -> Tuple[
        List[RustStructInfo],
        List[RustEnumInfo],
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
        try:
            # Call the Rust parser binary
            result = subprocess.run(
                [str(RUST_PARSER_BINARY), str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the JSON result
            # Expect JSON with two keys: "structs" and "diesel_tables"
            data = json.loads(result.stdout)

            # Handle old format (just array of structs) for backward compatibility
            if isinstance(data, list):
                structs_data = data
                enums_data = []
                diesel_tables_data = []
                diesel_derives_data = []
                impl_blocks_data = []
                route_handlers_data = []
            else:
                structs_data = data.get("structs", [])
                enums_data = data.get("enums", [])
                diesel_tables_data = data.get("diesel_tables", [])
                diesel_derives_data = data.get("diesel_derives", [])
                impl_blocks_data = data.get("impl_blocks", [])
                route_handlers_data = data.get("route_handlers", [])

            # Parse structs (existing code)
            structs = []
            for struct_data in structs_data:
                fields = []
                for field_data in struct_data["fields"]:
                    field = RustFieldInfo(
                        name=field_data["name"],
                        field_type=field_data["field_type"],
                        is_optional=field_data["is_optional"],
                        attributes=field_data["attributes"],
                    )
                    fields.append(field)

                struct = RustStructInfo(
                    name=struct_data["name"],
                    fields=fields,
                    attributes=struct_data["attributes"],
                )
                structs.append(struct)

            # Parse Diesel tables (NEW CODE)
            diesel_tables = []
            for table_data in diesel_tables_data:
                columns = []
                for col_data in table_data["columns"]:
                    column = DieselColumnInfo(
                        name=col_data["name"],
                        sql_type=col_data["sql_type"],
                        is_nullable=col_data["is_nullable"],
                    )
                    columns.append(column)

                table = DieselTableInfo(
                    name=table_data["name"],
                    primary_key=table_data["primary_key"],
                    columns=columns,
                )
                diesel_tables.append(table)

            # Parse Diesel derives (NEW)
            diesel_derives = []
            for derive_data in diesel_derives_data:
                derive = DieselDeriveInfo(
                    struct_name=derive_data["struct_name"],
                    derives=derive_data["derives"],
                    associations=derive_data["associations"],
                )
                diesel_derives.append(derive)

            # Parse impl blocks (NEW)
            impl_blocks = []
            for impl_data in impl_blocks_data:
                methods = []
                for method_data in impl_data["methods"]:
                    method = ImplMethodInfo(
                        name=method_data["name"],
                        visibility=method_data["visibility"],
                        parameters=method_data["parameters"],
                        return_type=method_data["return_type"],
                        is_async=method_data["is_async"],
                    )
                    methods.append(method)

                impl_block = ImplBlockInfo(
                    type_name=impl_data["type_name"],
                    methods=methods,
                    trait_impl=impl_data.get("trait_impl"),
                )
                impl_blocks.append(impl_block)

            # Parse enums (NEW)
            enums = []
            for enum_data in enums_data:
                variants = []
                for variant_data in enum_data["variants"]:
                    fields = None
                    if variant_data.get("fields") is not None:
                        fields = []
                        for field_data in variant_data["fields"]:
                            field = RustFieldInfo(
                                name=field_data["name"],
                                field_type=field_data["field_type"],
                                is_optional=field_data["is_optional"],
                                attributes=field_data["attributes"],
                            )
                            fields.append(field)

                    variant = RustEnumVariantInfo(
                        name=variant_data["name"],
                        fields=fields,
                        discriminant=variant_data.get("discriminant"),
                    )
                    variants.append(variant)

                rust_enum = RustEnumInfo(
                    name=enum_data["name"],
                    variants=variants,
                    attributes=enum_data["attributes"],
                )
                enums.append(rust_enum)

            # Parse route handlers (NEW)
            route_handlers = []
            for route_data in route_handlers_data:
                route_handler = RouteHandlerInfo(
                    method=route_data["method"],
                    path=route_data["path"],
                    function_name=route_data["function_name"],
                    is_async=route_data["is_async"],
                    return_type=route_data["return_type"],
                    parameters=route_data["parameters"],
                )
                route_handlers.append(route_handler)

            return (
                structs,
                enums,
                diesel_tables,
                diesel_derives,
                impl_blocks,
                route_handlers,
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Rust parser: {e}")
            logger.error(f"stderr: {e.stderr}")
            # Return empty results instead of crashing
            return ([], [], [], [], [], [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Rust parser for {file_path}: {e}")
            # Return empty results for malformed JSON
            return ([], [], [], [], [], [])
        except Exception as e:
            logger.error(f"Failed to parse Rust file {file_path}: {e}")
            # Return empty results for any other errors
            return ([], [], [], [], [], [])

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


class RustToSpecQLMapper:
    """Maps parsed Rust structs to SpecQL entities."""

    def __init__(self):
        self.type_mapper = RustTypeMapper()

    def is_diesel_struct(self, struct: RustStructInfo) -> bool:
        """
        Check if a struct is Diesel-related.

        A struct is considered Diesel-related if it has:
        - Queryable derive
        - Insertable derive
        - table_name attribute
        - diesel(...) attributes
        - Fields with belongs_to or other Diesel attributes

        Args:
            struct: Parsed Rust struct information

        Returns:
            True if the struct is Diesel-related, False otherwise
        """
        # Check struct-level attributes
        if struct.attributes:
            attributes_str = " ".join(struct.attributes).lower()

            # Check for Diesel-related derives
            diesel_derives = ["queryable", "insertable", "aschangeset", "associations"]
            for derive in diesel_derives:
                if derive in attributes_str:
                    return True

            # Check for Diesel-related attributes
            diesel_attributes = ["table_name", "diesel(", "belongs_to"]
            for attr in diesel_attributes:
                if attr in attributes_str:
                    return True

        # Check field-level attributes for Diesel markers
        for field in struct.fields:
            if field.attributes:
                field_attrs_str = " ".join(field.attributes).lower()
                diesel_field_attributes = ["belongs_to", "diesel(", "column_name"]
                for attr in diesel_field_attributes:
                    if attr in field_attrs_str:
                        return True

        return False

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

    def _parse_field_attributes(
        self, field_def: FieldDefinition, attributes: List[str]
    ):
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
                attr.replace("# [", "#[")
                .replace("] ", "]")
                .replace(" (", "(")
                .replace(") ", ")")
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
            "Varchar": "varchar",
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
            inner_content = rust_type[
                rust_type.find("<") + 1 : rust_type.rfind(">")
            ].strip()

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

        # Process structs - only include Diesel-related structs
        for struct in structs:
            # Filter to only Diesel-related structs
            if self.mapper.is_diesel_struct(struct):
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
