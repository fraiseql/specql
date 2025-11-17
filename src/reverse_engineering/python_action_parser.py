"""
Python Action Parser - Extract actions from Python web frameworks

Supports:
- FastAPI (async routes with decorators)
- Flask (app.route, blueprints, MethodView)
- Django (function views, class views, ViewSets)

Based on proven Rust action parser architecture.
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PythonAction:
    """Represents an action extracted from Python code"""

    name: str
    type: str  # create, read, update, delete, custom
    http_method: str | None = None
    path: str | None = None
    parameters: list[str] | None = None
    is_async: bool = False
    framework: str = "unknown"  # fastapi, flask, django
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.parameters is None:
            self.parameters = []


class PythonActionParser:
    """
    Extract actions from Python web framework code.

    Usage:
        parser = PythonActionParser()
        actions = parser.extract_actions(Path("views.py"))
    """

    def __init__(self) -> None:
        self.action_mapper = PythonActionMapper()
        self.route_mapper = PythonRouteMapper()

    def extract_actions(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract actions from Python file"""
        with open(file_path) as f:
            code = f.read()

        return self.extract_actions_from_code(code)

    def extract_actions_from_code(self, code: str) -> list[dict[str, Any]]:
        """Extract actions from Python code string"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Failed to parse Python code: {e}")
            return []

        actions = []
        processed_functions = set()  # Track functions that are part of classes

        # First pass: Extract from classes (Django, Flask MethodView)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_actions = self._extract_from_class(node)
                actions.extend(class_actions)
                # Mark all functions in this class as processed
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        processed_functions.add(id(item))

        # Second pass: Extract from standalone function definitions (FastAPI, Flask routes)
        for node in ast.walk(tree):
            if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)) and id(
                node
            ) not in processed_functions:
                action = self._extract_from_function(node)
                if action:
                    actions.append(action)

        return [self._action_to_dict(a) for a in actions]

    def _extract_from_function(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> PythonAction | None:
        """Extract action from standalone function"""
        # Check decorators for route information
        route_info = self.route_mapper.extract_route_from_decorators(func.decorator_list)

        if route_info:
            # Has route decorator (FastAPI, Flask)
            action_type = self.action_mapper.http_method_to_crud(route_info["http_method"])
            return PythonAction(
                name=func.name,
                type=action_type,
                http_method=route_info["http_method"],
                path=route_info.get("path"),
                parameters=self._extract_parameters(func),
                is_async=isinstance(func, ast.AsyncFunctionDef),
                framework=route_info.get("framework", "unknown"),
                confidence=0.95,  # High confidence when decorator present
            )
        else:
            # No decorator, try name-based detection
            action_type = self.action_mapper.detect_crud_from_name(func.name)
            if action_type:
                return PythonAction(
                    name=func.name,
                    type=action_type,
                    parameters=self._extract_parameters(func),
                    is_async=isinstance(func, ast.AsyncFunctionDef),
                    framework="django",  # Assume Django for non-decorated
                    confidence=0.70,  # Lower confidence for name-based
                )

        return None

    def _extract_from_class(self, cls: ast.ClassDef) -> list[PythonAction]:
        """Extract actions from class (MethodView, ViewSet, etc.)"""
        actions = []

        # Check if it's a view class (Django, Flask)
        is_view_class = self._is_view_class(cls)

        if is_view_class:
            for item in cls.body:
                if isinstance(item, ast.FunctionDef):
                    # HTTP method names in view classes
                    if item.name.lower() in ["get", "post", "put", "patch", "delete"]:
                        action = PythonAction(
                            name=item.name,
                            type=self.action_mapper.http_method_to_crud(item.name.upper()),
                            http_method=item.name.upper(),
                            parameters=self._extract_parameters(item),
                            is_async=False,
                            framework="django"
                            if "View" in [b.id for b in cls.bases if isinstance(b, ast.Name)]
                            else "flask",
                            confidence=0.90,
                        )
                        actions.append(action)
                    # ViewSet-style methods
                    elif item.name in ["list", "retrieve", "create", "update", "destroy"]:
                        crud_map = {
                            "list": "read",
                            "retrieve": "read",
                            "create": "create",
                            "update": "update",
                            "destroy": "delete",
                        }
                        action = PythonAction(
                            name=item.name,
                            type=crud_map[item.name],
                            parameters=self._extract_parameters(item),
                            framework="django",  # ViewSet is DRF
                            confidence=0.95,
                        )
                        actions.append(action)

        return actions

    def _is_view_class(self, cls: ast.ClassDef) -> bool:
        """Check if class is a view class"""
        # Check base classes
        base_names = []
        for base in cls.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)

        view_indicators = ["View", "MethodView", "ViewSet", "ModelViewSet", "APIView"]
        return any(indicator in name for name in base_names for indicator in view_indicators)

    def _extract_parameters(self, func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Extract parameter names from function"""
        params = []
        for arg in func.args.args:
            # Skip 'self', 'request', 'cls'
            if arg.arg not in ["self", "request", "cls"]:
                params.append(arg.arg)
        return params

    def _action_to_dict(self, action: PythonAction) -> dict[str, Any]:
        """Convert PythonAction to dict"""
        return {
            "name": action.name,
            "type": action.type,
            "http_method": action.http_method,
            "path": action.path,
            "parameters": action.parameters,
            "is_async": action.is_async,
            "framework": action.framework,
            "confidence": action.confidence,
        }


class PythonActionMapper:
    """Map Python constructs to SpecQL CRUD actions"""

    def detect_crud_from_name(self, name: str) -> str | None:
        """Detect CRUD type from method/function name"""
        name_lower = name.lower()

        # CREATE patterns
        if any(kw in name_lower for kw in ["create", "add", "insert", "save", "new"]):
            return "create"

        # READ patterns
        if any(
            kw in name_lower
            for kw in ["get", "find", "fetch", "retrieve", "list", "search", "query"]
        ):
            return "read"

        # UPDATE patterns
        if any(kw in name_lower for kw in ["update", "modify", "edit", "change", "patch"]):
            return "update"

        # DELETE patterns
        if any(kw in name_lower for kw in ["delete", "remove", "destroy", "purge"]):
            return "delete"

        return None

    def http_method_to_crud(self, http_method: str) -> str:
        """Map HTTP method to CRUD type"""
        mapping = {
            "POST": "create",
            "GET": "read",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        return mapping.get(http_method.upper(), "custom")


class PythonRouteMapper:
    """Extract route information from decorators"""

    def extract_route_from_decorators(self, decorators: list[ast.expr]) -> dict[str, Any] | None:
        """Extract route info from function decorators"""
        for decorator in decorators:
            # FastAPI: @router.get("/path")
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                attr = decorator.func
                if isinstance(attr.value, ast.Name) and "router" in attr.value.id.lower():
                    http_method = attr.attr.upper()  # get, post, put, delete
                    path = self._extract_path_from_call(decorator)
                    return {"http_method": http_method, "path": path, "framework": "fastapi"}

            # Flask: @app.route("/path", methods=["POST"]) or @bp.route(...)
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                attr = decorator.func
                if attr.attr == "route":
                    path = self._extract_path_from_call(decorator)
                    http_method = self._extract_methods_from_call(decorator)
                    return {"http_method": http_method or "GET", "path": path, "framework": "flask"}

        return None

    def _extract_path_from_call(self, call: ast.Call) -> str | None:
        """Extract path string from decorator call"""
        if call.args and isinstance(call.args[0], ast.Constant):
            value = call.args[0].value
            if isinstance(value, str):
                return value
        return None

    def _extract_methods_from_call(self, call: ast.Call) -> str | None:
        """Extract HTTP methods from Flask route decorator"""
        for keyword in call.keywords:
            if keyword.arg == "methods":
                if isinstance(keyword.value, ast.List) and keyword.value.elts:
                    if isinstance(keyword.value.elts[0], ast.Constant):
                        value = keyword.value.elts[0].value
                        if isinstance(value, str):
                            return value
        return None
