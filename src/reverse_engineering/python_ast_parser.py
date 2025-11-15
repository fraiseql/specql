import ast
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.reverse_engineering.protocols import (
    ParsedEntity,
    ParsedField,
    ParsedMethod,
    SourceLanguage
)

class PythonASTParser:
    """
    Parse Python code to language-agnostic AST

    Supports:
    - Dataclasses
    - Pydantic models
    - Django models
    - SQLAlchemy models
    - Plain Python classes
    """

    def __init__(self):
        self.type_mapping = self._build_type_mapping()

    @property
    def supported_language(self) -> SourceLanguage:
        return SourceLanguage.PYTHON

    def parse_entity(self, source_code: str, file_path: str = "") -> ParsedEntity:
        """
        Parse Python class to ParsedEntity

        Example input:
        ```python
        from dataclasses import dataclass
        from typing import Optional

        @dataclass
        class Contact:
            '''CRM contact entity'''
            email: str
            company_id: Optional[int] = None
            status: str = "lead"

            def qualify_lead(self) -> bool:
                if self.status != "lead":
                    return False
                self.status = "qualified"
                return True
        ```

        Returns ParsedEntity with fields and methods
        """
        try:
            tree = ast.parse(source_code)

            # Find class definition
            class_def = self._find_class_definition(tree)
            if not class_def:
                raise ValueError("No class definition found in source code")

            # Extract namespace from file path or imports
            namespace = self._extract_namespace(file_path, tree)

            # Parse class components
            entity = ParsedEntity(
                entity_name=class_def.name,
                namespace=namespace,
                fields=self._parse_fields(class_def),
                methods=self._parse_methods(class_def),
                inheritance=self._parse_inheritance(class_def),
                decorators=self._parse_class_decorators(class_def),
                docstring=ast.get_docstring(class_def),
                source_language=SourceLanguage.PYTHON,
                metadata={
                    "file_path": file_path,
                    "line_number": class_def.lineno,
                }
            )

            return entity

        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse Python entity: {e}")

    def parse_method(self, source_code: str) -> ParsedMethod:
        """Parse Python function/method to ParsedMethod"""
        try:
            tree = ast.parse(source_code)
            func_def = self._find_function_definition(tree)

            if not func_def:
                raise ValueError("No function definition found")

            return ParsedMethod(
                method_name=func_def.name,
                parameters=self._parse_function_parameters(func_def),
                return_type=self._parse_return_type(func_def),
                body_lines=self._extract_body_lines(func_def),
                decorators=self._parse_function_decorators(func_def),
                docstring=ast.get_docstring(func_def),
                is_async=isinstance(func_def, ast.AsyncFunctionDef),
                metadata={
                    "line_number": func_def.lineno,
                }
            )

        except Exception as e:
            raise ValueError(f"Failed to parse Python method: {e}")

    def detect_patterns(self, entity: ParsedEntity) -> List[str]:
        """
        Detect Python-specific patterns

        Patterns:
        - dataclass
        - pydantic_model
        - django_model
        - sqlalchemy_model
        - enum_class
        - state_machine
        - repository_pattern
        """
        patterns = []

        # Dataclass pattern
        if "@dataclass" in entity.decorators:
            patterns.append("dataclass")

        # Pydantic model
        if "BaseModel" in entity.inheritance:
            patterns.append("pydantic_model")

        # Django model
        if "models.Model" in entity.inheritance or "Model" in entity.inheritance:
            patterns.append("django_model")

        # SQLAlchemy model
        if "Base" in entity.inheritance or "DeclarativeBase" in entity.inheritance:
            patterns.append("sqlalchemy_model")

        # Enum class
        if "Enum" in entity.inheritance:
            patterns.append("enum_class")

        # State machine (has status field + transition methods)
        has_status = any(f.field_name in ["status", "state"] for f in entity.fields)
        has_transitions = any("transition" in m.method_name or "set_" in m.method_name
                              for m in entity.methods)
        if has_status and has_transitions:
            patterns.append("state_machine")

        # Repository pattern (CRUD methods)
        crud_methods = {"create", "read", "update", "delete", "find", "save"}
        method_names = {m.method_name for m in entity.methods}
        if len(crud_methods & method_names) >= 3:
            patterns.append("repository_pattern")

        return patterns

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _find_class_definition(self, tree: ast.Module) -> Optional[ast.ClassDef]:
        """Find first class definition in AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return node
        return None

    def _find_function_definition(self, tree: ast.Module) -> Optional[ast.FunctionDef | ast.AsyncFunctionDef]:
        """Find first function definition in AST"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return node
        return None

    def _extract_namespace(self, file_path: str, tree: ast.Module) -> str:
        """Extract namespace from file path or package"""
        if file_path:
            # Convert file path to Python module path
            # e.g., src/domain/crm/contact.py → crm
            parts = Path(file_path).parts
            if "domain" in parts:
                idx = parts.index("domain")
                if idx + 1 < len(parts):
                    return parts[idx + 1]

        # Default namespace
        return "public"

    def _parse_fields(self, class_def: ast.ClassDef) -> List[ParsedField]:
        """Parse class fields from annotations and assignments"""
        fields = []

        # From type annotations (dataclass, Pydantic)
        if hasattr(class_def, 'body'):
            for node in class_def.body:
                if isinstance(node, ast.AnnAssign):
                    field = self._parse_annotated_field(node)
                    if field:
                        fields.append(field)

                # Django/SQLAlchemy field assignments
                elif isinstance(node, ast.Assign):
                    field = self._parse_assigned_field(node)
                    if field:
                        fields.append(field)

        return fields

    def _parse_annotated_field(self, node: ast.AnnAssign) -> Optional[ParsedField]:
        """Parse annotated field (e.g., email: str)"""
        if not isinstance(node.target, ast.Name):
            return None

        field_name = node.target.id

        # Skip private/magic fields
        if field_name.startswith('_'):
            return None

        # Parse type annotation
        original_type = ast.unparse(node.annotation)
        field_type, required = self._normalize_type(original_type)

        # Parse default value
        default = None
        if node.value:
            default = self._extract_default_value(node.value)
            required = False

        return ParsedField(
            field_name=field_name,
            field_type=field_type,
            original_type=original_type,
            required=required,
            default=default,
        )

    def _parse_assigned_field(self, node: ast.Assign) -> Optional[ParsedField]:
        """Parse field assignment (Django/SQLAlchemy models)"""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return None

        field_name = node.targets[0].id

        # Skip private fields
        if field_name.startswith('_'):
            return None

        # Detect Django/SQLAlchemy field types
        if isinstance(node.value, ast.Call):
            field_info = self._parse_orm_field(node.value)
            if field_info:
                return ParsedField(
                    field_name=field_name,
                    field_type=field_info['type'],
                    original_type=field_info['original_type'],
                    required=field_info.get('required', True),
                    default=field_info.get('default'),
                    is_foreign_key=field_info.get('is_foreign_key', False),
                    foreign_key_target=field_info.get('foreign_key_target'),
                )

        return None

    def _parse_orm_field(self, call_node: ast.Call) -> Optional[Dict[str, Any]]:
        """Parse Django/SQLAlchemy field definition"""
        if not isinstance(call_node.func, ast.Attribute):
            return None

        field_class = call_node.func.attr

        # Django fields
        django_mapping = {
            'CharField': 'text',
            'TextField': 'text',
            'EmailField': 'email',
            'IntegerField': 'integer',
            'BigIntegerField': 'integer',
            'DecimalField': 'decimal',
            'FloatField': 'float',
            'BooleanField': 'boolean',
            'DateField': 'date',
            'DateTimeField': 'timestamp',
            'JSONField': 'json',
            'ForeignKey': 'ref',
            'OneToOneField': 'ref',
        }

        # SQLAlchemy fields
        sqlalchemy_mapping = {
            'String': 'text',
            'Text': 'text',
            'Integer': 'integer',
            'BigInteger': 'integer',
            'Numeric': 'decimal',
            'Float': 'float',
            'Boolean': 'boolean',
            'Date': 'date',
            'DateTime': 'timestamp',
            'JSON': 'json',
            'ForeignKey': 'ref',
        }

        specql_type = (django_mapping.get(field_class) or
                       sqlalchemy_mapping.get(field_class))

        if not specql_type:
            return None

        field_info: Dict[str, Any] = {
            'type': specql_type,
            'original_type': field_class,
        }

        # Extract field constraints from kwargs
        for keyword in call_node.keywords:
            if keyword.arg == 'null' and isinstance(keyword.value, ast.Constant):
                field_info['required'] = not keyword.value.value

            elif keyword.arg == 'default':
                field_info['default'] = self._extract_default_value(keyword.value)
                field_info['required'] = False

            elif keyword.arg == 'to' and specql_type == 'ref':
                # ForeignKey target
                if isinstance(keyword.value, ast.Constant):
                    field_info['foreign_key_target'] = keyword.value.value
                    field_info['is_foreign_key'] = True

        # Handle positional arguments for ForeignKey
        if specql_type == 'ref' and call_node.args:
            # First argument is usually the target model
            if isinstance(call_node.args[0], ast.Constant):
                field_info['foreign_key_target'] = call_node.args[0].value
                field_info['is_foreign_key'] = True

        return field_info

    def _normalize_type(self, type_str: str) -> tuple[str, bool]:
        """
        Normalize Python type to SpecQL type

        Returns (specql_type, required)
        """
        # Remove Optional wrapper
        required = True
        if type_str.startswith('Optional['):
            type_str = type_str[9:-1]
            required = False

        # Type mapping
        normalized = self.type_mapping.get(type_str, 'text')

        return normalized, required

    def _build_type_mapping(self) -> Dict[str, str]:
        """Build Python → SpecQL type mapping"""
        return {
            'str': 'text',
            'int': 'integer',
            'float': 'float',
            'bool': 'boolean',
            'date': 'date',
            'datetime': 'timestamp',
            'Decimal': 'decimal',
            'UUID': 'uuid',
            'dict': 'json',
            'Dict': 'json',
            'list': 'list',
            'List': 'list',
            'Any': 'json',
        }

    def _extract_default_value(self, node: ast.expr) -> Any:
        """Extract default value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return []
        elif isinstance(node, ast.Dict):
            return {}
        else:
            return None

    def _parse_methods(self, class_def: ast.ClassDef) -> List[ParsedMethod]:
        """Parse all methods in class"""
        methods = []

        for node in class_def.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip magic methods and private methods
                if node.name.startswith('__') or node.name.startswith('_'):
                    continue

                method = ParsedMethod(
                    method_name=node.name,
                    parameters=self._parse_function_parameters(node),
                    return_type=self._parse_return_type(node),
                    body_lines=self._extract_body_lines(node),
                    decorators=self._parse_function_decorators(node),
                    docstring=ast.get_docstring(node),
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    is_classmethod='@classmethod' in [d for d in self._parse_function_decorators(node)],
                    is_staticmethod='@staticmethod' in [d for d in self._parse_function_decorators(node)],
                    metadata={
                        "line_number": node.lineno,
                    }
                )
                methods.append(method)

        return methods

    def _parse_function_parameters(self, func_def) -> List[Dict[str, str]]:
        """Parse function parameters"""
        params = []

        for arg in func_def.args.args:
            # Skip 'self' and 'cls'
            if arg.arg in ['self', 'cls']:
                continue

            param_type = 'Any'
            if arg.annotation:
                param_type = ast.unparse(arg.annotation)

            params.append({
                'name': arg.arg,
                'type': param_type,
            })

        return params

    def _parse_return_type(self, func_def) -> Optional[str]:
        """Parse return type annotation"""
        if func_def.returns:
            return ast.unparse(func_def.returns)
        return None

    def _extract_body_lines(self, func_def) -> List[str]:
        """Extract function body as source lines"""
        body_lines = []

        for node in func_def.body:
            try:
                line = ast.unparse(node)
                body_lines.append(line)
            except Exception:
                continue

        return body_lines

    def _parse_function_decorators(self, func_def) -> List[str]:
        """Parse function decorators"""
        decorators = []

        for decorator in func_def.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(f"@{decorator.id}")
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(f"@{decorator.func.id}")

        return decorators

    def _parse_class_decorators(self, class_def: ast.ClassDef) -> List[str]:
        """Parse class decorators"""
        decorators = []

        for decorator in class_def.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(f"@{decorator.id}")
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(f"@{decorator.func.id}")

        return decorators

    def _parse_inheritance(self, class_def: ast.ClassDef) -> List[str]:
        """Parse base classes"""
        bases = []

        for base in class_def.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        return bases