"""
Reverse Schema CLI Command

Converts PostgreSQL CREATE TABLE statements to SpecQL entity YAML files.
"""

from pathlib import Path

import click
from rich.console import Console

from reverse_engineering.entity_generator import EntityYAMLGenerator
from reverse_engineering.fk_detector import ForeignKeyDetector
from reverse_engineering.pattern_orchestrator import PatternDetectionOrchestrator
from reverse_engineering.table_parser import SQLTableParser
from reverse_engineering.translation_detector import TranslationMerger, TranslationTableDetector

console = Console()


@click.command()
@click.argument("sql_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--output-dir", "-o", type=click.Path(), required=True, help="Output directory for YAML files"
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.80,
    help="Minimum confidence threshold (default: 0.80)",
)
@click.option("--preview", is_flag=True, help="Preview mode (don't write files)")
@click.option(
    "--merge-translations",
    is_flag=True,
    default=True,
    help="Auto-merge translation tables (default: true)",
)
def reverse_schema(sql_files, output_dir, min_confidence, preview, merge_translations):
    """
    Reverse engineer PostgreSQL tables to SpecQL entity YAML

    Automatically detects and converts:
    - Trinity pattern (id, pk_*, identifier)
    - Foreign keys → ref() relationships
    - Translation tables → nested translations
    - Audit trails, soft deletes, and other patterns

    Examples:
        specql reverse-schema db/schema.sql -o entities/
        specql reverse-schema db/tables/*.sql -o entities/
        specql reverse-schema tables.sql -o entities/ --preview
    """

    console.print("[bold cyan]🔄 SQL → SpecQL Entity Reverse Engineering[/bold cyan]\n")

    # Initialize components
    parser = SQLTableParser()
    pattern_detector = PatternDetectionOrchestrator()
    entity_generator = EntityYAMLGenerator()
    fk_detector = ForeignKeyDetector()
    translation_detector = TranslationTableDetector()
    translation_merger = TranslationMerger()

    # Parse all tables first
    all_tables = []
    for sql_file in sql_files:
        try:
            with open(sql_file) as f:
                sql = f.read()
            parsed_table = parser.parse_table(sql)
            all_tables.append((sql_file, parsed_table))
        except Exception as e:
            console.print(f"❌ Failed to parse {sql_file}: {e}", style="red")
            all_tables.append((sql_file, None))

    # Detect translation tables and build merge map
    translation_map = {}
    if merge_translations:
        for sql_file, table in all_tables:
            if table is None:
                continue
            translation_info = translation_detector.detect(table)
            if translation_info.is_translation_table:
                translation_map[translation_info.parent_table] = (sql_file, table)

    results = []

    for sql_file, table in all_tables:
        if table is None:
            results.append((sql_file, 0, 0))
            continue

        console.print(f"📄 Processing {sql_file}...")

        try:
            # Skip translation tables (will be merged)
            if merge_translations and table.table_name in [
                t[1].table_name for t in translation_map.values()
            ]:
                console.print(f"   ⏭️  Skipping {table.table_name} (will merge with parent)")
                results.append((sql_file, 0, 0))  # Don't count as processed
                continue

            # Check if this table has a translation
            merged_fields = None
            if merge_translations and table.table_name in translation_map:
                _, translation_table = translation_map[table.table_name]
                merged_fields = translation_merger.merge(table, translation_table)

            # Detect patterns
            patterns = pattern_detector.detect_all(table)

            # Check confidence threshold
            if patterns.confidence < min_confidence:
                console.print(
                    f"   ⚠️  Confidence {patterns.confidence:.0%} below threshold {min_confidence:.0%}",
                    style="yellow",
                )

            # Generate YAML
            if merged_fields is not None:
                # Create entity dict with merged fields
                entity_name = entity_generator._table_to_entity_name(table.table_name)
                entity = {
                    "entity": entity_name,
                    "schema": table.schema,
                    "description": f"Auto-generated from {table.schema}.{table.table_name}",
                    "fields": merged_fields,
                    "patterns": patterns.patterns + (["translation"] if merged_fields else []),
                    "_metadata": {
                        "source_table": f"{table.schema}.{table.table_name}",
                        "confidence": patterns.confidence,
                        "detected_patterns": patterns.patterns,
                        "generated_by": "specql-reverse-schema",
                        "generated_at": entity_generator._get_timestamp(),
                    },
                }
                yaml_output = entity_generator._generate_yaml(entity)
            else:
                yaml_output = entity_generator.generate(table, patterns)

            # Write file (unless preview)
            if not preview:
                output_path = _write_yaml_file(yaml_output, table, output_dir)
                console.print(f"   ✅ Written to {output_path}", style="green")
            else:
                console.print(f"   👁️  Preview:\n{yaml_output}", style="dim")

            results.append((sql_file, patterns.confidence, len(table.columns)))

        except Exception as e:
            console.print(f"   ❌ Failed: {e}", style="red")
            results.append((sql_file, 0, 0))

    # Summary
    _print_summary(results, min_confidence)


def _write_yaml_file(yaml_content: str, table, output_dir: str) -> Path:
    """Write YAML to output directory with schema/entity.yaml structure"""
    entity_name = table.table_name.removeprefix("tb_").removeprefix("tv_")

    # Create schema subdirectory
    schema_dir = Path(output_dir) / table.schema
    schema_dir.mkdir(parents=True, exist_ok=True)

    # Write entity file
    output_path = schema_dir / f"{entity_name}.yaml"
    output_path.write_text(yaml_content)

    return output_path


def _print_summary(results, min_confidence):
    """Print processing summary"""
    console.print("\n[bold]📊 Summary:[/bold]")
    console.print(f"  Total files: {len(results)}")

    successful = [r for r in results if r[1] > 0]
    if successful:
        avg_confidence = sum(r[1] for r in successful) / len(successful)
        above_threshold = sum(1 for r in successful if r[1] >= min_confidence)
        total_columns = sum(r[2] for r in successful)

        console.print(f"  Average confidence: {avg_confidence:.0%}")
        console.print(
            f"  Above threshold ({min_confidence:.0%}): {above_threshold}/{len(successful)}"
        )
        console.print(f"  Total columns processed: {total_columns}")
    else:
        console.print("  No successful conversions", style="yellow")
