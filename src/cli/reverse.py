"""
CLI commands for reverse engineering SQL functions to SpecQL YAML

Usage:
    specql reverse function.sql
    specql reverse reference_sql/**/*.sql --output-dir=entities/
    specql reverse function.sql --no-ai --preview
"""

import click
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser
from src.reverse_engineering.ai_enhancer import AIEnhancer
from src.reverse_engineering.java.java_parser import JavaParser


@dataclass
class JavaProcessingResult:
    """Wrapper for Java processing results with confidence"""

    entities: List[Any]
    errors: List[str]
    confidence: float

    def __post_init__(self):
        if not self.entities:
            self.confidence = 0.0


@click.command()
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", type=click.Path(), help="Output directory for YAML files"
)
@click.option(
    "--min-confidence", type=float, default=0.80, help="Minimum confidence threshold"
)
@click.option("--no-ai", is_flag=True, help="Skip AI enhancement (faster)")
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option("--compare", is_flag=True, help="Generate comparison report")
@click.option(
    "--use-heuristics/--no-heuristics", default=True, help="Use heuristic enhancements"
)
@click.option("--discover-patterns", is_flag=True, help="Suggest applicable patterns")
def reverse(
    input_files,
    output_dir,
    min_confidence,
    no_ai,
    preview,
    compare,
    use_heuristics,
    discover_patterns,
):
    """
    Reverse engineer SQL functions, Java JPA entities, or enhance entity YAML with patterns

    Examples:
        specql reverse function.sql
        specql reverse reference_sql/**/*.sql -o entities/
        specql reverse function.sql --no-ai --preview
        specql reverse entity.yaml --discover-patterns
        specql reverse Contact.java --output-dir entities/
        specql reverse src/main/java/com/example/ --output-dir entities/
    """
    if not input_files:
        click.echo("❌ No input files specified")
        return

    # Initialize parser with requested options
    parser = AlgorithmicParser(
        use_heuristics=use_heuristics,
        use_ai=not no_ai,
        enable_pattern_discovery=discover_patterns,
    )

    # Process files
    results = []
    for input_file in input_files:
        click.echo(f"🔄 Processing {input_file}...")

        try:
            file_path = Path(input_file)

            # Check file type
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                # Process YAML entity file
                result = _process_entity_file(input_file, discover_patterns)
                results.append((input_file, result))
            elif file_path.suffix.lower() == ".java":
                # Process Java file
                result = _process_java_file(
                    input_file, min_confidence, preview, output_dir
                )
                results.append((input_file, result))
            else:
                # Process SQL file
                with open(input_file, "r") as f:
                    sql = f.read()

                # Parse and enhance
                result = parser.parse(sql)

                # Check confidence threshold
                click.echo(".0%")

                if result.confidence < min_confidence:
                    click.echo(
                        f"   ⚠️  Confidence {result.confidence:.0%} below threshold {min_confidence:.0%}"
                    )

                results.append((input_file, result))

                # Write YAML if not preview mode and output dir specified
                if not preview and output_dir:
                    _write_yaml_file(result, output_dir, input_file)

        except Exception as e:
            click.echo(f"❌ Failed to process {input_file}: {e}")
            results.append((input_file, None))

    # Summary
    _print_summary(results, min_confidence)

    # Comparison report
    if compare:
        _generate_comparison_report(results)


def _process_entity_file(input_file: str, discover_patterns: bool) -> Dict[str, Any]:
    """Process YAML entity file and optionally suggest patterns"""
    # Load entity spec
    with open(input_file, "r") as f:
        entity_spec = yaml.safe_load(f)

    if discover_patterns:
        # Get pattern suggestions
        enhancer = AIEnhancer()
        entity_spec = enhancer.enhance_entity(entity_spec)

        # Display suggestions
        if "suggested_patterns" in entity_spec:
            suggestions = entity_spec["suggested_patterns"]
            if suggestions:
                click.echo(
                    f"\n💡 Pattern suggestions for {entity_spec.get('entity', 'entity')}:"
                )
                for suggestion in suggestions:
                    confidence_pct = suggestion["confidence"]
                    click.secho(f"  • {suggestion['name']} ", fg="cyan", nl=False)
                    click.echo(f"({confidence_pct})")
                    click.echo(f"    {suggestion['description'][:80]}...")

                    if suggestion["popularity"] > 10:
                        click.echo(
                            f"    ⭐ Popular: Used {suggestion['popularity']} times"
                        )

    return entity_spec


def _process_java_file(
    input_file: str, min_confidence: float, preview: bool, output_dir: str
) -> Any:
    """Process Java file and extract JPA entities"""
    java_parser = JavaParser()

    # Parse Java file
    result = java_parser.parse_file(input_file)

    # Validate result
    metrics = java_parser.validate_parse_result(result)

    # Check confidence threshold
    status = "✅" if metrics["confidence"] >= min_confidence else "⚠️"
    click.echo(f"   {status} Confidence: {metrics['confidence']:.0%}")

    if metrics["confidence"] < min_confidence:
        click.echo(
            f"   ⚠️  Confidence {metrics['confidence']:.0%} below threshold {min_confidence:.0%}"
        )

    # Report entities found
    if result.entities:
        click.echo(f"   📋 Found {len(result.entities)} entities:")
        for entity in result.entities:
            click.echo(f"     • {entity.name} → {entity.table}")
    else:
        click.echo("   📋 No entities found")

    # Report errors
    if result.errors:
        click.echo(f"   ❌ {len(result.errors)} errors:")
        for error in result.errors[:3]:  # Show first 3 errors
            click.echo(f"     • {error}")
        if len(result.errors) > 3:
            click.echo(f"     • ... and {len(result.errors) - 3} more")

    # Write YAML files if not preview mode and output dir specified
    if not preview and output_dir and result.entities:
        _write_java_yaml_files(result.entities, output_dir, input_file)

    # Return wrapped result with confidence
    return JavaProcessingResult(
        entities=result.entities, errors=result.errors, confidence=metrics["confidence"]
    )


def _write_yaml_file(result, output_dir, sql_file):
    """Write conversion result to YAML file"""
    output_path = Path(output_dir) / f"{result.function_name}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = AlgorithmicParser()._to_yaml(result)
    with open(output_path, "w") as f:
        f.write(yaml_content)

    click.echo(f"   💾 Written to {output_path}")


def _write_java_yaml_files(entities, output_dir, java_file):
    """Write Java entities to YAML files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for entity in entities:
        # Convert entity to YAML
        yaml_content = _entity_to_yaml(entity)

        # Write to file
        filename = f"{entity.name}.yaml"
        file_path = output_path / filename
        with open(file_path, "w") as f:
            f.write(yaml_content)

        click.echo(f"   💾 Written {entity.name} to {file_path}")


def _entity_to_yaml(entity) -> str:
    """Convert Entity object to YAML string"""
    entity_dict = {
        "entity": entity.name,
        "schema": entity.schema,
        "table": entity.table,
        "fields": {},
    }

    for field_name, field in entity.fields.items():
        field_dict = {"type": field.type_name}

        # Add optional properties
        if hasattr(field, "nullable") and field.nullable is not None:
            field_dict["nullable"] = field.nullable
        if hasattr(field, "unique") and field.unique is not None:
            field_dict["unique"] = field.unique

        entity_dict["fields"][field_name] = field_dict

    return yaml.dump(entity_dict, default_flow_style=False, sort_keys=False)


def _print_summary(results: List[Tuple[str, Any]], min_confidence: float):
    """Print processing summary"""
    click.echo("\n📊 Summary:")
    click.echo(f"  Total files: {len(results)}")

    successful_results = [r for _, r in results if r is not None]
    if successful_results:
        # Handle different result types
        confidences = []
        for r in successful_results:
            if hasattr(r, "confidence"):
                # SQL parsing result or JavaProcessingResult
                confidences.append(r.confidence)

        if confidences:
            sum(confidences) / len(confidences)
            above_threshold = sum(1 for c in confidences if c >= min_confidence)

            click.echo(".0%")
            click.echo(f"  Above threshold ({min_confidence:.0%}): {above_threshold}")
        else:
            click.echo("  No confidence metrics available")
    else:
        click.echo("  No successful conversions")

    failed_count = sum(1 for _, r in results if r is None)
    if failed_count > 0:
        click.echo(f"  Failed: {failed_count}")


def _generate_comparison_report(results: List[Tuple[str, Any]]):
    """Generate comparison report between original SQL and generated YAML"""
    click.echo("\n📋 Comparison Report:")

    for sql_file, result in results:
        if result is None:
            continue

        click.echo(f"\n{sql_file}:")
        click.echo(f"  Function: {result.function_name}")
        click.echo(f"  Schema: {result.schema}")
        click.echo(f"  Confidence: {result.confidence:.0%}")

        if hasattr(result, "metadata") and result.metadata:
            if "intent" in result.metadata:
                click.echo(f"  Intent: {result.metadata['intent'][:60]}...")
            if "detected_patterns" in result.metadata:
                click.echo(
                    f"  Patterns: {', '.join(result.metadata['detected_patterns'])}"
                )
            if "variable_purposes" in result.metadata:
                purposes = result.metadata["variable_purposes"]
                if purposes:
                    click.echo(f"  Variables: {len(purposes)} analyzed")

        if result.warnings:
            click.echo(f"  Warnings: {len(result.warnings)}")
