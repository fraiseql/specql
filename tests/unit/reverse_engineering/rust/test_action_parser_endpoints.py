"""
Unit tests for RustActionParser endpoint extraction.

Tests the extract_endpoints and extract_actions methods.
"""

import pytest
import tempfile
import os
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
