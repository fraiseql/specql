# Team A: Rich Types Implementation - SpecQL Parser Extension

**Epic**: Add FraiseQL Rich Type Support to SpecQL Parser
**Timeline**: Week 2, Days 1-2 (parallel with schema generation work)
**Complexity**: Medium (extends existing parser)

---

## 🎯 Objective

Extend the SpecQL parser to recognize and validate FraiseQL rich types (email, url, phone, ipAddress, coordinates, etc.) in field definitions.

**Success Criteria**:
- ✅ Parser recognizes 20+ rich type keywords
- ✅ Validates rich type syntax
- ✅ Stores type metadata in AST
- ✅ Backward compatible with existing types (text, integer, etc.)
- ✅ 95%+ test coverage
- ✅ Zero breaking changes to existing functionality

---

## 📋 PHASE 1: Type Registry & Validation

**Duration**: 2 hours

### 🔴 RED Phase: Write Failing Tests

**Test File**: `tests/unit/core/test_rich_types.py`

```python
import pytest
from src.core.specql_parser import SpecQLParser
from src.core.type_registry import TypeRegistry, FRAISEQL_RICH_TYPES


def test_parse_email_type():
    """Test: Parse email rich type"""
    yaml_content = """
entity: Contact
fields:
  email: email
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Expected: email field with rich type
    assert "email" in entity.fields
    email_field = entity.fields["email"]
    assert email_field.type == "email"
    assert email_field.is_rich_type() is True
    assert email_field.get_postgres_type() == "TEXT"


def test_parse_multiple_rich_types():
    """Test: Parse multiple different rich types"""
    yaml_content = """
entity: Contact
fields:
  email: email
  website: url
  phone: phoneNumber
  ip_address: ipAddress
  mac_address: macAddress
  location: coordinates
  price: money
  birth_date: date
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Expected: all fields parsed with correct types
    assert entity.fields["email"].type == "email"
    assert entity.fields["website"].type == "url"
    assert entity.fields["phone"].type == "phoneNumber"
    assert entity.fields["ip_address"].type == "ipAddress"
    assert entity.fields["mac_address"].type == "macAddress"
    assert entity.fields["location"].type == "coordinates"
    assert entity.fields["price"].type == "money"
    assert entity.fields["birth_date"].type == "date"

    # All should be recognized as rich types
    for field_name, field_def in entity.fields.items():
        assert field_def.is_rich_type() is True


def test_parse_rich_type_with_nullable():
    """Test: Rich types with nullable modifier"""
    yaml_content = """
entity: Contact
fields:
  email: email!        # NOT NULL
  website: url         # nullable
"""
    entity = SpecQLParser().parse_string(yaml_content)

    assert entity.fields["email"].nullable is False
    assert entity.fields["website"].nullable is True


def test_parse_rich_type_with_default():
    """Test: Rich types with default values"""
    yaml_content = """
entity: Settings
fields:
  theme_color: color = '#000000'
  default_url: url = 'https://example.com'
"""
    entity = SpecQLParser().parse_string(yaml_content)

    assert entity.fields["theme_color"].default == "#000000"
    assert entity.fields["default_url"].default == "https://example.com"


def test_parse_complex_money_type():
    """Test: Money type with currency metadata"""
    yaml_content = """
entity: Product
fields:
  price: money(currency=USD, precision=2)
"""
    entity = SpecQLParser().parse_string(yaml_content)

    price_field = entity.fields["price"]
    assert price_field.type == "money"
    assert price_field.type_metadata["currency"] == "USD"
    assert price_field.type_metadata["precision"] == 2


def test_backward_compatibility_with_basic_types():
    """Test: Existing basic types still work"""
    yaml_content = """
entity: Contact
fields:
  name: text
  age: integer
  active: boolean
  metadata: jsonb
  company: ref(Company)
  tags: list(text)
  status: enum(active, inactive)
"""
    entity = SpecQLParser().parse_string(yaml_content)

    # Basic types should NOT be rich types
    assert entity.fields["name"].is_rich_type() is False
    assert entity.fields["age"].is_rich_type() is False
    assert entity.fields["active"].is_rich_type() is False

    # ref, list, enum should still work
    assert entity.fields["company"].type == "ref"
    assert entity.fields["tags"].type == "list"
    assert entity.fields["status"].type == "enum"


def test_invalid_rich_type_raises_error():
    """Test: Unknown type raises validation error"""
    yaml_content = """
entity: Contact
fields:
  mystery: unknownType
"""

    with pytest.raises(ValueError) as exc_info:
        SpecQLParser().parse_string(yaml_content)

    assert "Unknown type: unknownType" in str(exc_info.value)


def test_type_registry_completeness():
    """Test: Type registry contains all FraiseQL types"""
    registry = TypeRegistry()

    # Verify all expected types are present
    expected_types = [
        "email", "url", "phone", "phoneNumber",
        "ipAddress", "macAddress", "markdown", "html",
        "money", "percentage",
        "date", "datetime", "time", "duration",
        "coordinates", "latitude", "longitude",
        "image", "file", "color",
        "uuid", "slug"
    ]

    for expected_type in expected_types:
        assert registry.is_rich_type(expected_type) is True
        assert registry.get_postgres_type(expected_type) is not None
```

**Run Tests**:
```bash
uv run pytest tests/unit/core/test_rich_types.py -v
# Expected: FAILED (not implemented)
```

---

### 🟢 GREEN Phase: Minimal Implementation

**Step 1: Create Type Registry**

**File**: `src/core/type_registry.py`

```python
"""
FraiseQL Rich Type Registry
Maps SpecQL rich types to PostgreSQL storage types and GraphQL scalars
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional


@dataclass
class TypeMetadata:
    """Metadata for a rich type"""
    specql_name: str
    postgres_type: str
    graphql_scalar: str
    description: str
    validation_pattern: Optional[str] = None


class TypeRegistry:
    """Registry of FraiseQL rich types and their mappings"""

    def __init__(self):
        self._types = self._build_type_registry()

    def _build_type_registry(self) -> Dict[str, TypeMetadata]:
        """Build the complete type registry"""
        return {
            # String-based types
            "email": TypeMetadata(
                specql_name="email",
                postgres_type="TEXT",
                graphql_scalar="Email",
                description="Valid email address",
                validation_pattern=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
            ),
            "url": TypeMetadata(
                specql_name="url",
                postgres_type="TEXT",
                graphql_scalar="Url",
                description="Valid URL",
                validation_pattern=r"^https?://"
            ),
            "phone": TypeMetadata(
                specql_name="phone",
                postgres_type="TEXT",
                graphql_scalar="PhoneNumber",
                description="Phone number (E.164 format)",
                validation_pattern=r"^\+?[1-9]\d{1,14}$"
            ),
            "phoneNumber": TypeMetadata(
                specql_name="phoneNumber",
                postgres_type="TEXT",
                graphql_scalar="PhoneNumber",
                description="Phone number (E.164 format)",
                validation_pattern=r"^\+?[1-9]\d{1,14}$"
            ),
            "ipAddress": TypeMetadata(
                specql_name="ipAddress",
                postgres_type="INET",
                graphql_scalar="IpAddress",
                description="IPv4 or IPv6 address"
            ),
            "macAddress": TypeMetadata(
                specql_name="macAddress",
                postgres_type="MACADDR",
                graphql_scalar="MacAddress",
                description="MAC address"
            ),
            "markdown": TypeMetadata(
                specql_name="markdown",
                postgres_type="TEXT",
                graphql_scalar="Markdown",
                description="Markdown formatted text"
            ),
            "html": TypeMetadata(
                specql_name="html",
                postgres_type="TEXT",
                graphql_scalar="Html",
                description="HTML content"
            ),

            # Numeric types
            "money": TypeMetadata(
                specql_name="money",
                postgres_type="NUMERIC(19,4)",
                graphql_scalar="Money",
                description="Monetary value"
            ),
            "percentage": TypeMetadata(
                specql_name="percentage",
                postgres_type="NUMERIC(5,2)",
                graphql_scalar="Percentage",
                description="Percentage value (0-100)"
            ),

            # Date/Time types
            "date": TypeMetadata(
                specql_name="date",
                postgres_type="DATE",
                graphql_scalar="Date",
                description="Date (YYYY-MM-DD)"
            ),
            "datetime": TypeMetadata(
                specql_name="datetime",
                postgres_type="TIMESTAMPTZ",
                graphql_scalar="DateTime",
                description="Timestamp with timezone"
            ),
            "time": TypeMetadata(
                specql_name="time",
                postgres_type="TIME",
                graphql_scalar="Time",
                description="Time of day"
            ),
            "duration": TypeMetadata(
                specql_name="duration",
                postgres_type="INTERVAL",
                graphql_scalar="Duration",
                description="Time duration"
            ),

            # Geographic types
            "coordinates": TypeMetadata(
                specql_name="coordinates",
                postgres_type="POINT",
                graphql_scalar="Coordinates",
                description="Geographic coordinates (lat/lng)"
            ),
            "latitude": TypeMetadata(
                specql_name="latitude",
                postgres_type="NUMERIC(10,8)",
                graphql_scalar="Latitude",
                description="Latitude (-90 to 90)"
            ),
            "longitude": TypeMetadata(
                specql_name="longitude",
                postgres_type="NUMERIC(11,8)",
                graphql_scalar="Longitude",
                description="Longitude (-180 to 180)"
            ),

            # Media types
            "image": TypeMetadata(
                specql_name="image",
                postgres_type="TEXT",
                graphql_scalar="Image",
                description="Image URL or path"
            ),
            "file": TypeMetadata(
                specql_name="file",
                postgres_type="TEXT",
                graphql_scalar="File",
                description="File URL or path"
            ),
            "color": TypeMetadata(
                specql_name="color",
                postgres_type="TEXT",
                graphql_scalar="Color",
                description="Color (hex code)",
                validation_pattern=r"^#[0-9A-Fa-f]{6}$"
            ),

            # Identifier types
            "uuid": TypeMetadata(
                specql_name="uuid",
                postgres_type="UUID",
                graphql_scalar="UUID",
                description="Universally unique identifier"
            ),
            "slug": TypeMetadata(
                specql_name="slug",
                postgres_type="TEXT",
                graphql_scalar="Slug",
                description="URL-friendly identifier",
                validation_pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
            ),

            # JSON types
            "json": TypeMetadata(
                specql_name="json",
                postgres_type="JSONB",
                graphql_scalar="JSON",
                description="JSON object"
            ),
        }

    def is_rich_type(self, type_name: str) -> bool:
        """Check if type is a FraiseQL rich type"""
        return type_name in self._types

    def get_postgres_type(self, type_name: str) -> str:
        """Get PostgreSQL storage type for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            raise ValueError(f"Unknown rich type: {type_name}")
        return metadata.postgres_type

    def get_graphql_scalar(self, type_name: str) -> str:
        """Get GraphQL scalar name for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            raise ValueError(f"Unknown rich type: {type_name}")
        return metadata.graphql_scalar

    def get_validation_pattern(self, type_name: str) -> Optional[str]:
        """Get regex validation pattern for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            return None
        return metadata.validation_pattern

    def get_all_rich_types(self) -> Set[str]:
        """Get set of all rich type names"""
        return set(self._types.keys())


# Global singleton instance
_type_registry = TypeRegistry()

# Convenience constants
FRAISEQL_RICH_TYPES = _type_registry.get_all_rich_types()


def get_type_registry() -> TypeRegistry:
    """Get the global type registry instance"""
    return _type_registry
```

---

**Step 2: Update FieldDefinition**

**File**: `src/core/ast_models.py`

```python
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from src.core.type_registry import get_type_registry


@dataclass
class FieldDefinition:
    """Parsed field definition with rich type support"""

    name: str
    type: str  # NOW SUPPORTS: text, integer, email, url, phone, coordinates, etc.
    nullable: bool = True
    default: Optional[Any] = None

    # Type metadata (for complex types like money(currency='USD'))
    type_metadata: Optional[Dict[str, Any]] = None

    # For enum fields
    values: Optional[List[str]] = None

    # For ref fields
    target_entity: Optional[str] = None

    # For list fields
    item_type: Optional[str] = None

    def is_rich_type(self) -> bool:
        """Check if this field uses a FraiseQL rich type"""
        registry = get_type_registry()
        return registry.is_rich_type(self.type)

    def get_postgres_type(self) -> str:
        """Get underlying PostgreSQL storage type"""
        registry = get_type_registry()

        # Rich types
        if self.is_rich_type():
            return registry.get_postgres_type(self.type)

        # Basic types
        basic_type_map = {
            "text": "TEXT",
            "integer": "INTEGER",
            "boolean": "BOOLEAN",
            "jsonb": "JSONB",
            "timestamp": "TIMESTAMPTZ",
        }

        return basic_type_map.get(self.type, "TEXT")

    def get_graphql_scalar(self) -> str:
        """Get GraphQL scalar type name"""
        registry = get_type_registry()

        # Rich types
        if self.is_rich_type():
            scalar = registry.get_graphql_scalar(self.type)
            return f"{scalar}!" if not self.nullable else scalar

        # Basic types
        basic_scalar_map = {
            "text": "String",
            "integer": "Int",
            "boolean": "Boolean",
            "jsonb": "JSON",
        }

        scalar = basic_scalar_map.get(self.type, "String")
        return f"{scalar}!" if not self.nullable else scalar

    def get_validation_pattern(self) -> Optional[str]:
        """Get regex validation pattern (if applicable)"""
        if not self.is_rich_type():
            return None

        registry = get_type_registry()
        return registry.get_validation_pattern(self.type)
```

---

**Step 3: Update Parser**

**File**: `src/core/specql_parser.py`

```python
import yaml
import re
from typing import Dict, Any
from src.core.ast_models import Entity, FieldDefinition
from src.core.type_registry import get_type_registry


class SpecQLParser:
    """Parses SpecQL YAML with rich type support"""

    def __init__(self):
        self.type_registry = get_type_registry()

    def parse_string(self, yaml_content: str) -> Entity:
        """Parse YAML string into Entity AST"""
        data = yaml.safe_load(yaml_content)
        return self._parse_entity(data)

    def parse_file(self, yaml_path: str) -> Entity:
        """Parse YAML file into Entity AST"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return self._parse_entity(data)

    def _parse_entity(self, data: Dict[str, Any]) -> Entity:
        """Parse entity definition"""
        entity = Entity(
            name=data.get("entity"),
            schema=data.get("schema", "public"),
            description=data.get("description", "")
        )

        # Parse fields
        if "fields" in data:
            entity.fields = self._parse_fields(data["fields"])

        # Parse actions, agents, etc. (existing code)
        # ...

        return entity

    def _parse_fields(self, fields_data: Dict[str, Any]) -> Dict[str, FieldDefinition]:
        """Parse field definitions with rich type support"""
        fields = {}

        for field_name, field_spec in fields_data.items():
            fields[field_name] = self._parse_field(field_name, field_spec)

        return fields

    def _parse_field(self, field_name: str, field_spec: Any) -> FieldDefinition:
        """Parse a single field definition"""

        # Handle simple string type: "email: email"
        if isinstance(field_spec, str):
            return self._parse_simple_field(field_name, field_spec)

        # Handle dict with options: "email: {type: email, nullable: false}"
        elif isinstance(field_spec, dict):
            return self._parse_complex_field(field_name, field_spec)

        else:
            raise ValueError(f"Invalid field spec for {field_name}: {field_spec}")

    def _parse_simple_field(self, field_name: str, type_spec: str) -> FieldDefinition:
        """Parse simple field type string"""

        # Check for nullable marker: "email!"
        nullable = True
        if type_spec.endswith("!"):
            nullable = False
            type_spec = type_spec[:-1]

        # Check for default value: "color = '#000000'"
        default = None
        if " = " in type_spec:
            type_spec, default_str = type_spec.split(" = ", 1)
            default = default_str.strip().strip("'\"")

        # Parse type with metadata: "money(currency=USD)"
        type_name, type_metadata = self._parse_type_with_metadata(type_spec)

        # Validate type exists
        self._validate_type(type_name)

        return FieldDefinition(
            name=field_name,
            type=type_name,
            nullable=nullable,
            default=default,
            type_metadata=type_metadata
        )

    def _parse_complex_field(self, field_name: str, field_dict: Dict[str, Any]) -> FieldDefinition:
        """Parse complex field definition with explicit options"""

        type_spec = field_dict.get("type")
        if not type_spec:
            raise ValueError(f"Missing 'type' for field {field_name}")

        type_name, type_metadata = self._parse_type_with_metadata(type_spec)

        # Validate type
        self._validate_type(type_name)

        return FieldDefinition(
            name=field_name,
            type=type_name,
            nullable=field_dict.get("nullable", True),
            default=field_dict.get("default"),
            type_metadata=type_metadata
        )

    def _parse_type_with_metadata(self, type_spec: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """Parse type with optional metadata: money(currency=USD, precision=2)"""

        # Check for metadata: "money(currency=USD)"
        match = re.match(r"(\w+)\((.*)\)", type_spec)
        if match:
            type_name = match.group(1)
            metadata_str = match.group(2)

            # Parse metadata key=value pairs
            metadata = {}
            for pair in metadata_str.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")

                    # Try to parse as number
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string

                    metadata[key] = value

            return type_name, metadata

        # No metadata, just type name
        return type_spec, None

    def _validate_type(self, type_name: str) -> None:
        """Validate that type is recognized"""

        # Check rich types
        if self.type_registry.is_rich_type(type_name):
            return

        # Check basic types
        basic_types = {"text", "integer", "boolean", "jsonb", "timestamp", "uuid"}
        if type_name in basic_types:
            return

        # Check special types
        if type_name in {"ref", "list", "enum"}:
            return

        # Unknown type
        raise ValueError(
            f"Unknown type: {type_name}. "
            f"Supported types: {', '.join(sorted(basic_types | self.type_registry.get_all_rich_types()))}"
        )
```

---

### 🔧 REFACTOR Phase

**Improvements**:

1. **Extract field parser to separate class**:

```python
class FieldParser:
    """Dedicated parser for field definitions"""

    def __init__(self, type_registry: TypeRegistry):
        self.type_registry = type_registry

    def parse(self, field_name: str, field_spec: Any) -> FieldDefinition:
        """Parse field definition"""
        # Cleaner separation of concerns
```

2. **Add type validation helper**:

```python
class TypeValidator:
    """Validates type specifications"""

    def validate_type_spec(self, type_spec: str) -> bool:
        """Validate type specification is well-formed"""
        # Validate syntax, metadata format, etc.
```

3. **Improve error messages**:

```python
def _validate_type(self, type_name: str) -> None:
    """Validate type with helpful error messages"""
    if not self._is_valid_type(type_name):
        similar = self._find_similar_types(type_name)
        suggestion = f" Did you mean: {', '.join(similar)}?" if similar else ""
        raise ValueError(f"Unknown type: {type_name}.{suggestion}")
```

---

### ✅ QA Phase

```bash
# Run all tests
uv run pytest tests/unit/core/test_rich_types.py -v

# Test backward compatibility
uv run pytest tests/unit/core/test_specql_parser.py -v

# Type checking
uv run mypy src/core/

# Coverage
uv run pytest tests/unit/core/ --cov=src/core/ --cov-report=term-missing
# Target: 95%+
```

---

## 📋 PHASE 2: Integration with Existing Code

**Duration**: 1 hour

### Update Existing Tests

Ensure existing tests still pass with new type system:

```bash
# All Team A tests should still pass
make teamA-test
```

### Add Rich Type Examples

**File**: `entities/examples/contact_with_rich_types.yaml`

```yaml
entity: Contact
schema: crm
description: "Contact with FraiseQL rich types"

fields:
  # Rich types
  email: email!
  website: url
  phone: phoneNumber
  avatar: image

  # Basic types (backward compatibility)
  first_name: text!
  last_name: text!
  notes: text

  # Relationships
  company: ref(Company)

  # Enums
  status: enum(lead, qualified, customer)

actions:
  - name: create_contact
    steps:
      # Rich types auto-validate!
      - insert: Contact
```

---

## 📊 Acceptance Criteria

### Must Have
- ✅ Parse 20+ FraiseQL rich types
- ✅ Extract type metadata (e.g., `money(currency=USD)`)
- ✅ Validate unknown types with helpful errors
- ✅ Backward compatible with existing types
- ✅ All existing tests pass
- ✅ 95%+ test coverage
- ✅ Type safety with mypy

### Nice to Have
- ✅ Suggest similar types on typos ("Did you mean 'email'?")
- ✅ Documentation for each rich type
- ✅ IDE autocomplete support (via JSON schema)

---

## 🎯 Definition of Done

- [ ] `TypeRegistry` class created with all FraiseQL types
- [ ] `FieldDefinition.is_rich_type()` method works
- [ ] `FieldDefinition.get_postgres_type()` returns correct type
- [ ] `FieldDefinition.get_graphql_scalar()` returns correct scalar
- [ ] Parser recognizes all rich type syntax
- [ ] Parser validates unknown types
- [ ] Parser extracts type metadata
- [ ] All tests pass (new + existing)
- [ ] 95%+ code coverage
- [ ] Documentation updated
- [ ] Examples added
- [ ] Code reviewed
- [ ] Merged to main

---

## 📚 Reference

### FraiseQL Rich Types to Support

| Category | Types |
|----------|-------|
| **String** | email, url, phone, phoneNumber, markdown, html, slug |
| **Network** | ipAddress, macAddress |
| **Numeric** | money, percentage |
| **Date/Time** | date, datetime, time, duration |
| **Geographic** | coordinates, latitude, longitude |
| **Media** | image, file, color |
| **Identifiers** | uuid, slug |
| **Structured** | json |

### PostgreSQL Mappings

| Rich Type | PostgreSQL Type | Has Validation |
|-----------|----------------|----------------|
| email | TEXT | CHECK constraint |
| url | TEXT | CHECK constraint |
| ipAddress | INET | Built-in |
| macAddress | MACADDR | Built-in |
| money | NUMERIC(19,4) | None |
| coordinates | POINT | CHECK constraint |
| date | DATE | Built-in |
| uuid | UUID | Built-in |

---

**Team A: Parser extension ready to implement!** 🚀

This prompt provides everything Team A needs to add rich type support without breaking existing functionality.
