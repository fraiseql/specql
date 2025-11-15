"""
PL/pgSQL Parser Package

Reverse engineer PostgreSQL databases to SpecQL YAML:
- DDL parsing (CREATE TABLE, CREATE TYPE, etc.)
- PL/pgSQL function parsing
- Pattern detection (Trinity, audit fields)
- Type mapping (PostgreSQL → SpecQL)
"""

from src.parsers.plpgsql.plpgsql_parser import PLpgSQLParser
from src.parsers.plpgsql.schema_analyzer import SchemaAnalyzer
from src.parsers.plpgsql.function_analyzer import FunctionAnalyzer
from src.parsers.plpgsql.pattern_detector import PatternDetector
from src.parsers.plpgsql.type_mapper import TypeMapper

__all__ = [
    "PLpgSQLParser",
    "SchemaAnalyzer",
    "FunctionAnalyzer",
    "PatternDetector",
    "TypeMapper",
]
