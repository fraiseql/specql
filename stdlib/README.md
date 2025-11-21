# SpecQL Standard Library

Battle-tested entity definitions extracted from PrintOptim production system.

## Overview

The SpecQL standard library provides reusable entity definitions for common business domains:

- **i18n**: Internationalization (countries, currencies, languages)
- **geo**: Geography and addresses
- **crm**: Customer relationship management
- **org**: Organizational structure
- **commerce**: Business commerce (contracts, orders, pricing)
- **tech**: Technology reference data
- **time**: Temporal entities
- **common**: Common reference data

## Usage

Import stdlib entities in your project:

```yaml
# Use as-is
import: stdlib/i18n/country

# Or extend with customization
entity: MyAddress
extends:
  from: stdlib/geo/public_address
fields:
  # Add your custom fields
  custom_field: text
```

## Philosophy

stdlib entities are:
- **Battle-tested**: Extracted from production PrintOptim system
- **Generic**: Useful across any application domain
- **Well-designed**: Follow SpecQL best practices
- **Standard-based**: Implement ISO/international standards where applicable
- **Minimal dependencies**: Only reference other stdlib entities

## Rich Types

stdlib demonstrates best practices for using FraiseQL rich scalar types:

- **coordinates**: Geographic coordinates (PostgreSQL POINT)
- **email**: Email addresses with validation
- **phone**: Phone numbers (E.164 format)
- **url**: URLs with validation
- **money**: Monetary amounts

See [stdlib/docs/rich_types.md](docs/rich_types.md) for details.

## Version

Current version: 1.1.0

See CHANGELOG.md for version history.
