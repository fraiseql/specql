# Rust Web Framework Support

This document outlines the supported Rust web frameworks for endpoint detection in SpecQL's reverse engineering capabilities.

## Supported Frameworks

SpecQL supports endpoint detection for 6 major Rust web frameworks:

### 1. Actix-web
**Detection Pattern**: `#[get("/path")]` macros and service configuration
**Features**:
- Route macros (`#[get]`, `#[post]`, `#[put]`, `#[delete]`, etc.)
- Service configuration with guards: `web::resource("/path").guard(...).route(...)`
- Nested scopes: `web::scope("/api").service(web::scope("/v1")...)`

**Example**:
```rust
// Macro-based routes
#[get("/users")]
pub async fn list_users() -> HttpResponse { }

// Service configuration with guards
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/contacts")
            .guard(guard::Header("content-type", "application/json"))
            .route(web::post().to(create_contact))
    );
}

// Nested scopes
web::scope("/api")
    .service(
        web::scope("/v1")
            .route("/users", web::get().to(list_users))
    )
```

### 2. Rocket
**Detection Pattern**: `#[get("/path")]` macros
**Features**:
- Route macros with all HTTP methods
- Path parameter conversion: `<id>` → `{id}`
- Data parameter support

**Example**:
```rust
#[get("/users")]
fn list_users() -> Json<Vec<User>> { }

#[post("/users", data = "<user>")]
fn create_user(user: Json<UserDTO>) -> Json<User> { }

#[get("/users/<id>")]
fn get_user(id: i32) -> Json<User> { }
```

### 3. Axum
**Detection Pattern**: `.route("path", method(handler))` calls
**Features**:
- Router-based route registration
- State extraction detection
- Path parameter conversion: `:id` → `{id}`

**Example**:
```rust
pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/users", axum::routing::get(list_users))
        .route("/users/:id", axum::routing::get(get_user))
        .with_state(state)
}

async fn list_users(State(db): State<Database>) -> Json<Vec<User>> { }
```

### 4. Warp
**Detection Pattern**: `warp::path("path").and(warp::method())` filter chains
**Features**:
- Filter-based routing
- Complex filter chains
- Handler detection via `.and_then(handler)`

**Example**:
```rust
fn list_users() -> impl Filter<Extract = impl warp::Reply> {
    warp::path("users")
        .and(warp::get())
        .and_then(handlers::list_users)
}

fn get_user() -> impl Filter<Extract = impl warp::Reply> {
    warp::path("users")
        .and(warp::path::param::<i32>())
        .and(warp::get())
        .and_then(handlers::get_user)
}
```

### 5. Tide
**Detection Pattern**: `app.at("path").method(handler)` calls
**Features**:
- Server-based route registration
- Path parameter conversion: `:id` → `{id}`

**Example**:
```rust
pub async fn routes(app: &mut tide::Server<State>) {
    app.at("/users").get(list_users);
    app.at("/users/:id").get(get_user);
}
```

## Framework Detection

The parser automatically detects which frameworks are being used by analyzing import statements:

- **Actix-web**: `use actix_web::`
- **Rocket**: `use rocket::` or `use rocket::*`
- **Axum**: `use axum::`
- **Warp**: `use warp::`
- **Tide**: `use tide::`

## Metadata

Each detected endpoint includes framework-specific metadata:

```json
{
  "method": "GET",
  "path": "/users",
  "handler": "list_users",
  "framework": "actix",
  "has_guard": true,      // Actix guards
  "has_state": true,      // Axum state
  "scoped": true          // Nested scopes
}
```

## Limitations

- Complex nested routing structures may not be fully parsed
- Custom middleware and filters are not analyzed
- Authentication/authorization logic is not extracted
- Only explicit route definitions are detected (no dynamic routing)

## Testing

Comprehensive tests cover all 6 frameworks with various routing patterns. Run tests with:

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py -v
```</content>
</xai:function_call">The file has been created successfully.