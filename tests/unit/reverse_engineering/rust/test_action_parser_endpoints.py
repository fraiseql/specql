"""
Unit tests for RustActionParser endpoint extraction.

Tests the extract_endpoints and extract_actions methods.
"""



import os
import tempfile
from pathlib import Path

from src.reverse_engineering.rust_action_parser import RustActionParser


class TestRustActionParserEndpoints:
    """Test RustActionParser endpoint extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustActionParser()

    def test_extract_endpoints_from_actix_routes(self):
        """Test extracting endpoints from Actix routes."""
        rust_code = """
use actix_web::{get, post, HttpResponse};

#[get("/api/users")]
pub async fn list_users() -> HttpResponse {
    HttpResponse::Ok().finish()
}

#[post("/api/users")]
pub async fn create_user() -> HttpResponse {
    HttpResponse::Created().finish()
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 2

            # Check GET endpoint
            get_endpoint = next(e for e in endpoints if e["method"] == "GET")
            assert get_endpoint["path"] == "/api/users"
            assert get_endpoint["handler"] == "list_users"
            assert get_endpoint["is_async"] is True

            # Check POST endpoint
            post_endpoint = next(e for e in endpoints if e["method"] == "POST")
            assert post_endpoint["path"] == "/api/users"
            assert post_endpoint["handler"] == "create_user"
            assert post_endpoint["is_async"] is True

        finally:
            os.unlink(temp_path)

    def test_extract_endpoints_with_path_parameters(self):
        """Test extracting endpoints with path parameters."""
        rust_code = """
use actix_web::{get, put, delete, web, HttpResponse};

#[get("/api/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> HttpResponse {
    HttpResponse::Ok().finish()
}

#[put("/api/users/{id}")]
pub async fn update_user(path: web::Path<i32>) -> HttpResponse {
    HttpResponse::Ok().finish()
}

#[delete("/api/users/{id}")]
pub async fn delete_user(path: web::Path<i32>) -> HttpResponse {
    HttpResponse::NoContent().finish()
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 3

            # Check all have path parameters
            for endpoint in endpoints:
                assert "{id}" in endpoint["path"]
                assert len(endpoint["parameters"]) == 1
                assert endpoint["parameters"][0]["name"] == "path"

        finally:
            os.unlink(temp_path)

    def test_extract_endpoints_empty_file(self):
        """Test extracting endpoints from file with no routes."""
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))
            assert len(endpoints) == 0

        finally:
            os.unlink(temp_path)

    def test_extract_actions_from_impl_blocks(self):
        """Test extracting actions from impl blocks."""
        rust_code = """
pub struct User {
    pub id: i32,
    pub name: String,
}

impl User {
    pub fn new(id: i32, name: String) -> Self {
        Self { id, name }
    }

    pub fn get_user(id: i32) -> Option<Self> {
        None
    }

    pub fn update_user(&mut self, name: String) {
        self.name = name;
    }

    fn private_method(&self) {
        // This should not be extracted
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            actions = self.parser.extract_actions(Path(temp_path))

            # Should extract 3 public methods (new, get_user, update_user)
            assert len(actions) == 3

            action_names = [a["name"] for a in actions]
            assert "new" in action_names
            assert "get_user" in action_names
            assert "update_user" in action_names
            assert "private_method" not in action_names

        finally:
            os.unlink(temp_path)

    def test_extract_actions_with_routes_and_impl(self):
        """Test extracting actions from file with both routes and impl blocks."""
        rust_code = """
use actix_web::{get, HttpResponse};

pub struct User {
    pub id: i32,
}

impl User {
    pub fn create_user() -> Self {
        Self { id: 0 }
    }
}

#[get("/api/users")]
pub async fn list_users() -> HttpResponse {
    HttpResponse::Ok().finish()
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            actions = self.parser.extract_actions(Path(temp_path))

            # Should extract 1 impl method + 1 route handler = 2 actions
            assert len(actions) == 2

            action_names = [a["name"] for a in actions]
            assert "create_user" in action_names
            assert "list_users" in action_names

        finally:
            os.unlink(temp_path)

    def test_extract_endpoints_filters_none_results(self):
        """Test that None results are filtered from endpoints."""
        rust_code = """
use actix_web::{get, HttpResponse};

// Valid route
#[get("/api/valid")]
pub async fn valid_route() -> HttpResponse {
    HttpResponse::Ok().finish()
}

// Function without route macro (should not create endpoint)
pub async fn not_a_route() -> HttpResponse {
    HttpResponse::Ok().finish()
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            # Should only extract the route with macro
            assert len(endpoints) == 1
            assert endpoints[0]["handler"] == "valid_route"

        finally:
            os.unlink(temp_path)

    def test_extract_actions_mixed_visibility(self):
        """Test that only public methods are extracted as actions."""
        rust_code = """
pub struct Service {
    data: String,
}

impl Service {
    pub fn create_record() -> Self {
        Self { data: String::new() }
    }

    pub(crate) fn internal_create() -> Self {
        Self { data: String::new() }
    }

    fn private_helper() {
        // Private
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            actions = self.parser.extract_actions(Path(temp_path))

            # Should only extract the pub method, not pub(crate) or private
            assert len(actions) == 1
            assert actions[0]["name"] == "create_record"

        finally:
            os.unlink(temp_path)

    def test_actix_route_with_guard(self):
        """Test Actix-web route with guard function"""
        rust_code = """
use actix_web::{web, guard, HttpResponse};

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/contacts")
            .guard(guard::Header("content-type", "application/json"))
            .route(web::post().to(create_contact))
    );
}

async fn create_contact(contact: web::Json<ContactDTO>) -> HttpResponse {
    HttpResponse::Ok().finish()
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 1
            assert endpoints[0]["path"] == "/contacts"
            assert endpoints[0]["method"] == "POST"
            assert endpoints[0]["handler"] == "create_contact"
            assert endpoints[0]["metadata"]["has_guard"]

        finally:
            os.unlink(temp_path)

    def test_actix_nested_scope(self):
        """Test Actix-web nested scopes"""
        rust_code = """
use actix_web::{web, HttpResponse};

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .service(
                web::scope("/v1")
                    .route("/contacts", web::post().to(create_contact))
                    .route("/contacts/{id}", web::get().to(get_contact))
            )
    );
}

async fn create_contact() -> HttpResponse {
    HttpResponse::Ok().finish()
}

async fn get_contact() -> HttpResponse {
    HttpResponse::Ok().finish()
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 2
            # Sort by path for consistent ordering
            endpoints.sort(key=lambda x: x["path"])

            assert endpoints[0]["path"] == "/api/v1/contacts"
            assert endpoints[0]["method"] == "POST"
            assert endpoints[0]["handler"] == "create_contact"

            assert endpoints[1]["path"] == "/api/v1/contacts/{id}"
            assert endpoints[1]["method"] == "GET"
            assert endpoints[1]["handler"] == "get_contact"

        finally:
            os.unlink(temp_path)

    def test_rocket_multiple_methods(self):
        """Test Rocket #[get], #[post], #[put], #[delete] macros"""
        rust_code = """
use rocket::*;

#[get("/contacts")]
fn list_contacts() -> Json<Vec<Contact>> { }

#[post("/contacts", data = "<contact>")]
fn create_contact(contact: Json<ContactDTO>) -> Json<Contact> { }

#[put("/contacts/<id>", data = "<contact>")]
fn update_contact(id: i32, contact: Json<ContactDTO>) -> Json<Contact> { }

#[delete("/contacts/<id>")]
fn delete_contact(id: i32) -> Status { }
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 4
            assert endpoints[0]["method"] == "GET"
            assert endpoints[0]["path"] == "/contacts"
            assert endpoints[0]["handler"] == "list_contacts"

            assert endpoints[1]["method"] == "POST"
            assert endpoints[1]["path"] == "/contacts"
            assert endpoints[1]["handler"] == "create_contact"

            assert endpoints[2]["method"] == "PUT"
            assert endpoints[2]["path"] == "/contacts/{id}"
            assert endpoints[2]["handler"] == "update_contact"

            assert endpoints[3]["method"] == "DELETE"
            assert endpoints[3]["path"] == "/contacts/{id}"
            assert endpoints[3]["handler"] == "delete_contact"

        finally:
            os.unlink(temp_path)

    def test_axum_handler_with_state(self):
        """Test Axum handlers with state extraction"""
        rust_code = """
use axum::{Router, extract::{State, Path}};

pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/contacts", axum::routing::post(create_contact))
        .route("/contacts/:id", axum::routing::get(get_contact))
        .with_state(state)
}

async fn create_contact(
    State(db): State<Database>,
    axum::Json(payload): axum::Json<ContactDTO>
) -> axum::Json<Contact> { }

async fn get_contact(
    State(db): State<Database>,
    Path(id): Path<i32>
) -> axum::Json<Contact> { }
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 2
            assert endpoints[0]["method"] == "POST"
            assert endpoints[0]["path"] == "/contacts"
            assert endpoints[0]["handler"] == "create_contact"
            assert endpoints[0]["metadata"]["has_state"]
            assert endpoints[0]["metadata"]["framework"] == "axum"

            assert endpoints[1]["method"] == "GET"
            assert endpoints[1]["path"] == "/contacts/{id}"
            assert endpoints[1]["handler"] == "get_contact"
            assert endpoints[1]["metadata"]["has_state"]

        finally:
            os.unlink(temp_path)

    def test_warp_filter_chain(self):
        """Test Warp filter chain detection"""
        rust_code = """
use warp::Filter;

pub fn routes() -> impl Filter<Extract = impl warp::Reply> {
    create_contact()
        .or(get_contact())
        .or(list_contacts())
}

fn create_contact() -> impl Filter<Extract = impl warp::Reply> {
    warp::path("contacts")
        .and(warp::post())
        .and(warp::body::json())
        .and_then(handlers::create_contact)
}

fn get_contact() -> impl Filter<Extract = impl warp::Reply> {
    warp::path("contacts")
        .and(warp::path::param::<i32>())
        .and(warp::get())
        .and_then(handlers::get_contact)
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            # Check that we found endpoints with warp framework
            warp_endpoints = [e for e in endpoints if e["metadata"].get("framework") == "warp"]
            assert len(warp_endpoints) >= 1

            # At minimum, we should detect the create_contact endpoint
            create_endpoint = next(
                (e for e in warp_endpoints if "create_contact" in e["handler"]), None
            )
            assert create_endpoint is not None
            assert create_endpoint["method"] == "POST"
            assert create_endpoint["path"] == "/contacts"

        finally:
            os.unlink(temp_path)

    def test_tide_endpoint(self):
        """Test Tide endpoint detection"""
        rust_code = """
use tide::{Request, Response};

pub async fn routes(app: &mut tide::Server<State>) {
    app.at("/contacts").post(create_contact);
    app.at("/contacts/:id").get(get_contact);
}

async fn create_contact(mut req: Request<State>) -> tide::Result<Response> {
    Ok(Response::new(201))
}

async fn get_contact(req: Request<State>) -> tide::Result<Response> {
    Ok(Response::new(200))
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            endpoints = self.parser.extract_endpoints(Path(temp_path))

            assert len(endpoints) == 2
            # Sort by path for consistent ordering
            endpoints.sort(key=lambda x: x["path"])

            assert endpoints[0]["method"] == "POST"
            assert endpoints[0]["path"] == "/contacts"
            assert endpoints[0]["handler"] == "create_contact"
            assert endpoints[0]["metadata"]["framework"] == "tide"

            assert endpoints[1]["method"] == "GET"
            assert endpoints[1]["path"] == "/contacts/{id}"
            assert endpoints[1]["handler"] == "get_contact"

        finally:
            os.unlink(temp_path)
