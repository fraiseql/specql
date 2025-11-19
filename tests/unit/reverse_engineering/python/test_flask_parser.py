"""
Unit tests for Python action parser - Flask framework
"""

import pytest

from src.reverse_engineering.python_action_parser import PythonActionParser


class TestFlaskParser:
    """Test Flask-specific action parsing"""

    @pytest.fixture
    def parser(self):
        return PythonActionParser()

    def test_simple_route_decorator(self, parser):
        """Test Flask @app.route decorator"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.route("/contacts", methods=["POST"])
def create_contact():
    return {"id": "123"}
"""
        # EXPECTED TO FAIL
        actions = parser.extract_actions_from_code(code)

        assert len(actions) == 1
        assert actions[0]["type"] == "create"
        assert actions[0]["framework"] == "flask"

    def test_blueprint_route(self, parser):
        """Test Flask Blueprint routes"""
        code = """
from flask import Blueprint

bp = Blueprint('contacts', __name__)

@bp.route("/contacts/<int:id>", methods=["GET"])
def get_contact(id):
    return {"id": id}
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert actions[0]["type"] == "read"
        assert actions[0]["path"] == "/contacts/<int:id>"

    def test_method_view(self, parser):
        """Test Flask MethodView class"""
        code = """
from flask.views import MethodView

class ContactAPI(MethodView):
    def get(self, id):
        return {"id": id}

    def post(self):
        return {"created": True}

    def put(self, id):
        return {"updated": True}

    def delete(self, id):
        return {"deleted": True}
"""
        actions = parser.extract_actions_from_code(code)

        # EXPECTED TO FAIL
        assert len(actions) == 4
        assert actions[0]["type"] == "read"  # get
        assert actions[1]["type"] == "create"  # post
        assert actions[2]["type"] == "update"  # put
        assert actions[3]["type"] == "delete"  # delete


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
