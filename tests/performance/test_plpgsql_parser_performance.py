"""Performance benchmarks for PL/pgSQL parser"""

import time
import psycopg
from pathlib import Path
from typing import List, Dict, Any
import pytest
from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.core.universal_ast import UniversalEntity


class TestPLpgSQLParserPerformance:
    """Performance benchmarks for PL/pgSQL parser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return PLpgSQLParser()

    @pytest.fixture
    def test_db_connection(self, db_config):
        """Database connection for performance tests"""
        conn_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        conn = psycopg.connect(conn_string)
        yield conn
        conn.close()

    def test_ddl_parsing_performance_small(self, parser, benchmark):
        """Benchmark parsing small DDL file"""
        ddl_content = self._generate_test_ddl(5, 10)  # 5 tables, 10 fields each

        def parse_ddl():
            return parser.parse_ddl_string(ddl_content)

        result = benchmark(parse_ddl)

        assert len(result) == 5
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_ddl_parsing_performance_medium(self, parser, benchmark):
        """Benchmark parsing medium DDL file"""
        ddl_content = self._generate_test_ddl(20, 15)  # 20 tables, 15 fields each

        def parse_ddl():
            return parser.parse_ddl_string(ddl_content)

        result = benchmark(parse_ddl)

        assert len(result) == 20
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_ddl_parsing_performance_large(self, parser, benchmark):
        """Benchmark parsing large DDL file"""
        ddl_content = self._generate_test_ddl(50, 20)  # 50 tables, 20 fields each

        def parse_ddl():
            return parser.parse_ddl_string(ddl_content)

        result = benchmark(parse_ddl)

        assert len(result) == 50
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_database_parsing_performance_small(
        self, test_db_connection, db_config, benchmark
    ):
        """Benchmark parsing small database schema"""
        self._setup_test_schema(test_db_connection, 5, 10)

        parser = PLpgSQLParser()
        conn_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        def parse_db():
            return parser.parse_database(conn_string, schemas=["perf_test"])

        result = benchmark(parse_db)

        assert len(result) == 5
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_database_parsing_performance_medium(
        self, test_db_connection, db_config, benchmark
    ):
        """Benchmark parsing medium database schema"""
        self._setup_test_schema(test_db_connection, 20, 15)

        parser = PLpgSQLParser()
        conn_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        def parse_db():
            return parser.parse_database(conn_string, schemas=["perf_test"])

        result = benchmark(parse_db)

        assert len(result) == 20
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_function_parsing_performance(
        self, test_db_connection, db_config, benchmark
    ):
        """Benchmark parsing database with functions"""
        self._setup_test_schema_with_functions(test_db_connection, 10, 5)

        parser = PLpgSQLParser()
        conn_string = f"postgresql://{db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"

        def parse_db_with_functions():
            return parser.parse_database(
                conn_string, schemas=["perf_test"], include_functions=True
            )

        result = benchmark(parse_db_with_functions)

        assert len(result) >= 10  # At least the entities
        assert all(isinstance(e, UniversalEntity) for e in result)

    def test_memory_usage_ddl_parsing(self, parser):
        """Test memory usage for large DDL parsing"""
        import psutil
        import os

        # Generate large DDL
        ddl_content = self._generate_test_ddl(100, 25)  # 100 tables, 25 fields each

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        start_time = time.time()
        result = parser.parse_ddl_string(ddl_content)
        end_time = time.time()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        parsing_time = end_time - start_time

        print(
            f"Large DDL parsing: {parsing_time:.2f}s, {memory_used:.1f}MB memory used"
        )

        assert len(result) == 100
        assert parsing_time < 5.0  # Should complete in under 5 seconds
        assert memory_used < 100.0  # Should use less than 100MB

    def test_confidence_filtering_performance(self, parser, benchmark):
        """Benchmark confidence filtering performance"""
        # Generate DDL with mixed confidence levels
        ddl_content = self._generate_mixed_confidence_ddl(50)

        def parse_with_filtering():
            return parser.parse_ddl_string(ddl_content)

        result = benchmark(parse_with_filtering)

        # Should filter out low confidence entities
        assert len(result) < 50

    def _generate_test_ddl(self, num_tables: int, fields_per_table: int) -> str:
        """Generate test DDL with specified number of tables and fields"""
        ddl_parts = ["CREATE SCHEMA test_schema;"]

        for i in range(num_tables):
            table_name = f"tb_entity_{i:03d}"
            ddl_parts.append(f"CREATE TABLE test_schema.{table_name} (")

            field_defs = []
            field_defs.append(
                "pk_entity INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY"
            )
            field_defs.append("id UUID NOT NULL DEFAULT gen_random_uuid()")
            field_defs.append("identifier TEXT")

            # Add additional fields
            for j in range(fields_per_table - 3):
                field_defs.append(f"field_{j} TEXT")

            # Add audit fields
            field_defs.append("created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
            field_defs.append("updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
            field_defs.append("deleted_at TIMESTAMPTZ")

            ddl_parts.append(",\n    ".join(field_defs))
            ddl_parts.append(");")

        return "\n".join(ddl_parts)

    def _generate_mixed_confidence_ddl(self, num_tables: int) -> str:
        """Generate DDL with mixed confidence levels"""
        ddl_parts = ["CREATE SCHEMA test_schema;"]

        for i in range(num_tables):
            if i % 3 == 0:
                # High confidence (Trinity pattern)
                table_name = f"tb_contact_{i}"
                ddl_parts.extend(
                    [
                        f"CREATE TABLE test_schema.{table_name} (",
                        "    pk_contact INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,",
                        "    id UUID NOT NULL DEFAULT gen_random_uuid(),",
                        "    identifier TEXT,",
                        "    email TEXT NOT NULL,",
                        "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),",
                        "    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),",
                        "    deleted_at TIMESTAMPTZ",
                        ");",
                    ]
                )
            elif i % 3 == 1:
                # Medium confidence (partial Trinity)
                table_name = f"tb_partial_{i}"
                ddl_parts.extend(
                    [
                        f"CREATE TABLE test_schema.{table_name} (",
                        "    id UUID NOT NULL DEFAULT gen_random_uuid(),",
                        "    identifier TEXT,",
                        "    name TEXT NOT NULL,",
                        "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
                        ");",
                    ]
                )
            else:
                # Low confidence (no patterns)
                table_name = f"tb_simple_{i}"
                ddl_parts.extend(
                    [
                        f"CREATE TABLE test_schema.{table_name} (",
                        "    id INTEGER,",
                        "    value TEXT",
                        ");",
                    ]
                )

        return "\n".join(ddl_parts)

    def _setup_test_schema(self, conn, num_tables: int, fields_per_table: int):
        """Set up test schema in database"""
        with conn.cursor() as cur:
            # Clean up
            cur.execute("DROP SCHEMA IF EXISTS perf_test CASCADE")
            cur.execute("CREATE SCHEMA perf_test")

            # Create tables
            for i in range(num_tables):
                table_name = f"tb_entity_{i:03d}"
                cur.execute(f"DROP TABLE IF EXISTS perf_test.{table_name}")

                field_defs = []
                field_defs.append(
                    "pk_entity INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY"
                )
                field_defs.append("id UUID NOT NULL DEFAULT gen_random_uuid()")
                field_defs.append("identifier TEXT")

                for j in range(fields_per_table - 3):
                    field_defs.append(f"field_{j} TEXT")

                field_defs.append("created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
                field_defs.append("updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
                field_defs.append("deleted_at TIMESTAMPTZ")

                fields_sql = ", ".join(field_defs)
                cur.execute(f"CREATE TABLE perf_test.{table_name} ({fields_sql})")

            conn.commit()

    def _setup_test_schema_with_functions(
        self, conn, num_tables: int, functions_per_table: int
    ):
        """Set up test schema with functions"""
        self._setup_test_schema(conn, num_tables, 8)  # Base tables

        with conn.cursor() as cur:
            # Create functions for each table
            for i in range(num_tables):
                table_name = f"tb_entity_{i:03d}"

                for j in range(functions_per_table):
                    func_name = f"process_{table_name}_{j}"
                    cur.execute(f"""
                    CREATE OR REPLACE FUNCTION perf_test.{func_name}(
                        p_id INTEGER
                    ) RETURNS INTEGER AS $$
                    BEGIN
                        UPDATE perf_test.{table_name}
                        SET updated_at = NOW()
                        WHERE pk_entity = p_id;
                        RETURN 1;
                    END;
                    $$ LANGUAGE plpgsql;
                    """)

            conn.commit()
