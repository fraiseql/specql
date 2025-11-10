"""
Tests for rich type validation in actions
"""

import pytest

from src.core.ast_models import Entity, FieldDefinition
from src.generators.actions.expression_compiler import ExpressionCompiler
from src.generators.actions.validation_step_compiler import ExpressionParser, ValidationStepCompiler


@pytest.fixture
def contact_entity():
    """Create a Contact entity with rich type fields for testing"""
    return Entity(
        name="contact",
        schema="tenant",
        fields={
            "id": FieldDefinition(name="id", type_name="uuid", nullable=False),
            "email_address": FieldDefinition(
                name="email_address", type_name="email", nullable=False
            ),
            "office_phone": FieldDefinition(
                name="office_phone", type_name="phoneNumber", nullable=True
            ),
            "mobile_phone": FieldDefinition(
                name="mobile_phone", type_name="phoneNumber", nullable=True
            ),
            "job_title": FieldDefinition(name="job_title", type_name="text", nullable=True),
            "salary": FieldDefinition(name="salary", type_name="money", nullable=True),
            "commission_rate": FieldDefinition(
                name="commission_rate", type_name="percentage", nullable=True
            ),
        },
    )


class TestRichTypeValidationStepCompiler:
    """Test validation step compilation with rich types"""

    def test_email_validation_pattern(self, contact_entity):
        """Test that email validation uses correct regex pattern"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test MATCHES expression with email
        sql = parser.parse("email_address MATCHES 'email'")
        expected_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert f"~ '{expected_pattern}'" in sql

    def test_phone_validation_pattern(self, contact_entity):
        """Test that phone validation uses E.164 pattern"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test MATCHES expression with phone
        sql = parser.parse("office_phone MATCHES 'phoneNumber'")
        expected_pattern = r"^\+[1-9]\d{1,14}$"
        assert f"~ '{expected_pattern}'" in sql

    def test_validate_rich_type_field(self, contact_entity):
        """Test VALIDATE expression for rich type fields"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test VALIDATE expression
        sql = parser.parse("VALIDATE email_address")
        # Should generate validation for email pattern
        assert "p_email_address ~" in sql
        assert "@" in sql  # Email pattern contains @

    def test_validate_phone_field(self, contact_entity):
        """Test VALIDATE expression for phone fields"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test VALIDATE expression for phone
        sql = parser.parse("VALIDATE office_phone")
        # Should generate validation for E.164 phone pattern
        assert "p_office_phone ~" in sql
        assert "+" in sql  # Phone pattern contains +

    def test_validate_money_field(self, contact_entity):
        """Test VALIDATE expression for money fields"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test VALIDATE expression for money
        sql = parser.parse("VALIDATE salary")
        # Should generate validation for money (min_value = 0)
        assert "p_salary >= 0.0" in sql

    def test_validate_percentage_field(self, contact_entity):
        """Test VALIDATE expression for percentage fields"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test VALIDATE expression for percentage
        sql = parser.parse("VALIDATE commission_rate")
        # Should generate validation for percentage (min=0, max=100)
        assert "p_commission_rate >= 0.0" in sql
        assert "p_commission_rate <= 100.0" in sql

    def test_legacy_pattern_names(self, contact_entity):
        """Test backward compatibility with legacy pattern names"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test legacy email_pattern
        sql = parser.parse("email_address MATCHES 'email_pattern'")
        expected_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert f"~ '{expected_pattern}'" in sql

        # Test legacy phone_pattern
        sql = parser.parse("office_phone MATCHES 'phone_pattern'")
        expected_pattern = r"^\+[1-9]\d{1,14}$"
        assert f"~ '{expected_pattern}'" in sql

    def test_invalid_rich_type_validation(self, contact_entity):
        """Test error handling for invalid rich type validation"""
        compiler = ValidationStepCompiler()
        parser = ExpressionParser(contact_entity)

        # Test VALIDATE on non-rich-type field
        with pytest.raises(ValueError, match="No validation defined"):
            parser.parse("VALIDATE job_title")  # job_title is text, not rich type


class TestRichTypeExpressionCompiler:
    """Test expression compilation with rich types"""

    def test_matches_email_expression(self, contact_entity):
        """Test MATCHES expression compilation for email"""
        compiler = ExpressionCompiler()

        # Test email validation expression
        sql = compiler.compile("email_address MATCHES 'email'", contact_entity)
        expected_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert f"v_email_address ~ '{expected_pattern}'" == sql

    def test_matches_phone_expression(self, contact_entity):
        """Test MATCHES expression compilation for phone"""
        compiler = ExpressionCompiler()

        # Test phone validation expression
        sql = compiler.compile("office_phone MATCHES 'phoneNumber'", contact_entity)
        expected_pattern = r"^\+[1-9]\d{1,14}$"
        assert f"v_office_phone ~ '{expected_pattern}'" == sql

    def test_literal_regex_pattern(self, contact_entity):
        """Test MATCHES with literal regex patterns"""
        compiler = ExpressionCompiler()

        # Test with literal regex pattern
        sql = compiler.compile("email_address MATCHES '[a-z]+'", contact_entity)
        assert "v_email_address ~ '[a-z]+'" == sql

    def test_complex_validation_expression(self, contact_entity):
        """Test complex expressions with rich type validation"""
        compiler = ExpressionCompiler()

        # Test complex expression with rich type validation
        sql = compiler.compile(
            "email_address MATCHES 'email' AND office_phone MATCHES 'phoneNumber'", contact_entity
        )

        # Should contain both validations
        assert "v_email_address ~" in sql
        assert "v_office_phone ~" in sql
        assert "AND" in sql

    def test_security_validation(self, contact_entity):
        """Test that dangerous expressions are blocked"""
        compiler = ExpressionCompiler()

        # Test SQL injection attempt
        with pytest.raises(Exception):  # SecurityError
            compiler.compile("email_address = 'test'; DROP TABLE users; --'", contact_entity)


class TestRichTypeIntegration:
    """Integration tests for rich type validation in complete actions"""

    def test_rich_type_validation_in_action_context(self, contact_entity):
        """Test that rich type validation works in action compilation context"""
        from src.core.ast_models import Action, ActionStep

        # Create a mock action with validation steps
        action = Action(
            name="create_contact",
            steps=[
                ActionStep(
                    type="validate",
                    expression="email_address MATCHES 'email'",
                    error="INVALID_EMAIL",
                ),
                ActionStep(
                    type="validate", expression="VALIDATE office_phone", error="INVALID_PHONE"
                ),
            ],
        )

        # Test that validation step compiler can handle these expressions
        compiler = ValidationStepCompiler()

        for step in action.steps:
            sql = compiler.compile(step, contact_entity)
            assert "IF NOT" in sql  # Should generate IF NOT validation
            assert "THEN" in sql
            assert "v_result.status := 'error'" in sql
