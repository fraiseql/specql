"""
Java Action Parser - Extract actions from Java Spring Boot code

Supports:
- Spring Boot controllers (@RestController, @RequestMapping, @GetMapping, etc.)
- JPA entities (@Entity, @Table, @Column)
- Spring Data repositories (CrudRepository, JpaRepository)

Uses regex-based parsing (Java is verbose, full AST parsing is complex).
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class JavaAction:
    """Represents an action extracted from Java code"""

    name: str
    type: str  # create, read, update, delete, custom
    http_method: Optional[str] = None
    path: Optional[str] = None
    parameters: Optional[List[str]] = None
    has_request_body: bool = False
    query_params: Optional[List[str]] = None
    has_custom_query: bool = False
    framework: str = "spring"
    confidence: float = 0.0

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.query_params is None:
            self.query_params = []


@dataclass
class JavaField:
    """Represents a field extracted from JPA entity"""

    name: str
    java_type: str
    specql_type: str
    nullable: bool = True
    is_relationship: bool = False


class JavaActionParser:
    """
    Extract actions from Java Spring Boot code.

    Usage:
        parser = JavaActionParser()
        actions = parser.extract_actions(Path("ContactController.java"))
    """

    def __init__(self):
        self.action_mapper = JavaActionMapper()
        self.entity_mapper = JavaEntityMapper()

    def extract_actions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract actions from Java file"""
        with open(file_path) as f:
            code = f.read()

        return self.extract_actions_from_code(code)

    def extract_actions_from_code(self, code: str) -> List[Dict[str, Any]]:
        """Extract actions from Java code string"""
        actions = []

        # Check if it's a controller
        if "@RestController" in code or "@Controller" in code:
            actions.extend(self._extract_from_controller(code))

        # Check if it's a repository
        elif "Repository" in code and "extends" in code:
            actions.extend(self._extract_from_repository(code))

        return [self._action_to_dict(a) for a in actions]

    def _extract_from_controller(self, code: str) -> List[JavaAction]:
        """Extract actions from Spring Boot controller"""
        actions = []

        # Extract class-level @RequestMapping path
        class_path = self._extract_class_request_mapping(code)

        # Find all method mappings
        mapping_patterns = [
            (r'@GetMapping(?:\("([^"]*)"\))?', "GET"),
            (r'@PostMapping(?:\("([^"]*)"\))?', "POST"),
            (r'@PutMapping(?:\("([^"]*)"\))?', "PUT"),
            (r'@PatchMapping(?:\("([^"]*)"\))?', "PATCH"),
            (r'@DeleteMapping(?:\("([^"]*)"\))?', "DELETE"),
            (r'@RequestMapping\(value\s*=\s*"([^"]*)".*method\s*=\s*RequestMethod\.(\w+)', None),
        ]

        # Collect all matches with their positions
        all_matches = []
        for pattern, default_method in mapping_patterns:
            for match in re.finditer(pattern, code):
                all_matches.append((match, default_method))

        # Sort matches by position in code
        all_matches.sort(key=lambda x: x[0].start())

        for match, default_method in all_matches:
            # Find method definition after this annotation
            method_start = match.end()
            method_match = re.search(
                r"public\s+\S+\s+(\w+)\s*\(([^)]*)\)", code[method_start : method_start + 500]
            )

            if method_match:
                method_name = method_match.group(1)
                method_params = method_match.group(2)

                # Extract path
                if default_method:
                    # @GetMapping, @PostMapping, etc.
                    method_path = (
                        match.group(1) if len(match.groups()) > 0 and match.group(1) else ""
                    )
                    http_method = default_method
                else:
                    # @RequestMapping with method parameter
                    method_path = match.group(1)
                    http_method = match.group(2).upper()

                # Combine class path and method path
                full_path = self._combine_paths(class_path, method_path)

                # Detect CRUD type
                action_type = self.action_mapper.http_method_to_crud(http_method)

                # Extract parameters
                params = self._extract_parameters(method_params)
                has_request_body = "@RequestBody" in method_params
                query_params = self._extract_query_params(method_params)

                action = JavaAction(
                    name=method_name,
                    type=action_type,
                    http_method=http_method,
                    path=full_path,
                    parameters=params,
                    has_request_body=has_request_body,
                    query_params=query_params,
                    framework="spring",
                    confidence=0.95,
                )
                actions.append(action)

        logger.debug(f"Total actions found: {len(actions)}")
        return actions

    def _extract_from_repository(self, code: str) -> List[JavaAction]:
        """Extract actions from Spring Data repository"""
        actions = []

        # Detect base repository type
        if "CrudRepository" in code or "JpaRepository" in code:
            # Add standard CRUD methods
            actions.extend(
                [
                    JavaAction("save", "create", confidence=0.90),
                    JavaAction("findById", "read", confidence=0.90),
                    JavaAction("findAll", "read", confidence=0.90),
                    JavaAction("deleteById", "delete", confidence=0.90),
                ]
            )

        # Find custom query methods
        method_pattern = r"(List<\w+>|\w+)\s+(\w+)\s*\(([^)]*)\)"
        for match in re.finditer(method_pattern, code):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)

            # Skip if it's in interface declaration
            if "interface" in code[: match.start()].split("\n")[-1]:
                continue

            # Detect action type from method name
            action_type = self.action_mapper.detect_crud_from_name(method_name)
            if action_type:
                has_custom_query = "@Query" in code[: match.start()][-200:]
                action = JavaAction(
                    name=method_name,
                    type=action_type,
                    parameters=self._extract_parameters(params),
                    has_custom_query=has_custom_query,
                    framework="spring_data",
                    confidence=0.85,
                )
                actions.append(action)

        return actions

    def _extract_class_request_mapping(self, code: str) -> str:
        """Extract class-level @RequestMapping path"""
        match = re.search(r'@RequestMapping\("([^"]*)"\)', code)
        return match.group(1) if match else ""

    def _combine_paths(self, class_path: str, method_path: str) -> str:
        """Combine class and method paths"""
        if not class_path:
            return method_path
        if not method_path:
            return class_path
        # Ensure single slash between paths
        return f"{class_path.rstrip('/')}/{method_path.lstrip('/')}"

    def _extract_parameters(self, params_str: str) -> List[str]:
        """Extract parameter names from method signature"""
        if not params_str.strip():
            return []

        params = []
        # Split by comma, extract parameter name (last word before comma/end)
        for param in params_str.split(","):
            # Remove annotations like @PathVariable, @RequestParam
            param = re.sub(r"@\w+(\([^)]*\))?\s*", "", param)
            # Extract last word (parameter name)
            words = param.strip().split()
            if words:
                params.append(words[-1])

        return params

    def _extract_query_params(self, params_str: str) -> List[str]:
        """Extract @RequestParam parameter names"""
        query_params = []
        for match in re.finditer(r"@RequestParam.*?(\w+)\s*$", params_str):
            query_params.append(match.group(1))
        return query_params

    def extract_entity_fields_from_code(self, code: str) -> List[Dict[str, Any]]:
        """Extract fields from JPA entity"""
        return self.entity_mapper.extract_fields(code)

    def extract_repository_actions_from_code(self, code: str) -> List[Dict[str, Any]]:
        """Extract actions from repository interface"""
        actions = self._extract_from_repository(code)
        return [self._action_to_dict(a) for a in actions]

    def _action_to_dict(self, action: JavaAction) -> Dict[str, Any]:
        """Convert JavaAction to dict"""
        result = {
            "name": action.name,
            "type": action.type,
            "framework": action.framework,
            "confidence": action.confidence,
        }

        if action.http_method:
            result["http_method"] = action.http_method
        if action.path:
            result["path"] = action.path
        if action.parameters:
            result["parameters"] = action.parameters
        if action.has_request_body:
            result["has_request_body"] = action.has_request_body
        if action.query_params:
            result["query_params"] = action.query_params
        if action.has_custom_query:
            result["has_custom_query"] = action.has_custom_query

        return result


class JavaActionMapper:
    """Map Java constructs to SpecQL CRUD actions"""

    def detect_crud_from_name(self, name: str) -> Optional[str]:
        """Detect CRUD type from method name"""
        name_lower = name.lower()

        # CREATE patterns
        if any(kw in name_lower for kw in ["create", "save", "insert", "add", "persist"]):
            return "create"

        # READ patterns
        if any(
            kw in name_lower
            for kw in ["find", "get", "read", "fetch", "retrieve", "list", "search", "query"]
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


class JavaEntityMapper:
    """Extract entity fields from JPA entities"""

    def extract_fields(self, code: str) -> List[Dict[str, Any]]:
        """Extract fields from JPA entity class"""
        fields = []

        # Find all field declarations with their annotations
        field_pattern = r"((?:@\w+(?:\([^)]*\))?[\s\n]*)*)private\s+(\w+(?:<\w+>)?)\s+(\w+)\s*;"

        for match in re.finditer(field_pattern, code):
            annotations = match.group(1)
            java_type = match.group(2)
            field_name = match.group(3)

            # Skip if marked with @Id (primary key)
            if "@Id" in annotations or field_name == "id":
                continue

            # Check if it's a relationship
            is_relationship = (
                "@ManyToOne" in annotations
                or "@OneToOne" in annotations
                or "@OneToMany" in annotations
                or "@ManyToMany" in annotations
            )

            # Skip collection relationships (List, Set, etc.)
            if is_relationship and (
                "List" in java_type or "Set" in java_type or "Collection" in java_type
            ):
                continue

            # Check nullable
            nullable = True
            if "@Column" in annotations:
                nullable_match = re.search(r"nullable\s*=\s*(false|true)", annotations)
                if nullable_match:
                    nullable = nullable_match.group(1) == "true"

            # Map Java type to SpecQL type
            specql_type = self._java_type_to_specql(java_type, is_relationship)

            fields.append(
                {
                    "name": self._camel_to_snake(field_name),
                    "java_type": java_type,
                    "type": specql_type,
                    "nullable": nullable,
                    "is_relationship": is_relationship,
                }
            )

        return fields

    def _java_type_to_specql(self, java_type: str, is_relationship: bool) -> str:
        """Map Java type to SpecQL type"""
        if is_relationship:
            # Extract entity name from type
            entity_name = re.sub(r"<.*>", "", java_type)
            return f"ref({entity_name})"

        mapping = {
            "String": "text",
            "Integer": "integer",
            "Long": "integer",
            "int": "integer",
            "long": "integer",
            "Double": "decimal",
            "Float": "decimal",
            "double": "decimal",
            "float": "decimal",
            "Boolean": "boolean",
            "boolean": "boolean",
            "LocalDateTime": "timestamp",
            "LocalDate": "date",
            "UUID": "uuid",
        }

        return mapping.get(java_type, "text")

    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case"""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
