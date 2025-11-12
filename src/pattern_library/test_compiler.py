"""
Test the pattern-based compiler with the existing database.
"""

import sqlite3
from jinja2 import Template


def test_pattern_compilation():
    """Test compiling patterns directly from the database"""

    # Connect to existing database
    conn = sqlite3.connect("pattern_library.db")
    conn.row_factory = sqlite3.Row

    # Test declare pattern
    impl = conn.execute("""
        SELECT pi.implementation_template
        FROM pattern_implementations pi
        JOIN patterns p ON pi.pattern_id = p.pattern_id
        WHERE p.pattern_name = 'declare'
    """).fetchone()

    if impl:
        template = Template(impl["implementation_template"])
        result = template.render(
            variable_name="total",
            variable_type="NUMERIC",
            default_value="0"
        )
        print("DECLARE result:", result)

    # Test assign pattern
    impl = conn.execute("""
        SELECT pi.implementation_template
        FROM pattern_implementations pi
        JOIN patterns p ON pi.pattern_id = p.pattern_id
        WHERE p.pattern_name = 'assign'
    """).fetchone()

    if impl:
        template = Template(impl["implementation_template"])
        result = template.render(
            variable_name="total",
            expression="total + 100"
        )
        print("ASSIGN result:", result)

    # Test insert pattern
    impl = conn.execute("""
        SELECT pi.implementation_template
        FROM pattern_implementations pi
        JOIN patterns p ON pi.pattern_id = p.pattern_id
        WHERE p.pattern_name = 'insert'
    """).fetchone()

    if impl:
        template = Template(impl["implementation_template"])
        result = template.render(
            entity="User",
            columns=["name", "email"],
            values=["'John'", "'john@example.com'"],
            table_name="public.tb_user",
            pk_column="pk_user",
            result_variable="v_user_id"
        )
        print("INSERT result:", result)

    conn.close()
    print("✅ Pattern compilation test completed!")


if __name__ == "__main__":
    test_pattern_compilation()