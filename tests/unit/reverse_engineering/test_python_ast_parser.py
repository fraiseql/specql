import pytest
from src.reverse_engineering.python_ast_parser import PythonASTParser
from src.reverse_engineering.protocols import SourceLanguage

class TestPythonASTParser:

    def test_parse_dataclass_entity(self):
        """Test parsing Python dataclass to ParsedEntity"""
        source = '''
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    """CRM contact entity"""
    email: str
    company_id: Optional[int] = None
    status: str = "lead"
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)

        assert entity.entity_name == "Contact"
        assert entity.source_language == SourceLanguage.PYTHON
        assert entity.docstring == "CRM contact entity"
        assert "@dataclass" in entity.decorators

        # Check fields
        assert len(entity.fields) == 3

        email_field = next(f for f in entity.fields if f.field_name == "email")
        assert email_field.field_type == "text"
        assert email_field.required is True

        company_field = next(f for f in entity.fields if f.field_name == "company_id")
        assert company_field.field_type == "integer"
        assert company_field.required is False

        status_field = next(f for f in entity.fields if f.field_name == "status")
        assert status_field.default == "lead"
        assert status_field.required is False

    def test_parse_pydantic_model(self):
        """Test parsing Pydantic model"""
        source = '''
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr
    age: int
    is_active: bool = True
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)

        assert entity.entity_name == "User"
        assert "BaseModel" in entity.inheritance

        patterns = parser.detect_patterns(entity)
        assert "pydantic_model" in patterns

    def test_parse_django_model(self):
        """Test parsing Django model"""
        source = '''
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_at = models.DateTimeField(null=True)
    author = models.ForeignKey('User', on_delete=models.CASCADE)
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)

        assert entity.entity_name == "Article"
        assert len(entity.fields) == 4

        title_field = next(f for f in entity.fields if f.field_name == "title")
        assert title_field.field_type == "text"
        assert title_field.original_type == "CharField"

        author_field = next(f for f in entity.fields if f.field_name == "author")
        assert author_field.field_type == "ref"
        assert author_field.is_foreign_key is True
        assert author_field.foreign_key_target == "User"

        patterns = parser.detect_patterns(entity)
        assert "django_model" in patterns

    def test_parse_methods(self):
        """Test parsing class methods"""
        source = '''
class Contact:
    status: str

    def qualify_lead(self) -> bool:
        """Qualify this lead"""
        if self.status != "lead":
            return False
        self.status = "qualified"
        return True

    @classmethod
    def create_from_email(cls, email: str):
        return cls(email=email)
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)

        assert len(entity.methods) == 2

        qualify = next(m for m in entity.methods if m.method_name == "qualify_lead")
        assert qualify.return_type == "bool"
        assert qualify.docstring == "Qualify this lead"
        assert len(qualify.body_lines) > 0

        create = next(m for m in entity.methods if m.method_name == "create_from_email")
        assert create.is_classmethod is True
        assert len(create.parameters) == 1
        assert create.parameters[0]['name'] == 'email'

    def test_detect_state_machine_pattern(self):
        """Test detecting state machine pattern"""
        source = '''
class Order:
    status: str

    def transition_to_shipped(self):
        self.status = "shipped"

    def transition_to_delivered(self):
        self.status = "delivered"
'''

        parser = PythonASTParser()
        entity = parser.parse_entity(source)

        patterns = parser.detect_patterns(entity)
        assert "state_machine" in patterns

    def test_type_normalization(self):
        """Test Python → SpecQL type normalization"""
        parser = PythonASTParser()

        # Test basic types
        assert parser._normalize_type("str") == ("text", True)
        assert parser._normalize_type("int") == ("integer", True)
        assert parser._normalize_type("float") == ("float", True)
        assert parser._normalize_type("bool") == ("boolean", True)

        # Test Optional types
        assert parser._normalize_type("Optional[str]") == ("text", False)
        assert parser._normalize_type("Optional[int]") == ("integer", False)

        # Test complex types
        assert parser._normalize_type("Dict") == ("json", True)
        assert parser._normalize_type("List") == ("list", True)