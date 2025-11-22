"""
SQL Table Parser using pglast

Converts PostgreSQL CREATE TABLE statements to structured data
"""

from dataclasses import dataclass

from core.dependencies import PGLAST

from .sql_type_mapper import SQLTypeMapper

# Lazy import with availability check
_pglast = None


def _get_pglast():
    global _pglast
    if _pglast is None:
        PGLAST.require()  # Raises helpful error if not installed
        import pglast

        _pglast = pglast
    return _pglast


@dataclass
class ColumnInfo:
    """Information about a table column"""

    name: str
    type: str
    specql_type: str
    nullable: bool = True
    default: str | None = None


@dataclass
class ParsedTable:
    """Parsed SQL table"""

    schema: str
    table_name: str
    columns: list[ColumnInfo]
    primary_key: list[str] | None = None
    unique_constraints: list[list[str]] | None = None
    check_constraints: list[str] | None = None
    table_comment: str | None = None
    column_comments: dict[str, str] | None = None


class SQLTableParser:
    """Parse CREATE TABLE statements using pglast"""

    # Map PostgreSQL internal type names to standard SQL types
    TYPE_MAPPING = {
        "int4": "INTEGER",
        "int8": "BIGINT",
        "int2": "SMALLINT",
        "text": "TEXT",
        "varchar": "VARCHAR",
        "bpchar": "CHAR",
        "bool": "BOOLEAN",
        "float4": "REAL",
        "float8": "DOUBLE PRECISION",
        "numeric": "NUMERIC",
        "timestamptz": "TIMESTAMPTZ",
        "timestamp": "TIMESTAMP",
        "date": "DATE",
        "time": "TIME",
        "timetz": "TIMETZ",
        "uuid": "UUID",
        "json": "JSON",
        "jsonb": "JSONB",
    }

    def __init__(self):
        # Check dependency on instantiation
        self.pglast = _get_pglast()
        self.type_mapper = SQLTypeMapper()

    def _extract_original_table_name(self, sql: str) -> str | None:
        """Extract original table name from SQL preserving case.

        pglast normalizes unquoted identifiers to lowercase, but we want to
        preserve the original case for better YAML filenames. This extracts
        the table name directly from the SQL text.
        """
        import re

        # Match CREATE TABLE [IF NOT EXISTS] [schema.]table_name
        # The table name can be quoted ("TableName") or unquoted (TableName)
        pattern = r"""
            CREATE\s+TABLE\s+
            (?:IF\s+NOT\s+EXISTS\s+)?
            (?:[\w"]+\.)?              # Optional schema
            ("?)([\w]+)\1              # Table name (with optional quotes)
        """
        match = re.search(pattern, sql, re.IGNORECASE | re.VERBOSE)
        if match:
            return match.group(2)  # Return just the name without quotes
        return None

    def parse_table(self, sql: str) -> ParsedTable:
        """Parse CREATE TABLE statement"""
        try:
            # Extract original table name before pglast normalizes it
            original_table_name = self._extract_original_table_name(sql)

            # Parse SQL to AST
            ast = self.pglast.parse_sql(sql)

            # Extract table definition
            stmt = ast[0].stmt

            if not isinstance(stmt, self.pglast.ast.CreateStmt):
                raise ValueError("Not a CREATE TABLE statement")

            table_stmt = stmt

            # Extract table name
            if hasattr(table_stmt.relation, "schemaname") and table_stmt.relation.schemaname:
                schema = table_stmt.relation.schemaname
            else:
                schema = "public"

            # Use original table name if we could extract it, otherwise fall back to pglast
            table_name = original_table_name or table_stmt.relation.relname

            # Extract columns and constraints
            columns = []
            primary_key = None
            unique_constraints = []
            check_constraints = []
            inline_primary_keys = []

            for table_elt in table_stmt.tableElts:
                if isinstance(table_elt, self.pglast.ast.ColumnDef):
                    column, is_primary = self._parse_column(table_elt)
                    columns.append(column)
                    if is_primary:
                        inline_primary_keys.append(column.name)
                elif isinstance(table_elt, self.pglast.ast.Constraint):
                    pk, uk, ck = self._parse_table_constraint(table_elt)
                    if pk:
                        primary_key = pk
                    if uk:
                        unique_constraints.append(uk)
                    if ck:
                        check_constraints.append(ck)

            # If no table-level PRIMARY KEY but we have inline ones, use those
            if not primary_key and inline_primary_keys:
                primary_key = inline_primary_keys

            return ParsedTable(
                schema=schema,
                table_name=table_name,
                columns=columns,
                primary_key=primary_key,
                unique_constraints=unique_constraints,
                check_constraints=check_constraints,
            )

        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}")

    def _parse_column(self, col_def) -> tuple[ColumnInfo, bool]:
        """Parse a column definition"""
        name = col_def.colname

        # Parse type - reconstruct full type name with parameters
        type_name = col_def.typeName
        type_str = "UNKNOWN"
        if hasattr(type_name, "names") and type_name.names:
            # Get the base type name
            base_type = type_name.names[-1].sval

            # Check for type modifiers (length, precision, etc.)
            if hasattr(type_name, "typmods") and type_name.typmods:
                modifiers = []
                for mod in type_name.typmods:
                    # typmods can be complex, but for simple cases like CHAR(2), it's an A_Const with ival
                    if hasattr(mod, "val") and hasattr(mod.val, "ival"):
                        modifiers.append(str(mod.val.ival))
                    elif hasattr(mod, "ival"):
                        modifiers.append(str(mod.ival))

                if modifiers:
                    type_str = f"{base_type.upper()}({','.join(modifiers)})"
                else:
                    type_str = base_type.upper()
            else:
                type_str = base_type.upper()

        # Check for column constraints
        nullable = True
        is_primary = False
        if col_def.constraints:
            for constraint in col_def.constraints:
                if isinstance(constraint, self.pglast.ast.Constraint):
                    if constraint.contype == self.pglast.enums.ConstrType.CONSTR_NOTNULL:
                        nullable = False
                    elif constraint.contype == self.pglast.enums.ConstrType.CONSTR_PRIMARY:
                        is_primary = True
                        nullable = False  # Primary keys are implicitly NOT NULL

        # Map to SpecQL type
        specql_type = self.type_mapper.map_type(type_str)

        return ColumnInfo(
            name=name, type=type_str, specql_type=specql_type, nullable=nullable
        ), is_primary

    def _parse_table_constraint(self, constraint):
        """Parse table-level constraint"""
        primary_key = None
        unique_cols = None
        check_expr = None

        if constraint.contype == self.pglast.enums.ConstrType.CONSTR_PRIMARY:
            # PRIMARY KEY constraint
            if hasattr(constraint, "keys") and constraint.keys:
                primary_key = [key.sval for key in constraint.keys]
        elif constraint.contype == self.pglast.enums.ConstrType.CONSTR_UNIQUE:
            # UNIQUE constraint
            if hasattr(constraint, "keys") and constraint.keys:
                unique_cols = [key.sval for key in constraint.keys]
        elif constraint.contype == self.pglast.enums.ConstrType.CONSTR_CHECK:
            # CHECK constraint
            if hasattr(constraint, "raw_expr"):
                # For now, just store the raw expression as string
                check_expr = str(constraint.raw_expr)

        return primary_key, unique_cols, check_expr
