"""
Read-side code parsing utilities

Parses 7-digit read-side codes into components for path generation.
"""

from dataclasses import dataclass


@dataclass
class ReadSideCodeComponents:
    """Components of a read-side code"""
    schema_layer: str   # "02" (read-side)
    domain: str         # "2" (crm), "3" (catalog), etc.
    subdomain: str      # "3" (customer), "1" (manufacturer), etc. (1 digit)
    entity: str         # "2", "1", etc.
    file_num: str       # "0", "1", etc.


class ReadSideCodeParser:
    """
    Parses 6-digit read-side codes into components

    Format: SDSEX
    - SS: schema layer (02 for read-side)
    - D: domain (1 digit)
    - S: subdomain (1 digit)
    - E: entity (1 digit)
    - X: file number (1 digit)
    """

    def parse(self, code: str) -> ReadSideCodeComponents:
        """
        Parse a 6-digit read-side code into components

        Format: SDSEX
        - SS: schema layer (should be "02" for read-side)
        - D: domain code (1 digit)
        - S: subdomain code (1 digit)
        - E: entity number (1 digit)
        - X: file number (1 digit)

        Args:
            code: 6-digit code string (e.g., "022310")

        Returns:
            ReadSideCodeComponents with parsed values

        Raises:
            ValueError: If code format is invalid

        Example:
            parse("022310") → ReadSideCodeComponents(
                schema_layer="02", domain="2",
                subdomain="3", entity="1", file_num="0"
            )
        """
        if not isinstance(code, str):
            raise ValueError(f"Code must be a string, got {type(code)}")

        if len(code) != 6:
            raise ValueError(f"Invalid code length: {len(code)} (expected 6 digits, got '{code}')")

        # Basic format validation
        if not code.isdigit():
            raise ValueError(f"Code must contain only digits, got '{code}'")

        try:
            return ReadSideCodeComponents(
                schema_layer=code[0:2],
                domain=code[2],
                subdomain=code[3],
                entity=code[4],
                file_num=code[5]
            )
        except IndexError as e:
            raise ValueError(f"Invalid code format: {code}") from e