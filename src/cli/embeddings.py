"""CLI commands for pattern embeddings."""

import click
from rich.console import Console
from rich.progress import Progress
from pathlib import Path
import os

console = Console()

@click.group(name="embeddings")
def embeddings_cli():
    """Pattern embedding management."""
    pass

@embeddings_cli.command(name="generate")
def generate_embeddings():
    """Generate embeddings for all patterns without embeddings."""
    from src.pattern_library.embeddings_pg import PatternEmbeddingService

    console.print("[cyan]Generating embeddings...[/cyan]")

    service = PatternEmbeddingService()
    service.generate_all_embeddings()
    service.close()

    console.print("[green]✓ Embeddings generated successfully[/green]")

@embeddings_cli.command(name="test-retrieval")
@click.argument("query", type=str)
@click.option("--top-k", default=5, help="Number of results")
def test_retrieval(query: str, top_k: int):
    """Test pattern retrieval with a query."""
    from src.pattern_library.embeddings_pg import PatternEmbeddingService

    service = PatternEmbeddingService()

    # Generate query embedding
    query_embedding = service.embed_function(query)

    # Retrieve similar patterns
    results = service.retrieve_similar(query_embedding, top_k=top_k)

    # Display results
    from rich.table import Table
    table = Table(title=f"Top-{top_k} Similar Patterns")
    table.add_column("Pattern", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Similarity", style="yellow")
    table.add_column("Description", style="dim")

    for r in results:
        table.add_row(
            r['name'],
            r['category'],
            f"{r['similarity']:.3f}",
            r['description'][:60] + "..." if len(r['description']) > 60 else r['description']
        )

    console.print(table)
    service.close()