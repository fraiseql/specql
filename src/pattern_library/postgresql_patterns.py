"""
PostgreSQL pattern implementations for the pattern library.

This file contains all PostgreSQL implementations of the 35 primitive patterns
extracted from the existing hard-coded compilers.
"""

from src.pattern_library.api import PatternLibrary


def add_postgresql_patterns(library: PatternLibrary):
    """Add all PostgreSQL pattern implementations to the library"""

    def add_pattern_if_not_exists(name, category, abstract_syntax, description=""):
        """Add pattern if it doesn't already exist"""
        if not library.get_pattern(name):
            library.add_pattern(name, category, abstract_syntax, description)

    # ===== PRIMITIVE PATTERNS =====

    # call_function
    add_pattern_if_not_exists(
        "call_function",
        "primitive",
        {"type": "call_function", "fields": ["function_name", "arguments", "result_variable"]},
        "Call a function and store result"
    )
    library.add_or_update_implementation(
        pattern_name="call_function",
        language_name="postgresql",
        template="""SELECT {{ function_name }}({{ arguments|join(', ') }}) INTO {{ result_variable }};"""
    )

    # call_service
    add_pattern_if_not_exists(
        "call_service",
        "primitive",
        {"type": "call_service", "fields": ["service_name", "service_function", "parameters"]}
    )
    library.add_or_update_implementation(
        pattern_name="call_service",
        language_name="postgresql",
        template="""-- Call service: {{ service_name }}
    SELECT * FROM {{ service_function }}({{ parameters|join(', ') }});""",
    )

    # ===== CONTROL FLOW PATTERNS =====

    # foreach
    add_pattern_if_not_exists(
        "foreach",
        "control_flow",
        {"type": "foreach", "fields": ["iterator_var", "collection", "loop_body"]}
    )
    library.add_or_update_implementation(
        pattern_name="foreach",
        language_name="postgresql",
        template="""-- ForEach: {{ iterator_var }} in {{ collection }}
    FOR {{ iterator_var }} IN
        {{ collection_query }}
    LOOP{{ loop_body }}
    END LOOP;""",
    )

    # while
    add_pattern_if_not_exists(
        "while",
        "control_flow",
        {"type": "while", "fields": ["condition", "body_steps"]},
        "While loop with condition"
    )
    library.add_or_update_implementation(
        pattern_name="while",
        language_name="postgresql",
        template="""-- While: {{ condition }}
    WHILE ({{ condition }}) LOOP{{ body }}
    END LOOP;""",
    )
    library.add_or_update_implementation(
        pattern_name="while",
        language_name="postgresql",
        template="""-- While: {{ condition }}
    WHILE ({{ condition }}) LOOP{{ body }}
    END LOOP;""",
    )

    # for_query
    add_pattern_if_not_exists(
        name="for_query",
        category="control_flow",
        abstract_syntax={
            "type": "for_query",
            "fields": ["query", "iterator_var", "body_steps"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="for_query",
        language_name="postgresql",
        template="""-- For Query: {{ iterator_var }} in ({{ query }})
    FOR {{ iterator_var }} IN {{ query }}
    LOOP{{ body }}
    END LOOP;""",
    )

    # switch
    add_pattern_if_not_exists(
        name="switch",
        category="control_flow",
        abstract_syntax={
            "type": "switch",
            "fields": ["expression", "cases", "default_case"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="switch",
        language_name="postgresql",
        template="""-- Switch: {{ expression }}
    CASE {{ expression }}{% for case in cases %}
    WHEN {{ case.when }} THEN{{ case.then }}{% endfor %}{% if default_case %}
    ELSE{{ default_case }}{% endif %}
    END CASE;""",
    )

    # ===== QUERY PATTERNS =====

    # subquery - already exists but add implementation
    library.add_or_update_implementation(
        pattern_name="subquery",
        language_name="postgresql",
        template="""SELECT ({{ subquery }}) INTO {{ result_variable }};""",
    )

    # cte
    add_pattern_if_not_exists(
        name="cte",
        category="query",
        abstract_syntax={
            "type": "cte",
            "fields": ["cte_name", "cte_query", "main_query"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="cte",
        language_name="postgresql",
        template="""-- CTE: {{ cte_name }}
    WITH {{ cte_name }} AS (
        {{ cte_query }}
    )
    {{ main_query }}""",
    )

    # ===== DATABASE OPERATION PATTERNS =====

    # insert - already exists but add implementation
    library.add_or_update_implementation(
        pattern_name="insert",
        language_name="postgresql",
        template="""-- Insert {{ entity }}
    INSERT INTO {{ table_name }} (
        {{ columns|join(', ') }}
    ) VALUES (
        {{ values|join(', ') }}
    ) RETURNING {{ pk_column }} INTO {{ result_variable }};""",
    )

    # update - already exists but add implementation
    library.add_or_update_implementation(
        pattern_name="update",
        language_name="postgresql",
        template="""-- Update {{ entity }}
    UPDATE {{ table_name }}
    SET {{ set_clause }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};""",
    )

    # delete
    add_pattern_if_not_exists(
        name="delete",
        category="database_ops",
        abstract_syntax={
            "type": "delete",
            "fields": ["entity", "where_clause"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="delete",
        language_name="postgresql",
        template="""-- Delete {{ entity }}
    DELETE FROM {{ table_name }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};""",
    )

    # partial_update
    add_pattern_if_not_exists(
        name="partial_update",
        category="database_ops",
        abstract_syntax={
            "type": "partial_update",
            "fields": ["entity", "updates", "where_clause"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="partial_update",
        language_name="postgresql",
        template="""-- Partial Update {{ entity }}
    UPDATE {{ table_name }}
    SET {{ updates|join(', ') }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};""",
    )

    # duplicate_check
    add_pattern_if_not_exists(
        name="duplicate_check",
        category="database_ops",
        abstract_syntax={
            "type": "duplicate_check",
            "fields": ["entity", "check_fields", "error_message"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="duplicate_check",
        language_name="postgresql",
        template="""-- Duplicate Check
    IF EXISTS (
        SELECT 1 FROM {{ table_name }}
        WHERE {{ conditions|join(' AND ') }}
    ) THEN
        RAISE EXCEPTION '{{ error_message }}';
    END IF;""",
    )

    # validate
    add_pattern_if_not_exists(
        name="validate",
        category="database_ops",
        abstract_syntax={
            "type": "validate",
            "fields": ["entity", "conditions", "error_message"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="validate",
        language_name="postgresql",
        template="""-- Validate: {{ conditions|join(' AND ') }}
    IF NOT ({{ conditions|join(' AND ') }}) THEN
        RAISE EXCEPTION '{{ error_message }}';
    END IF;""",
    )

    # refresh_table_view
    add_pattern_if_not_exists(
        name="refresh_table_view",
        category="database_ops",
        abstract_syntax={
            "type": "refresh_table_view",
            "fields": ["view_name"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="refresh_table_view",
        language_name="postgresql",
        template="""-- Refresh Table View: {{ view_name }}
    REFRESH MATERIALIZED VIEW {{ view_name }};""",
    )

    # notify
    add_pattern_if_not_exists(
        name="notify",
        category="database_ops",
        abstract_syntax={
            "type": "notify",
            "fields": ["channel", "payload"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="notify",
        language_name="postgresql",
        template="""-- Notify: {{ channel }}
    PERFORM pg_notify('{{ channel }}', {{ payload }});""",
    )

    # ===== DATA TRANSFORM PATTERNS =====

    # aggregate
    add_pattern_if_not_exists(
        name="aggregate",
        category="data_transform",
        abstract_syntax={
            "type": "aggregate",
            "fields": ["operation", "field", "result_variable"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="aggregate",
        language_name="postgresql",
        template="""SELECT {{ operation }}({{ field }}) INTO {{ result_variable }}
    FROM {{ table_name }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};""",
    )

    # json_build
    add_pattern_if_not_exists(
        name="json_build",
        category="data_transform",
        abstract_syntax={
            "type": "json_build",
            "fields": ["fields", "result_variable"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="json_build",
        language_name="postgresql",
        template="""SELECT json_build_object({{ fields|join(', ') }}) INTO {{ result_variable }};""",
    )

    # ===== EXCEPTION HANDLING PATTERNS =====

    # exception_handling
    add_pattern_if_not_exists(
        name="exception_handling",
        category="control_flow",
        abstract_syntax={
            "type": "exception_handling",
            "fields": ["try_steps", "catch_steps", "exception_var"]
        },
    )
    library.add_or_update_implementation(
        pattern_name="exception_handling",
        language_name="postgresql",
        template="""-- Exception Handling
    BEGIN{{ try_body }}
    EXCEPTION WHEN OTHERS THEN
        {{ exception_var }} := SQLERRM;{{ catch_body }}
    END;""",
    )

    # return_early - already exists but add implementation
    library.add_or_update_implementation(
        pattern_name="return_early",
        language_name="postgresql",
        template="""-- Return Early
    RETURN{% if return_value %} {{ return_value }}{% endif %};""",
    )

    # ===== MISSING PRIMITIVE PATTERNS =====

    # declare
    add_pattern_if_not_exists(
        "declare",
        "primitive",
        {"type": "declare", "fields": ["variable_name", "variable_type", "default_value"]},
        "Declare a variable with optional default value"
    )
    library.add_or_update_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="""{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""
    )

    # assign
    add_pattern_if_not_exists(
        "assign",
        "primitive",
        {"type": "assign", "fields": ["variable_name", "expression"]},
        "Assign value to a variable"
    )
    library.add_or_update_implementation(
        pattern_name="assign",
        language_name="postgresql",
        template="""{{ variable_name }} := {{ expression }};"""
    )

    # return
    add_pattern_if_not_exists(
        "return",
        "primitive",
        {"type": "return", "fields": ["expression"]},
        "Return value from function"
    )
    library.add_or_update_implementation(
        pattern_name="return",
        language_name="postgresql",
        template="""RETURN {{ expression }};"""
    )

    # ===== MISSING CONTROL FLOW PATTERNS =====

    # if
    add_pattern_if_not_exists(
        "if",
        "control_flow",
        {"type": "if", "fields": ["condition", "then_steps", "else_steps"]},
        "Conditional branching"
    )
    library.add_or_update_implementation(
        pattern_name="if",
        language_name="postgresql",
        template="""IF {{ condition }} THEN
    {{ then_steps|join('\n    ') }}
{% if else_steps %}ELSE
    {{ else_steps|join('\n    ') }}
{% endif %}END IF;"""
    )

    # ===== MISSING QUERY PATTERNS =====

    # query
    add_pattern_if_not_exists(
        "query",
        "query",
        {"type": "query", "fields": ["sql", "into_variable"]},
        "Execute query and store result"
    )
    library.add_or_update_implementation(
        pattern_name="query",
        language_name="postgresql",
        template="""SELECT * FROM ({{ sql }}) INTO {{ into_variable }};"""
    )

    print("✅ Added PostgreSQL implementations for all patterns")


if __name__ == "__main__":
    library = PatternLibrary("pattern_library.db")
    add_postgresql_patterns(library)
    library.close()