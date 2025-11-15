"""Handle advanced Rust patterns when parsing Diesel models"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class RustAdvancedMetadata:
    """Metadata extracted from advanced Rust patterns"""

    has_lifetimes: bool = False
    lifetime_params: Optional[List[str]] = None
    has_generics: bool = False
    generic_params: Optional[List[str]] = None
    is_async: bool = False
    advanced_types: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.lifetime_params is None:
            self.lifetime_params = []
        if self.generic_params is None:
            self.generic_params = []
        if self.advanced_types is None:
            self.advanced_types = {}


class AdvancedRustPatternHandler:
    """Parse and handle advanced Rust patterns"""

    def extract_advanced_metadata(self, rust_code: str) -> RustAdvancedMetadata:
        """Extract advanced pattern metadata from Rust code"""
        metadata = RustAdvancedMetadata()

        # Check for lifetime parameters
        lifetime_pattern = r"struct\s+\w+<\'(\w+)(?:,\s*\'(\w+))*>"
        lifetime_match = re.search(lifetime_pattern, rust_code)
        if lifetime_match:
            metadata.has_lifetimes = True
            metadata.lifetime_params = [g for g in lifetime_match.groups() if g]

        # Check for generic type parameters
        generic_pattern = (
            r"struct\s+\w+<([A-Z]\w*(?::\s*\w+)?(?:,\s*[A-Z]\w*(?::\s*\w+)?)*)>"
        )
        generic_match = re.search(generic_pattern, rust_code)
        if generic_match:
            metadata.has_generics = True
            generic_str = generic_match.group(1)
            # Parse generic parameters
            metadata.generic_params = [p.strip() for p in generic_str.split(",")]

        # Check for async functions
        if "async fn" in rust_code:
            metadata.is_async = True

        # Find advanced Diesel types
        metadata.advanced_types = self._find_advanced_types(rust_code)

        return metadata

    def _find_advanced_types(self, rust_code: str) -> Dict[str, str]:
        """Find fields with advanced Diesel types"""
        advanced_types = {}

        # Pattern for Diesel advanced types
        type_patterns = {
            "Array": r"pub\s+(\w+):\s*Vec<(.+?)>",
            "Jsonb": r"pub\s+(\w+):\s*serde_json::Value",
            "Uuid": r"pub\s+(\w+):\s*uuid::Uuid",
            "Range": r"pub\s+(\w+):\s*\((.+?),\s*(.+?)\)",
        }

        for diesel_type, pattern in type_patterns.items():
            matches = re.finditer(pattern, rust_code)
            for match in matches:
                field_name = match.group(1)
                advanced_types[field_name] = diesel_type

        return advanced_types

    def should_generate_async(self, metadata: RustAdvancedMetadata) -> bool:
        """Determine if we should generate async handlers"""
        return metadata.is_async

    def get_type_constraints(self, metadata: RustAdvancedMetadata) -> List[str]:
        """Get type constraints for generic parameters"""
        constraints = []
        if metadata.generic_params:
            for param in metadata.generic_params:
                if ":" in param:
                    constraints.append(param)
        return constraints
