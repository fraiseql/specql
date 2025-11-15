"""Generate Java enum classes from SpecQL enum fields"""

from src.core.universal_ast import UniversalField, FieldType


class JavaEnumGenerator:
    """Generates Java enum classes"""

    def generate(self, field: UniversalField, package: str, entity_name: str) -> str:
        """Generate enum class for an enum field"""
        if field.type != FieldType.ENUM:
            raise ValueError(f"Field {field.name} is not an enum")

        enum_name = entity_name + self._to_pascal_case(field.name)

        lines = []
        lines.append(f"package {package};")
        lines.append("")
        lines.append(f"public enum {enum_name} {{")

        # Enum values
        if field.enum_values:
            values = [f"    {val.upper()}" for val in field.enum_values]
            lines.append(",\n".join(values))

        lines.append("}")

        return "\n".join(lines)

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return "".join(word.capitalize() for word in name.split("_"))
