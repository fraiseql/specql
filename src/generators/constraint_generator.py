"""
Constraint Generator for Rich Types
Generates CHECK constraints for FraiseQL rich types
"""

from typing import Optional
from src.core.ast_models import FieldDefinition


class ConstraintGenerator:
    """Generates CHECK constraints for rich types"""

    def generate_constraint(self, field: FieldDefinition, table_name: str) -> Optional[str]:
        """Generate appropriate constraint for a field"""

        if not field.is_rich_type():
            return None

        # Get validation pattern
        pattern = field.get_validation_pattern()
        if pattern:
            constraint_name = self._generate_constraint_name(table_name, field.name, "check")
            return f"CONSTRAINT {constraint_name} CHECK ({field.name} ~* '{pattern}')"

        # Special constraints for specific types
        if field.type == "coordinates":
            constraint_name = self._generate_constraint_name(table_name, field.name, "bounds")
            return f"CONSTRAINT {constraint_name} CHECK ({field.name}[0] BETWEEN -90 AND 90 AND {field.name}[1] BETWEEN -180 AND 180)"

        return None

    def _generate_constraint_name(
        self, table_name: str, field_name: str, constraint_type: str
    ) -> str:
        """Generate consistent constraint names"""
        # Remove schema prefix if present
        table_short = table_name.split(".")[-1] if "." in table_name else table_name
        return f"chk_{table_short}_{field_name}_{constraint_type}"

    # Specific constraint generators for better organization
    def generate_email_constraint(self, field_name: str, table_name: str) -> str:
        """Generate email validation constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "email")
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
        return f"CONSTRAINT {constraint_name} CHECK ({field_name} ~* '{pattern}')"

    def generate_url_constraint(self, field_name: str, table_name: str) -> str:
        """Generate URL validation constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "url")
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return f"CONSTRAINT {constraint_name} CHECK ({field_name} ~* '{pattern}')"

    def generate_phone_constraint(self, field_name: str, table_name: str) -> str:
        """Generate phone number validation constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "phone")
        pattern = r"^\+?[1-9]\d{1,14}$"
        return f"CONSTRAINT {constraint_name} CHECK ({field_name} ~* '{pattern}')"

    def generate_color_constraint(self, field_name: str, table_name: str) -> str:
        """Generate color hex validation constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "color")
        pattern = r"^#[0-9A-Fa-f]{6}$"
        return f"CONSTRAINT {constraint_name} CHECK ({field_name} ~* '{pattern}')"

    def generate_slug_constraint(self, field_name: str, table_name: str) -> str:
        """Generate slug validation constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "slug")
        pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
        return f"CONSTRAINT {constraint_name} CHECK ({field_name} ~* '{pattern}')"

    def generate_coordinates_constraint(self, field_name: str, table_name: str) -> str:
        """Generate coordinates bounds constraint"""
        constraint_name = self._generate_constraint_name(table_name, field_name, "bounds")
        return f"CONSTRAINT {constraint_name} CHECK ({field_name}[0] BETWEEN -90 AND 90 AND {field_name}[1] BETWEEN -180 AND 180)"
