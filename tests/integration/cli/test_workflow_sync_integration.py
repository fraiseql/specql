"""
Integration tests for workflow sync command with real backend.
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


class TestWorkflowSyncIntegration:
    """Integration tests for workflow sync command."""

    def test_sync_detects_modified_yaml(self, runner):
        """Sync detects and regenerates modified YAML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create initial YAML
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            # Generate initial output
            result = runner.invoke(app, ["generate", str(contact), "-o", str(output)])
            assert result.exit_code == 0

            # Verify initial output exists
            initial_sql = Path("db/schema/10_tables/contact.sql").read_text()
            assert "email" in initial_sql

            # Modify YAML
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  phone: text
""")

            # Run sync
            result = runner.invoke(app, ["workflow", "sync", str(entities)])

            assert result.exit_code == 0
            assert "contact.yaml" in result.output

            # Verify regeneration
            updated_sql = Path("db/schema/10_tables/contact.sql").read_text()
            assert "phone" in updated_sql

    def test_sync_dry_run_no_changes(self, runner):
        """Dry run detects changes but doesn't regenerate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create YAML
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            # Generate initial output
            runner.invoke(app, ["generate", str(contact), "-o", str(output)])

            # Modify YAML
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  phone: text
""")

            # Run sync dry-run
            result = runner.invoke(app, ["workflow", "sync", str(entities), "--dry-run"])

            assert result.exit_code == 0
            assert "contact.yaml" in result.output
            assert "changed file(s)" in result.output

            # Verify no new output was generated (should still have old content)
            sql_file = Path("db/schema/10_tables/contact.sql")
            if sql_file.exists():
                content = sql_file.read_text()
                # Should not contain phone since dry-run shouldn't regenerate
                assert "phone" not in content

    def test_sync_force_regenerates_all(self, runner):
        """--force regenerates all files regardless of modification time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create YAML
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            # Generate initial output
            runner.invoke(app, ["generate", str(contact), "-o", str(output)])

            # Run sync with force (no changes made to YAML)
            result = runner.invoke(app, ["workflow", "sync", str(entities), "--force"])

            assert result.exit_code == 0
            assert "contact.yaml" in result.output
            assert "Sync completed" in result.output

    def test_sync_exclude_pattern_works(self, runner):
        """--exclude skips matching files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create multiple YAML files
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            user = entities / "user.yaml"
            user.write_text("""
entity: User
schema: auth
fields:
  username: text
""")

            # Generate initial output
            runner.invoke(app, ["generate", str(contact), "-o", str(output)])
            runner.invoke(app, ["generate", str(user), "-o", str(output)])

            # Modify both files
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  phone: text
""")

            user.write_text("""
entity: User
schema: auth
fields:
  username: text
  email: text
""")

            # Run sync excluding user.yaml
            result = runner.invoke(app, ["workflow", "sync", str(entities), "--exclude=user.yaml"])

            assert result.exit_code == 0
            assert "contact.yaml" in result.output
            # Should only show contact.yaml as being processed
            assert "📄 contact.yaml" in result.output
            assert "📄 user.yaml" not in result.output

            # Verify only contact was regenerated
            contact_sql = Path("db/schema/10_tables/contact.sql")
            user_sql = Path("db/schema/10_tables/user.sql")

            assert "phone" in contact_sql.read_text()
            # User should not have been regenerated, so no email field
            assert "email" not in user_sql.read_text()

    def test_sync_include_patterns_applies_detection(self, runner):
        """--include-patterns runs pattern detection on changed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create YAML with audit trail pattern
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  created_at: timestamp
  updated_at: timestamp
  created_by: ref(User)
  updated_by: ref(User)
""")

            # Generate initial output
            runner.invoke(app, ["generate", str(contact), "-o", str(output)])

            # Modify YAML to trigger change
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
  phone: text
  created_at: timestamp
  updated_at: timestamp
  created_by: ref(User)
  updated_by: ref(User)
""")

            # Run sync with pattern detection
            result = runner.invoke(app, ["workflow", "sync", str(entities), "--include-patterns"])

            assert result.exit_code == 0
            assert "contact.yaml" in result.output
            # Should detect audit-trail pattern
            assert (
                "audit-trail" in result.output.lower()
                or "patterns detected" in result.output.lower()
            )

    def test_sync_handles_deleted_files(self, runner):
        """Sync handles files deleted between runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create YAML
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            # Generate initial output
            runner.invoke(app, ["generate", str(contact), "-o", str(output)])

            # Delete the YAML file
            contact.unlink()

            # Run sync - should handle gracefully
            result = runner.invoke(app, ["workflow", "sync", str(entities)])

            assert result.exit_code == 0
            # Should not crash, may show warning or just complete successfully
            assert "Sync completed" in result.output or "No changes detected" in result.output

    def test_sync_state_persistence(self, runner):
        """Sync state is persisted between runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entities = Path(tmpdir) / "entities"
            entities.mkdir()
            output = Path(tmpdir) / "output"
            output.mkdir()

            # Create YAML
            contact = entities / "contact.yaml"
            contact.write_text("""
entity: Contact
schema: crm
fields:
  email: text
""")

            # First sync - should detect and process
            result1 = runner.invoke(app, ["workflow", "sync", str(entities)])
            assert result1.exit_code == 0
            assert "contact.yaml" in result1.output

            # Second sync - should detect no changes
            result2 = runner.invoke(app, ["workflow", "sync", str(entities)])
            assert result2.exit_code == 0
            assert "No changes detected" in result2.output

            # Verify state file exists
            state_file = entities / ".specql-sync-state.json"
            assert state_file.exists()

            # Verify state contains hash
            state = json.loads(state_file.read_text())
            assert str(contact) in state
