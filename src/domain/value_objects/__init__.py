"""Value Objects for Domain Model"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class DomainNumber:
    """Domain number (1-9) - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^[1-9]$', self.value):
            raise ValueError(f"Domain number must be 1-9, got: {self.value}")

    def __str__(self):
        return self.value

@dataclass(frozen=True)
class TableCode:
    """6-digit table code - immutable value object"""
    value: str

    def __post_init__(self):
        if not re.match(r'^\d{6}$', self.value):
            raise ValueError(f"Table code must be 6 digits, got: {self.value}")

    @classmethod
    def generate(cls, domain_num: str, subdomain_num: str, entity_seq: int) -> 'TableCode':
        """Generate 6-digit code from components"""
        code = f"{domain_num}{subdomain_num}{entity_seq:02d}"
        if len(code) > 6:
            # Handle longer sequences by using the last 6 digits
            code = code[-6:]
        elif len(code) < 6:
            # Pad with zeros if too short
            code = code.zfill(6)
        return cls(code)

    def __str__(self):
        return self.value