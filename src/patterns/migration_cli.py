#!/usr/bin/env python3
"""
SpecQL Pattern Migration CLI

Command-line tool for analyzing SpecQL entities and suggesting pattern migrations
from manual SQL implementations to declarative patterns.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from .migration_analyzer import MigrationAnalyzer, MigrationSuggestion


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze SpecQL entities and suggest pattern migrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single entity
  python -m src.patterns.migration_cli entities/examples/contract.yaml

  # Analyze all entities in a directory
  python -m src.patterns.migration_cli entities/

  # Generate detailed migration report
  python -m src.patterns.migration_cli entities/ --report migration_report.md

  # Show only high-confidence suggestions
  python -m src.patterns.migration_cli entities/ --min-confidence 0.8
        """,
    )

    parser.add_argument(
        "path", type=Path, help="Path to entity YAML file or directory containing entities"
    )

    parser.add_argument("--report", type=Path, help="Generate detailed migration report to file")

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence threshold (0.0-1.0, default: 0.0)",
    )

    parser.add_argument(
        "--pattern", help="Filter suggestions to specific pattern type (e.g., crud/create)"
    )

    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    # Validate arguments
    if not args.path.exists():
        print(f"Error: Path {args.path} does not exist", file=sys.stderr)
        sys.exit(1)

    if args.min_confidence < 0.0 or args.min_confidence > 1.0:
        print("Error: min-confidence must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)

    # Initialize analyzer
    analyzer = MigrationAnalyzer()

    # Analyze entities
    suggestions = []
    if args.path.is_file():
        if not args.quiet:
            print(f"Analyzing {args.path}...")
        suggestions = analyzer.analyze_entity(args.path)
    else:
        if not args.quiet:
            print(f"Analyzing entities in {args.path}...")
        suggestions = analyzer.analyze_directory(args.path)

    # Filter suggestions
    filtered_suggestions = [s for s in suggestions if s.confidence >= args.min_confidence]

    if args.pattern:
        filtered_suggestions = [s for s in filtered_suggestions if s.pattern_type == args.pattern]

    # Display results
    if not args.quiet:
        print(f"\nFound {len(filtered_suggestions)} migration suggestions")

    if filtered_suggestions:
        display_suggestions(filtered_suggestions)

        # Generate report if requested
        if args.report:
            if not args.quiet:
                print(f"\nGenerating detailed report to {args.report}...")
            report = analyzer.generate_migration_report(filtered_suggestions)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with open(args.report, "w") as f:
                f.write(report)
            print(f"Report saved to {args.report}")
    else:
        if not args.quiet:
            print("No migration suggestions found with current filters.")

    # Exit with success/failure based on findings
    sys.exit(0 if filtered_suggestions else 1)


def display_suggestions(suggestions: List[MigrationSuggestion]):
    """Display migration suggestions in a readable format."""
    # Group by entity
    by_entity = {}
    for suggestion in suggestions:
        entity = suggestion.entity_name
        if entity not in by_entity:
            by_entity[entity] = []
        by_entity[entity].append(suggestion)

    # Display by entity
    for entity_name, entity_suggestions in by_entity.items():
        print(f"\n📋 {entity_name} ({len(entity_suggestions)} suggestions)")

        # Group by pattern type
        by_pattern = {}
        for suggestion in entity_suggestions:
            pattern = suggestion.pattern_type
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(suggestion)

        for pattern_type, pattern_suggestions in by_pattern.items():
            print(f"  🔄 {pattern_type}")

            for suggestion in pattern_suggestions:
                confidence_pct = int(suggestion.confidence * 100)
                print(f"    ✓ {suggestion.action_name} ({confidence_pct}% confidence)")
                print(f"      {suggestion.description}")

                if suggestion.benefits:
                    print("      Benefits:")
                    for benefit in suggestion.benefits:
                        print(f"        • {benefit}")


if __name__ == "__main__":
    main()
