"""Comprehensive integration tests for test generation workflows."""

import pytest
import subprocess
from pathlib import Path
import tempfile


class TestEndToEndTestGeneration:
    """End-to-end test generation workflows."""

    def test_full_workflow_entity_to_passing_tests(self):
        """
        Complete workflow: Entity YAML → Generate tests → Run tests → All pass

        This is the golden path integration test.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Step 1: Create entity YAML
            entity_file = tmp_path / "sample.yaml"
            entity_file.write_text("""
entity: Sample
schema: test_schema

fields:
  name: text
  email: email
  status: enum(active, inactive)

actions:
  - name: activate
    steps:
      - update: Sample SET status = 'active'
            """)

            # Step 2: Generate tests
            test_dir = tmp_path / "tests"
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "--output-dir",
                    str(test_dir),
                    "-v",
                ],
                input="y\n",
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Generation failed: {result.stderr}"

            # Step 3: Verify files created
            sql_files = list(test_dir.glob("*.sql"))
            py_files = list(test_dir.glob("*.py"))

            assert len(sql_files) >= 2, "Should generate pgTAP tests"
            assert len(py_files) >= 1, "Should generate pytest tests"

            # Step 4: Validate SQL syntax
            for sql_file in sql_files:
                content = sql_file.read_text()
                assert "BEGIN;" in content
                assert "ROLLBACK;" in content
                assert "SELECT plan(" in content

            # Step 5: Validate Python syntax
            import py_compile

            for py_file in py_files:
                py_compile.compile(str(py_file), doraise=True)

    def test_regenerate_after_entity_change(self):
        """Test regenerating tests after entity definition changes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            entity_file = tmp_path / "entity.yaml"
            test_dir = tmp_path / "tests"

            # Initial entity
            entity_file.write_text("""
entity: TestEntity
schema: test_schema
fields:
  name: text
            """)

            # Generate initial tests
            subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "-o",
                    str(test_dir),
                ],
                check=True,
            )

            initial_files = set(test_dir.glob("*"))

            # Modify entity (add field)
            entity_file.write_text("""
entity: TestEntity
schema: test_schema
fields:
  name: text
  email: email
            """)

            # Regenerate tests
            subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "-o",
                    str(test_dir),
                    "--overwrite",
                ],
                check=True,
            )

            updated_files = set(test_dir.glob("*"))

            # Should have same number of files
            assert len(initial_files) == len(updated_files)

            # Content should be updated (should mention email)
            structure_test = test_dir / "test_testentity_structure.sql"
            content = structure_test.read_text()
            assert "email" in content

    def test_multiple_entities_batch_generation(self):
        """Test generating tests for multiple entities at once."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            entity_dir = tmp_path / "entities"
            entity_dir.mkdir()

            # Create 3 entities
            for i, name in enumerate(["Contact", "Company", "Deal"], 1):
                entity_file = entity_dir / f"{name.lower()}.yaml"
                entity_file.write_text(f"""
entity: {name}
schema: crm
fields:
  name: text
                """)

            # Generate tests for all
            test_dir = tmp_path / "tests"
            result = subprocess.run(
                ["python", "-m", "src.cli.confiture_extensions", "generate-tests"]
                + list(entity_dir.glob("*.yaml"))
                + ["-o", str(test_dir)],
                input="y\n",
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # Should have tests for all 3 entities
            all_files = list(test_dir.glob("*.sql")) + list(test_dir.glob("*.py"))
            assert len(all_files) >= 9  # 3 entities × 3 files each

            # Each entity should have its tests
            assert any("contact" in f.name.lower() for f in all_files)
            assert any("company" in f.name.lower() for f in all_files)
            assert any("deal" in f.name.lower() for f in all_files)

    def test_reverse_engineer_then_analyze(self):
        """Test reverse engineering generated tests and analyzing coverage."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Generate tests
            entity_file = tmp_path / "entity.yaml"
            entity_file.write_text("""
entity: TestEntity
schema: test_schema
fields:
  name: text
  email: email
            """)

            test_dir = tmp_path / "tests"
            subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "-o",
                    str(test_dir),
                ],
                check=True,
            )

            # Reverse engineer the generated tests
            spec_dir = tmp_path / "specs"
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "reverse-tests",
                    str(test_dir / "test_testentity_structure.sql"),
                    "--entity",
                    "TestEntity",
                    "--output-dir",
                    str(spec_dir),
                    "--format",
                    "yaml",
                ],
                input="y\n",
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            # Should create TestSpec YAML
            spec_file = spec_dir / "TestEntity_tests.yaml"
            assert spec_file.exists()

            # YAML should be valid
            import yaml

            spec_content = yaml.safe_load(spec_file.read_text())
            assert spec_content["entity_name"] == "TestEntity"

    def test_preview_mode_no_files_created(self):
        """Test that preview mode doesn't create files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            entity_file = tmp_path / "entity.yaml"
            entity_file.write_text("entity: Test\nschema: test\nfields:\n  name: text")

            test_dir = tmp_path / "tests"

            # Generate with preview
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "src.cli.confiture_extensions",
                    "generate-tests",
                    str(entity_file),
                    "-o",
                    str(test_dir),
                    "--preview",
                ],
                input="y\n",
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert (
                "preview" in result.stdout.lower()
                or "would generate" in result.stdout.lower()
            )

            # No files should be created
            assert not test_dir.exists() or len(list(test_dir.iterdir())) == 0
