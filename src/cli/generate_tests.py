"""
CLI command for generating tests from SpecQL entities

Usage:
    specql generate-tests entities/contact.yaml
    specql generate-tests entities/*.yaml --type pgtap
    specql generate-tests entities/ --type pytest --output-dir tests/
"""

import click
from pathlib import Path
from typing import List
import yaml

from src.core.specql_parser import SpecQLParser
from src.testing.pgtap.pgtap_generator import PgTAPGenerator
from src.testing.pytest.pytest_generator import PytestGenerator


def _generate_tests_core(
    entity_files: tuple[str, ...],
    test_type: str,
    output_dir: str,
    preview: bool,
    verbose: bool,
    overwrite: bool,
) -> int:
    """Core logic for generating tests."""
    if not entity_files:
        click.secho("❌ Error: No entity files specified", fg="red")
        click.echo("\nUsage: specql generate-tests entities/contact.yaml")
        return 1

    # Initialize generators
    pgtap_gen = PgTAPGenerator()
    pytest_gen = PytestGenerator()
    parser = SpecQLParser()

    # Prepare output directory
    output_path = Path(output_dir)
    if not preview:
        output_path.mkdir(parents=True, exist_ok=True)

    # Track statistics
    stats = {
        "entities_processed": 0,
        "pgtap_files": 0,
        "pytest_files": 0,
        "total_files": 0,
        "errors": [],
    }

    # Process each entity file
    for entity_file_path in entity_files:
        try:
            entity_file = Path(entity_file_path)

            if verbose:
                click.echo(f"\n📄 Processing {entity_file.name}...")

            # Parse entity YAML
            with open(entity_file, "r") as f:
                entity_content = f.read()

            # Parse with SpecQL parser
            try:
                entity = parser.parse(entity_content)
            except Exception:
                # Try as dict
                entity_dict = yaml.safe_load(entity_content)
                entity = entity_dict  # We'll use dict directly

            # Ensure entity is a dict for compatibility
            if not isinstance(entity, dict):
                entity_name = getattr(entity, "name", "Unknown")
                entity_schema = getattr(entity, "schema", "public")
                entity = {"entity": entity_name, "schema": entity_schema}

            # Extract entity config
            entity_config = _build_entity_config(entity, entity_file)

            if verbose:
                click.echo(f"   Entity: {entity_config['entity_name']}")
                click.echo(f"   Schema: {entity_config['schema_name']}")

            # Generate tests based on type
            generated_files = []

            if test_type in ["all", "pgtap"]:
                pgtap_files = _generate_pgtap_tests(
                    pgtap_gen,
                    entity_config,
                    entity,
                    output_path,
                    preview,
                    verbose,
                    overwrite,
                )
                generated_files.extend(pgtap_files)
                stats["pgtap_files"] += len(pgtap_files)

            if test_type in ["all", "pytest"]:
                pytest_files = _generate_pytest_tests(
                    pytest_gen,
                    entity_config,
                    entity,
                    output_path,
                    preview,
                    verbose,
                    overwrite,
                )
                generated_files.extend(pytest_files)
                stats["pytest_files"] += len(pytest_files)

            stats["entities_processed"] += 1
            stats["total_files"] += len(generated_files)

            if preview:
                click.echo(
                    f"\n   📋 Would generate {len(generated_files)} test file(s):"
                )
                for file_info in generated_files:
                    click.echo(f"      • {file_info['path']}")
            else:
                click.echo(f"   ✅ Generated {len(generated_files)} test file(s)")

        except Exception as e:
            error_msg = f"Failed to process {entity_file_path}: {e}"
            stats["errors"].append(error_msg)
            click.secho(f"   ❌ {error_msg}", fg="red")
            if verbose:
                import traceback

                traceback.print_exc()
            continue

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("📊 Test Generation Summary")
    click.echo("=" * 60)
    click.echo(f"Entities processed: {stats['entities_processed']}")
    click.echo(f"pgTAP test files:   {stats['pgtap_files']}")
    click.echo(f"pytest test files:  {stats['pytest_files']}")
    click.echo(f"Total test files:   {stats['total_files']}")

    if stats["errors"]:
        click.echo(f"\n⚠️  Errors: {len(stats['errors'])}")
        for error in stats["errors"]:
            click.echo(f"   • {error}")

    if preview:
        click.secho("\n🔍 Preview mode - no files were written", fg="yellow")
    else:
        click.secho(f"\n✅ Tests generated in {output_dir}/", fg="green", bold=True)

    return 1 if stats["errors"] else 0


@click.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--type",
    "test_type",
    type=click.Choice(["all", "pgtap", "pytest"], case_sensitive=False),
    default="all",
    help="Type of tests to generate (default: all)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="tests",
    help="Output directory for generated tests (default: tests/)",
)
@click.option(
    "--preview",
    is_flag=True,
    help="Preview mode - show what would be generated without writing files",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed generation progress")
@click.option("--overwrite", is_flag=True, help="Overwrite existing test files")
def generate_tests(
    entity_files: tuple[str, ...],
    test_type: str,
    output_dir: str,
    preview: bool,
    verbose: bool,
    overwrite: bool,
) -> int:
    """
    Generate test files from SpecQL entity definitions.

    Generates comprehensive test suites including:
    - pgTAP tests: Structure, CRUD, constraints, actions
    - pytest tests: Integration tests for CRUD and actions

    Examples:

        # Generate all tests for Contact entity
        specql generate-tests entities/contact.yaml

        # Generate only pgTAP tests
        specql generate-tests entities/*.yaml --type pgtap

        # Generate pytest tests to custom directory
        specql generate-tests entities/ --type pytest --output-dir tests/integration/

        # Preview what would be generated
        specql generate-tests entities/contact.yaml --preview
    """
    return _generate_tests_core(
        entity_files=entity_files,
        test_type=test_type,
        output_dir=output_dir,
        preview=preview,
        verbose=verbose,
        overwrite=overwrite,
    )


def _build_entity_config(entity, entity_file: Path) -> dict:
    """Build entity configuration from parsed entity."""
    # Handle both UniversalEntity and dict
    if isinstance(entity, dict):
        entity_name = entity.get("entity", entity_file.stem.capitalize())
        schema_name = entity.get("schema", "public")
    else:
        # For EntityDefinition and similar objects, try to extract name safely
        if hasattr(entity, "__dict__") and "name" in entity.__dict__:
            # Access dataclass field directly to avoid property overrides
            name_value = entity.__dict__["name"]
        else:
            name_value = getattr(entity, "name", entity_file.stem.capitalize())

        # Ensure name_value is a string
        if isinstance(name_value, str):
            entity_name = name_value
        else:
            # If name_value is not a string, try to extract name from it
            if hasattr(name_value, "__dict__") and "name" in name_value.__dict__:
                entity_name = name_value.__dict__["name"]
            elif hasattr(name_value, "name") and isinstance(name_value.name, str):
                entity_name = name_value.name
            else:
                entity_name = str(name_value)

        schema_name = getattr(entity, "schema", "public")

    table_name = f"tb_{entity_name.lower()}"

    return {
        "entity_name": entity_name,
        "schema_name": schema_name,
        "table_name": table_name,
        "default_tenant_id": "01232122-0000-0000-2000-000000000001",
        "default_user_id": "01232122-0000-0000-2000-000000000002",
    }


def _generate_pgtap_tests(
    generator: PgTAPGenerator,
    entity_config: dict,
    entity,
    output_path: Path,
    preview: bool,
    verbose: bool,
    overwrite: bool,
) -> List[dict]:
    """Generate pgTAP test files."""
    entity_name = entity_config["entity_name"]
    # Ensure entity_name is a string (handle case where it might be the entity object)
    if not isinstance(entity_name, str):
        if hasattr(entity_name, "name") and isinstance(
            getattr(entity_name, "name", None), str
        ):
            entity_name = entity_name.name
        else:
            entity_name = str(entity_name)
    generated = []

    # 1. Structure tests
    structure_sql = generator.generate_structure_tests(entity_config)
    structure_file = output_path / f"test_{entity_name.lower()}_structure.sql"

    if not preview:
        if overwrite or not structure_file.exists():
            structure_file.write_text(structure_sql)
            if verbose:
                click.echo(f"      ✓ {structure_file.name}")

    generated.append(
        {
            "path": str(structure_file.relative_to(output_path.parent)),
            "type": "pgtap_structure",
        }
    )

    # 2. CRUD tests
    field_mappings = _extract_field_mappings(entity)
    crud_sql = generator.generate_crud_tests(entity_config, field_mappings)
    crud_file = output_path / f"test_{entity_name.lower()}_crud.sql"

    if not preview:
        if overwrite or not crud_file.exists():
            crud_file.write_text(crud_sql)
            if verbose:
                click.echo(f"      ✓ {crud_file.name}")

    generated.append(
        {"path": str(crud_file.relative_to(output_path.parent)), "type": "pgtap_crud"}
    )

    # 3. Action tests (if actions exist)
    actions = _extract_actions(entity)
    if actions:
        action_scenarios = _build_action_scenarios(actions)
        action_sql = generator.generate_action_tests(
            entity_config, actions, action_scenarios
        )
        action_file = output_path / f"test_{entity_name.lower()}_actions.sql"

        if not preview:
            if overwrite or not action_file.exists():
                action_file.write_text(action_sql)
                if verbose:
                    click.echo(f"      ✓ {action_file.name}")

        generated.append(
            {
                "path": str(action_file.relative_to(output_path.parent)),
                "type": "pgtap_actions",
            }
        )

    return generated


def _generate_pytest_tests(
    generator: PytestGenerator,
    entity_config: dict,
    entity,
    output_path: Path,
    preview: bool,
    verbose: bool,
    overwrite: bool,
) -> List[dict]:
    """Generate pytest test files."""
    entity_name = entity_config["entity_name"]
    # Ensure entity_name is a string (handle case where it might be the entity object)
    if not isinstance(entity_name, str):
        if hasattr(entity_name, "name") and isinstance(
            getattr(entity_name, "name", None), str
        ):
            entity_name = entity_name.name
        else:
            entity_name = str(entity_name)
    generated = []

    # Integration tests
    actions = _extract_actions(entity)
    pytest_code = generator.generate_pytest_integration_tests(entity_config, actions)
    pytest_file = output_path / f"test_{entity_name.lower()}_integration.py"

    if not preview:
        if overwrite or not pytest_file.exists():
            pytest_file.write_text(pytest_code)
            if verbose:
                click.echo(f"      ✓ {pytest_file.name}")

    generated.append(
        {
            "path": str(pytest_file.relative_to(output_path.parent)),
            "type": "pytest_integration",
        }
    )

    return generated


def _extract_field_mappings(entity) -> List[dict]:
    """Extract field mappings from entity."""
    mappings = []

    # Handle both dict and object
    if isinstance(entity, dict):
        fields = entity.get("fields", {})
        if isinstance(fields, dict):
            for field_name, field_def in fields.items():
                field_type = (
                    field_def
                    if isinstance(field_def, str)
                    else field_def.get("type", "text")
                )
                mappings.append(
                    {
                        "field_name": field_name,
                        "field_type": field_type,
                        "generator_type": "random",
                    }
                )
    else:
        fields = getattr(entity, "fields", [])
        for field in fields:
            mappings.append(
                {
                    "field_name": field.name,
                    "field_type": field.type.value
                    if hasattr(field.type, "value")
                    else str(field.type),
                    "generator_type": "random",
                }
            )

    return mappings


def _extract_actions(entity) -> List[dict]:
    """Extract actions from entity."""
    actions = []

    # Handle both dict and object
    if isinstance(entity, dict):
        entity_actions = entity.get("actions", [])
        for action in entity_actions:
            if isinstance(action, dict):
                actions.append(
                    {
                        "name": action.get("name"),
                        "description": action.get("description", ""),
                    }
                )
            else:
                actions.append(
                    {
                        "name": getattr(action, "name"),
                        "description": getattr(action, "description", ""),
                    }
                )
    else:
        entity_actions = getattr(entity, "actions", [])
        for action in entity_actions:
            actions.append(
                {"name": action.name, "description": getattr(action, "description", "")}
            )

    return actions


def _build_action_scenarios(actions: List[dict]) -> List[dict]:
    """Build basic test scenarios for actions."""
    scenarios = []

    for action in actions:
        scenarios.append(
            {
                "target_action": action["name"],
                "scenario_name": f"{action['name']}_happy_path",
                "expected_result": "success",
                "setup_sql": f"-- Setup for {action['name']} test",
            }
        )

    return scenarios
