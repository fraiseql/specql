# Rust Migration Guide

This guide explains how to migrate Rust projects to use SpecQL for schema management and code generation.

## Overview

SpecQL now supports Rust struct parsing and can reverse-engineer your existing Rust code into SpecQL entities. This enables:

- **Schema Management**: Centralized database schema definitions
- **Code Generation**: Generate Rust structs, Diesel migrations, and API endpoints
- **Multi-Language Support**: Maintain consistency across different language implementations
- **Type Safety**: Leverage Rust's type system while benefiting from SpecQL's features

## Supported Features

### Struct Parsing
- ✅ Basic Rust structs with named fields
- ✅ All primitive types (i32, i64, bool, f32, f64, etc.)
- ✅ String types (String, &str)
- ✅ Option<T> for nullable fields
- ✅ Collections (Vec<T>, HashMap<K,V>) mapped to JSONB
- ✅ Time types (NaiveDateTime, DateTime, etc.)
- ✅ UUID support
- ✅ Complex types (serde_json::Value)

### Diesel Integration
- ✅ Basic struct parsing (Diesel schema macro parsing planned for future release)
- ✅ Relationship attribute recognition (`#[belongs_to(...)]`)
- ✅ Type mapping from Diesel to SQL types

### Enum Parsing
- ✅ Unit variants (`Admin`, `Moderator`)
- ✅ Tuple variants (`User(String)`)
- ✅ Struct variants (`Custom { name: String, permissions: Vec<String> }`)
- ✅ Discriminants (`Pending = 0`, `Active = 1`)
- ✅ Diesel derive support for enums

### Route Handler Parsing
- ✅ Actix-web route handlers (`#[get("/users")]`, `#[post("/users")]`, etc.)
- ✅ Axum route handlers (function-based routing)
- ✅ HTTP method detection (GET, POST, PUT, DELETE)
- ✅ Path parameter extraction
- ✅ Automatic REST endpoint mapping

### Impl Block Parsing
- ✅ Extract business logic from `impl` blocks
- ✅ Automatic CRUD pattern detection from method names
- ✅ Parameter and return type mapping
- ✅ Async method support
- ✅ Public method filtering (private methods ignored)

## Quick Start

### 1. Install SpecQL

```bash
pip install specql-generator
```

### 2. Prepare Your Rust Code

Ensure your Rust structs are properly defined:

```rust
use chrono::{NaiveDateTime, NaiveDate};
use uuid::Uuid;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i32,
    pub username: String,
    pub email: Option<String>,
    pub created_at: NaiveDateTime,
    pub profile: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Post {
    pub id: i64,
    pub title: String,
    pub content: Option<String>,
    pub user_id: i32,  // Foreign key
    pub published_at: Option<NaiveDateTime>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
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
```

### 3. Reverse Engineer

```bash
# Reverse engineer a single file
specql reverse rust path/to/models.rs

# Reverse engineer a directory
specql reverse rust path/to/src/ --output user_entities.yaml

# Generate SpecQL entities
specql generate --input user_entities.yaml --language rust
```

### 4. Extract Actions from Business Logic

SpecQL can also extract actions from your Rust impl blocks:

```rust
impl User {
    pub fn create_user(&self, name: String, email: String) -> Result<User, Error> {
        // Create logic
        Ok(User { id: 1, name, email })
    }

    pub fn get_user(&self, id: i32) -> Result<User, Error> {
        // Read logic
        Ok(User { id, name: "test".to_string(), email: "test@test.com".to_string() })
    }

    pub fn update_user(&self, id: i32, name: String) -> Result<(), Error> {
        // Update logic
        Ok(())
    }

    pub fn delete_user(&self, id: i32) -> Result<(), Error> {
        // Delete logic
        Ok(())
    }

    pub fn validate_email(&self, email: &str) -> bool {
        // Custom business logic
        email.contains("@")
    }
}
```

The system automatically detects CRUD patterns and maps them to SpecQL actions:
- `create_user` → `create` action
- `get_user` → `read` action
- `update_user` → `update` action
- `delete_user` → `delete` action
- `validate_email` → `custom` action

### 5. Extract Route Handlers

SpecQL can also extract REST endpoints from your route handlers:

#### Actix-web Example
```rust
use actix_web::{web, HttpResponse, Result as ActixResult};

#[get("/users")]
pub async fn get_users() -> ActixResult<HttpResponse> {
    // Return all users
    Ok(HttpResponse::Ok().json(vec!["user1", "user2"]))
}

#[post("/users")]
pub async fn create_user(
    user_data: web::Json<CreateUserRequest>
) -> ActixResult<HttpResponse> {
    // Create new user
    Ok(HttpResponse::Created().json({"id": 1}))
}

#[get("/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    let user_id = path.into_inner();
    // Return specific user
    Ok(HttpResponse::Ok().json({"id": user_id}))
}
```

#### Axum Example
```rust
use axum::{Json, extract::Path};

pub async fn get_users() -> Json<Vec<String>> {
    Json(vec!["user1".to_string(), "user2".to_string()])
}

pub async fn create_user(
    Json(payload): Json<CreateUserRequest>,
) -> Json<User> {
    Json(User {
        id: 1,
        username: payload.username,
        email: payload.email,
    })
}

pub async fn get_user(
    Path(user_id): Path<i32>,
) -> Json<User> {
    Json(User {
        id: user_id,
        username: "test".to_string(),
        email: Some("test@example.com".to_string()),
    })
}
```

Route handlers are automatically mapped to REST endpoints:
- `#[get("/users")]` → `GET /users` endpoint
- `#[post("/users")]` → `POST /users` endpoint
- `#[get("/users/{id}")]` → `GET /users/{id}` endpoint

## Type Mapping

### Rust to SQL Type Mapping

| Rust Type | SQL Type | Notes |
|-----------|----------|-------|
| `i32` | `integer` | |
| `i64` | `bigint` | |
| `f32` | `real` | |
| `f64` | `double_precision` | |
| `bool` | `boolean` | |
| `String` | `text` | |
| `&str` | `text` | |
| `Option<T>` | `T` | Nullable at field level |
| `Vec<T>` | `jsonb` | JSON array |
| `HashMap<K,V>` | `jsonb` | JSON object |
| `NaiveDateTime` | `timestamp` | |
| `DateTime<Utc>` | `timestamp with time zone` | |
| `Uuid` | `uuid` | |
| `serde_json::Value` | `jsonb` | |

### Nullable Fields

Rust `Option<T>` types are automatically mapped to nullable SQL fields:

```rust
pub struct User {
    pub id: i32,                    // NOT NULL
    pub email: Option<String>,      // NULL
    pub age: Option<i32>,          // NULL
}
```

## Relationships

### Foreign Keys

Foreign key relationships are detected through field naming conventions:

```rust
#[derive(Debug, Clone)]
pub struct Post {
    pub id: i64,
    pub title: String,
    pub user_id: i32,  // Automatically detected as FK to User
    pub category_id: Option<i32>,  // FK to Category
}
```

### Diesel Relationships

SpecQL recognizes Diesel `belongs_to` attributes:

```rust
use diesel::prelude::*;

#[derive(Debug, Clone)]
pub struct Post {
    pub id: i64,
    pub title: String,
    #[belongs_to(User)]
    pub user_id: i32,
    #[belongs_to(Category, foreign_key = "category_id")]
    pub category_id: Option<i32>,
}
```

## Advanced Usage

### Custom Type Mapping

For custom types not in the default mapping, you can extend the type mapper:

```python
from src.reverse_engineering.rust_parser import RustTypeMapper

class CustomRustTypeMapper(RustTypeMapper):
    def __init__(self):
        super().__init__()
        # Add custom mappings
        self.type_mapping.update({
            'MyCustomType': 'text',
            'DomainId': 'uuid',
        })
```

### Complex Schemas

For complex schemas with many entities, organize your code:

```
src/
  models/
    user.rs
    post.rs
    category.rs
    mod.rs
```

Then reverse engineer the entire directory:

```bash
specql reverse rust src/models/ --recursive
```

## Best Practices

### Struct Design

1. **Use descriptive names**: Struct and field names become table and column names
2. **Leverage Option<T>**: Use `Option<T>` for nullable fields
3. **Add documentation**: Use doc comments for better entity descriptions
4. **Consistent naming**: Follow Rust naming conventions

### Schema Organization

1. **Group related entities**: Keep related structs in the same file or directory
2. **Use modules**: Organize complex schemas with Rust modules
3. **Version control**: Keep your SpecQL schemas in version control
4. **Validation**: Regularly validate generated code against your requirements

## Troubleshooting

### Common Issues

#### Parser Not Found
```
Error: Rust parser binary not found
```
**Solution**: Build the Rust parser:
```bash
cd rust && cargo build --release
```

#### Unsupported Syntax
```
Error: Failed to parse struct
```
**Solution**: Ensure your Rust code uses supported syntax:
- Use named structs (not tuple structs)
- Avoid complex macros in struct definitions
- Use supported attribute syntax

#### Type Mapping Issues
```
Warning: Unknown type mapping
```
**Solution**: Check the type mapping table above or extend the type mapper for custom types.

### Performance Considerations

- **Large files**: Split large model files into smaller modules
- **Complex types**: Very complex generic types may map to `text` as fallback
- **Many structs**: Parsing scales linearly with the number of structs

## Migration Workflow

### Step 1: Analyze Existing Code
```bash
# Get an overview of your Rust structs
specql reverse rust src/models/ --dry-run
```

### Step 2: Generate SpecQL Schema
```bash
# Create the SpecQL YAML file
specql reverse rust src/models/ --output schema.yaml
```

### Step 3: Review and Customize
Edit `schema.yaml` to add:
- Custom validations
- Additional relationships
- Business logic rules
- API endpoints

### Step 4: Generate Code
```bash
# Generate updated Rust structs
specql generate --input schema.yaml --language rust --output src/generated/

# Generate database migrations
specql generate --input schema.yaml --language sql --output migrations/
```

### Step 5: Integrate
- Replace manual struct definitions with generated ones
- Update your Diesel schema files
- Run database migrations
- Update your application code

## Next Steps

- **Diesel Schema Integration**: Full parsing of `table!` macros (planned)
- **Code Generation**: Generate Rust structs from SpecQL schemas
- **Migration Generation**: Automatic Diesel migration creation
- **API Generation**: Generate REST APIs from entity definitions

## Support

For issues or questions:
- Check the [troubleshooting guide](RUST_TROUBLESHOOTING.md)
- File issues on GitHub
- Review the test cases in `tests/integration/rust/`