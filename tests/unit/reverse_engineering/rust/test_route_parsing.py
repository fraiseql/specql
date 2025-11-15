"""
Tests for route handler parsing in Rust files.
"""

from src.reverse_engineering.rust_parser import RustParser


class TestRouteHandlerParsing:
    """Test parsing of Actix web route handlers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()

    def test_simple_get_route(self):
        """Test parsing a simple GET route."""
        rust_code = """
use actix_web::{get, web, HttpResponse, Result};

#[get("/users")]
async fn get_users() -> Result<HttpResponse> {
    // Handler logic
    Ok(HttpResponse::Ok().json("users"))
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/users"
        assert route.function_name == "get_users"
        assert route.is_async  is True
        assert route.return_type == "Result<HttpResponse>"

    def test_multiple_routes(self):
        """Test parsing multiple routes in one file."""
        rust_code = """
use actix_web::{get, post, put, delete, web, HttpResponse, Result};

#[get("/users")]
async fn get_users() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json("users"))
}

#[post("/users")]
async fn create_user() -> Result<HttpResponse> {
    Ok(HttpResponse::Created().json("user created"))
}

#[put("/users/{id}")]
async fn update_user() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json("user updated"))
}

#[delete("/users/{id}")]
async fn delete_user() -> Result<HttpResponse> {
    Ok(HttpResponse::NoContent().finish())
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 4

        # Check each route
        routes_by_method = {r.method: r for r in routes}

        assert "GET" in routes_by_method
        assert routes_by_method["GET"].path == "/users"
        assert routes_by_method["GET"].function_name == "get_users"

        assert "POST" in routes_by_method
        assert routes_by_method["POST"].path == "/users"
        assert routes_by_method["POST"].function_name == "create_user"

        assert "PUT" in routes_by_method
        assert routes_by_method["PUT"].path == "/users/{id}"
        assert routes_by_method["PUT"].function_name == "update_user"

        assert "DELETE" in routes_by_method
        assert routes_by_method["DELETE"].path == "/users/{id}"
        assert routes_by_method["DELETE"].function_name == "delete_user"

    def test_route_with_parameters(self):
        """Test parsing routes with parameters."""
        rust_code = """
use actix_web::{get, web, HttpResponse, Result};
use serde::Deserialize;

#[derive(Deserialize)]
struct UserQuery {
    limit: Option<i32>,
    offset: Option<i32>,
}

#[get("/users")]
async fn get_users(query: web::Query<UserQuery>) -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json("users"))
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/users"
        assert route.function_name == "get_users"
        assert len(route.parameters) == 1
        assert route.parameters[0]["name"] == "query"
        assert route.parameters[0]["param_type"] == "web::Query<UserQuery>"

    def test_sync_route(self):
        """Test parsing synchronous routes."""
        rust_code = """
use actix_web::{get, HttpResponse};

#[get("/health")]
fn health_check() -> HttpResponse {
    HttpResponse::Ok().json("healthy")
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/health"
        assert route.function_name == "health_check"
        assert not route.is_async
        assert route.return_type == "HttpResponse"

    def test_different_http_methods(self):
        """Test parsing different HTTP methods."""
        rust_code = """
use actix_web::{get, post, put, delete, patch, head, options, HttpResponse, Result};

#[get("/test")] async fn test_get() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[post("/test")] async fn test_post() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[put("/test")] async fn test_put() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[delete("/test")] async fn test_delete() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[patch("/test")] async fn test_patch() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[head("/test")] async fn test_head() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
#[options("/test")] async fn test_options() -> Result<HttpResponse> { Ok(HttpResponse::Ok().finish()) }
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 7

        methods = [r.method for r in routes]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods
        assert "PATCH" in methods
        assert "HEAD" in methods
        assert "OPTIONS" in methods

    def test_no_routes(self):
        """Test files without route handlers."""
        rust_code = """
pub struct User {
    pub id: i32,
    pub name: String,
}

impl User {
    pub fn new(id: i32, name: String) -> Self {
        Self { id, name }
    }
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 0
        assert len(structs) == 1
        assert len(impl_blocks) == 1

    def test_complex_route_path(self):
        """Test parsing complex route paths."""
        rust_code = """
use actix_web::{get, HttpResponse, Result};

#[get("/api/v1/users/{user_id}/posts/{post_id}/comments")]
async fn get_user_post_comments() -> Result<HttpResponse> {
    Ok(HttpResponse::Ok().json("comments"))
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 1
        route = routes[0]
        assert route.method == "GET"
        assert route.path == "/api/v1/users/{user_id}/posts/{post_id}/comments"
        assert route.function_name == "get_user_post_comments"

    def test_axum_route_macros(self):
        """Test parsing Axum route macros."""
        rust_code = """
use axum::{routing::get, Router};

async fn handler() -> &'static str {
    "Hello, World!"
}

#[route(GET, "/")]
async fn root() -> &'static str {
    "Hello, World!"
}

#[route(POST, "/users", create_user)]
async fn create_user_handler() -> &'static str {
    "User created"
}

#[get("/health")]
async fn health_check() -> &'static str {
    "OK"
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 3

        # Sort routes by path for consistent testing
        routes_by_path = {r.path: r for r in routes}

        # Test #[route(GET, "/")] -> root function
        root_route = routes_by_path["/"]
        assert root_route.method == "GET"
        assert root_route.function_name == "root"

        # Test #[route(POST, "/users", create_user)] -> create_user_handler function
        users_route = routes_by_path["/users"]
        assert users_route.method == "POST"
        assert users_route.function_name == "create_user_handler"

        # Test #[get("/health")] -> health_check function
        health_route = routes_by_path["/health"]
        assert health_route.method == "GET"
        assert health_route.function_name == "health_check"

    def test_axum_route_with_different_methods(self):
        """Test parsing Axum routes with different HTTP methods."""
        rust_code = """
use axum::Router;

#[route(PUT, "/users/{id}")]
async fn update_user() -> &'static str {
    "User updated"
}

#[route(DELETE, "/users/{id}")]
async fn delete_user() -> &'static str {
    "User deleted"
}

#[route(PATCH, "/users/{id}")]
async fn patch_user() -> &'static str {
    "User patched"
}
"""
        structs, enums, tables, derives, impl_blocks, routes = self.parser.parse_source(
            rust_code
        )

        assert len(routes) == 3

        routes_by_method = {r.method: r for r in routes}

        assert "PUT" in routes_by_method
        assert routes_by_method["PUT"].path == "/users/{id}"
        assert routes_by_method["PUT"].function_name == "update_user"

        assert "DELETE" in routes_by_method
        assert routes_by_method["DELETE"].path == "/users/{id}"
        assert routes_by_method["DELETE"].function_name == "delete_user"

        assert "PATCH" in routes_by_method
        assert routes_by_method["PATCH"].path == "/users/{id}"
        assert routes_by_method["PATCH"].function_name == "patch_user"
