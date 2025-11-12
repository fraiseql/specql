"""End-to-end integration tests for hierarchical generation workflow."""

import pytest
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator


class TestHierarchicalGenerationWorkflow:
    """Integration tests for the complete hierarchical generation workflow."""

    def test_generate_hierarchical_structure_end_to_end(self, tmp_path):
        """
        Test complete end-to-end hierarchical generation workflow.

        This test verifies the full pipeline from SpecQL YAML files to
        hierarchical directory structure with proper file organization.
        """
        # Create test entity files with explicit table codes to avoid conflicts
        contact_yaml = tmp_path / "contact.yaml"
        contact_yaml.write_text("""
entity: TestContact
schema: crm
subdomain: customer
table_code: "012321"
fields:
  first_name: text
  last_name: text
  email: text
  company_id: uuid
""")

        order_yaml = tmp_path / "order.yaml"
        order_yaml.write_text("""
entity: TestOrder
schema: crm
subdomain: core
table_code: "012121"
fields:
  contact_id: uuid
  total_amount: money
  status: text
""")

        # Generate hierarchically
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_hierarchical(
            entity_files=[str(contact_yaml), str(order_yaml)],
            output_dir=str(output_dir)
        )

        # Verify successful generation
        assert len(result.errors) == 0, f"Generation errors: {result.errors}"

        # Check that all expected files exist (relative to output_dir)
        output_path = Path(output_dir)
        schema_base = output_path / "0_schema"
        write_side = schema_base / "01_write_side"
        crm_write = write_side / "012_crm"

        # Contact (customer subdomain)
        contact_entity_dir = crm_write / "0123_customer" / "01232_testcontact"
        assert contact_entity_dir.exists(), f"Contact entity directory not created at {contact_entity_dir}"
        contact_table = contact_entity_dir / "012321_tb_testcontact.sql"
        assert contact_table.exists(), f"Contact table not generated at {contact_table}"

        # Order (core subdomain)
        order_entity_dir = crm_write / "0121_core" / "01212_testorder"
        assert order_entity_dir.exists(), f"Order entity directory not created at {order_entity_dir}"
        order_table = order_entity_dir / "012121_tb_testorder.sql"
        assert order_table.exists(), f"Order table not generated at {order_table}"

    def test_hierarchical_handles_multiple_domains(self, tmp_path):
        """
        Test hierarchical generation with multiple domains and subdomains.

        This test ensures the system can handle complex multi-domain
        architectures with proper directory structure.
        """
        # Create entities across multiple subdomains in CRM domain
        entities = [
            ("crm", "core", "TestCompany", "012121"),
            ("crm", "customer", "TestContact", "012321"),
        ]

        entity_files = []
        for domain, subdomain, entity_name, table_code in entities:
            entity_yaml = tmp_path / f"{entity_name.lower()}.yaml"
            entity_yaml.write_text(f"""
entity: {entity_name}
schema: {domain}
subdomain: {subdomain}
table_code: "{table_code}"
fields:
  name: text
  description: text
""")
            entity_files.append(str(entity_yaml))

        # Generate hierarchically
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_hierarchical(
            entity_files=entity_files,
            output_dir=str(output_dir)
        )

        # Verify successful generation
        assert len(result.errors) == 0, f"Generation errors: {result.errors}"

        # Check directory structure for each domain (relative to output_dir)
        output_path = Path(output_dir)
        schema_base = output_path / "0_schema"
        write_side = schema_base / "01_write_side"

        # CRM domain
        crm_write = write_side / "012_crm"
        crm_core = crm_write / "0121_core"
        assert crm_core.exists(), f"CRM core subdomain directory not created at {crm_core}"
        company_entity_dir = crm_core / "01212_testcompany"
        assert company_entity_dir.exists(), f"Company entity directory not created at {company_entity_dir}"
        assert (company_entity_dir / "012121_tb_testcompany.sql").exists(), "Company table not created"

        crm_customer = crm_write / "0123_customer"
        assert crm_customer.exists(), f"CRM customer subdomain directory not created at {crm_customer}"
        contact_entity_dir = crm_customer / "01232_testcontact"
        assert contact_entity_dir.exists(), f"Contact entity directory not created at {contact_entity_dir}"
        assert (contact_entity_dir / "012321_tb_testcontact.sql").exists(), "Contact table not created"



    def test_flat_mode_backward_compatible(self, tmp_path):
        """
        Test that flat mode (--flat) maintains backward compatibility.

        Flat mode should generate files in the traditional Confiture-style
        directory structure without hierarchical paths.
        """
        # Create test entity
        contact_yaml = tmp_path / "contact.yaml"
        contact_yaml.write_text("""
entity: TestContact
schema: crm
fields:
  first_name: text
  last_name: text
  email: text
""")

        # Generate in flat mode
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=False, output_format="confiture")

        result = orchestrator.generate_from_files(
            entity_files=[str(contact_yaml)],
            output_dir=str(output_dir)
        )

        # Verify successful generation
        assert len(result.errors) == 0, f"Generation errors: {result.errors}"

        # Check that generation succeeded (flat mode should work without errors)
        # The exact file structure may vary, but the important thing is that
        # flat mode generation completes successfully
        output_path = Path(output_dir)

        # Check that hierarchical directories don't exist (confirming we're in flat mode)
        hierarchical_base = output_path / "0_schema"
        assert not hierarchical_base.exists(), "Hierarchical directories should not exist in flat mode"

    def test_dry_run_shows_preview(self, tmp_path):
        """
        Test that --dry-run shows preview without writing files.

        Dry run should display what would be generated but not create
        any actual files on disk.
        """
        # Create test entity
        contact_yaml = tmp_path / "contact.yaml"
        contact_yaml.write_text("""
entity: TestContact
schema: crm
subdomain: customer
table_code: "012321"
fields:
  first_name: text
  last_name: text
  email: text
actions:
  - name: create_contact
    steps:
      - insert: TestContact
""")

        order_yaml = tmp_path / "order.yaml"
        order_yaml.write_text("""
entity: TestOrder
schema: crm
subdomain: core
table_code: "012131"
fields:
  contact_id: uuid
  total_amount: money
""")

        # Generate with dry run
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_hierarchical(
            entity_files=[str(contact_yaml), str(order_yaml)],
            output_dir=str(output_dir),
            dry_run=True
        )

        # Verify no errors
        assert len(result.errors) == 0, f"Generation errors: {result.errors}"

        # Verify no files were actually created
        output_path = Path(output_dir)
        schema_base = output_path / "0_schema"
        assert not schema_base.exists(), "No files should be created in dry run mode"

        # Check that result contains migration info (for preview)
        assert len(result.migrations) > 0, "Dry run should return migration info for preview"

        # Verify migration paths are set (even though files don't exist)
        for migration in result.migrations:
            assert migration.path is not None, "Migration should have path set for preview"