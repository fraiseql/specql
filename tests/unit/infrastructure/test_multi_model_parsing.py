"""Test parsing files with multiple Django models"""

import textwrap

from reverse_engineering.python_ast_parser import PythonASTParser


def test_multiple_models_in_one_file():
    """Test all models in file are detected"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Booker(models.Model):
            name = models.CharField(max_length=255)

        class Accommodation(models.Model):
            title = models.CharField(max_length=255)

        class Booking(models.Model):
            status = models.CharField(max_length=50)
    """)

    parser = PythonASTParser()
    entities = parser.parse(source_code, "test_models.py")

    # Should extract all 3 models
    assert len(entities) == 3

    entity_names = [e.entity_name for e in entities]
    assert "Booker" in entity_names
    assert "Accommodation" in entity_names
    assert "Booking" in entity_names


def test_models_with_intermediate_classes():
    """Test models are detected even with non-model classes"""
    source_code = textwrap.dedent("""
        from django.db import models

        class HelperClass:
            pass

        class ModelA(models.Model):
            field1 = models.CharField(max_length=255)

        class AnotherHelper:
            pass

        class ModelB(models.Model):
            field2 = models.CharField(max_length=255)
    """)

    parser = PythonASTParser()
    entities = parser.parse(source_code, "test_models.py")

    # Should only extract models, not helpers
    assert len(entities) == 2
    entity_names = [e.entity_name for e in entities]
    assert "ModelA" in entity_names
    assert "ModelB" in entity_names
    assert "HelperClass" not in entity_names
    assert "AnotherHelper" not in entity_names
