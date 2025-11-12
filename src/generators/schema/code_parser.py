"""
Read-side code parsing utilities

Parses 7-digit read-side codes into components for path generation.
"""

from dataclasses import dataclass


@dataclass
class ReadSideCodeComponents:
    """Components of a read-side code"""
    schema_prefix: str  # "0"
    layer: str          # "2" (read-side)
    domain: str         # "2" (crm), "3" (catalog), etc.
    subdomain: str      # "03" (customer), "01" (manufacturer), etc.
    entity: str         # "1", "2", etc.
    file_num: str       # "0", "1", etc.


class ReadSideCodeParser:
    """
    Parses 7-digit read-side codes into components

    Format: 0SDSSEV
    - 0: schema prefix
    - S: layer (2 for read-side)
    - D: domain (1 digit)
    - SS: subdomain (2 digits)
    - E: entity (1 digit)
    - V: file number (1 digit)
    """

    def parse(self, code: str) -> ReadSideCodeComponents:
        """
        Parse a 7-digit read-side code into components

        Format: 0SDSSEV
        - 0: schema prefix (always "0")
        - S: schema layer (should be "2" for read-side)
        - D: domain code (1 digit)
        - SS: subdomain code (2 digits)
        - E: entity number (1 digit)
        - V: file number (1 digit)

        Args:
            code: 7-digit code string (e.g., "0220310")

        Returns:
            ReadSideCodeComponents with parsed values

        Raises:
            ValueError: If code format is invalid

        Example:
            parse("0220310") → ReadSideCodeComponents(
                schema_prefix="0", layer="2", domain="2",
                subdomain="03", entity="1", file_num="0"
            )
        """
        if not isinstance(code, str):
            raise ValueError(f"Code must be a string, got {type(code)}")

        if len(code) != 7:
            raise ValueError(f"Invalid code length: {len(code)} (expected 7 digits, got '{code}')")

        # Basic format validation
        if not code.isdigit():
            raise ValueError(f"Code must contain only digits, got '{code}'")

        try:
            return ReadSideCodeComponents(
                schema_prefix=code[0],
                layer=code[1],
                domain=code[2],
                subdomain=code[3:5],
                entity=code[5],
                file_num=code[6]
            )
        except IndexError as e:
            raise ValueError(f"Invalid code format: {code}") from e