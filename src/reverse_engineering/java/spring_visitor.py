"""
Spring Boot Annotation Visitor

Extracts Spring Boot annotations from Java AST to identify:
- Services (@Service)
- Controllers (@Controller, @RestController)
- Repositories (@Repository)
- Components (@Component)
- Configuration classes (@Configuration)
- MVC endpoints (@RequestMapping, @GetMapping, etc.)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class SpringMethod:
    """Represents a method in a Spring component"""

    name: str
    return_type: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    http_method: Optional[str] = None
    path: Optional[str] = None
    produces: Optional[str] = None
    consumes: Optional[str] = None


@dataclass
class SpringComponent:
    """Represents a Spring component (Service, Controller, Repository, etc.)"""

    class_name: str
    component_type: (
        str  # 'service', 'controller', 'repository', 'component', 'configuration'
    )
    package_name: str
    methods: List[SpringMethod] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    base_path: Optional[str] = None  # For controllers


class SpringAnnotationVisitor:
    """Visit Java AST and extract Spring Boot annotations"""

    def __init__(self, compilation_unit):
        """
        Initialize visitor

        Args:
            compilation_unit: Eclipse JDT CompilationUnit or MockCompilationUnit
        """
        self.cu = compilation_unit
        self.components: List[SpringComponent] = []

    def visit(self) -> List[SpringComponent]:
        """Visit AST and extract Spring components"""
        # Get all types in compilation unit
        types = self.cu.types()

        for type_decl in types:
            if self._is_spring_component(type_decl):
                component = self._extract_component(type_decl)
                self.components.append(component)

        return self.components

    def _is_spring_component(self, type_decl) -> bool:
        """Check if type is a Spring component"""
        modifiers = type_decl.modifiers()

        for modifier in modifiers:
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                # Check for Spring Boot stereotype annotations
                if annotation_name in (
                    "Service",
                    "org.springframework.stereotype.Service",
                    "Controller",
                    "org.springframework.stereotype.Controller",
                    "RestController",
                    "org.springframework.web.bind.annotation.RestController",
                    "Repository",
                    "org.springframework.stereotype.Repository",
                    "Component",
                    "org.springframework.stereotype.Component",
                    "Configuration",
                    "org.springframework.context.annotation.Configuration",
                ):
                    return True

        # Also check if it's a repository interface (extends Repository/JpaRepository/etc.)
        if self._is_repository_interface(type_decl):
            return True

        return False

    def _is_repository_interface(self, type_decl) -> bool:
        """Check if type is a repository interface"""
        # Check if it extends repository interfaces
        for super_interface in type_decl.superInterfaceTypes():
            interface_name = super_interface.toString()
            if any(
                repo in interface_name
                for repo in [
                    "Repository",
                    "JpaRepository",
                    "CrudRepository",
                    "PagingAndSortingRepository",
                    "MongoRepository",
                ]
            ):
                return True
        return False

    def _extract_component(self, type_decl) -> SpringComponent:
        """Extract component information from type declaration"""
        class_name = type_decl.getName().getIdentifier()
        package_name = self._extract_package_name()

        # Determine component type
        component_type = self._get_component_type(type_decl)

        # Extract annotations
        annotations = []
        base_path = None

        for modifier in type_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                annotations.append(annotation_name)

                # Extract base path for controllers
                if component_type in ("controller", "rest_controller"):
                    if annotation_name in (
                        "RequestMapping",
                        "org.springframework.web.bind.annotation.RequestMapping",
                    ):
                        base_path = self._extract_request_mapping_path(modifier)

        # Create component
        component = SpringComponent(
            class_name=class_name,
            component_type=component_type,
            package_name=package_name,
            annotations=annotations,
            base_path=base_path,
        )

        # Extract methods
        for body_decl in type_decl.bodyDeclarations():
            # Check if it's a method declaration
            node_type = body_decl.getNodeType()
            if node_type == "METHOD_DECLARATION" or (
                hasattr(body_decl, "METHOD_DECLARATION")
                and node_type == body_decl.METHOD_DECLARATION
            ):
                spring_method = self._extract_method(body_decl, component_type)
                if spring_method:
                    component.methods.append(spring_method)

        return component

    def _get_component_type(self, type_decl) -> str:
        """Determine the component type from annotations"""
        modifiers = type_decl.modifiers()

        for modifier in modifiers:
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()

                if annotation_name in (
                    "Service",
                    "org.springframework.stereotype.Service",
                ):
                    return "service"
                elif annotation_name in (
                    "RestController",
                    "org.springframework.web.bind.annotation.RestController",
                ):
                    return "rest_controller"
                elif annotation_name in (
                    "Controller",
                    "org.springframework.stereotype.Controller",
                ):
                    return "controller"
                elif annotation_name in (
                    "Repository",
                    "org.springframework.stereotype.Repository",
                ):
                    return "repository"
                elif annotation_name in (
                    "Configuration",
                    "org.springframework.context.annotation.Configuration",
                ):
                    return "configuration"
                elif annotation_name in (
                    "Component",
                    "org.springframework.stereotype.Component",
                ):
                    return "component"

        # Check for repository interface
        if self._is_repository_interface(type_decl):
            return "repository"

        return "unknown"

    def _extract_method(
        self, method_decl, component_type: str = "unknown"
    ) -> Optional[SpringMethod]:
        """Extract method information from method declaration"""
        method_name = method_decl.getName().getIdentifier()
        return_type = self._extract_method_return_type(method_decl)

        # Extract parameters
        parameters = []
        for param in self._extract_method_parameters(method_decl):
            param_info = {
                "name": param.getName().getIdentifier(),
                "type": param.getType().toString(),
            }
            parameters.append(param_info)

        # Check for Spring annotations
        annotations = []
        http_method = None
        path = None
        produces = None
        consumes = None

        has_spring_annotation = False

        for modifier in method_decl.modifiers():
            if modifier.isAnnotation():
                annotation_name = modifier.getTypeName().getFullyQualifiedName()
                annotations.append(annotation_name)

                # Check for HTTP method annotations
                if annotation_name in (
                    "GetMapping",
                    "org.springframework.web.bind.annotation.GetMapping",
                ):
                    http_method = "GET"
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True
                elif annotation_name in (
                    "PostMapping",
                    "org.springframework.web.bind.annotation.PostMapping",
                ):
                    http_method = "POST"
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True
                elif annotation_name in (
                    "PutMapping",
                    "org.springframework.web.bind.annotation.PutMapping",
                ):
                    http_method = "PUT"
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True
                elif annotation_name in (
                    "DeleteMapping",
                    "org.springframework.web.bind.annotation.DeleteMapping",
                ):
                    http_method = "DELETE"
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True
                elif annotation_name in (
                    "PatchMapping",
                    "org.springframework.web.bind.annotation.PatchMapping",
                ):
                    http_method = "PATCH"
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True
                elif annotation_name in (
                    "RequestMapping",
                    "org.springframework.web.bind.annotation.RequestMapping",
                ):
                    http_method = self._extract_request_method(modifier)
                    path = self._extract_mapping_path(modifier)
                    has_spring_annotation = True

                # Check for other Spring annotations
                elif annotation_name in (
                    "Transactional",
                    "org.springframework.transaction.annotation.Transactional",
                    "Cacheable",
                    "org.springframework.cache.annotation.Cacheable",
                    "Async",
                    "org.springframework.scheduling.annotation.Async",
                    "Bean",
                    "org.springframework.context.annotation.Bean",
                    "Query",
                    "org.springframework.data.jpa.repository.Query",
                ):
                    has_spring_annotation = True

        # For repository interfaces, also check for Spring Data method patterns
        if self._is_repository_method(method_name):
            has_spring_annotation = True

        # For controllers and services, include all public methods
        if component_type in (
            "rest_controller",
            "controller",
            "service",
            "configuration",
        ):
            has_spring_annotation = True

        # Only return method if it has Spring annotations or belongs to a Spring component
        if not has_spring_annotation:
            return None

        return SpringMethod(
            name=method_name,
            return_type=return_type,
            parameters=parameters,
            annotations=annotations,
            http_method=http_method,
            path=path,
            produces=produces,
            consumes=consumes,
        )

    def _is_repository_method(self, method_name: str) -> bool:
        """Check if method name follows Spring Data repository patterns"""
        repository_patterns = [
            "findBy",
            "findAllBy",
            "findFirstBy",
            "findTopBy",
            "save",
            "saveAll",
            "delete",
            "deleteBy",
            "deleteAll",
            "deleteAllBy",
            "existsBy",
            "countBy",
            "findAndModify",
            "findAndReplace",
            "findAndDelete",
        ]

        return any(method_name.startswith(pattern) for pattern in repository_patterns)

    def _extract_package_name(self) -> str:
        """Extract package name from compilation unit"""
        if hasattr(self.cu, "getPackage") and self.cu.getPackage():
            return self.cu.getPackage().getName().getFullyQualifiedName()
        # For mock implementation, try to extract from source
        if hasattr(self.cu, "source"):
            import re

            package_match = re.search(r"package\s+([^\s;]+)", self.cu.source)
            if package_match:
                return package_match.group(1)
        return ""

    def _extract_method_return_type(self, method_decl) -> str:
        """Extract method return type safely"""
        if hasattr(method_decl, "getReturnType2") and method_decl.getReturnType2():
            return method_decl.getReturnType2().toString()
        return "void"

    def _extract_method_parameters(self, method_decl) -> list:
        """Extract method parameters safely"""
        if hasattr(method_decl, "parameters"):
            return method_decl.parameters()
        return []

    def _extract_request_mapping_path(self, annotation) -> Optional[str]:
        """Extract path from @RequestMapping annotation"""
        return self._extract_mapping_path(annotation)

    def _extract_mapping_path(self, annotation) -> Optional[str]:
        """Extract path from mapping annotation"""
        if annotation.isSingleMemberAnnotation():
            return self._get_annotation_string_value(annotation.getValue())
        elif annotation.isNormalAnnotation():
            for pair in annotation.values():
                key = pair.getName().getIdentifier()
                if key in ("value", "path"):
                    return self._get_annotation_string_value(pair.getValue())
        return None

    def _extract_request_method(self, annotation) -> Optional[str]:
        """Extract HTTP method from @RequestMapping annotation"""
        if annotation.isNormalAnnotation():
            for pair in annotation.values():
                key = pair.getName().getIdentifier()
                if key == "method":
                    value = self._get_annotation_value(pair.getValue())
                    if value and "." in str(value):
                        # Extract method name from RequestMethod.GET
                        return str(value).split(".")[-1]
        return None

    def _get_annotation_string_value(self, value_node) -> Optional[str]:
        """Extract string value from annotation"""
        if hasattr(value_node, "getNodeType"):
            if value_node.getNodeType() == value_node.STRING_LITERAL:
                return value_node.getLiteralValue()

        # Fallback for mock implementation
        if hasattr(value_node, "literal_value"):
            return value_node.literal_value

        return None

    def _get_annotation_value(self, value_node):
        """Extract value from annotation (generic)"""
        # Handle string literals
        if hasattr(value_node, "getNodeType"):
            if value_node.getNodeType() == value_node.STRING_LITERAL:
                return value_node.getLiteralValue()

            # Handle qualified names (e.g., RequestMethod.GET)
            if value_node.getNodeType() == value_node.QUALIFIED_NAME:
                return value_node.getFullyQualifiedName()

        # Fallback for mock implementation
        if hasattr(value_node, "literal_value"):
            return value_node.literal_value

        return None
