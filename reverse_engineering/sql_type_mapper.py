"""
SQL Type Mapper

Maps PostgreSQL column types to SpecQL field types
"""


class SQLTypeMapper:
    """Maps PostgreSQL types to SpecQL types"""

    TYPE_MAP = {
        "TEXT": "text",
        "VARCHAR": "text",
        "CHAR": "text",
        "BPCHAR": "text",  # PostgreSQL's internal CHAR type
        "INTEGER": "integer",
        "INT": "integer",
        "INT4": "integer",  # PostgreSQL's internal INTEGER type
        "BIGINT": "bigint",
        "INT8": "bigint",  # PostgreSQL's internal BIGINT type
        "SMALLINT": "smallint",
        "INT2": "smallint",  # PostgreSQL's internal SMALLINT type
        "SERIAL": "integer",
        "BIGSERIAL": "bigint",
        "NUMERIC": "decimal",
        "DECIMAL": "decimal",
        "BOOLEAN": "boolean",
        "BOOL": "boolean",  # PostgreSQL's internal BOOLEAN type
        "TIMESTAMPTZ": "timestamptz",
        "TIMESTAMP": "timestamp",
        "DATE": "date",
        "TIME": "time",
        "TIMETZ": "timetz",
        "UUID": "uuid",
        "JSON": "json",
        "JSONB": "jsonb",
        "REAL": "real",
        "FLOAT4": "real",  # PostgreSQL's internal REAL type
        "DOUBLE PRECISION": "double",
        "FLOAT8": "double",  # PostgreSQL's internal DOUBLE PRECISION type
    }

    def map_type(self, pg_type: str) -> str:
        """Map PostgreSQL type to SpecQL type"""
        # Handle types with parameters like BPCHAR(2), NUMERIC(10,2)
        if "(" in pg_type:
            base_type = pg_type.upper().split("(")[0]
            params = pg_type.split("(")[1].rstrip(")")

            if base_type == "BPCHAR":  # PostgreSQL's CHAR(n)
                return f"char({params})"
            elif base_type == "VARCHAR":
                return f"varchar({params})"
            elif base_type == "NUMERIC" or base_type == "DECIMAL":
                return f"decimal({params})"
            else:
                # For other parameterized types, keep the base mapping
                mapped = self.TYPE_MAP.get(base_type, "text")
                return mapped
        else:
            return self.TYPE_MAP.get(pg_type.upper(), "text")  # Default to text for unknown types
