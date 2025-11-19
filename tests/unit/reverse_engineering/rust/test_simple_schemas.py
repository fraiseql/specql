"""
Tests for simple Rust schema reverse engineering

These tests ensure basic functionality continues to work
while we enhance complex case handling.
"""

from src.reverse_engineering.rust_parser import RustParser


class TestSimpleRustSchemas:
    """Test simple Rust schema parsing (should maintain 96%+ confidence)"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = RustParser()

    def test_basic_diesel_schema(self):
        """Test basic Diesel schema parsing"""
        code = """
        table! {
            contacts (id) {
                id -> Int4,
                email -> Varchar,
                company_id -> Nullable<Int4>,
                status -> Varchar,
            }
        }
        """

        diesel_table = self.parser.parse_diesel_schema(code)

        assert diesel_table.table_name == "contacts"
        assert diesel_table.primary_key == "id"
        assert len(diesel_table.columns) == 4

        # Check email field
        email_col = next(c for c in diesel_table.columns if c["name"] == "email")
        assert email_col["type"] == "text"
        assert email_col["required"]

        # Check nullable company_id
        company_col = next(c for c in diesel_table.columns if c["name"] == "company_id")
        assert not company_col["required"]

    def test_simple_struct_parsing(self):
        """Test simple Rust struct parsing"""
        code = """
        #[derive(Queryable, Insertable)]
        #[table_name = "contacts"]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub company_id: Option<i32>,
        }
        """

        entity = self.parser.parse_rust_struct(code)

        assert entity["entity"] == "Contact"
        assert len(entity["fields"]) == 3

        # Check company_id is detected as ref
        company_field = next(f for f in entity["fields"] if f["name"] == "company_id")
        assert "ref(Company)" in company_field["type"]
        assert not company_field["required"]
