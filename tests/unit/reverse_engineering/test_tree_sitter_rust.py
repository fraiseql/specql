"""
Tree-sitter Rust AST Parser Tests

Test tree-sitter based Rust parsing for complex macros and structures.
"""

import pytest
from src.reverse_engineering.tree_sitter_rust_parser import TreeSitterRustParser


class TestTreeSitterRustParser:
    """Test tree-sitter Rust AST parsing"""

    def test_parse_diesel_table_macro(self):
        """Test parsing Diesel table! macro"""
        code = """
        diesel::table! {
            contacts (id) {
                id -> Integer,
                email -> Varchar,
                status -> Varchar,
                created_at -> Timestamp,
            }
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        assert ast is not None
        assert parser.extract_table_name(ast) == "contacts"
        assert len(parser.extract_columns(ast)) == 4
        assert "email" in [col.name for col in parser.extract_columns(ast)]

    def test_extract_function_signatures(self):
        """Test extracting function signatures from AST"""
        code = """
        pub async fn create_contact(
            db: web::Data<Database>,
            contact: web::Json<ContactDTO>
        ) -> Result<HttpResponse, Error> {
            // Implementation
            Ok(HttpResponse::Created().json(contact))
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        functions = parser.extract_functions(ast)

        assert len(functions) == 1
        assert functions[0].name == "create_contact"
        assert functions[0].is_public == True
        assert functions[0].is_async == True
        assert len(functions[0].parameters) == 2

    def test_extract_derive_macros(self):
        """Test extracting derive macros from structs"""
        code = """
        #[derive(Debug, Clone, Serialize, Deserialize)]
        #[diesel(table_name = contacts)]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub status: String,
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        structs = parser.extract_structs(ast)

        assert len(structs) == 1
        assert "Serialize" in structs[0].derives
        assert "Deserialize" in structs[0].derives
        assert structs[0].attributes.get("table_name") == "contacts"

    def test_rust_action_parser_integration(self):
        """Test RustActionParser integration with tree-sitter"""
        from src.reverse_engineering.rust_action_parser import RustActionParser

        code = """
        pub async fn create_contact() -> Result<(), Error> {
            Ok(())
        }

        #[derive(Serialize)]
        pub struct Contact {
            pub id: i32,
        }
        """

        # Test with tree-sitter enabled
        parser = RustActionParser(use_tree_sitter=True)

        # Create a temporary file for testing
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = parser.parse_file(temp_file)
            assert result.parser_used == "tree-sitter"
            assert len(result.functions) == 1
            assert len(result.structs) == 1
        finally:
            import os

            os.unlink(temp_file)
