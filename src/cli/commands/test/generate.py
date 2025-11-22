"""Test generation command"""

from pathlib import Path

import click

from cli.base import common_options, validate_common_options
from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output as cli_output
from cli.utils.output import set_output_config


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@common_options
@click.option(
    "--type",
    "test_type",
    type=click.Choice(["pgtap", "pytest", "both"]),
    default="both",
    help="Test framework to generate",
)
@click.option("--include-crud/--no-crud", default=True, help="Include CRUD tests")
@click.option("--include-actions/--no-actions", default=True, help="Include action tests")
@click.option(
    "--include-constraints/--no-constraints",
    default=True,
    help="Include constraint violation tests",
)
@click.option("--with-seed", is_flag=True, help="Generate seed data alongside tests")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
@click.pass_context
def generate(
    ctx,
    files,
    output,
    verbose,
    quiet,
    test_type,
    include_crud,
    include_actions,
    include_constraints,
    with_seed,
    dry_run,
):
    """Auto-generate test files from SpecQL entities.

    Generates pgTAP (SQL) and/or pytest (Python) test files based on
    entity definitions and action specifications.

    Examples:

        # Generate both pgTAP and pytest tests
        specql test generate entities/*.yaml -o tests/

        # Only pgTAP tests
        specql test generate contact.yaml --type pgtap

        # Tests with seed data
        specql test generate entities/*.yaml --with-seed
    """
    with handle_cli_error():
        validate_common_options(verbose=verbose, quiet=quiet)
        set_output_config(verbose=verbose, quiet=quiet)

        from core.specql_parser import SpecQLParser
        from testing.pgtap.pgtap_generator import PgTAPGenerator
        from testing.pytest.pytest_generator import PytestGenerator

        parser = SpecQLParser()
        pgtap_gen = PgTAPGenerator()
        pytest_gen = PytestGenerator()

        output_dir = Path(output) if output else Path("tests")

        for file_path in files:
            with open(file_path) as f:
                yaml_content = f.read()
            entity = parser.parse(yaml_content)
            entity_config = _build_entity_config(entity)
            field_mappings = _build_field_mappings(entity)
            actions = _extract_actions(entity)

            generated_files = []

            # Generate pgTAP tests
            if test_type in ("pgtap", "both"):
                pgtap_content = _generate_pgtap(
                    pgtap_gen,
                    entity_config,
                    field_mappings,
                    actions,
                    include_crud,
                    include_actions,
                    include_constraints,
                )

                if dry_run:
                    cli_output.info(f"\n--- pgtap/test_{entity.name.lower()}.sql ---")
                    cli_output.info(pgtap_content[:2000])
                else:
                    pgtap_dir = output_dir / "pgtap"
                    pgtap_dir.mkdir(parents=True, exist_ok=True)
                    pgtap_file = pgtap_dir / f"test_{entity.name.lower()}.sql"
                    pgtap_file.write_text(pgtap_content)
                    generated_files.append(str(pgtap_file))

            # Generate pytest tests
            if test_type in ("pytest", "both"):
                pytest_content = pytest_gen.generate_pytest_integration_tests(
                    entity_config, actions
                )

                # Filter based on options
                if not include_crud:
                    pytest_content = _filter_crud_tests(pytest_content)

                if dry_run:
                    cli_output.info(f"\n--- pytest/test_{entity.name.lower()}.py ---")
                    cli_output.info(pytest_content[:2000])
                else:
                    pytest_dir = output_dir / "pytest"
                    pytest_dir.mkdir(parents=True, exist_ok=True)
                    pytest_file = pytest_dir / f"test_{entity.name.lower()}.py"
                    pytest_file.write_text(pytest_content)
                    generated_files.append(str(pytest_file))

            # Generate seed data if requested
            if with_seed and not dry_run:
                from testing.seed.seed_generator import EntitySeedGenerator
                from testing.seed.sql_generator import SeedSQLGenerator

                # Parse entity again for seed generation
                entity_config = _build_entity_config(entity)
                field_mappings = _build_field_mappings(entity)

                generator = EntitySeedGenerator(
                    entity_config=entity_config,
                    field_mappings=field_mappings,
                    seed=42,  # deterministic
                )

                records = generator.generate_batch(count=10, scenario=0)

                sql_gen = SeedSQLGenerator(entity_config)
                seed_content = sql_gen.generate_file(
                    entities=records,
                    scenario=0,
                    description=f"Generated 10 records for {entity.name}",
                )

                seed_dir = output_dir / "seeds"
                seed_dir.mkdir(parents=True, exist_ok=True)
                seed_file = seed_dir / f"seed_{entity.name.lower()}.sql"
                seed_file.write_text(seed_content)
                cli_output.success(f"Generated {seed_file}")

            if not dry_run:
                for f in generated_files:
                    cli_output.success(f"Generated {f}")

        if not dry_run:
            cli_output.success(f"\nTests written to {output_dir}/")


def _generate_pgtap(
    generator,
    entity_config,
    field_mappings,
    actions,
    include_crud,
    include_actions,
    include_constraints,
) -> str:
    """Generate combined pgTAP test file"""
    sections = []

    # Structure tests (always included)
    sections.append(generator.generate_structure_tests(entity_config))

    # CRUD tests
    if include_crud:
        sections.append(generator.generate_crud_tests(entity_config, field_mappings))

    # Constraint tests
    if include_constraints:
        scenarios = [
            {
                "scenario_type": "constraint_violation",
                "scenario_name": "duplicate_email",
                "input_overrides": {"email": "duplicate@test.com"},
                "expected_error_code": "duplicate",
            }
        ]
        sections.append(generator.generate_constraint_tests(entity_config, scenarios))

    # Action tests
    if include_actions and actions:
        scenarios = [
            {
                "target_action": a["name"],
                "scenario_name": f"{a['name']}_happy_path",
                "expected_result": "success",
                "setup_sql": "",
            }
            for a in actions
        ]
        sections.append(generator.generate_action_tests(entity_config, actions, scenarios))

    return "\n\n".join(sections)


def _filter_crud_tests(content: str) -> str:
    """Remove CRUD test methods from pytest content"""
    import re

    # Remove test_create_*, test_update_*, test_delete_* methods
    content = re.sub(
        r"\n    def test_(create|update|delete)_\w+\(self.*?(?=\n    def |\nclass |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )
    return content


def _build_entity_config(entity) -> dict:
    """Build entity config dict"""
    return {
        "entity_name": entity.name,
        "schema_name": entity.schema or "public",
        "table_name": f"tb_{entity.name.lower()}",
        "base_uuid_prefix": entity.name[:6].upper(),
        "is_tenant_scoped": False,  # TODO: determine from entity metadata
        "default_tenant_id": "01232122-0000-0000-2000-000000000001",
        "default_user_id": "01232122-0000-0000-2000-000000000002",
    }


def _build_field_mappings(entity) -> list:
    """Build field mappings list"""
    return [
        {
            "field_name": name,
            "field_type": field.type_name,
            "generator_type": "random",
            "nullable": field.nullable,
            "priority_order": i,
        }
        for i, (name, field) in enumerate(entity.fields.items())
    ]


def _extract_actions(entity) -> list:
    """Extract actions from entity"""
    if not hasattr(entity, "actions") or not entity.actions:
        return []
    return [{"name": a.name} for a in entity.actions]
