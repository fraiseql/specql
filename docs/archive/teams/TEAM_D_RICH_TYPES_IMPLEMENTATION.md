# Team D: Rich Types Implementation - FraiseQL Metadata Annotations

**Epic**: Add FraiseQL Rich Type Annotations
**Timeline**: Week 5, Days 1-2 (after Teams B & C complete)
**Complexity**: Low-Medium (annotation generation)

---

## 🎯 Objective

Generate FraiseQL `@fraiseql:field` comments that map rich types to GraphQL scalars, enabling FraiseQL to auto-discover and expose properly typed GraphQL fields.

**Success Criteria**:
- ✅ Generate correct scalar names for all rich types
- ✅ FraiseQL introspection discovers rich type scalars
- ✅ GraphQL schema includes typed fields (Email, Url, PhoneNumber, etc.)
- ✅ Nullable markers correct (!  for non-null)
- ✅ Field names properly camelCased
- ✅ All tests pass
- ✅ 95%+ test coverage

---

## 📋 PHASE 1: Rich Type to GraphQL Scalar Mapping

**Duration**: 2 hours

### 🔴 RED Phase: Write Failing Tests

**Test File**: `tests/unit/fraiseql/test_rich_type_annotations.py`

```python
import pytest
from src.generators.fraiseql.annotator import FraiseQLAnnotator
from src.core.ast_models import Entity, FieldDefinition


def test_email_field_annotation():
    """Test: Email field gets Email scalar"""
    field = FieldDefinition(name="email", type="email", nullable=False)
    entity = Entity(name="Contact", schema="crm", fields={"email": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    # Expected: @fraiseql:field with Email scalar
    assert "@fraiseql:field" in annotation
    assert "name=email" in annotation
    assert "type=Email!" in annotation  # Non-nullable
    assert "COMMENT ON COLUMN crm.tb_contact.email" in annotation


def test_nullable_url_field_annotation():
    """Test: Nullable URL field has no ! marker"""
    field = FieldDefinition(name="website", type="url", nullable=True)
    entity = Entity(name="Contact", schema="crm", fields={"website": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=Url" in annotation
    assert "type=Url!" not in annotation  # Should be nullable


def test_phone_number_field_annotation():
    """Test: phoneNumber type maps to PhoneNumber scalar"""
    field = FieldDefinition(name="phone", type="phoneNumber")
    entity = Entity(name="Contact", schema="crm", fields={"phone": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=PhoneNumber" in annotation


def test_ip_address_field_annotation():
    """Test: ipAddress type maps to IpAddress scalar"""
    field = FieldDefinition(name="ip_address", type="ipAddress")
    entity = Entity(name="Server", schema="infra", fields={"ip_address": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    # Field name should be camelCased
    assert "name=ipAddress" in annotation
    assert "type=IpAddress" in annotation


def test_coordinates_field_annotation():
    """Test: coordinates type maps to Coordinates scalar"""
    field = FieldDefinition(name="location", type="coordinates")
    entity = Entity(name="Place", fields={"location": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=Coordinates" in annotation


def test_money_field_annotation():
    """Test: money type maps to Money scalar"""
    field = FieldDefinition(name="price", type="money", nullable=False)
    entity = Entity(name="Product", fields={"price": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=Money!" in annotation


def test_mac_address_field_annotation():
    """Test: macAddress type maps to MacAddress scalar"""
    field = FieldDefinition(name="mac_address", type="macAddress")
    entity = Entity(name="Device", fields={"mac_address": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "name=macAddress" in annotation
    assert "type=MacAddress" in annotation


def test_color_field_annotation():
    """Test: color type maps to Color scalar"""
    field = FieldDefinition(name="theme_color", type="color")
    entity = Entity(name="Settings", fields={"theme_color": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "name=themeColor" in annotation
    assert "type=Color" in annotation


def test_slug_field_annotation():
    """Test: slug type maps to Slug scalar"""
    field = FieldDefinition(name="slug", type="slug")
    entity = Entity(name="Post", fields={"slug": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=Slug" in annotation


def test_markdown_field_annotation():
    """Test: markdown type maps to Markdown scalar"""
    field = FieldDefinition(name="content", type="markdown")
    entity = Entity(name="Post", fields={"content": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "type=Markdown" in annotation


def test_percentage_field_annotation():
    """Test: percentage type maps to Percentage scalar"""
    field = FieldDefinition(name="completion_rate", type="percentage")
    entity = Entity(name="Task", fields={"completion_rate": field})

    annotator = FraiseQLAnnotator()
    annotation = annotator.generate_field_annotation(field, entity)

    assert "name=completionRate" in annotation
    assert "type=Percentage" in annotation


def test_complete_entity_with_mixed_types():
    """Test: Entity with basic and rich types gets correct annotations"""
    entity = Entity(
        name="Contact",
        schema="crm",
        fields={
            "first_name": FieldDefinition(name="first_name", type="text", nullable=False),
            "email": FieldDefinition(name="email", type="email", nullable=False),
            "website": FieldDefinition(name="website", type="url"),
            "phone": FieldDefinition(name="phone", type="phoneNumber"),
            "age": FieldDefinition(name="age", type="integer"),
        }
    )

    annotator = FraiseQLAnnotator()
    annotations = annotator.generate_all_field_annotations(entity)

    # Check each field has correct annotation
    assert any("name=firstName" in a and "type=String!" in a for a in annotations)
    assert any("name=email" in a and "type=Email!" in a for a in annotations)
    assert any("name=website" in a and "type=Url" in a for a in annotations)
    assert any("name=phone" in a and "type=PhoneNumber" in a for a in annotations)
    assert any("name=age" in a and "type=Int" in a for a in annotations)


def test_backward_compatibility_basic_types():
    """Test: Basic types still get correct GraphQL scalars"""
    entity = Entity(
        name="Product",
        fields={
            "name": FieldDefinition(name="name", type="text"),
            "quantity": FieldDefinition(name="quantity", type="integer"),
            "active": FieldDefinition(name="active", type="boolean"),
        }
    )

    annotator = FraiseQLAnnotator()
    annotations = annotator.generate_all_field_annotations(entity)

    assert any("type=String" in a for a in annotations)
    assert any("type=Int" in a for a in annotations)
    assert any("type=Boolean" in a for a in annotations)
```

**Run Tests**:
```bash
uv run pytest tests/unit/fraiseql/test_rich_type_annotations.py -v
# Expected: FAILED (not implemented)
```

---

### 🟢 GREEN Phase: Minimal Implementation

**File**: `src/generators/fraiseql/scalar_mapper.py`

```python
"""
FraiseQL Scalar Mapper
Maps SpecQL rich types to FraiseQL/GraphQL scalar names
"""

from typing import Dict
from src.core.type_registry import get_type_registry


class ScalarMapper:
    """Maps rich types to GraphQL scalar names"""

    def __init__(self):
        self.type_registry = get_type_registry()
        self._scalar_map = self._build_scalar_map()

    def _build_scalar_map(self) -> Dict[str, str]:
        """Build mapping of SpecQL types to GraphQL scalars"""
        return {
            # String-based rich types
            "email": "Email",
            "url": "Url",
            "phone": "PhoneNumber",
            "phoneNumber": "PhoneNumber",
            "ipAddress": "IpAddress",
            "macAddress": "MacAddress",
            "markdown": "Markdown",
            "html": "Html",
            "slug": "Slug",
            "color": "Color",

            # Numeric rich types
            "money": "Money",
            "percentage": "Percentage",

            # Date/Time rich types
            "date": "Date",
            "datetime": "DateTime",
            "time": "Time",
            "duration": "Duration",

            # Geographic rich types
            "coordinates": "Coordinates",
            "latitude": "Latitude",
            "longitude": "Longitude",

            # Media rich types
            "image": "Image",
            "file": "File",

            # Identifier rich types
            "uuid": "UUID",

            # Structured rich types
            "json": "JSON",

            # Basic types (backward compatibility)
            "text": "String",
            "integer": "Int",
            "boolean": "Boolean",
            "jsonb": "JSON",
            "timestamp": "DateTime",
        }

    def get_graphql_scalar(self, specql_type: str, nullable: bool = True) -> str:
        """Get GraphQL scalar name for SpecQL type"""

        # Get base scalar name
        scalar = self._scalar_map.get(specql_type)

        if not scalar:
            # Unknown type, default to String
            scalar = "String"

        # Add non-null marker if needed
        if not nullable:
            scalar += "!"

        return scalar

    def is_rich_scalar(self, specql_type: str) -> bool:
        """Check if type maps to a FraiseQL rich scalar"""
        return self.type_registry.is_rich_type(specql_type)
```

---

**File**: `src/generators/fraiseql/annotator.py`

```python
"""
FraiseQL Annotator with Rich Type Support
"""

import re
from typing import List
from src.core.ast_models import Entity, FieldDefinition
from src.generators.fraiseql.scalar_mapper import ScalarMapper


class FraiseQLAnnotator:
    """Generates FraiseQL metadata annotations"""

    def __init__(self):
        self.scalar_mapper = ScalarMapper()

    def generate_field_annotation(self, field: FieldDefinition, entity: Entity) -> str:
        """Generate @fraiseql:field annotation for a field"""

        table_name = f"{entity.schema}.tb_{entity.name.lower()}"

        # Get GraphQL field name (camelCase)
        graphql_name = self._to_camel_case(field.name)

        # Get GraphQL scalar type
        graphql_type = self.scalar_mapper.get_graphql_scalar(field.type, field.nullable)

        return f"""
COMMENT ON COLUMN {table_name}.{field.name} IS
  '@fraiseql:field
   name={graphql_name}
   type={graphql_type}';
"""

    def generate_all_field_annotations(self, entity: Entity) -> List[str]:
        """Generate annotations for all fields in entity"""
        annotations = []

        for field_name, field_def in entity.fields.items():
            annotation = self.generate_field_annotation(field_def, entity)
            annotations.append(annotation)

        return annotations

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
```

---

### 🔧 REFACTOR Phase

**Improvements**:

1. **Add description support**:

```python
def generate_field_annotation(self, field: FieldDefinition, entity: Entity) -> str:
    """Generate annotation with optional description"""

    annotation_parts = [
        f"name={self._to_camel_case(field.name)}",
        f"type={self.scalar_mapper.get_graphql_scalar(field.type, field.nullable)}"
    ]

    # Add description if available
    if field.description:
        annotation_parts.append(f"description=\"{field.description}\"")

    annotation_text = "\n   ".join(annotation_parts)

    return f"""
COMMENT ON COLUMN {table_name}.{field.name} IS
  '@fraiseql:field
   {annotation_text}';
"""
```

2. **Add validation hints**:

```python
def generate_field_annotation_with_validation(self, field: FieldDefinition, entity: Entity) -> str:
    """Generate annotation with validation metadata"""

    if field.is_rich_type():
        validation_pattern = field.get_validation_pattern()
        if validation_pattern:
            # Include validation pattern in metadata
            annotation_parts.append(f"validation=\"{validation_pattern}\"")
```

---

### ✅ QA Phase

```bash
# Unit tests
uv run pytest tests/unit/fraiseql/test_rich_type_annotations.py -v

# Test with existing functionality
uv run pytest tests/unit/fraiseql/ -v

# Coverage
uv run pytest tests/unit/fraiseql/ --cov=src/generators/fraiseql/ --cov-report=term-missing
# Target: 95%+
```

---

## 📋 PHASE 2: Integration Testing with FraiseQL

**Duration**: 1 hour

### Integration Tests

**Test File**: `tests/integration/fraiseql/test_rich_scalars_discovery.py`

```python
import pytest
from src.cli.orchestrator import Orchestrator


@pytest.fixture
def fraiseql_schema():
    """Generate schema and run FraiseQL introspection"""
    # Generate complete migration from SpecQL
    orchestrator = Orchestrator()
    migration = orchestrator.generate_from_file("entities/examples/contact_with_rich_types.yaml")

    # Apply to test database
    apply_migration(migration)

    # Run FraiseQL introspection
    schema = run_fraiseql_introspection()

    return schema


def test_email_field_exposed_as_email_scalar(fraiseql_schema):
    """Integration: Email field uses Email scalar in GraphQL"""
    contact_type = fraiseql_schema["types"]["Contact"]

    # Check email field
    email_field = contact_type["fields"]["email"]
    assert email_field["type"] == "Email!"


def test_url_field_exposed_as_url_scalar(fraiseql_schema):
    """Integration: URL field uses Url scalar"""
    contact_type = fraiseql_schema["types"]["Contact"]

    website_field = contact_type["fields"]["website"]
    assert website_field["type"] == "Url"  # Nullable


def test_phone_field_exposed_as_phone_number_scalar(fraiseql_schema):
    """Integration: Phone field uses PhoneNumber scalar"""
    contact_type = fraiseql_schema["types"]["Contact"]

    phone_field = contact_type["fields"]["phone"]
    assert phone_field["type"] == "PhoneNumber"


def test_coordinates_field_exposed_as_coordinates_scalar(fraiseql_schema):
    """Integration: Coordinates field uses Coordinates scalar"""
    place_type = fraiseql_schema["types"]["Place"]

    location_field = place_type["fields"]["location"]
    assert location_field["type"] == "Coordinates"


def test_money_field_exposed_as_money_scalar(fraiseql_schema):
    """Integration: Money field uses Money scalar"""
    product_type = fraiseql_schema["types"]["Product"]

    price_field = product_type["fields"]["price"]
    assert price_field["type"] == "Money!"


def test_fraiseql_provides_custom_scalars(fraiseql_schema):
    """Integration: FraiseQL schema includes custom scalar definitions"""

    # Check that FraiseQL provides these scalars
    scalars = fraiseql_schema["scalars"]

    expected_scalars = [
        "Email", "Url", "PhoneNumber", "IpAddress", "MacAddress",
        "Coordinates", "Money", "Percentage", "Markdown", "Color", "Slug"
    ]

    for scalar in expected_scalars:
        assert scalar in scalars


def test_graphql_query_with_rich_types(fraiseql_schema):
    """Integration: GraphQL query returns properly typed data"""

    # Execute GraphQL query
    result = execute_graphql_query("""
        query {
          contact(id: "...") {
            email
            website
            phone
          }
        }
    """)

    # FraiseQL should validate and format rich types
    assert "@" in result["contact"]["email"]  # Email validated
    assert result["contact"]["website"].startswith("http")  # URL validated
```

---

## 📋 PHASE 3: Documentation Generation

**Duration**: 30 minutes

### Generate Rich Type Documentation

**File**: `src/generators/fraiseql/documentation_generator.py`

```python
class DocumentationGenerator:
    """Generates documentation for rich type fields"""

    def generate_field_documentation(self, entity: Entity) -> str:
        """Generate markdown documentation for entity fields"""

        docs = [f"# {entity.name} Fields\n"]

        for field_name, field_def in entity.fields.items():
            # Field name and type
            docs.append(f"## {field_name}")
            docs.append(f"**Type**: `{field_def.type}`")

            # GraphQL scalar
            if field_def.is_rich_type():
                scalar = self.scalar_mapper.get_graphql_scalar(field_def.type, field_def.nullable)
                docs.append(f"**GraphQL Scalar**: `{scalar}`")

                # Validation info
                pattern = field_def.get_validation_pattern()
                if pattern:
                    docs.append(f"**Validation**: `{pattern}`")

            # PostgreSQL type
            docs.append(f"**PostgreSQL**: `{field_def.get_postgres_type()}`")

            docs.append("")  # Blank line

        return "\n".join(docs)
```

---

## 📊 Acceptance Criteria

### Must Have
- ✅ All rich types map to correct GraphQL scalars
- ✅ Nullable markers correct (! for non-null)
- ✅ Field names properly camelCased
- ✅ FraiseQL discovers all rich type fields
- ✅ GraphQL schema includes typed scalars
- ✅ Backward compatible with basic types
- ✅ All tests pass (unit + integration)
- ✅ 95%+ test coverage

### Nice to Have
- ✅ Validation metadata in annotations
- ✅ Field descriptions in annotations
- ✅ Auto-generated documentation
- ✅ Examples in documentation

---

## 🎯 Definition of Done

- [ ] `ScalarMapper` class created
- [ ] `FraiseQLAnnotator` updated for rich types
- [ ] All rich types generate correct annotations
- [ ] FraiseQL introspection discovers rich scalars
- [ ] GraphQL queries work with typed fields
- [ ] Integration tests pass
- [ ] Backward compatibility verified
- [ ] 95%+ code coverage
- [ ] Documentation generated
- [ ] Examples added
- [ ] Code reviewed
- [ ] Merged to main

---

## 📚 Rich Type to GraphQL Scalar Mappings

| SpecQL Type | GraphQL Scalar | FraiseQL Provides |
|-------------|---------------|-------------------|
| email | Email | ✅ Yes |
| url | Url | ✅ Yes |
| phoneNumber | PhoneNumber | ✅ Yes |
| ipAddress | IpAddress | ✅ Yes |
| macAddress | MacAddress | ✅ Yes |
| coordinates | Coordinates | ✅ Yes |
| money | Money | ✅ Yes |
| percentage | Percentage | ✅ Yes |
| markdown | Markdown | ✅ Yes |
| color | Color | ✅ Yes |
| slug | Slug | ✅ Yes |
| date | Date | ✅ Yes |
| datetime | DateTime | ✅ Yes |
| uuid | UUID | ✅ Yes |

---

## 🔍 Example Output

### Input (SpecQL YAML)

```yaml
entity: Contact
  fields:
    email: email!
    website: url
    phone: phoneNumber
```

### Output (FraiseQL Annotations)

```sql
COMMENT ON COLUMN crm.tb_contact.email IS
  '@fraiseql:field
   name=email
   type=Email!';

COMMENT ON COLUMN crm.tb_contact.website IS
  '@fraiseql:field
   name=website
   type=Url';

COMMENT ON COLUMN crm.tb_contact.phone IS
  '@fraiseql:field
   name=phone
   type=PhoneNumber';
```

### Result (GraphQL Schema)

```graphql
type Contact {
  email: Email!
  website: Url
  phone: PhoneNumber
}

scalar Email
scalar Url
scalar PhoneNumber
```

---

**Team D: FraiseQL rich type annotations ready to implement!** 🚀

This provides everything Team D needs to generate proper FraiseQL annotations that map rich types to GraphQL scalars, completing the end-to-end rich type integration.
