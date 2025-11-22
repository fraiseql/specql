"""Tests for reverse rust CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_diesel_model():
    return """
use diesel::prelude::*;

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub company_id: Option<i32>,
    pub status: String,
    pub created_at: NaiveDateTime,
}
"""


@pytest.fixture
def sample_seaorm_model():
    return """
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
    pub company_id: Option<i32>,
    pub status: String,
}
"""


@pytest.fixture
def sample_actix_routes():
    return """
use actix_web::{get, post, web, HttpResponse};

#[get("/contacts")]
pub async fn get_contacts() -> HttpResponse {
    HttpResponse::Ok().json(vec![])
}

#[post("/contacts")]
pub async fn create_contact(body: web::Json<ContactInput>) -> HttpResponse {
    HttpResponse::Created().json(body.into_inner())
}

#[get("/contacts/{id}")]
pub async fn get_contact(path: web::Path<i32>) -> HttpResponse {
    HttpResponse::Ok().json(Contact::default())
}
"""


@pytest.fixture
def sample_axum_routes():
    return """
use axum::{routing::get, Router, extract::State, Json};

pub fn router() -> Router {
    Router::new()
        .route("/contacts", axum::routing::get(get_contacts))
        .route("/contacts/:id", axum::routing::get(get_contact))
        .route("/contacts", axum::routing::post(create_contact))
}
"""


@pytest.fixture
def sample_diesel_table_macro():
    return """
diesel::table! {
    contacts (id) {
        id -> Int4,
        email -> Varchar,
        company_id -> Nullable<Int4>,
        status -> Varchar,
        created_at -> Timestamp,
    }
}
"""


class TestReverseRustCommand:
    """Tests for the reverse rust CLI command."""

    def test_reverse_rust_requires_files(self, cli_runner):
        """reverse rust should require file arguments."""
        from cli.main import app

        result = cli_runner.invoke(app, ["reverse", "rust"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_reverse_rust_requires_output_dir(self, cli_runner):
        """reverse rust should require output directory."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("model.rs").write_text("pub struct Test { pub id: i32 }")
            result = cli_runner.invoke(app, ["reverse", "rust", "model.rs"])

            assert result.exit_code != 0

    def test_reverse_rust_parses_diesel_model(self, cli_runner, sample_diesel_model):
        """reverse rust should parse Diesel models."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("models.rs").write_text(sample_diesel_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "models.rs", "-o", "out/"])

            assert result.exit_code == 0

    def test_reverse_rust_parses_seaorm_model(self, cli_runner, sample_seaorm_model):
        """reverse rust should parse SeaORM models."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(sample_seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "entity.rs", "-o", "out/"])

            assert result.exit_code == 0
            # Should generate YAML file
            yaml_files = list(Path("out/").glob("*.yaml"))
            assert len(yaml_files) >= 1

    def test_reverse_rust_parses_actix_routes(self, cli_runner, sample_actix_routes):
        """reverse rust should parse Actix-web routes."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("routes.rs").write_text(sample_actix_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "routes.rs", "-o", "out/"])

            assert result.exit_code == 0

    def test_reverse_rust_preview_mode(self, cli_runner, sample_seaorm_model):
        """reverse rust --preview should not write files."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(sample_seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "rust", "entity.rs", "-o", "out/", "--preview"]
            )

            assert result.exit_code == 0
            yaml_files = list(Path("out/").glob("*.yaml"))
            assert len(yaml_files) == 0

    def test_reverse_rust_auto_detects_diesel(self, cli_runner, sample_diesel_model):
        """reverse rust should auto-detect Diesel ORM."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("models.rs").write_text(sample_diesel_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "models.rs", "-o", "out/"])

            assert result.exit_code == 0
            # Check that Diesel was detected (case-insensitive)
            assert "diesel" in result.output.lower()

    def test_reverse_rust_auto_detects_seaorm(self, cli_runner, sample_seaorm_model):
        """reverse rust should auto-detect SeaORM."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(sample_seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "entity.rs", "-o", "out/"])

            assert result.exit_code == 0
            assert "seaorm" in result.output.lower() or "sea" in result.output.lower()

    def test_reverse_rust_orm_option(self, cli_runner, sample_diesel_model):
        """reverse rust --framework should specify ORM type."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("models.rs").write_text(sample_diesel_model)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "rust", "models.rs", "-o", "out/", "--framework", "diesel"]
            )

            assert result.exit_code == 0

    def test_reverse_rust_multiple_files(
        self, cli_runner, sample_diesel_model, sample_seaorm_model
    ):
        """reverse rust should handle multiple files."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("contact.rs").write_text(sample_diesel_model)
            Path("task.rs").write_text(sample_seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "rust", "contact.rs", "task.rs", "-o", "out/"]
            )

            assert result.exit_code == 0

    def test_reverse_rust_creates_output_directory(self, cli_runner, sample_seaorm_model):
        """reverse rust should create output directory if it doesn't exist."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(sample_seaorm_model)
            # Don't create output directory

            result = cli_runner.invoke(app, ["reverse", "rust", "entity.rs", "-o", "new_output/"])

            assert result.exit_code == 0
            assert Path("new_output/").exists()


class TestReverseRustSeaORMIntegration:
    """Integration tests for SeaORM parsing."""

    def test_seaorm_model_fields_mapped_correctly(self, cli_runner):
        """SeaORM model fields should be mapped to SpecQL types."""
        import yaml as yaml_lib

        from cli.main import app

        seaorm_model = """
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
    pub age: Option<i32>,
    pub is_active: bool,
    pub created_at: DateTime,
}
"""
        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "entity.rs", "-o", "out/"])

            assert result.exit_code == 0
            yaml_files = list(Path("out/").glob("*.yaml"))
            assert len(yaml_files) >= 1

            # Parse the generated YAML
            content = yaml_files[0].read_text()
            parsed = yaml_lib.safe_load(content)

            assert "entity" in parsed
            assert "fields" in parsed

    def test_seaorm_generates_valid_yaml(self, cli_runner, sample_seaorm_model):
        """reverse rust should generate valid YAML files."""
        import yaml as yaml_lib

        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("entity.rs").write_text(sample_seaorm_model)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "entity.rs", "-o", "out/"])

            assert result.exit_code == 0
            yaml_files = list(Path("out/").glob("*.yaml"))

            for yaml_file in yaml_files:
                content = yaml_file.read_text()
                # Should be valid YAML
                parsed = yaml_lib.safe_load(content)
                assert parsed is not None


class TestReverseRustDieselIntegration:
    """Integration tests for Diesel parsing."""

    def test_diesel_table_macro_parsed(self, cli_runner, sample_diesel_table_macro):
        """Diesel table! macro should be parsed."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.rs").write_text(sample_diesel_table_macro)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "schema.rs", "-o", "out/"])

            assert result.exit_code == 0


class TestReverseRustRouteExtraction:
    """Tests for Rust route extraction."""

    def test_extract_actix_crud_routes(self, cli_runner, sample_actix_routes):
        """Should extract CRUD routes from Actix-web."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("routes.rs").write_text(sample_actix_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "routes.rs", "-o", "out/"])

            assert result.exit_code == 0
            # Routes should be mentioned in output
            assert "route" in result.output.lower() or "rust" in result.output.lower()

    def test_extract_axum_routes(self, cli_runner, sample_axum_routes):
        """Should extract routes from Axum router."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("routes.rs").write_text(sample_axum_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "rust", "routes.rs", "-o", "out/"])

            assert result.exit_code == 0
