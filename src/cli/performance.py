"""
Performance analysis CLI for SpecQL patterns

Provides commands to benchmark pattern implementations vs manual SQL
"""

import sys
from typing import Optional

from src.testing.performance_benchmark import run_pattern_performance_analysis


def run_performance_analysis(entity_name: str, db_connection: Optional[str] = None) -> None:
    """
    Run performance analysis for a specific entity

    Args:
        entity_name: Name of the entity to analyze
        db_connection: Optional database connection string
    """
    try:
        report = run_pattern_performance_analysis(entity_name, db_connection)
        print(report)
    except Exception as e:
        print(f"❌ Error running performance analysis: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: specql performance <entity_name> [--db-connection=<connection_string>]")
        print("")
        print("Examples:")
        print("  specql performance contact")
        print("  specql performance contact --db-connection=postgresql://user:pass@localhost/db")
        sys.exit(1)

    entity_name = sys.argv[1]
    db_connection = None

    # Parse additional arguments
    for arg in sys.argv[2:]:
        if arg.startswith("--db-connection="):
            db_connection = arg.split("=", 1)[1]

    run_performance_analysis(entity_name, db_connection)


if __name__ == "__main__":
    main()
