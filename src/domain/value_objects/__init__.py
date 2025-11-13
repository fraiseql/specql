"""Value Objects for Domain Model"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class DomainNumber:
    """Domain number (00-FF hex) - immutable value object"""
    value: str

    def __post_init__(self):
        # Validate hex format: 00-FF (case insensitive)
        if not re.match(r'^[0-9a-fA-F]{2}$', self.value):
            raise ValueError(f"Domain number must be 2-digit hex (00-FF), got: {self.value}")

        # Ensure it's not 00 (reserved)
        if self.value.upper() == '00':
            raise ValueError("Domain number cannot be 00 (reserved)")

        # Convert to uppercase for consistency
        object.__setattr__(self, "value", self.value.upper())

    def __str__(self):
        return self.value

@dataclass(frozen=True)
class SubdomainNumber:
    """
    Value Object: Subdomain Number (3-digit hex format: 01A)

    Format: DDS where DD = domain (2 hex digits), S = subdomain (1 hex digit)
    Examples: 01A (domain 01, subdomain A), 05F (domain 05, subdomain F)
    """
    value: str

    def __post_init__(self):
        """Validate subdomain number format"""
        self._validate()

    def _validate(self):
        """Validate subdomain number"""
        if not self.value:
            raise ValueError("Subdomain number cannot be empty")

        # Remove separator if present (01:A → 01A)
        clean_value = self.value.replace(":", "")

        if len(clean_value) != 3:
            raise ValueError(f"Subdomain number must be 3 hex digits, got: {self.value}")

        if not re.match(r'^[0-9a-fA-F]{3}$', clean_value):
            raise ValueError(f"Subdomain number must contain only hex digits (0-9,A-F), got: {self.value}")

        # Update value to clean uppercase format
        object.__setattr__(self, "value", clean_value.upper())

    @property
    def domain_part(self) -> str:
        """Get domain part (first 2 digits)"""
        return self.value[:2]

    @property
    def subdomain_part(self) -> str:
        """Get subdomain part (last digit)"""
        return self.value[2]

    @property
    def subdomain_sequence(self) -> int:
        """Get subdomain sequence number (0-9)"""
        return int(self.subdomain_part)

    def get_parent_domain_number(self) -> DomainNumber:
        """Get parent domain number as DomainNumber value object"""
        return DomainNumber(self.domain_part)

    def format_with_separator(self) -> str:
        """Format with separator (012 → 01:2)"""
        return f"{self.domain_part}:{self.subdomain_part}"

    def format_full(self) -> str:
        """Format as full description"""
        return f"Domain {self.domain_part}, Subdomain {self.subdomain_part}"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"SubdomainNumber('{self.value}')"

@dataclass(frozen=True)
class EntitySequence:
    """
    Value Object: Entity Sequence Number (single digit: 0-9)

    Represents the sequential position of an entity within a subdomain.
    Used as the fourth digit in entity codes (DDSE where E = entity sequence).

    Examples:
    - 0: First entity in subdomain
    - 5: Sixth entity in subdomain
    - 9: Tenth entity in subdomain
    """
    value: int

    def __post_init__(self):
        """Validate entity sequence"""
        self._validate()

    def _validate(self):
        """Validate entity sequence number"""
        if not isinstance(self.value, int):
            raise TypeError(f"Entity sequence must be an integer, got: {type(self.value)}")

        if self.value < 0 or self.value > 9:
            raise ValueError(f"Entity sequence must be between 0 and 9, got: {self.value}")

    def next(self) -> "EntitySequence":
        """Get next sequence number"""
        if self.value >= 9:
            raise ValueError("No next sequence available (already at 9)")
        return EntitySequence(self.value + 1)

    def previous(self) -> "EntitySequence":
        """Get previous sequence number"""
        if self.value <= 0:
            raise ValueError("No previous sequence available (already at 0)")
        return EntitySequence(self.value - 1)

    def to_hex(self) -> str:
        """Convert to hexadecimal string (0-9)"""
        return f"{self.value:x}"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"EntitySequence({self.value})"

    def __lt__(self, other: "EntitySequence") -> bool:
        return self.value < other.value

    def __le__(self, other: "EntitySequence") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "EntitySequence") -> bool:
        return self.value > other.value

    def __ge__(self, other: "EntitySequence") -> bool:
        return self.value >= other.value

@dataclass(frozen=True)
class TableCode:
    """6-digit table code - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^\d{6}$', self.value):
            raise ValueError(f"Table code must be 6 digits, got: {self.value}")

    @classmethod
    def generate(cls, domain_num: str, subdomain_num: str, entity_seq: int, file_seq: int = 0) -> 'TableCode':
        """Generate 6-digit code from components"""
        code = f"{domain_num}{subdomain_num}{entity_seq:02d}{file_seq}"
        if len(code) > 6:
            # Handle longer sequences by using the last 6 digits
            code = code[-6:]
        elif len(code) < 6:
            # Pad with zeros if too short
            code = code.zfill(6)
        return cls(code)

    def __str__(self):
        return self.value