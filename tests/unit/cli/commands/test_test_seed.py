"""Tests for specql test seed command"""

import pytest
from click.testing import CliRunner

from cli.main import app


class TestSeedCommand:
    """Test seed data generation command"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_entity(self, tmp_path):
        entity_file = tmp_path / "contact.yaml"
        entity_file.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  first_name: text
  last_name: text
  status: enum(lead, qualified, customer)
""")
        return entity_file

    def test_seed_generates_sql_file(self, runner, sample_entity, tmp_path):
        """Test seed generates SQL INSERT statements"""
        output_dir = tmp_path / "seeds"
        result = runner.invoke(
            app, ["test", "seed", str(sample_entity), "-o", str(output_dir), "--count", "5"]
        )

        assert result.exit_code == 0
        seed_file = output_dir / "seed_contact.sql"
        assert seed_file.exists()
        content = seed_file.read_text()
        assert "INSERT INTO crm.tb_contact" in content
        assert content.count("INSERT") == 5

    def test_seed_deterministic_mode(self, runner, sample_entity, tmp_path):
        """Test deterministic mode produces same output"""
        output_dir1 = tmp_path / "seeds1"
        output_dir2 = tmp_path / "seeds2"

        runner.invoke(
            app,
            [
                "test",
                "seed",
                str(sample_entity),
                "-o",
                str(output_dir1),
                "--count",
                "3",
                "--deterministic",
            ],
        )
        runner.invoke(
            app,
            [
                "test",
                "seed",
                str(sample_entity),
                "-o",
                str(output_dir2),
                "--count",
                "3",
                "--deterministic",
            ],
        )

        content1 = (output_dir1 / "seed_contact.sql").read_text()
        content2 = (output_dir2 / "seed_contact.sql").read_text()

        # Remove timestamp lines for comparison
        lines1 = [line for line in content1.split("\n") if not line.startswith("-- Generated:")]
        lines2 = [line for line in content2.split("\n") if not line.startswith("-- Generated:")]
        assert lines1 == lines2

    def test_seed_json_format(self, runner, sample_entity, tmp_path):
        """Test seed can output JSON format"""
        output_dir = tmp_path / "seeds"
        result = runner.invoke(
            app, ["test", "seed", str(sample_entity), "-o", str(output_dir), "--format", "json"]
        )

        assert result.exit_code == 0
        seed_file = output_dir / "seed_contact.json"
        assert seed_file.exists()

    def test_seed_scenario_parameter(self, runner, sample_entity, tmp_path):
        """Test scenario parameter affects UUID generation"""
        output_dir = tmp_path / "seeds"
        result = runner.invoke(
            app, ["test", "seed", str(sample_entity), "-o", str(output_dir), "--scenario", "5"]
        )

        assert result.exit_code == 0
        content = (output_dir / "seed_contact.sql").read_text()
        assert "Scenario: 5" in content

    def test_seed_dry_run(self, runner, sample_entity, tmp_path):
        """Test dry run shows preview without writing"""
        result = runner.invoke(app, ["test", "seed", str(sample_entity), "--dry-run"])

        assert result.exit_code == 0
        assert "INSERT INTO crm.tb_contact" in result.output
        # No files should be created
        assert not list(tmp_path.glob("seeds/*.sql"))

    def test_seed_multiple_entities(self, runner, tmp_path):
        """Test seeding multiple entities respects FK dependencies"""
        # Create company entity
        company_file = tmp_path / "company.yaml"
        company_file.write_text("""
entity: Company
schema: crm
fields:
  name: text
  website: text?
""")

        # Create contact entity with FK to company
        contact_file = tmp_path / "contact.yaml"
        contact_file.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  company: ref(Company)
""")

        output_dir = tmp_path / "seeds"
        result = runner.invoke(
            app, ["test", "seed", str(company_file), str(contact_file), "-o", str(output_dir)]
        )

        assert result.exit_code == 0
        # Company should be seeded before Contact
        assert (output_dir / "seed_company.sql").exists()
        assert (output_dir / "seed_contact.sql").exists()
