"""
Tests for Spring Boot to SpecQL Converter
"""


from src.reverse_engineering.java.spring_visitor import SpringComponent, SpringMethod
from src.reverse_engineering.java.spring_to_specql import SpringToSpecQLConverter
from src.core.ast_models import ActionImpact


class TestSpringToSpecQLConverter:
    """Test Spring to SpecQL conversion functionality"""

    def setup_method(self):
        self.converter = SpringToSpecQLConverter()

    def test_convert_controller_component(self):
        """Test converting a controller component to actions"""
        # Create a mock controller component
        method = SpringMethod(
            name="getUser",
            return_type="User",
            parameters=[{"name": "id", "type": "Long"}],
            annotations=["@GetMapping"],
            http_method="GET",
            path="/users/{id}",
        )

        component = SpringComponent(
            class_name="UserController",
            component_type="rest_controller",
            package_name="com.example",
            methods=[method],
        )

        actions = self.converter.convert_component(component)

        assert len(actions) == 1
        action = actions[0]
        assert action.name == "get_users_{id}"
        assert len(action.steps) == 1
        assert action.steps[0].type == "select"
        assert action.steps[0].entity == "users"
        assert isinstance(action.impact, ActionImpact)

    def test_convert_service_component(self):
        """Test converting a service component to actions"""
        method = SpringMethod(
            name="createUser",
            return_type="User",
            parameters=[{"name": "user", "type": "User"}],
            annotations=["@Transactional"],
            http_method=None,
            path=None,
        )

        component = SpringComponent(
            class_name="UserService",
            component_type="service",
            package_name="com.example",
            methods=[method],
        )

        actions = self.converter.convert_component(component)

        assert len(actions) == 1
        action = actions[0]
        assert action.name == "userservice_createuser"
        assert len(action.steps) == 1
        assert action.steps[0].type == "call"
        assert action.steps[0].function_name == "createUser"

    def test_convert_repository_component(self):
        """Test converting a repository component to actions"""
        method = SpringMethod(
            name="findByEmail",
            return_type="User",
            parameters=[{"name": "email", "type": "String"}],
            annotations=[],
            http_method=None,
            path=None,
        )

        component = SpringComponent(
            class_name="UserRepository",
            component_type="repository",
            package_name="com.example",
            methods=[method],
        )

        actions = self.converter.convert_component(component)

        assert len(actions) == 1
        action = actions[0]
        assert action.name == "userrepository_findbyemail"
        assert len(action.steps) == 1
        assert action.steps[0].type == "select"
        assert action.steps[0].entity == "user"

    def test_generate_action_name(self):
        """Test action name generation from HTTP method and path"""
        method = SpringMethod(
            name="getUser",
            return_type="User",
            parameters=[],
            annotations=[],
            http_method="GET",
            path="/api/users/{id}",
        )

        name = self.converter._generate_action_name(method, "/api")
        assert name == "get_users_{id}"

    def test_infer_table_from_path(self):
        """Test table name inference from URL path"""
        assert self.converter._infer_table_from_path("/api/users") == "users"
        assert self.converter._infer_table_from_path("/users/{id}") == "users"
        assert self.converter._infer_table_from_path("/api/products") == "products"

    def test_plural_to_singular(self):
        """Test plural to singular conversion"""
        assert self.converter._plural_to_singular("users") == "user"
        assert self.converter._plural_to_singular("products") == "product"
        assert self.converter._plural_to_singular("categories") == "category"
        assert self.converter._plural_to_singular("data") == "data"  # No change

    def test_extract_path_parameters(self):
        """Test path parameter extraction"""
        params = self.converter._extract_path_parameters("/users/{id}/posts/{postId}")
        assert params == {"id": "$id", "postId": "$postId"}

        params = self.converter._extract_path_parameters("/users")
        assert params is None

    def test_get_repository_action_type(self):
        """Test repository action type determination"""
        assert self.converter._get_repository_action_type("findByEmail") == "read"
        assert self.converter._get_repository_action_type("save") == "create"
        assert self.converter._get_repository_action_type("deleteById") == "delete"
        assert self.converter._get_repository_action_type("existsByName") == "read"
        assert self.converter._get_repository_action_type("customMethod") == "custom"
