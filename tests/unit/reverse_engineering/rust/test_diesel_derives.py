"""
Tests for Diesel derive parsing functionality.
"""

from src.reverse_engineering.rust_parser import RustParser


class TestDieselDeriveDetection:
    """Test detection of Diesel derive macros."""

    def test_queryable_detection(self):
        """Test #[derive(Queryable)] detection."""
        rust_code = """
#[derive(Queryable)]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "User"
        assert "Queryable" in derive.derives
        assert derive.associations == []

    def test_insertable_detection(self):
        """Test #[derive(Insertable)] detection."""
        rust_code = """
#[derive(Insertable)]
pub struct NewUser {
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "NewUser"
        assert "Insertable" in derive.derives

    def test_multiple_derives(self):
        """Test multiple derives: Queryable, Insertable, Debug."""
        rust_code = """
#[derive(Queryable, Insertable, Debug)]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "User"
        assert "Queryable" in derive.derives
        assert "Insertable" in derive.derives
        assert "Debug" not in derive.derives  # Only Diesel derives

    def test_table_name_attribute(self):
        """Test #[table_name = \"users\"] extraction."""
        rust_code = """
#[derive(Queryable)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "User"
        assert derive.associations == ["users"]

    def test_belongs_to_in_derive(self):
        """Test #[belongs_to(...)] in derives."""
        # Note: belongs_to is typically a separate attribute, not in derive
        # But let's test if our parser handles it
        rust_code = """
#[derive(Queryable)]
#[belongs_to(User)]
pub struct Post {
    pub id: i32,
    pub user_id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        # For now, our parser only extracts derive macros and table_name
        # belongs_to would need separate parsing
        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "Post"
        assert "Queryable" in derive.derives

    def test_no_derives(self):
        """Test struct without Diesel derives."""
        rust_code = """
#[derive(Debug, Clone)]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        # Should not extract non-Diesel derives
        assert len(derives) == 0

    def test_as_changeset_derive(self):
        """Test #[derive(AsChangeset)] detection."""
        rust_code = """
#[derive(AsChangeset)]
pub struct UserUpdate {
    pub name: Option<String>,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "UserUpdate"
        assert "AsChangeset" in derive.derives

    def test_associations_derive(self):
        """Test #[derive(Associations)] detection."""
        rust_code = """
#[derive(Associations)]
pub struct Post {
    pub id: i32,
    pub user_id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "Post"
        assert "Associations" in derive.derives

    def test_multiple_table_associations(self):
        """Test multiple table associations (shouldn't happen but test robustness)."""
        rust_code = """
#[derive(Queryable)]
#[table_name = "users"]
#[table_name = "people"]  // This shouldn't happen in real code
pub struct User {
    pub id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        # Our simple parser takes the last one or first one
        assert len(derive.associations) >= 1

    def test_derive_with_table_name(self):
        """Test complete example with derive and table_name."""
        rust_code = """
#[derive(Queryable, Insertable, AsChangeset)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "User"
        assert "Queryable" in derive.derives
        assert "Insertable" in derive.derives
        assert "AsChangeset" in derive.derives
        assert derive.associations == ["users"]

    def test_empty_derives(self):
        """Test #[derive()] with no derives."""
        rust_code = """
#[derive()]
pub struct User {
    pub id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        # Should not extract empty derives
        assert len(derives) == 0

    def test_non_diesel_derives_only(self):
        """Test only non-Diesel derives are ignored."""
        rust_code = """
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 0

    def test_case_insensitive_derives(self):
        """Test that derive names are case-sensitive (they should be)."""
        rust_code = """
#[derive(queryable)]  // lowercase
pub struct User {
    pub id: i32,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        # Should not match lowercase
        assert len(derives) == 0

    def test_mixed_derives(self):
        """Test mix of Diesel and non-Diesel derives."""
        rust_code = """
#[derive(Debug, Queryable, Clone, Insertable, Serialize)]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert "Queryable" in derive.derives
        assert "Insertable" in derive.derives
        assert len(derive.derives) == 2  # Only Diesel ones

    def test_complex_derive_ordering(self):
        """Test that derive order doesn't matter."""
        rust_code = """
#[derive(Insertable, Queryable, AsChangeset, Associations)]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(derives) == 1
        derive = derives[0]
        assert derive.struct_name == "User"
        assert set(derive.derives) == {
            "Queryable",
            "Insertable",
            "AsChangeset",
            "Associations",
        }
