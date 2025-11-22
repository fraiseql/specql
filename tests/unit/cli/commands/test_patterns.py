"""
Tests for patterns detect/apply commands
"""

import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from cli.main import app


class TestPatternsCommands:
    """Test patterns command group functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_detect_audit_trail_pattern(self):
        """Detects audit trail pattern from entity with audit fields."""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
  created_at: timestamp
  created_by: ref(User)
  updated_at: timestamp
  updated_by: ref(User)
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name])

            assert result.exit_code == 0
            assert "audit-trail" in result.output
            assert "confidence" in result.output.lower()

    def test_detect_multi_tenant_pattern(self):
        """Detects multi-tenant pattern from entity with tenant_id."""
        yaml_content = """
entity: Invoice
schema: finance
fields:
  tenant_id: uuid
  amount: decimal
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name])

            assert result.exit_code == 0
            assert "multi-tenant" in result.output
            assert "confidence" in result.output.lower()

    def test_detect_outputs_json_format(self):
        """--format=json produces valid JSON output."""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name, "--format=json"])

            assert result.exit_code == 0
            # Should show warning about needing --output for JSON
            assert "Specify --output file for JSON/YAML format" in result.output

    def test_apply_audit_trail_adds_fields(self):
        """Applying audit-trail pattern adds required fields."""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "apply", "audit-trail", f.name])

            assert result.exit_code == 0

            # Verify file was modified
            updated = yaml.safe_load(Path(f.name).read_text())
            assert "created_at" in updated["fields"]
            assert "updated_at" in updated["fields"]

    def test_apply_preview_no_modification(self):
        """--preview shows changes without modifying file."""
        yaml_content = """
entity: Contact
schema: crm
fields:
  email: text
"""
        original_content = yaml_content

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(
                app, ["patterns", "apply", "audit-trail", f.name, "--preview"]
            )

            assert result.exit_code == 0
            assert "Preview mode" in result.output

            # Verify file was NOT modified
            updated_content = Path(f.name).read_text()
            assert updated_content == original_content

    def test_detect_soft_delete_pattern(self):
        """Detects soft-delete pattern from entity with deleted_at."""
        yaml_content = """
entity: User
schema: auth
fields:
  email: text
  deleted_at: timestamptz
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name])

            assert result.exit_code == 0
            assert "soft-delete" in result.output

    def test_detect_state_machine_pattern(self):
        """Detects state-machine pattern from entity with status enum."""
        yaml_content = """
entity: Order
schema: commerce
fields:
  status: enum(pending, processing, completed, cancelled)
  status_updated_at: timestamptz
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name])

            assert result.exit_code == 0
            assert "state-machine" in result.output

    def test_apply_soft_delete_adds_deleted_at(self):
        """Applying soft-delete pattern adds deleted_at field."""
        yaml_content = """
entity: User
schema: auth
fields:
  email: text
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "apply", "soft-delete", f.name])

            assert result.exit_code == 0

            # Verify file was modified
            updated = yaml.safe_load(Path(f.name).read_text())
            assert "deleted_at" in updated["fields"]

    def test_apply_multi_tenant_adds_tenant_id(self):
        """Applying multi-tenant pattern adds tenant_id field."""
        yaml_content = """
entity: Invoice
schema: finance
fields:
  amount: decimal
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "apply", "multi-tenant", f.name])

            assert result.exit_code == 0

            # Verify file was modified
            updated = yaml.safe_load(Path(f.name).read_text())
            assert "tenant_id" in updated["fields"]

    def test_detect_no_patterns_found(self):
        """Returns empty result when no patterns detected."""
        yaml_content = """
entity: SimpleEntity
schema: test
fields:
  id: serial
  name: text
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "detect", f.name])

            assert result.exit_code == 0
            # Should indicate no patterns found
            assert "no patterns" in result.output.lower() or "0 patterns" in result.output

    def test_apply_unknown_pattern_fails(self):
        """Applying unknown pattern shows error."""
        yaml_content = """
entity: Test
schema: test
fields:
  id: serial
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            f.write(yaml_content.encode())
            f.flush()

            result = self.runner.invoke(app, ["patterns", "apply", "unknown-pattern", f.name])

            assert result.exit_code != 0
            assert "unknown" in result.output.lower() or "not found" in result.output.lower()
