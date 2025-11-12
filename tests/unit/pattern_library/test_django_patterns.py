"""
Tests for Django ORM pattern implementations
"""

import pytest
import sqlite3
from src.pattern_library.api import PatternLibrary


@pytest.fixture
def library_with_django():
    """Create a pattern library with Django patterns loaded"""
    # Connect to existing database
    library = PatternLibrary.__new__(PatternLibrary)
    library.db_path = "pattern_library.db"
    library.db = sqlite3.connect("pattern_library.db")
    library.db.row_factory = sqlite3.Row

    return library


def test_django_declare_pattern(library_with_django):
    """Test Django declare pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="declare",
        language_name="python_django",
        context={
            "variable_name": "total",
            "variable_type": "Decimal",
            "default_value": "Decimal('0')"
        }
    )

    assert result == "total: Decimal = Decimal('0')"


def test_django_assign_pattern(library_with_django):
    """Test Django assign pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="assign",
        language_name="python_django",
        context={
            "variable_name": "total",
            "expression": "Decimal('100.50')"
        }
    )

    assert result == "total = Decimal('100.50')"


def test_django_if_pattern(library_with_django):
    """Test Django if pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="if",
        language_name="python_django",
        context={
            "condition": "total > 0",
            "then_steps": "return True",
            "else_steps": "return False"
        }
    )

    expected = """if total > 0:
    return True
else:
    return False
"""

    assert result == expected


def test_django_if_pattern_no_else(library_with_django):
    """Test Django if pattern without else"""
    result = library_with_django.compile_pattern(
        pattern_name="if",
        language_name="python_django",
        context={
            "condition": "user.is_active",
            "then_steps": "user.last_login = timezone.now()\nuser.save()",
            "else_steps": None
        }
    )

    expected = """if user.is_active:
    user.last_login = timezone.now()
    user.save()
"""

    assert result == expected


def test_django_foreach_pattern(library_with_django):
    """Test Django foreach pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="foreach",
        language_name="python_django",
        context={
            "iterator_var": "item",
            "collection": "items",
            "loop_body": "print(item.name)"
        }
    )

    expected = """for item in items:
    print(item.name)"""

    assert result == expected


def test_django_for_query_pattern(library_with_django):
    """Test Django for_query pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="for_query",
        language_name="python_django",
        context={
            "item_var": "user",
            "queryset": "User.objects.filter(is_active=True)",
            "loop_body": "send_email(user.email, 'Welcome!')"
        }
    )

    expected = """for user in User.objects.filter(is_active=True):
    send_email(user.email, 'Welcome!')"""

    assert result == expected


def test_django_insert_pattern(library_with_django):
    """Test Django insert pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="insert",
        language_name="python_django",
        context={
            "model_name": "User",
            "instance_var": "user",
            "field_values": {
                "username": "'john_doe'",
                "email": "'john@example.com'",
                "is_active": "True"
            }
        }
    )

    expected = """# Insert new User
user = User(
    username='john_doe',
    email='john@example.com',
    is_active=True,
)
user.save()"""

    assert result == expected


def test_django_update_pattern(library_with_django):
    """Test Django update pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="update",
        language_name="python_django",
        context={
            "model_name": "User",
            "instance_var": "user",
            "lookup_field": "pk",
            "lookup_value": "user_id",
            "field_values": {
                "email": "'new_email@example.com'",
                "last_login": "timezone.now()"
            }
        }
    )

    expected = """# Update User
user = User.objects.get(pk=user_id)
user.email = 'new_email@example.com'
user.last_login = timezone.now()
user.save()"""

    assert result == expected


def test_django_partial_update_pattern(library_with_django):
    """Test Django partial_update pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="partial_update",
        language_name="python_django",
        context={
            "model_name": "User",
            "instance_var": "user",
            "lookup_field": "pk",
            "lookup_value": "user_id",
            "updates": {
                "email": "'new_email@example.com'",
                "is_active": "False"
            }
        }
    )

    expected = """# Partial update User
user = User.objects.get(pk=user_id)
user.email = 'new_email@example.com'
user.is_active = False
user.save(update_fields=['email', 'is_active'])"""

    assert result == expected


def test_django_delete_pattern(library_with_django):
    """Test Django delete pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="delete",
        language_name="python_django",
        context={
            "model_name": "User",
            "instance_var": "user",
            "lookup_field": "pk",
            "lookup_value": "user_id"
        }
    )

    expected = """# Delete User
user = User.objects.get(pk=user_id)
user.delete()"""

    assert result == expected


def test_django_query_pattern(library_with_django):
    """Test Django query pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="query",
        language_name="python_django",
        context={
            "model_name": "User",
            "result_var": "users",
            "filters": {
                "is_active": "True",
                "created_at__gte": "start_date"
            },
            "select_related": ["profile"],
            "order_by": ["-created_at"]
        }
    )

    expected = """# Query User
users = User.objects.filter(
    is_active=True,
    created_at__gte=start_date
).select_related('profile').order_by('-created_at')"""

    assert result == expected


def test_django_aggregate_pattern(library_with_django):
    """Test Django aggregate pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="aggregate",
        language_name="python_django",
        context={
            "model_name": "Order",
            "result_var": "stats",
            "filters": {
                "status": "'completed'"
            },
            "aggregations": {
                "total_orders": "Count('id')",
                "total_amount": "Sum('amount')"
            }
        }
    )

    expected = """# Aggregate Order
stats = Order.objects.filter(
    status='completed',
).aggregate(
    total_orders=Count('id'),
    total_amount=Sum('amount'),
)"""

    assert result == expected


def test_django_call_function_pattern(library_with_django):
    """Test Django call_function pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="call_function",
        language_name="python_django",
        context={
            "result_variable": "result",
            "function_name": "calculate_total",
            "arguments": ["order.items", "tax_rate"]
        }
    )

    assert result == "result = calculate_total(order.items, tax_rate)"


def test_django_return_pattern(library_with_django):
    """Test Django return pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="return",
        language_name="python_django",
        context={
            "expression": "JsonResponse({'status': 'success'})"
        }
    )

    assert result == "return JsonResponse({'status': 'success'})"


def test_django_exception_handling_pattern(library_with_django):
    """Test Django exception_handling pattern compilation"""
    result = library_with_django.compile_pattern(
        pattern_name="exception_handling",
        language_name="python_django",
        context={
            "try_body": "user = User.objects.get(pk=user_id)\nuser.is_active = True\nuser.save()",
            "exception_handlers": [
                {"exception_type": "User.DoesNotExist", "handler_body": "raise Http404('User not found')"},
                {"exception_type": "ValidationError", "handler_body": "return JsonResponse({'error': str(e)}, status=400)"}
            ],
            "finally_body": "logger.info(f'Processed user {user_id}')"
        }
    )

    expected = """try:
    user = User.objects.get(pk=user_id)
    user.is_active = True
    user.save()

except User.DoesNotExist:
    raise Http404('User not found')
except ValidationError:
    return JsonResponse({'error': str(e)}, status=400)
finally:
    logger.info(f'Processed user {user_id}')"""

    assert result == expected