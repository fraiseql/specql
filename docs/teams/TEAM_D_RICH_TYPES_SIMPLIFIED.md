# Team D: Rich Types Integration - Simplified FraiseQL Compatibility

**Epic**: Ensure FraiseQL Rich Type Compatibility
**Timeline**: Week 5, Day 1 (1-2 hours only!)
**Complexity**: Low (FraiseQL now handles most work automatically)

---

## 🎯 Objective (SIMPLIFIED!)

**MAJOR SIMPLIFICATION**: FraiseQL v1.3.4+ now automatically:
- ✅ Converts PostgreSQL `COMMENT ON` to GraphQL descriptions
- ✅ Discovers composite types and their fields
- ✅ Maps PostgreSQL types to GraphQL scalars

**Team D's New Role**: Verify compatibility and add minimal `@fraiseql:type` annotations where needed.

**Success Criteria**:
- ✅ FraiseQL discovers all rich type fields correctly
- ✅ GraphQL schema includes proper scalars (Email, Url, PhoneNumber, etc.)
- ✅ Field descriptions appear from PostgreSQL comments
- ✅ No manual annotation duplication needed
- ✅ Integration tests pass

---

## 📋 What Changed?

### Before (Original Team D Plan)
Team D had to manually generate extensive `@fraiseql:field` annotations:

```sql
COMMENT ON COLUMN crm.tb_contact.email IS
  '@fraiseql:field
   name=email
   type=Email!
   description="Email address (validated format)"';
```

### After (FraiseQL v1.3.4+)
PostgreSQL comments automatically become GraphQL descriptions:

```sql
-- Team B generates this
COMMENT ON COLUMN crm.tb_contact.email IS 'Email address (validated format) (required)';

-- FraiseQL automatically discovers and uses it!
```

**Result**: ~90% less work for Team D!

---

## 📋 PHASE 1: Verification & Compatibility Testing

**Duration**: 1-2 hours

### 🔴 RED Phase: Write Integration Tests

**Test File**: `tests/integration/fraiseql/test_rich_type_autodiscovery.py`

```python
import pytest
from src.cli.orchestrator import Orchestrator


@pytest.fixture
def generated_schema(test_db):
    """Generate complete schema from SpecQL and apply to test database"""

    # Generate from SpecQL with rich types
    orchestrator = Orchestrator()
    migration = orchestrator.generate_from_file(
        "entities/examples/contact_with_rich_types.yaml"
    )

    # Apply to test database
    cursor = test_db.cursor()
    cursor.execute(migration)
    test_db.commit()

    # Run FraiseQL introspection
    from fraiseql import FraiseQL

    fraiseql = FraiseQL(database_url="postgresql://localhost/test_specql")
    schema = fraiseql.introspect()

    return schema


def test_email_field_autodiscovered_as_email_scalar(generated_schema):
    """Test: FraiseQL discovers email type as Email scalar"""

    contact_type = generated_schema.get_type("Contact")
    assert contact_type is not None

    email_field = contact_type.get_field("email")
    assert email_field is not None
    assert email_field.type == "Email!"  # Non-nullable Email scalar


def test_email_field_has_description_from_comment(generated_schema):
    """Test: Field description comes from PostgreSQL COMMENT"""

    contact_type = generated_schema.get_type("Contact")
    email_field = contact_type.get_field("email")

    # Description should come from Team B's generated COMMENT
    assert "email address" in email_field.description.lower()
    assert "validated" in email_field.description.lower()


def test_url_field_autodiscovered_as_url_scalar(generated_schema):
    """Test: FraiseQL discovers url type as Url scalar"""

    contact_type = generated_schema.get_type("Contact")
    website_field = contact_type.get_field("website")

    assert website_field.type == "Url"  # Nullable Url scalar


def test_phone_field_autodiscovered_as_phone_number_scalar(generated_schema):
    """Test: FraiseQL discovers phoneNumber type"""

    contact_type = generated_schema.get_type("Contact")
    phone_field = contact_type.get_field("phone")

    assert phone_field.type == "PhoneNumber"


def test_coordinates_field_autodiscovered(generated_schema):
    """Test: FraiseQL discovers coordinates type"""

    place_type = generated_schema.get_type("Place")
    location_field = place_type.get_field("location")

    assert location_field.type == "Coordinates"


def test_money_field_autodiscovered(generated_schema):
    """Test: FraiseQL discovers money type"""

    product_type = generated_schema.get_type("Product")
    price_field = product_type.get_field("price")

    assert price_field.type == "Money!"


def test_all_fraiseql_scalars_available(generated_schema):
    """Test: FraiseQL provides all custom scalars"""

    expected_scalars = [
        "Email", "Url", "PhoneNumber", "IpAddress", "MacAddress",
        "Coordinates", "Money", "Percentage", "Markdown",
        "Color", "Slug", "Date", "DateTime"
    ]

    available_scalars = generated_schema.get_all_scalars()

    for scalar in expected_scalars:
        assert scalar in available_scalars, f"Missing scalar: {scalar}"


def test_graphql_query_with_rich_types(generated_schema, test_db):
    """Test: GraphQL queries work with rich type fields"""

    # Insert test data
    cursor = test_db.cursor()
    cursor.execute("""
        INSERT INTO crm.tb_contact (email, website, phone)
        VALUES ('test@example.com', 'https://example.com', '+1234567890')
        RETURNING id
    """)
    contact_id = cursor.fetchone()[0]
    test_db.commit()

    # Execute GraphQL query
    from fraiseql import FraiseQL

    fraiseql = FraiseQL(database_url="postgresql://localhost/test_specql")
    result = fraiseql.execute(f"""
        query {{
          contact(id: "{contact_id}") {{
            email
            website
            phone
          }}
        }}
    """)

    # Verify results
    assert result["data"]["contact"]["email"] == "test@example.com"
    assert result["data"]["contact"]["website"] == "https://example.com"
    assert result["data"]["contact"]["phone"] == "+1234567890"


def test_graphql_mutation_with_rich_types(generated_schema, test_db):
    """Test: GraphQL mutations validate rich types"""

    from fraiseql import FraiseQL

    fraiseql = FraiseQL(database_url="postgresql://localhost/test_specql")

    # Valid email should work
    result = fraiseql.execute("""
        mutation {
          createContact(input: {
            email: "valid@example.com"
            website: "https://example.com"
          }) {
            contact {
              email
            }
          }
        }
    """)

    assert result["data"]["createContact"]["contact"]["email"] == "valid@example.com"

    # Invalid email should fail (if FraiseQL validates input scalars)
    result = fraiseql.execute("""
        mutation {
          createContact(input: {
            email: "not-an-email"
          }) {
            contact {
              email
            }
          }
        }
    """)

    # Should either fail at GraphQL validation or database constraint
    assert result.get("errors") is not None or "error" in result["data"]["createContact"]
```

**Run Tests**:
```bash
uv run pytest tests/integration/fraiseql/test_rich_type_autodiscovery.py -v
# Expected: Should mostly pass (FraiseQL handles autodiscovery)
```

---

## 📋 PHASE 2: Add Minimal Annotations (If Needed)

**Duration**: 30 minutes

Only needed if FraiseQL requires explicit type hints for certain rich types.

### Check Which Types Need Explicit Annotations

**File**: `src/generators/fraiseql/compatibility_checker.py`

```python
"""
FraiseQL Compatibility Checker
Determines which rich types need explicit @fraiseql:type annotations
"""

from typing import List, Set
from src.core.type_registry import get_type_registry


class CompatibilityChecker:
    """Checks which rich types need explicit FraiseQL annotations"""

    def __init__(self):
        self.type_registry = get_type_registry()
        # Types that FraiseQL might not auto-discover
        self._needs_explicit_annotation = self._check_fraiseql_support()

    def _check_fraiseql_support(self) -> Set[str]:
        """Determine which types need explicit @fraiseql:type annotations"""

        # Most types are auto-discovered from PostgreSQL base types
        # Only add types here if testing reveals they need explicit hints

        return set()  # Empty for now - FraiseQL is smart!

    def needs_annotation(self, type_name: str) -> bool:
        """Check if type needs explicit @fraiseql:type annotation"""
        return type_name in self._needs_explicit_annotation

    def generate_type_annotation_if_needed(self, type_name: str) -> str:
        """Generate @fraiseql:type annotation only if needed"""

        if not self.needs_annotation(type_name):
            return ""  # FraiseQL auto-discovers it!

        # Generate explicit annotation
        return f"@fraiseql:type name={type_name.capitalize()}"
```

---

## 📋 PHASE 3: Documentation

**Duration**: 30 minutes

Document the FraiseQL integration for future reference.

**File**: `docs/fraiseql-integration.md`

```markdown
# FraiseQL Integration with SpecQL Rich Types

## Overview

SpecQL rich types seamlessly integrate with FraiseQL's autodiscovery system.
PostgreSQL comments and base types are automatically mapped to GraphQL scalars.

## How It Works

### 1. SpecQL Generates PostgreSQL Schema

```yaml
# SpecQL
entity: Contact
fields:
  email: email!
  website: url
```

↓

```sql
-- Team B generates
CREATE TABLE crm.tb_contact (
    email TEXT NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@...'),
    website TEXT CHECK (website ~* '^https?://...')
);

COMMENT ON COLUMN crm.tb_contact.email IS 'Email address (validated format) (required)';
COMMENT ON COLUMN crm.tb_contact.website IS 'URL/website address (validated format)';
```

### 2. FraiseQL Autodiscovery

FraiseQL introspects PostgreSQL:
- Reads base PostgreSQL types (TEXT, INET, etc.)
- Reads COMMENT ON statements
- Maps to appropriate GraphQL scalars

### 3. GraphQL Schema Generated

```graphql
type Contact {
  """Email address (validated format) (required)"""
  email: Email!

  """URL/website address (validated format)"""
  website: Url
}

scalar Email
scalar Url
```

## Rich Type Mappings

| SpecQL Type | PostgreSQL Type | GraphQL Scalar | Auto-Discovered |
|-------------|----------------|----------------|-----------------|
| email | TEXT + CHECK | Email | ✅ Yes |
| url | TEXT + CHECK | Url | ✅ Yes |
| phoneNumber | TEXT + CHECK | PhoneNumber | ✅ Yes |
| ipAddress | INET | IpAddress | ✅ Yes |
| macAddress | MACADDR | MacAddress | ✅ Yes |
| coordinates | POINT | Coordinates | ✅ Yes |
| money | NUMERIC(19,4) | Money | ✅ Yes |
| date | DATE | Date | ✅ Yes |
| datetime | TIMESTAMPTZ | DateTime | ✅ Yes |
| uuid | UUID | UUID | ✅ Yes |

## Benefits

- ✅ **Zero Configuration**: No manual annotations needed
- ✅ **Single Source of Truth**: PostgreSQL is the documentation source
- ✅ **Type Safety**: PostgreSQL validates + GraphQL type-checks
- ✅ **Rich Documentation**: GraphQL Playground shows field descriptions
- ✅ **Maintainability**: Update PostgreSQL comments, GraphQL updates automatically

## Testing

Integration tests verify:
1. All rich types are auto-discovered
2. Field descriptions come from PostgreSQL comments
3. GraphQL queries/mutations work correctly
4. Type validation works end-to-end

Run tests:
```bash
uv run pytest tests/integration/fraiseql/ -v
```
```

---

## 📊 Acceptance Criteria

### Must Have
- ✅ FraiseQL discovers all rich type fields
- ✅ GraphQL schema includes proper scalars
- ✅ Field descriptions from PostgreSQL comments
- ✅ Integration tests pass
- ✅ Documentation complete

### Nice to Have
- ✅ Performance benchmarks
- ✅ Examples in documentation
- ✅ Comparison with manual annotation approach

---

## 🎯 Definition of Done

- [ ] Integration tests written and passing
- [ ] Compatibility checker created (even if empty)
- [ ] FraiseQL autodiscovery verified for all rich types
- [ ] GraphQL queries work with rich type fields
- [ ] Documentation updated
- [ ] Examples added
- [ ] Code reviewed
- [ ] Merged to main

---

## 📚 Key Differences from Original Plan

### Original Team D Plan (Deprecated)
- **400+ lines** of annotation generation code
- Manual `@fraiseql:field` comments for every field
- Complex scalar mapping logic
- Extensive test suite for annotation correctness

### New Team D Plan (Simplified)
- **~200 lines** of integration tests
- Rely on FraiseQL autodiscovery
- Verify compatibility only
- Documentation-focused

**Time Savings**: ~6-7 hours → ~1-2 hours

---

## 🎉 Why This Is Better

### 1. Less Code to Maintain
- No annotation generation code
- No complex mapping logic
- Fewer tests needed (integration only)

### 2. Single Source of Truth
- PostgreSQL comments → GraphQL descriptions
- Database is the documentation source
- No duplication

### 3. Better FraiseQL Integration
- Uses FraiseQL's native autodiscovery
- Follows FraiseQL best practices
- Future-proof as FraiseQL improves

### 4. Cleaner Architecture
- Team B: Generate PostgreSQL (DDL + COMMENTS)
- Team D: Verify FraiseQL compatibility
- Clear separation of concerns

---

**Team D: FraiseQL compatibility verification ready!** 🚀

This simplified approach leverages FraiseQL's autodiscovery capabilities,
reducing Team D's work from ~8 hours to ~2 hours while providing better
integration and maintainability.
