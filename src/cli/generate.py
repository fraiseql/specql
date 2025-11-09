#!/usr/bin/env python3
"""
SpecQL Generate CLI
Generate SQL migrations from SpecQL entity definitions
"""

import click
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator
from src.core.specql_parser import SpecQLParser
from src.generators.schema_orchestrator import SchemaOrchestrator
from src.core.ast_models import Entity, Action, EntityDefinition
from src.testing.pgtap.pgtap_generator import PgTAPGenerator
from src.testing.pytest.pytest_generator import PytestGenerator


def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for orchestrator compatibility"""
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )  # TODO: Convert impact dict to ActionImpact
        actions.append(action)

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        description=entity_def.description,
        fields=entity_def.fields,
        actions=actions,
        agents=entity_def.agents,
        organization=entity_def.organization,
    )

    return entity


@click.group()
def cli():
    """SpecQL Generator CLI"""
    pass


@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output-dir", default="migrations", help="Output directory")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option(
    "--use-registry", is_flag=True, help="Use hexadecimal registry for table codes and paths"
)  # NEW
@click.option(
    "--output-format",
    type=click.Choice(["hierarchical", "confiture"]),
    default="hierarchical",
    help="Output format: hierarchical (full registry paths) or confiture (db/schema/ flat)",
)  # NEW
@click.option(
    "--with-impacts",
    is_flag=True,
    help="Generate mutation impacts JSON for frontend cache management",
)  # NEW
@click.option(
    "--output-frontend",
    type=click.Path(),
    help="Generate frontend code (TypeScript types, Apollo hooks, docs) to specified directory",
)  # NEW
def entities(
    entity_files: tuple,
    output_dir: str,
    foundation_only: bool,
    include_tv: bool,
    use_registry: bool,  # NEW
    output_format: str,  # NEW
    with_impacts: bool,  # NEW
    output_frontend: str,  # NEW
):
    """Generate PostgreSQL migrations from SpecQL YAML files"""

    # Create orchestrator with registry support
    orchestrator = CLIOrchestrator(use_registry=use_registry, output_format=output_format)

    # Generate migrations
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir=output_dir,
        foundation_only=foundation_only,
        include_tv=include_tv,
    )

    # Generate frontend code if requested
    if output_frontend:
        click.secho("🔧 Generating frontend code...", fg="blue", bold=True)

        try:
            from src.generators.frontend import (
                MutationImpactsGenerator,
                TypeScriptTypesGenerator,
                ApolloHooksGenerator,
                MutationDocsGenerator,
            )

            frontend_dir = Path(output_frontend)

            # Parse entities for frontend generators
            parser = SpecQLParser()
            entities = []
            for file_path in entity_files:
                content = Path(file_path).read_text()
                entity_def = parser.parse(content)
                entities.append(convert_entity_definition_to_entity(entity_def))

            # Generate mutation impacts if requested
            if with_impacts:
                impacts_gen = MutationImpactsGenerator(frontend_dir)
                impacts_gen.generate_impacts(entities)
                click.echo("  ✅ Generated mutation-impacts.json")

            # Generate TypeScript types
            types_gen = TypeScriptTypesGenerator(frontend_dir)
            types_gen.generate_types(entities)
            click.echo("  ✅ Generated types.ts")

            # Generate Apollo hooks
            hooks_gen = ApolloHooksGenerator(frontend_dir)
            hooks_gen.generate_hooks(entities)
            click.echo("  ✅ Generated hooks.ts")

            # Generate documentation
            docs_gen = MutationDocsGenerator(frontend_dir)
            docs_gen.generate_docs(entities)
            click.echo("  ✅ Generated mutations.md")

            click.secho(f"✅ Frontend code generated in {output_frontend}", fg="green", bold=True)

        except ImportError as e:
            click.secho(f"❌ Frontend generators not available: {e}", fg="red")
            return 1
        except Exception as e:
            click.secho(f"❌ Frontend generation failed: {e}", fg="red")
            return 1

    # Report results
    if result.errors:
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red", bold=True)
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    if use_registry:
        format_desc = "hierarchical" if output_format == "hierarchical" else "Confiture-compatible"
        click.secho(
            f"✅ Generated {len(result.migrations)} file(s) with hexadecimal codes ({format_desc} format)",
            fg="green",
            bold=True,
        )

        # Show generated structure
        click.echo("\nGenerated files:")
        for migration in result.migrations:
            if migration.table_code:
                click.echo(f"  [{migration.table_code}] {migration.path}")
            else:
                click.echo(f"  {migration.path}")
    else:
        click.secho(f"✅ Generated {len(result.migrations)} migration(s)", fg="green", bold=True)

    if result.warnings:
        click.secho(f"\n⚠️  {len(result.warnings)} warning(s):", fg="yellow")
        for warning in result.warnings:
            click.echo(f"  {warning}")

    return 0


@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output-dir", default="tests", help="Output directory for generated tests")
@click.option(
    "--test-type",
    type=click.Choice(["pgtap", "pytest", "both"]),
    default="both",
    help="Type of tests to generate: pgtap, pytest, or both",
)
@click.option("--with-metadata", is_flag=True, help="Generate test metadata alongside tests")
def tests(
    entity_files: tuple,
    output_dir: str,
    test_type: str,
    with_metadata: bool,
):
    """Generate automated tests from SpecQL YAML files

    Generates comprehensive test suites including:
    - pgTAP tests for database schema validation and constraints
    - Pytest integration tests for end-to-end workflows
    - Test metadata for advanced scenarios
    """

    click.secho("🧪 Generating automated tests...", fg="blue", bold=True)

    # Parse SpecQL files
    parser = SpecQLParser()
    entities = []

    for file_path in entity_files:
        click.echo(f"  📄 Parsing {file_path}...")
        try:
            content = Path(file_path).read_text()
            entity_def = parser.parse(content)
            entity = convert_entity_definition_to_entity(entity_def)
            entities.append(entity)
        except Exception as e:
            click.secho(f"❌ Failed to parse {file_path}: {e}", fg="red")
            return 1

    if not entities:
        click.secho("❌ No valid entities found", fg="red")
        return 1

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Generate tests for each entity
    for entity in entities:
        click.echo(f"  🏗️  Generating tests for {entity.name}...")

        # Build entity config for generators
        entity_config = {
            "entity_name": entity.name,
            "schema_name": entity.schema,
            "table_name": f"tb_{entity.name.lower()}",
            "default_tenant_id": "01232122-0000-0000-2000-000000000001",
            "default_user_id": "01232122-0000-0000-2000-000000000002",
        }

        # Extract actions from entity
        actions = []
        for action in entity.actions:
            actions.append(
                {
                    "name": action.name,
                    "description": getattr(action, "description", f"Action {action.name}"),
                }
            )

        try:
            # Generate pgTAP tests
            if test_type in ["pgtap", "both"]:
                click.echo(f"    📊 Generating pgTAP tests...")
                pgtap_gen = PgTAPGenerator()

                # Structure tests
                structure_sql = pgtap_gen.generate_structure_tests(entity_config)
                pgtap_file = output_path / "pgtap" / f"{entity.name.lower()}_test.sql"
                pgtap_file.parent.mkdir(parents=True, exist_ok=True)
                pgtap_file.write_text(f"""-- Auto-generated pgTAP tests for {entity.name} entity
-- Generated from {Path(entity_files[0]).name}

{structure_sql}

-- CRUD Tests
{pgtap_gen.generate_crud_tests(entity_config, [])}

-- Action Tests
{pgtap_gen.generate_action_tests(entity_config, actions, [])}

-- Constraint Tests
{pgtap_gen.generate_constraint_tests(entity_config, [])}
""")
                generated_files.append(str(pgtap_file))

            # Generate Pytest tests
            if test_type in ["pytest", "both"]:
                click.echo(f"    🐍 Generating Pytest tests...")
                pytest_gen = PytestGenerator()

                pytest_code = pytest_gen.generate_pytest_integration_tests(entity_config, actions)
                pytest_file = output_path / "pytest" / f"test_{entity.name.lower()}_integration.py"
                pytest_file.parent.mkdir(parents=True, exist_ok=True)
                pytest_file.write_text(pytest_code)
                generated_files.append(str(pytest_file))

        except Exception as e:
            click.secho(f"❌ Failed to generate tests for {entity.name}: {e}", fg="red")
            return 1

    # Generate test metadata if requested
    if with_metadata:
        click.echo("  📋 Generating test metadata...")
        # TODO: Implement metadata generation
        pass

    # Report results
    click.secho(f"✅ Generated {len(generated_files)} test file(s)", fg="green", bold=True)

    click.echo("\nGenerated files:")
    for file_path in generated_files:
        click.echo(f"  📄 {file_path}")

    if test_type == "both":
        click.echo(f"\n💡 Run pgTAP tests: pg_prove tests/pgtap/*.sql")
        click.echo(f"💡 Run Pytest tests: pytest tests/pytest/")

    return 0


def main():
    """Entry point for specql generate command"""
    cli()


if __name__ == "__main__":
    main()
