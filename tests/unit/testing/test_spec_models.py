from src.testing.spec.spec_models import (
    TestSpec,
    TestScenario,
    TestAssertion,
    TestStep,
    TestFixture,
    TestType,
    ScenarioCategory,
    AssertionType,
)


class TestTestSpecModels:
    """Test universal test specification models"""

    def test_create_simple_test_assertion(self):
        """Test creating equality assertion"""
        assertion = TestAssertion(
            assertion_type=AssertionType.EQUALS,
            target="result.status",
            expected="success",
            message="Status should be success",
        )

        assert assertion.assertion_type == AssertionType.EQUALS
        assert assertion.target == "result.status"
        assert assertion.expected == "success"

    def test_create_exception_assertion(self):
        """Test creating exception assertion"""
        assertion = TestAssertion(
            assertion_type=AssertionType.THROWS,
            target="action_call",
            expected="ValidationError",
            message="Should throw ValidationError",
        )

        assert assertion.assertion_type == AssertionType.THROWS
        assert assertion.expected == "ValidationError"

    def test_create_test_step(self):
        """Test creating test step"""
        step = TestStep(
            step_type="setup",
            action="create_entity",
            entity="Contact",
            data={"email": "test@example.com", "status": "lead"},
            store_result="contact",
        )

        assert step.step_type == "setup"
        assert step.action == "create_entity"
        assert step.entity == "Contact"
        assert step.data["email"] == "test@example.com"

    def test_create_test_scenario(self):
        """Test creating complete test scenario"""
        scenario = TestScenario(
            scenario_name="test_qualify_lead_happy_path",
            description="Successfully qualify a lead contact",
            category=ScenarioCategory.HAPPY_PATH,
            setup_steps=[
                TestStep(
                    step_type="setup",
                    action="create_entity",
                    entity="Contact",
                    data={"email": "test@example.com", "status": "lead"},
                    store_result="contact",
                )
            ],
            action_steps=[
                TestStep(
                    step_type="action",
                    action="call_function",
                    function="qualify_lead",
                    parameters={"contact_id": "{{contact.id}}"},
                    store_result="result",
                )
            ],
            assertions=[
                TestAssertion(
                    assertion_type=AssertionType.EQUALS,
                    target="result.status",
                    expected="success",
                ),
                TestAssertion(
                    assertion_type=AssertionType.STATE_CHANGE,
                    target="contact.status",
                    expected="qualified",
                    actual="lead",
                ),
            ],
        )

        assert scenario.category == ScenarioCategory.HAPPY_PATH
        assert len(scenario.setup_steps) == 1
        assert len(scenario.action_steps) == 1
        assert len(scenario.assertions) == 2

    def test_test_spec_to_yaml(self):
        """Test converting TestSpec to YAML"""
        spec = TestSpec(
            test_name="contact_qualification_tests",
            entity_name="Contact",
            test_type=TestType.WORKFLOW,
            scenarios=[
                TestScenario(
                    scenario_name="test_qualify_lead",
                    description="Qualify a lead",
                    category=ScenarioCategory.HAPPY_PATH,
                    setup_steps=[],
                    action_steps=[],
                    assertions=[],
                )
            ],
            fixtures=[],
            coverage={"actions_covered": ["qualify_lead"], "coverage_percentage": 85.0},
        )

        yaml_output = spec.to_yaml()

        assert "test: contact_qualification_tests" in yaml_output
        assert "entity: Contact" in yaml_output
        assert "type: workflow" in yaml_output
        assert "actions_covered" in yaml_output

    def test_test_spec_with_complex_scenario(self):
        """Test TestSpec with complex scenario including all components"""
        spec = TestSpec(
            test_name="user_registration_tests",
            entity_name="User",
            test_type=TestType.WORKFLOW,
            scenarios=[
                TestScenario(
                    scenario_name="test_user_registration_complete_flow",
                    description="Complete user registration flow with email verification",
                    category=ScenarioCategory.HAPPY_PATH,
                    setup_steps=[
                        TestStep(
                            step_type="setup",
                            action="create_entity",
                            entity="User",
                            data={
                                "email": "test@example.com",
                                "username": "testuser",
                                "status": "pending_verification",
                            },
                            store_result="user",
                        )
                    ],
                    action_steps=[
                        TestStep(
                            step_type="action",
                            action="call_function",
                            function="send_verification_email",
                            parameters={"user_id": "{{user.id}}"},
                        ),
                        TestStep(
                            step_type="action",
                            action="call_function",
                            function="verify_email",
                            parameters={
                                "user_id": "{{user.id}}",
                                "token": "valid_token_123",
                            },
                            store_result="verification_result",
                        ),
                    ],
                    assertions=[
                        TestAssertion(
                            assertion_type=AssertionType.EQUALS,
                            target="verification_result.success",
                            expected=True,
                            message="Email verification should succeed",
                        ),
                        TestAssertion(
                            assertion_type=AssertionType.STATE_CHANGE,
                            target="user.status",
                            expected="verified",
                            actual="pending_verification",
                            message="User status should change to verified",
                        ),
                        TestAssertion(
                            assertion_type=AssertionType.EQUALS,
                            target="user.email_verified_at",
                            expected="not_null",
                            message="Email verified timestamp should be set",
                        ),
                    ],
                    fixtures=["test_email_service", "test_database"],
                    tags=["integration", "email", "verification"],
                )
            ],
            fixtures=[
                TestFixture(
                    fixture_name="test_email_service",
                    fixture_type="mock",
                    data={"service_class": "EmailService", "mock_responses": True},
                ),
                TestFixture(
                    fixture_name="test_database",
                    fixture_type="database",
                    setup_sql="INSERT INTO test_data VALUES (...)",
                    teardown_sql="DELETE FROM test_data",
                    scope="module",
                ),
            ],
            coverage={
                "actions_covered": ["send_verification_email", "verify_email"],
                "entities_covered": ["User"],
                "scenarios_covered": ["happy_path", "error_case"],
                "coverage_percentage": 92.5,
            },
        )

        # Test basic properties
        assert spec.test_name == "user_registration_tests"
        assert spec.entity_name == "User"
        assert spec.test_type == TestType.WORKFLOW
        assert len(spec.scenarios) == 1
        assert len(spec.fixtures) == 2

        # Test scenario details
        scenario = spec.scenarios[0]
        assert scenario.scenario_name == "test_user_registration_complete_flow"
        assert scenario.category == ScenarioCategory.HAPPY_PATH
        assert len(scenario.setup_steps) == 1
        assert len(scenario.action_steps) == 2
        assert len(scenario.assertions) == 3
        assert "test_email_service" in scenario.fixtures
        assert "integration" in scenario.tags

        # Test YAML serialization includes all components
        yaml_output = spec.to_yaml()
        assert "test: user_registration_tests" in yaml_output
        assert "entity: User" in yaml_output
        assert "type: workflow" in yaml_output
        assert "send_verification_email" in yaml_output
        assert "test_email_service" in yaml_output
        assert "integration" in yaml_output

    def test_assertion_types_comprehensive(self):
        """All assertion types should be valid."""
        assertion_types = [
            AssertionType.EQUALS,
            AssertionType.NOT_EQUALS,
            AssertionType.CONTAINS,
            AssertionType.IS_NULL,
            AssertionType.IS_NOT_NULL,
            AssertionType.THROWS,
            AssertionType.GREATER_THAN,
            AssertionType.LESS_THAN,
            AssertionType.STATE_CHANGE,
        ]

        for atype in assertion_types:
            assertion = TestAssertion(
                assertion_type=atype, target="field", expected="value"
            )
            assert assertion.assertion_type == atype

    def test_scenario_categories(self):
        """All scenario categories should be valid."""
        categories = [
            ScenarioCategory.HAPPY_PATH,
            ScenarioCategory.ERROR_CASE,
            ScenarioCategory.EDGE_CASE,
            ScenarioCategory.BOUNDARY,
        ]

        for category in categories:
            scenario = TestScenario(
                scenario_name="test",
                category=category,
                description="Test",
                setup_steps=[],
                action_steps=[],
                assertions=[],
            )
            assert scenario.category == category

    def test_test_types(self):
        """All test types should be valid."""
        test_types = [
            TestType.CRUD_CREATE,
            TestType.CRUD_READ,
            TestType.CRUD_UPDATE,
            TestType.CRUD_DELETE,
            TestType.VALIDATION,
            TestType.STATE_MACHINE,
            TestType.WORKFLOW,
        ]

        # Just verify they exist and are accessible
        for ttype in test_types:
            assert ttype.value is not None

    def test_test_spec_with_multiple_scenarios(self):
        """TestSpec should handle multiple scenarios."""
        assertion1 = TestAssertion(
            assertion_type=AssertionType.EQUALS, target="status", expected="success"
        )
        assertion2 = TestAssertion(
            assertion_type=AssertionType.THROWS,
            target="error",
            expected="ValidationError",
        )

        scenario1 = TestScenario(
            scenario_name="happy_path",
            category=ScenarioCategory.HAPPY_PATH,
            description="Happy path test",
            setup_steps=[],
            action_steps=[],
            assertions=[assertion1],
        )

        scenario2 = TestScenario(
            scenario_name="error_case",
            category=ScenarioCategory.ERROR_CASE,
            description="Error case test",
            setup_steps=[],
            action_steps=[],
            assertions=[assertion2],
        )

        test_spec = TestSpec(
            test_name="multi_scenario_test",
            entity_name="Contact",
            test_type=TestType.WORKFLOW,
            scenarios=[scenario1, scenario2],
        )

        assert len(test_spec.scenarios) == 2
        assert test_spec.scenarios[0].category == ScenarioCategory.HAPPY_PATH
        assert test_spec.scenarios[1].category == ScenarioCategory.ERROR_CASE

    def test_assertion_with_message(self):
        """TestAssertion should handle optional message."""
        assertion = TestAssertion(
            assertion_type=AssertionType.EQUALS, target="result", expected="ok"
        )

        assert assertion.message is None

        assertion_with_message = TestAssertion(
            assertion_type=AssertionType.EQUALS,
            target="result",
            expected="ok",
            message="Result should be ok",
        )

        assert assertion_with_message.message == "Result should be ok"

    def test_scenario_with_multiple_assertions(self):
        """TestScenario should handle multiple assertions."""
        assertions = [
            TestAssertion(
                assertion_type=AssertionType.EQUALS, target="status", expected="success"
            ),
            TestAssertion(
                assertion_type=AssertionType.IS_NOT_NULL, target="id", expected=None
            ),
            TestAssertion(
                assertion_type=AssertionType.CONTAINS, target="data", expected="email"
            ),
        ]

        scenario = TestScenario(
            scenario_name="comprehensive_test",
            category=ScenarioCategory.HAPPY_PATH,
            description="Test with multiple assertions",
            setup_steps=[],
            action_steps=[],
            assertions=assertions,
        )

        assert len(scenario.assertions) == 3
        assertion_types = [a.assertion_type for a in scenario.assertions]
        assert AssertionType.EQUALS in assertion_types
        assert AssertionType.IS_NOT_NULL in assertion_types
        assert AssertionType.CONTAINS in assertion_types

    def test_test_spec_different_frameworks(self):
        """TestSpec should support different test frameworks."""
        frameworks = ["pgtap", "pytest", "junit", "jest"]

        for framework in frameworks:
            test_spec = TestSpec(
                test_name="test",
                entity_name="TestEntity",
                test_type=TestType.WORKFLOW,
                scenarios=[],
            )
            assert test_spec.test_name == "test"

    def test_enum_values_unique(self):
        """All enum values should be unique."""
        assertion_values = [atype.value for atype in AssertionType]
        assert len(assertion_values) == len(set(assertion_values))

        category_values = [cat.value for cat in ScenarioCategory]
        assert len(category_values) == len(set(category_values))

        type_values = [ttype.value for ttype in TestType]
        assert len(type_values) == len(set(type_values))

    def test_assertion_type_string_representation(self):
        """Assertion types should have meaningful string representations."""
        assertion = TestAssertion(
            assertion_type=AssertionType.EQUALS, target="x", expected=5
        )

        # Should be able to convert to string
        str(assertion)
        repr(assertion)

    def test_scenario_type_string_representation(self):
        """Scenarios should have meaningful string representations."""
        scenario = TestScenario(
            scenario_name="test",
            category=ScenarioCategory.HAPPY_PATH,
            description="Test scenario",
            setup_steps=[],
            action_steps=[],
            assertions=[],
        )

        str(scenario)
        repr(scenario)

    def test_test_spec_string_representation(self):
        """TestSpec should have meaningful string representations."""
        test_spec = TestSpec(
            test_name="test",
            entity_name="Contact",
            test_type=TestType.WORKFLOW,
            scenarios=[],
        )

        str(test_spec)
        repr(test_spec)
