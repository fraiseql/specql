"""
Add PostgreSQL implementations for the original 5 seeded patterns.
"""

import sqlite3


def add_original_implementations():
    """Add implementations for the original patterns"""

    conn = sqlite3.connect("pattern_library.db")
    conn.row_factory = sqlite3.Row

    implementations = [
        ("declare", """{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""),
        ("assign", """{{ variable_name }} := {{ expression }};"""),
        ("if", """-- If: {{ condition }}
    SELECT {{ fields_to_fetch|join(', ') }} INTO {{ variables|join(', ') }}
    FROM {{ table_name }}
    WHERE {{ pk_column }} = v_pk;

    IF ({{ condition }}) THEN{{ then_steps }}
    ELSE{{ else_steps }}
    END IF;"""),
        ("query", """{{ sql }} INTO {{ into_variable }};"""),
        ("return", """RETURN {{ expression }};""")
    ]

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

    print("\n✅ Original pattern implementations added!")


if __name__ == "__main__":
    add_original_implementations()