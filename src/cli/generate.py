#!/usr/bin/env python3
"""
SpecQL Generate CLI
Generate SQL migrations from SpecQL entity definitions
"""

from pathlib import Path

import click

from src.cli.orchestrator import CLIOrchestrator
from src.core.ast_models import Action, Entity, EntityDefinition
from src.core.specql_parser import SpecQLParser
from src.testing.pgtap.pgtap_generator import PgTAPGenerator
from src.testing.pytest.pytest_generator import PytestGenerator
from src.utils.logger import configure_logging, get_team_logger


def convert_entity_definition_to_entity(entity_def: EntityDefinition) -> Entity:
    """Convert EntityDefinition to Entity for backward compatibility

    This function bridges the gap between the parsed EntityDefinition
    (from SpecQL YAML) and the Entity object used by code generators.

    Key conversions:
    - ActionDefinition → Action (with impact placeholder)
    - organization.table_code → entity.table_code (for numbering system)

    Args:
        entity_def: Parsed entity definition from SpecQL YAML

    Returns:
        Entity object ready for code generation

    Note:
        If entity_def.organization.table_code is present, it will be
        extracted and set as entity.table_code for use in SQL comments,
        migration naming, and the table numbering registry.
    """
    # Convert ActionDefinition to Action
    actions = []
    for action_def in entity_def.actions:
        action = Action(
            name=action_def.name, steps=action_def.steps, impact=None
        )  # TODO: Convert impact dict to ActionImpact
        actions.append(action)

    # Extract table_code from organization if present
    table_code = None
    if entity_def.organization and entity_def.organization.table_code:
        table_code = entity_def.organization.table_code

    # Create Entity
    entity = Entity(
        name=entity_def.name,
        schema=entity_def.schema,
        table_code=table_code,
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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.option("--performance", is_flag=True, help="Enable performance monitoring and output metrics")
@click.option("--performance-output", type=click.Path(), help="Write performance metrics to specified JSON file")
def entities(
    entity_files: tuple,
    output_dir: str,
    foundation_only: bool,
    include_tv: bool,
    use_registry: bool,  # NEW
    output_format: str,  # NEW
    with_impacts: bool,  # NEW
    output_frontend: str,  # NEW
    verbose: bool,
    quiet: bool,
    performance: bool,
    performance_output: str,
):
    """Generate PostgreSQL migrations from SpecQL YAML files"""

    # Configure logging based on verbosity flags
    import logging
    if quiet:
        configure_logging(level=logging.ERROR)
    elif verbose:
        configure_logging(level=logging.DEBUG, verbose=True)
    else:
        configure_logging(level=logging.INFO)

    logger = get_team_logger("Team E", __name__)
    logger.info(f"Starting generation for {len(entity_files)} entity file(s)")

    # Create orchestrator with registry support and performance monitoring
    orchestrator = CLIOrchestrator(
        use_registry=use_registry,
        output_format=output_format,
        enable_performance_monitoring=performance
    )

    # Generate migrations
    logger.debug(f"Output directory: {output_dir}")
    logger.debug(f"Foundation only: {foundation_only}, Include TV: {include_tv}")
    result = orchestrator.generate_from_files(
        entity_files=list(entity_files),
        output_dir=output_dir,
        foundation_only=foundation_only,
        include_tv=include_tv,
    )

    logger.info(f"Generated {len(result.migrations)} migration file(s)")

    # Generate frontend code if requested
    if output_frontend:
        logger.info(f"Generating frontend code to {output_frontend}")
        click.secho("🔧 Generating frontend code...", fg="blue", bold=True)

        try:
            from src.generators.frontend import (
                ApolloHooksGenerator,
                MutationDocsGenerator,
                MutationImpactsGenerator,
                TypeScriptTypesGenerator,
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
                logger.debug("Generating mutation impacts JSON")
                impacts_gen = MutationImpactsGenerator(frontend_dir)
                impacts_gen.generate_impacts(entities)
                click.echo("  ✅ Generated mutation-impacts.json")

            # Generate TypeScript types
            logger.debug("Generating TypeScript types")
            types_gen = TypeScriptTypesGenerator(frontend_dir)
            types_gen.generate_types(entities)
            click.echo("  ✅ Generated types.ts")

            # Generate Apollo hooks
            logger.debug("Generating Apollo hooks")
            hooks_gen = ApolloHooksGenerator(frontend_dir)
            hooks_gen.generate_hooks(entities)
            click.echo("  ✅ Generated hooks.ts")

            # Generate documentation
            logger.debug("Generating mutation documentation")
            docs_gen = MutationDocsGenerator(frontend_dir)
            docs_gen.generate_docs(entities)
            click.echo("  ✅ Generated mutations.md")

            logger.info("Frontend code generation completed successfully")
            click.secho(f"✅ Frontend code generated in {output_frontend}", fg="green", bold=True)

        except ImportError as e:
            logger.error(f"Frontend generators not available: {e}")
            click.secho(f"❌ Frontend generators not available: {e}", fg="red")
            return 1
        except Exception as e:
            logger.error(f"Frontend generation failed: {e}", exc_info=True)
            click.secho(f"❌ Frontend generation failed: {e}", fg="red")
            return 1

    # Report results
    if result.errors:
        logger.error(f"Generation completed with {len(result.errors)} error(s)")
        click.secho(f"❌ {len(result.errors)} error(s):", fg="red", bold=True)
        for error in result.errors:
            click.echo(f"  {error}")
        return 1

    logger.info("Generation completed successfully")

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

    # Output performance metrics if enabled
    if performance and orchestrator.perf_monitor:
        from src.utils.performance_monitor import get_performance_monitor

        perf_monitor = get_performance_monitor()
        metrics = perf_monitor.get_metrics()

        if performance_output:
            # Write to file
            output_file = Path(performance_output)
            metrics.write_to_file(output_file)
            click.secho(f"\n📊 Performance metrics written to {performance_output}", fg="blue", bold=True)
        else:
            # Print to stdout
            click.secho("\n📊 Performance Metrics:", fg="blue", bold=True)
            click.echo(metrics.to_json(indent=2))

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
                click.echo("    📊 Generating pgTAP tests...")
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
                click.echo("    🐍 Generating Pytest tests...")
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
        click.echo("\n💡 Run pgTAP tests: pg_prove tests/pgtap/*.sql")
        click.echo("💡 Run Pytest tests: pytest tests/pytest/")

    return 0


def main():
    """Entry point for specql generate command"""
    cli()


if __name__ == "__main__":
    main()
