"""
Schema comparison utilities for round-trip testing.

Compares two PostgreSQL schemas for semantic equivalence.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
import re
import psycopg
from psycopg.rows import dict_row


@dataclass
class TableSchema:
    """Represents a PostgreSQL table schema"""

    name: str
    schema: str
    columns: Dict[str, "ColumnSchema"]
    primary_keys: Set[str]
    foreign_keys: List["ForeignKeySchema"]
    unique_constraints: List[Set[str]]
    check_constraints: List[str]
    indexes: List["IndexSchema"]

    def __eq__(self, other: object) -> bool:
        """Check semantic equivalence"""
        if not isinstance(other, TableSchema):
            return False

        return (
            self.name == other.name
            and self.schema == other.schema
            and self.columns_equivalent(other)
            and self.primary_keys == other.primary_keys
            and self.foreign_keys_equivalent(other.foreign_keys)
            and self.unique_constraints_equivalent(other.unique_constraints)
            and self.check_constraints_equivalent(other.check_constraints)
            # Note: Indexes are implementation detail, not semantic
        )

    def columns_equivalent(self, other: "TableSchema") -> bool:
        """Check if columns are semantically equivalent"""
        if set(self.columns.keys()) != set(other.columns.keys()):
            return False

        for col_name in self.columns:
            if not self.columns[col_name].equivalent(other.columns[col_name]):
                return False

        return True

    def foreign_keys_equivalent(self, other_fks: List["ForeignKeySchema"]) -> bool:
        """Check if foreign keys are equivalent (order-independent)"""
        if len(self.foreign_keys) != len(other_fks):
            return False

        # Convert to comparable sets
        self_fk_set = {fk.to_comparable() for fk in self.foreign_keys}
        other_fk_set = {fk.to_comparable() for fk in other_fks}

        return self_fk_set == other_fk_set

    def unique_constraints_equivalent(self, other_constraints: List[Set[str]]) -> bool:
        """Check if unique constraints are equivalent (order-independent)"""
        if len(self.unique_constraints) != len(other_constraints):
            return False

        self_set = {frozenset(uc) for uc in self.unique_constraints}
        other_set = {frozenset(uc) for uc in other_constraints}

        return self_set == other_set

    def check_constraints_equivalent(self, other_checks: List[str]) -> bool:
        """Check if check constraints are equivalent (normalized comparison)"""
        if len(self.check_constraints) != len(other_checks):
            return False

        # Normalize check constraints for comparison
        self_normalized = {self._normalize_check(c) for c in self.check_constraints}
        other_normalized = {self._normalize_check(c) for c in other_checks}

        return self_normalized == other_normalized

    @staticmethod
    def _normalize_check(check_constraint: str) -> str:
        """Normalize check constraint for comparison"""
        # Remove whitespace variations
        normalized = re.sub(r"\s+", " ", check_constraint.strip().lower())
        # Remove parentheses variations
        normalized = re.sub(r"\(\s*", "(", normalized)
        normalized = re.sub(r"\s*\)", ")", normalized)
        return normalized


@dataclass
class ColumnSchema:
    """Represents a PostgreSQL column schema"""

    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]

    def equivalent(self, other: "ColumnSchema") -> bool:
        """Check if columns are semantically equivalent"""
        return (
            self.name == other.name
            and self._normalize_type(self.data_type)
            == self._normalize_type(other.data_type)
            and self.is_nullable == other.is_nullable
            and self._normalize_default(self.default_value)
            == self._normalize_default(other.default_value)
            and self.character_maximum_length == other.character_maximum_length
            and self.numeric_precision == other.numeric_precision
            and self.numeric_scale == other.numeric_scale
        )

    @staticmethod
    def _normalize_type(data_type: str) -> str:
        """Normalize data type for comparison"""
        # Handle type aliases
        type_map = {
            "character varying": "varchar",
            "character": "char",
            "timestamp without time zone": "timestamp",
            "timestamp with time zone": "timestamptz",
            "integer": "int4",
            "bigint": "int8",
            "smallint": "int2",
            "double precision": "float8",
            "real": "float4",
        }

        normalized = data_type.lower().strip()
        return type_map.get(normalized, normalized)

    @staticmethod
    def _normalize_default(default_value: Optional[str]) -> Optional[str]:
        """Normalize default value for comparison"""
        if default_value is None:
            return None

        # Remove type casts
        normalized = re.sub(r"::\w+", "", default_value)
        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized.strip())
        # Normalize quotes
        normalized = normalized.replace("'", "").replace('"', "")

        return normalized.lower()


@dataclass
class ForeignKeySchema:
    """Represents a foreign key constraint"""

    constraint_name: str
    columns: List[str]
    referenced_table: str
    referenced_schema: str
    referenced_columns: List[str]
    on_delete: str
    on_update: str

    def to_comparable(self) -> Tuple:
        """Convert to comparable tuple (for set operations)"""
        return (
            tuple(sorted(self.columns)),
            self.referenced_schema,
            self.referenced_table,
            tuple(sorted(self.referenced_columns)),
            self.on_delete.upper(),
            self.on_update.upper(),
        )


@dataclass
class IndexSchema:
    """Represents a database index"""

    name: str
    columns: List[str]
    is_unique: bool
    index_type: str  # btree, hash, gin, gist, etc.


class SchemaComparator:
    """Compare PostgreSQL schemas for semantic equivalence"""

    def __init__(self, conn: psycopg.Connection):
        self.conn = conn

    def extract_table_schema(self, schema_name: str, table_name: str) -> TableSchema:
        """Extract complete schema for a table"""
        return TableSchema(
            name=table_name,
            schema=schema_name,
            columns=self._extract_columns(schema_name, table_name),
            primary_keys=self._extract_primary_keys(schema_name, table_name),
            foreign_keys=self._extract_foreign_keys(schema_name, table_name),
            unique_constraints=self._extract_unique_constraints(
                schema_name, table_name
            ),
            check_constraints=self._extract_check_constraints(schema_name, table_name),
            indexes=self._extract_indexes(schema_name, table_name),
        )

    def _extract_columns(
        self, schema_name: str, table_name: str
    ) -> Dict[str, ColumnSchema]:
        """Extract column definitions"""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """

        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (schema_name, table_name))
            columns = {}

            for row in cur.fetchall():
                col = ColumnSchema(
                    name=row["column_name"],
                    data_type=row["data_type"],
                    is_nullable=(row["is_nullable"] == "YES"),
                    default_value=row["column_default"],
                    character_maximum_length=row["character_maximum_length"],
                    numeric_precision=row["numeric_precision"],
                    numeric_scale=row["numeric_scale"],
                )
                columns[col.name] = col

            return columns

    def _extract_primary_keys(self, schema_name: str, table_name: str) -> Set[str]:
        """Extract primary key columns"""
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            return {row[0] for row in cur.fetchall()}

    def _extract_foreign_keys(
        self, schema_name: str, table_name: str
    ) -> List[ForeignKeySchema]:
        """Extract foreign key constraints"""
        query = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints rc
              ON rc.constraint_name = tc.constraint_name
              AND rc.constraint_schema = tc.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """

        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (schema_name, table_name))

            # Group by constraint name
            fk_dict: Dict[str, Dict] = {}
            for row in cur.fetchall():
                constraint_name = row["constraint_name"]
                if constraint_name not in fk_dict:
                    fk_dict[constraint_name] = {
                        "constraint_name": constraint_name,
                        "columns": [],
                        "referenced_schema": row["foreign_table_schema"],
                        "referenced_table": row["foreign_table_name"],
                        "referenced_columns": [],
                        "on_delete": row["delete_rule"],
                        "on_update": row["update_rule"],
                    }

                fk_dict[constraint_name]["columns"].append(row["column_name"])
                fk_dict[constraint_name]["referenced_columns"].append(
                    row["foreign_column_name"]
                )

            return [ForeignKeySchema(**fk_data) for fk_data in fk_dict.values()]

    def _extract_unique_constraints(
        self, schema_name: str, table_name: str
    ) -> List[Set[str]]:
        """Extract unique constraints"""
        query = """
            SELECT tc.constraint_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'UNIQUE'
            ORDER BY tc.constraint_name, kcu.ordinal_position
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))

            # Group by constraint name
            constraint_dict: Dict[str, Set[str]] = {}
            for row in cur.fetchall():
                constraint_name, column_name = row
                if constraint_name not in constraint_dict:
                    constraint_dict[constraint_name] = set()
                constraint_dict[constraint_name].add(column_name)

            return list(constraint_dict.values())

    def _extract_check_constraints(
        self, schema_name: str, table_name: str
    ) -> List[str]:
        """Extract check constraints"""
        query = """
            SELECT check_clause
            FROM information_schema.check_constraints cc
            JOIN information_schema.table_constraints tc
              ON cc.constraint_name = tc.constraint_name
              AND cc.constraint_schema = tc.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (schema_name, table_name))
            return [row[0] for row in cur.fetchall()]

    def _extract_indexes(self, schema_name: str, table_name: str) -> List[IndexSchema]:
        """Extract indexes"""
        query = """
            SELECT
                i.relname AS index_name,
                ix.indisunique AS is_unique,
                am.amname AS index_type,
                array_agg(a.attname ORDER BY a.attnum) AS column_names
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON i.relam = am.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = %s AND t.relname = %s
            GROUP BY i.relname, ix.indisunique, am.amname
        """

        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (schema_name, table_name))

            indexes = []
            for row in cur.fetchall():
                indexes.append(
                    IndexSchema(
                        name=row["index_name"],
                        columns=row["column_names"],
                        is_unique=row["is_unique"],
                        index_type=row["index_type"],
                    )
                )

            return indexes

    def compare_tables(
        self, table1: TableSchema, table2: TableSchema
    ) -> Tuple[bool, List[str]]:
        """
        Compare two table schemas for equivalence.

        Returns:
            (is_equivalent, differences) where differences is a list of human-readable differences
        """
        differences = []

        # Check table name and schema
        if table1.name != table2.name:
            differences.append(f"Table name mismatch: {table1.name} vs {table2.name}")

        if table1.schema != table2.schema:
            differences.append(
                f"Schema name mismatch: {table1.schema} vs {table2.schema}"
            )

        # Check columns
        if not table1.columns_equivalent(table2):
            col1_names = set(table1.columns.keys())
            col2_names = set(table2.columns.keys())

            missing_in_2 = col1_names - col2_names
            missing_in_1 = col2_names - col1_names

            if missing_in_2:
                differences.append(f"Columns in table1 but not table2: {missing_in_2}")
            if missing_in_1:
                differences.append(f"Columns in table2 but not table1: {missing_in_1}")

            # Check column differences
            for col_name in col1_names & col2_names:
                col1 = table1.columns[col_name]
                col2 = table2.columns[col_name]

                if not col1.equivalent(col2):
                    differences.append(f"Column {col_name} differs:")
                    if col1.data_type != col2.data_type:
                        differences.append(
                            f"  Type: {col1.data_type} vs {col2.data_type}"
                        )
                    if col1.is_nullable != col2.is_nullable:
                        differences.append(
                            f"  Nullable: {col1.is_nullable} vs {col2.is_nullable}"
                        )
                    if col1.default_value != col2.default_value:
                        differences.append(
                            f"  Default: {col1.default_value} vs {col2.default_value}"
                        )

        # Check primary keys
        if table1.primary_keys != table2.primary_keys:
            differences.append(
                f"Primary keys differ: {table1.primary_keys} vs {table2.primary_keys}"
            )

        # Check foreign keys
        if not table1.foreign_keys_equivalent(table2.foreign_keys):
            differences.append("Foreign keys differ")
            # Detailed FK comparison could be added here

        # Check unique constraints
        if not table1.unique_constraints_equivalent(table2.unique_constraints):
            differences.append("Unique constraints differ")

        # Check check constraints
        if not table1.check_constraints_equivalent(table2.check_constraints):
            differences.append("Check constraints differ")

        return (len(differences) == 0, differences)


def assert_tables_equivalent(
    conn: psycopg.Connection, schema1: str, table1: str, schema2: str, table2: str
):
    """Assert that two tables are semantically equivalent (for pytest)"""
    comparator = SchemaComparator(conn)

    table1_schema = comparator.extract_table_schema(schema1, table1)
    table2_schema = comparator.extract_table_schema(schema2, table2)

    is_equivalent, differences = comparator.compare_tables(table1_schema, table2_schema)

    if not is_equivalent:
        diff_str = "\n".join(differences)
        raise AssertionError(f"Tables are not equivalent:\n{diff_str}")
