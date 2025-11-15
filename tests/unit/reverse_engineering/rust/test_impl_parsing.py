"""
Tests for impl block parsing functionality.
"""

from src.reverse_engineering.rust_parser import (
    RustParser,
)


class TestImplBlockParsing:
    """Test parsing of Rust impl blocks."""

    def test_simple_impl_block(self):
        """Test parsing a simple impl block with one method."""
        rust_code = """
pub struct User {
    pub id: i32,
    pub name: String,
}

impl User {
    pub fn new(id: i32, name: String) -> Self {
        User { id, name }
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        impl_block = impl_blocks[0]
        assert impl_block.type_name == "User"
        assert impl_block.trait_impl is None
        assert len(impl_block.methods) == 1

        method = impl_block.methods[0]
        assert method.name == "new"
        assert method.visibility == "pub"
        assert method.return_type == "Self"
        assert not method.is_async
        assert len(method.parameters) == 2

        # Check parameters
        assert method.parameters[0]["name"] == "id"
        assert method.parameters[0]["param_type"] == "i32"
        assert method.parameters[1]["name"] == "name"
        assert method.parameters[1]["param_type"] == "String"

    def test_multiple_methods_in_impl(self):
        """Test parsing impl block with multiple methods."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn new(id: i32) -> Self {
        User { id }
    }

    pub fn get_id(&self) -> i32 {
        self.id
    }

    pub fn set_id(&mut self, id: i32) {
        self.id = id;
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        impl_block = impl_blocks[0]
        assert len(impl_block.methods) == 3

        # Check method names
        method_names = [m.name for m in impl_block.methods]
        assert "new" in method_names
        assert "get_id" in method_names
        assert "set_id" in method_names

    def test_async_method(self):
        """Test parsing async methods."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub async fn save(&self) -> Result<(), String> {
        Ok(())
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        method = impl_blocks[0].methods[0]
        assert method.name == "save"
        assert method.is_async  is True
        assert method.return_type == "Result<(), String>"

    def test_self_parameters(self):
        """Test parsing different self parameter types."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn by_ref(&self) -> i32 {
        self.id
    }

    pub fn by_mut_ref(&mut self, new_id: i32) {
        self.id = new_id;
    }

    pub fn by_value(self) -> i32 {
        self.id
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        methods = impl_blocks[0].methods
        assert len(methods) == 3

        # Find methods by name
        by_ref = next(m for m in methods if m.name == "by_ref")
        by_mut_ref = next(m for m in methods if m.name == "by_mut_ref")
        by_value = next(m for m in methods if m.name == "by_value")

        # Check self parameters
        assert len(by_ref.parameters) == 1
        assert by_ref.parameters[0]["name"] == "self"
        assert by_ref.parameters[0]["param_type"] == "&self"
        assert by_ref.parameters[0]["is_ref"]  is True
        assert not by_ref.parameters[0]["is_mut"]

        assert len(by_mut_ref.parameters) == 2  # self + new_id
        assert by_mut_ref.parameters[0]["name"] == "self"
        assert by_mut_ref.parameters[0]["param_type"] == "&mut self"

        assert len(by_value.parameters) == 1
        assert by_value.parameters[0]["name"] == "self"
        assert by_value.parameters[0]["param_type"] == "self"

    def test_visibility_levels(self):
        """Test parsing different visibility levels."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn public_method(&self) {}

    fn private_method(&self) {}

    pub(crate) fn crate_visible(&self) {}
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        methods = impl_blocks[0].methods
        assert len(methods) == 3

        # Check visibilities
        visibilities = {m.name: m.visibility for m in methods}
        assert visibilities["public_method"] == "pub"
        assert visibilities["private_method"] == "private"
        assert visibilities["crate_visible"] == "pub(crate)"

    def test_trait_impl(self):
        """Test parsing trait implementations."""
        rust_code = """
pub struct User {
    pub name: String,
}

impl Display for User {
    fn fmt(&self, f: &mut Formatter) -> Result<(), Error> {
        write!(f, "User: {}", self.name)
    }
}

impl Debug for User {
    fn fmt(&self, f: &mut Formatter) -> Result<(), Error> {
        write!(f, "User {{ name: {} }}", self.name)
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 2

        # Find trait impls
        display_impl = next(ib for ib in impl_blocks if ib.trait_impl == "Display")
        debug_impl = next(ib for ib in impl_blocks if ib.trait_impl == "Debug")

        assert display_impl.type_name == "User"
        assert debug_impl.type_name == "User"

        assert len(display_impl.methods) == 1
        assert display_impl.methods[0].name == "fmt"

        assert len(debug_impl.methods) == 1
        assert debug_impl.methods[0].name == "fmt"

    def test_generic_parameters(self):
        """Test parsing methods with generic parameters."""
        rust_code = """
pub struct Container<T> {
    value: T,
}

impl<T> Container<T> {
    pub fn new(value: T) -> Self {
        Container { value }
    }

    pub fn get(&self) -> &T {
        &self.value
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        impl_block = impl_blocks[0]
        assert impl_block.type_name == "Container"
        assert len(impl_block.methods) == 2

    def test_complex_return_types(self):
        """Test parsing complex return types."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn find_all() -> Vec<User> {
        vec![]
    }

    pub fn find_by_id(id: i32) -> Option<User> {
        None
    }

    pub fn create(&self) -> Result<User, String> {
        Ok(User { id: self.id })
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        methods = impl_blocks[0].methods
        assert len(methods) == 3

        # Check return types
        return_types = {m.name: m.return_type for m in methods}
        assert return_types["find_all"] == "Vec<User>"
        assert return_types["find_by_id"] == "Option<User>"
        assert return_types["create"] == "Result<User, String>"

    def test_reference_parameters(self):
        """Test parsing reference parameters."""
        rust_code = """
pub struct User {
    pub name: String,
}

impl User {
    pub fn set_name(&mut self, name: &str) {
        self.name = name.to_string();
    }

    pub fn with_name(name: &String) -> Self {
        User { name: name.clone() }
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        methods = impl_blocks[0].methods
        assert len(methods) == 2

        set_name = next(m for m in methods if m.name == "set_name")
        assert len(set_name.parameters) == 2  # self + name
        assert set_name.parameters[1]["name"] == "name"
        assert set_name.parameters[1]["param_type"] == "&str"
        assert set_name.parameters[1]["is_ref"]  is True

    def test_empty_impl_block(self):
        """Test parsing empty impl block."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    // No methods
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        # Should not include empty impl blocks
        assert len(impl_blocks) == 0

    def test_multiple_impl_blocks_same_type(self):
        """Test multiple impl blocks for the same type."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn method1(&self) {}
}

impl User {
    pub fn method2(&self) {}
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 2
        all_methods = []
        for impl_block in impl_blocks:
            all_methods.extend([m.name for m in impl_block.methods])

        assert "method1" in all_methods
        assert "method2" in all_methods

    def test_impl_with_lifetimes(self):
        """Test parsing impl blocks with lifetime parameters."""
        rust_code = """
pub struct Container<'a> {
    data: &'a str,
}

impl<'a> Container<'a> {
    pub fn new(data: &'a str) -> Self {
        Container { data }
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        assert impl_blocks[0].type_name == "Container"
        assert len(impl_blocks[0].methods) == 1

    def test_unit_return_type(self):
        """Test parsing methods with unit return type."""
        rust_code = """
pub struct User {
    pub id: i32,
}

impl User {
    pub fn do_something(&self) {
        // No return
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        method = impl_blocks[0].methods[0]
        assert method.return_type == "()"

    def test_tuple_parameters(self):
        """Test parsing tuple parameters (edge case)."""
        rust_code = """
pub struct Calculator {}

impl Calculator {
    pub fn add(&self, pair: (i32, i32)) -> i32 {
        pair.0 + pair.1
    }
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, routes = parser.parse_source(
            rust_code
        )

        assert len(impl_blocks) == 1
        method = impl_blocks[0].methods[0]
        assert len(method.parameters) == 2  # self + pair
        assert method.parameters[1]["param_type"] == "Tuple"
