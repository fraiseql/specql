"""Tests for security CLI commands"""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner


class TestSecurityCLI:
    """Test security CLI commands"""

    def setup_method(self):
        self.runner = CliRunner()

    def test_validate_security_command_valid_yaml(self):
        """Test validate command with valid security YAML"""
        from cli.confiture_extensions import validate_security

        yaml_content = """
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
"""

        with self.runner.isolated_filesystem():
            yaml_file = Path("test_security.yaml")
            yaml_file.write_text(yaml_content)

            result = self.runner.invoke(validate_security, [str(yaml_file)])

            assert result.exit_code == 0
            assert "Valid security configuration" in result.output

    def test_validate_security_command_invalid_yaml(self):
        """Test validate command with invalid YAML"""
        from cli.confiture_extensions import validate_security

        yaml_content = """
security:
  network_tiers:
    - name: web
      firewall_rules: [  # Missing closing bracket - malformed YAML
      - allow: [http, https]
          from: internet
"""

        with self.runner.isolated_filesystem():
            yaml_file = Path("test_security.yaml")
            yaml_file.write_text(yaml_content)

            result = self.runner.invoke(validate_security, [str(yaml_file)])

            assert result.exit_code == 1
            assert "Validation failed" in result.output

    def test_check_compliance_command_compliant(self):
        """Test check-compliance command with compliant config"""
        from cli.confiture_extensions import check_compliance

        yaml_content = """
security:
  compliance_preset: pci-compliant
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: api
      firewall_rules:
        - allow: 8080
          from: web
    - name: database
      firewall_rules:
        - allow: 5432
          from: api
  waf:
    enabled: true
  encryption_at_rest: true
  encryption_in_transit: true
  audit_logging: true
"""

        with self.runner.isolated_filesystem():
            yaml_file = Path("test_security.yaml")
            yaml_file.write_text(yaml_content)

            result = self.runner.invoke(check_compliance, [str(yaml_file)])

            assert result.exit_code == 0
            assert "Compliant" in result.output

    def test_check_compliance_command_non_compliant(self):
        """Test check-compliance command with non-compliant config"""
        from cli.confiture_extensions import check_compliance

        yaml_content = """
security:
  compliance_preset: pci-compliant
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
  # Missing required controls for PCI-DSS
"""

        with self.runner.isolated_filesystem():
            yaml_file = Path("test_security.yaml")
            yaml_file.write_text(yaml_content)

            result = self.runner.invoke(check_compliance, [str(yaml_file)])

            assert result.exit_code == 1
            assert "Compliance gaps found" in result.output

    def test_init_command_three_tier(self):
        """Test init command with three-tier preset"""
        from cli.confiture_extensions import init

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                init, ["--preset", "three-tier", "--output", "security.yaml"]
            )

            assert result.exit_code == 0
            assert "Created security configuration" in result.output

            # Check that file was created
            output_file = Path("security.yaml")
            assert output_file.exists()

            content = output_file.read_text()
            assert "three-tier" in content
            assert "network_tiers:" in content

    def test_init_command_with_compliance(self):
        """Test init command with compliance preset"""
        from cli.confiture_extensions import init

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                init,
                ["--preset", "three-tier", "--compliance", "pci-dss", "--output", "security.yaml"],
            )

            assert result.exit_code == 0

            output_file = Path("security.yaml")
            content = output_file.read_text()
            assert "pci-compliant" in content

    def test_diff_command_identical_files(self):
        """Test diff command with identical files"""
        from cli.confiture_extensions import diff

        yaml_content = """
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
"""

        with self.runner.isolated_filesystem():
            file1 = Path("security1.yaml")
            file2 = Path("security2.yaml")
            file1.write_text(yaml_content)
            file2.write_text(yaml_content)

            result = self.runner.invoke(diff, [str(file1), str(file2)])

            assert result.exit_code == 0
            assert "No differences found" in result.output

    def test_diff_command_different_files(self):
        """Test diff command with different files"""
        from cli.confiture_extensions import diff

        yaml1 = """
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
"""

        yaml2 = """
security:
  network_tiers:
    - name: web
      firewall_rules:
        - allow: [http, https]
          from: internet
    - name: api
      firewall_rules:
        - allow: 8080
          from: web
"""

        with self.runner.isolated_filesystem():
            file1 = Path("security1.yaml")
            file2 = Path("security2.yaml")
            file1.write_text(yaml1)
            file2.write_text(yaml2)

            result = self.runner.invoke(diff, [str(file1), str(file2)])

            assert result.exit_code == 1
            assert "Differences found" in result.output
            assert "Added network tier: api" in result.output

    @patch("infrastructure.generators.aws_security_generator.AWSSecurityGenerator")
    def test_generate_infra_command_aws(self, mock_generator_class):
        """Test generate-infra command for AWS"""
        from cli.confiture_extensions import generate_infra

        # Mock the generator
        mock_generator = mock_generator_class.return_value
        mock_generator.generate_security_groups.return_value = "mock terraform code"

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                generate_infra, ["three-tier-app", "--provider", "aws", "--dry-run"]
            )

            assert result.exit_code == 0
            assert "mock terraform code" in result.output
            mock_generator.generate_security_groups.assert_called_once()

    def test_generate_infra_command_unknown_pattern(self):
        """Test generate-infra command with unknown pattern"""
        from cli.confiture_extensions import generate_infra

        result = self.runner.invoke(generate_infra, ["unknown-pattern", "--provider", "aws"])

        assert result.exit_code == 1
        assert "Pattern 'unknown-pattern' not found" in result.output
