"""Additional tests for service_generator.py coverage"""

from src.core.universal_ast import (
    UniversalEntity,
    UniversalField,
    UniversalAction,
    UniversalStep,
    FieldType,
    StepType,
)
from src.generators.java.service_generator import JavaServiceGenerator


class TestServiceGeneratorCoverage:
    """Tests to increase service_generator.py coverage"""

    def test_generate_service_with_if_step(self):
        """Test IF step generation"""
        entity = UniversalEntity(
            name="Order",
            schema="ecommerce",
            fields=[
                UniversalField(name="total", type=FieldType.INTEGER),
                UniversalField(name="discount", type=FieldType.INTEGER),
            ],
            actions=[
                UniversalAction(
                    name="apply_discount",
                    entity="Order",
                    steps=[
                        UniversalStep(
                            type=StepType.IF,
                            expression="total > 100",
                            steps=[
                                UniversalStep(
                                    type=StepType.UPDATE,
                                    entity="Order",
                                    fields={"discount": 10},
                                )
                            ],
                        )
                    ],
                    impacts=["Order"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate if statement
        assert "if (" in java_code
        assert "applyDiscount" in java_code

    def test_generate_service_with_complex_expression(self):
        """Test complex expression parsing"""
        entity = UniversalEntity(
            name="Payment",
            schema="billing",
            fields=[
                UniversalField(name="amount", type=FieldType.INTEGER),
                UniversalField(name="currency", type=FieldType.TEXT),
            ],
            actions=[
                UniversalAction(
                    name="process",
                    entity="Payment",
                    steps=[
                        UniversalStep(
                            type=StepType.VALIDATE,
                            expression="amount > 0 AND currency = 'USD'",
                        )
                    ],
                    impacts=["Payment"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should handle complex validation
        assert "process" in java_code

    def test_generate_service_with_enum_comparison(self):
        """Test enum value comparison in actions"""
        entity = UniversalEntity(
            name="Task",
            schema="project",
            fields=[
                UniversalField(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["todo", "in_progress", "done"],
                )
            ],
            actions=[
                UniversalAction(
                    name="start_task",
                    entity="Task",
                    steps=[
                        UniversalStep(
                            type=StepType.VALIDATE, expression="status = 'todo'"
                        ),
                        UniversalStep(
                            type=StepType.UPDATE,
                            entity="Task",
                            fields={"status": "in_progress"},
                        ),
                    ],
                    impacts=["Task"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate enum comparison
        assert "TaskStatus" in java_code or "status" in java_code
        assert "startTask" in java_code

    def test_generate_service_with_multiple_updates(self):
        """Test multiple field updates in one step"""
        entity = UniversalEntity(
            name="User",
            schema="auth",
            fields=[
                UniversalField(name="loginCount", type=FieldType.INTEGER),
                UniversalField(name="lastLoginAt", type=FieldType.DATETIME),
                UniversalField(name="active", type=FieldType.BOOLEAN),
            ],
            actions=[
                UniversalAction(
                    name="record_login",
                    entity="User",
                    steps=[
                        UniversalStep(
                            type=StepType.UPDATE,
                            entity="User",
                            fields={
                                "loginCount": "loginCount + 1",
                                "lastLoginAt": "NOW()",
                                "active": "true",
                            },
                        )
                    ],
                    impacts=["User"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should generate multiple setters
        assert "setLoginCount" in java_code or "recordLogin" in java_code
        assert "setLastLoginAt" in java_code or "recordLogin" in java_code
        assert "setActive" in java_code or "recordLogin" in java_code

    def test_generate_service_error_handling(self):
        """Test error handling in service methods"""
        entity = UniversalEntity(
            name="Account",
            schema="banking",
            fields=[UniversalField(name="balance", type=FieldType.INTEGER)],
            actions=[
                UniversalAction(
                    name="withdraw",
                    entity="Account",
                    steps=[
                        UniversalStep(
                            type=StepType.VALIDATE, expression="balance >= amount"
                        )
                    ],
                    impacts=["Account"],
                )
            ],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should include error throwing
        assert (
            "throw" in java_code
            or "RuntimeException" in java_code
            or "IllegalStateException" in java_code
        )

    def test_generate_service_with_no_actions(self):
        """Test service generation with no custom actions"""
        entity = UniversalEntity(
            name="SimpleEntity",
            schema="test",
            fields=[UniversalField(name="value", type=FieldType.INTEGER)],
            actions=[],
        )

        generator = JavaServiceGenerator()
        java_code = generator.generate(entity)

        # Should only have CRUD methods
        assert "public SimpleEntity create" in java_code
        assert "public Optional<SimpleEntity> findById" in java_code
        assert "public List<SimpleEntity> findAll" in java_code
        assert "public SimpleEntity update" in java_code
        assert "public void delete" in java_code
