"""Test SQL code generation and complete workflow"""

import tempfile
import textwrap
from pathlib import Path

import pytest
from cli.generate import cli as generate_cli
from cli.reverse_python import reverse_python
from cli.validate import validate as validate_cli
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing."""
    return CliRunner()


def test_foundation_generation(cli_runner):
    """Test foundation SQL generation"""
    spec = textwrap.dedent(
        """
        entity: Product
        schema: catalog
        fields:
          name: text
          price: decimal
    """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "product.yaml"
        spec_file.write_text(spec)

        output_dir = Path(tmpdir) / "sql"

        # Should generate SQL without errors
        result = cli_runner.invoke(
            generate_cli,
            ["entities", str(spec_file), "--output-dir", str(output_dir), "--foundation-only"],
        )
        assert result.exit_code == 0

        # Check foundation file exists (foundation-only mode only generates foundation)
        assert (output_dir / "000_app_foundation.sql").exists()


def test_entity_generation(cli_runner):
    """Test basic entity SQL generation"""
    spec = textwrap.dedent(
        """
        entity: Order
        schema: sales
        fields:
          status: text
    """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "order.yaml"
        spec_file.write_text(spec)

        output_dir = Path(tmpdir) / "sql"

        # Should generate entity SQL
        result = cli_runner.invoke(
            generate_cli, ["entities", str(spec_file), "--output-dir", str(output_dir)]
        )
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback

            traceback.print_exc()

        # List files in output directory and db/schema
        if output_dir.exists():
            all_files = list(output_dir.rglob("*"))
            print(f"All files in {output_dir}: {all_files}")

        db_schema_files = list(Path("db/schema").rglob("*")) if Path("db/schema").exists() else []
        print(f"All files in db/schema: {db_schema_files}")

        assert result.exit_code == 0

        # Check that entity table is generated (in db/schema for hierarchical format)
        all_files = list(output_dir.rglob("*")) + db_schema_files
        assert any("order.sql" in str(f) for f in all_files)


def test_complete_workflow(cli_runner):
    """Test complete SpecQL workflow: Django model → YAML → validation → SQL generation"""
    # Create a comprehensive Django model
    django_model = textwrap.dedent(
        """
        from django.db import models

        class Booker(models.Model):
            name = models.CharField(max_length=255)
            email = models.EmailField()
            phone = models.CharField(max_length=20)
            group_size = models.PositiveIntegerField()
            registered_at = models.DateTimeField(auto_now_add=True)
            last_updated = models.DateTimeField(auto_now=True)

            def create_booking(self, accommodation_id, check_in, check_out):
                # Custom method that should be detected
                pass

        class Accommodation(models.Model):
            title = models.CharField(max_length=255)
            description = models.TextField()
            max_guests = models.IntegerField()
            price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
            is_active = models.BooleanField(default=True)

        class Booking(models.Model):
            booker = models.ForeignKey(Booker, on_delete=models.CASCADE)
            accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE)
            check_in = models.DateField()
            check_out = models.DateField()
            status = models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('confirmed', 'Confirmed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending'
            )
            total_price = models.DecimalField(max_digits=10, decimal_places=2)
            booked_at = models.DateTimeField(auto_now_add=True)
    """
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # 1. Create Django model file
        django_file = tmpdir_path / "models.py"
        django_file.write_text(django_model)

        # 2. Reverse engineer to YAML
        entities_dir = tmpdir_path / "entities"
        result = cli_runner.invoke(
            reverse_python, [str(django_file), "--output-dir", str(entities_dir)]
        )
        print(f"Reverse exit code: {result.exit_code}")
        print(f"Reverse output: {result.output}")
        if result.exception:
            print(f"Reverse exception: {result.exception}")
            import traceback

            traceback.print_exc()
        assert result.exit_code == 0

        # Should generate 3 YAML files
        yaml_files = list(entities_dir.glob("*.yaml"))
        assert len(yaml_files) == 3
        assert any("booker" in str(f) for f in yaml_files)
        assert any("accommodation" in str(f) for f in yaml_files)
        assert any("booking" in str(f) for f in yaml_files)

        # 3. Validate generated YAML
        yaml_files = list(entities_dir.glob("*.yaml"))
        result = cli_runner.invoke(validate_cli, [str(f) for f in yaml_files])
        print(f"Validate exit code: {result.exit_code}")
        print(f"Validate output: {result.output}")
        if result.exception:
            print(f"Validate exception: {result.exception}")
        assert result.exit_code == 0

        # 4. Generate SQL from YAML
        sql_dir = tmpdir_path / "sql"
        result = cli_runner.invoke(
            generate_cli,
            ["entities"] + [str(f) for f in yaml_files] + ["--output-dir", str(sql_dir)],
        )
        assert result.exit_code == 0

        # Check that SQL files were generated
        all_sql_files = list(sql_dir.rglob("*.sql"))
        assert len(all_sql_files) > 0

        # Should have foundation and tables
        foundation_files = [f for f in all_sql_files if "foundation" in str(f)]
        table_files = [f for f in all_sql_files if "table" in str(f) or "tb_" in f.read_text()]

        assert len(foundation_files) > 0
        assert len(table_files) > 0
