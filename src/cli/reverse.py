"""
CLI commands for reverse engineering SQL functions to SpecQL YAML

Usage:
    specql reverse function.sql
    specql reverse reference_sql/**/*.sql --output-dir=entities/
    specql reverse function.sql --no-ai --preview
"""

import click
from pathlib import Path
from typing import List, Tuple
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


@click.command()
@click.argument("sql_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory for YAML files")
@click.option("--min-confidence", type=float, default=0.80, help="Minimum confidence threshold")
@click.option("--no-ai", is_flag=True, help="Skip AI enhancement (faster)")
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option("--compare", is_flag=True, help="Generate comparison report")
@click.option("--use-heuristics/--no-heuristics", default=True, help="Use heuristic enhancements")
def reverse(sql_files, output_dir, min_confidence, no_ai, preview, compare, use_heuristics):
    """
    Reverse engineer SQL functions to SpecQL YAML

    Examples:
        specql reverse function.sql
        specql reverse reference_sql/**/*.sql -o entities/
        specql reverse function.sql --no-ai --preview
        specql reverse function.sql --min-confidence=0.90
    """
    if not sql_files:
        click.echo("❌ No SQL files specified")
        return

    # Initialize parser with requested options
    parser = AlgorithmicParser(use_heuristics=use_heuristics, use_ai=not no_ai)

    # Process files
    results = []
    for sql_file in sql_files:
        click.echo(f"🔄 Processing {sql_file}...")

        try:
            # Read SQL
            with open(sql_file, 'r') as f:
                sql = f.read()

            # Parse and enhance
            result = parser.parse(sql)

            # Check confidence threshold
            status = "✅" if result.confidence >= min_confidence else "⚠️"
            click.echo(f"   {status} Confidence: {result.confidence:.0%}")

            if result.confidence < min_confidence:
                click.echo(f"   ⚠️  Confidence {result.confidence:.0%} below threshold {min_confidence:.0%}")

            results.append((sql_file, result))

            # Write YAML if not preview mode and output dir specified
            if not preview and output_dir:
                _write_yaml_file(result, output_dir, sql_file)

        except Exception as e:
            click.echo(f"❌ Failed to process {sql_file}: {e}")
            results.append((sql_file, None))

    # Summary
    _print_summary(results, min_confidence)

    # Comparison report
    if compare:
        _generate_comparison_report(results)


def _write_yaml_file(result, output_dir, sql_file):
    """Write conversion result to YAML file"""
    output_path = Path(output_dir) / f"{result.function_name}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = AlgorithmicParser()._to_yaml(result)
    with open(output_path, "w") as f:
        f.write(yaml_content)

    click.echo(f"   💾 Written to {output_path}")


def _print_summary(results: List[Tuple[str, any]], min_confidence: float):
    """Print processing summary"""
    click.echo(f"\n📊 Summary:")
    click.echo(f"  Total files: {len(results)}")

    successful_results = [r for _, r in results if r is not None]
    if successful_results:
        avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
        above_threshold = sum(1 for r in successful_results if r.confidence >= min_confidence)

        click.echo(f"  Average confidence: {avg_confidence:.0%}")
        click.echo(f"  Above threshold ({min_confidence:.0%}): {above_threshold}")
    else:
        click.echo("  No successful conversions")

    failed_count = sum(1 for _, r in results if r is None)
    if failed_count > 0:
        click.echo(f"  Failed: {failed_count}")


def _generate_comparison_report(results: List[Tuple[str, any]]):
    """Generate comparison report between original SQL and generated YAML"""
    click.echo(f"\n📋 Comparison Report:")

    for sql_file, result in results:
        if result is None:
            continue

        click.echo(f"\n{sql_file}:")
        click.echo(f"  Function: {result.function_name}")
        click.echo(f"  Schema: {result.schema}")
        click.echo(f"  Confidence: {result.confidence:.0%}")

        if hasattr(result, 'metadata') and result.metadata:
            if 'intent' in result.metadata:
                click.echo(f"  Intent: {result.metadata['intent'][:60]}...")
            if 'detected_patterns' in result.metadata:
                click.echo(f"  Patterns: {', '.join(result.metadata['detected_patterns'])}")
            if 'variable_purposes' in result.metadata:
                purposes = result.metadata['variable_purposes']
                if purposes:
                    click.echo(f"  Variables: {len(purposes)} analyzed")

        if result.warnings:
            click.echo(f"  Warnings: {len(result.warnings)}")
