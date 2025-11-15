#!/usr/bin/env python3
"""
SpecQL Generate CLI
Generate SQL migrations from SpecQL entity definitions
"""

from pathlib import Path

import click

from src.cli.orchestrator import CLIOrchestrator
from src.cli.help_text import get_generate_help_text
from src.core.ast_models import Action, ActionImpact, Entity, EntityDefinition
from src.core.specql_parser import SpecQLParser
from src.testing.pgtap.pgtap_generator import PgTAPGenerator
from src.testing.pytest.pytest_generator import PytestGenerator


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
        # Convert impact dict to ActionImpact if present
        impact = None
        if action_def.impact:
            impact = ActionImpact.from_dict(action_def.impact, entity_def.name)

        action = Action(
            name=action_def.name,
            steps=action_def.steps,
            impact=impact,
            cdc=action_def.cdc,
        )
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


@cli.command(help=get_generate_help_text())
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output-dir", default="migrations", help="Output directory")
@click.option("--foundation-only", is_flag=True, help="Generate only app foundation")
@click.option("--include-tv", is_flag=True, help="Generate table views")
@click.option(
    "--framework",
    type=click.Choice(["fraiseql", "django", "rails", "prisma"]),
    default="fraiseql",
    help="Target framework (default: fraiseql)",
)  # NEW
@click.option(
    "--target",
    type=click.Choice(["postgresql", "python_django", "python_sqlalchemy", "rust"]),
    help="Target language for pattern-based code generation",
)  # NEW
@click.option(
    "--use-registry",
    is_flag=True,
    default=True,
    help="Use hexadecimal registry for table codes and paths",
)  # CHANGED: Default to True
@click.option(
    "--output-format",
    type=click.Choice(["hierarchical", "confiture"]),
    default="hierarchical",
    help="Output format: hierarchical (full registry paths) or confiture (db/schema/ flat)",
)  # NEW
@click.option(
    "--hierarchical/--flat",
    default=True,
    help="Use hierarchical file structure (default) or flat structure",
)  # NEW
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be generated without writing files",
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
@click.option(
    "--with-query-patterns",
    is_flag=True,
    help="Generate SQL views from query patterns defined in entity YAML",
)  # NEW
@click.option(
    "--with-audit-cascade",
    is_flag=True,
    help="Integrate cascade data with audit trail for complete mutation history",
)  # NEW
@click.option(
    "--with-outbox",
    is_flag=True,
    help="Generate CDC outbox table and functions for event streaming",
)  # NEW
@click.option(
    "--dev", is_flag=True, help="Development mode: flat structure in db/schema/"
)
@click.option("--no-tv", is_flag=True, help="Skip table view (tv_*) generation")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed generation progress")
@click.option(
    "--performance",
    is_flag=True,
    help="Enable performance monitoring and output metrics",
)
@click.option(
    "--performance-output",
    type=click.Path(),
    help="Write performance metrics to specified JSON file",
)
def entities(
    entity_files: tuple,
    output_dir: str,
    foundation_only: bool,
    include_tv: bool,
    framework: str,  # NEW
    target: str,  # NEW
    use_registry: bool,  # NEW
    output_format: str,  # NEW
    hierarchical: bool,  # NEW
    dry_run: bool,  # NEW
    with_impacts: bool,  # NEW
    output_frontend: str,  # NEW
    with_query_patterns: bool,  # NEW
    with_audit_cascade: bool,  # NEW
    with_outbox: bool,  # NEW
    dev: bool,  # NEW
    no_tv: bool,  # NEW
    verbose: bool,
    performance: bool,
    performance_output: str,
):
    """Generate production-ready PostgreSQL schema from SpecQL YAML entity definitions.

    By default, generates hierarchical directory structure with db/schema/ prefix,
    ready for migration deployment.

    COMMON EXAMPLES:

       # Generate all entities hierarchically (default, production-ready)
       specql generate entities/**/*.yaml
       # → Hierarchical structure: 0_schema/01_write_side/012_crm/...

       # Generate in flat structure (legacy)
       specql generate entities/**/*.yaml --flat
       # → Flat structure: db/schema/10_tables/...

       # Dry run to preview what would be generated
       specql generate entities/**/*.yaml --dry-run --verbose

       # Generate for specific framework
       specql generate entities/**/*.yaml --framework django
       # → Uses Django defaults: models.py, admin.py, no tv_*

       # Generate specific entities
       specql generate entities/catalog/*.yaml

       # Custom output directory
       specql generate entities/**/*.yaml --output migrations/v2/

       # Development mode (flat structure for confiture)
       specql generate entities/**/*.yaml --dev

       # List available frameworks
       specql list-frameworks

    OUTPUT FORMATS:

       hierarchical (default, --hierarchical)
         Organized directory structure matching domain/subdomain/entity hierarchy.
         Best for: Production migrations, large codebases, team collaboration

       flat (--flat or --dev)
         Flat directory structure grouped by object type.
         Best for: Development with confiture, simple projects

       dry-run (--dry-run)
         Show what would be generated without writing any files.
         Best for: Previewing changes, validation

    For comprehensive help, run: specql generate --help
    """

    # Handle pattern-based multi-language generation
    if target:
        from tests.integration.test_pattern_library_multilang import (
            MultiLanguageGenerator,
        )

        click.secho(
            f"🔧 Generating {target} code using pattern library...",
            fg="blue",
            bold=True,
        )

        parser = SpecQLParser()
        generator = MultiLanguageGenerator()

        for entity_file in entity_files:
            with open(entity_file) as f:
                yaml_content = f.read()
            entity_def = parser.parse(yaml_content)

            if target == "postgresql":
                code = generator.generate_postgresql(entity_def)
            elif target == "python_django":
                code = generator.generate_django(entity_def)
            elif target == "python_sqlalchemy":
                code = generator.generate_sqlalchemy(entity_def)
            elif target == "rust":
                from src.generators.rust.rust_generator_orchestrator import (
                    RustGeneratorOrchestrator,
                )

                orchestrator = RustGeneratorOrchestrator()
                orchestrator.generate(
                    entity_files=[Path(entity_file)],
                    output_dir=Path(output_dir),
                    with_handlers=True,
                    with_routes=True,
                )
                click.secho(f"✅ Rust backend generated in {output_dir}", fg="green")
                return
            else:
                raise click.ClickException(f"Unsupported target: {target}")

            # Write to output file
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = (
                output_path / f"{entity_def.name.lower()}_{target}.sql"
                if target == "postgresql"
                else f"{entity_def.name.lower()}_{target}.py"
            )

            if dry_run:
                click.echo(f"Would write to {output_file}:")
                click.echo(code[:500] + "..." if len(code) > 500 else code)
            else:
                with open(output_file, "w") as f:
                    f.write(code)
                click.secho(f"✅ Generated {output_file}", fg="green")

        return

    # Apply development mode overrides
    if dev:
        use_registry = False
        output_format = "confiture"
        output_dir = "db/schema"
        include_tv = False

    # Apply --hierarchical/--flat override
    if not hierarchical:
        output_format = "confiture"
    else:
        output_format = "hierarchical"

    # Apply --no-tv override
    if no_tv:
        include_tv = False

    # Create orchestrator with framework-aware defaults and performance monitoring
    orchestrator = CLIOrchestrator(
        use_registry=use_registry,
        output_format=output_format,
        verbose=verbose,
        framework=framework,
        enable_performance_monitoring=performance,
    )

    # Generate migrations
    if hierarchical and use_registry:
        # Use new hierarchical generation
        result = orchestrator.generate_hierarchical(
            entity_files=list(entity_files), output_dir=output_dir, dry_run=dry_run
        )
    else:
        # Use legacy generation
        result = orchestrator.generate_from_files(
            entity_files=list(entity_files),
            output_dir=output_dir,
            foundation_only=foundation_only,
            include_tv=include_tv,
            with_query_patterns=with_query_patterns,
            with_audit_cascade=with_audit_cascade,
            with_outbox=with_outbox,
        )

    # Generate frontend code if requested
    if output_frontend:
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

            click.secho(
                f"✅ Frontend code generated in {output_frontend}",
                fg="green",
                bold=True,
            )

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
        format_desc = (
            "hierarchical"
            if output_format == "hierarchical"
            else "Confiture-compatible"
        )
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
        click.secho(
            f"✅ Generated {len(result.migrations)} migration(s)", fg="green", bold=True
        )

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
            click.secho(
                f"\n📊 Performance metrics written to {performance_output}",
                fg="blue",
                bold=True,
            )
        else:
            # Print to stdout
            click.secho("\n📊 Performance Metrics:", fg="blue", bold=True)
            click.echo(metrics.to_json(indent=2))

    return 0


@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--backends",
    default=["postgresql"],
    multiple=True,
    help="Target backends to generate for (e.g., postgresql, django, rails)",
)
@click.option(
    "--output-dir",
    default="generated",
    help="Base output directory for generated code",
)
def universal(
    entity_files: tuple,
    backends: tuple,
    output_dir: str,
):
    """Generate code for multiple frameworks from SpecQL YAML files

    This command uses the new Universal AST and adapter system to generate
    code for any supported backend framework.

    Examples:
        specql generate universal entities/contact.yaml --backends=postgresql
        specql generate universal entities/*.yaml --backends=postgresql,django
    """

    click.secho("🚀 Generating universal code...", fg="blue", bold=True)

    # Import here to avoid circular imports
    from src.core.specql_parser import SpecQLParser
    from src.adapters.registry import get_registry

    # Initialize parser and registry
    parser = SpecQLParser()
    registry = get_registry()
    registry.auto_discover()

    # Parse SpecQL files to Universal AST
    entities = []
    for file_path in entity_files:
        click.echo(f"  📄 Parsing {file_path}...")
        try:
            content = Path(file_path).read_text()
            entity = parser.parse_universal(content)
            entities.append(entity)
        except Exception as e:
            click.secho(f"❌ Failed to parse {file_path}: {e}", fg="red")
            return 1

    if not entities:
        click.secho("❌ No valid entities found", fg="red")
        return 1

    # Create universal schema
    from src.core.universal_ast import UniversalSchema

    schema = UniversalSchema(
        entities=entities, composite_types={}, tenant_mode="multi_tenant"
    )

    # Generate for each backend
    total_files = 0
    for backend_name in backends:
        click.echo(f"  🏗️  Generating for {backend_name}...")

        try:
            adapter = registry.get_adapter(backend_name)
            generated_files = adapter.generate_full_schema(schema)

            # Create output directory for this backend
            backend_dir = Path(output_dir) / backend_name
            backend_dir.mkdir(parents=True, exist_ok=True)

            # Write generated files
            for gen_file in generated_files:
                file_path = backend_dir / gen_file.file_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(gen_file.content)
                click.echo(f"    ✅ {gen_file.file_path}")

            total_files += len(generated_files)

        except ValueError as e:
            click.secho(f"❌ Unknown backend '{backend_name}': {e}", fg="red")
            click.echo("Available backends:")
            for available in registry.list_adapters():
                click.echo(f"  - {available}")
            return 1
        except Exception as e:
            click.secho(f"❌ Failed to generate for {backend_name}: {e}", fg="red")
            return 1

    click.secho(
        f"✅ Generated {total_files} file(s) across {len(backends)} backend(s)",
        fg="green",
        bold=True,
    )
    return 0


@cli.group()
def jobs():
    """Manage call_service jobs"""
    pass


@jobs.command()
@click.option("--service", help="Filter by service name")
@click.option("--operation", help="Filter by operation name")
@click.option(
    "--status",
    type=click.Choice(["pending", "running", "completed", "failed", "cancelled"]),
    help="Filter by job status",
)
@click.option("--limit", default=50, help="Maximum number of jobs to show")
def list(service: str, operation: str, status: str, limit: int):
    """List jobs with optional filtering"""
    click.secho("🔍 Listing jobs...", fg="blue", bold=True)

    # Build query conditions
    conditions = []
    params = []

    if service:
        conditions.append("service_name = %s")
        params.append(service)

    if operation:
        conditions.append("operation = %s")
        params.append(operation)

    if status:
        conditions.append("status = %s")
        params.append(status)

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    # This would connect to database and query jobs
    # For now, just show the query that would be executed
    query = f"""
SELECT
    id,
    service_name,
    operation,
    status,
    created_at,
    started_at,
    completed_at
FROM jobs.tb_job_run
WHERE {where_clause}
ORDER BY created_at DESC
LIMIT {limit}
"""

    click.echo("Query that would be executed:")
    click.echo(query)
    if params:
        click.echo(f"Parameters: {params}")

    click.secho(
        "💡 To implement: Connect to database and execute this query", fg="yellow"
    )


@jobs.command()
@click.argument("job_id")
def status(job_id: str):
    """Get detailed status of a specific job"""
    click.secho(f"🔍 Getting status for job {job_id}...", fg="blue", bold=True)

    query = """
SELECT
    id,
    service_name,
    operation,
    status,
    input_data,
    output_data,
    error_message,
    attempts,
    max_attempts,
    created_at,
    started_at,
    completed_at,
    updated_at
FROM jobs.tb_job_run
WHERE id = %s
"""

    click.echo("Query that would be executed:")
    click.echo(query)
    click.echo(f"Parameters: [{job_id}]")

    click.secho(
        "💡 To implement: Connect to database and execute this query", fg="yellow"
    )


@jobs.command()
@click.argument("job_id")
@click.option("--force", is_flag=True, help="Force cancellation even if running")
def cancel(job_id: str, force: bool):
    """Cancel a pending or running job"""
    click.secho(f"🛑 Cancelling job {job_id}...", fg="red", bold=True)

    if force:
        update_query = """
UPDATE jobs.tb_job_run
SET status = 'cancelled', updated_at = NOW()
WHERE id = %s
"""
    else:
        update_query = """
UPDATE jobs.tb_job_run
SET status = 'cancelled', updated_at = NOW()
WHERE id = %s AND status IN ('pending', 'running')
"""

    click.echo("Update query that would be executed:")
    click.echo(update_query)
    click.echo(f"Parameters: [{job_id}]")

    click.secho(
        "💡 To implement: Connect to database and execute this update", fg="yellow"
    )


@jobs.command()
@click.option("--service", help="Filter by service name")
@click.option("--operation", help="Filter by operation name")
@click.option("--hours", default=1, help="Look back hours")
def stats(service: str, operation: str, hours: int):
    """Show job statistics and health metrics"""
    click.secho("📊 Calculating job statistics...", fg="blue", bold=True)

    conditions = []
    params = []

    if service:
        conditions.append("service_name = %s")
        params.append(service)

    if operation:
        conditions.append("operation = %s")
        params.append(operation)

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    query = f"""
SELECT
    service_name,
    operation,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'completed')::numeric /
        NULLIF(COUNT(*), 0) * 100, 2
    ) as success_rate_percent,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::numeric(10,2) as avg_duration_sec
FROM jobs.tb_job_run
WHERE {where_clause}
    AND created_at > now() - interval '{hours} hours'
GROUP BY service_name, operation
ORDER BY success_rate_percent ASC
"""

    click.echo("Query that would be executed:")
    click.echo(query)
    if params:
        click.echo(f"Parameters: {params}")

    click.secho(
        "💡 To implement: Connect to database and execute this query", fg="yellow"
    )


@cli.command()
def list_backends():
    """List all available framework backends"""

    from src.adapters.registry import get_registry

    registry = get_registry()
    registry.auto_discover()

    backends = registry.list_adapters()

    if not backends:
        click.secho("❌ No backends available", fg="red")
        return 1

    click.secho("Available backends:", fg="blue", bold=True)
    for backend in sorted(backends):
        click.echo(f"  • {backend}")

    return 0


@cli.command()
@click.argument("entity_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--output-dir", default="tests", help="Output directory for generated tests"
)
@click.option(
    "--test-type",
    type=click.Choice(["pgtap", "pytest", "both"]),
    default="both",
    help="Type of tests to generate: pgtap, pytest, or both",
)
@click.option(
    "--with-metadata", is_flag=True, help="Generate test metadata alongside tests"
)
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
                    "description": getattr(
                        action, "description", f"Action {action.name}"
                    ),
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
                pgtap_file.write_text(
                    f"""-- Auto-generated pgTAP tests for {entity.name} entity
-- Generated from {Path(entity_files[0]).name}

{structure_sql}

-- CRUD Tests
{pgtap_gen.generate_crud_tests(entity_config, [])}

-- Action Tests
{pgtap_gen.generate_action_tests(entity_config, actions, [])}

-- Constraint Tests
{pgtap_gen.generate_constraint_tests(entity_config, [])}
"""
                )
                generated_files.append(str(pgtap_file))

            # Generate Pytest tests
            if test_type in ["pytest", "both"]:
                click.echo("    🐍 Generating Pytest tests...")
                pytest_gen = PytestGenerator()

                pytest_code = pytest_gen.generate_pytest_integration_tests(
                    entity_config, actions
                )
                pytest_file = (
                    output_path
                    / "pytest"
                    / f"test_{entity.name.lower()}_integration.py"
                )
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
    click.secho(
        f"✅ Generated {len(generated_files)} test file(s)", fg="green", bold=True
    )

    click.echo("\nGenerated files:")
    for file_path in generated_files:
        click.echo(f"  📄 {file_path}")

    if test_type == "both":
        click.echo("\n💡 Run pgTAP tests: pg_prove tests/pgtap/*.sql")
        click.echo("💡 Run Pytest tests: pytest tests/pytest/")

    return 0


@cli.command()
@click.argument("entity_file", type=click.Path(exists=True))
@click.option("--output-dir", default="generated/java", help="Output directory")
def generate_java(entity_file: str, output_dir: str):
    """Generate Spring Boot Java code from SpecQL entity"""
    from src.generators.java.java_generator_orchestrator import (
        JavaGeneratorOrchestrator,
    )

    click.secho("☕ Generating Spring Boot Java code...", fg="blue", bold=True)

    # Parse SpecQL
    parser = SpecQLParser()
    with open(entity_file) as f:
        entity = parser.parse_universal(f.read())

    # Generate Java code
    orchestrator = JavaGeneratorOrchestrator(output_dir)
    files = orchestrator.generate_all(entity)
    orchestrator.write_files(files)

    click.echo(f"✅ Generated {len(files)} Java files in {output_dir}")
    for file in files:
        click.echo(f"  - {file.path}")

    return 0


# Add CDC commands
from src.cli.cdc import cdc

cli.add_command(cdc)


def main():
    """Entry point for specql generate command"""
    cli()


if __name__ == "__main__":
    main()
# ruff: noqa: E402
