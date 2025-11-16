"""
Tests for CRUD pattern detection in impl methods.
"""

from src.reverse_engineering.rust_action_parser import RustActionMapper
from src.reverse_engineering.rust_parser import ImplMethodInfo


class TestCRUDPatternDetection:
    """Test detection of CRUD patterns from method names."""

    def test_create_patterns(self):
        """Test detection of create/insert patterns."""
        mapper = RustActionMapper()

        create_patterns = [
            "create",
            "Create",
            "insert",
            "Insert",
            "add",
            "Add",
            "new",
            "New",
            "save",
            "Save",
        ]

        for pattern in create_patterns:
            method = ImplMethodInfo(
                name=pattern,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed to detect create pattern: {pattern}"
            assert action["type"] == "create", (
                f"Wrong type for {pattern}: {action['type']}"
            )

    def test_read_patterns(self):
        """Test detection of read/find/get patterns."""
        mapper = RustActionMapper()

        read_patterns = [
            "get",
            "Get",
            "find",
            "Find",
            "read",
            "Read",
            "select",
            "Select",
            "fetch",
            "Fetch",
            "retrieve",
            "Retrieve",
            "query",
            "Query",
        ]

        for pattern in read_patterns:
            method = ImplMethodInfo(
                name=pattern,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed to detect read pattern: {pattern}"
            assert action["type"] == "read", (
                f"Wrong type for {pattern}: {action['type']}"
            )

    def test_update_patterns(self):
        """Test detection of update/modify patterns."""
        mapper = RustActionMapper()

        update_patterns = [
            "update",
            "Update",
            "modify",
            "Modify",
            "edit",
            "Edit",
            "change",
            "Change",
            "set",
            "Set",
        ]

        for pattern in update_patterns:
            method = ImplMethodInfo(
                name=pattern,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed to detect update pattern: {pattern}"
            assert action["type"] == "update", (
                f"Wrong type for {pattern}: {action['type']}"
            )

    def test_delete_patterns(self):
        """Test detection of delete/remove patterns."""
        mapper = RustActionMapper()

        delete_patterns = [
            "delete",
            "Delete",
            "remove",
            "Remove",
            "destroy",
            "Destroy",
            "erase",
            "Erase",
        ]

        for pattern in delete_patterns:
            method = ImplMethodInfo(
                name=pattern,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed to detect delete pattern: {pattern}"
            assert action["type"] == "delete", (
                f"Wrong type for {pattern}: {action['type']}"
            )

    def test_custom_patterns(self):
        """Test that non-CRUD methods are classified as custom."""
        mapper = RustActionMapper()

        custom_methods = [
            "validate",
            "process",
            "calculate",
            "transform",
            "send_email",
            "log_event",
            "authenticate",
        ]

        for method_name in custom_methods:
            method = ImplMethodInfo(
                name=method_name,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed to map custom method: {method_name}"
            assert action["type"] == "custom", (
                f"Wrong type for {method_name}: {action['type']}"
            )

    def test_private_methods_ignored(self):
        """Test that private methods are not mapped to actions."""
        mapper = RustActionMapper()

        method = ImplMethodInfo(
            name="create",
            visibility="private",
            parameters=[],
            return_type="()",
            is_async=False,
        )
        action = mapper.map_method_to_action(method)
        # Private methods should not be mapped to actions
        assert action is None

    def test_parameter_mapping(self):
        """Test that parameters are correctly mapped."""
        mapper = RustActionMapper()

        method = ImplMethodInfo(
            name="create_user",
            visibility="pub",
            parameters=[
                {
                    "name": "self",
                    "param_type": "&self",
                    "is_mut": False,
                    "is_ref": True,
                },
                {
                    "name": "name",
                    "param_type": "String",
                    "is_mut": False,
                    "is_ref": False,
                },
                {
                    "name": "email",
                    "param_type": "&str",
                    "is_mut": False,
                    "is_ref": True,
                },
            ],
            return_type="Result",
            is_async=True,
        )
        action = mapper.map_method_to_action(method)

        assert action is not None
        assert action["name"] == "create_user"
        assert action["type"] == "create"
        assert action["return_type"] == "Result"
        assert action["is_async"] is True

        # Check parameters (self should be excluded)
        assert len(action["parameters"]) == 2
        assert action["parameters"][0]["name"] == "name"
        assert action["parameters"][0]["type"] == "String"
        assert action["parameters"][1]["name"] == "email"
        assert action["parameters"][1]["type"] == "&str"

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive."""
        mapper = RustActionMapper()

        # Test mixed case
        mixed_case_methods = [
            ("CreateUser", "create"),
            ("FIND_BY_ID", "read"),
            ("updateProfile", "update"),
            ("DELETE_ITEM", "delete"),
        ]

        for method_name, expected_type in mixed_case_methods:
            method = ImplMethodInfo(
                name=method_name,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed for {method_name}"
            assert action["type"] == expected_type, (
                f"Wrong type for {method_name}: {action['type']}"
            )

    def test_compound_method_names(self):
        """Test CRUD detection in compound method names."""
        mapper = RustActionMapper()

        test_cases = [
            ("create_new_user", "create"),
            ("find_user_by_id", "read"),
            ("update_user_profile", "update"),
            ("delete_old_records", "delete"),
            ("insert_bulk_data", "create"),
            ("get_all_items", "read"),
            ("modify_settings", "update"),
            ("remove_duplicates", "delete"),
        ]

        for method_name, expected_type in test_cases:
            method = ImplMethodInfo(
                name=method_name,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed for {method_name}"
            assert action["type"] == expected_type, (
                f"Wrong type for {method_name}: {action['type']}"
            )

    def test_edge_cases(self):
        """Test edge cases in pattern detection."""
        mapper = RustActionMapper()

        # Methods that start with CRUD words but aren't actually CRUD
        edge_cases = [
            "created_at",  # Should be custom
            "getters",  # Should be custom
            "updater",  # Should be custom
            "deletable",  # Should be custom
        ]

        for method_name in edge_cases:
            method = ImplMethodInfo(
                name=method_name,
                visibility="pub",
                parameters=[],
                return_type="()",
                is_async=False,
            )
            action = mapper.map_method_to_action(method)
            assert action is not None, f"Failed for {method_name}"
            assert action["type"] == "custom", (
                f"Should be custom for {method_name}: {action['type']}"
            )

    def test_async_flag_preserved(self):
        """Test that async flag is preserved in action mapping."""
        mapper = RustActionMapper()

        # Test async create method
        async_method = ImplMethodInfo(
            name="create_async",
            visibility="pub",
            parameters=[],
            return_type="()",
            is_async=True,
        )
        action = mapper.map_method_to_action(async_method)
        assert action is not None
        assert action["is_async"] is True

        # Test sync method
        sync_method = ImplMethodInfo(
            name="create_sync",
            visibility="pub",
            parameters=[],
            return_type="()",
            is_async=False,
        )
        action = mapper.map_method_to_action(sync_method)
        assert action is not None
        assert not action["is_async"]
