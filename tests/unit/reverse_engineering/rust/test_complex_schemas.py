"""
Tests for complex Rust schema reverse engineering

These tests target capabilities that currently have unknown confidence
and need enhancement.
"""

from reverse_engineering.rust_parser import RustParser


class TestComplexRustSchemas:
    """Test complex Rust schema parsing capabilities"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = RustParser()

    def test_custom_derive_macros(self):
        """Test parsing custom derive macros"""
        code = """
        #[derive(Debug, Clone, Queryable, Insertable, AsChangeset)]
        #[table_name = "contacts"]
        pub struct Contact {
            pub id: i32,
            pub email: String,
        }
        """

        entity = self.parser.parse_rust_struct(code)

        assert entity["entity"] == "Contact"
        assert "Queryable" in entity["_metadata"]["derives"]
        assert "Insertable" in entity["_metadata"]["derives"]
        assert "AsChangeset" in entity["_metadata"]["derives"]

    def test_complex_generics(self):
        """Test parsing complex generic types"""
        code = """
        #[derive(Queryable, Insertable)]
        #[table_name = "contacts"]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub tags: Vec<String>,
            pub metadata: Option<HashMap<String, String>>,
        }
        """

        entity = self.parser.parse_rust_struct(code)

        assert entity["entity"] == "Contact"

        # Check Vec<String> -> list
        tags_field = next(f for f in entity["fields"] if f["name"] == "tags")
        assert tags_field["type"] == "list"

        # Check Option<HashMap<String, String>> -> json (not required)
        metadata_field = next(f for f in entity["fields"] if f["name"] == "metadata")
        assert metadata_field["type"] == "json"
        assert not metadata_field["required"]

    def test_embedded_structs(self):
        """Test parsing embedded structs"""
        code = """
        pub struct Address {
            pub street: String,
            pub city: String,
        }

        #[derive(Queryable, Insertable)]
        #[table_name = "contacts"]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub address: Address,
        }
        """

        entity = self.parser.parse_rust_struct(code)

        assert entity["entity"] == "Contact"

        # Check embedded struct -> composite
        address_field = next(f for f in entity["fields"] if f["name"] == "address")
        assert address_field["type"] == "composite"

    def test_association_macros(self):
        """Test parsing Diesel association macros"""
        code = """
        #[derive(Associations)]
        #[belongs_to(Company, foreign_key = "company_id")]
        #[derive(Queryable, Insertable)]
        #[table_name = "contacts"]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub company_id: i32,
        }
        """

        entity = self.parser.parse_rust_struct(code)

        assert entity["entity"] == "Contact"

        # Check association metadata
        associations = entity["_metadata"]["associations"]
        assert len(associations) == 1
        assert associations[0]["type"] == "belongs_to"
        assert associations[0]["entity"] == "Company"
        assert associations[0]["foreign_key"] == "company_id"

        # Check that company_id field is marked as ref(Company)
        company_field = next(f for f in entity["fields"] if f["name"] == "company_id")
        assert company_field["type"] == "ref(Company)"
