"""
Mock Entity fixtures for Team B generator testing
"""

from core.ast_models import (
    Action,
    ActionStep,
    Entity,
    FieldDefinition,
    OperationConfig,
    Organization,
)


def mock_contact_entity() -> Entity:
    """Create mock Contact entity for testing"""
    return Entity(
        name="Contact",
        schema="crm",
        description="CRM contact entity",
        organization=Organization(table_code="CON", domain_name="Contacts"),
        fields={
            "email": FieldDefinition(name="email", type_name="text", nullable=False),
            "status": FieldDefinition(
                name="status",
                type_name="enum",
                values=["lead", "qualified", "customer"],
                nullable=False,
            ),
            "company": FieldDefinition(
                name="company", type_name="ref", reference_entity="Company", nullable=True
            ),
        },
        actions=[
            Action(
                name="qualify_lead",
                steps=[
                    ActionStep(type="validate", expression="status = 'lead'"),
                    ActionStep(type="update", entity="Contact", fields={"status": "qualified"}),
                    ActionStep(
                        type="notify",
                        function_name="owner",
                        arguments={"channel": "email", "message": "Contact qualified"},
                    ),
                ],
            )
        ],
    )


def mock_company_entity() -> Entity:
    """Create mock Company entity for testing"""
    return Entity(
        name="Company",
        schema="crm",
        description="CRM company entity",
        organization=Organization(table_code="CMP", domain_name="Companies"),
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "industry": FieldDefinition(name="industry", type_name="text", nullable=True),
        },
    )


def mock_simple_entity() -> Entity:
    """Create simple entity with minimal fields"""
    return Entity(
        name="Product",
        schema="inventory",
        description="Simple product entity",
        fields={
            "name": FieldDefinition(name="name", type_name="text", nullable=False),
            "price": FieldDefinition(name="price", type_name="integer", nullable=False),
        },
        operations=OperationConfig(create=True, update=True, delete="soft"),
    )
