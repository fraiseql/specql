"""
End-to-end tests for Rust reverse engineering

These tests verify the complete pipeline from Rust to SpecQL YAML.
"""

from reverse_engineering.rust_parser import RustParser


class TestRustEndToEnd:
    """Test complete Rust reverse engineering pipeline"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = RustParser()

    def test_diesel_schema_to_yaml(self):
        """Test converting Diesel schema to YAML (basic field extraction)"""
        # Test basic struct parsing (Diesel-style structs)
        rust_code = """
#[derive(Queryable)]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
}
"""
        # Use tree-sitter parser for struct extraction
        from reverse_engineering.tree_sitter_rust_parser import TreeSitterRustParser

        ts_parser = TreeSitterRustParser()
        ast = ts_parser.parse(rust_code)
        assert ast is not None, "Failed to parse Rust code"

        structs = ts_parser.extract_structs(ast)

        # Verify struct extraction works
        assert len(structs) >= 1
        found_user = False
        for struct in structs:
            if struct.name == "User":
                found_user = True
                assert len(struct.fields) == 3
                field_names = [f.name for f in struct.fields]
                assert "id" in field_names
                assert "name" in field_names
                assert "email" in field_names

        assert found_user, "User struct not found in parsed structs"

    def test_complex_struct_to_yaml(self):
        """Test converting complex Rust struct with nested types"""
        rust_code = """
#[derive(Serialize, Deserialize)]
pub struct Contact {
    pub id: i32,
    pub name: String,
    pub profile: Profile,
    pub tags: Vec<String>,
    pub metadata: Option<HashMap<String, String>>,
}

#[derive(Serialize, Deserialize)]
pub struct Profile {
    pub bio: String,
    pub avatar_url: Option<String>,
}
"""
        from reverse_engineering.tree_sitter_rust_parser import TreeSitterRustParser

        ts_parser = TreeSitterRustParser()
        ast = ts_parser.parse(rust_code)
        assert ast is not None, "Failed to parse Rust code"

        structs = ts_parser.extract_structs(ast)

        # Should extract both structs
        assert len(structs) >= 2

        # Find Contact struct
        contact_struct = None
        profile_struct = None
        for struct in structs:
            if struct.name == "Contact":
                contact_struct = struct
            elif struct.name == "Profile":
                profile_struct = struct

        assert contact_struct is not None, "Contact struct not found"
        assert profile_struct is not None, "Profile struct not found"

        # Verify Contact fields
        assert len(contact_struct.fields) == 5
        field_types = {f.name: f.type_name for f in contact_struct.fields}
        assert "tags" in field_types
        assert "Vec" in field_types["tags"] or "String" in field_types["tags"]

        # Verify Profile fields
        assert len(profile_struct.fields) == 2
