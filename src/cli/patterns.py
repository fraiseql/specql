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