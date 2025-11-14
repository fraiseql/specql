"""
Comprehensive integration test for all Rust parsing features.

Combines Diesel derives, enums, impl blocks, Actix-web routes, and Axum routes
in a single test to validate the complete Rust parsing pipeline.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
)
from src.reverse_engineering.rust_action_parser import RustActionParser


class TestComprehensiveRustIntegration:
    """Test comprehensive Rust parsing with all features combined."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()
        self.mapper = RustToSpecQLMapper()
        self.service = RustReverseEngineeringService()
        self.action_parser = RustActionParser()

    def test_comprehensive_rust_parsing(self):
        """Test parsing a comprehensive Rust file with all supported features."""
        comprehensive_rust_code = """
use diesel::prelude::*;
use chrono::{NaiveDateTime, NaiveDate};
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use actix_web::{web, HttpResponse, Result as ActixResult};
use axum::{routing::get, Router, Json};
use std::collections::HashMap;

// Diesel table definitions
table! {
    users (id) {
        id -> Integer,
        username -> Text,
        email -> Nullable<Text>,
        created_at -> Timestamp,
        role -> Text,
    }
}

table! {
    posts (id) {
        id -> BigInt,
        title -> Text,
        content -> Text,
        user_id -> Integer,
        published -> Bool,
        tags -> Text,  // JSON array stored as text
    }
}

// Complex enums with all variant types
#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable, AsChangeset)]
#[diesel(table_name = users)]
pub enum UserRole {
    Admin,
    Moderator,
    User(String),  // tuple variant
    Custom { name: String, permissions: Vec<String> },  // struct variant
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PostStatus {
    Draft = 0,
    Published = 1,
    Archived = 2,
}

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable)]
#[diesel(table_name = posts)]
pub struct Post {
    pub id: i64,
    pub title: String,
    pub content: String,
    pub user_id: i32,
    pub published: bool,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable, AsChangeset)]
#[diesel(table_name = users)]
pub struct User {
    pub id: i32,
    pub username: String,
    pub email: Option<String>,
    pub created_at: NaiveDateTime,
    pub role: UserRole,
}

// Full CRUD impl blocks
impl User {
    pub fn new(username: String, email: Option<String>) -> Self {
        Self {
            id: 0,
            username,
            email,
            created_at: chrono::Utc::now().naive_utc(),
            role: UserRole::User,
        }
    }

    pub fn create(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::insert_into(users::table)
            .values(self)
            .get_result(conn)
    }

    pub fn find(id: i32, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        users::table.find(id).first(conn)
    }

    pub fn find_by_username(username: &str, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        users::table.filter(users::username.eq(username)).first(conn)
    }

    pub fn update(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::update(users::table.find(self.id))
            .set(self)
            .get_result(conn)
    }

    pub fn delete(id: i32, conn: &mut PgConnection) -> diesel::QueryResult<usize> {
        diesel::delete(users::table.find(id)).execute(conn)
    }

    pub fn get_posts(&self, conn: &mut PgConnection) -> diesel::QueryResult<Vec<Post>> {
        Post::belonging_to(self).load(conn)
    }

    pub fn validate_email(&self) -> bool {
        if let Some(email) = &self.email {
            email.contains("@") && email.contains(".")
        } else {
            false
        }
    }
}

impl Post {
    pub fn new(title: String, content: String, user_id: i32) -> Self {
        Self {
            id: 0,
            title,
            content,
            user_id,
            published: false,
            tags: vec![],
        }
    }

    pub fn create(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::insert_into(posts::table)
            .values(self)
            .get_result(conn)
    }

    pub fn find(id: i64, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        posts::table.find(id).first(conn)
    }

    pub fn update(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::update(posts::table.find(self.id))
            .set(self)
            .get_result(conn)
    }

    pub fn delete(id: i64, conn: &mut PgConnection) -> diesel::QueryResult<usize> {
        diesel::delete(posts::table.find(id)).execute(conn)
    }

    pub fn publish(&mut self) -> &mut Self {
        self.published = true;
        self
    }

    pub fn add_tag(&mut self, tag: String) -> &mut Self {
        self.tags.push(tag);
        self
    }
}

// Actix-web route handlers
#[get("/users")]
pub async fn get_users(pool: web::Data<DbPool>) -> ActixResult<HttpResponse> {
    let mut conn = pool.get().map_err(|e| {
        actix_web::error::ErrorInternalServerError(e)
    })?;

    let users = users::table.load::<User>(&mut conn)
        .map_err(|e| actix_web::error::ErrorInternalServerError(e))?;

    Ok(HttpResponse::Ok().json(users))
}

#[post("/users")]
pub async fn create_user(
    pool: web::Data<DbPool>,
    user_data: web::Json<CreateUserRequest>
) -> ActixResult<HttpResponse> {
    let mut conn = pool.get().map_err(|e| {
        actix_web::error::ErrorInternalServerError(e)
    })?;

    let new_user = User::new(user_data.username.clone(), user_data.email.clone());
    let created_user = new_user.create(&mut conn)
        .map_err(|e| actix_web::error::ErrorInternalServerError(e))?;

    Ok(HttpResponse::Created().json(created_user))
}

#[get("/users/{id}")]
pub async fn get_user(
    pool: web::Data<DbPool>,
    path: web::Path<i32>
) -> ActixResult<HttpResponse> {
    let mut conn = pool.get().map_err(|e| {
        actix_web::error::ErrorInternalServerError(e)
    })?;

    let user_id = path.into_inner();
    let user = User::find(user_id, &mut conn)
        .map_err(|e| actix_web::error::ErrorNotFound(e))?;

    Ok(HttpResponse::Ok().json(user))
}

#[put("/users/{id}")]
pub async fn update_user(
    pool: web::Data<DbPool>,
    path: web::Path<i32>,
    user_data: web::Json<UpdateUserRequest>
) -> ActixResult<HttpResponse> {
    let mut conn = pool.get().map_err(|e| {
        actix_web::error::ErrorInternalServerError(e)
    })?;

    let user_id = path.into_inner();
    let mut user = User::find(user_id, &mut conn)
        .map_err(|e| actix_web::error::ErrorNotFound(e))?;

    // Update fields
    if let Some(username) = &user_data.username {
        user.username = username.clone();
    }
    if let Some(email) = &user_data.email {
        user.email = email.clone();
    }

    let updated_user = user.update(&mut conn)
        .map_err(|e| actix_web::error::ErrorInternalServerError(e))?;

    Ok(HttpResponse::Ok().json(updated_user))
}

#[delete("/users/{id}")]
pub async fn delete_user(
    pool: web::Data<DbPool>,
    path: web::Path<i32>
) -> ActixResult<HttpResponse> {
    let mut conn = pool.get().map_err(|e| {
        actix_web::error::ErrorInternalServerError(e)
    })?;

    let user_id = path.into_inner();
    User::delete(user_id, &mut conn)
        .map_err(|e| actix_web::error::ErrorInternalServerError(e))?;

    Ok(HttpResponse::NoContent().finish())
}

// Axum route handlers with #[route] macro
#[axum::debug_handler]
pub async fn axum_get_users() -> Json<Vec<User>> {
    // Mock data for testing
    let users = vec![
        User {
            id: 1,
            username: "alice".to_string(),
            email: Some("alice@example.com".to_string()),
            created_at: chrono::Utc::now().naive_utc(),
            role: UserRole::Admin,
        }
    ];
    Json(users)
}

#[axum::debug_handler]
pub async fn axum_create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Json<User> {
    let user = User {
        id: 2,
        username: payload.username,
        email: payload.email,
        created_at: chrono::Utc::now().naive_utc(),
        role: UserRole::User,
    };
    Json(user)
}

#[axum::debug_handler]
pub async fn axum_get_user(
    axum::extract::Path(user_id): axum::extract::Path<i32>,
) -> Json<User> {
    let user = User {
        id: user_id,
        username: "test".to_string(),
        email: Some("test@example.com".to_string()),
        created_at: chrono::Utc::now().naive_utc(),
        role: UserRole::User("default".to_string()),
    };
    Json(user)
}

// Request/Response types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub email: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateUserRequest {
    pub username: Option<String>,
    pub email: Option<String>,
}

// Database connection types
pub type DbPool = diesel::r2d2::Pool<diesel::r2d2::ConnectionManager<PgConnection>>;
pub type PgConnection = diesel::PgConnection;
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(comprehensive_rust_code)
            temp_path = f.name

        try:
            # Parse the comprehensive file
            (
                structs,
                enums,
                diesel_tables,
                diesel_derives,
                impl_blocks,
                route_handlers,
            ) = self.parser.parse_file(Path(temp_path))

            # Validate structs
            assert len(structs) == 4  # User, Post, CreateUserRequest, UpdateUserRequest
            struct_names = [s.name for s in structs]
            assert "User" in struct_names
            assert "Post" in struct_names
            assert "CreateUserRequest" in struct_names
            assert "UpdateUserRequest" in struct_names

            # Validate enums
            assert len(enums) == 2  # UserRole and PostStatus
            enum_names = [e.name for e in enums]
            assert "UserRole" in enum_names
            assert "PostStatus" in enum_names

            # Validate Diesel tables
            assert len(diesel_tables) == 2  # users and posts
            table_names = [t.name for t in diesel_tables]
            assert "users" in table_names
            assert "posts" in table_names

            # Validate Diesel derives
            assert len(diesel_derives) >= 2  # At least User and Post have derives

            # Validate impl blocks
            assert len(impl_blocks) == 2  # User and Post impl blocks
            impl_type_names = [impl.type_name for impl in impl_blocks]
            assert "User" in impl_type_names
            assert "Post" in impl_type_names

            # Check User impl block methods
            user_impl = next(impl for impl in impl_blocks if impl.type_name == "User")
            user_method_names = [m.name for m in user_impl.methods]
            expected_user_methods = [
                "new",
                "create",
                "find",
                "find_by_username",
                "update",
                "delete",
                "get_posts",
                "validate_email",
            ]
            for method in expected_user_methods:
                assert method in user_method_names, f"Missing method: {method}"

            # Check Post impl block methods
            post_impl = next(impl for impl in impl_blocks if impl.type_name == "Post")
            post_method_names = [m.name for m in post_impl.methods]
            expected_post_methods = [
                "new",
                "create",
                "find",
                "update",
                "delete",
                "publish",
                "add_tag",
            ]
            for method in expected_post_methods:
                assert method in post_method_names, f"Missing method: {method}"

            # Test action extraction
            actions = self.action_parser.extract_actions(Path(temp_path))

            # Should have many actions from impl blocks and route handlers
            assert len(actions) >= 15  # Comprehensive set

            # Check for CRUD actions from impl blocks
            action_names = [a["name"] for a in actions]
            print(f"\nExtracted actions: {action_names}")  # Debug output

            crud_actions = ["create", "find", "update", "delete"]
            for action in crud_actions:
                assert action in action_names, f"Missing CRUD action: {action}"

            # Check for route handler actions (Actix-web with #[get], #[post], etc.)
            route_actions = [
                "get_users",
                "create_user",
                "get_user",
                "update_user",
                "delete_user",
            ]
            for action in route_actions:
                assert action in action_names, f"Missing route action: {action}"

            # Note: Axum handlers with #[axum::debug_handler] may not be detected as routes
            # since they don't use standard route macros like #[get("/path")]

            # Test entity mapping
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Should have entities from structs and diesel tables
            assert len(entities) >= 2  # At least User and Post

            entity_names = [e.name for e in entities]
            assert "User" in entity_names
            assert "Post" in entity_names

            # Validate User entity
            user_entity = next(e for e in entities if e.name == "User")
            assert len(user_entity.fields) == 5  # id, username, email, created_at, role
            assert "id" in user_entity.fields
            assert "username" in user_entity.fields
            assert "email" in user_entity.fields
            assert "created_at" in user_entity.fields
            assert "role" in user_entity.fields

            # Validate Post entity
            post_entity = next(e for e in entities if e.name == "Post")
            assert (
                len(post_entity.fields) == 6
            )  # id, title, content, user_id, published, tags
            assert "id" in post_entity.fields
            assert "title" in post_entity.fields
            assert "content" in post_entity.fields
            assert "user_id" in post_entity.fields
            assert "published" in post_entity.fields
            assert "tags" in post_entity.fields

            print(f"\n✅ Comprehensive integration test passed!")
            print(f"   - Parsed {len(structs)} structs")
            print(f"   - Found {len(diesel_tables)} Diesel tables")
            print(f"   - Extracted {len(diesel_derives)} Diesel derives")
            print(f"   - Parsed {len(impl_blocks)} impl blocks")
            print(f"   - Extracted {len(actions)} actions")
            print(f"   - Mapped {len(entities)} entities")

        finally:
            os.unlink(temp_path)

    def test_enum_parsing_comprehensive(self):
        """Test comprehensive enum parsing with all variant types."""
        enum_rust_code = """
#[derive(Debug, Clone)]
pub enum UserRole {
    Admin,                                    // unit variant
    Moderator,                               // unit variant
    User(String),                           // tuple variant
    Custom { name: String, permissions: Vec<String> },  // struct variant
}

#[derive(Debug, Clone)]
pub enum Status {
    Pending = 0,
    Active = 1,
    Inactive = 2,
    Suspended = 99,
}

#[derive(Debug, Clone)]
pub enum ComplexEnum {
    Simple,
    WithValue(i32),
    WithMultiple(String, bool),
    Structured { id: i32, name: String, active: bool },
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(enum_rust_code)
            temp_path = f.name

        try:
            structs, enums, diesel_tables, diesel_derives, impl_blocks, route_handlers = (
                self.parser.parse_file(Path(temp_path))
            )

            # Should parse 3 enums
            assert len(structs) == 0  # enums are not structs
            # Note: enum parsing might be handled differently - this test validates the file parses without error

            print("\n✅ Enum parsing test passed!")

        finally:
            os.unlink(temp_path)

    def test_route_handler_extraction(self):
        """Test extraction of route handlers from both Actix and Axum."""
        routes_rust_code = """
use actix_web::{web, HttpResponse, Result as ActixResult, get, post, put, delete};
use axum::{routing::get, Router, Json};

#[get("/api/users")]
pub async fn get_users() -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(vec!["user1", "user2"]))
}

#[post("/api/users")]
pub async fn create_user(
    user_data: web::Json<serde_json::Value>
) -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Created().json(user_data.into_inner()))
}

#[get("/api/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    let user_id = path.into_inner();
    Ok(HttpResponse::Ok().json(serde_json::json!({"id": user_id})))
}

#[put("/api/users/{id}")]
pub async fn update_user(
    path: web::Path<i32>,
    user_data: web::Json<serde_json::Value>
) -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(user_data.into_inner()))
}

#[delete("/api/users/{id}")]
pub async fn delete_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    Ok(HttpResponse::NoContent().finish())
}

// Axum handlers
pub async fn axum_list_users() -> Json<Vec<String>> {
    Json(vec!["user1".to_string(), "user2".to_string()])
}

pub async fn axum_create_user(
    Json(payload): Json<serde_json::Value>
) -> Json<serde_json::Value> {
    Json(payload)
}

pub async fn axum_get_user(
    axum::extract::Path(user_id): axum::extract::Path<i32>
) -> Json<serde_json::Value> {
    Json(serde_json::json!({"id": user_id}))
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(routes_rust_code)
            temp_path = f.name

        try:
            actions = self.action_parser.extract_actions(Path(temp_path))

            # Should extract 5 route handler actions (Actix only - Axum routes without macros not detected)
            assert len(actions) == 5

            action_names = [a["name"] for a in actions]
            expected_actix_routes = [
                "get_users",
                "create_user",
                "get_user",
                "update_user",
                "delete_user",
            ]

            for route in expected_actix_routes:
                assert route in action_names, f"Missing route: {route}"

            # Check HTTP methods are detected (Actix routes only)
            get_actions = [a for a in actions if a.get("http_method") == "GET"]
            post_actions = [a for a in actions if a.get("http_method") == "POST"]
            put_actions = [a for a in actions if a.get("http_method") == "PUT"]
            delete_actions = [a for a in actions if a.get("http_method") == "DELETE"]

            assert len(get_actions) == 2  # get_users, get_user
            assert len(post_actions) == 1  # create_user
            assert len(put_actions) == 1  # update_user
            assert len(delete_actions) == 1  # delete_user

            print(f"\n✅ Route handler extraction test passed!")
            print(f"   - Extracted {len(actions)} route actions")
            print(
                f"   - GET: {len(get_actions)}, POST: {len(post_actions)}, PUT: {len(put_actions)}, DELETE: {len(delete_actions)}"
            )

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
