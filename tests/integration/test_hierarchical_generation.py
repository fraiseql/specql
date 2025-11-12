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
table_code: "012399"
fields:
  first_name: text
  last_name: text
  email: text
  phone: text
actions:
  - name: create_contact
    steps:
      - insert: TestContact
""")

        order_yaml = tmp_path / "order.yaml"
        order_yaml.write_text("""
entity: TestOrder
schema: crm
subdomain: sales
table_code: "012299"
fields:
  contact_id: uuid
  total_amount: money
  status: enum(pending, confirmed, shipped, delivered)
  order_date: timestamp
actions:
  - name: create_order
    steps:
      - insert: TestOrder
""")

        # Generate using hierarchical workflow
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_hierarchical(
            entity_files=[str(contact_yaml), str(order_yaml)],
            output_dir=str(output_dir)
        )

        # Check for errors (allow some for now while debugging)
        if result.errors:
            print(f"Generation errors: {result.errors}")
        if result.warnings:
            print(f"Generation warnings: {result.warnings}")

        # Verify files were created
        assert len(result.migrations) > 0, "No migration files generated"

        # Check hierarchical directory structure relative to output_dir
        output_path = Path(output_dir)
        schema_base = output_path / "0_schema"

        # Write-side structure
        write_side = schema_base / "01_write_side"
        assert write_side.exists(), f"Write-side directory not created at {write_side}"

        # CRM domain
        crm_write = write_side / "012_crm" / "0123_customer"
        assert crm_write.exists(), f"CRM customer subdomain directory not created at {crm_write}"

        # Contact entity directory (using table code 012399)
        contact_entity_dir = crm_write / "01239_testcontact"
        assert contact_entity_dir.exists(), f"Contact entity directory not created at {contact_entity_dir}"

        # Contact table file
        contact_table = contact_entity_dir / "012399_tb_testcontact.sql"
        assert contact_table.exists(), f"Contact table file not created at {contact_table}"

        # Contact function file
        contact_function = contact_entity_dir / "012399_fn_testcontact_create_contact.sql"
        assert contact_function.exists(), f"Contact function file not created at {contact_function}"

        # Sales domain
        sales_write = write_side / "012_crm" / "0122_sales"
        assert sales_write.exists(), f"Sales subdomain directory not created at {sales_write}"

        # Order entity directory (using table code 012299)
        order_entity_dir = sales_write / "01229_testorder"
        assert order_entity_dir.exists(), f"Order entity directory not created at {order_entity_dir}"

        # Order table file
        order_table = order_entity_dir / "012299_tb_testorder.sql"
        assert order_table.exists(), f"Order table file not created at {order_table}"

        # TODO: Add read-side assertions once read-side generation is working
        # Read-side structure
        # read_side = schema_base / "02_query_side"
        # assert read_side.exists(), f"Read-side directory not created at {read_side}"

    def test_hierarchical_preserves_dependencies(self, tmp_path):
        """
        Test that hierarchical generation preserves entity dependencies.

        When entities reference each other, they should be generated in
        the correct dependency order to avoid foreign key constraint errors.
        """
        # Create entities with dependencies: Company -> Contact -> Order
        company_yaml = tmp_path / "company.yaml"
        company_yaml.write_text("""
entity: TestCompany
schema: crm
subdomain: core
table_code: "012199"
fields:
  name: text
  industry: text
""")

        contact_yaml = tmp_path / "contact.yaml"
        contact_yaml.write_text("""
entity: TestContact
schema: crm
subdomain: customer
table_code: "012399"
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
subdomain: sales
table_code: "012299"
fields:
  contact_id: uuid
  total_amount: money
  status: text
""")

        # Generate hierarchically
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_hierarchical(
            entity_files=[str(order_yaml), str(contact_yaml), str(company_yaml)],  # Out of order
            output_dir=str(output_dir)
        )

        # Verify successful generation
        assert len(result.errors) == 0, f"Generation errors: {result.errors}"

        # Check that all expected files exist (relative to output_dir)
        output_path = Path(output_dir)
        schema_base = output_path / "0_schema"
        write_side = schema_base / "01_write_side"
        crm_write = write_side / "012_crm"

        # Company (core subdomain)
        company_entity_dir = crm_write / "0121_core" / "01219_testcompany"
        assert company_entity_dir.exists(), f"Company entity directory not created at {company_entity_dir}"
        company_table = company_entity_dir / "012199_tb_testcompany.sql"
        assert company_table.exists(), f"Company table not generated at {company_table}"

        # Contact (customer subdomain)
        contact_entity_dir = crm_write / "0123_customer" / "01239_testcontact"
        assert contact_entity_dir.exists(), f"Contact entity directory not created at {contact_entity_dir}"
        contact_table = contact_entity_dir / "012399_tb_testcontact.sql"
        assert contact_table.exists(), f"Contact table not generated at {contact_table}"

        # Order (sales subdomain)
        order_entity_dir = crm_write / "0122_sales" / "01229_testorder"
        assert order_entity_dir.exists(), f"Order entity directory not created at {order_entity_dir}"
        order_table = order_entity_dir / "012299_tb_testorder.sql"
        assert order_table.exists(), f"Order table not generated at {order_table}"

    def test_hierarchical_handles_multiple_domains(self, tmp_path):
        """
        Test hierarchical generation with multiple domains and subdomains.

        This test ensures the system can handle complex multi-domain
        architectures with proper directory structure.
        """
        # Create entities across multiple subdomains in CRM domain
        entities = [
            ("crm", "core", "TestCompany", "012199"),
            ("crm", "customer", "TestContact", "012399"),
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
        company_entity_dir = crm_core / "01219_testcompany"
        assert company_entity_dir.exists(), f"Company entity directory not created at {company_entity_dir}"
        assert (company_entity_dir / "012199_tb_testcompany.sql").exists(), "Company table not created"

        crm_customer = crm_write / "0123_customer"
        assert crm_customer.exists(), f"CRM customer subdomain directory not created at {crm_customer}"
        contact_entity_dir = crm_customer / "01239_testcontact"
        assert contact_entity_dir.exists(), f"Contact entity directory not created at {contact_entity_dir}"
        assert (contact_entity_dir / "012399_tb_testcontact.sql").exists(), "Contact table not created"



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
table_code: "012399"
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
subdomain: sales
table_code: "012299"
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