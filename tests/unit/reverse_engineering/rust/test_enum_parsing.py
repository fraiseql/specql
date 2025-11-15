"""
Tests for enum parsing in Rust files.
"""

from src.reverse_engineering.rust_parser import (
    RustParser,
)


class TestEnumParsing:
    """Test parsing of Rust enums."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()

    def test_simple_unit_enum(self):
        """Test parsing a simple enum with unit variants."""
        rust_code = """
enum Status {
    Active,
    Inactive,
    Pending,
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 1
        assert len(structs) == 0
        enum = enums[0]
        assert enum.name == "Status"
        assert len(enum.variants) == 3

        variant_names = [v.name for v in enum.variants]
        assert "Active" in variant_names
        assert "Inactive" in variant_names
        assert "Pending" in variant_names

        # All should be unit variants (no fields)
        for variant in enum.variants:
            assert variant.fields is None or len(variant.fields) == 0
            assert variant.discriminant is None

    def test_enum_with_discriminants(self):
        """Test parsing enum with explicit discriminants."""
        rust_code = """
enum Color {
    Red = 1,
    Green = 2,
    Blue = 3,
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 1
        enum = enums[0]
        assert enum.name == "Color"
        assert len(enum.variants) == 3

        # Check discriminants
        discriminants = {v.name: v.discriminant for v in enum.variants}
        assert discriminants["Red"] == "1"
        assert discriminants["Green"] == "2"
        assert discriminants["Blue"] == "3"

    def test_enum_with_tuple_variants(self):
        """Test parsing enum with tuple variants."""
        rust_code = """
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 1
        enum = enums[0]
        assert enum.name == "Message"
        assert len(enum.variants) == 4

        variants_by_name = {v.name: v for v in enum.variants}

        # Quit - unit variant
        assert variants_by_name["Quit"].fields is None

        # Write(String) - tuple variant
        write_variant = variants_by_name["Write"]
        assert len(write_variant.fields) == 1
        assert write_variant.fields[0].name == "field_0"
        assert write_variant.fields[0].field_type == "String"

        # ChangeColor(i32, i32, i32) - tuple variant
        color_variant = variants_by_name["ChangeColor"]
        assert len(color_variant.fields) == 3
        for i in range(3):
            assert color_variant.fields[i].name == f"field_{i}"
            assert color_variant.fields[i].field_type == "i32"

        # Move { x: i32, y: i32 } - struct variant
        move_variant = variants_by_name["Move"]
        assert len(move_variant.fields) == 2
        field_names = [f.name for f in move_variant.fields]
        assert "x" in field_names
        assert "y" in field_names

    def test_enum_with_attributes(self):
        """Test parsing enum with attributes."""
        rust_code = """
#[derive(Debug, Clone)]
enum Status {
    Active,
    Inactive,
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 1
        enum = enums[0]
        assert enum.name == "Status"
        assert len(enum.attributes) > 0
        # Check that derive attributes are captured
        attr_str = " ".join(enum.attributes)
        assert "derive" in attr_str

    def test_multiple_enums(self):
        """Test parsing multiple enums in one file."""
        rust_code = """
enum Status {
    Active,
    Inactive,
}

enum Color {
    Red = 1,
    Blue = 2,
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 2
        enum_names = [e.name for e in enums]
        assert "Status" in enum_names
        assert "Color" in enum_names

    def test_no_enums(self):
        """Test files without enums."""
        rust_code = """
pub struct User {
    pub id: i32,
    pub name: String,
}

impl User {
    pub fn new(id: i32, name: String) -> Self {
        Self { id, name }
    }
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(enums) == 0
        assert len(structs) == 1
        assert len(impl_blocks) == 1
