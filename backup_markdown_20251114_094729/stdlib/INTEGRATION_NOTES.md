# SpecQL stdlib Integration Notes

**Copied from**: `/home/lionel/code/printoptim_specql/stdlib/`
**Date**: 2025-11-09
**Version**: 1.1.0

---

## What Was Copied

Complete SpecQL standard library with 30 battle-tested entities:

### Directory Structure

```
stdlib/
├── README.md                   # Overview and usage
├── VERSION                     # 1.1.0
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── validate_rich_types.py      # Rich type validation script
├── docs/
│   └── rich_types.md          # Rich types reference
├── i18n/                      # 6 entities (Country, Currency, Language, etc.)
├── geo/                       # 11 entities (PublicAddress, Location, etc.)
├── crm/                       # 3 entities (Organization, Contact, etc.)
├── org/                       # 2 entities (OrganizationalUnit, etc.)
├── commerce/                  # 3 entities (Contract, Order, Price)
├── tech/                      # 2 entities (OperatingSystem, etc.)
├── time/                      # 1 entity (Calendar)
└── common/                    # 2 entities (Genre, Industry)
```

**Total**: 30 entities

---

## Key Features (v1.1.0)

### Rich Type Implementation

stdlib v1.1.0 demonstrates FraiseQL best practices with rich scalar types:

1. **coordinates** - PostgreSQL POINT (PublicAddress, Location)
2. **email** - Email validation (Contact)
3. **phone** - E.164 phone format (Contact)
4. **money** - NUMERIC(19,4) (Price)
5. **url** - URL validation (AddressDatasource)

### Entity Categories

- **i18n**: ISO standards (ISO 3166, ISO 4217, ISO 639, BCP 47)
- **geo**: Complete address management with PostGIS support
- **crm**: CRM foundation (Organization, Contact)
- **org**: Organizational structure (hierarchical)
- **commerce**: Business commerce (contracts, orders, pricing)
- **tech**: Technology reference data
- **time**: Temporal entities
- **common**: Common reference data

---

## Integration with printoptim_backend_poc

### Status

✅ **Ready for integration** - stdlib can be used as-is or as reference

### Usage Options

#### Option 1: Use stdlib as Reference

Review stdlib entities for patterns and best practices:
- Rich type usage examples
- Field naming conventions
- Action patterns
- Hierarchical entity patterns

#### Option 2: Import stdlib Entities

Once Team A implements `import`/`extends` syntax in parser:

```yaml
# Import as-is
import: stdlib/i18n/country

# Or extend with customizations
entity: MyAddress
extends:
  from: stdlib/geo/public_address
fields:
  custom_field: text
```

#### Option 3: Generate from stdlib

Use stdlib as source for code generation:
- Team B: Generate SQL DDL from stdlib entities
- Team C: Generate PL/pgSQL functions from stdlib actions
- Team D: Generate GraphQL schemas from stdlib entities

---

## Rich Types Reference

### coordinates (PostgreSQL POINT)

**Used in**: PublicAddress, Location

**YAML**:
```yaml
coordinates:
  type: coordinates
  nullable: true
  description: "Geographic coordinates (latitude, longitude) stored as PostgreSQL POINT"
```

**Generated SQL**:
```sql
coordinates POINT

-- Spatial index
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address USING GIST (coordinates);
```

**GraphQL**:
```graphql
type Coordinates {
  lat: Float!
  lng: Float!
}
```

### email

**Used in**: Contact

**YAML**:
```yaml
email_address:
  type: email
  nullable: false
  description: "Primary email address (unique)"
```

**Generated SQL**:
```sql
email_address TEXT NOT NULL CHECK (
  email_address ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)
```

### phone (E.164 format)

**Used in**: Contact

**YAML**:
```yaml
office_phone:
  type: phone
  description: "Landline or office phone number"
```

**Generated SQL**:
```sql
office_phone TEXT CHECK (
  office_phone ~ '^\+[1-9]\d{1,14}$'
)
```

### money

**Used in**: Price

**YAML**:
```yaml
amount:
  type: money
  nullable: false
  description: "Price amount with currency semantics"
```

**Generated SQL**:
```sql
amount NUMERIC(19,4) NOT NULL
```

### url

**Used in**: AddressDatasource

**YAML**:
```yaml
website:
  type: url
  nullable: true
  description: "Website URL of the address data source"
```

**Generated SQL**:
```sql
website TEXT CHECK (
  website ~ '^https?://'
)
```

---

## Key Entities Overview

### PublicAddress (geo)

Geolocated addresses with:
- PostgreSQL POINT coordinates (rich type)
- References to Country, PostalCode, AdministrativeUnit
- National address ID support (French BAN, UK UPRN, etc.)
- Geocoding and validation actions

### Contact (crm)

Individual contact information with:
- Email (rich type with validation)
- Phone numbers (rich type with E.164 format)
- Localization (language, locale, timezone)
- Organization relationship

### Organization (crm)

Hierarchical organizations with:
- Company information (legal identifiers, VAT)
- Domain information (for email domains)
- Industry classification
- Parent-child hierarchy support

### Location (geo)

Hierarchical physical locations with:
- PostgreSQL POINT coordinates (rich type)
- Accessibility features (elevator, stairs)
- Physical dimensions (for space planning)
- Parent-child hierarchy support

### Price (commerce)

Time-based pricing with:
- Money amount (rich type)
- Currency reference
- Validity period (start_date, end_date)
- Contract and organization relationships

---

## Breaking Changes in v1.1.0

See `CHANGELOG.md` for complete migration guide.

### PublicAddress

**Changed**: `latitude`/`longitude` → `coordinates`

**Migration**:
```sql
ALTER TABLE common.tb_public_address ADD COLUMN coordinates POINT;
UPDATE common.tb_public_address
  SET coordinates = POINT(longitude, latitude);
ALTER TABLE common.tb_public_address
  DROP COLUMN latitude,
  DROP COLUMN longitude;

CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address USING GIST (coordinates);
```

### Contact

**Changed**: Email and phone fields now use rich types with validation

**Migration**: Existing data must conform to email/phone formats

---

## Integration Checklist

For printoptim_backend_poc integration:

- [ ] Review stdlib entities for patterns and conventions
- [ ] Identify which stdlib entities are useful for POC
- [ ] Decide on import/extend vs reference approach
- [ ] Update Team A parser to support `import`/`extends` syntax (if using)
- [ ] Update Team B schema generator to handle rich types
- [ ] Update Team C actions generator to handle stdlib actions
- [ ] Update Team D GraphQL generator to handle stdlib entities
- [ ] Test rich type generation (coordinates, email, phone, money, url)
- [ ] Test hierarchical entity generation (Organization, Location)
- [ ] Validate generated SQL matches expectations
- [ ] Validate generated GraphQL schemas

---

## Next Steps

1. **Review**: Browse stdlib entities for patterns
2. **Test**: Try generating SQL from stdlib entities
3. **Integrate**: Use stdlib as reference for POC implementation
4. **Contribute**: Improve stdlib based on POC learnings

---

## Support

- **stdlib Source**: `/home/lionel/code/printoptim_specql/stdlib/`
- **Version**: 1.1.0
- **Quality**: Battle-tested from PrintOptim production
- **Documentation**: See `README.md` and `docs/rich_types.md`

---

**stdlib is ready for integration!** 🚀
