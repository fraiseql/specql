#!/usr/bin/env python3
"""
Migrate Pattern Library Data to PostgreSQL

Phase 5: Migrate existing pattern data from SQLite to PostgreSQL
using the repository pattern architecture.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.application.services.pattern_service_factory import get_pattern_service
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PatternMigrator:
    """Migrates pattern data from SQLite to PostgreSQL"""

    def __init__(self, sqlite_path: str, dry_run: bool = False):
        self.sqlite_path = Path(sqlite_path)
        self.dry_run = dry_run
        self.service = get_pattern_service()

    def migrate(self) -> Dict[str, Any]:
        """Perform the migration"""
        results = {
            'success': True,
            'patterns_migrated': 0,
            'patterns_skipped': 0,
            'errors': [],
            'warnings': []
        }

        try:
            # Load patterns from SQLite
            sqlite_patterns = self._load_sqlite_patterns()

            if not sqlite_patterns:
                logger.info("No patterns found in SQLite database")
                return results

            logger.info(f"Found {len(sqlite_patterns)} patterns in SQLite")

            # Migrate each pattern
            for pattern_name, pattern_data in sqlite_patterns.items():
                try:
                    # Check if pattern already exists in PostgreSQL
                    try:
                        self.service.get_pattern(pattern_name)
                        logger.info(f"Pattern {pattern_name} already exists in PostgreSQL, skipping")
                        results['patterns_skipped'] += 1
                        continue
                    except ValueError:
                        # Pattern doesn't exist, proceed with migration
                        pass

                    # Convert to domain entity
                    pattern = self._convert_to_domain_entity(pattern_name, pattern_data)

                    if not self.dry_run:
                        # Save to PostgreSQL
                        self.service.repository.save(pattern)
                        logger.info(f"Migrated pattern: {pattern_name}")
                    else:
                        logger.info(f"Would migrate pattern: {pattern_name} (dry run)")

                    results['patterns_migrated'] += 1

                except Exception as e:
                    error_msg = f"Failed to migrate pattern {pattern_name}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)

            # Summary
            logger.info(f"Migration complete: {results['patterns_migrated']} migrated, {results['patterns_skipped']} skipped")

        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Migration failed: {e}")
            logger.error(f"Migration failed: {e}")

        return results

    def _load_sqlite_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns from SQLite database"""
        import sqlite3

        patterns = {}

        if not self.sqlite_path.exists():
            logger.warning(f"SQLite database not found: {self.sqlite_path}")
            return patterns

        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Find pattern tables
            cur.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND (name LIKE '%pattern%' OR name = 'patterns')
            """)
            tables = cur.fetchall()

            if not tables:
                logger.warning("No pattern tables found in SQLite database")
                conn.close()
                return patterns

            # Use the first pattern table found
            table_name = tables[0]['name']
            logger.info(f"Using pattern table: {table_name}")

            # Get all patterns
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()

            for row in rows:
                row_dict = dict(row)
                # Try different possible name columns
                pattern_name = (row_dict.get('name') or
                              row_dict.get('pattern_name') or
                              row_dict.get('title'))

                if pattern_name:
                    patterns[pattern_name] = row_dict

            conn.close()
            logger.info(f"Loaded {len(patterns)} patterns from SQLite")

        except Exception as e:
            logger.error(f"Failed to load patterns from SQLite: {e}")
            raise

        return patterns

    def _convert_to_domain_entity(self, pattern_name: str, data: Dict[str, Any]) -> Pattern:
        """Convert SQLite data to Pattern domain entity"""
        import json

        # Extract and normalize data
        category_str = data.get('category', 'workflow')
        try:
            category = PatternCategory(category_str.lower())
        except ValueError:
            logger.warning(f"Unknown category '{category_str}' for pattern {pattern_name}, defaulting to 'workflow'")
            category = PatternCategory.WORKFLOW

        description = data.get('description', f'Pattern: {pattern_name}')

        # Handle parameters (could be JSON string or dict)
        parameters = data.get('parameters', {})
        if isinstance(parameters, str):
            try:
                parameters = json.loads(parameters)
            except Exception:
                parameters = {}

        # Handle implementation (could be JSON string or dict)
        implementation = data.get('implementation', {})
        if isinstance(implementation, str):
            try:
                implementation = json.loads(implementation)
            except Exception:
                implementation = {}

        # Handle source type
        source_type_str = data.get('source_type', 'migrated')
        try:
            source_type = SourceType(source_type_str.lower())
        except ValueError:
            source_type = SourceType.MIGRATED

        # Create pattern entity
        pattern = Pattern(
            id=None,  # Will be set by database
            name=pattern_name,
            category=category,
            description=description,
            parameters=parameters,
            implementation=implementation,
            source_type=source_type,
            complexity_score=data.get('complexity_score'),
            deprecated=data.get('deprecated', False),
            deprecated_reason=data.get('deprecated_reason'),
            times_instantiated=data.get('times_instantiated', 0)
        )

        return pattern


def main():
    """Main migration script"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate pattern library data to PostgreSQL")
    parser.add_argument(
        "--sqlite-db",
        default="pattern_library.db",
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually doing it"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check environment
    if not os.getenv('SPECQL_DB_URL'):
        logger.error("SPECQL_DB_URL environment variable must be set")
        sys.exit(1)

    logger.info("Starting pattern library migration to PostgreSQL")
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    # Perform migration
    migrator = PatternMigrator(args.sqlite_db, dry_run=args.dry_run)
    results = migrator.migrate()

    # Report results
    if results['success']:
        logger.info("Migration completed successfully")
        logger.info(f"Patterns migrated: {results['patterns_migrated']}")
        logger.info(f"Patterns skipped: {results['patterns_skipped']}")

        if results['warnings']:
            logger.warning(f"Warnings: {len(results['warnings'])}")
            for warning in results['warnings']:
                logger.warning(f"  - {warning}")

        if results['errors']:
            logger.error(f"Errors: {len(results['errors'])}")
            for error in results['errors']:
                logger.error(f"  - {error}")
            sys.exit(1)
    else:
        logger.error("Migration failed")
        for error in results['errors']:
            logger.error(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()