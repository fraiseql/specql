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


@dataclass
class ParsedEntity:
    """Represents a parsed JPA entity"""

    name: str
    fields: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


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

    def parse_entity_from_code(self, code: str) -> "ParsedEntity":
        """Parse complete entity from Java code"""
        fields = self.extract_entity_fields_from_code(code)

        # Extract entity name from class declaration
        class_match = re.search(r"public\s+class\s+(\w+)", code)
        entity_name = class_match.group(1) if class_match else "Unknown"

        # Extract inheritance metadata from class level
        inheritance_info = self.entity_mapper._extract_inheritance_metadata(code)
        metadata = None
        if inheritance_info:
            specql_inheritance = self.entity_mapper._map_inheritance_to_specql(inheritance_info)
            metadata = specql_inheritance["_metadata"]

            # Add discriminator field if present
            if "discriminator_field" in specql_inheritance:
                fields.append(specql_inheritance["discriminator_field"])

        # Extract composite key information
        composite_key_info = self.entity_mapper._extract_composite_key(code)
        if composite_key_info:
            if composite_key_info["type"] == "id_class":
                # Add multiple ID fields
                for field_info in composite_key_info["composite_fields"]:
                    fields.append(
                        {
                            "name": self.entity_mapper._camel_to_snake(field_info["name"]),
                            "java_type": field_info["type"],
                            "type": self.entity_mapper._java_type_to_specql(
                                field_info["type"], False
                            ),
                            "nullable": False,  # Primary keys are not nullable
                            "is_relationship": False,
                            "is_primary_key_component": True,
                            "composite_key": composite_key_info["id_class"],
                        }
                    )
            elif composite_key_info["type"] == "embedded_id":
                # Add embedded ID field
                fields.append(
                    {
                        "name": self.entity_mapper._camel_to_snake(composite_key_info["id_field"]),
                        "java_type": composite_key_info["id_class"],
                        "type": "composite",
                        "nullable": False,  # Primary keys are not nullable
                        "is_relationship": False,
                        "composite_key": composite_key_info["id_class"],
                        "note": "Composite primary key - expand embedded fields",
                    }
                )

        return ParsedEntity(name=entity_name, fields=fields, metadata=metadata)

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

        # Check if this entity has composite keys
        has_composite_key = self._extract_composite_key(code) is not None

        # Extract embedded fields first
        embedded_fields = self._extract_embedded_fields(code)
        fields.extend(embedded_fields)

        # Find all field declarations
        field_pattern = r"private\s+(\w+(?:<\w+(?:<\w+>)?>)?)\s+(\w+)\s*;"

        for match in re.finditer(field_pattern, code):
            java_type = match.group(1)
            field_name = match.group(2)

            # Skip @Id fields if entity has composite key (they'll be added separately)
            # Look for @Id annotation immediately before this field
            before_field = code[: match.start()]
            lines_before = before_field.split("\n")[-3:]  # Last 3 lines
            has_id_annotation = any("@Id" in line for line in lines_before)
            if has_id_annotation and has_composite_key:
                continue

            # Skip simple @Id fields
            if field_name == "id":
                continue

            # Skip embedded fields (already processed)
            if any(f["name"].startswith(f"{field_name}_") for f in embedded_fields):
                continue

            # Get the field block including annotations
            # Look for annotations in the 10 lines before the field
            before_match = code[max(0, match.start() - 500) : match.start()]
            lines_before = before_match.split("\n")[-10:]  # last 10 lines

            annotation_lines = []
            in_annotation_block = False
            for line in reversed(lines_before):
                stripped = line.strip()
                if stripped.startswith("@"):
                    annotation_lines.insert(0, line)
                    in_annotation_block = True
                elif in_annotation_block and (
                    stripped == ""
                    or stripped.startswith("//")
                    or stripped.startswith("/*")
                    or stripped.endswith(",")
                    or stripped.endswith("(")
                ):
                    # Continue through empty lines, comments, and continuation lines
                    continue
                elif in_annotation_block and stripped and "private " in stripped:
                    # Stop at other field declarations
                    break
                elif in_annotation_block:
                    # Stop at other significant code
                    break

            field_block = "\n".join(annotation_lines) + "\n" + match.group(0)

            # Check if it's a relationship
            relationship_info = self._extract_relationship_annotations(field_block)

            # If it's a relationship, map it appropriately
            if relationship_info:
                field_info = self._map_relationship_field(
                    {"field_name": field_name, "java_type": java_type, **relationship_info}
                )
                fields.append(field_info)
                continue

            # Skip @Embedded fields (already processed)
            if "@Embedded" in field_block:
                continue

            # Check for @Convert annotation
            converter_info = self._extract_converter_annotation(field_block)
            if converter_info:
                specql_type = converter_info["specql_type"]
                nullable = True  # Custom types typically nullable
            else:
                # Check for @Column annotation
                nullable = True
                if "@Column" in field_block:
                    nullable_match = re.search(r"nullable\s*=\s*(false|true)", field_block)
                    if nullable_match:
                        nullable = nullable_match.group(1) == "true"

                # Map Java type to SpecQL type
                specql_type = self._java_type_to_specql(java_type, False)

            fields.append(
                {
                    "name": self._camel_to_snake(field_name),
                    "java_type": java_type,
                    "type": specql_type,
                    "nullable": nullable,
                    "is_relationship": False,
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

    def _extract_relationship_annotations(self, field_block: str) -> Optional[Dict[str, Any]]:
        """
        Extract JPA relationship metadata from field annotations

        Patterns to detect:
        - @OneToMany(mappedBy="contact", cascade=CascadeType.ALL)
        - @ManyToOne(fetch=FetchType.LAZY)
        - @JoinColumn(name="company_id")
        """
        relationship_patterns = {
            "one_to_many": r"@OneToMany(?:\s*\(([^)]*)\))?",
            "many_to_one": r"@ManyToOne(?:\s*\(([^)]*)\))?",
            "one_to_one": r"@OneToOne(?:\s*\(([^)]*)\))?",
            "many_to_many": r"@ManyToMany(?:\s*\(([^)]*)\))?",
        }

        for rel_type, pattern in relationship_patterns.items():
            match = re.search(pattern, field_block)
            if match:
                params = match.group(1) if match.groups() and match.group(1) else ""
                return {
                    "relationship_type": rel_type,
                    "mapped_by": self._extract_param(params, "mappedBy"),
                    "cascade": self._extract_param(params, "cascade"),
                    "fetch": self._extract_param(params, "fetch"),
                    "join_column": self._extract_join_column(field_block),
                    "target_entity": self._extract_target_entity(field_block, params),
                }

        return None

    def _map_inheritance_to_specql(self, inheritance_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map JPA inheritance to SpecQL entity metadata

        SpecQL doesn't have native inheritance, but we can:
        1. Flatten fields from parent
        2. Add discriminator as enum field
        3. Document inheritance in _metadata
        """
        specql_additions = {}

        if inheritance_info.get("discriminator_column"):
            # Add discriminator as enum field
            specql_additions["discriminator_field"] = {
                "name": inheritance_info["discriminator_column"],
                "type": "enum",
                "values": [inheritance_info["discriminator_value"]]
                if inheritance_info.get("discriminator_value")
                else [],
                "description": f"Discriminator for {inheritance_info['strategy']} inheritance",
            }

        specql_additions["_metadata"] = {
            "jpa_inheritance": inheritance_info,
            "note": "Inheritance flattened - check parent entity for base fields",
        }

        return specql_additions

    def _extract_embedded_fields(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract @Embedded fields and flatten them

        Strategy:
        1. Find @Embedded annotation
        2. Extract embedded class name
        3. Parse embedded class definition
        4. Flatten embedded fields with prefix (address_street, address_city)
        """
        embedded_fields = []

        # Find all @Embedded fields
        embedded_pattern = r"@Embedded\s+private\s+(\w+)\s+(\w+)\s*;"
        for match in re.finditer(embedded_pattern, code):
            embedded_class = match.group(1)
            field_name = match.group(2)

            # Find embedded class definition
            embedded_class_pattern = (
                rf"@Embeddable\s+public\s+class\s+{embedded_class}\s*\{{([^}}]+)\}}"
            )
            embedded_def = re.search(embedded_class_pattern, code, re.DOTALL)

            if embedded_def:
                # Parse embedded fields
                embedded_body = embedded_def.group(1)
                embedded_simple_fields = self._extract_simple_fields(embedded_body)

                # Flatten with prefix
                for ef in embedded_simple_fields:
                    flattened_field = {
                        "name": f"{field_name}_{ef['name']}",
                        "java_type": ef["java_type"],
                        "type": ef["type"],
                        "nullable": ef["nullable"],
                        "is_relationship": False,
                        "embedded_from": embedded_class,
                    }
                    embedded_fields.append(flattened_field)

        return embedded_fields

    def _extract_simple_fields(self, code_block: str) -> List[Dict[str, Any]]:
        """Extract simple (non-relationship) fields from a code block"""
        fields = []

        # Find all field declarations (excluding @Id and relationships)
        field_pattern = r"private\s+(\w+(?:<\w+>)?)\s+(\w+)\s*;"

        for match in re.finditer(field_pattern, code_block):
            java_type = match.group(1)
            field_name = match.group(2)

            # Skip if it's a relationship or ID
            if (
                "@Id" in code_block
                or "@ManyToOne" in code_block
                or "@OneToOne" in code_block
                or "@OneToMany" in code_block
                or "@ManyToMany" in code_block
            ):
                continue

            # Check nullable
            nullable = True
            if "@Column" in code_block:
                nullable_match = re.search(r"nullable\s*=\s*(false|true)", code_block)
                if nullable_match:
                    nullable = nullable_match.group(1) == "true"

            # Map Java type to SpecQL type
            specql_type = self._java_type_to_specql(java_type, False)

            fields.append(
                {
                    "name": self._camel_to_snake(field_name),
                    "java_type": java_type,
                    "type": specql_type,
                    "nullable": nullable,
                }
            )

        return fields

    def _extract_param(self, params_str: str, param_name: str) -> Optional[str]:
        """Extract parameter value from annotation parameters string"""
        pattern = rf"{param_name}\s*=\s*([^,\s)]+)"
        match = re.search(pattern, params_str)
        if match:
            value = match.group(1).strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            return value
        return None

    def _extract_join_column(self, field_block: str) -> Optional[str]:
        """Extract @JoinColumn name"""
        join_column_pattern = r'@JoinColumn\s*\(\s*name\s*=\s*"([^"]+)"'
        match = re.search(join_column_pattern, field_block)
        return match.group(1) if match else None

    def _extract_target_entity(self, field_block: str, relationship_params: str) -> str:
        """
        Extract target entity from:
        1. Generic type: List<Contact> → Contact
        2. Field type: Company contact → Company
        3. targetEntity parameter: @OneToMany(targetEntity=Contact.class)
        """
        # Check for targetEntity parameter
        target_match = re.search(r"targetEntity\s*=\s*(\w+)\.class", relationship_params)
        if target_match:
            return target_match.group(1)

        # Extract from generic type
        generic_match = re.search(r"List<(\w+)>|Set<(\w+)>|Collection<(\w+)>", field_block)
        if generic_match:
            return generic_match.group(1) or generic_match.group(2) or generic_match.group(3)

        # Extract from field type
        type_match = re.search(r"private\s+(\w+)\s+\w+\s*;", field_block)
        if type_match:
            return type_match.group(1)

        return "Unknown"

    def _map_relationship_field(self, field_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map JPA relationship to SpecQL field

        Examples:
        - @ManyToOne → ref(Company) with is_foreign_key=True
        - @OneToMany → ref(Contact) with is_list=True
        - @OneToOne → ref(User) with is_foreign_key=True
        - @ManyToMany → ref(Tag) with is_list=True, is_many_to_many=True
        """
        rel_type = field_info["relationship_type"]
        target_entity = field_info["target_entity"]

        # Detect bidirectional relationship
        bidirectional_info = self._detect_bidirectional_relationship(field_info)

        specql_field = {
            "name": self._camel_to_snake(field_info["field_name"]),
            "java_type": field_info["java_type"],
            "type": f"ref({target_entity})",
            "nullable": True,  # Relationships are typically nullable
            "is_relationship": True,
            "relationship_metadata": {
                "type": rel_type,
                "target": target_entity,
                "mapped_by": field_info.get("mapped_by"),
                "cascade": field_info.get("cascade"),
                "fetch": field_info.get("fetch"),
                **bidirectional_info,
            },
        }

        # Set SpecQL-specific flags
        if rel_type in ["one_to_many", "many_to_many"]:
            specql_field["is_list"] = True

        if rel_type in ["many_to_one", "one_to_one"]:
            specql_field["is_foreign_key"] = True

        if rel_type == "many_to_many":
            specql_field["is_many_to_many"] = True

        return specql_field

    def _detect_bidirectional_relationship(
        self, relationship_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect bidirectional relationships via mappedBy

        If mappedBy is present, this is the INVERSE side
        If JoinColumn is present, this is the OWNING side
        """
        if relationship_info.get("mapped_by"):
            return {
                "is_bidirectional": True,
                "side": "inverse",
                "owned_by": relationship_info["mapped_by"],
            }
        elif relationship_info.get("join_column"):
            return {
                "is_bidirectional": True,
                "side": "owning",
                "foreign_key": relationship_info["join_column"],
            }
        else:
            return {
                "is_bidirectional": False,
                "side": "unidirectional",
            }

    def _extract_converter_annotation(self, field_block: str) -> Optional[Dict[str, Any]]:
        """
        Extract @Convert annotation

        Strategy: Treat as custom type, map to 'text' or 'json' in SpecQL
        """
        converter_pattern = r"@Convert\s*\(\s*converter\s*=\s*(\w+)\.class\s*\)"
        match = re.search(converter_pattern, field_block)

        if match:
            return {
                "has_converter": True,
                "converter_class": match.group(1),
                "specql_type": "text",  # Default to text for custom types
                "note": f"Custom converter {match.group(1)} - review mapping",
            }

        return None

    def _extract_composite_key(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Extract composite primary key

        Two patterns:
        1. @IdClass - multiple @Id fields
        2. @EmbeddedId - single embedded ID field
        """
        # Check for @IdClass
        id_class_pattern = r"@IdClass\s*\(\s*(\w+)\.class\s*\)"
        id_class_match = re.search(id_class_pattern, code)

        if id_class_match:
            # Find all @Id fields
            id_fields = re.findall(r"@Id\s+private\s+(\w+)\s+(\w+)\s*;", code)
            return {
                "type": "id_class",
                "id_class": id_class_match.group(1),
                "composite_fields": [{"type": t, "name": n} for t, n in id_fields],
            }

        # Check for @EmbeddedId
        embedded_id_pattern = r"@EmbeddedId\s+private\s+(\w+)\s+(\w+)\s*;"
        embedded_id_match = re.search(embedded_id_pattern, code)

        if embedded_id_match:
            return {
                "type": "embedded_id",
                "id_class": embedded_id_match.group(1),
                "id_field": embedded_id_match.group(2),
            }

        return None

    def _extract_inheritance_metadata(self, class_block: str) -> Optional[Dict[str, Any]]:
        """
        Extract JPA inheritance strategy

        Returns:
        {
            'strategy': 'SINGLE_TABLE' | 'JOINED' | 'TABLE_PER_CLASS',
            'discriminator_column': 'contact_type',
            'discriminator_type': 'STRING',
            'discriminator_value': 'LEAD',
            'parent_entity': 'Contact',
        }
        """
        inheritance_pattern = r"@Inheritance\s*\(\s*strategy\s*=\s*InheritanceType\.(\w+)\s*\)"
        match = re.search(inheritance_pattern, class_block)

        if match:
            strategy = match.group(1)

            # Extract discriminator column
            disc_col_pattern = r'@DiscriminatorColumn\s*\(\s*name\s*=\s*"([^"]+)"(?:\s*,\s*discriminatorType\s*=\s*DiscriminatorType\.(\w+))?\s*\)'
            disc_col_match = re.search(disc_col_pattern, class_block)

            # Extract discriminator value
            disc_val_pattern = r'@DiscriminatorValue\s*\(\s*"([^"]+)"\s*\)'
            disc_val_match = re.search(disc_val_pattern, class_block)

            # Extract parent class
            extends_pattern = r"class\s+\w+\s+extends\s+(\w+)"
            parent_match = re.search(extends_pattern, class_block)

            return {
                "strategy": strategy,
                "discriminator_column": disc_col_match.group(1) if disc_col_match else None,
                "discriminator_type": disc_col_match.group(2)
                if disc_col_match and disc_col_match.group(2)
                else "STRING",
                "discriminator_value": disc_val_match.group(1) if disc_val_match else None,
                "parent_entity": parent_match.group(1) if parent_match else None,
            }

        return None
