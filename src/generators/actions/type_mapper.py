"""Centralized type mapping for all step compilers"""

class TypeMapper:
    """Maps SpecQL types to target language types"""

    SPECQL_TO_POSTGRES = {
        "text": "TEXT",
        "integer": "INTEGER",
        "bigint": "BIGINT",
        "numeric": "NUMERIC",
        "decimal": "DECIMAL",
        "boolean": "BOOLEAN",
        "uuid": "UUID",
        "timestamp": "TIMESTAMPTZ",
        "date": "DATE",
        "time": "TIME",
        "json": "JSONB",
        "array": "ARRAY",
    }

    @classmethod
    def to_postgres(cls, specql_type: str) -> str:
        """Convert SpecQL type to PostgreSQL type"""
        return cls.SPECQL_TO_POSTGRES.get(specql_type.lower(), "TEXT")

    @classmethod
    def to_python(cls, specql_type: str) -> str:
        """Convert SpecQL type to Python type hint"""
        type_map = {
            "text": "str",
            "integer": "int",
            "numeric": "Decimal",
            "boolean": "bool",
            "uuid": "UUID",
            "timestamp": "datetime",
            "json": "dict",
        }
        return type_map.get(specql_type.lower(), "Any")