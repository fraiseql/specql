"""
Unit tests for Rust action mapper functionality.

Tests the CRUD pattern detection and action mapping logic.
"""

from src.reverse_engineering.rust_action_parser import (
    RustActionMapper,
    RouteToActionMapper,
)
from src.reverse_engineering.rust_parser import (
    ImplMethodInfo,
    RouteHandlerInfo,
    DieselDeriveInfo,
)


class TestRustActionMapper:
    """Test RustActionMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = RustActionMapper()

    def test_map_public_method_to_action(self):
        """Test mapping a public method to an action."""
        method = ImplMethodInfo(
            name="create_user",
            visibility="pub",
            parameters=[
                {
                    "name": "name",
                    "param_type": "String",
                    "is_mut": False,
                    "is_ref": False,
                },
                {
                    "name": "email",
                    "param_type": "String",
                    "is_mut": False,
                    "is_ref": False,
                },
            ],
            return_type="Result<User, Error>",
            is_async=True,
        )

        action = self.mapper.map_method_to_action(method)

        assert action is not None
        assert action["name"] == "create_user"
        assert action["type"] == "create"
        assert action["is_async"] is True
        assert len(action["parameters"]) == 2

    def test_map_private_method_returns_none(self):
        """Test that private methods are not mapped."""
        method = ImplMethodInfo(
            name="create_user",
            visibility="private",
            parameters=[],
            return_type="User",
            is_async=False,
        )

        action = self.mapper.map_method_to_action(method)
        assert action is None

    def test_detect_crud_create_patterns(self):
        """Test detection of create action patterns."""
        create_names = [
            "create_user",
            "createUser",
            "insert_record",
            "insertRecord",
            "add_item",
            "addItem",
            "new_instance",
            "save_data",
        ]

        for name in create_names:
            action_type = self.mapper._detect_crud_pattern(name)
            assert action_type == "create", f"Failed for: {name}"

    def test_detect_crud_read_patterns(self):
        """Test detection of read action patterns."""
        read_names = [
            "get_user",
            "getUser",
            "find_record",
            "findRecord",
            "read_data",
            "select_items",
            "fetch_all",
            "retrieve_one",
            "query_records",
        ]

        for name in read_names:
            action_type = self.mapper._detect_crud_pattern(name)
            assert action_type == "read", f"Failed for: {name}"

    def test_detect_crud_update_patterns(self):
        """Test detection of update action patterns."""
        update_names = [
            "update_user",
            "updateUser",
            "modify_record",
            "modifyRecord",
            "edit_item",
            "change_status",
            "set_value",
        ]

        for name in update_names:
            action_type = self.mapper._detect_crud_pattern(name)
            assert action_type == "update", f"Failed for: {name}"

    def test_detect_crud_delete_patterns(self):
        """Test detection of delete action patterns."""
        delete_names = [
            "delete_user",
            "deleteUser",
            "remove_record",
            "removeRecord",
            "destroy_item",
            "erase_data",
        ]

        for name in delete_names:
            action_type = self.mapper._detect_crud_pattern(name)
            assert action_type == "delete", f"Failed for: {name}"

    def test_detect_custom_pattern(self):
        """Test detection of custom actions (no CRUD pattern)."""
        custom_names = [
            "validate_email",
            "calculate_total",
            "send_notification",
            "process_payment",
        ]

        for name in custom_names:
            action_type = self.mapper._detect_crud_pattern(name)
            assert action_type == "custom", f"Failed for: {name}"

    def test_detect_underscore_patterns(self):
        """Test detection with underscore patterns like user_create."""
        # Test pattern: prefix_action
        action_type = self.mapper._detect_crud_pattern("user_create")
        assert action_type == "create"

        action_type = self.mapper._detect_crud_pattern("record_delete")
        assert action_type == "delete"

        action_type = self.mapper._detect_crud_pattern("data_update")
        assert action_type == "update"

    def test_map_parameters_filters_self(self):
        """Test that self parameter is filtered out."""
        method = ImplMethodInfo(
            name="get_user",
            visibility="pub",
            parameters=[
                {
                    "name": "self",
                    "param_type": "&self",
                    "is_mut": False,
                    "is_ref": True,
                },
                {"name": "id", "param_type": "i32", "is_mut": False, "is_ref": False},
            ],
            return_type="Option<User>",
            is_async=False,
        )

        action = self.mapper.map_method_to_action(method)

        assert action is not None
        assert len(action["parameters"]) == 1
        assert action["parameters"][0]["name"] == "id"

    def test_map_diesel_derive_to_action_not_implemented(self):
        """Test that diesel derive mapping returns None (not yet implemented)."""
        derive = DieselDeriveInfo(
            struct_name="User",
            derives=["Queryable", "Insertable"],
            associations=["users"],
        )

        action = self.mapper.map_diesel_derive_to_action(derive)
        assert action is None  # Not implemented yet

    def test_action_type_none_returns_none(self):
        """Test that methods with no CRUD pattern still return custom."""
        method = ImplMethodInfo(
            name="some_random_method",
            visibility="pub",
            parameters=[],
            return_type="()",
            is_async=False,
        )

        action = self.mapper.map_method_to_action(method)
        assert action is not None
        assert action["type"] == "custom"


class TestRouteToActionMapper:
    """Test RouteToActionMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = RouteToActionMapper()

    def test_map_get_route_to_read_action(self):
        """Test mapping GET route to read action."""
        route = RouteHandlerInfo(
            method="GET",
            path="/api/users/{id}",
            function_name="get_user",
            parameters=[{"name": "id", "param_type": "i32"}],
            return_type="Json<User>",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)

        assert action is not None
        assert action["name"] == "get_user"
        assert action["type"] == "read"
        assert action["http_method"] == "GET"
        assert action["path"] == "/api/users/{id}"
        assert action["is_async"] is True

    def test_map_post_route_to_create_action(self):
        """Test mapping POST route to create action."""
        route = RouteHandlerInfo(
            method="POST",
            path="/api/users",
            function_name="create_user",
            parameters=[],
            return_type="Json<User>",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)

        assert action is not None
        assert action["type"] == "create"
        assert action["http_method"] == "POST"

    def test_map_put_route_to_update_action(self):
        """Test mapping PUT route to update action."""
        route = RouteHandlerInfo(
            method="PUT",
            path="/api/users/{id}",
            function_name="update_user",
            parameters=[],
            return_type="Json<User>",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)

        assert action is not None
        assert action["type"] == "update"

    def test_map_patch_route_to_update_action(self):
        """Test mapping PATCH route to update action."""
        route = RouteHandlerInfo(
            method="PATCH",
            path="/api/users/{id}",
            function_name="patch_user",
            parameters=[],
            return_type="Json<User>",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)

        assert action is not None
        assert action["type"] == "update"

    def test_map_delete_route_to_delete_action(self):
        """Test mapping DELETE route to delete action."""
        route = RouteHandlerInfo(
            method="DELETE",
            path="/api/users/{id}",
            function_name="delete_user",
            parameters=[],
            return_type="HttpResponse",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)

        assert action is not None
        assert action["type"] == "delete"
        assert action["http_method"] == "DELETE"

    def test_map_unsupported_http_method_returns_none(self):
        """Test that unsupported HTTP methods return None."""
        route = RouteHandlerInfo(
            method="OPTIONS",
            path="/api/users",
            function_name="options_handler",
            parameters=[],
            return_type="HttpResponse",
            is_async=True,
        )

        action = self.mapper.map_route_to_action(route)
        assert action is None

    def test_map_route_to_endpoint(self):
        """Test mapping route to endpoint."""
        route = RouteHandlerInfo(
            method="GET",
            path="/api/users",
            function_name="list_users",
            parameters=[],
            return_type="Json<Vec<User>>",
            is_async=True,
        )

        endpoint = self.mapper.map_route_to_endpoint(route)

        assert endpoint is not None
        assert endpoint["method"] == "GET"
        assert endpoint["path"] == "/api/users"
        assert endpoint["handler"] == "list_users"
        assert endpoint["is_async"] is True
        assert endpoint["return_type"] == "Json<Vec<User>>"

    def test_map_route_with_parameters_to_endpoint(self):
        """Test mapping route with parameters to endpoint."""
        route = RouteHandlerInfo(
            method="POST",
            path="/api/users",
            function_name="create_user",
            parameters=[
                {"name": "user_data", "param_type": "Json<CreateUser>"},
            ],
            return_type="Json<User>",
            is_async=True,
        )

        endpoint = self.mapper.map_route_to_endpoint(route)

        assert endpoint is not None
        assert len(endpoint["parameters"]) == 1
        assert endpoint["parameters"][0]["name"] == "user_data"
