"""
Tests for Spring Boot Annotation Visitor
"""

from unittest.mock import Mock

from src.reverse_engineering.java.spring_visitor import (
    SpringAnnotationVisitor,
)


class TestSpringAnnotationVisitor:
    """Test Spring annotation visitor functionality"""

    def test_visit_spring_service(self):
        """Test visiting a Spring @Service class"""
        # Mock compilation unit with @Service annotation
        cu = Mock()
        type_decl = Mock()

        # Mock modifiers with @Service annotation
        modifier = Mock()
        modifier.isAnnotation.return_value = True
        annotation_type = Mock()
        annotation_type.getFullyQualifiedName.return_value = "Service"
        modifier.getTypeName.return_value = annotation_type
        modifier.isNormalAnnotation.return_value = True
        modifier.values.return_value = []

        type_decl.modifiers.return_value = [modifier]
        type_decl.getName.return_value = Mock()
        type_decl.getName.return_value.getIdentifier.return_value = "UserService"
        type_decl.bodyDeclarations.return_value = []

        cu.types.return_value = [type_decl]

        visitor = SpringAnnotationVisitor(cu)
        components = visitor.visit()

        assert len(components) == 1
        assert components[0].class_name == "UserService"
        assert components[0].component_type == "service"

    def test_visit_spring_controller(self):
        """Test visiting a Spring @RestController class"""
        cu = Mock()
        type_decl = Mock()

        # Mock @RestController annotation
        modifier = Mock()
        modifier.isAnnotation.return_value = True
        annotation_type = Mock()
        annotation_type.getFullyQualifiedName.return_value = "RestController"
        modifier.getTypeName.return_value = annotation_type

        # Mock @RequestMapping for base path
        request_mapping = Mock()
        request_mapping.isAnnotation.return_value = True
        rm_annotation_type = Mock()
        rm_annotation_type.getFullyQualifiedName.return_value = "RequestMapping"
        request_mapping.getTypeName.return_value = rm_annotation_type
        request_mapping.isNormalAnnotation.return_value = True
        request_mapping.values.return_value = []

        type_decl.modifiers.return_value = [modifier, request_mapping]
        type_decl.getName.return_value = Mock()
        type_decl.getName.return_value.getIdentifier.return_value = "UserController"
        type_decl.bodyDeclarations.return_value = []

        cu.types.return_value = [type_decl]

        visitor = SpringAnnotationVisitor(cu)
        components = visitor.visit()

        assert len(components) == 1
        assert components[0].class_name == "UserController"
        assert components[0].component_type == "rest_controller"

    def test_visit_repository_interface(self):
        """Test visiting a repository interface"""
        cu = Mock()
        type_decl = Mock()

        # Mock interface extending JpaRepository
        type_decl.modifiers.return_value = []
        type_decl.getName.return_value = Mock()
        type_decl.getName.return_value.getIdentifier.return_value = "UserRepository"

        # Mock super interfaces
        super_interface = Mock()
        super_interface.toString.return_value = "JpaRepository<User, Long>"
        type_decl.superInterfaceTypes.return_value = [super_interface]

        type_decl.bodyDeclarations.return_value = []

        cu.types.return_value = [type_decl]

        visitor = SpringAnnotationVisitor(cu)
        components = visitor.visit()

        assert len(components) == 1
        assert components[0].class_name == "UserRepository"
        assert components[0].component_type == "repository"

    def test_extract_controller_method(self):
        """Test extracting a controller method with @GetMapping"""
        cu = Mock()
        visitor = SpringAnnotationVisitor(cu)

        # Mock method declaration
        method_decl = Mock()
        method_decl.getName.return_value = Mock()
        method_decl.getName.return_value.getIdentifier.return_value = "getUser"
        method_decl.getReturnType2.return_value = Mock()
        method_decl.getReturnType2.return_value.toString.return_value = "User"
        method_decl.parameters.return_value = []

        # Mock @GetMapping annotation
        modifier = Mock()
        modifier.isAnnotation.return_value = True
        annotation_type = Mock()
        annotation_type.getFullyQualifiedName.return_value = "GetMapping"
        modifier.getTypeName.return_value = annotation_type

        method_decl.modifiers.return_value = [modifier]

        # Mock the visitor's _extract_mapping_path method
        visitor._extract_mapping_path = Mock(return_value="/users/{id}")

        method = visitor._extract_method(method_decl)

        assert method is not None
        assert method.name == "getUser"
        assert method.http_method == "GET"
        assert method.path == "/users/{id}"

    def test_extract_repository_method(self):
        """Test extracting a repository method"""
        cu = Mock()
        visitor = SpringAnnotationVisitor(cu)

        # Mock method declaration
        method_decl = Mock()
        method_decl.getName.return_value = Mock()
        method_decl.getName.return_value.getIdentifier.return_value = "findByEmail"
        method_decl.getReturnType2.return_value = Mock()
        method_decl.getReturnType2.return_value.toString.return_value = "User"
        method_decl.parameters.return_value = []

        # No annotations, but should be recognized as repository method
        method_decl.modifiers.return_value = []

        method = visitor._extract_method(method_decl)

        assert method is not None
        assert method.name == "findByEmail"
        assert method.http_method is None  # Not a web method

    def test_is_repository_method(self):
        """Test repository method pattern recognition"""
        cu = Mock()
        visitor = SpringAnnotationVisitor(cu)

        assert visitor._is_repository_method("findByEmail") is True
        assert visitor._is_repository_method("save") is True
        assert visitor._is_repository_method("deleteById") is True
        assert visitor._is_repository_method("existsByName") is True
        assert visitor._is_repository_method("countByStatus") is True
        assert visitor._is_repository_method("someOtherMethod") is False
