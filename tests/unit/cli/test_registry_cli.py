"""
Tests for Registry CLI commands

Tests the registry management CLI commands for listing domains, subdomains,
adding entries, and inspecting registry contents.
"""

import pytest
from click.testing import CliRunner

from src.cli.registry import registry


class TestRegistryCLI:
    """Test registry CLI commands"""

    @pytest.fixture
    def runner(self):
        """CLI test runner"""
        return CliRunner()

    def test_list_domains(self, runner):
        """Should list all domains"""
        result = runner.invoke(registry, ["list-domains"])

        assert result.exit_code == 0
        assert "Registered Domains:" in result.output
        assert "2 - crm" in result.output
        assert "3 - catalog" in result.output
        assert "Customer relationship management" in result.output

    def test_list_subdomains(self, runner):
        """Should list subdomains for a domain"""
        result = runner.invoke(registry, ["list-subdomains", "crm"])

        assert result.exit_code == 0
        assert "Subdomains for crm (2):" in result.output
        assert "03 - customer" in result.output
        assert "Customer contact entities" in result.output

    def test_list_subdomains_invalid_domain(self, runner):
        """Should error for invalid domain"""
        result = runner.invoke(registry, ["list-subdomains", "invalid"])

        assert result.exit_code == 1
        assert "Domain 'invalid' not found" in result.output

    def test_show_entity(self, runner):
        """Should show entity information"""
        result = runner.invoke(registry, ["show-entity", "Contact"])

        assert result.exit_code == 0
        assert "Entity: Contact" in result.output
        assert "Domain: crm" in result.output
        assert "Subdomain: customer" in result.output
        assert "Table Code: 01203571" in result.output

    def test_show_entity_not_found(self, runner):
        """Should error for non-existent entity"""
        result = runner.invoke(registry, ["show-entity", "NonExistentEntity"])

        assert result.exit_code == 1
        assert "Entity 'NonExistentEntity' not found" in result.output

    def test_add_domain(self, runner, tmp_path):
        """Should add a new domain"""
        # Create a temporary registry file
        registry_path = tmp_path / "test_registry.yaml"
        registry_path.write_text("""
version: 1.0.0
last_updated: '2025-11-12T10:35:39.498996'
schema_layers:
  '00': common
  '01': write_side
  '02': read_side
domains: {}
""")

        # Test adding domain
        result = runner.invoke(
            registry,
            [
                "add-domain",
                "--code",
                "7",
                "--name",
                "finance",
                "--description",
                "Financial management",
                "--multi-tenant",
            ],
            env={"DOMAIN_REGISTRY_PATH": str(registry_path)},
        )

        assert result.exit_code == 0
        assert "Domain 'finance' (7) added successfully" in result.output

    def test_add_domain_duplicate_code(self, runner):
        """Should error when adding domain with existing code"""
        result = runner.invoke(
            registry,
            [
                "add-domain",
                "--code",
                "2",  # Existing CRM domain
                "--name",
                "test",
                "--description",
                "Test domain",
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_add_domain_invalid_code(self, runner):
        """Should error for invalid domain code"""
        result = runner.invoke(
            registry,
            [
                "add-domain",
                "--code",
                "abc",  # Invalid
                "--name",
                "test",
                "--description",
                "Test domain",
            ],
        )

        assert result.exit_code == 1
        assert "Domain code must be a single digit from 1-9" in result.output

    def test_add_subdomain(self, runner):
        """Should add a new subdomain"""
        result = runner.invoke(
            registry,
            [
                "add-subdomain",
                "--domain",
                "crm",
                "--code",
                "99",
                "--name",
                "test_subdomain",
                "--description",
                "Test subdomain for CLI",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Subdomain 'test_subdomain' (99) added to domain 'crm' successfully"
            in result.output
        )

    def test_add_subdomain_invalid_domain(self, runner):
        """Should error for invalid domain"""
        result = runner.invoke(
            registry,
            [
                "add-subdomain",
                "--domain",
                "invalid",
                "--code",
                "99",
                "--name",
                "test",
                "--description",
                "Test",
            ],
        )

        assert result.exit_code == 1
        assert "Domain 'invalid' not found" in result.output

    def test_add_subdomain_duplicate_code(self, runner):
        """Should error when adding subdomain with existing code"""
        result = runner.invoke(
            registry,
            [
                "add-subdomain",
                "--domain",
                "crm",
                "--code",
                "03",  # Existing customer subdomain
                "--name",
                "test",
                "--description",
                "Test",
            ],
        )

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_validate_registry(self, runner):
        """Should validate registry integrity"""
        result = runner.invoke(registry, ["validate"])

        assert result.exit_code == 0
        assert "Registry validation passed!" in result.output

    def test_registry_help(self, runner):
        """Should show help for registry commands"""
        result = runner.invoke(registry, ["--help"])

        assert result.exit_code == 0
        assert "Manage domain registry" in result.output
        assert "list-domains" in result.output
        assert "list-subdomains" in result.output
        assert "show-entity" in result.output
