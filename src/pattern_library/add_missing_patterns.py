"""
Add missing patterns and PostgreSQL implementations to the pattern library.
"""

import sqlite3


def add_missing_patterns():
    """Add all missing patterns and their PostgreSQL implementations"""

    # Connect to existing database
    conn = sqlite3.connect("pattern_library.db")
    conn.row_factory = sqlite3.Row

    # ===== ADD MISSING PATTERNS =====

    patterns_to_add = [
        # Control Flow
        ("foreach", "control_flow", '{"type": "foreach", "fields": ["iterator_var", "collection", "body_steps"]}', "Iterate over a collection"),
        ("while", "control_flow", '{"type": "while", "fields": ["condition", "body_steps"]}', "While loop with condition"),
        ("for_query", "control_flow", '{"type": "for_query", "fields": ["query", "iterator_var", "body_steps"]}', "FOR loop over query results"),
        ("switch", "control_flow", '{"type": "switch", "fields": ["expression", "cases", "default_case"]}', "Switch/case statement"),

        # Query
        ("subquery", "query", '{"type": "subquery", "fields": ["subquery", "result_variable"]}', "Execute subquery and store result"),
        ("cte", "query", '{"type": "cte", "fields": ["cte_name", "cte_query", "main_query"]}', "Common Table Expression (WITH clause)"),

        # Database Operations
        ("insert", "database_ops", '{"type": "insert", "fields": ["entity", "fields", "result_variable"]}', "Insert record into table"),
        ("update", "database_ops", '{"type": "update", "fields": ["entity", "set_clause", "where_clause"]}', "Update records in table"),
        ("delete", "database_ops", '{"type": "delete", "fields": ["entity", "where_clause"]}', "Delete records from table"),
        ("partial_update", "database_ops", '{"type": "partial_update", "fields": ["entity", "updates", "where_clause"]}', "Partial update of specific fields"),
        ("duplicate_check", "database_ops", '{"type": "duplicate_check", "fields": ["entity", "check_fields", "error_message"]}', "Check for duplicate records"),
        ("validate", "database_ops", '{"type": "validate", "fields": ["entity", "conditions", "error_message"]}', "Validate business rules"),
        ("refresh_table_view", "database_ops", '{"type": "refresh_table_view", "fields": ["view_name"]}', "Refresh materialized view"),
        ("notify", "database_ops", '{"type": "notify", "fields": ["channel", "payload"]}', "Send PostgreSQL notification"),

        # Data Transform
        ("aggregate", "data_transform", '{"type": "aggregate", "fields": ["operation", "field", "result_variable", "table_name", "where_clause"]}', "Aggregate operation (COUNT, SUM, AVG, etc.)"),
        ("json_build", "data_transform", '{"type": "json_build", "fields": ["fields", "result_variable"]}', "Build JSON object from fields"),

        # Exception Handling
        ("exception_handling", "control_flow", '{"type": "exception_handling", "fields": ["try_steps", "catch_steps", "exception_var"]}', "Exception handling with try/catch"),
        ("return_early", "primitive", '{"type": "return_early", "fields": ["return_value"]}', "Early return from function"),

        # Additional Primitives
        ("call_function", "primitive", '{"type": "call_function", "fields": ["function_name", "arguments", "result_variable"]}', "Call a PostgreSQL function and store result"),
        ("call_service", "primitive", '{"type": "call_service", "fields": ["service_name", "parameters"]}', "Call a service function")
    ]

    # Add patterns
    for name, category, abstract_syntax, description in patterns_to_add:
        try:
            conn.execute(
                "INSERT INTO patterns (pattern_name, pattern_category, abstract_syntax, description) VALUES (?, ?, ?, ?)",
                (name, category, abstract_syntax, description)
            )
            print(f"✅ Added pattern: {name}")
        except sqlite3.IntegrityError:
            print(f"⚠️  Pattern {name} already exists")

    # ===== ADD POSTGRESQL IMPLEMENTATIONS =====

    implementations = [
        # Control Flow
        ("foreach", """-- ForEach: {{ iterator_var }} in {{ collection }}
    FOR {{ iterator_var }} IN
        {{ collection_query }}
    LOOP{{ loop_body }}
    END LOOP;"""),
        ("while", """-- While: {{ condition }}
    WHILE ({{ condition }}) LOOP{{ body }}
    END LOOP;"""),
        ("for_query", """-- For Query: {{ iterator_var }} in ({{ query }})
    FOR {{ iterator_var }} IN {{ query }}
    LOOP{{ body }}
    END LOOP;"""),
        ("switch", """-- Switch: {{ expression }}
    CASE {{ expression }}{% for case in cases %}
    WHEN {{ case.when }} THEN{{ case.then }}{% endfor %}{% if default_case %}
    ELSE{{ default_case }}{% endif %}
    END CASE;"""),

        # Query
        ("subquery", """SELECT ({{ subquery }}) INTO {{ result_variable }};"""),
        ("cte", """-- CTE: {{ cte_name }}
    WITH {{ cte_name }} AS (
        {{ cte_query }}
    )
    {{ main_query }}"""),

        # Database Operations
        ("insert", """-- Insert {{ entity }}
    INSERT INTO {{ table_name }} (
        {{ columns|join(', ') }}
    ) VALUES (
        {{ values|join(', ') }}
    ) RETURNING {{ pk_column }} INTO {{ result_variable }};"""),
        ("update", """-- Update {{ entity }}
    UPDATE {{ table_name }}
    SET {{ set_clause }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};"""),
        ("delete", """-- Delete {{ entity }}
    DELETE FROM {{ table_name }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};"""),
        ("partial_update", """-- Partial Update {{ entity }}
    UPDATE {{ table_name }}
    SET {{ updates|join(', ') }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};"""),
        ("duplicate_check", """-- Duplicate Check
    IF EXISTS (
        SELECT 1 FROM {{ table_name }}
        WHERE {{ conditions|join(' AND ') }}
    ) THEN
        RAISE EXCEPTION '{{ error_message }}';
    END IF;"""),
        ("validate", """-- Validate: {{ conditions|join(' AND ') }}
    IF NOT ({{ conditions|join(' AND ') }}) THEN
        RAISE EXCEPTION '{{ error_message }}';
    END IF;"""),
        ("refresh_table_view", """-- Refresh Table View: {{ view_name }}
    REFRESH MATERIALIZED VIEW {{ view_name }};"""),
        ("notify", """-- Notify: {{ channel }}
    PERFORM pg_notify('{{ channel }}', {{ payload }});"""),

        # Data Transform
        ("aggregate", """SELECT {{ operation }}({{ field }}) INTO {{ result_variable }}
    FROM {{ table_name }}{% if where_clause %}
    WHERE {{ where_clause }}{% endif %};"""),
        ("json_build", """SELECT json_build_object({{ fields|join(', ') }}) INTO {{ result_variable }};"""),

        # Exception Handling
        ("exception_handling", """-- Exception Handling
    BEGIN{{ try_body }}
    EXCEPTION WHEN OTHERS THEN
        {{ exception_var }} := SQLERRM;{{ catch_body }}
    END;"""),
        ("return_early", """-- Return Early
    RETURN{% if return_value %} {{ return_value }}{% endif %};"""),

        # Additional Primitives
        ("call_function", """SELECT {{ function_name }}({{ arguments|join(', ') }}) INTO {{ result_variable }};"""),
        ("call_service", """-- Call service: {{ service_name }}
    SELECT * FROM {{ service_function }}({{ parameters|join(', ') }});""")
    ]

    # Add implementations
    for pattern_name, template in implementations:
        try:
            # Get pattern_id
            pattern_row = conn.execute(
                "SELECT pattern_id FROM patterns WHERE pattern_name = ?",
                (pattern_name,)
            ).fetchone()

            if not pattern_row:
                print(f"❌ Pattern {pattern_name} not found")
                continue

            # Get language_id for postgresql
            lang_row = conn.execute(
                "SELECT language_id FROM languages WHERE language_name = 'postgresql'"
            ).fetchone()

            if not lang_row:
                print("❌ PostgreSQL language not found")
                continue

            conn.execute(
                "INSERT INTO pattern_implementations (pattern_id, language_id, implementation_template) VALUES (?, ?, ?)",
                (pattern_row["pattern_id"], lang_row["language_id"], template)
            )
            print(f"✅ Added implementation: {pattern_name} -> postgresql")
        except sqlite3.IntegrityError:
            print(f"⚠️  Implementation {pattern_name} already exists")

    conn.commit()
    conn.close()

    print("\n✅ Pattern library migration complete!")


if __name__ == "__main__":
    add_missing_patterns()