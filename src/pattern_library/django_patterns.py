"""
Django ORM pattern implementations for the pattern library.

This file contains all Django ORM implementations of the primitive patterns
translated from PostgreSQL to Python/Django ORM style.
"""

from src.pattern_library.api import PatternLibrary


def add_django_patterns(library: PatternLibrary):
    """Add all Django ORM pattern implementations to the library"""

    def add_pattern_if_not_exists(name, category, abstract_syntax, description=""):
        """Add pattern if it doesn't already exist"""
        if not library.get_pattern(name):
            library.add_pattern(name, category, abstract_syntax, description)

    def add_or_update(pattern_name, language_name, template):
        """Add implementation or update if it exists"""
        existing = library.get_implementation(pattern_name, language_name)
        print(f"Debug: {pattern_name} {language_name} exists: {existing is not None}")
        if existing:
            # Update existing implementation
            library.db.execute(
                "UPDATE pattern_implementations SET implementation_template = ? WHERE implementation_id = ?",
                (template, existing["implementation_id"])
            )
            library.db.commit()
            print(f"Debug: Updated {pattern_name}")
        else:
            print(f"Debug: Adding {pattern_name}")
            library.add_implementation(pattern_name, language_name, template)

    # ===== PRIMITIVE PATTERNS =====

    # declare - Variable declaration with type hints
    add_or_update(
        "declare",
        "python_django",
        """{{ variable_name }}: {{ variable_type }}{% if default_value %} = {{ default_value }}{% endif %}"""
    )

    # assign - Variable assignment
    add_or_update(
        "assign",
        "python_django",
        """{{ variable_name }} = {{ expression }}"""
    )

    # call_function - Call a Python function
    add_or_update(
        "call_function",
        "python_django",
        """{{ result_variable }} = {{ function_name }}({{ arguments|join(', ') }})"""
    )

    # call_service - Call a service method
    add_or_update(
        "call_service",
        "python_django",
        """# Call service: {{ service_name }}
{{ result_variable }} = {{ service_class }}.{{ service_method }}({{ parameters|join(', ') }})"""
    )

    # return - Return from function
    add_or_update(
        "return",
        "python_django",
        """return {{ expression }}"""
    )

    # return_early - Early return
    add_or_update(
        "return_early",
        "python_django",
        """return"""
    )

    # ===== CONTROL FLOW PATTERNS =====

    # if - Conditional branching
    add_or_update(
        "if",
        "python_django",
        """if {{ condition }}:
    {{ then_steps|replace('\n', '\n    ') }}
{% if else_steps %}else:
    {{ else_steps|replace('\n', '\n    ') }}
{% endif %}"""
    )

    # foreach - Iterate over collection
    add_or_update(
        "foreach",
        "python_django",
        """for {{ iterator_var }} in {{ collection }}:
    {{ loop_body }}"""
    )

    # for_query - Iterate over Django queryset results
    add_or_update(
        "for_query",
        "python_django",
        """for {{ item_var }} in {{ queryset }}:
    {{ loop_body }}"""
    )

    # while - While loop with condition
    add_or_update(
        "while",
        "python_django",
        """while {{ condition }}:
    {{ loop_body }}"""
    )

    # switch - Switch statement using if-elif-else chain
    add_or_update(
        "switch",
        "python_django",
        """{% for case_value, case_body in cases %}
{% if loop.first %}if {{ switch_var }} == {{ case_value }}:
    {{ case_body }}
{% else %}elif {{ switch_var }} == {{ case_value }}:
    {{ case_body }}
{% endif %}{% endfor %}
{% if default_case %}
else:
    {{ default_case }}{% endif %}"""
    )



    # for_query - Iterate over Django queryset results
    add_or_update(
        "for_query",
        "python_django",
        """for {{ item_var }} in {{ queryset }}:
    {{ loop_body }}"""
    )

    # while - While loop with condition
    add_or_update(
        "while",
        "python_django",
        """while {{ condition }}:
    {{ loop_body }}"""
    )

    # switch - Switch statement using if-elif-else chain
    add_or_update(
        "switch",
        "python_django",
        """{% for case_value, case_body in cases %}
{% if loop.first %}if {{ switch_var }} == {{ case_value }}:
    {{ case_body }}
{% else %}elif {{ switch_var }} == {{ case_value }}:
    {{ case_body }}
{% endif %}{% endfor %}
{% if default_case %}
else:
    {{ default_case }}{% endif %}"""
    )



    # exception_handling - Try-except block
    add_or_update(
        "exception_handling",
        "python_django",
        """try:
    {{ try_body|replace('\n', '\n    ') }}

{% for handler in exception_handlers -%}
except {{ handler['exception_type'] }}:
    {{ handler['handler_body']|replace('\n', '\n    ') }}
{% endfor -%}
{% if finally_body -%}
finally:
    {{ finally_body|replace('\n', '\n    ') }}{% endif %}"""
    )

    # ===== DATABASE OPERATIONS PATTERNS =====

    # insert - Create new model instance
    add_or_update(
        "insert",
        "python_django",
        """# Insert new {{ model_name }}
{{ instance_var }} = {{ model_name }}(
{% for field, value in field_values.items() %}    {{ field }}={{ value }},
{% endfor %})
{{ instance_var }}.save()"""
    )

    # update - Update existing model instance
    add_or_update(
        "update",
        "python_django",
        """# Update {{ model_name }}
{{ instance_var }} = {{ model_name }}.objects.get({{ lookup_field }}={{ lookup_value }})
{% for field, value in field_values.items() %}{{ instance_var }}.{{ field }} = {{ value }}
{% endfor %}{{ instance_var }}.save()"""
    )

    # partial_update - Update specific fields
    add_or_update(
        "partial_update",
        "python_django",
        """# Partial update {{ model_name }}
{{ instance_var }} = {{ model_name }}.objects.get({{ lookup_field }}={{ lookup_value }})
{% for field, value in updates.items() %}{{ instance_var }}.{{ field }} = {{ value }}
{% endfor %}{{ instance_var }}.save(update_fields=[{% for field in updates.keys() %}'{{ field }}'{% if not loop.last %}, {% endif %}{% endfor %}])"""
    )

    # delete - Delete model instance
    add_or_update(
        "delete",
        "python_django",
        """# Delete {{ model_name }}
{{ instance_var }} = {{ model_name }}.objects.get({{ lookup_field }}={{ lookup_value }})
{{ instance_var }}.delete()"""
    )

    # duplicate_check - Check for duplicates
    add_or_update(
        "duplicate_check",
        "python_django",
        """# Check for duplicates
{{ exists_var }} = {{ model_name }}.objects.filter(
{% for field, value in check_fields.items() %}    {{ field }}={{ value }}{% if not loop.last %},{% endif %}
{% endfor %}){% if exclude_pk %}.exclude(pk={{ exclude_pk }}){% endif %}.exists()

if {{ exists_var }}:
    {{ duplicate_body }}"""
    )

    # validate - Validate model data
    add_or_update(
        "validate",
        "python_django",
        """# Validate {{ model_name }}
{{ instance_var }}.full_clean()
{% for validator in custom_validators %}{{ validator }}({{ instance_var }})
{% endfor %}"""
    )

    # notify - Send notification (using Django signals or custom logic)
    add_or_update(
        "notify",
        "python_django",
        """# Send notification
from django.core.mail import send_mail
{% if email_recipients %}send_mail(
    '{{ email_subject }}',
    '{{ email_message }}',
    '{{ email_from }}',
    [{% for recipient in email_recipients %}'{{ recipient }}', {% endfor %}],
    fail_silently=False,
){% endif %}
{% if signal_to_send %}{{ signal_to_send }}.send(sender={{ model_name }}, instance={{ instance_var }}){% endif %}"""
    )

    # refresh_table_view - Refresh model data from database
    add_or_update(
        "refresh_table_view",
        "python_django",
        """# Refresh {{ model_name }} from database
{{ instance_var }}.refresh_from_db()"""
    )

    # ===== QUERY PATTERNS =====

    # query - Execute Django ORM query
    add_or_update(
        "query",
        "python_django",
        """# Query {{ model_name }}
{{ result_var }} = {{ model_name }}.objects{% if filters %}.filter(
{% for field, value in filters.items() %}    {{ field }}={{ value }}{% if not loop.last %},{% endif %}
{% endfor %}){% endif %}{% if select_related %}.select_related({% for related in select_related %}'{{ related }}'{% if not loop.last %}, {% endif %}{% endfor %}){% endif %}{% if prefetch_related %}.prefetch_related({% for related in prefetch_related %}'{{ related }}'{% if not loop.last %}, {% endif %}{% endfor %}){% endif %}{% if order_by %}.order_by({% for field in order_by %}'{{ field }}'{% if not loop.last %}, {% endif %}{% endfor %}){% endif %}"""
    )

    # cte - Common Table Expression (using subqueries or raw SQL)
    add_or_update(
        "cte",
        "python_django",
        """# CTE: {{ cte_name }}
{{ cte_name }}_subquery = {{ model_name }}.objects{% if cte_filters %}.filter(
{% for field, value in cte_filters.items() %}    {{ field }}={{ value }},
{% endfor %}){% endif %}{% if cte_annotations %}.annotate(
{% for alias, expression in cte_annotations.items() %}    {{ alias }}={{ expression }},
{% endfor %}){% endif %}

{{ result_var }} = {{ model_name }}.objects.filter(
    pk__in=Subquery({{ cte_name }}_subquery.values('pk'))
)"""
    )

    # aggregate - Aggregate operations
    add_or_update(
        "aggregate",
        "python_django",
        """# Aggregate {{ model_name }}
{{ result_var }} = {{ model_name }}.objects{% if filters %}.filter(
{% for field, value in filters.items() %}    {{ field }}={{ value }},
{% endfor %}){% endif %}.aggregate(
{% for alias, expression in aggregations.items() %}    {{ alias }}={{ expression }}{% if not loop.last %},{% endif %}
{% endfor %})"""
    )

    # json_build - Build JSON from fields
    add_or_update(
        "json_build",
        "python_django",
        """# Build JSON
{{ result_var }} = {
{% for key, value in json_structure.items() %}    '{{ key }}': {{ value }}{% if not loop.last %},{% endif %}
{% endfor %}}
{% if serialize %}{{ result_var }} = json.dumps({{ result_var }}){% endif %}"""
    )

    # cte - Common Table Expression (using subqueries or raw SQL)
    add_or_update(
        "cte",
        "python_django",
        """# CTE: {{ cte_name }}
{{ cte_name }}_subquery = {{ model_name }}.objects{% if cte_filters %}.filter(
{% for field, value in cte_filters.items() %}    {{ field }}={{ value }},
{% endfor %}){% endif %}{% if cte_annotations %}.annotate(
{% for alias, expression in cte_annotations.items() %}    {{ alias }}={{ expression }},
{% endfor %}){% endif %}

{{ result_var }} = {{ model_name }}.objects.filter(
    pk__in=Subquery({{ cte_name }}_subquery.values('pk'))
)"""
    )

    # subquery - Subquery operation
    add_or_update(
        "subquery",
        "python_django",
        """# Subquery
{{ result_var }} = {{ model_name }}.objects.filter(
{% for field, subquery in subquery_filters.items() %}    {{ field }}__in=Subquery({{ subquery }}.values('{{ subquery_field }}')),
{% endfor %})"""
    )

    # ===== DATA TRANSFORM PATTERNS =====

    # aggregate - Aggregation operations
    add_or_update(
        "aggregate",
        "python_django",
        """# Aggregate {{ model_name }}
{{ result_var }} = {{ model_name }}.objects{% if filters %}.filter(
{% for field, value in filters.items() %}    {{ field }}={{ value }},
{% endfor %}){% endif %}.aggregate(
{% for alias, agg_func in aggregations.items() %}    {{ alias }}={{ agg_func }},
{% endfor %})"""
    )

    # json_build - Build JSON structures
    add_or_update(
        "json_build",
        "python_django",
        """# Build JSON structure
import json
{{ result_var }} = {
{% for key, value in json_structure.items() %}    "{{ key }}": {{ value }},
{% endfor %}}
{% if serialize %}json.dumps({{ result_var }}){% endif %}"""
    )


if __name__ == "__main__":
    library = PatternLibrary("pattern_library.db")
    add_django_patterns(library)
    library.close()

    print("✅ Added Django ORM patterns to library")
    print(f"Total Django implementations: {len(library.get_all_languages()[1]['implementations'])}")