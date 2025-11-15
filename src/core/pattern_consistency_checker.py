"""
Pattern Library Consistency Checker

Validates data consistency between PostgreSQL and legacy pattern storage
during the Phase 5 pattern library integration.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PatternConsistencyChecker:
    """
    Checks data consistency between PostgreSQL and legacy pattern repositories.

    Used during Phase 5 pattern library integration to ensure data integrity.
    """

    def __init__(self, db_url: str, legacy_patterns_path: Path | None = None):
        self.db_url = db_url
        self.legacy_patterns_path = legacy_patterns_path or Path("pattern_library.db")

    def check_consistency(self) -> Dict[str, Any]:
        """
        Check consistency between PostgreSQL and legacy pattern storage.

        Returns:
            Dict with consistency results and any discrepancies found
        """
        results = {
            'consistent': True,
            'patterns_checked': 0,
            'discrepancies': [],
            'summary': {}
        }

        try:
            # Load data from both sources
            pg_patterns = self._load_postgresql_patterns()
            legacy_patterns = self._load_legacy_patterns()

            results['patterns_checked'] = len(pg_patterns)

            # Compare patterns
            discrepancies = self._compare_patterns(pg_patterns, legacy_patterns)
            results['discrepancies'] = discrepancies
            results['consistent'] = len(discrepancies) == 0

            # Summary
            results['summary'] = {
                'postgresql_patterns': len(pg_patterns),
                'legacy_patterns': len(legacy_patterns),
                'discrepancies_found': len(discrepancies)
            }

            if discrepancies:
                logger.warning(f"Found {len(discrepancies)} pattern data discrepancies")
            else:
                logger.info("Pattern data consistency check passed")

        except Exception as e:
            logger.error(f"Pattern consistency check failed: {e}")
            results['consistent'] = False
            results['error'] = str(e)

        return results

    def _load_postgresql_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns from PostgreSQL"""
        import psycopg

        patterns = {}
        try:
            with psycopg.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            id, name, category, description, parameters, implementation,
                            embedding, times_instantiated, source_type, complexity_score,
                            deprecated, deprecated_reason, replacement_pattern_id,
                            created_at, updated_at
                        FROM pattern_library.domain_patterns
                        ORDER BY name
                    """)

                    for row in cur.fetchall():
                        pattern_name = row[1]  # name is at index 1
                        patterns[pattern_name] = {
                            'id': row[0],
                            'name': row[1],
                            'category': row[2],
                            'description': row[3],
                            'parameters': row[4],
                            'implementation': row[5],
                            'embedding': row[6],
                            'times_instantiated': row[7],
                            'source_type': row[8],
                            'complexity_score': row[9],
                            'deprecated': row[10],
                            'deprecated_reason': row[11],
                            'replacement_pattern_id': row[12],
                            'created_at': str(row[13]) if row[13] else None,
                            'updated_at': str(row[14]) if row[14] else None
                        }

        except Exception as e:
            logger.error(f"Failed to load PostgreSQL patterns: {e}")
            raise

        return patterns

    def _load_legacy_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns from legacy SQLite storage"""
        import sqlite3

        patterns = {}
        try:
            if not self.legacy_patterns_path.exists():
                logger.info("No legacy pattern database found")
                return patterns

            conn = sqlite3.connect(str(self.legacy_patterns_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Try to find patterns table (schema may vary)
            cur.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE '%pattern%'
            """)
            tables = cur.fetchall()

            if not tables:
                logger.info("No pattern tables found in legacy database")
                conn.close()
                return patterns

            # Assume first pattern-like table
            table_name = tables[0]['name']

            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()

            for row in rows:
                row_dict = dict(row)
                # Use 'name' or 'pattern_name' as key
                pattern_name = row_dict.get('name') or row_dict.get('pattern_name')
                if pattern_name:
                    patterns[pattern_name] = row_dict

            conn.close()

        except Exception as e:
            logger.error(f"Failed to load legacy patterns: {e}")
            # Don't raise - legacy might not exist or be accessible

        return patterns

    def _compare_patterns(self, pg_patterns: Dict, legacy_patterns: Dict) -> List[Dict[str, Any]]:
        """Compare patterns between PostgreSQL and legacy storage"""
        discrepancies = []

        # Check all patterns exist in both (if legacy exists)
        if legacy_patterns:
            all_pattern_names = set(pg_patterns.keys()) | set(legacy_patterns.keys())

            for pattern_name in all_pattern_names:
                pg_pattern = pg_patterns.get(pattern_name)
                legacy_pattern = legacy_patterns.get(pattern_name)

                if pg_pattern is None:
                    discrepancies.append({
                        'type': 'missing_in_postgresql',
                        'pattern': pattern_name,
                        'details': f"Pattern {pattern_name} exists in legacy storage but not in PostgreSQL"
                    })
                    continue

                if legacy_pattern is None:
                    discrepancies.append({
                        'type': 'missing_in_legacy',
                        'pattern': pattern_name,
                        'details': f"Pattern {pattern_name} exists in PostgreSQL but not in legacy storage"
                    })
                    continue

                # Compare pattern attributes
                pattern_discrepancies = self._compare_pattern_attributes(pattern_name, pg_pattern, legacy_pattern)
                discrepancies.extend(pattern_discrepancies)
        else:
            # No legacy patterns to compare - this is expected for fresh PostgreSQL setup
            logger.info("No legacy patterns found - assuming fresh PostgreSQL setup")

        return discrepancies

    def _compare_pattern_attributes(self, pattern_name: str, pg_pattern: Dict, legacy_pattern: Dict) -> List[Dict]:
        """Compare pattern attributes between sources"""
        discrepancies = []

        # Key attributes to compare
        attrs_to_check = [
            'category', 'description', 'times_instantiated',
            'source_type', 'complexity_score', 'deprecated'
        ]

        for attr in attrs_to_check:
            pg_value = pg_pattern.get(attr)
            legacy_value = legacy_pattern.get(attr)

            # Normalize types for comparison
            if isinstance(pg_value, str) and isinstance(legacy_value, bytes):
                legacy_value = legacy_value.decode('utf-8')
            elif isinstance(legacy_value, str) and isinstance(pg_value, bytes):
                pg_value = pg_value.decode('utf-8')

            # Handle None vs empty string
            if pg_value == '' and legacy_value is None:
                continue
            if legacy_value == '' and pg_value is None:
                continue

            if pg_value != legacy_value:
                discrepancies.append({
                    'type': 'pattern_attribute_mismatch',
                    'pattern': pattern_name,
                    'attribute': attr,
                    'postgresql_value': pg_value,
                    'legacy_value': legacy_value
                })

        # Special handling for complex attributes
        self._compare_complex_attributes(pattern_name, pg_pattern, legacy_pattern, discrepancies)

        return discrepancies

    def _compare_complex_attributes(self, pattern_name: str, pg_pattern: Dict,
                                  legacy_pattern: Dict, discrepancies: List[Dict]):
        """Compare complex attributes like JSON fields"""

        # Compare parameters (JSON)
        pg_params = pg_pattern.get('parameters')
        legacy_params = legacy_pattern.get('parameters')

        if pg_params != legacy_params:
            # Try to normalize JSON strings
            try:
                import json
                if isinstance(pg_params, str):
                    pg_params = json.loads(pg_params)
                if isinstance(legacy_params, str):
                    legacy_params = json.loads(legacy_params)
            except Exception:
                pass  # Keep as-is for comparison

            if pg_params != legacy_params:
                discrepancies.append({
                    'type': 'pattern_parameters_mismatch',
                    'pattern': pattern_name,
                    'postgresql_value': pg_params,
                    'legacy_value': legacy_params
                })

        # Compare implementation (JSON)
        pg_impl = pg_pattern.get('implementation')
        legacy_impl = legacy_pattern.get('implementation')

        if pg_impl != legacy_impl:
            # Try to normalize JSON strings
            try:
                import json
                if isinstance(pg_impl, str):
                    pg_impl = json.loads(pg_impl)
                if isinstance(legacy_impl, str):
                    legacy_impl = json.loads(legacy_impl)
            except Exception:
                pass  # Keep as-is for comparison

            if pg_impl != legacy_impl:
                discrepancies.append({
                    'type': 'pattern_implementation_mismatch',
                    'pattern': pattern_name,
                    'postgresql_value': pg_impl,
                    'legacy_value': legacy_impl
                })

        # Compare embeddings (arrays)
        pg_embedding = pg_pattern.get('embedding')
        legacy_embedding = legacy_pattern.get('embedding')

        if pg_embedding != legacy_embedding:
            # Handle different array formats
            if pg_embedding and legacy_embedding:
                try:
                    # Convert to lists for comparison
                    if isinstance(pg_embedding, str):
                        import json
                        pg_embedding = json.loads(pg_embedding)
                    if isinstance(legacy_embedding, str):
                        import json
                        legacy_embedding = json.loads(legacy_embedding)

                    # Compare lengths first
                    if len(pg_embedding) != len(legacy_embedding):
                        discrepancies.append({
                            'type': 'pattern_embedding_length_mismatch',
                            'pattern': pattern_name,
                            'postgresql_length': len(pg_embedding),
                            'legacy_length': len(legacy_embedding)
                        })
                    else:
                        # Check if values are close (floating point comparison)
                        max_diff = max(abs(a - b) for a, b in zip(pg_embedding, legacy_embedding))
                        if max_diff > 1e-6:  # Allow small floating point differences
                            discrepancies.append({
                                'type': 'pattern_embedding_mismatch',
                                'pattern': pattern_name,
                                'max_difference': max_diff
                            })
                except Exception as e:
                    discrepancies.append({
                        'type': 'pattern_embedding_parse_error',
                        'pattern': pattern_name,
                        'error': str(e)
                    })