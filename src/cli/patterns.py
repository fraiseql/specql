"""
CLI commands for pattern library management.

Usage:
    specql patterns review-suggestions
    specql patterns show 1
    specql patterns approve 1
    specql patterns reject 1 --reason "Not reusable"
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
import json

from src.core.config import get_config
from src.infrastructure.repositories.postgresql_pattern_repository import PostgreSQLPatternRepository
from src.application.services.pattern_service import PatternService

console = Console()

@click.group(name="patterns")
def patterns_cli():
    """Pattern library management commands."""
    pass


@patterns_cli.command(name="review-suggestions")
@click.option("--limit", default=20, help="Maximum suggestions to show")
def review_suggestions(limit: int):
    """List pending pattern suggestions for review."""
    try:
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        service = PatternSuggestionService()
        suggestions = service.list_pending(limit=limit)
        stats = service.get_stats()
        service.close()

        if not suggestions:
            console.print("[yellow]No pending pattern suggestions.[/yellow]")
            return

        # Header with stats
        console.print("\n[bold blue]Pattern Suggestions Review Queue[/bold blue]")
        console.print(f"Total: {stats.get('total', 0)} | Pending: {stats.get('pending', 0)} | Approved: {stats.get('approved', 0)} | Rejected: {stats.get('rejected', 0)}")

        # Table
        table = Table(title=f"Pending Suggestions (showing {min(len(suggestions), limit)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Category", style="green")
        table.add_column("Confidence", style="yellow")
        table.add_column("Hours Pending", style="red")
        table.add_column("Description", style="dim")

        for s in suggestions:
            confidence = f"{s['confidence']:.2f}" if s['confidence'] else "N/A"
            hours = f"{s['hours_pending']:.1f}h" if s['hours_pending'] > 0 else "<1h"

            # Truncate description
            desc = s['description']
            if len(desc) > 60:
                desc = desc[:57] + "..."

            table.add_row(
                str(s['id']),
                s['name'],
                s['category'],
                confidence,
                hours,
                desc
            )

        console.print(table)
        console.print("\n[dim]Use 'specql patterns show <id>' to see details[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing suggestions: {e}[/red]")


@patterns_cli.command(name="show")
@click.argument("suggestion_id", type=int)
def show_suggestion(suggestion_id: int):
    """Show detailed information about a pattern suggestion."""
    try:
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        service = PatternSuggestionService()
        suggestion = service.get_suggestion(suggestion_id)
        service.close()

        if not suggestion:
            console.print(f"[red]Suggestion #{suggestion_id} not found.[/red]")
            return

        # Header
        status_color = {
            'pending': 'yellow',
            'approved': 'green',
            'rejected': 'red',
            'merged': 'blue'
        }.get(suggestion['status'], 'white')

        console.print(f"\n[bold {status_color}]Suggestion #{suggestion['id']}: {suggestion['name']}[/bold {status_color}]")
        console.print(f"Status: {suggestion['status'].upper()}")

        # Basic info
        console.print("\n[bold]Basic Information:[/bold]")
        console.print(f"Category: {suggestion['category']}")
        console.print(f"Source: {suggestion['source_type']}")
        console.print(f"Created: {suggestion['created_at']}")

        if suggestion['confidence_score']:
            console.print(f"Confidence: {suggestion['confidence_score']:.2f}")
        if suggestion['complexity_score']:
            console.print(f"Complexity: {suggestion['complexity_score']:.2f}")

        # Description
        console.print("\n[bold]Description:[/bold]")
        console.print(Panel(suggestion['description'], border_style="dim"))

        # Parameters
        if suggestion['parameters']:
            console.print("\n[bold]Parameters:[/bold]")
            console.print(Panel(json.dumps(suggestion['parameters'], indent=2), border_style="blue"))

        # Implementation
        if suggestion['implementation']:
            console.print("\n[bold]Implementation:[/bold]")
            console.print(Panel(json.dumps(suggestion['implementation'], indent=2), border_style="green"))

        # Source info
        if suggestion['source_sql']:
            console.print("\n[bold]Source SQL:[/bold]")
            # Truncate very long SQL
            sql = suggestion['source_sql']
            if len(sql) > 500:
                sql = sql[:497] + "..."
            console.print(Panel(sql, border_style="magenta"))

        if suggestion['source_function_id']:
            console.print(f"Source Function: {suggestion['source_function_id']}")

        # Actions
        if suggestion['status'] == 'pending':
            console.print("\n[bold]Actions:[/bold]")
            console.print("• Approve: specql patterns approve <id>")
            console.print("• Reject:  specql patterns reject <id> --reason '...'")

    except Exception as e:
        console.print(f"[red]Error showing suggestion: {e}[/red]")


@patterns_cli.command(name="approve")
@click.argument("suggestion_id", type=int)
@click.option("--reviewer", default="cli", help="Reviewer name")
def approve_suggestion(suggestion_id: int, reviewer: str):
    """Approve a pattern suggestion and add it to the pattern library."""
    try:
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        # Confirm action
        if not Confirm.ask(f"Are you sure you want to approve suggestion #{suggestion_id}?"):
            console.print("[yellow]Approval cancelled.[/yellow]")
            return

        service = PatternSuggestionService()
        success = service.approve_suggestion(suggestion_id, reviewer)
        service.close()

        if success:
            console.print(f"[green]✓ Successfully approved suggestion #{suggestion_id}[/green]")
            console.print("[dim]The pattern has been added to the domain pattern library.[/dim]")
        else:
            console.print(f"[red]✗ Failed to approve suggestion #{suggestion_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error approving suggestion: {e}[/red]")


@patterns_cli.command(name="reject")
@click.argument("suggestion_id", type=int)
@click.option("--reason", required=True, help="Reason for rejection")
@click.option("--reviewer", default="cli", help="Reviewer name")
def reject_suggestion(suggestion_id: int, reason: str, reviewer: str):
    """Reject a pattern suggestion."""
    try:
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        # Confirm action
        if not Confirm.ask(f"Are you sure you want to reject suggestion #{suggestion_id}?"):
            console.print("[yellow]Rejection cancelled.[/yellow]")
            return

        service = PatternSuggestionService()
        success = service.reject_suggestion(suggestion_id, reason, reviewer)
        service.close()

        if success:
            console.print(f"[green]✓ Successfully rejected suggestion #{suggestion_id}[/green]")
            console.print(f"[dim]Reason: {reason}[/dim]")
        else:
            console.print(f"[red]✗ Failed to reject suggestion #{suggestion_id}[/red]")

    except Exception as e:
        console.print(f"[red]Error rejecting suggestion: {e}[/red]")


@patterns_cli.command(name="create-from-description")
@click.option("--description", required=True, help="Natural language description of the pattern")
@click.option("--category", help="Pattern category (workflow, validation, audit, etc.)")
@click.option("--save", is_flag=True, help="Save the generated pattern to database")
@click.option("--reviewer", default="cli", help="Reviewer name for saved patterns")
def create_from_description(description: str, category: str, save: bool, reviewer: str):
    """Generate a SpecQL pattern from natural language description."""
    try:
        from src.pattern_library.nl_generator import NLPatternGenerator

        console.print("[cyan]Generating pattern from description...[/cyan]")
        console.print(f"Description: {description}")
        if category:
            console.print(f"Category hint: {category}")

        # Generate pattern
        generator = NLPatternGenerator()
        pattern, confidence, validation_msg = generator.generate(description, category)
        generator.close()

        # Display results
        console.print("\n[green]✓ Pattern generated successfully![/green]")
        console.print(f"Confidence: {confidence:.2f} ({validation_msg})")

        # Show pattern details
        console.print("\n[bold]Generated Pattern:[/bold]")
        console.print(f"Name: {pattern['name']}")
        console.print(f"Category: {pattern['category']}")
        console.print(f"Description: {pattern['description']}")

        # Parameters
        if pattern.get('parameters'):
            console.print("\n[bold]Parameters:[/bold]")
            console.print(Panel(json.dumps(pattern['parameters'], indent=2), border_style="blue"))

        # Implementation
        if pattern.get('implementation'):
            console.print("\n[bold]Implementation:[/bold]")
            console.print(Panel(json.dumps(pattern['implementation'], indent=2), border_style="green"))

        # Save to database if requested
        if save:
            if confidence < 0.7:
                console.print(f"\n[yellow]⚠️  Low confidence score ({confidence:.2f}). Consider manual review.[/yellow]")

            if Confirm.ask("Save this pattern to the database?"):
                pattern_id = generator.save_pattern(pattern, confidence)
                console.print(f"[green]✓ Pattern saved with ID: {pattern_id}[/green]")
            else:
                console.print("[yellow]Pattern not saved.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error generating pattern: {e}[/red]")


@patterns_cli.command(name="stats")
def show_stats():
    """Show pattern suggestion statistics."""
    try:
        from src.pattern_library.suggestion_service_pg import PatternSuggestionService

        service = PatternSuggestionService()
        stats = service.get_stats()
        service.close()

        console.print("\n[bold blue]Pattern Suggestion Statistics[/bold blue]")
        console.print(f"Total suggestions: {stats.get('total', 0)}")
        console.print(f"Pending review: {stats.get('pending', 0)}")
        console.print(f"Approved: {stats.get('approved', 0)}")
        console.print(f"Rejected: {stats.get('rejected', 0)}")
        console.print(f"Merged: {stats.get('merged', 0)}")

    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")


@patterns_cli.command(name="list")
@click.option("--category", help="Filter by category")
@click.option("--active-only", is_flag=True, help="Show only active (non-deprecated) patterns")
def list_patterns(category: str, active_only: bool):
    """List patterns in the pattern library."""
    try:
        from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

        service = get_pattern_service_with_fallback()

        if category:
            patterns = service.find_patterns_by_category(category)
        else:
            patterns = service.list_all_patterns()

        if active_only:
            patterns = [p for p in patterns if p.is_active]

        if not patterns:
            console.print("[yellow]No patterns found.[/yellow]")
            return

        # Header
        console.print(f"\n[bold blue]Pattern Library ({len(patterns)} patterns)[/bold blue]")

        # Table
        table = Table(title="Domain Patterns")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="green")
        table.add_column("Usage", style="yellow", justify="right")
        table.add_column("Status", style="magenta")
        table.add_column("Description", style="dim")

        for pattern in sorted(patterns, key=lambda p: p.name):
            status = "Active" if pattern.is_active else "Deprecated"
            usage = str(pattern.times_instantiated)

            # Truncate description
            desc = pattern.description
            if len(desc) > 50:
                desc = desc[:47] + "..."

            table.add_row(
                pattern.name,
                pattern.category.value,
                usage,
                status,
                desc
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing patterns: {e}[/red]")


@patterns_cli.command(name="get")
@click.argument("pattern_name")
def get_pattern(pattern_name: str):
    """Get detailed information about a specific pattern."""
    try:
        from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

        service = get_pattern_service_with_fallback()
        pattern = service.get_pattern(pattern_name)

        # Header
        status_color = "green" if pattern.is_active else "red"
        console.print(f"\n[bold {status_color}]{pattern.name}[/bold {status_color}]")
        console.print(f"Category: {pattern.category.value}")
        console.print(f"Status: {'Active' if pattern.is_active else 'Deprecated'}")
        console.print(f"Usage: {pattern.times_instantiated} times")
        console.print(f"Source: {pattern.source_type.value}")

        if pattern.complexity_score:
            console.print(f"Complexity: {pattern.complexity_score:.1f}/10")

        if not pattern.is_active and pattern.deprecated_reason:
            console.print(f"Deprecation: {pattern.deprecated_reason}")

        # Description
        console.print("\n[bold]Description:[/bold]")
        console.print(Panel(pattern.description, border_style="dim"))

        # Parameters
        if pattern.parameters:
            console.print("\n[bold]Parameters:[/bold]")
            console.print(Panel(json.dumps(pattern.parameters, indent=2), border_style="blue"))

        # Implementation
        if pattern.implementation:
            console.print("\n[bold]Implementation:[/bold]")
            console.print(Panel(json.dumps(pattern.implementation, indent=2), border_style="green"))

        # Embedding info
        if pattern.has_embedding:
            console.print(f"\n[bold]Vector Embedding:[/bold] {len(pattern.embedding)} dimensions")
        else:
            console.print("\n[bold]Vector Embedding:[/bold] Not available")

        # Timestamps
        if pattern.created_at:
            console.print(f"\nCreated: {pattern.created_at}")
        if pattern.updated_at and pattern.updated_at != pattern.created_at:
            console.print(f"Updated: {pattern.updated_at}")

    except Exception as e:
        console.print(f"[red]Error getting pattern: {e}[/red]")


@patterns_cli.command(name="performance-report")
def pattern_performance_report():
    """Show pattern repository performance metrics."""
    try:
        from src.application.services.pattern_service_factory import get_pattern_service
        from src.core.config import get_config

        config = get_config()

        # Only show performance report if using monitored repository
        if not config.should_use_postgresql_primary():
            console.print("[yellow]Performance monitoring only available with PostgreSQL backend.[/yellow]")
            console.print("Set SPECQL_REPOSITORY_BACKEND=postgresql to enable monitoring.")
            return

        service = get_pattern_service(monitoring=True)

        # Access the monitored repository directly for performance stats
        # This is a bit of a hack, but necessary to get performance data
        repository = service.repository
        if hasattr(repository, 'get_performance_report'):
            report = repository.get_performance_report()

            console.print("\n[bold blue]Pattern Repository Performance Report[/bold blue]")
            console.print(f"Queries executed: {report['queries_executed']}")
            console.print(f"Average query time: {report['average_query_time']:.3f}s")
            console.print(f"Slow queries (>100ms): {report['slow_query_count']}")
            console.print(f"Success rate: {report['success_rate']:.1f}%")
            console.print(f"Failed queries: {report['failed_queries']}")

            if report['slow_queries']:
                console.print("\n[bold yellow]Recent Slow Queries:[/bold yellow]")
                for slow_query in report['slow_queries'][-5:]:  # Last 5 slow queries
                    console.print(f"• {slow_query['operation']}: {slow_query['duration']:.3f}s")
        else:
            console.print("[yellow]Performance monitoring not available for current repository.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting performance report: {e}[/red]")


@patterns_cli.command(name="check-consistency")
@click.option("--legacy-db", help="Path to legacy pattern database", default="pattern_library.db")
def check_pattern_consistency(legacy_db: str):
    """Check data consistency between PostgreSQL and legacy pattern storage."""
    try:
        from src.core.pattern_consistency_checker import PatternConsistencyChecker
        from src.core.config import get_config
        from pathlib import Path

        config = get_config()

        if not config.database_url:
            console.print("[red]PostgreSQL database URL not configured.[/red]")
            console.print("Set SPECQL_DB_URL environment variable.")
            return

        console.print("[cyan]Checking pattern data consistency...[/cyan]")

        checker = PatternConsistencyChecker(
            db_url=config.database_url,
            legacy_patterns_path=Path(legacy_db)
        )

        results = checker.check_consistency()

        if results['consistent']:
            console.print("[green]✓ Pattern data consistency check passed![/green]")
        else:
            console.print("[red]✗ Pattern data inconsistencies found![/red]")

        # Summary
        summary = results['summary']
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"PostgreSQL patterns: {summary['postgresql_patterns']}")
        console.print(f"Legacy patterns: {summary['legacy_patterns']}")
        console.print(f"Discrepancies found: {summary['discrepancies_found']}")

        # Show discrepancies
        if results['discrepancies']:
            console.print("\n[bold yellow]Discrepancies:[/bold yellow]")
            for i, disc in enumerate(results['discrepancies'][:10], 1):  # Show first 10
                console.print(f"{i}. [{disc['type']}] {disc.get('pattern', 'N/A')}: {disc['details']}")

            if len(results['discrepancies']) > 10:
                console.print(f"... and {len(results['discrepancies']) - 10} more discrepancies")

    except Exception as e:
        console.print(f"[red]Error checking pattern consistency: {e}[/red]")


@patterns_cli.command(name="search")
@click.argument("query")
@click.option("--limit", default=10, help="Maximum results to return")
@click.option("--min-similarity", default=0.5, type=float,
              help="Minimum similarity threshold (0.0-1.0)")
@click.option("--category", help="Filter by category")
def search_patterns(query, limit, min_similarity, category):
    """
    Search patterns using natural language

    Examples:
        specql patterns search "validate email addresses"
        specql patterns search "audit logging" --category infrastructure
        specql patterns search "phone number" --min-similarity 0.7
    """
    try:
        from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

        service = get_pattern_service_with_fallback()

        console.print(f"🔍 Searching for: '{query}'")
        if category:
            console.print(f"   Category: {category}")
        console.print(f"   Minimum similarity: {min_similarity}")
        console.print()

        # Search
        results = service.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=min_similarity,
            category=category
        )

        if not results:
            console.print("No matching patterns found.")
            console.print(f"Try lowering --min-similarity (current: {min_similarity})")
            return

        console.print(f"Found {len(results)} pattern(s):\n")

        for i, (pattern, similarity) in enumerate(results, 1):
            # Similarity as percentage
            sim_pct = similarity * 100

            # Color code by similarity
            if similarity >= 0.8:
                color = "green"
            elif similarity >= 0.6:
                color = "yellow"
            else:
                color = "white"

            console.print(f"{i}. {pattern.name} ({sim_pct:.1f}% match)", style=f"bold {color}")

            console.print(f"   Category: {pattern.category}")
            console.print(f"   Description: {pattern.description[:100]}...")

            if pattern.times_instantiated > 0:
                console.print(f"   Used {pattern.times_instantiated} times")

            console.print()

    except Exception as e:
        console.print(f"[red]Error searching patterns: {e}[/red]")


@patterns_cli.command(name="similar")
@click.argument("pattern_name")
@click.option("--limit", default=5, help="Maximum results to return")
@click.option("--min-similarity", default=0.5, type=float,
              help="Minimum similarity threshold")
def find_similar_patterns(pattern_name, limit, min_similarity):
    """
    Find patterns similar to a given pattern

    Examples:
        specql patterns similar email_validation
        specql patterns similar audit_trail --limit 10
    """
    try:
        from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

        service = get_pattern_service_with_fallback()

        # Get reference pattern
        pattern = service.get_pattern(pattern_name)
        if not pattern:
            console.print(f"[red]Pattern not found: {pattern_name}[/red]")
            return

        if not pattern.embedding:
            console.print(f"[red]Pattern has no embedding: {pattern_name}[/red]")
            console.print("Run: python scripts/backfill_pattern_embeddings.py")
            return

        console.print(f"🔍 Finding patterns similar to: {pattern.name}")
        console.print(f"   {pattern.description}")
        console.print()

        # Find similar
        if pattern.id is None:
            console.print("[red]Pattern has no ID[/red]")
            return

        results = service.find_similar_patterns(
            pattern_id=pattern.id,
            limit=limit,
            min_similarity=min_similarity
        )

        if not results:
            console.print("No similar patterns found.")
            return

        console.print(f"Found {len(results)} similar pattern(s):\n")

        for i, (similar_pattern, similarity) in enumerate(results, 1):
            sim_pct = similarity * 100

            if similarity >= 0.8:
                color = "green"
            elif similarity >= 0.6:
                color = "yellow"
            else:
                color = "white"

            console.print(f"{i}. {similar_pattern.name} ({sim_pct:.1f}% similar)", style=f"bold {color}")

            console.print(f"   {similar_pattern.description[:100]}...")
            console.print()

    except Exception as e:
        console.print(f"[red]Error finding similar patterns: {e}[/red]")


@patterns_cli.command(name="recommend")
@click.option("--entity-description", required=True,
              help="Description of the entity")
@click.option("--field", "fields", multiple=True, required=True,
              help="Field names in the entity (can specify multiple)")
@click.option("--limit", default=5, help="Maximum recommendations")
def recommend_patterns(entity_description, fields, limit):
    """
    Recommend patterns for an entity

    Examples:
        specql patterns recommend \
            --entity-description "Customer contact information" \
            --field email \
            --field phone \
            --field address
    """
    try:
        from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

        service = get_pattern_service_with_fallback()

        console.print("🎯 Pattern recommendations for:")
        console.print(f"   Entity: {entity_description}")
        console.print(f"   Fields: {', '.join(fields)}")
        console.print()

        # Get recommendations
        recommendations = service.recommend_patterns_for_entity(
            entity_description=entity_description,
            field_names=list(fields),
            limit=limit
        )

        if not recommendations:
            console.print("No pattern recommendations found.")
            return

        console.print(f"💡 Recommended {len(recommendations)} pattern(s):\n")

        for i, (pattern, similarity) in enumerate(recommendations, 1):
            sim_pct = similarity * 100

            console.print(f"{i}. {pattern.name} ({sim_pct:.1f}% match)", style="bold cyan")

            console.print(f"   {pattern.description}")

            if pattern.times_instantiated > 0:
                console.print(f"   ⭐ Popular: Used {pattern.times_instantiated} times")

            console.print()

    except Exception as e:
        console.print(f"[red]Error getting recommendations: {e}[/red]")


@patterns_cli.command()
@click.option("--output", required=True, type=click.Path(),
              help="Output file path")
@click.option("--format", "fmt", type=click.Choice(["yaml", "json"]),
              default="yaml", help="Export format")
@click.option("--category", help="Export only patterns in this category")
@click.option("--include-embeddings", is_flag=True,
              help="Include embeddings in export (large file)")
def export(output, fmt, category, include_embeddings):
    """
    Export patterns to file

    Examples:
        specql patterns export --output patterns.yaml
        specql patterns export --output validation.json --format json --category validation
        specql patterns export --output all_patterns.yaml --include-embeddings
    """
    from pathlib import Path
    from src.cli.pattern_exporter import PatternExporter

    config = get_config()

    # Check if PostgreSQL is configured
    if not config.database_url:
        console.print("[red]❌ PostgreSQL database not configured.[/red]")
        console.print("Set SPECQL_DB_URL environment variable to enable pattern export/import.")
        console.print("Example: export SPECQL_DB_URL='postgresql://user:pass@localhost:5432/specql'")
        raise click.Abort()

    repository = PostgreSQLPatternRepository(config.database_url)  # type: ignore
    service = PatternService(repository)
    exporter = PatternExporter(service)

    output_path = Path(output)

    console.print("📦 Exporting patterns...")
    if category:
        console.print(f"   Category: {category}")
    console.print(f"   Format: {fmt}")
    console.print(f"   Output: {output}")

    try:
        if fmt == "yaml":
            exporter.export_to_yaml(
                output_path,
                category=category,
                include_embeddings=include_embeddings
            )
        else:
            exporter.export_to_json(
                output_path,
                category=category,
                include_embeddings=include_embeddings
            )

        # Get pattern count
        if category:
            patterns = [p for p in service.repository.list_all() if p.category.value == category]
        else:
            patterns = service.repository.list_all()

        console.print(f"✅ Exported {len(patterns)} pattern(s) to {output}")

    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")
        raise click.Abort()


@patterns_cli.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--skip-existing/--update-existing", default=True,
              help="Skip existing patterns or update them")
@click.option("--no-embeddings", is_flag=True,
              help="Don't generate embeddings during import")
def import_patterns(input_file, skip_existing, no_embeddings):
    """
    Import patterns from file

    Examples:
        specql patterns import patterns.yaml
        specql patterns import validation.json --update-existing
        specql patterns import patterns.yaml --no-embeddings
    """
    from pathlib import Path
    from src.cli.pattern_importer import PatternImporter

    config = get_config()

    # Check if PostgreSQL is configured
    if not config.database_url:
        console.print("[red]❌ PostgreSQL database not configured.[/red]")
        console.print("Set SPECQL_DB_URL environment variable to enable pattern export/import.")
        console.print("Example: export SPECQL_DB_URL='postgresql://user:pass@localhost:5432/specql'")
        raise click.Abort()

    repository = PostgreSQLPatternRepository(config.database_url)  # type: ignore
    service = PatternService(repository)
    importer = PatternImporter(service)

    input_path = Path(input_file)

    console.print(f"📥 Importing patterns from {input_file}...")
    if skip_existing:
        console.print("   Mode: Skip existing patterns")
    else:
        console.print("   Mode: Update existing patterns")

    try:
        # Determine format from extension
        if input_path.suffix == ".yaml" or input_path.suffix == ".yml":
            imported_count = importer.import_from_yaml(
                input_path,
                skip_existing=skip_existing,
                generate_embeddings=not no_embeddings
            )
        elif input_path.suffix == ".json":
            imported_count = importer.import_from_json(
                input_path,
                skip_existing=skip_existing,
                generate_embeddings=not no_embeddings
            )
        else:
            console.print(f"[red]❌ Unsupported file format: {input_path.suffix}[/red]")
            raise click.Abort()

        if imported_count > 0:
            console.print(f"✅ Imported {imported_count} pattern(s)")
        else:
            console.print("ℹ️  No new patterns imported (all existed)")

    except Exception as e:
        console.print(f"[red]❌ Import failed: {e}[/red]")
        raise click.Abort()


@patterns_cli.command()
@click.option("--threshold", default=0.9, type=float,
              help="Similarity threshold (0.0-1.0)")
@click.option("--auto-merge", is_flag=True,
              help="Automatically merge duplicates")
@click.option("--strategy", type=click.Choice(["most_used", "oldest", "newest"]),
              default="most_used",
              help="Merge strategy")
def deduplicate(threshold, auto_merge, strategy):
    """
    Find and optionally merge duplicate patterns

    Examples:
        specql patterns deduplicate
        specql patterns deduplicate --threshold 0.95
        specql patterns deduplicate --auto-merge --strategy most_used
    """
    from src.application.services.pattern_deduplicator import PatternDeduplicator

    config = get_config()

    # Check if PostgreSQL is configured
    if not config.database_url:
        console.print("[red]❌ PostgreSQL database not configured.[/red]")
        console.print("Set SPECQL_DB_URL environment variable to enable pattern deduplication.")
        console.print("Example: export SPECQL_DB_URL='postgresql://user:pass@localhost:5432/specql'")
        raise click.Abort()

    repository = PostgreSQLPatternRepository(config.database_url)  # type: ignore
    service = PatternService(repository)
    deduplicator = PatternDeduplicator(service)

    console.print(f"🔍 Finding duplicate patterns (threshold: {threshold})...")
    console.print()

    # Find duplicates
    duplicate_groups = deduplicator.find_duplicates(similarity_threshold=threshold)

    if not duplicate_groups:
        console.print("✅ No duplicate patterns found")
        return

    console.print(f"Found {len(duplicate_groups)} group(s) of duplicates:\n")

    # Process each group
    for i, group in enumerate(duplicate_groups, 1):
        console.print(f"[bold]Group {i}:[/bold]")

        for pattern in group:
            console.print(f"  • {pattern.name}")
            console.print(f"    Category: {pattern.category.value}")
            console.print(f"    Used: {pattern.times_instantiated} times")
            console.print(f"    Source: {pattern.source_type.value}")

        # Get merge suggestion
        suggestion = deduplicator.suggest_merge(group, strategy=strategy)

        console.print()
        console.print(f"  [green]Suggestion: Keep '{suggestion['keep'].name}'[/green]")
        console.print(f"  Reason: {suggestion['reason']}")

        if auto_merge:
            # Perform merge
            merged = deduplicator.merge_patterns(
                keep=suggestion["keep"],
                merge=suggestion["merge"]
            )
            console.print(f"  [green]✅ Merged into '{merged.name}'[/green]")
        else:
            console.print("  💡 Run with --auto-merge to perform merge")

        console.print()

    if not auto_merge:
        console.print("💡 Run with --auto-merge to automatically merge duplicates")


@patterns_cli.command()
@click.argument("pattern1_name")
@click.argument("pattern2_name")
def compare(pattern1_name, pattern2_name):
    """
    Compare two patterns for similarity

    Examples:
        specql patterns compare email_validation email_validator
    """
    from src.application.services.pattern_deduplicator import PatternDeduplicator

    config = get_config()

    # Check if PostgreSQL is configured
    if not config.database_url:
        console.print("[red]❌ PostgreSQL database not configured.[/red]")
        console.print("Set SPECQL_DB_URL environment variable to enable pattern comparison.")
        console.print("Example: export SPECQL_DB_URL='postgresql://user:pass@localhost:5432/specql'")
        raise click.Abort()

    repository = PostgreSQLPatternRepository(config.database_url)  # type: ignore
    service = PatternService(repository)
    deduplicator = PatternDeduplicator(service)

    # Get patterns
    try:
        pattern1 = service.get_pattern_by_name(pattern1_name)
        pattern2 = service.get_pattern_by_name(pattern2_name)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    # Calculate similarity
    similarity = deduplicator.calculate_similarity(pattern1, pattern2)
    sim_pct = similarity * 100

    console.print("📊 Comparing patterns:\n")

    console.print(f"Pattern 1: {pattern1.name}")
    console.print(f"  Category: {pattern1.category.value}")
    console.print(f"  Description: {pattern1.description[:80]}...")
    console.print()

    console.print(f"Pattern 2: {pattern2.name}")
    console.print(f"  Category: {pattern2.category.value}")
    console.print(f"  Description: {pattern2.description[:80]}...")
    console.print()

    # Color code by similarity
    if similarity >= 0.9:
        color = "red"
        verdict = "Very similar (likely duplicate)"
    elif similarity >= 0.7:
        color = "yellow"
        verdict = "Similar"
    else:
        color = "green"
        verdict = "Different"

    console.print(f"Similarity: [bold {color}]{sim_pct:.1f}%[/bold {color}]")
    console.print(f"Verdict: {verdict}")