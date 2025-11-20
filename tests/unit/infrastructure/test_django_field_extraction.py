"""Test extraction of all Django field types"""

import textwrap
from reverse_engineering.python_ast_parser import PythonASTParser


def test_positive_integer_field_extraction():
    """Test PositiveIntegerField is extracted"""
    source_code = textwrap.dedent("""
        from django.db import models
        from django.core.validators import MinValueValidator

        class Booker(models.Model):
            group_size = models.PositiveIntegerField(
                validators=[MinValueValidator(1)]
            )
    """)

    parser = PythonASTParser()
    entity = parser.parse_entity(source_code)

    # Should extract group_size field
    field_names = [f.field_name for f in entity.fields]
    assert "group_size" in field_names

    # Should map to integer type
    group_size = next(f for f in entity.fields if f.field_name == "group_size")
    assert group_size.field_type == "integer"


def test_all_django_numeric_fields():
    """Test all numeric field types are extracted"""
    source_code = textwrap.dedent("""
        from django.db import models

        class TestModel(models.Model):
            int_field = models.IntegerField()
            positive_int = models.PositiveIntegerField()
            small_int = models.SmallIntegerField()
            big_int = models.BigIntegerField()
            decimal_field = models.DecimalField(max_digits=10, decimal_places=2)
            float_field = models.FloatField()
    """)

    parser = PythonASTParser()
    entity = parser.parse_entity(source_code)

    field_names = [f.field_name for f in entity.fields]
    assert len(field_names) == 6
    assert "int_field" in field_names
    assert "positive_int" in field_names
    assert "small_int" in field_names
    assert "big_int" in field_names
    assert "decimal_field" in field_names
    assert "float_field" in field_names


def test_field_with_validators():
    """Test fields with validators are extracted"""
    source_code = textwrap.dedent("""
        from django.db import models
        from django.core.validators import MinValueValidator, MaxValueValidator

        class TestModel(models.Model):
            age = models.PositiveIntegerField(
                validators=[
                    MinValueValidator(0),
                    MaxValueValidator(150)
                ]
            )
    """)

    parser = PythonASTParser()
    entity = parser.parse_entity(source_code)

    field_names = [f.field_name for f in entity.fields]
    assert "age" in field_names
