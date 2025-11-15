"""
End-to-end integration tests for Rust code generation
"""

import pytest
from click.testing import CliRunner
from src.cli.confiture_extensions import specql


class TestEndToEndRustGeneration:
    """Test complete SpecQL → Rust generation pipeline"""

    @pytest.fixture
    def sample_entity_file(self, tmp_path):
        """Create a sample SpecQL entity file"""
        entity_content = """
entity: Contact
schema: crm
description: "A contact in the CRM system"

fields:
  email:
    type: text
    required: true
    description: "Email address"

  phone:
    type: text
    required: false
    description: "Phone number"

  active:
    type: boolean
    required: true
    description: "Whether contact is active"
"""
        entity_file = tmp_path / "contact.yaml"
        entity_file.write_text(entity_content)
        return entity_file

    def test_cli_generate_rust_basic(self, tmp_path, sample_entity_file):
        """Test CLI generates basic Rust code"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Rust backend generated" in result.output

        # Check basic file structure
        assert output_dir.exists()
        assert (output_dir / "Cargo.toml").exists()
        assert (output_dir / "src").exists()
        assert (output_dir / "src" / "schema.rs").exists()
        assert (output_dir / "src" / "models.rs").exists()
        assert (output_dir / "src" / "queries.rs").exists()

    def test_cli_generate_rust_with_handlers(self, tmp_path, sample_entity_file):
        """Test CLI generates Rust code with handlers"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
                "--with-handlers",
                "--with-routes",
            ],
        )

        assert result.exit_code == 0

        # Check handler files
        handlers_dir = output_dir / "src" / "handlers"
        assert handlers_dir.exists()
        assert (handlers_dir / "contact.rs").exists()

        # Check routes file
        assert (output_dir / "src" / "routes.rs").exists()

    def test_generated_schema_compiles(self, tmp_path, sample_entity_file):
        """Test generated schema.rs is valid Rust"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Check that schema.rs contains expected content
        schema_file = output_dir / "src" / "schema.rs"
        schema_content = schema_file.read_text()

        assert "diesel::table!" in schema_content
        assert "crm.tb_contact" in schema_content
        assert "pk_contact -> Int4" in schema_content
        assert "email -> Varchar" in schema_content

    def test_generated_models_compile(self, tmp_path, sample_entity_file):
        """Test generated models.rs is valid Rust"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Check that models.rs contains expected content
        models_file = output_dir / "src" / "models.rs"
        models_content = models_file.read_text()

        assert "#[derive(Debug, Clone, Queryable, Selectable)]" in models_content
        assert "pub struct Contact" in models_content
        assert "pub pk_contact: i32" in models_content
        assert "pub email: String" in models_content

    def test_generated_queries_compile(self, tmp_path, sample_entity_file):
        """Test generated queries.rs is valid Rust"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Check that queries.rs contains expected content
        queries_file = output_dir / "src" / "queries.rs"
        queries_content = queries_file.read_text()

        assert "pub struct ContactQueries" in queries_content
        assert "pub fn find_by_id" in queries_content
        assert "pub fn create" in queries_content

    def test_generated_handlers_compile(self, tmp_path, sample_entity_file):
        """Test generated handlers are valid Rust"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code with handlers
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
                "--with-handlers",
            ],
        )

        assert result.exit_code == 0

        # Check that handlers/contact.rs contains expected content
        handler_file = output_dir / "src" / "handlers" / "contact.rs"
        handler_content = handler_file.read_text()

        assert "pub async fn get_contact" in handler_content
        assert "web::Data<DbPool>" in handler_content
        assert "HttpResponse::Ok().json(contact)" in handler_content

    def test_cargo_toml_dependencies(self, tmp_path, sample_entity_file):
        """Test Cargo.toml contains all required dependencies"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Check Cargo.toml
        cargo_file = output_dir / "Cargo.toml"
        cargo_content = cargo_file.read_text()

        required_deps = [
            "actix-web",
            "diesel",
            "bigdecimal",
            "chrono",
            "uuid",
            "serde",
            "serde_json",
            "r2d2",
            "dotenvy",
        ]

        for dep in required_deps:
            assert dep in cargo_content

    def test_main_rs_structure(self, tmp_path, sample_entity_file):
        """Test main.rs has proper application structure"""
        runner = CliRunner()

        output_dir = tmp_path / "rust_output"

        # Generate the code
        result = runner.invoke(
            specql,
            [
                "generate",
                str(sample_entity_file),
                "--target",
                "rust",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0

        # Check main.rs
        main_file = output_dir / "src" / "main.rs"
        main_content = main_file.read_text()

        assert "HttpServer::new" in main_content
        assert "DATABASE_URL" in main_content
        assert "configure_all_routes" in main_content
        assert "127.0.0.1:8080" in main_content
