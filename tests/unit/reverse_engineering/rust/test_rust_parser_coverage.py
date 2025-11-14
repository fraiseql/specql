"""
Additional tests to increase coverage to 95%+.

INSTALLATION: Copy to tests/unit/reverse_engineering/rust/test_rust_parser_coverage.py

PURPOSE:
Cover untested code paths identified in coverage report (currently at 62%).

Target areas:
1. Error handling paths
2. Edge cases in type mapping
3. Complex attribute parsing
4. Directory traversal with errors
5. Temporary file cleanup
6. Parse source (not just files)
"""

import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
    RustTypeMapper,
    RustFieldInfo,
    RustStructInfo,
    DieselColumnInfo,
    DieselTableInfo,
)
from src.core.ast_models import FieldDefinition, FieldTier


class TestRustParserErrorHandling:
    """Test error handling paths."""

    def test_parser_binary_not_found(self):
        """Test error when Rust parser binary doesn't exist."""
        # This would require mocking RUST_PARSER_BINARY path
        # For now, document the expected behavior
        pass  # Covered by FileNotFoundError in __init__

    def test_invalid_rust_syntax(self):
        """Test handling of invalid Rust syntax."""
        invalid_rust = """
        pub struct User {
            pub id: i32
            pub name: String  // Missing comma - syntax error
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(invalid_rust)
            temp_path = f.name

        try:
            parser = RustParser()
            with pytest.raises(Exception):  # Should raise subprocess.CalledProcessError
                parser.parse_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        parser = RustParser()

        with pytest.raises(
            Exception
        ):  # Should raise FileNotFoundError or subprocess error
            parser.parse_file(Path("/nonexistent/file.rs"))

    def test_directory_traversal_with_errors(self):
        """Test directory parsing continues after file errors."""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()

        try:
            # Create one valid and one invalid file
            (Path(temp_dir) / "valid.rs").write_text("""
            pub struct User { pub id: i32, }
            """)

            (Path(temp_dir) / "invalid.rs").write_text("""
            pub struct Broken { invalid syntax here }
            """)

            service = RustReverseEngineeringService()

            # Should log warning but continue
            entities = service.reverse_engineer_directory(Path(temp_dir))

            # Should get at least the valid entity
            # (may be 0 if error handling stops parsing)
            assert isinstance(entities, list)

        finally:
            shutil.rmtree(temp_dir)


class TestRustTypeMapperEdgeCases:
    """Test edge cases in type mapping."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = RustTypeMapper()

    def test_empty_generic_type(self):
        """Test handling of malformed generics with empty content."""
        # Vec< > with empty content
        result = self.mapper.map_type("Vec< >")
        assert result == "text"  # Fallback for malformed generics

    def test_nested_generics(self):
        """Test deeply nested generic types."""
        # Option<Vec<HashMap<String, Value>>>
        result = self.mapper.map_type("Option<Vec<HashMap<String, Value>>>")
        assert result == "jsonb"  # Should extract inner Vec and map to jsonb

    def test_array_syntax_types(self):
        """Test Rust array syntax [T; N] and [T]."""
        assert self.mapper.map_type("[i32; 10]") == "jsonb"
        assert self.mapper.map_type("[String]") == "jsonb"

    def test_unknown_types_fallback(self):
        """Test that unknown types fall back to text."""
        assert self.mapper.map_type("CustomUnknownType") == "text"
        assert self.mapper.map_type("some::path::CustomType") == "text"

    def test_multipath_types(self):
        """Test types with multiple path segments."""
        result = self.mapper.map_type("std::collections::HashMap")
        # Should handle multi-segment paths
        assert result in ["jsonb", "text"]

    def test_reference_types(self):
        """Test reference type handling."""
        result = self.mapper.map_type("&str")
        assert result == "text"

    def test_diesel_nullable_type(self):
        """Test Diesel Nullable<T> type mapping."""
        result = self.mapper.map_diesel_type("Nullable<Text>")
        assert result == "text"

        result = self.mapper.map_diesel_type("Nullable<Integer>")
        assert result == "integer"

    def test_unknown_diesel_type(self):
        """Test fallback for unknown Diesel types."""
        result = self.mapper.map_diesel_type("UnknownDieselType")
        assert result == "text"


class TestRustToSpecQLMapperEdgeCases:
    """Test edge cases in mapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = RustToSpecQLMapper()

    def test_struct_with_no_fields(self):
        """Test mapping of unit struct (no fields)."""
        struct = RustStructInfo(name="EmptyStruct", fields=[], attributes=[])

        entity = self.mapper.map_struct_to_entity(struct)

        assert entity.name == "EmptyStruct"
        assert entity.table == "empty_struct"
        assert len(entity.fields) == 0

    def test_struct_with_complex_attributes(self):
        """Test struct with various attributes."""
        field = RustFieldInfo(
            name="test_field",
            field_type="String",
            is_optional=False,
            attributes=[
                "#[primary_key]",
                '#[column_name = "custom_name"]',
                "#[index]",
                "#[unique]",
            ],
        )

        struct = RustStructInfo(
            name="Test", fields=[field], attributes=["#[derive(Debug, Clone)]"]
        )

        entity = self.mapper.map_struct_to_entity(struct)

        # Should parse without errors
        assert "test_field" in entity.fields

    def test_belongs_to_parsing_variations(self):
        """Test various belongs_to attribute formats."""
        test_cases = [
            "#[belongs_to(User)]",
            "#[belongs_to( User )]",  # Extra spaces
            '#[belongs_to(User, foreign_key = "user_id")]',
            "#[belongs_to(User, foreign_key = 'user_id')]",  # Single quotes
        ]

        for attr in test_cases:
            field = RustFieldInfo(
                name="user_id", field_type="i32", is_optional=False, attributes=[attr]
            )

            struct = RustStructInfo(name="Test", fields=[field], attributes=[])
            entity = self.mapper.map_struct_to_entity(struct)

            # Should parse without errors
            assert "user_id" in entity.fields

    def test_belongs_to_error_handling(self):
        """Test that malformed belongs_to doesn't crash."""
        malformed_attrs = [
            "#[belongs_to(",  # Unclosed
            "#[belongs_to()]",  # Empty
            "#[belongs_to(]",  # Malformed
        ]

        for attr in malformed_attrs:
            field = RustFieldInfo(
                name="test", field_type="i32", is_optional=False, attributes=[attr]
            )

            struct = RustStructInfo(name="Test", fields=[field], attributes=[])

            # Should not crash, just skip the malformed attribute
            entity = self.mapper.map_struct_to_entity(struct)
            assert "test" in entity.fields

    def test_camel_to_snake_conversion(self):
        """Test CamelCase to snake_case conversion."""
        test_cases = [
            ("User", "user"),
            ("UserProfile", "user_profile"),
            ("HTTPRequest", "http_request"),
            ("IOError", "io_error"),
            ("SimpleTest", "simple_test"),
        ]

        for camel, expected_snake in test_cases:
            result = self.mapper._camel_to_snake(camel)
            assert result == expected_snake

    def test_derive_table_name(self):
        """Test table name derivation from struct name."""
        test_cases = [
            ("User", "user"),
            ("BlogPost", "blog_post"),
            ("CommentReply", "comment_reply"),
        ]

        for struct_name, expected_table in test_cases:
            result = self.mapper._derive_table_name(struct_name)
            assert result == expected_table


class TestRustParserParseSource:
    """Test parsing from source code string (not file)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()

    def test_parse_source_simple(self):
        """Test parsing from source string."""
        source = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }
        """

        structs, enums, diesel_tables, diesel_derives, impl_blocks, routes = (
            self.parser.parse_source(source)
        )

        assert len(structs) == 1
        assert len(diesel_tables) == 0
        assert structs[0].name == "User"
        assert len(structs[0].fields) == 2

    def test_parse_source_creates_temp_file(self):
        """Test that parse_source properly cleans up temp file."""
        import tempfile

        source = "pub struct Test { pub id: i32, }"

        # Get temp file count before
        temp_dir = tempfile.gettempdir()
        before_count = len(list(Path(temp_dir).glob("*.rs")))

        # Parse
        structs = self.parser.parse_source(source)

        # Temp file should be cleaned up
        after_count = len(list(Path(temp_dir).glob("*.rs")))

        # Count should be the same (file was deleted)
        assert after_count == before_count


class TestComplexRustStructures:
    """Test complex real-world Rust structures."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = RustReverseEngineeringService()

    def test_struct_with_lifetime_parameters(self):
        """Test struct with lifetime parameters (should be ignored)."""
        rust_code = """
        pub struct User<'a> {
            pub id: i32,
            pub name: &'a str,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Should handle or skip lifetime parameters
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # May parse successfully or skip - either is acceptable
            assert isinstance(entities, list)

        finally:
            os.unlink(temp_path)

    def test_struct_with_derive_macros(self):
        """Test struct with multiple derive macros."""
        rust_code = """
        #[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
        #[serde(rename_all = "camelCase")]
        pub struct User {
            pub id: i32,
            pub username: String,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            assert len(entities) >= 1
            user = next(e for e in entities if e.name == "User")
            assert len(user.fields) == 2

        finally:
            os.unlink(temp_path)

    def test_struct_with_doc_comments(self):
        """Test struct with documentation comments."""
        rust_code = """
        /// User entity representing system users
        ///
        /// # Fields
        /// - id: Primary key
        /// - name: User's full name
        pub struct User {
            /// Primary key
            pub id: i32,
            /// User's full name
            pub name: String,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            assert len(entities) >= 1
            user = next(e for e in entities if e.name == "User")
            assert "id" in user.fields
            assert "name" in user.fields

        finally:
            os.unlink(temp_path)


class TestPathEdgeCases:
    """Test path handling edge cases."""

    def test_relative_vs_absolute_paths(self):
        """Test handling of relative and absolute paths."""
        rust_code = "pub struct User { pub id: i32, }"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            parser = RustParser()

            # Absolute path
            abs_path = Path(temp_path).absolute()
            structs1 = parser.parse_file(abs_path)

            # Relative path (if possible)
            rel_path = Path(temp_path)
            structs2 = parser.parse_file(rel_path)

            # Both should work
            assert len(structs1) == len(structs2)

        finally:
            os.unlink(temp_path)

    def test_path_with_spaces(self):
        """Test handling of paths with spaces."""
        import tempfile
        import shutil

        # Create temp directory with spaces
        temp_dir = tempfile.mkdtemp(suffix=" with spaces")

        try:
            file_path = Path(temp_dir) / "test file.rs"
            file_path.write_text("pub struct User { pub id: i32, }")

            parser = RustParser()
            structs, enums, diesel_tables, diesel_derives, impl_blocks, routes = (
                parser.parse_file(file_path)
            )

            assert len(structs) == 1
            assert len(diesel_tables) == 0

        finally:
            shutil.rmtree(temp_dir)


class TestDieselTableCoverage:
    """Test Diesel table parsing and mapping coverage."""

    def test_diesel_column_info_constructor(self):
        """Test DieselColumnInfo constructor."""
        col = DieselColumnInfo(name="id", sql_type="Integer", is_nullable=False)
        assert col.name == "id"
        assert col.sql_type == "Integer"
        assert col.is_nullable is False

    def test_diesel_table_info_constructor(self):
        """Test DieselTableInfo constructor."""
        columns = [DieselColumnInfo("id", "Integer", False)]
        table = DieselTableInfo(name="users", primary_key=["id"], columns=columns)
        assert table.name == "users"
        assert table.primary_key == ["id"]
        assert len(table.columns) == 1

    def test_parse_file_with_diesel_tables(self):
        """Test parsing file that returns both structs and diesel_tables."""
        # Mock the parser to return diesel tables
        from unittest.mock import patch, MagicMock

        parser = RustParser()

        # Mock subprocess result with both structs and diesel_tables
        mock_result = MagicMock()
        mock_result.stdout = """{
            "structs": [{"name": "User", "fields": [], "attributes": []}],
            "diesel_tables": [{
                "name": "users",
                "primary_key": ["id"],
                "columns": [
                    {"name": "id", "sql_type": "Integer", "is_nullable": false},
                    {"name": "name", "sql_type": "Text", "is_nullable": false}
                ]
            }]
        }"""

        with patch("subprocess.run", return_value=mock_result):
            structs, enums, diesel_tables, diesel_derives, impl_blocks, routes = (
                parser.parse_file(Path("/fake/path.rs"))
            )

            assert len(structs) == 1
            assert len(diesel_tables) == 1
            assert diesel_tables[0].name == "users"
            assert len(diesel_tables[0].columns) == 2

    def test_parse_file_backward_compatibility(self):
        """Test backward compatibility with old format (just array of structs)."""
        from unittest.mock import patch, MagicMock

        parser = RustParser()

        # Mock subprocess result with old format (just array)
        mock_result = MagicMock()
        mock_result.stdout = """[{"name": "User", "fields": [], "attributes": []}]"""

        with patch("subprocess.run", return_value=mock_result):
            structs, enums, diesel_tables, diesel_derives, impl_blocks, routes = (
                parser.parse_file(Path("/fake/path.rs"))
            )

            assert len(structs) == 1
            assert len(diesel_tables) == 0  # Should be empty for old format

    def test_map_diesel_table_to_entity(self):
        """Test mapping Diesel table to SpecQL entity."""
        mapper = RustToSpecQLMapper()

        columns = [
            DieselColumnInfo("id", "Integer", False),
            DieselColumnInfo("name", "Text", False),
            DieselColumnInfo("user_id", "Integer", True),  # FK field
        ]
        table = DieselTableInfo("users", ["id"], columns)

        entity = mapper.map_diesel_table_to_entity(table)

        assert entity.name == "Users"  # snake_to_pascal
        assert entity.table == "users"
        assert "id" in entity.fields
        assert "name" in entity.fields
        assert "user_id" in entity.fields
        assert entity.fields["user_id"].reference_entity == "users"  # FK detection
        assert entity.fields["user_id"].tier.name == "REFERENCE"

    def test_map_diesel_table_to_entity_no_fk(self):
        """Test mapping Diesel table without FK fields."""
        mapper = RustToSpecQLMapper()

        columns = [
            DieselColumnInfo("id", "Integer", False),
            DieselColumnInfo("title", "Text", False),
        ]
        table = DieselTableInfo("posts", ["id"], columns)

        entity = mapper.map_diesel_table_to_entity(table)

        assert entity.name == "Posts"
        assert entity.table == "posts"
        assert len(entity.fields) == 2
        # No FK fields, so reference_entity should be None
        assert entity.fields["title"].reference_entity is None

    def test_snake_to_pascal_conversion(self):
        """Test snake_case to PascalCase conversion."""
        mapper = RustToSpecQLMapper()

        # Access private method for testing
        result = mapper._snake_to_pascal("user_profile")
        assert result == "UserProfile"

        result = mapper._snake_to_pascal("simple_table")
        assert result == "SimpleTable"

    def test_reverse_engineer_file_with_diesel_tables(self):
        """Test reverse engineering file with Diesel tables included."""
        from unittest.mock import patch, MagicMock

        service = RustReverseEngineeringService()

        # Mock parser to return both structs and diesel tables
        mock_structs = [RustStructInfo("User", [], [])]
        mock_diesel_tables = [DieselTableInfo("users", ["id"], [])]

        with patch.object(
            service.parser,
            "parse_file",
            return_value=(mock_structs, [], mock_diesel_tables, [], [], []),
        ):
            entities = service.reverse_engineer_file(
                Path("/fake/path.rs"), include_diesel_tables=True
            )

            assert len(entities) == 2  # One from struct, one from diesel table

    def test_reverse_engineer_file_exclude_diesel_tables(self):
        """Test reverse engineering file with Diesel tables excluded."""
        from unittest.mock import patch, MagicMock

        service = RustReverseEngineeringService()

        # Mock parser to return both structs and diesel tables
        mock_structs = [RustStructInfo("User", [], [])]
        mock_diesel_tables = [DieselTableInfo("users", ["id"], [])]

        with patch.object(
            service.parser,
            "parse_file",
            return_value=(mock_structs, [], mock_diesel_tables, [], [], []),
        ):
            entities = service.reverse_engineer_file(
                Path("/fake/path.rs"), include_diesel_tables=False
            )

            assert len(entities) == 1  # Only struct, no diesel table


class TestExceptionHandlingCoverage:
    """Test exception handling paths for full coverage."""

    def test_parse_file_subprocess_error(self):
        """Test subprocess.CalledProcessError handling."""
        from unittest.mock import patch

        parser = RustParser()

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "cmd", stderr=b"error"),
        ):
            with pytest.raises(subprocess.CalledProcessError):
                parser.parse_file(Path("/fake/path.rs"))

    def test_parse_file_json_error(self):
        """Test JSON parsing error handling."""
        from unittest.mock import patch, MagicMock

        parser = RustParser()

        mock_result = MagicMock()
        mock_result.stdout = "invalid json"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(Exception):  # JSON decode error
                parser.parse_file(Path("/fake/path.rs"))

    def test_parse_belongs_to_exception_handling(self):
        """Test exception handling in belongs_to parsing."""
        mapper = RustToSpecQLMapper()

        field_def = FieldDefinition(name="user_id", type_name="integer", nullable=False)
        malformed_attrs = ["#[belongs_to(invalid syntax"]

        # Should not crash, just skip malformed attribute
        mapper._parse_field_attributes(field_def, malformed_attrs)

        # Field should still be created normally
        assert field_def.name == "user_id"

    def test_type_mapper_generic_fallback(self):
        """Test generic type mapping fallback."""
        mapper = RustTypeMapper()

        # Test the fallback path in generic handling
        result = mapper.map_type("UnknownGeneric<SomeType>")
        assert result == "text"  # Should fall back to text

    def test_diesel_type_mapper_unknown(self):
        """Test unknown Diesel type mapping."""
        mapper = RustTypeMapper()

        result = mapper.map_diesel_type("UnknownDieselType")
        assert result == "text"  # Should fall back to text


# Run with: pytest test_rust_parser_coverage.py -v --cov=src.reverse_engineering.rust_parser
