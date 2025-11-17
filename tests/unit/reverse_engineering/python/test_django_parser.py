"""
Unit tests for Python action parser - Django framework
"""

import pytest
from src.reverse_engineering.python_action_parser import PythonActionParser


class TestDjangoParser:
    """Test Django-specific action parsing"""

    @pytest.fixture
    def parser(self):
        return PythonActionParser()

    def test_function_based_view(self, parser):
        """Test Django function-based view"""
        code = """
from django.http import JsonResponse

def create_contact(request):
    if request.method == "POST":
        # Create logic
        return JsonResponse({"id": "123"})
"""
        # EXPECTED TO FAIL
        actions = parser.extract_actions_from_code(code)

        assert len(actions) == 1
        assert actions[0]["type"] == "create"
        assert actions[0]["framework"] == "django"

    def test_class_based_view(self, parser):
        """Test Django class-based view"""
        code = """
from django.views import View

class ContactView(View):
    def get(self, request, pk):
        return JsonResponse({"id": pk})

    def post(self, request):
        return JsonResponse({"created": True})
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert len(actions) == 2
        assert actions[0]["type"] == "read"
        assert actions[1]["type"] == "create"

    def test_viewset(self, parser):
        """Test Django REST framework ViewSet"""
        code = """
from rest_framework import viewsets

class ContactViewSet(viewsets.ModelViewSet):
    def list(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def create(self, request):
        pass

    def update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert len(actions) == 5
        assert actions[0]["type"] == "read"  # list
        assert actions[1]["type"] == "read"  # retrieve
        assert actions[2]["type"] == "create"  # create
        assert actions[3]["type"] == "update"  # update
        assert actions[4]["type"] == "delete"  # destroy


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
