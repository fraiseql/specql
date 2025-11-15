import click
from pathlib import Path

from src.core.specql_parser import SpecQLParser
from src.generators.diagrams.relationship_extractor import RelationshipExtractor
from src.generators.diagrams.dependency_graph import DependencyGraph
from src.generators.diagrams.graphviz_generator import GraphvizGenerator
from src.generators.diagrams.mermaid_generator import MermaidGenerator
from src.generators.diagrams.html_viewer_generator import HTMLViewerGenerator

@click.command()
@click.argument('yaml_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), default='docs/schema.svg',
              help='Output file path')
@click.option('--format', '-f', type=click.Choice(['svg', 'png', 'pdf', 'dot', 'mermaid', 'html']),
              default='svg', help='Output format')
@click.option('--title', '-t', type=str, help='Diagram title')
@click.option('--cluster/--no-cluster', default=True,
              help='Cluster entities by schema')
@click.option('--show-fields/--hide-fields', default=True,
              help='Show entity fields')
@click.option('--show-trinity/--hide-trinity', default=True,
              help='Show Trinity pattern fields (pk_, id, identifier)')
@click.option('--stats', is_flag=True,
              help='Show relationship statistics')
def diagram(
    yaml_files,
    output,
    format,
    title,
    cluster,
    show_fields,
    show_trinity,
    stats
):
    """
    Generate visual schema diagram from SpecQL YAML

    Examples:
        # Basic diagram
        specql diagram entities/*.yaml

        # Custom output
        specql diagram entities/*.yaml --output docs/erd.svg

        # PNG format
        specql diagram entities/*.yaml --format png

        # Mermaid format (for Markdown docs)
        specql diagram entities/*.yaml --format mermaid --output docs/schema.md

        # Interactive HTML viewer
        specql diagram entities/*.yaml --format html --output docs/schema.html

        # With title
        specql diagram entities/*.yaml --title "CRM Schema"

        # Show statistics
        specql diagram entities/*.yaml --stats

        # Flat layout (no clustering)
        specql diagram entities/*.yaml --no-cluster

        # Hide Trinity fields
        specql diagram entities/*.yaml --hide-trinity
    """
    click.echo("🎨 Generating schema diagram...\n")

    # Parse YAML files
    parser = SpecQLParser()
    entities = []

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                yaml_content = f.read()
                entity = parser.parse(yaml_content)
                entities.append(entity)
                click.echo(f"  ✅ Parsed: {entity.name}")
        except Exception as e:
            click.echo(f"  ❌ Error parsing {yaml_file}: {e}", err=True)
            continue

    if not entities:
        click.echo("❌ No entities found", err=True)
        return

    click.echo(f"\n📊 Found {len(entities)} entities\n")

    # Extract relationships
    extractor = RelationshipExtractor()
    extractor.extract_from_entities(entities)

    click.echo(f"🔗 Found {len(extractor.relationships)} relationships\n")

    # Show statistics
    if stats:
        _show_statistics(extractor)
        click.echo()

    # Generate diagram based on format
    if format in ['svg', 'png', 'pdf', 'dot']:
        # Graphviz formats
        generator = GraphvizGenerator(extractor)
        dot_source = generator.generate(
            output_path=output,
            format=format,
            title=title,
            cluster_by_schema=cluster,
            show_fields=show_fields,
            show_trinity=show_trinity,
        )

        if format == 'dot':
            # Just save DOT source
            Path(output).write_text(dot_source)
            click.echo(f"✅ DOT source saved: {output}")
        else:
            click.echo(f"✅ Diagram generated: {output}")

    elif format == 'mermaid':
        # Mermaid format
        generator = MermaidGenerator(extractor)
        generator.generate(
            output_path=output,
            title=title,
            show_fields=show_fields,
            show_trinity=show_trinity,
        )
        click.echo(f"✅ Mermaid diagram saved: {output}")

    elif format == 'html':
        # HTML interactive viewer
        # First generate SVG for embedding
        graphviz_gen = GraphvizGenerator(extractor)
        svg_content = graphviz_gen.generate(
            format='svg',
            title=title,
            cluster_by_schema=cluster,
            show_fields=show_fields,
            show_trinity=show_trinity,
        )

        # Generate HTML viewer
        html_gen = HTMLViewerGenerator(extractor)
        html_gen.generate(
            svg_content=svg_content,
            output_path=output,
            title=title or "Schema Diagram"
        )
        click.echo(f"✅ Interactive HTML viewer saved: {output}")

    # Show next steps
    click.echo("\n📋 Next steps:")
    click.echo(f"  1. View diagram: open {output}")
    click.echo(f"  2. Include in docs: ![Schema]({{{{url_for('static', filename='{output}')}}}})")

def _show_statistics(extractor: RelationshipExtractor) -> None:
    """Show relationship statistics"""

    summary = extractor.get_relationship_summary()

    click.echo("📈 Statistics:")
    click.echo(f"  Entities: {summary['total_entities']}")
    click.echo(f"  Relationships: {summary['total_relationships']}")
    click.echo(f"  Schemas: {', '.join(summary['schemas'])}")
    click.echo()

    click.echo("  Relationship Types:")
    for rel_type, count in summary['relationship_types'].items():
        if count > 0:
            click.echo(f"    - {rel_type}: {count}")

    # Dependency analysis
    graph = DependencyGraph(extractor)

    cycles = graph.detect_cycles()
    if cycles:
        click.echo(f"\n  ⚠️  Circular dependencies detected: {len(cycles)}")
        for cycle in cycles[:3]:  # Show first 3
            click.echo(f"    - {' → '.join(cycle + [cycle[0]])}")

    # Entity metrics
    click.echo("\n  Top Referenced Entities:")
    metrics = graph.calculate_entity_metrics()
    sorted_entities = sorted(
        metrics.items(),
        key=lambda x: x[1]['referenced_by_count'],
        reverse=True
    )

    for entity, metric in sorted_entities[:5]:
        click.echo(
            f"    - {entity}: "
            f"{metric['referenced_by_count']} references, "
            f"importance {metric['importance']}"
        )