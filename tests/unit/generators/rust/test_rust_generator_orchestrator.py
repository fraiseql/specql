"""
Tests for Rust Generator Orchestrator
"""

import pytest
from pathlib import Path
from src.generators.rust.rust_generator_orchestrator import RustGeneratorOrchestrator
from src.core.ast_models import Entity, FieldDefinition


class TestRustGeneratorOrchestrator:
    """Test the complete Rust generation pipeline"""

    @pytest.fixture
    def orchestrator(self):
        return RustGeneratorOrchestrator()

    @pytest.fixture
    def sample_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "phone": FieldDefinition(name="phone", type_name="text", nullable=True),
            },
        )

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initializes with all generators"""
        assert orchestrator.table_generator is not None
        assert orchestrator.model_generator is not None
        assert orchestrator.query_generator is not None
        assert orchestrator.handler_generator is not None

    def test_generate_creates_output_directory(
        self, orchestrator, tmp_path, sample_entity
    ):
        """Test generate creates output directory structure"""
        # Mock the _parse_entities method to return our sample entity
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]  # Won't be used due to mock

        orchestrator.generate(entity_files, output_dir)

        # Check directory structure
        assert output_dir.exists()
        assert (output_dir / "src").exists()
        assert (output_dir / "Cargo.toml").exists()
        assert (output_dir / "src" / "main.rs").exists()
        assert (output_dir / "src" / "lib.rs").exists()

    def test_generate_creates_core_files(self, orchestrator, tmp_path, sample_entity):
        """Test generate creates core Rust files"""
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]

        orchestrator.generate(entity_files, output_dir)

        src_dir = output_dir / "src"

        # Core files
        assert (src_dir / "schema.rs").exists()
        assert (src_dir / "models.rs").exists()
        assert (src_dir / "queries.rs").exists()

    def test_generate_with_handlers(self, orchestrator, tmp_path, sample_entity):
        """Test generate creates handler files when requested"""
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]

        orchestrator.generate(entity_files, output_dir, with_handlers=True)

        handlers_dir = output_dir / "src" / "handlers"
        assert handlers_dir.exists()
        assert (handlers_dir / "contact.rs").exists()

    def test_generate_with_routes(self, orchestrator, tmp_path, sample_entity):
        """Test generate creates routes file when requested"""
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]

        orchestrator.generate(entity_files, output_dir, with_routes=True)

        src_dir = output_dir / "src"
        assert (src_dir / "routes.rs").exists()

    def test_cargo_toml_content(self, orchestrator, tmp_path, sample_entity):
        """Test Cargo.toml contains required dependencies"""
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]

        orchestrator.generate(entity_files, output_dir)

        cargo_file = output_dir / "Cargo.toml"
        cargo_content = cargo_file.read_text()

        # Check for key dependencies
        assert "actix-web" in cargo_content
        assert "diesel" in cargo_content
        assert "bigdecimal" in cargo_content
        assert "chrono" in cargo_content
        assert "uuid" in cargo_content

    def test_main_rs_content(self, orchestrator, tmp_path, sample_entity):
        """Test main.rs contains proper application setup"""
        orchestrator._parse_entities = lambda files: [sample_entity]

        output_dir = tmp_path / "rust_output"
        entity_files = [Path("dummy.yaml")]

        orchestrator.generate(entity_files, output_dir)

        main_file = output_dir / "src" / "main.rs"
        main_content = main_file.read_text()

        # Check for key components
        assert "HttpServer::new" in main_content
        assert "DATABASE_URL" in main_content
        assert "configure_all_routes" in main_content
