"""
CLI commands for reverse engineering tests to SpecQL TestSpec YAML

Usage:
    specql reverse-tests test.sql
    specql reverse-tests tests/**/*.py --output-dir=test_specs/
    specql reverse-tests test.sql --entity=Contact --analyze-coverage
"""

import click
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from src.reverse_engineering.tests.pgtap_test_parser import PgTAPTestParser
from src.reverse_engineering.tests.pytest_test_parser import PytestParser
from src.testing.spec.test_parser_protocol import TestSourceLanguage


@click.command()
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", type=click.Path(), help="Output directory for YAML files"
)
@click.option("--entity", "-e", help="Entity name (auto-detected if not provided)")
@click.option(
    "--analyze-coverage",
    is_flag=True,
    help="Analyze test coverage and suggest missing tests",
)
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format",
)
@click.option("--preview", is_flag=True, help="Preview mode (no files written)")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed processing information"
)
def reverse_tests(
    input_files, output_dir, entity, analyze_coverage, format, preview, verbose
) -> int:
    """
    Reverse engineer test files to SpecQL TestSpec YAML

    Supports multiple test frameworks:
    - pgTAP (SQL): PostgreSQL unit tests
    - pytest (Python): Python unit tests

    Examples:
        specql reverse-tests test_contact.sql
        specql reverse-tests tests/**/*.py -o test_specs/ --entity=Contact
        specql reverse-tests test.sql --analyze-coverage --preview
    """
    if not input_files:
        click.echo("❌ No input files specified")
        click.echo("\nUsage: specql reverse-tests test.sql")
        return 1

    # Initialize parsers
    parsers = {
        TestSourceLanguage.PGTAP: PgTAPTestParser(),
        TestSourceLanguage.PYTEST: PytestParser(),
    }

    # Process files
    results = []
    for input_file in input_files:
        click.echo(f"🔄 Processing {input_file}...")

        try:
            file_path = Path(input_file)

            # Auto-detect test format
            detected_format = _detect_test_format(file_path)
            if not detected_format:
                click.echo(f"⚠️  Could not detect test format for {input_file}")
                continue

            parser = parsers.get(detected_format)
            if not parser:
                click.echo(f"⚠️  No parser available for {detected_format.value} format")
                continue

            # Read and parse test file
            with open(input_file, "r", encoding="utf-8") as f:
                content = f.read()

            parsed_test = parser.parse_test_file(content, str(file_path))

            # Convert to TestSpec
            if hasattr(parser, "map_to_test_spec"):
                test_spec = parser.map_to_test_spec(
                    parsed_test, entity or _infer_entity_name(file_path)
                )
            else:
                # Use separate mapper for parsers that don't implement it directly
                from src.reverse_engineering.tests.pgtap_test_parser import (
                    PgTAPTestSpecMapper,
                )
                from src.reverse_engineering.tests.pytest_test_parser import (
                    PytestTestSpecMapper,
                )

                if isinstance(parser, PgTAPTestParser):
                    mapper = PgTAPTestSpecMapper()
                elif isinstance(parser, PytestParser):
                    mapper = PytestTestSpecMapper()
                else:
                    raise ValueError(f"No mapper available for parser {type(parser)}")

                test_spec = mapper.map_to_test_spec(
                    parsed_test, entity or _infer_entity_name(file_path)
                )

            # Analyze coverage if requested
            if analyze_coverage:
                coverage_analysis = _analyze_test_coverage(test_spec)
                test_spec.metadata["coverage_analysis"] = coverage_analysis

            results.append((input_file, test_spec))

            # Show output in preview mode or write to file
            if preview:
                click.echo(f"\n📋 Generated TestSpec for {input_file}:")
                click.echo("=" * 50)
                if format == "yaml":
                    click.echo(test_spec.to_yaml())
                else:
                    import json

                    click.echo(json.dumps(test_spec.__dict__, indent=2, default=str))
                click.echo("=" * 50)
            elif output_dir:
                _write_test_spec(test_spec, output_dir, input_file, format)

        except Exception as e:
            click.echo(f"❌ Failed to process {input_file}: {e}")
            if verbose:
                import traceback

                traceback.print_exc()
            results.append((input_file, None))

    # Summary
    _print_summary(results, analyze_coverage)

    # Coverage analysis summary
    if analyze_coverage:
        _print_coverage_summary(results)

    return 0


def _detect_test_format(file_path: Path) -> Optional[TestSourceLanguage]:
    """Auto-detect test file format based on file extension and content"""
    suffix = file_path.suffix.lower()

    # Check file extension
    if suffix == ".sql":
        return TestSourceLanguage.PGTAP
    elif suffix in [".py", ".pytest"]:
        return TestSourceLanguage.PYTEST

    # Check content-based detection
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(1000)  # Read first 1000 chars

        # pgTAP indicators
        if "SELECT plan(" in content or "SELECT ok(" in content:
            return TestSourceLanguage.PGTAP

        # pytest indicators
        if "def test_" in content or "import pytest" in content:
            return TestSourceLanguage.PYTEST

    except Exception:
        pass

    raise ValueError(f"Could not detect test format for {file_path}")


def _infer_entity_name(file_path: Path) -> str:
    """Infer entity name from file path"""
    stem = file_path.stem.lower()

    # Remove common test prefixes/suffixes
    for prefix in ["test_", "tests_", "spec_"]:
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]

    for suffix in ["_test", "_tests", "_spec"]:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]

    # Convert snake_case to PascalCase
    return "".join(word.capitalize() for word in stem.split("_"))


def _write_test_spec(test_spec, output_dir, input_file, format):
    """Write test spec to file"""
    output_path = Path(output_dir) / f"{test_spec.test_name}.{format}"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "yaml":
        content = test_spec.to_yaml()
    else:  # json
        import json

        content = json.dumps(test_spec.__dict__, indent=2, default=str)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    click.echo(f"   💾 Written to {output_path}")


def _analyze_test_coverage(test_spec) -> Dict[str, Any]:
    """Analyze test coverage and identify gaps"""
    analysis = {
        "total_scenarios": len(test_spec.scenarios),
        "scenario_categories": {},
        "assertion_types": {},
        "crud_operations": {"create": 0, "read": 0, "update": 0, "delete": 0},
        "missing_tests": [],
        "coverage_score": 0.0,
    }

    # Count scenario categories
    for scenario in test_spec.scenarios:
        category = scenario.category.value
        analysis["scenario_categories"][category] = (
            analysis["scenario_categories"].get(category, 0) + 1
        )

        # Count assertions
        for assertion in scenario.assertions:
            assertion_type = assertion.assertion_type.value
            analysis["assertion_types"][assertion_type] = (
                analysis["assertion_types"].get(assertion_type, 0) + 1
            )

        # Detect CRUD operations
        scenario_text = (scenario.scenario_name + " " + scenario.description).lower()
        if any(word in scenario_text for word in ["create", "insert", "add"]):
            analysis["crud_operations"]["create"] += 1
        if any(word in scenario_text for word in ["read", "get", "select", "find"]):
            analysis["crud_operations"]["read"] += 1
        if any(word in scenario_text for word in ["update", "modify", "change"]):
            analysis["crud_operations"]["update"] += 1
        if any(word in scenario_text for word in ["delete", "remove", "destroy"]):
            analysis["crud_operations"]["delete"] += 1

    # Calculate coverage score (0-100)
    total_crud = sum(analysis["crud_operations"].values())
    crud_coverage = min(100, (total_crud / 4) * 100) if total_crud > 0 else 0

    happy_path_count = analysis["scenario_categories"].get("happy_path", 0)
    error_case_count = analysis["scenario_categories"].get("error_case", 0)
    scenario_balance = (
        min(
            100,
            (
                min(happy_path_count, error_case_count)
                / max(happy_path_count, error_case_count)
            )
            * 100,
        )
        if max(happy_path_count, error_case_count) > 0
        else 0
    )

    analysis["coverage_score"] = (crud_coverage + scenario_balance) / 2

    # Suggest missing tests
    if analysis["crud_operations"]["create"] == 0:
        analysis["missing_tests"].append("Create operation tests")
    if analysis["crud_operations"]["read"] == 0:
        analysis["missing_tests"].append("Read operation tests")
    if analysis["crud_operations"]["update"] == 0:
        analysis["missing_tests"].append("Update operation tests")
    if analysis["crud_operations"]["delete"] == 0:
        analysis["missing_tests"].append("Delete operation tests")

    if analysis["scenario_categories"].get("error_case", 0) == 0:
        analysis["missing_tests"].append("Error case scenarios")

    if analysis["scenario_categories"].get("edge_case", 0) == 0:
        analysis["missing_tests"].append("Edge case scenarios")

    return analysis


def _print_summary(results: List[Tuple[str, Any]], analyze_coverage: bool):
    """Print processing summary"""
    click.echo("\n📊 Summary:")
    click.echo(f"  Total files: {len(results)}")

    successful_results = [r for _, r in results if r is not None]
    if successful_results:
        total_scenarios = sum(len(r.scenarios) for r in successful_results)
        total_assertions = sum(
            sum(len(s.assertions) for s in r.scenarios) for r in successful_results
        )

        click.echo(f"  Test specs generated: {len(successful_results)}")
        click.echo(f"  Total scenarios: {total_scenarios}")
        click.echo(f"  Total assertions: {total_assertions}")

        if analyze_coverage:
            sum(
                r.metadata.get("coverage_analysis", {}).get("coverage_score", 0)
                for r in successful_results
            ) / len(successful_results)
            click.echo(".1f")
    else:
        click.echo("  No successful conversions")

    failed_count = sum(1 for _, r in results if r is None)
    if failed_count > 0:
        click.echo(f"  Failed: {failed_count}")


def _print_coverage_summary(results: List[Tuple[str, Any]]):
    """Print coverage analysis summary"""
    click.echo("\n📈 Coverage Analysis:")

    successful_results = [r for _, r in results if r is not None]
    if not successful_results:
        return

    # Aggregate coverage data
    total_crud = {"create": 0, "read": 0, "update": 0, "delete": 0}
    total_categories = {}
    missing_tests = set()

    for result in successful_results:
        analysis = result.metadata.get("coverage_analysis", {})
        for op, count in analysis.get("crud_operations", {}).items():
            total_crud[op] += count

        for cat, count in analysis.get("scenario_categories", {}).items():
            total_categories[cat] = total_categories.get(cat, 0) + count

        for missing in analysis.get("missing_tests", []):
            missing_tests.add(missing)

    # Print CRUD coverage
    click.echo("  CRUD Operations:")
    for op, count in total_crud.items():
        status = "✅" if count > 0 else "❌"
        click.echo(f"    {status} {op.capitalize()}: {count} tests")

    # Print scenario categories
    click.echo("  Scenario Types:")
    for cat, count in sorted(total_categories.items()):
        click.echo(f"    • {cat.replace('_', ' ').title()}: {count}")

    # Print missing tests
    if missing_tests:
        click.echo("  Suggested Missing Tests:")
        for missing in sorted(missing_tests):
            click.echo(f"    ⚠️  {missing}")

    # Overall assessment
    crud_complete = all(count > 0 for count in total_crud.values())
    has_error_cases = total_categories.get("error_case", 0) > 0
    has_edge_cases = total_categories.get("edge_case", 0) > 0

    if crud_complete and has_error_cases and has_edge_cases:
        click.echo("  🎉 Comprehensive test coverage!")
    elif crud_complete:
        click.echo("  ✅ Good CRUD coverage, consider adding error/edge cases")
    else:
        click.echo("  ⚠️  Incomplete coverage, focus on missing CRUD operations")
