"""TypeScript type generation for polymorphic patterns."""

from typing import Dict, Any


def generate_polymorphic_types(pattern_config: Dict[str, Any]) -> str:
    """Generate TypeScript types for a polymorphic pattern.

    Args:
        pattern_config: The polymorphic pattern configuration

    Returns:
        TypeScript type definitions as a string
    """
    config = pattern_config.get("config", pattern_config)

    discriminator_field = config["discriminator_field"]
    variants = config["variants"]
    output_key = config.get("output_key", "pk_value")

    # Generate the union type name
    pattern_name = pattern_config["name"]
    union_type_name = _to_pascal_case(pattern_name) + "Type"

    # Generate class values union
    class_values = [f"'{variant['class_value']}'" for variant in variants]
    class_union = " | ".join(class_values)

    # Generate the resolver interface
    resolver_interface = f"""
export interface {union_type_name}Resolver {{
  {output_key}: string;
  {discriminator_field}: {class_union};
}}
"""

    # Generate discriminated union type
    union_cases = []
    for variant in variants:
        entity_name = _extract_entity_name(variant["entity"])
        case = (
            f"""  | {{ {discriminator_field}: '{variant["class_value"]}'; data: {entity_name} }}"""
        )
        union_cases.append(case)

    union_type = f"""
export type {union_type_name} ={"".join(union_cases)};
"""

    # Generate type guard functions
    type_guards = []
    for variant in variants:
        class_value = variant["class_value"]
        function_name = f"is{union_type_name.replace('Type', '')}{_to_pascal_case(class_value)}"
        type_guards.append(f"""
export function {function_name}(item: {union_type_name}): item is Extract<{union_type_name}, {{ {discriminator_field}: '{class_value}' }}> {{
  return item.{discriminator_field} === '{class_value}';
}}
""")

    # Combine all parts
    result = f"// Generated TypeScript types for polymorphic pattern: {pattern_name}\n"
    result += resolver_interface
    result += union_type
    result += "".join(type_guards)

    return result.strip()


def _to_pascal_case(s: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in s.split("_"))


def _extract_entity_name(entity_ref: Dict[str, Any]) -> str:
    """Extract a suitable TypeScript type name from entity reference."""
    # This is a simplified implementation - in practice this would
    # need to map entity references to actual TypeScript types
    if isinstance(entity_ref, dict) and "table" in entity_ref:
        # Extract from table name like "tb_contract_item" -> "ContractItem"
        table_name = entity_ref["table"]
        if table_name.startswith("tb_"):
            # Remove "tb_" prefix and convert snake_case to PascalCase
            name_parts = table_name[3:].split("_")
            return "".join(word.capitalize() for word in name_parts)
        return table_name.capitalize()

    # Fallback
    return "Entity"
