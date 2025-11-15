"""Seed pattern library with initial data"""

from src.pattern_library.api import PatternLibrary
from src.pattern_library.postgresql_patterns import add_postgresql_patterns
from src.pattern_library.django_patterns import add_django_patterns
from src.pattern_library.sqlalchemy_patterns import add_sqlalchemy_patterns


def seed_initial_data(library: PatternLibrary):
    """Seed library with initial patterns and languages"""

    # Add languages
    library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative",
        version="14+"
    )

    library.add_language(
        name="python_django",
        ecosystem="python",
        paradigm="imperative",
        version="3.11+"
    )

    library.add_language(
        name="python_sqlalchemy",
        ecosystem="python",
        paradigm="imperative",
        version="3.11+"
    )

    # Add universal types
    types_to_add = [
        ("text", "scalar", "Text string"),
        ("integer", "scalar", "Integer number"),
        ("numeric", "scalar", "Decimal number"),
        ("boolean", "scalar", "Boolean value"),
        ("uuid", "scalar", "UUID identifier"),
        ("timestamp", "scalar", "Timestamp with timezone"),
        ("json", "composite", "JSON object"),
        ("array", "collection", "Array of values"),
    ]

    for type_name, type_category, description in types_to_add:
        library.add_universal_type(type_name, type_category, description)

    # Add type mappings - PostgreSQL
    pg_mappings = [
        ("text", "postgresql", "TEXT"),
        ("integer", "postgresql", "INTEGER"),
        ("numeric", "postgresql", "NUMERIC"),
        ("boolean", "postgresql", "BOOLEAN"),
        ("uuid", "postgresql", "UUID"),
        ("timestamp", "postgresql", "TIMESTAMPTZ"),
        ("json", "postgresql", "JSONB"),
        ("array", "postgresql", "ARRAY"),
    ]

    for universal_type, language, lang_type in pg_mappings:
        library.add_type_mapping(universal_type, language, lang_type)

    # Add type mappings - Python
    python_mappings = [
        ("text", "python_django", "str", None),
        ("integer", "python_django", "int", None),
        ("numeric", "python_django", "Decimal", "from decimal import Decimal"),
        ("boolean", "python_django", "bool", None),
        ("uuid", "python_django", "UUID", "from uuid import UUID"),
        ("timestamp", "python_django", "datetime", "from datetime import datetime"),
        ("json", "python_django", "dict", None),
        ("array", "python_django", "list", None),
    ]

    for universal_type, language, lang_type, import_stmt in python_mappings:
        library.add_type_mapping(universal_type, language, lang_type, import_stmt)

    # Add all core patterns
    patterns_to_add = [
        # Primitive patterns
        ("declare", "primitive", {"type": "declare", "fields": ["variable_name", "variable_type", "default_value"]}, "Declare a variable with optional default value"),
        ("assign", "primitive", {"type": "assign", "fields": ["variable_name", "expression"]}, "Assign value to a variable"),
        ("call_function", "primitive", {"type": "call_function", "fields": ["function_name", "arguments", "result_variable"]}, "Call a function and store result"),
        ("call_service", "primitive", {"type": "call_service", "fields": ["service_name", "service_function", "parameters"]}, "Call a service function"),
        ("return", "primitive", {"type": "return", "fields": ["expression"]}, "Return value from function"),
        ("return_early", "primitive", {"type": "return_early", "fields": []}, "Early return from function"),

        # Control flow patterns
        ("if", "control_flow", {"type": "if", "fields": ["condition", "then_steps", "else_steps"]}, "Conditional branching"),
        ("foreach", "control_flow", {"type": "foreach", "fields": ["iterator_var", "collection", "loop_body"]}, "Iterate over a collection"),
        ("while", "control_flow", {"type": "while", "fields": ["condition", "body_steps"]}, "While loop with condition"),
        ("for_query", "control_flow", {"type": "for_query", "fields": ["query", "iterator_var", "body_steps"]}, "FOR loop over query results"),
        ("switch", "control_flow", {"type": "switch", "fields": ["expression", "cases", "default_case"]}, "Switch/case statement"),
        ("exception_handling", "control_flow", {"type": "exception_handling", "fields": ["try_steps", "catch_steps", "exception_var"]}, "Exception handling with try/catch"),

        # Query patterns
        ("query", "query", {"type": "query", "fields": ["sql", "into_variable"]}, "Execute query and store result"),
        ("subquery", "query", {"type": "subquery", "fields": ["subquery", "result_variable"]}, "Execute subquery and store result"),
        ("cte", "query", {"type": "cte", "fields": ["cte_name", "cte_query", "main_query"]}, "Common Table Expression (WITH clause)"),

        # Database operation patterns
        ("insert", "database_ops", {"type": "insert", "fields": ["entity", "table_name", "columns", "values", "result_variable"]}, "INSERT with RETURNING"),
        ("update", "database_ops", {"type": "update", "fields": ["entity", "table_name", "set_clause", "where_clause"]}, "UPDATE with conditions"),
        ("delete", "database_ops", {"type": "delete", "fields": ["entity", "table_name", "where_clause"]}, "DELETE from table"),
        ("partial_update", "database_ops", {"type": "partial_update", "fields": ["entity", "updates", "where_clause"]}, "Partial update of specific fields"),
        ("duplicate_check", "database_ops", {"type": "duplicate_check", "fields": ["entity", "check_fields", "error_message"]}, "Check for duplicate records"),
        ("validate", "database_ops", {"type": "validate", "fields": ["entity", "conditions", "error_message"]}, "Validate business rules"),
        ("refresh_table_view", "database_ops", {"type": "refresh_table_view", "fields": ["view_name"]}, "Refresh materialized view"),
        ("notify", "database_ops", {"type": "notify", "fields": ["channel", "payload"]}, "Send notification"),

        # Data transform patterns
        ("aggregate", "data_transform", {"type": "aggregate", "fields": ["operation", "field", "result_variable", "where_clause"]}, "Aggregate operation (COUNT, SUM, AVG, etc.)"),
        ("json_build", "data_transform", {"type": "json_build", "fields": ["fields", "result_variable"]}, "Build JSON object from fields"),
    ]

    for name, category, abstract_syntax, description in patterns_to_add:
        library.add_pattern(name, category, abstract_syntax, description)

    # Load pattern implementations
    try:
        add_postgresql_patterns(library)
    except Exception as e:
        print(f"Note: PostgreSQL patterns may already be loaded: {e}")

    try:
        add_django_patterns(library)
    except Exception as e:
        print(f"Note: Django patterns may already be loaded: {e}")

    try:
        add_sqlalchemy_patterns(library)
    except Exception as e:
        print(f"Note: SQLAlchemy patterns may already be loaded: {e}")

    print("✅ Seeded initial data")
    print(f"  - Languages: {len(library.get_all_languages())}")
    print(f"  - Patterns: {len(library.get_all_patterns())}")
    print("  - Universal types: 8")
    print(f"  - PostgreSQL implementations: {len([impl for impl in library.db.execute('SELECT * FROM pattern_implementations WHERE language_id = (SELECT language_id FROM languages WHERE language_name = \"postgresql\")').fetchall()])}")
    print(f"  - Django implementations: {len([impl for impl in library.db.execute('SELECT * FROM pattern_implementations WHERE language_id = (SELECT language_id FROM languages WHERE language_name = \"python_django\")').fetchall()])}")
    print(f"  - SQLAlchemy implementations: {len([impl for impl in library.db.execute('SELECT * FROM pattern_implementations WHERE language_id = (SELECT language_id FROM languages WHERE language_name = \"python_sqlalchemy\")').fetchall()])}")


if __name__ == "__main__":
    library = PatternLibrary("pattern_library.db")
    seed_initial_data(library)
    library.close()