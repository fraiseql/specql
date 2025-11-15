"""Handle Lombok annotations when parsing Java entities"""

from typing import Dict, Set
from dataclasses import dataclass, field


@dataclass
class LombokMetadata:
    """Metadata extracted from Lombok annotations"""

    has_data: bool = False
    has_getter: bool = False
    has_setter: bool = False
    has_builder: bool = False
    has_all_args_constructor: bool = False
    has_no_args_constructor: bool = False
    has_required_args_constructor: bool = False
    non_null_fields: Set[str] = field(default_factory=set)
    builder_defaults: Dict[str, str] = field(default_factory=dict)


class LombokAnnotationHandler:
    """Parse and handle Lombok annotations"""

    def extract_lombok_metadata(self, java_code: str) -> LombokMetadata:
        """Extract Lombok annotation metadata from Java code"""
        metadata = LombokMetadata()

        # Check for @Data
        if "@Data" in java_code:
            metadata.has_data = True
            metadata.has_getter = True
            metadata.has_setter = True

        # Check for @Getter
        if "@Getter" in java_code:
            metadata.has_getter = True

        # Check for @Setter
        if "@Setter" in java_code:
            metadata.has_setter = True

        # Check for @Builder
        if "@Builder" in java_code:
            metadata.has_builder = True

        # Check for constructors
        if "@NoArgsConstructor" in java_code:
            metadata.has_no_args_constructor = True

        if "@AllArgsConstructor" in java_code:
            metadata.has_all_args_constructor = True

        if "@RequiredArgsConstructor" in java_code:
            metadata.has_required_args_constructor = True

        # Find @NonNull fields
        metadata.non_null_fields = self._find_non_null_fields(java_code)

        # Find @Builder.Default values
        metadata.builder_defaults = self._find_builder_defaults(java_code)

        return metadata

    def _find_non_null_fields(self, java_code: str) -> Set[str]:
        """Find fields marked with @NonNull"""
        import re

        non_null_fields = set()

        # Simple approach: find all field declarations and check if they're preceded by @NonNull
        # Look for patterns where @NonNull appears before a field declaration
        lines = java_code.split("\n")
        for i, line in enumerate(lines):
            if "@NonNull" in line:
                # Look ahead up to 3 lines for a field declaration
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if (
                        next_line
                        and next_line.startswith(("private", "public", "protected"))
                        and ";" in next_line
                    ):
                        match = re.search(
                            r"(?:private|public|protected)\s+\w+\s+(\w+)\s*;", next_line
                        )
                        if match:
                            field_name = match.group(1)
                            non_null_fields.add(field_name)
                            break

        return non_null_fields

    def _find_builder_defaults(self, java_code: str) -> Dict[str, str]:
        """Find fields with @Builder.Default"""
        import re

        builder_defaults = {}

        # Find all field declarations with @Builder.Default that have default values
        # Updated pattern to handle generic types like List<String> and Map<String, String>
        pattern = r"@Builder\.Default(?:\s*\n\s*@NonNull)?\s*\n?\s*(?:private|public|protected)\s+[^;]*?(\w+)\s*=\s*([^;]+);"
        matches = re.finditer(pattern, java_code, re.MULTILINE | re.DOTALL)

        for match in matches:
            field_name = match.group(1)
            default_value = match.group(2).strip()
            builder_defaults[field_name] = default_value

        return builder_defaults

    def should_infer_accessors(self, metadata: LombokMetadata) -> bool:
        """Determine if we should infer getters/setters exist"""
        return metadata.has_data or metadata.has_getter or metadata.has_setter

    def is_field_required(self, field_name: str, metadata: LombokMetadata) -> bool:
        """Check if a field is required based on Lombok annotations"""
        return field_name in metadata.non_null_fields
