# Metadata Layer for Stdlib Entities

**Status**: ✅ Complete
**Purpose**: Automatic FraiseQL metadata generation for rich types
**Mechanism**: `CommentGenerator` + `SCALAR_TYPES` registry

---

## Overview

Stdlib entities (like `Contact`, `Organization`, etc.) automatically get rich FraiseQL metadata through a layered approach:

1. **SCALAR_TYPES Registry** - Central definition of all rich types
2. **CommentGenerator** - Dynamic comment generation from registry
3. **Schema Orchestrator** - Integration into complete DDL

**Result**: Zero manual work, full GraphQL type safety! 🎉

---

## How It Works

### 1. SCALAR_TYPES Registry (Foundation)

```python
# src/core/scalar_types.py
SCALAR_TYPES = {
    "email": ScalarTypeDef(
        name="email",
        postgres_type=PostgreSQLType.TEXT,
        fraiseql_scalar_name="Email",  # ← GraphQL scalar name
        validation_pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Valid email address (RFC 5322 simplified)",  # ← Human description
        example="user@example.com",
    ),
    # ... 49 more rich types
}
```

**Key Properties**:
- `fraiseql_scalar_name`: Maps to GraphQL scalar (e.g., "Email" → `scalar Email`)
- `description`: Becomes GraphQL field description
- `validation_pattern`: Ensures data quality at database level

### 2. CommentGenerator (Dynamic Generation)

```python
# src/generators/comment_generator.py
class CommentGenerator:
    def generate_field_comment(self, field: FieldDefinition, entity: Entity) -> str:
        # 1. Check if field uses rich type
        scalar_def = get_scalar_type(field.type_name)

        if scalar_def:
            # Use registry description + validation note
            description = scalar_def.description
            if scalar_def.validation_pattern:
                description += " (validated format)"

            # Map to GraphQL scalar
            graphql_type = scalar_def.fraiseql_scalar_name
        else:
            # Fallback to basic types
            description = self._get_basic_description(field)
            graphql_type = self._map_basic_type(field)

        # Generate FraiseQL annotation
        return f"""COMMENT ON COLUMN {table}.{field.name} IS
'{description}

@fraiseql:field
name: {field.name}
type: {graphql_type}{"!" if not field.nullable else ""}
required: {str(not field.nullable).lower()}';"""
```

### 3. Schema Orchestrator Integration

```python
# src/generators/schema_orchestrator.py
def generate_complete_schema(self, entity: Entity) -> str:
    # Generate table DDL (includes basic comments)
    table_sql = self.table_gen.generate_table_ddl(entity)

    # Add rich type field comments
    field_comments = self.table_gen.generate_field_comments(entity)
    if field_comments:
        parts.append("-- Field Comments for FraiseQL\n" + "\n\n".join(field_comments))

    return "\n\n".join(parts)
```

---

## Generated Output Example

### Input: Stdlib Contact Entity

```yaml
# stdlib/crm/contact.yaml
entity: Contact
schema: tenant

fields:
  email_address: email!
  office_phone: phoneNumber
  website: url
```

### Generated PostgreSQL Comments

```sql
-- Basic table comment
COMMENT ON TABLE tenant.tb_contact IS
'Individual contact information linked to an organization.
Includes roles, communication details, and authentication.

@fraiseql:type
trinity: true';

-- Rich type field comments (auto-generated)
COMMENT ON COLUMN tenant.tb_contact.email_address IS
'Valid email address (RFC 5322 simplified) (validated format)

@fraiseql:field
name: email_address
type: Email!
required: true';

COMMENT ON COLUMN tenant.tb_contact.office_phone IS
'International phone number (E.164 format) (validated format)

@fraiseql:field
name: office_phone
type: PhoneNumber
required: false';

COMMENT ON COLUMN tenant.tb_contact.website IS
'Valid URL

@fraiseql:field
name: website
type: Url
required: false';
```

### FraiseQL Autodiscovery Result

```graphql
type Contact {
  """Individual contact information linked to an organization.
Includes roles, communication details, and authentication."""
  id: UUID!
  tenantId: UUID!

  """Valid email address (RFC 5322 simplified) (validated format)"""
  emailAddress: Email!

  """International phone number (E.164 format) (validated format)"""
  officePhone: PhoneNumber

  """Valid URL"""
  website: Url

  createdAt: DateTime!
  updatedAt: DateTime!
}
```

---

## Metadata Flow Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  SCALAR_TYPES   │───▶│ CommentGenerator │───▶│ PostgreSQL DDL  │
│   Registry      │    │                  │    │                 │
│ • descriptions  │    │ • Dynamic        │    │ • COMMENT ON    │
│ • GraphQL names │    │   comments       │    │   COLUMN        │
│ • validation    │    │ • FraiseQL       │    │ • @fraiseql:field│
└─────────────────┘    │   annotations    │    └─────────────────┘
                       └──────────────────┘             │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  FraiseQL       │───▶│ GraphQL Schema   │───▶│ TypeScript      │
│  Autodiscovery  │    │                  │    │ Types           │
│ • Introspects   │    │ • type Contact   │    │                 │
│   PostgreSQL    │    │ • scalar Email   │    │ interface       │
│ • Reads comments│    │ • field descs    │    │ Contact {       │
└─────────────────┘    └──────────────────┘    │   email: string │
                                                └─────────────────┘
```

---

## Key Benefits

### 1. Single Source of Truth
- **Registry**: One place defines rich type behavior
- **Automatic**: Descriptions, GraphQL names, validation all sync
- **DRY**: No duplication between database and API layers

### 2. Zero Maintenance Overhead
- **Add new type**: Update `SCALAR_TYPES` → Everything updates automatically
- **Change description**: Edit registry → GraphQL docs update instantly
- **New validation**: Add pattern → Database + GraphQL both enforce

### 3. Type Safety End-to-End
- **Database**: CHECK constraints validate on INSERT/UPDATE
- **GraphQL**: Custom scalars provide input validation
- **Frontend**: Generated TypeScript types prevent runtime errors

### 4. Developer Experience
- **GraphQL Playground**: Rich field descriptions from PostgreSQL comments
- **Auto-complete**: FraiseQL provides full schema introspection
- **Documentation**: Always up-to-date, no manual sync needed

---

## Testing the Metadata Layer

### Unit Tests
```bash
# Test CommentGenerator with rich types
uv run pytest tests/unit/generators/test_comment_generator.py -v

# Test SCALAR_TYPES registry
uv run pytest tests/unit/core/test_scalar_types.py -v
```

### Integration Tests
```bash
# End-to-end GraphQL generation
uv run pytest tests/integration/fraiseql/test_rich_type_graphql_generation.py -v

# Verify FraiseQL autodiscovery
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
```

### Manual Verification
```python
from src.core.scalar_types import get_scalar_type
from src.generators.comment_generator import CommentGenerator

# Verify registry has all types
assert len(SCALAR_TYPES) == 50

# Test comment generation
gen = CommentGenerator()
email_type = get_scalar_type("email")
comment = gen.generate_field_comment(email_field, contact_entity)

assert "Valid email address" in comment
assert "type: Email!" in comment
assert "@fraiseql:field" in comment
```

---

## Maintenance Guidelines

### Adding New Rich Types

1. **Add to SCALAR_TYPES**:
```python
"new_type": ScalarTypeDef(
    name="new_type",
    postgres_type=PostgreSQLType.TEXT,
    fraiseql_scalar_name="NewType",
    validation_pattern=r"...",
    description="Human readable description (validated format)",
    example="example value",
),
```

2. **Update tests**:
   - Add to `test_rich_type_scalar_mappings_complete`
   - Add to `test_postgresql_types_support_fraiseql_autodiscovery`
   - Add to `test_validation_patterns_produce_meaningful_comments`

3. **Verify integration**:
   - Run full test suite
   - Check GraphQL schema generation
   - Test with stdlib entity

### Updating Existing Types

1. **Modify SCALAR_TYPES entry**
2. **Run tests** to ensure no regressions
3. **Check GraphQL output** updates automatically

---

## Conclusion

The metadata layer provides a robust, automated system for rich type GraphQL integration:

✅ **Automatic**: Registry → Comments → GraphQL
✅ **Maintainable**: Single source of truth
✅ **Tested**: Comprehensive coverage
✅ **Extensible**: Easy to add new types

**Result**: Rich types "just work" in GraphQL with zero manual configuration! 🎉

---

**Status**: ✅ Complete
**Next**: Phase 6 - CLI Integration with Rich Types