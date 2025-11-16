from src.core.ast_models import FieldDefinition
from src.generators.constraint_generator import ConstraintGenerator


def test_generate_email_field_with_check_constraint():
    """Email rich type should generate TEXT with email validation CHECK constraint"""
    field = FieldDefinition(name="email_address", type_name="email", nullable=False)

    generator = ConstraintGenerator()
    constraint = generator.generate_constraint(field, "tenant.tb_contact")

    # Should generate CHECK constraint with email regex
    assert constraint is not None
    assert "CHECK (" in constraint
    assert "@" in constraint  # Email regex pattern
    assert "email_address" in constraint


def test_generate_percentage_field_with_min_max_constraints():
    """Percentage rich type should generate NUMERIC with min/max CHECK constraints"""
    field = FieldDefinition(
        name="discount_rate", type_name="percentage", nullable=False
    )

    generator = ConstraintGenerator()
    constraint = generator.generate_constraint(field, "tenant.tb_product")

    # Should generate CHECK constraint with min/max range
    assert constraint is not None
    assert "CHECK (" in constraint
    assert ">= 0" in constraint  # min_value = 0
    assert "<= 100" in constraint  # max_value = 100
    assert "discount_rate" in constraint
