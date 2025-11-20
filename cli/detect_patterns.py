from pathlib import Path

import click

from reverse_engineering.universal_pattern_detector import UniversalPatternDetector
from infrastructure.pattern_detector import PatternDetector
from cli.language_detector import LanguageDetector


@click.command("detect-patterns")
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--min-confidence", type=float, default=0.75, help="Minimum confidence threshold (0.0-1.0)"
)
@click.option(
    "--patterns", multiple=True, help="Specific patterns to detect (e.g., soft-delete, audit-trail)"
)
@click.option(
    "--format", type=click.Choice(["text", "json", "yaml"]), default="text", help="Output format"
)
@click.option("--language", type=str, help="Source language (auto-detected if not specified)")
def detect_patterns(input_files, min_confidence, patterns, format, language):
    """Detect architectural patterns in source code

    Supported patterns:
      - soft-delete: Soft deletion with deleted_at timestamps
      - audit-trail: created_at/updated_at tracking
      - multi-tenant: tenant_id isolation
      - state-machine: Status transitions with validation
      - hierarchical: Parent-child relationships
      - versioning: Version number tracking
      - event-sourcing: Event-driven state changes
      - sharding: Data partitioning strategies
      - cache-invalidation: Cache management patterns
      - rate-limiting: Request throttling
    """

    detector = UniversalPatternDetector()
    all_results = []

    for file_path in input_files:
        if format == "text":
            click.echo(f"\n📁 Analyzing {file_path}...")

        # Auto-detect language if not specified
        if not language:
            detected_lang = LanguageDetector.detect(file_path)
            if detected_lang:
                if format == "text":
                    click.echo(f"   Detected language: {detected_lang}")
                language = detected_lang
            else:
                if format == "text":
                    click.echo(f"   ⚠️ Could not detect language for {file_path}")
                continue

        # Read source code
        try:
            source_code = Path(file_path).read_text()
        except (UnicodeDecodeError, OSError) as e:
            if format == "text":
                click.echo(f"   ❌ Could not read file {file_path}: {e}")
            continue

        # Detect patterns
        if language == "python":
            # Use Django-specific pattern detector for Python files
            django_detector = PatternDetector()
            detected_patterns = django_detector.detect(
                source_code, min_confidence=0.0
            )  # Don't filter here

            # Convert to expected format
            detected_results = {}
            for pattern in detected_patterns:
                detected_results[pattern.name] = {
                    "confidence": pattern.confidence,
                    "evidence": [pattern.explanation] if pattern.explanation else [],
                    "language": language,
                }
        else:
            # Use universal detector for other languages
            if patterns:
                # Only detect specified patterns
                detected_results = {}
                for pattern in patterns:
                    detected_results[pattern] = detector.detect_pattern(
                        source_code, pattern, language
                    )
            else:
                # Detect all patterns
                detected_results = detector.detect_all_patterns(source_code, language)

        # Filter by confidence
        filtered_patterns = {}
        for pattern_name, data in detected_results.items():
            if data["confidence"] >= min_confidence:
                filtered_patterns[pattern_name] = data

        all_results.append({"file": file_path, "language": language, "patterns": filtered_patterns})

        # Display results (only for text format)
        if format == "text":
            if filtered_patterns:
                click.echo(f"   ✓ Found {len(filtered_patterns)} patterns:")
                for pattern_name, data in filtered_patterns.items():
                    confidence_pct = data["confidence"] * 100
                    click.echo(f"      • {pattern_name}: {confidence_pct:.1f}% confidence")
                    if data.get("evidence"):
                        for evidence in data["evidence"][:3]:  # Show top 3 pieces of evidence
                            click.echo(f"        - {evidence}")
            else:
                click.echo(f"   ℹ No patterns detected above {min_confidence:.0%} confidence")

    # Output formatted results
    if format == "json":
        import json

        click.echo(json.dumps(all_results, indent=2))
    elif format == "yaml":
        import yaml

        click.echo(yaml.dump(all_results, default_flow_style=False))

    return all_results
