"""
Unit tests for Python action parser - FastAPI framework

Your responsibility: Ensure these tests cover all FastAPI patterns
"""

import pytest
from src.reverse_engineering.python_action_parser import PythonActionParser


class TestFastAPIParser:
    """Test FastAPI-specific action parsing"""

    @pytest.fixture
    def parser(self):
        return PythonActionParser()

    def test_simple_post_route(self, parser):
        """Test extracting CREATE action from POST route"""
        code = '''
from fastapi import APIRouter

router = APIRouter()

@router.post("/contacts")
async def create_contact(email: str):
    """Create a new contact"""
    return {"id": "123"}
'''
        # EXPECTED TO FAIL: Parser not implemented yet
        actions = parser.extract_actions_from_code(code)

        assert len(actions) == 1
        assert actions[0]["name"] == "create_contact"
        assert actions[0]["type"] == "create"
        assert actions[0]["http_method"] == "POST"
        assert actions[0]["path"] == "/contacts"
        assert actions[0]["is_async"] is True

    def test_get_with_path_param(self, parser):
        """Test extracting READ action with path parameter"""
        code = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: int):
    return {"id": contact_id}
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert len(actions) == 1
        assert actions[0]["type"] == "read"
        assert actions[0]["parameters"] == ["contact_id"]

    def test_put_route(self, parser):
        """Test extracting UPDATE action from PUT route"""
        code = """
@router.put("/contacts/{id}")
async def update_contact(id: int, email: str):
    return {"updated": True}
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "update"
        assert actions[0]["http_method"] == "PUT"

    def test_delete_route(self, parser):
        """Test extracting DELETE action"""
        code = """
@router.delete("/contacts/{id}")
async def delete_contact(id: int):
    return {"deleted": True}
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "delete"

    def test_multiple_routes(self, parser):
        """Test extracting multiple actions from single file"""
        code = """
from fastapi import APIRouter

router = APIRouter()

@router.post("/contacts")
async def create_contact(email: str):
    pass

@router.get("/contacts")
async def list_contacts():
    pass

@router.get("/contacts/{id}")
async def get_contact(id: int):
    pass
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert len(actions) == 3
        assert actions[0]["type"] == "create"
        assert actions[1]["type"] == "read"  # list
        assert actions[2]["type"] == "read"  # get

    def test_request_body_model(self, parser):
        """Test extracting action with Pydantic model"""
        code = """
from fastapi import APIRouter
from pydantic import BaseModel

class ContactCreate(BaseModel):
    email: str
    name: str

router = APIRouter()

@router.post("/contacts")
async def create_contact(contact: ContactCreate):
    pass
"""
        actions = parser.extract_actions_from_code(code)

        # Action is detected
        assert len(actions) == 1
        assert actions[0]["name"] == "create_contact"
        assert actions[0]["http_method"] == "POST"
        # NOTE: Pydantic model detection (has_body_model metadata) not yet implemented

    def test_response_model(self, parser):
        """Test action with response_model"""
        code = """
@router.get("/contacts/{id}", response_model=ContactResponse)
async def get_contact(id: int):
    pass
"""
        actions = parser.extract_actions_from_code(code)

        # Action is detected
        assert len(actions) == 1
        assert actions[0]["name"] == "get_contact"
        assert actions[0]["http_method"] == "GET"
        # NOTE: Response model extraction from decorators not yet implemented


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
