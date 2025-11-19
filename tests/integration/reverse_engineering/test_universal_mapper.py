"""
Integration tests for universal action mapper
"""

import pytest
import yaml

from src.reverse_engineering.universal_action_mapper import UniversalActionMapper


class TestUniversalMapperPython:
    """Test Python integration with universal mapper"""

    @pytest.fixture
    def mapper(self):
        return UniversalActionMapper()

    def test_python_to_specql(self, mapper, tmp_path):
        """Test converting Python FastAPI to SpecQL"""
        py_file = tmp_path / "contacts.py"
        py_file.write_text("""
from fastapi import APIRouter

router = APIRouter()

@router.post("/contacts")
async def create_contact(email: str):
    pass

@router.get("/contacts/{id}")
async def get_contact(id: int):
    pass
        """)

        yaml_output = mapper.convert_file(py_file, language="python")

        # Verify YAML structure
        spec = yaml.safe_load(yaml_output)
        assert "entity" in spec
        assert "actions" in spec
        assert len(spec["actions"]) == 2

    def test_flask_to_specql(self, mapper, tmp_path):
        """Test Flask conversion"""
        py_file = tmp_path / "views.py"
        py_file.write_text("""
from flask import Blueprint

bp = Blueprint('contacts', __name__)

@bp.route("/contacts", methods=["POST"])
def create_contact():
    pass
        """)

        yaml_output = mapper.convert_file(py_file, language="python")
        spec = yaml.safe_load(yaml_output)

        assert spec["actions"][0]["name"] == "create_contact"

    def test_django_to_specql(self, mapper, tmp_path):
        """Test Django conversion"""
        py_file = tmp_path / "views.py"
        py_file.write_text("""
from django.views import View

class ContactView(View):
    def get(self, request, pk):
        return {"id": pk}

    def post(self, request):
        return {"created": True}
        """)

        yaml_output = mapper.convert_file(py_file, language="python")
        spec = yaml.safe_load(yaml_output)

        assert len(spec["actions"]) == 2
        assert spec["actions"][0]["type"] == "read"
        assert spec["actions"][1]["type"] == "create"

    def test_python_code_string_conversion(self, mapper):
        """Test converting Python code string directly"""
        code = """
from fastapi import APIRouter

router = APIRouter()

@router.post("/users")
async def create_user(name: str):
    pass
        """

        yaml_output = mapper.convert_code(code, language="python")
        spec = yaml.safe_load(yaml_output)

        assert spec["entity"] == "User"  # Should infer from action name
        assert len(spec["actions"]) == 1
        assert spec["actions"][0]["name"] == "create_user"

    def test_unsupported_language(self, mapper, tmp_path):
        """Test error handling for unsupported languages"""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")

        with pytest.raises(ValueError, match="Unsupported language"):
            mapper.convert_file(py_file, language="javascript")


class TestUniversalMapperIntegration:
    """Test integration between different language parsers"""

    @pytest.fixture
    def mapper(self):
        return UniversalActionMapper()

    def test_metadata_included(self, mapper, tmp_path):
        """Test that metadata is properly included in output"""
        py_file = tmp_path / "contacts.py"
        py_file.write_text("""
from fastapi import APIRouter

router = APIRouter()

@router.get("/contacts")
async def list_contacts():
    pass
        """)

        yaml_output = mapper.convert_file(py_file, language="python")
        spec = yaml.safe_load(yaml_output)

        assert "_metadata" in spec
        assert spec["_metadata"]["source_language"] == "python"
        assert spec["_metadata"]["extraction_method"] == "universal_action_mapper"
        assert spec["_metadata"]["total_actions"] == 1

    def test_entity_name_inference(self, mapper, tmp_path):
        """Test entity name inference from file and actions"""
        # Test file-based inference
        py_file = tmp_path / "contact_controller.py"
        py_file.write_text("""
@router.get("/contacts")
def get_contacts():
    pass
        """)

        yaml_output = mapper.convert_file(py_file, language="python")
        spec = yaml.safe_load(yaml_output)

        # Should infer 'Contact' from filename 'contact_controller.py'
        assert spec["entity"] == "Contact"
