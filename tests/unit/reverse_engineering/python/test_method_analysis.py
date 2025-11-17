"""
Tests for Python method analysis and action generation

These tests focus on converting Python methods to SpecQL actions.
"""

import pytest
from src.reverse_engineering.python_ast_parser import PythonASTParser


class TestPythonMethodAnalysis:
    """Test Python method parsing and analysis"""

    def setup_method(self):
        """Initialize parser for each test"""
        self.parser = PythonASTParser()

    def test_crud_method_detection(self):
        """Test detection of CRUD operations in methods"""
        python_code = """
        class ContactRepository:
            def create_contact(self, email: str, name: str) -> Contact:
                contact = Contact(email=email, name=name)
                self.db.add(contact)
                self.db.commit()
                return contact

            def get_contact(self, contact_id: int) -> Optional[Contact]:
                return self.db.query(Contact).filter(Contact.id == contact_id).first()

            def update_contact(self, contact_id: int, updates: dict) -> Contact:
                contact = self.get_contact(contact_id)
                for key, value in updates.items():
                    setattr(contact, key, value)
                self.db.commit()
                return contact

            def delete_contact(self, contact_id: int) -> bool:
                contact = self.get_contact(contact_id)
                if contact:
                    self.db.delete(contact)
                    self.db.commit()
                    return True
                return False
        """

        result = self.parser.parse_entity(python_code)

        # Check that methods are parsed correctly
        create_method = next(m for m in result.methods if m.method_name == "create_contact")
        assert create_method.return_type == "Contact"
        assert len(create_method.parameters) == 2
        assert create_method.parameters[0]["name"] == "email"

        get_method = next(m for m in result.methods if m.method_name == "get_contact")
        assert "Optional[Contact]" in get_method.return_type or "Contact" in get_method.return_type

        update_method = next(m for m in result.methods if m.method_name == "update_contact")
        assert update_method.return_type == "Contact"

        delete_method = next(m for m in result.methods if m.method_name == "delete_contact")
        assert delete_method.return_type == "bool"
        # NOTE: CRUD operation detection in metadata not yet implemented

    def test_business_logic_method_parsing(self):
        """Test parsing methods with business logic"""
        python_code = """
        class ContactService:
            def qualify_lead(self, contact: Contact) -> bool:
                '''Qualify a lead based on business rules'''
                if contact.status != 'lead':
                    return False

                # Check if contact has been engaged
                engagements = self.get_engagements(contact.id)
                if len(engagements) < 3:
                    return False

                # Check company size
                if contact.company and contact.company.employee_count < 50:
                    return False

                # Check budget signals
                budget_signals = self.analyze_budget_signals(contact.id)
                if budget_signals.score < 0.7:
                    return False

                return True
        """

        result = self.parser.parse_entity(python_code)

        qualify_method = next(m for m in result.methods if m.method_name == "qualify_lead")
        assert len(qualify_method.body_lines) > 5  # Should parse the complex logic
        assert qualify_method.return_type == "bool"
        assert qualify_method.docstring == "Qualify a lead based on business rules"
        # NOTE: Complexity analysis and business logic categorization not yet implemented

    def test_validation_method_parsing(self):
        """Test parsing validation methods"""
        python_code = """
        class ContactValidator:
            def validate_email(self, email: str) -> List[str]:
                errors = []
                if not email:
                    errors.append("Email is required")
                elif '@' not in email:
                    errors.append("Invalid email format")
                elif len(email) > 254:
                    errors.append("Email too long")
                return errors

            def validate_contact(self, contact: Contact) -> ValidationResult:
                errors = {}

                # Email validation
                email_errors = self.validate_email(contact.email)
                if email_errors:
                    errors['email'] = email_errors

                # Required fields
                if not contact.first_name:
                    errors['first_name'] = ["First name is required"]

                return ValidationResult(is_valid=len(errors) == 0, errors=errors)
        """

        result = self.parser.parse_entity(python_code)

        validate_email = next(m for m in result.methods if m.method_name == "validate_email")
        assert validate_email.return_type == "List[str]"
        assert len(validate_email.body_lines) > 0

        validate_contact = next(m for m in result.methods if m.method_name == "validate_contact")
        assert validate_contact.return_type and "ValidationResult" in validate_contact.return_type
        # NOTE: Validation method detection (is_validator metadata) not yet implemented
