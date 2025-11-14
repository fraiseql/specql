"""
Rust AST Parser for SpecQL

Parses Rust structs and Diesel schema macros using subprocess and syn crate.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

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


class RustParser:
    """Parser for Rust code using subprocess and syn crate."""

    def __init__(self):
        if not RUST_PARSER_BINARY.exists():
            raise FileNotFoundError(
                f"Rust parser binary not found at {RUST_PARSER_BINARY}. "
                "Please build it by running: cd rust && cargo build --release"
            )

    def parse_file(self, file_path: Path) -> List[RustStructInfo]:
        """
        Parse a Rust source file and extract struct definitions.

        Args:
            file_path: Path to the Rust file

        Returns:
            List of parsed struct information
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
            structs_data = json.loads(result.stdout)

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

            return structs

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Rust parser: {e}")
            logger.error(f"stderr: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse Rust file {file_path}: {e}")
            raise

    def parse_source(self, source_code: str) -> List[RustStructInfo]:
        """
        Parse Rust source code and extract struct definitions.

        Args:
            source_code: Rust source code as string

        Returns:
            List of parsed struct information
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
            elif "#[belongs_to(" in attr:
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
        try:
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

    def reverse_engineer_file(self, file_path: Path) -> List[Entity]:
        """
        Reverse engineer a Rust file to SpecQL entities.

        Args:
            file_path: Path to the Rust file

        Returns:
            List of SpecQL entities
        """
        structs = self.parser.parse_file(file_path)
        entities = []

        for struct in structs:
            entity = self.mapper.map_struct_to_entity(struct)
            entities.append(entity)

        return entities

    def reverse_engineer_directory(self, directory_path: Path) -> List[Entity]:
        """
        Reverse engineer all Rust files in a directory.

        Args:
            directory_path: Path to the directory containing Rust files

        Returns:
            List of SpecQL entities
        """
        entities = []

        for rust_file in directory_path.rglob("*.rs"):
            try:
                file_entities = self.reverse_engineer_file(rust_file)
                entities.extend(file_entities)
            except Exception as e:
                logger.warning(f"Failed to parse {rust_file}: {e}")
                continue

        return entities
