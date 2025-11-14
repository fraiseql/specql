"""
Rust Integration Examples for SpecQL Reverse Engineering

This file demonstrates real-world usage of the Rust parser with Diesel integration.
Each example shows how to use the reverse engineering service to parse Rust code
and generate SpecQL entities.

INSTALLATION: Copy to examples/rust_integration_examples.py

PURPOSE:
- Demonstrate end-to-end Rust reverse engineering workflows
- Show Diesel table! macro parsing capabilities
- Provide examples for common Rust ORM patterns
- Validate integration between Rust parser and SpecQL entities

USAGE:
    python examples/rust_integration_examples.py
"""

import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import RustReverseEngineeringService


def example_1_basic_struct_parsing():
    """Example 1: Basic struct parsing with foreign keys."""
    print("=== Example 1: Basic Struct Parsing ===")

    rust_code = """
    #[derive(Debug, Clone)]
    pub struct User {
        pub id: i32,
        pub username: String,
        pub email: String,
        pub created_at: chrono::NaiveDateTime,
    }

    #[derive(Debug, Clone)]
    pub struct Post {
        pub id: i32,
        pub title: String,
        pub content: String,
        pub user_id: i32,  // Foreign key
        pub published: bool,
    }
    """

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        entities = service.reverse_engineer_file(Path(temp_path))

        print(f"Parsed {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity.name} ({entity.table})")
            print(f"    Fields: {list(entity.fields.keys())}")
            # Check for FK detection
            for field_name, field in entity.fields.items():
                if field.reference_entity:
                    print(f"    FK: {field_name} -> {field.reference_entity}")
        print()

    finally:
        os.unlink(temp_path)


def example_2_diesel_table_macro():
    """Example 2: Diesel table! macro parsing."""
    print("=== Example 2: Diesel table! Macro Parsing ===")

    rust_code = """
    table! {
        users (id) {
            id -> Integer,
            username -> Text,
            email -> Text,
            created_at -> Timestamp,
        }
    }

    table! {
        posts (id) {
            id -> Integer,
            title -> Text,
            content -> Text,
            user_id -> Integer,
            published -> Bool,
        }
    }
    """

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        entities = service.reverse_engineer_file(
            Path(temp_path), include_diesel_tables=True
        )

        print(f"Parsed {len(entities)} entities from Diesel tables:")
        for entity in entities:
            print(f"  - {entity.name} ({entity.table})")
            print(f"    Fields: {list(entity.fields.keys())}")
            # Check for FK detection in Diesel tables
            for field_name, field in entity.fields.items():
                if field.reference_entity:
                    print(f"    FK: {field_name} -> {field.reference_entity}")
        print()

    finally:
        os.unlink(temp_path)


def example_3_belongs_to_relationships():
    """Example 3: Belongs-to relationship parsing."""
    print("=== Example 3: Belongs-to Relationships ===")

    rust_code = """
    use diesel::prelude::*;

    #[derive(Debug, Clone, Queryable, Associations)]
    #[belongs_to(User)]
    pub struct Post {
        pub id: i32,
        pub title: String,
        pub content: String,
        pub user_id: i32,
        pub published: bool,
    }

    #[derive(Debug, Clone, Queryable)]
    pub struct User {
        pub id: i32,
        pub username: String,
        pub email: String,
    }

    #[derive(Debug, Clone, Queryable, Associations)]
    #[belongs_to(Post)]
    #[belongs_to(User)]
    pub struct Comment {
        pub id: i32,
        pub content: String,
        pub post_id: i32,
        pub user_id: i32,
        pub created_at: chrono::NaiveDateTime,
    }
    """

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        entities = service.reverse_engineer_file(Path(temp_path))

        print(f"Parsed {len(entities)} entities with relationships:")
        for entity in entities:
            print(f"  - {entity.name}")
            relationships = []
            for field_name, field in entity.fields.items():
                if field.reference_entity:
                    relationships.append(f"{field_name} -> {field.reference_entity}")
            if relationships:
                print(f"    Relationships: {relationships}")
            else:
                print("    No relationships detected")
        print()

    finally:
        os.unlink(temp_path)


def example_4_complex_types_and_attributes():
    """Example 4: Complex types and attributes."""
    print("=== Example 4: Complex Types and Attributes ===")

    rust_code = """
    use diesel::prelude::*;
    use serde::{Deserialize, Serialize};

    #[derive(Debug, Clone, Serialize, Deserialize, Queryable)]
    #[table_name = "users"]
    pub struct User {
        #[primary_key]
        pub id: uuid::Uuid,
        pub username: String,
        pub email: String,
        pub preferences: serde_json::Value,  // JSON field
        pub tags: Vec<String>,  // Array field
        pub metadata: Option<serde_json::Value>,  // Optional JSON
        pub created_at: chrono::NaiveDateTime,
    }

    #[derive(Debug, Clone, Queryable, Associations)]
    #[belongs_to(User)]
    pub struct UserProfile {
        pub id: i32,
        pub user_id: uuid::Uuid,
        pub bio: Option<String>,
        pub avatar_url: Option<String>,
        pub settings: serde_json::Value,
    }
    """

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        entities = service.reverse_engineer_file(Path(temp_path))

        print(f"Parsed {len(entities)} entities with complex types:")
        for entity in entities:
            print(f"  - {entity.name}")
            for field_name, field in entity.fields.items():
                print(
                    f"    {field_name}: {field.type_name} (nullable: {field.nullable})"
                )
                if field.reference_entity:
                    print(f"      -> references {field.reference_entity}")
        print()

    finally:
        os.unlink(temp_path)


def example_5_directory_parsing():
    """Example 5: Directory parsing with mixed content."""
    print("=== Example 5: Directory Parsing ===")

    service = RustReverseEngineeringService()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple files
        files_content = {
            "models.rs": """
            pub struct User { pub id: i32, pub name: String }
            pub struct Post { pub id: i32, pub user_id: i32, pub title: String }
            """,
            "schema.rs": """
            table! {
                comments (id) {
                    id -> Integer,
                    post_id -> Integer,
                    content -> Text,
                }
            }
            """,
            "invalid.rs": """
            // This file has syntax errors
            pub struct Broken { invalid syntax here
            """,
        }

        for filename, content in files_content.items():
            (Path(temp_dir) / filename).write_text(content)

        # Parse directory
        entities = service.reverse_engineer_directory(
            Path(temp_dir), include_diesel_tables=True
        )

        print(f"Parsed {len(entities)} entities from directory:")
        for entity in entities:
            print(f"  - {entity.name} (from {entity.table})")
            field_count = len(entity.fields)
            fk_count = sum(1 for f in entity.fields.values() if f.reference_entity)
            print(f"    {field_count} fields, {fk_count} foreign keys")
        print()


def example_6_enum_parsing():
    """Example 6: Enum parsing with all variant types."""
    print("=== Example 6: Enum Parsing ===")

    rust_code = """
    #[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable, AsChangeset)]
    #[diesel(table_name = users)]
    pub enum UserRole {
        Admin,                                    // unit variant
        Moderator,                               // unit variant
        User(String),                           // tuple variant
        Custom { name: String, permissions: Vec<String> },  // struct variant
    }

    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub enum PostStatus {
        Draft = 0,
        Published = 1,
        Archived = 2,
    }

    #[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable)]
    #[diesel(table_name = users)]
    pub struct User {
        pub id: i32,
        pub username: String,
        pub role: UserRole,
        pub status: PostStatus,
    }
    """

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        entities = service.reverse_engineer_file(Path(temp_path))

        print(f"Parsed {len(entities)} entities with enums:")
        for entity in entities:
            print(f"  - {entity.name}")
            for field_name, field in entity.fields.items():
                print(f"    {field_name}: {field.type_name}")
        print()

    finally:
        os.unlink(temp_path)


def example_7_route_handler_extraction():
    """Example 7: Route handler extraction from Actix and Axum."""
    print("=== Example 7: Route Handler Extraction ===")

    rust_code = """
use actix_web::{web, HttpResponse, Result as ActixResult, get, post, put, delete};
use axum::{Json, extract::Path};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub email: Option<String>,
}

// Actix-web route handlers
#[get("/users")]
pub async fn get_users() -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(vec!["user1", "user2"]))
}

#[post("/users")]
pub async fn create_user(
    user_data: web::Json<CreateUserRequest>
) -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Created().json(serde_json::json!({"id": 1})))
}

#[get("/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    let user_id = path.into_inner();
    Ok(HttpResponse::Ok().json(serde_json::json!({"id": user_id})))
}

#[put("/users/{id}")]
pub async fn update_user(
    path: web::Path<i32>,
    user_data: web::Json<CreateUserRequest>
) -> ActixResult<HttpResponse> {
    let user_id = path.into_inner();
    Ok(HttpResponse::Ok().json(serde_json::json!({"id": user_id, "updated": true})))
}

#[delete("/users/{id}")]
pub async fn delete_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    Ok(HttpResponse::NoContent().finish())
}

// Axum route handlers
pub async fn axum_get_users() -> Json<Vec<String>> {
    Json(vec!["user1".to_string(), "user2".to_string()])
}

pub async fn axum_create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Json<serde_json::Value> {
    Json(serde_json::json!({"id": 2, "username": payload.username}))
}

pub async fn axum_get_user(
    Path(user_id): Path<i32>,
) -> Json<serde_json::Value> {
    Json(serde_json::json!({"id": user_id, "username": "test"}))
}
"""

    from src.reverse_engineering.rust_action_parser import RustActionParser

    action_parser = RustActionParser()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        actions = action_parser.extract_actions(Path(temp_path))

        print(f"Extracted {len(actions)} actions from route handlers:")
        for action in actions:
            method = action.get("http_method", "N/A")
            path = action.get("path", "N/A")
            name = action["name"]
            action_type = action["type"]
            print(f"  - {method} {path} -> {name} ({action_type})")
        print()

    finally:
        os.unlink(temp_path)


def example_8_performance_benchmark():
    """Example 6: Performance benchmark with large codebase."""
    print("=== Example 6: Performance Benchmark ===")

    # Generate a large number of structs
    structs = []
    for i in range(50):  # 50 structs
        struct = f"""
        #[derive(Debug, Clone)]
        pub struct Entity{i} {{
            pub id: i32,
            pub name: String,
            pub description: String,
            pub parent_id: Option<i32>,
            pub created_at: chrono::NaiveDateTime,
        }}
        """
        structs.append(struct)

    rust_code = "\n".join(structs)

    service = RustReverseEngineeringService()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(rust_code)
        temp_path = f.name

    try:
        import time

        start_time = time.time()

        entities = service.reverse_engineer_file(Path(temp_path))

        end_time = time.time()
        duration = end_time - start_time

        print(f"Parsed {len(entities)} entities in {duration:.3f} seconds")
        print(".2f")
        print()

    finally:
        os.unlink(temp_path)


def main():
    """Run all integration examples."""
    print("Rust Integration Examples for SpecQL")
    print("=" * 50)
    print()

    examples = [
        example_1_basic_struct_parsing,
        example_2_diesel_table_macro,
        example_3_belongs_to_relationships,
        example_4_complex_types_and_attributes,
        example_5_directory_parsing,
        example_6_enum_parsing,
        example_7_route_handler_extraction,
        example_8_performance_benchmark,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")
            print()

    print("All examples completed!")


if __name__ == "__main__":
    main()
