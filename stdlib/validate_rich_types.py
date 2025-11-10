#!/usr/bin/env python3
"""
Validate that stdlib entities use rich types where appropriate.

Checks:
1. No lat/lng pairs without coordinates type
2. Email fields use email type
3. Phone fields use phone type
4. URL fields use url type
5. Money fields use money type
"""

from pathlib import Path

import yaml

RICH_TYPE_RULES = {
    # Field name patterns → expected type
    'email': 'email',
    'phone': 'phone',
    'mobile': 'phone',
    'website': 'url',
    'homepage': 'url',
    'url': 'url',
    'amount': 'money',
    'price': 'money',
}

def validate_rich_types():
    errors = []
    warnings = []

    for yaml_file in Path("stdlib").rglob("*.yaml"):
        if yaml_file.name in ["README.md", "VERSION"]:
            continue

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        if not data or "fields" not in data:
            continue

        # Check for lat/lng without coordinates
        fields = data["fields"]
        has_lat = any("lat" in str(k).lower() for k in fields.keys())
        has_lng = any("lng" in str(k).lower() or "lon" in str(k).lower() for k in fields.keys())
        has_coordinates = "coordinates" in fields

        if (has_lat and has_lng) and not has_coordinates:
            errors.append(f"{yaml_file}: Has lat/lng fields but no coordinates type")

        # Check field name → type mapping
        for field_name, field_def in fields.items():
            field_type = field_def.get("type") if isinstance(field_def, dict) else field_def

            for pattern, expected_type in RICH_TYPE_RULES.items():
                if pattern in field_name.lower():
                    if field_type != expected_type:
                        warnings.append(
                            f"{yaml_file}: Field '{field_name}' type is '{field_type}', "
                            f"should consider '{expected_type}'"
                        )

    return errors, warnings

if __name__ == "__main__":
    errors, warnings = validate_rich_types()

    if errors:
        print("❌ Errors:")
        for err in errors:
            print(f"  - {err}")

    if warnings:
        print("\n⚠️  Warnings:")
        for warn in warnings:
            print(f"  - {warn}")

    if not errors and not warnings:
        print("✅ All stdlib entities use rich types appropriately")

    exit(1 if errors else 0)
