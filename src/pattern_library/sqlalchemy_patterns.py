"""
SQLAlchemy ORM pattern implementations for the pattern library.

This file contains SQLAlchemy ORM implementations of the core 15 primitive patterns
translated from PostgreSQL to Python/SQLAlchemy style.

Core patterns implemented:
- Primitive: declare, assign, call_function, return
- Control flow: if, foreach, while, for_query, switch, exception_handling
- Database ops: insert, update, delete, validate, duplicate_check
- Query: query, aggregate
- Data transform: json_build

All templates use SQLAlchemy session-based patterns for database operations.
"""

from src.pattern_library.api import PatternLibrary


def add_sqlalchemy_patterns(library: PatternLibrary):
    """Add SQLAlchemy ORM pattern implementations to the library"""

    def add_pattern_if_not_exists(name, category, abstract_syntax, description=""):
        """Add pattern if it doesn't already exist"""
        if not library.get_pattern(name):
            library.add_pattern(name, category, abstract_syntax, description)

    def add_if_not_exists(pattern_name, language_name, template):
        """Add implementation only if it doesn't already exist"""
        if not library.get_implementation(pattern_name, language_name):
            library.add_or_update_implementation(pattern_name, language_name, template)

    # ===== PRIMITIVE PATTERNS =====

    # declare - Variable declaration with type hints
    library.add_or_update_implementation(
        "declare",
        "python_sqlalchemy",
        """{{ variable_name }}: {{ variable_type }}{% if default_value %} = {{ default_value }}{% endif %}"""
    )

    # assign - Variable assignment
    library.add_or_update_implementation(
        "assign",
        "python_sqlalchemy",
        """{{ variable_name }} = {{ expression }}"""
    )

    # call_function - Call a Python function
    library.add_or_update_implementation(
        "call_function",
        "python_sqlalchemy",
        """{{ result_variable }} = {{ function_name }}({{ arguments|join(', ') }})"""
    )

    # return - Return from function
    library.add_or_update_implementation(
        "return",
        "python_sqlalchemy",
        """return {{ expression }}"""
    )

    # ===== CONTROL FLOW PATTERNS =====

    # if - Conditional branching
    library.add_or_update_implementation(
        "if",
        "python_sqlalchemy",
        """if {{ condition }}:
    {{ then_steps }}{% if else_steps %}
else:
    {{ else_steps }}{% endif %}"""
    )

    # foreach - Iterate over collection
    library.add_or_update_implementation(
        "foreach",
        "python_sqlalchemy",
        """for {{ iterator_var }} in {{ collection }}:
    {{ loop_body }}"""
    )

    # ===== DATABASE OPERATIONS PATTERNS =====

    # insert - Create new model instance
    library.add_or_update_implementation(
        "insert",
        "python_sqlalchemy",
        """# Insert new {{ model_name }}
{{ instance_var }} = {{ model_name }}(
{% for field, value in field_values.items() %}    {{ field }}={{ value }},
{% endfor %})
session.add({{ instance_var }})
session.commit()"""
    )

    # update - Update existing model instance
    library.add_or_update_implementation(
        "update",
        "python_sqlalchemy",
        """# Update {{ model_name }}
{{ instance_var }} = session.query({{ model_name }}).get({{ lookup_value }})
{% for field, value in field_values.items() %}{{ instance_var }}.{{ field }} = {{ value }}
{% endfor %}
session.commit()"""
    )

    # delete - Delete model instance
    library.add_or_update_implementation(
        "delete",
        "python_sqlalchemy",
        """# Delete {{ model_name }}
{{ instance_var }} = session.query({{ model_name }}).get({{ lookup_value }})
session.delete({{ instance_var }})
session.commit()"""
    )

    # ===== QUERY PATTERNS =====

    # query - Execute SQLAlchemy query
    library.add_or_update_implementation(
        "query",
        "python_sqlalchemy",
        """# Query {{ model_name }}
{{ result_var }} = session.query({{ model_name }}){% if filters %}.filter({% for field, value in filters.items() %}{{ model_name }}.{{ field }} == {{ value }}{% if not loop.last %}, {% endif %}{% endfor %}){% endif %}{% if order_by %}.order_by({% for field in order_by %}{% if field.startswith('-') %}{{ model_name }}.{{ field[1:] }}.desc(){% else %}{{ model_name }}.{{ field }}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}){% endif %}"""
    )

    # ===== DATA TRANSFORM PATTERNS =====

    # aggregate - Aggregation operations
    library.add_or_update_implementation(
        "aggregate",
        "python_sqlalchemy",
        """# Aggregate {{ model_name }}
{{ result_var }} = (session.query(
{% for alias, agg_func in aggregations.items() %}    {{ agg_func }}.label('{{ alias }}'){% if not loop.last %},
{% endif %}{% endfor %}
){% if filters %}
.filter(
{% for field, value in filters.items() %}    {{ model_name }}.{{ field }} == {{ value }}{% if not loop.last %},
{% endif %}{% endfor %}
){% endif %}).first()"""
    )

    # validate - Validate model data
    library.add_or_update_implementation(
        "validate",
        "python_sqlalchemy",
        """# Validate {{ model_name }}
{% for validator in custom_validators %}{{ validator }}({{ instance_var }})
{% endfor %}"""
    )

    # duplicate_check - Check for duplicates
    library.add_or_update_implementation(
        "duplicate_check",
        "python_sqlalchemy",
        """# Check for duplicates
{{ exists_var }} = session.query({{ model_name }}).filter(
{% for field, value in check_fields.items() %}    {{ model_name }}.{{ field }} == {{ value }}{% if not loop.last %},{% endif %}
{% endfor %}{% if exclude_pk %}).filter({{ model_name }}.id != {{ exclude_pk }}){% endif %}.first() is not None

if {{ exists_var }}:
    {{ duplicate_body }}"""
    )

    # exception_handling - Try-except block
    library.add_or_update_implementation(
        "exception_handling",
        "python_sqlalchemy",
        """try:
    {{ try_body }}
{% for exception_type, handler_body in exception_handlers %}
except {{ exception_type }}:
    {{ handler_body }}{% endfor %}{% if finally_body %}
finally:
    {{ finally_body }}{% endif %}"""
    )

    # json_build - Build JSON structures
    library.add_or_update_implementation(
        "json_build",
        "python_sqlalchemy",
        """# Build JSON structure
import json
{{ result_var }} = {
{% for key, value in json_structure.items() %}    "{{ key }}": {{ value }},
{% endfor %}}
{% if serialize %}{{ result_var }} = json.dumps({{ result_var }}){% endif %}"""
    )


if __name__ == "__main__":
    library = PatternLibrary("pattern_library.db")
    add_sqlalchemy_patterns(library)
    library.close()

    print("✅ Added SQLAlchemy ORM patterns to library")