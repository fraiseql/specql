"""
Integration tests for Diesel derive parsing with real-world scenarios.
"""

import pytest
from pathlib import Path
from src.reverse_engineering.rust_parser import RustParser


class TestDieselDerivesIntegration:
    """Integration tests for diesel derive parsing."""

    def test_complete_user_model(self):
        """Test parsing a complete User model with all Diesel derives."""
        rust_code = """
use diesel::prelude::*;

#[derive(Queryable, Identifiable, Debug, Clone)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
    pub created_at: chrono::NaiveDateTime,
}

#[derive(Insertable)]
#[table_name = "users"]
pub struct NewUser<'a> {
    pub name: &'a str,
    pub email: &'a str,
}

#[derive(AsChangeset)]
#[table_name = "users"]
pub struct UserUpdate {
    pub name: Option<String>,
    pub email: Option<String>,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, route_handlers = parser.parse_source(rust_code)

        # Should parse 3 structs
        assert len(structs) == 3
        assert len(derives) == 3

        # Check User struct
        user_derive = next(d for d in derives if d.struct_name == "User")
        assert "Queryable" in user_derive.derives
        assert "Identifiable" in user_derive.derives
        assert user_derive.associations == ["users"]

        # Check NewUser struct
        new_user_derive = next(d for d in derives if d.struct_name == "NewUser")
        assert "Insertable" in new_user_derive.derives
        assert new_user_derive.associations == ["users"]

        # Check UserUpdate struct
        update_derive = next(d for d in derives if d.struct_name == "UserUpdate")
        assert "AsChangeset" in update_derive.derives
        assert update_derive.associations == ["users"]

    def test_relationship_models(self):
        """Test parsing models with relationships."""
        rust_code = """
use diesel::prelude::*;

#[derive(Queryable, Associations, Identifiable, Debug)]
#[belongs_to(User)]
#[table_name = "posts"]
pub struct Post {
    pub id: i32,
    pub user_id: i32,
    pub title: String,
    pub content: String,
}

#[derive(Insertable, Associations)]
#[belongs_to(User)]
#[table_name = "posts"]
pub struct NewPost {
    pub user_id: i32,
    pub title: String,
    pub content: String,
}

#[derive(Queryable, Identifiable, Debug)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub name: String,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, route_handlers = parser.parse_source(rust_code)

        assert len(structs) == 3
        assert len(derives) == 3

        # Check Post has Associations derive
        post_derive = next(d for d in derives if d.struct_name == "Post")
        assert "Associations" in post_derive.derives
        assert "Queryable" in post_derive.derives

        # Check NewPost has Associations derive
        new_post_derive = next(d for d in derives if d.struct_name == "NewPost")
        assert "Associations" in new_post_derive.derives
        assert "Insertable" in new_post_derive.derives

    def test_enum_with_derives(self):
        """Test that enums without derives don't interfere."""
        rust_code = """
#[derive(Debug, Clone)]
pub enum Status {
    Active,
    Inactive,
}

#[derive(Queryable)]
#[table_name = "users"]
pub struct User {
    pub id: i32,
    pub status: Status,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, route_handlers = parser.parse_source(rust_code)

        # Should only extract derives from structs with Diesel derives
        assert len(derives) == 1
        assert derives[0].struct_name == "User"
        assert "Queryable" in derives[0].derives

    def test_complex_generic_structs(self):
        """Test parsing generic structs with derives."""
        rust_code = """
use diesel::prelude::*;

#[derive(Queryable)]
#[table_name = "audit_logs"]
pub struct AuditLog<T> {
    pub id: i32,
    pub entity_type: String,
    pub entity_id: i32,
    pub changes: T,
}

#[derive(Insertable)]
#[table_name = "audit_logs"]
pub struct NewAuditLog<T> {
    pub entity_type: String,
    pub entity_id: i32,
    pub changes: T,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, route_handlers = parser.parse_source(rust_code)

        assert len(structs) == 2
        assert len(derives) == 2

        # Check generic structs are parsed
        audit_derive = next(d for d in derives if d.struct_name == "AuditLog")
        assert "Queryable" in audit_derive.derives

        new_audit_derive = next(d for d in derives if d.struct_name == "NewAuditLog")
        assert "Insertable" in new_audit_derive.derives

    def test_mixed_diesel_and_non_diesel(self):
        """Test file with both Diesel and non-Diesel code."""
        rust_code = """
use diesel::prelude::*;
use serde::{Deserialize, Serialize};

// Non-Diesel struct
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

// Diesel structs
#[derive(Queryable, Serialize, Deserialize)]
#[table_name = "products"]
pub struct Product {
    pub id: i32,
    pub name: String,
    pub price: f64,
}

#[derive(Insertable)]
#[table_name = "products"]
pub struct NewProduct {
    pub name: String,
    pub price: f64,
}

#[derive(AsChangeset, Serialize, Deserialize)]
#[table_name = "products"]
pub struct ProductUpdate {
    pub name: Option<String>,
    pub price: Option<f64>,
}
"""
        parser = RustParser()
        structs, enums, tables, derives, impl_blocks, route_handlers = parser.parse_source(rust_code)

        assert len(structs) == 4  # ApiResponse + 3 Diesel structs
        assert len(derives) == 3  # Only the Diesel ones

        # Check that only Diesel derives are extracted
        derive_names = {d.struct_name for d in derives}
        assert derive_names == {"Product", "NewProduct", "ProductUpdate"}

        # Check specific derives
        product_derive = next(d for d in derives if d.struct_name == "Product")
        assert set(product_derive.derives) == {"Queryable"}

        new_product_derive = next(d for d in derives if d.struct_name == "NewProduct")
        assert set(new_product_derive.derives) == {"Insertable"}

        update_derive = next(d for d in derives if d.struct_name == "ProductUpdate")
        assert set(update_derive.derives) == {"AsChangeset"}
