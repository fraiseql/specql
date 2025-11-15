"""
Round-trip testing framework for PL/pgSQL.

Tests the complete bidirectional flow:
1. Original PostgreSQL DDL
2. Parse to SpecQL YAML
3. Generate PostgreSQL DDL from YAML
4. Compare original vs generated
"""

import pytest
import tempfile
import psycopg
from pathlib import Path
from typing import List, Optional

from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.generators.plpgsql.schema_generator import SchemaGenerator
from tests.utils.schema_comparison import SchemaComparator, assert_tables_equivalent
from tests.utils.test_db_utils import (
    create_test_database,
    drop_test_database,
    execute_sql,
    get_test_connection,
)


class RoundTripTest:
    """Base class for round-trip tests"""

    def __init__(self):
        self.parser = PLpgSQLParser(confidence_threshold=0.70)
        self.generator = SchemaGenerator()
        self.original_db = None
        self.generated_db = None

    def setup_databases(self):
        """Create two test databases: original and generated"""
        self.original_db = create_test_database(prefix="original_")
        self.generated_db = create_test_database(prefix="generated_")

    def teardown_databases(self):
        """Drop test databases"""
        if self.original_db:
            drop_test_database(self.original_db)
        if self.generated_db:
            drop_test_database(self.generated_db)

    def run_round_trip(
        self,
        original_ddl: str,
        schema_name: str = "public",
        expected_tables: Optional[List[str]] = None,
    ) -> None:
        """
        Run complete round-trip test.

        Args:
            original_ddl: Original PostgreSQL DDL
            schema_name: Schema to test
            expected_tables: List of expected table names (for validation)
        """
        # Step 1: Apply original DDL to original database
        with get_test_connection(self.original_db) as conn:
            execute_sql(conn, original_ddl)
            conn.commit()

        # Step 2: Parse original database to SpecQL entities
        entities = self.parser.parse_database(
            connection_string=f"postgresql://lionel@localhost:5432/{self.original_db}",
            schemas=[schema_name],
        )

        # Validate expected number of entities
        if expected_tables is not None:
            entity_names = {e.name for e in entities}
            expected_set = set(expected_tables)
            assert entity_names == expected_set, (
                f"Expected tables {expected_set}, got {entity_names}"
            )

        # Step 3: Generate DDL from SpecQL entities
        generated_ddl = self.generator.generate_schema(entities)

        # Step 4: Apply generated DDL to generated database
        with get_test_connection(self.generated_db) as conn:
            execute_sql(conn, generated_ddl)
            conn.commit()

        # Step 5: Compare schemas for equivalence
        with get_test_connection(self.original_db) as orig_conn:
            with get_test_connection(self.generated_db) as gen_conn:
                for entity in entities:
                    table_name = self.generator._get_table_name(entity)

                    # Compare each table individually using separate connections
                    orig_comparator = SchemaComparator(orig_conn)
                    gen_comparator = SchemaComparator(gen_conn)

                    orig_schema = orig_comparator.extract_table_schema(
                        schema_name, table_name
                    )
                    gen_schema = gen_comparator.extract_table_schema(
                        schema_name, table_name
                    )

                    is_equivalent, differences = orig_comparator.compare_tables(
                        orig_schema, gen_schema
                    )
                    assert is_equivalent, (
                        f"Table {table_name} not equivalent: {differences}"
                    )

    def run_round_trip_with_yaml(
        self, original_ddl: str, schema_name: str = "public"
    ) -> str:
        """
        Run round-trip and return intermediate YAML for inspection.

        Returns:
            The generated SpecQL YAML
        """
        # Step 1: Apply original DDL
        with get_test_connection(self.original_db) as conn:
            execute_sql(conn, original_ddl)
            conn.commit()

        # Step 2: Parse to entities
        entities = self.parser.parse_database(
            connection_string=f"postgresql://lionel@localhost:5432/{self.original_db}",
            schemas=[schema_name],
        )

        # Step 3: Convert entities to YAML
        yaml_content = self._entities_to_yaml(entities)

        return yaml_content

    def _entities_to_yaml(self, entities: List) -> str:
        """Convert entities to SpecQL YAML format"""
        from src.utils.yaml_utils import entities_to_yaml_string

        return entities_to_yaml_string(entities)


@pytest.fixture
def round_trip_tester():
    """Fixture that provides round-trip testing infrastructure"""
    tester = RoundTripTest()
    tester.setup_databases()

    yield tester

    tester.teardown_databases()
