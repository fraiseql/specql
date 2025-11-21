# tests/unit/cli/test_registry_integration.py

from pathlib import Path

from cli.orchestrator import CLIOrchestrator
from core.ast_models import Entity


def test_orchestrator_uses_registry_table_codes():
    """Orchestrator should derive table codes from registry"""
    orchestrator = CLIOrchestrator(use_registry=True)

    # Create test entity
    entity = Entity(name="Contact", schema="crm", fields={})

    # Generate should use registry to get table code
    table_code = orchestrator.get_table_code(entity)

    # Should be hexadecimal, 6 chars
    assert len(table_code) == 6
    assert all(c in "0123456789ABCDEF" for c in table_code.upper())


def test_orchestrator_generates_hierarchical_paths():
    """Orchestrator should generate hierarchical file paths"""
    orchestrator = CLIOrchestrator(use_registry=True)

    entity = Entity(name="Contact", schema="crm", fields={})
    table_code = "012311"

    # Should generate multi-level path
    file_path = orchestrator.generate_file_path(entity, table_code)

    # Should have hierarchy: layer/domain/subdomain/group/file
    parts = Path(file_path).parts
    assert len(parts) >= 5
    assert "01_write_side" in parts
    assert any("012_crm" in p for p in parts)


def test_orchestrator_creates_directories(sample_entity_file):
    """Orchestrator should create all required directories"""
    orchestrator = CLIOrchestrator(use_registry=False, output_format="confiture")

    # Generate from entity file - should create directory structure
    # Note: This creates db/schema/ in the current working directory
    result = orchestrator.generate_from_files(
        entity_files=[str(sample_entity_file)], output_dir="migrations"
    )

    # Verify no errors
    assert result.errors == [], f"Generation errors: {result.errors}"

    # Verify Confiture directory structure was created in current directory
    db_schema = Path("db/schema")

    # Check that all required directories exist
    assert (db_schema / "00_foundation").exists(), "00_foundation directory not created"
    assert (db_schema / "10_tables").exists(), "10_tables directory not created"
    assert (db_schema / "20_helpers").exists(), "20_helpers directory not created"
    assert (db_schema / "30_functions").exists(), "30_functions directory not created"

    # Verify files were created in the correct directories
    assert (db_schema / "00_foundation" / "000_app_foundation.sql").exists()

    # Check for entity-specific files
    contact_files = list((db_schema / "10_tables").glob("contact.sql"))
    assert len(contact_files) > 0, "Contact table file not created"
