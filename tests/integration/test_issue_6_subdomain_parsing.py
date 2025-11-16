"""
Integration tests for Issue #6: Subdomain parsing fix

Issue #6: Hierarchical generator incorrectly parses table_code subdomain as 2 digits instead of 1 digit.

PROBLEM:
- Table codes like "013111" should parse subdomain as "1" (position 3)
- But code was parsing as "11" (positions 3-4)
- This created wrong directories: "01311_subdomain_11" instead of "0131_classification"

SOLUTION:
- Fixed TableCodeComponents to use single-digit subdomain_code field
- Updated generate_file_path() and register_entity_auto() to use correct parsing
- Added validation and backward compatibility

TESTS:
These tests verify the fix works end-to-end with real entity generation scenarios
matching the Production migration use case with 74+ entities.
"""

from src.cli.orchestrator import CLIOrchestrator


def create_test_entity_yaml(tmp_path, name, table_code, description, schema="catalog"):
    """Helper to create a test entity YAML file"""
    yaml_file = tmp_path / f"{name.lower()}.yaml"
    yaml_file.write_text(f"""
entity: {name}
schema: {schema}
organization:
  table_code: "{table_code}"
description: {description}

fields:
  name: text
  code: text
""")
    return str(yaml_file)


class TestIssue6SubdomainParsing:
    """Test fix for Issue #6: Hierarchical generator subdomain parsing"""

    def test_classification_subdomain_entities_share_directory(self, tmp_path):
        """
        Test that entities in same subdomain share directory

        Reproduces Production scenario:
        - ColorMode (013111), DuplexMode (013121), MachineFunction (013131)
        - All have subdomain code "1" (classification)
        - Should all be in directory: 0131_classification/
        """

        # Create test YAML files for classification entities
        entities = [
            ("ColorMode", "013111", "Color mode options (BW, color, grayscale)"),
            ("DuplexMode", "013121", "Duplex printing modes"),
            ("MachineFunction", "013131", "Machine function categories"),
        ]

        yaml_files = []
        for name, table_code, desc in entities:
            yaml_files.append(create_test_entity_yaml(tmp_path, name, table_code, desc))

        # Generate with hierarchical output
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        # Verify no errors
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        # Check directory structure
        # Should have: 01_write_side/013_catalog/0131_classification/
        classification_dir = (
            output_dir / "01_write_side" / "013_catalog" / "0131_classification"
        )
        assert classification_dir.exists(), (
            "Classification subdomain directory not found"
        )

        # All three entity directories should be under classification (snake_case, no _group)
        entity_dirs = list(classification_dir.glob("*"))
        assert len(entity_dirs) == 3, (
            f"Expected 3 entity dirs, found {len(entity_dirs)}"
        )

        # Verify snake_case names (no _group)
        dir_names = [d.name for d in entity_dirs]
        assert any("color_mode" in d for d in dir_names), (
            f"color_mode not found in {dir_names}"
        )
        assert any("duplex_mode" in d for d in dir_names), (
            f"duplex_mode not found in {dir_names}"
        )
        assert any("machine_function" in d for d in dir_names), (
            f"machine_function not found in {dir_names}"
        )

        # Verify NO _group suffix
        assert not any("_group" in d for d in dir_names), f"Found _group in {dir_names}"

        # Verify NO lowercase-only (non-snake_case)
        assert not any(d == "01311_colormode" for d in dir_names), (
            "Found non-snake_case colormode"
        )

        # Verify NO wrong directories exist
        wrong_dirs = list(output_dir.rglob("*subdomain_11*"))
        assert len(wrong_dirs) == 0, f"Found wrong subdomain_11 directory: {wrong_dirs}"

    def test_manufacturer_subdomain_entities_share_directory(self, tmp_path):
        """
        Test manufacturer subdomain (code 2)

        Entities: Manufacturer (013211), Model (013231), Accessory (013242)
        All should be in: 0132_manufacturer/
        """

        entities = [
            ("Manufacturer", "013211", "Printer/copier manufacturers"),
            ("Model", "013231", "Manufacturer product models"),
            ("Accessory", "013242", "Machine accessories and add-ons"),
        ]

        yaml_files = []
        for name, table_code, desc in entities:
            yaml_files.append(create_test_entity_yaml(tmp_path, name, table_code, desc))

        # Generate with hierarchical output
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        # Verify no errors
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        # Check manufacturer subdomain directory
        manufacturer_dir = (
            output_dir / "01_write_side" / "013_catalog" / "0132_manufacturer"
        )
        assert manufacturer_dir.exists(), "Manufacturer subdomain directory not found"

        # All three entity directories should be under manufacturer (snake_case, no _group)
        entity_dirs = list(manufacturer_dir.glob("*"))
        assert len(entity_dirs) == 3, (
            f"Expected 3 entity dirs, found {len(entity_dirs)}"
        )

        # Verify snake_case names
        dir_names = [d.name for d in entity_dirs]
        assert any("manufacturer" in d for d in dir_names), (
            f"manufacturer not found in {dir_names}"
        )
        assert any("model" in d for d in dir_names), f"model not found in {dir_names}"
        assert any("accessory" in d for d in dir_names), (
            f"accessory not found in {dir_names}"
        )

        # Verify NO _group suffix
        assert not any("_group" in d for d in dir_names), f"Found _group in {dir_names}"

        # Verify NO wrong directories
        wrong_dirs = list(output_dir.rglob("*subdomain_21*"))
        assert len(wrong_dirs) == 0, "Found wrong subdomain_21 directory"
        wrong_dirs = list(output_dir.rglob("*subdomain_23*"))
        assert len(wrong_dirs) == 0, "Found wrong subdomain_23 directory"

    def test_cross_subdomain_separation(self, tmp_path):
        """
        Test that different subdomains create separate directories

        ColorMode (013111) → 0131_classification/
        Manufacturer (013211) → 0132_manufacturer/
        """

        entities = [
            ("ColorMode", "013111", "Color mode options"),
            ("Manufacturer", "013211", "Printer manufacturers"),
        ]

        yaml_files = []
        for name, table_code, desc in entities:
            yaml_files.append(create_test_entity_yaml(tmp_path, name, table_code, desc))

        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        assert len(result.errors) == 0

        # Both subdomain directories should exist
        catalog_dir = output_dir / "01_write_side" / "013_catalog"
        classification_dir = catalog_dir / "0131_classification"
        manufacturer_dir = catalog_dir / "0132_manufacturer"

        assert classification_dir.exists(), "Classification subdomain missing"
        assert manufacturer_dir.exists(), "Manufacturer subdomain missing"

        # ColorMode should be under classification (snake_case)
        color_mode_dirs = list(classification_dir.glob("*color_mode*"))
        assert len(color_mode_dirs) > 0, "ColorMode not in classification subdomain"

        # Manufacturer should be under manufacturer (snake_case)
        manufacturer_dirs = list(manufacturer_dir.glob("*manufacturer*"))
        assert len(manufacturer_dirs) > 0, "Manufacturer not in manufacturer subdomain"

    def test_file_names_use_snake_case(self, tmp_path):
        """Test that generated SQL files use snake_case"""

        yaml_file = tmp_path / "colormode.yaml"
        yaml_file.write_text("""
entity: ColorMode
schema: catalog
organization:
  table_code: "013111"

fields:
  name: text
""")

        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=[str(yaml_file)],
            output_dir=str(output_dir),
        )

        assert len(result.errors) == 0

        # Find SQL files
        sql_files = list(output_dir.rglob("*.sql"))

        if sql_files:
            # Should use snake_case
            filenames = [f.name for f in sql_files]
            assert any("color_mode" in f for f in filenames), (
                f"No snake_case in {filenames}"
            )
            assert not any("colormode.sql" in f for f in filenames), (
                f"Found non-snake_case in {filenames}"
            )
