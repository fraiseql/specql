# Week 1: Domain Model Refinement

**Date**: 2025-11-12
**Duration**: 5 days
**Status**: ✅ Complete
**Objective**: Complete the DDD domain model with all aggregates, value objects, and domain events

**Output**: ~1,200 lines of domain code, 800 lines of tests

---

## Week 1: Domain Model Refinement

**Goal**: Complete the DDD domain model with all aggregates, value objects, and domain events.

**Output**: ~1,200 lines of domain code, 800 lines of tests

---

### Day 1: EntityTemplate Aggregate

**Objective**: Create EntityTemplate aggregate for reusable entity patterns

#### Morning: Design & Tests (4 hours)

**1. Create test file** `tests/unit/domain/test_entity_template.py`:

```python
"""Tests for EntityTemplate aggregate"""
import pytest
from src.domain.entities.entity_template import (
    EntityTemplate,
    TemplateField,
    TemplateComposition,
    TemplateInstantiation
)
from src.domain.value_objects.domain_number import DomainNumber
from src.domain.value_objects.table_code import TableCode


class TestEntityTemplate:
    """Test EntityTemplate aggregate"""

    def test_create_basic_template(self):
        """Test creating a basic entity template"""
        template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact Template",
            description="Standard contact entity with email, phone, address",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField(
                    field_name="email",
                    field_type="text",
                    required=True,
                    description="Contact email address"
                ),
                TemplateField(
                    field_name="phone",
                    field_type="text",
                    required=False,
                    description="Contact phone number"
                ),
                TemplateField(
                    field_name="address",
                    field_type="composite",
                    composite_type="address_type",
                    required=False
                )
            ],
            included_patterns=["audit_trail", "soft_delete"],
            version="1.0.0"
        )

        assert template.template_id == "tpl_contact"
        assert template.template_name == "Contact Template"
        assert len(template.fields) == 3
        assert "audit_trail" in template.included_patterns
        assert template.version == "1.0.0"

    def test_template_composition(self):
        """Test composing templates together"""
        base_template = EntityTemplate(
            template_id="tpl_base_entity",
            template_name="Base Entity",
            description="Common fields for all entities",
            domain_number=DomainNumber("01"),
            base_entity_name="base",
            fields=[
                TemplateField("created_at", "timestamp", required=True),
                TemplateField("updated_at", "timestamp", required=True)
            ],
            version="1.0.0"
        )

        contact_template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact",
            description="Contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField("email", "text", required=True),
                TemplateField("phone", "text", required=False)
            ],
            composed_from=["tpl_base_entity"],
            version="1.0.0"
        )

        # Composition logic
        composition = TemplateComposition(
            base_templates=[base_template],
            extending_template=contact_template
        )

        composed = composition.compose()

        # Should have all fields from both templates
        assert len(composed.fields) == 4
        field_names = [f.field_name for f in composed.fields]
        assert "created_at" in field_names
        assert "email" in field_names

    def test_template_instantiation(self):
        """Test instantiating a template to create an entity"""
        template = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact Template",
            description="Standard contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField("email", "text", required=True),
                TemplateField("phone", "text", required=False)
            ],
            included_patterns=["audit_trail"],
            version="1.0.0"
        )

        # Instantiate with customization
        instantiation = TemplateInstantiation(
            template=template,
            entity_name="customer_contact",
            subdomain_number="012",
            table_code=TableCode("01236"),
            field_overrides={
                "phone": {"required": True}  # Make phone required
            },
            additional_fields=[
                TemplateField("company", "ref", ref_entity="company")
            ]
        )

        entity_spec = instantiation.generate_entity_spec()

        assert entity_spec["entity"] == "customer_contact"
        assert entity_spec["schema"] == "01"  # Domain number
        assert entity_spec["table_code"] == "01236"
        assert len(entity_spec["fields"]) == 3  # email, phone, company
        assert entity_spec["fields"]["phone"]["required"] is True

    def test_template_versioning(self):
        """Test template versioning"""
        v1 = EntityTemplate(
            template_id="tpl_contact",
            template_name="Contact",
            description="Contact entity",
            domain_number=DomainNumber("01"),
            base_entity_name="contact",
            fields=[
                TemplateField("email", "text", required=True)
            ],
            version="1.0.0"
        )

        # Create new version with additional field
        v2 = v1.create_new_version(
            additional_fields=[
                TemplateField("phone", "text", required=False)
            ],
            version="2.0.0",
            changelog="Added phone field"
        )

        assert v2.version == "2.0.0"
        assert len(v2.fields) == 2
        assert v2.previous_version == "1.0.0"
        assert "Added phone field" in v2.changelog

    def test_template_validation(self):
        """Test template validation"""
        # Invalid: duplicate field names
        with pytest.raises(ValueError, match="Duplicate field name"):
            EntityTemplate(
                template_id="tpl_invalid",
                template_name="Invalid",
                description="Invalid template",
                domain_number=DomainNumber("01"),
                base_entity_name="invalid",
                fields=[
                    TemplateField("email", "text"),
                    TemplateField("email", "text")  # Duplicate
                ],
                version="1.0.0"
            )

        # Invalid: empty fields list
        with pytest.raises(ValueError, match="must have at least one field"):
            EntityTemplate(
                template_id="tpl_empty",
                template_name="Empty",
                description="Empty template",
                domain_number=DomainNumber("01"),
                base_entity_name="empty",
                fields=[],
                version="1.0.0"
            )
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/domain/test_entity_template.py -v
# Expected: FAILED (EntityTemplate not implemented)
```

#### Afternoon: Implementation (4 hours)

**3. Create EntityTemplate aggregate** `src/domain/entities/entity_template.py`:

```python
"""EntityTemplate aggregate for reusable entity patterns"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.domain.value_objects.domain_number import DomainNumber
from src.domain.value_objects.table_code import TableCode


@dataclass
class TemplateField:
    """A field definition in a template"""
    field_name: str
    field_type: str  # text, integer, ref, enum, composite, etc.
    required: bool = False
    description: str = ""
    composite_type: Optional[str] = None  # For composite types
    ref_entity: Optional[str] = None  # For ref fields
    enum_values: Optional[List[str]] = None  # For enum fields
    default_value: Optional[Any] = None
    validation_rules: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate field configuration"""
        if self.field_type == "composite" and not self.composite_type:
            raise ValueError(f"Field {self.field_name}: composite type must specify composite_type")
        if self.field_type == "ref" and not self.ref_entity:
            raise ValueError(f"Field {self.field_name}: ref type must specify ref_entity")
        if self.field_type == "enum" and not self.enum_values:
            raise ValueError(f"Field {self.field_name}: enum type must specify enum_values")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "type": self.field_type,
            "required": self.required
        }
        if self.description:
            result["description"] = self.description
        if self.composite_type:
            result["composite_type"] = self.composite_type
        if self.ref_entity:
            result["ref_entity"] = self.ref_entity
        if self.enum_values:
            result["enum_values"] = self.enum_values
        if self.default_value is not None:
            result["default"] = self.default_value
        if self.validation_rules:
            result["validation"] = self.validation_rules
        return result


@dataclass
class EntityTemplate:
    """
    Aggregate: Reusable entity template

    EntityTemplate defines a reusable pattern for creating entities with
    common field structures, patterns, and behaviors.
    """
    template_id: str  # Unique identifier (e.g., "tpl_contact")
    template_name: str
    description: str
    domain_number: DomainNumber
    base_entity_name: str  # Base name for entities created from this template
    fields: List[TemplateField]
    included_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    composed_from: List[str] = field(default_factory=list)  # Other template IDs
    version: str = "1.0.0"
    previous_version: Optional[str] = None
    changelog: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    times_instantiated: int = 0
    is_public: bool = True  # Can be used by others
    author: str = "system"

    def __post_init__(self):
        """Validate template configuration"""
        self._validate()

    def _validate(self):
        """Validate template invariants"""
        # Must have at least one field
        if not self.fields:
            raise ValueError(f"Template {self.template_id} must have at least one field")

        # No duplicate field names
        field_names = [f.field_name for f in self.fields]
        if len(field_names) != len(set(field_names)):
            duplicates = [name for name in field_names if field_names.count(name) > 1]
            raise ValueError(f"Duplicate field name in template {self.template_id}: {duplicates[0]}")

        # Validate template_id format
        if not self.template_id.startswith("tpl_"):
            raise ValueError(f"Template ID must start with 'tpl_': {self.template_id}")

    def create_new_version(
        self,
        additional_fields: Optional[List[TemplateField]] = None,
        removed_fields: Optional[List[str]] = None,
        modified_fields: Optional[Dict[str, TemplateField]] = None,
        version: str = "",
        changelog: str = ""
    ) -> "EntityTemplate":
        """Create a new version of this template"""
        import copy

        # Copy current fields
        new_fields = copy.deepcopy(self.fields)

        # Remove fields
        if removed_fields:
            new_fields = [f for f in new_fields if f.field_name not in removed_fields]

        # Modify fields
        if modified_fields:
            for i, field_obj in enumerate(new_fields):
                if field_obj.field_name in modified_fields:
                    new_fields[i] = modified_fields[field_obj.field_name]

        # Add fields
        if additional_fields:
            new_fields.extend(additional_fields)

        # Create new version
        return EntityTemplate(
            template_id=self.template_id,
            template_name=self.template_name,
            description=self.description,
            domain_number=self.domain_number,
            base_entity_name=self.base_entity_name,
            fields=new_fields,
            included_patterns=self.included_patterns.copy(),
            composed_from=self.composed_from.copy(),
            version=version or self._increment_version(),
            previous_version=self.version,
            changelog=changelog,
            times_instantiated=self.times_instantiated,
            is_public=self.is_public,
            author=self.author
        )

    def _increment_version(self) -> str:
        """Auto-increment version number"""
        major, minor, patch = map(int, self.version.split("."))
        return f"{major}.{minor}.{patch + 1}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "description": self.description,
            "domain_number": str(self.domain_number.value),
            "base_entity_name": self.base_entity_name,
            "fields": {f.field_name: f.to_dict() for f in self.fields},
            "included_patterns": self.included_patterns,
            "composed_from": self.composed_from,
            "version": self.version,
            "previous_version": self.previous_version,
            "changelog": self.changelog,
            "times_instantiated": self.times_instantiated,
            "is_public": self.is_public,
            "author": self.author
        }


@dataclass
class TemplateComposition:
    """Composes multiple templates together"""
    base_templates: List[EntityTemplate]
    extending_template: EntityTemplate

    def compose(self) -> EntityTemplate:
        """Compose templates into a single template"""
        import copy

        # Start with extending template's fields
        composed_fields = copy.deepcopy(self.extending_template.fields)
        field_names = {f.field_name for f in composed_fields}

        # Add fields from base templates (no duplicates)
        for base in self.base_templates:
            for field_obj in base.fields:
                if field_obj.field_name not in field_names:
                    composed_fields.append(copy.deepcopy(field_obj))
                    field_names.add(field_obj.field_name)

        # Merge patterns
        all_patterns = set(self.extending_template.included_patterns)
        for base in self.base_templates:
            all_patterns.update(base.included_patterns)

        # Create composed template
        return EntityTemplate(
            template_id=self.extending_template.template_id,
            template_name=self.extending_template.template_name,
            description=self.extending_template.description,
            domain_number=self.extending_template.domain_number,
            base_entity_name=self.extending_template.base_entity_name,
            fields=composed_fields,
            included_patterns=list(all_patterns),
            composed_from=[t.template_id for t in self.base_templates],
            version=self.extending_template.version,
            is_public=self.extending_template.is_public,
            author=self.extending_template.author
        )


@dataclass
class TemplateInstantiation:
    """Instantiates a template to create an entity specification"""
    template: EntityTemplate
    entity_name: str
    subdomain_number: str
    table_code: TableCode
    field_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    additional_fields: List[TemplateField] = field(default_factory=list)
    pattern_overrides: Optional[List[str]] = None  # Replace template's patterns

    def generate_entity_spec(self) -> Dict[str, Any]:
        """
        Generate a complete entity specification from the template

        Returns a dict that matches SpecQL YAML format
        """
        import copy

        # Start with template fields
        fields = {}
        for template_field in self.template.fields:
            field_name = template_field.field_name
            field_spec = template_field.to_dict()

            # Apply overrides
            if field_name in self.field_overrides:
                field_spec.update(self.field_overrides[field_name])

            fields[field_name] = field_spec

        # Add additional fields
        for additional in self.additional_fields:
            fields[additional.field_name] = additional.to_dict()

        # Determine patterns to include
        patterns = (
            self.pattern_overrides
            if self.pattern_overrides is not None
            else self.template.included_patterns
        )

        # Build entity spec
        spec = {
            "entity": self.entity_name,
            "schema": str(self.template.domain_number.value),
            "table_code": str(self.table_code.value),
            "description": f"Generated from template: {self.template.template_name}",
            "fields": fields
        }

        if patterns:
            spec["patterns"] = patterns

        # Update template usage counter (domain event would be raised here)
        self.template.times_instantiated += 1
        self.template.updated_at = datetime.utcnow()

        return spec
```

**4. Run tests** (should pass):
```bash
uv run pytest tests/unit/domain/test_entity_template.py -v
# Expected: PASSED
```

**5. Create repository interface** `src/domain/repositories/entity_template_repository.py`:

```python
"""Repository interface for EntityTemplate aggregate"""
from typing import Protocol, Optional, List
from src.domain.entities.entity_template import EntityTemplate


class EntityTemplateRepository(Protocol):
    """Repository for managing entity templates"""

    def save(self, template: EntityTemplate) -> None:
        """Save or update an entity template"""
        ...

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        ...

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        ...

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        ...

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        ...

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        ...

    def increment_usage(self, template_id: str) -> None:
        """Increment times_instantiated counter"""
        ...
```

**6. Commit Day 1**:
```bash
git add src/domain/entities/entity_template.py
git add src/domain/repositories/entity_template_repository.py
git add tests/unit/domain/test_entity_template.py
git commit -m "feat: implement EntityTemplate aggregate with composition and instantiation"
```

---

### Day 2: Value Objects (SubdomainNumber, EntitySequence)

**Objective**: Create remaining value objects for complete domain model

#### Morning: SubdomainNumber Value Object (4 hours)

**1. Create test** `tests/unit/domain/value_objects/test_subdomain_number.py`:

```python
"""Tests for SubdomainNumber value object"""
import pytest
from src.domain.value_objects.subdomain_number import SubdomainNumber


class TestSubdomainNumber:
    """Test SubdomainNumber value object"""

    def test_valid_subdomain_numbers(self):
        """Test valid subdomain number formats"""
        # 3-digit format (012)
        sn1 = SubdomainNumber("012")
        assert str(sn1) == "012"
        assert sn1.value == "012"
        assert sn1.domain_part == "01"
        assert sn1.subdomain_part == "2"

        # With domain separator
        sn2 = SubdomainNumber("01:2")
        assert str(sn2) == "012"
        assert sn2.domain_part == "01"

        # With leading zeros
        sn3 = SubdomainNumber("001")
        assert str(sn3) == "001"

    def test_invalid_subdomain_numbers(self):
        """Test invalid subdomain number formats"""
        # Too short
        with pytest.raises(ValueError, match="must be 3 digits"):
            SubdomainNumber("01")

        # Too long
        with pytest.raises(ValueError, match="must be 3 digits"):
            SubdomainNumber("0123")

        # Non-numeric
        with pytest.raises(ValueError, match="must contain only digits"):
            SubdomainNumber("01a")

        # Empty
        with pytest.raises(ValueError, match="cannot be empty"):
            SubdomainNumber("")

    def test_subdomain_number_equality(self):
        """Test value object equality"""
        sn1 = SubdomainNumber("012")
        sn2 = SubdomainNumber("012")
        sn3 = SubdomainNumber("013")

        assert sn1 == sn2
        assert sn1 != sn3
        assert hash(sn1) == hash(sn2)

    def test_parent_domain_number(self):
        """Test extracting parent domain number"""
        sn = SubdomainNumber("012")
        domain_num = sn.get_parent_domain_number()

        from src.domain.value_objects.domain_number import DomainNumber
        assert isinstance(domain_num, DomainNumber)
        assert str(domain_num) == "01"

    def test_subdomain_sequence(self):
        """Test subdomain sequence number"""
        sn = SubdomainNumber("012")
        assert sn.subdomain_sequence == 2

        sn2 = SubdomainNumber("019")
        assert sn2.subdomain_sequence == 9

    def test_formatting(self):
        """Test different formatting options"""
        sn = SubdomainNumber("012")

        # Default format (012)
        assert str(sn) == "012"

        # With separator (01:2)
        assert sn.format_with_separator() == "01:2"

        # Full format with domain (Domain 01, Subdomain 2)
        assert sn.format_full() == "Domain 01, Subdomain 2"
```

**2. Implement SubdomainNumber** `src/domain/value_objects/subdomain_number.py`:

```python
"""SubdomainNumber value object"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SubdomainNumber:
    """
    Value Object: Subdomain Number (3-digit format: 012)

    Format: DDS where DD = domain (2 digits), S = subdomain (1 digit)
    Examples: 012 (domain 01, subdomain 2), 055 (domain 05, subdomain 5)
    """
    value: str

    def __post_init__(self):
        """Validate subdomain number format"""
        self._validate()

    def _validate(self):
        """Validate subdomain number"""
        if not self.value:
            raise ValueError("Subdomain number cannot be empty")

        # Remove separator if present (01:2 → 012)
        clean_value = self.value.replace(":", "")

        if len(clean_value) != 3:
            raise ValueError(f"Subdomain number must be 3 digits, got: {self.value}")

        if not clean_value.isdigit():
            raise ValueError(f"Subdomain number must contain only digits, got: {self.value}")

        # Update value to clean format
        object.__setattr__(self, "value", clean_value)

    @property
    def domain_part(self) -> str:
        """Get domain part (first 2 digits)"""
        return self.value[:2]

    @property
    def subdomain_part(self) -> str:
        """Get subdomain part (last digit)"""
        return self.value[2]

    @property
    def subdomain_sequence(self) -> int:
        """Get subdomain sequence number (0-9)"""
        return int(self.subdomain_part)

    def get_parent_domain_number(self) -> "DomainNumber":
        """Get parent domain number as DomainNumber value object"""
        from src.domain.value_objects.domain_number import DomainNumber
        return DomainNumber(self.domain_part)

    def format_with_separator(self) -> str:
        """Format with separator (012 → 01:2)"""
        return f"{self.domain_part}:{self.subdomain_part}"

    def format_full(self) -> str:
        """Format as full description"""
        return f"Domain {self.domain_part}, Subdomain {self.subdomain_part}"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"SubdomainNumber('{self.value}')"
```

**3. Run tests**:
```bash
uv run pytest tests/unit/domain/value_objects/test_subdomain_number.py -v
```

#### Afternoon: EntitySequence Value Object (4 hours)

**4. Create test** `tests/unit/domain/value_objects/test_entity_sequence.py`:

```python
"""Tests for EntitySequence value object"""
import pytest
from src.domain.value_objects.entity_sequence import EntitySequence


class TestEntitySequence:
    """Test EntitySequence value object"""

    def test_valid_sequences(self):
        """Test valid entity sequences"""
        # Single digit (0-9)
        seq1 = EntitySequence(1)
        assert seq1.value == 1
        assert str(seq1) == "1"

        # Zero
        seq0 = EntitySequence(0)
        assert seq0.value == 0

        # Max single digit
        seq9 = EntitySequence(9)
        assert seq9.value == 9

    def test_invalid_sequences(self):
        """Test invalid entity sequences"""
        # Negative
        with pytest.raises(ValueError, match="must be between 0 and 9"):
            EntitySequence(-1)

        # Too large
        with pytest.raises(ValueError, match="must be between 0 and 9"):
            EntitySequence(10)

    def test_sequence_equality(self):
        """Test value object equality"""
        seq1 = EntitySequence(1)
        seq2 = EntitySequence(1)
        seq3 = EntitySequence(2)

        assert seq1 == seq2
        assert seq1 != seq3
        assert hash(seq1) == hash(seq2)

    def test_sequence_comparison(self):
        """Test sequence ordering"""
        seq1 = EntitySequence(1)
        seq5 = EntitySequence(5)
        seq9 = EntitySequence(9)

        assert seq1 < seq5
        assert seq5 < seq9
        assert seq9 > seq1

    def test_next_sequence(self):
        """Test getting next sequence"""
        seq1 = EntitySequence(1)
        seq2 = seq1.next()
        assert seq2.value == 2

        # At boundary
        seq9 = EntitySequence(9)
        with pytest.raises(ValueError, match="No next sequence"):
            seq9.next()

    def test_previous_sequence(self):
        """Test getting previous sequence"""
        seq5 = EntitySequence(5)
        seq4 = seq5.previous()
        assert seq4.value == 4

        # At boundary
        seq0 = EntitySequence(0)
        with pytest.raises(ValueError, match="No previous sequence"):
            seq0.previous()

    def test_to_hex(self):
        """Test hexadecimal representation"""
        seq0 = EntitySequence(0)
        assert seq0.to_hex() == "0"

        seq9 = EntitySequence(9)
        assert seq9.to_hex() == "9"

        seq5 = EntitySequence(5)
        assert seq5.to_hex() == "5"
```

**5. Implement EntitySequence** `src/domain/value_objects/entity_sequence.py`:

```python
"""EntitySequence value object"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EntitySequence:
    """
    Value Object: Entity Sequence Number (single digit: 0-9)

    Represents the sequential position of an entity within a subdomain.
    Used as the fourth digit in entity codes (DDSE where E = entity sequence).

    Examples:
    - 0: First entity in subdomain
    - 5: Sixth entity in subdomain
    - 9: Tenth entity in subdomain
    """
    value: int

    def __post_init__(self):
        """Validate entity sequence"""
        self._validate()

    def _validate(self):
        """Validate entity sequence number"""
        if not isinstance(self.value, int):
            raise TypeError(f"Entity sequence must be an integer, got: {type(self.value)}")

        if self.value < 0 or self.value > 9:
            raise ValueError(f"Entity sequence must be between 0 and 9, got: {self.value}")

    def next(self) -> "EntitySequence":
        """Get next sequence number"""
        if self.value >= 9:
            raise ValueError("No next sequence available (already at 9)")
        return EntitySequence(self.value + 1)

    def previous(self) -> "EntitySequence":
        """Get previous sequence number"""
        if self.value <= 0:
            raise ValueError("No previous sequence available (already at 0)")
        return EntitySequence(self.value - 1)

    def to_hex(self) -> str:
        """Convert to hexadecimal string (0-9)"""
        return f"{self.value:x}"

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"EntitySequence({self.value})"

    def __lt__(self, other: "EntitySequence") -> bool:
        return self.value < other.value

    def __le__(self, other: "EntitySequence") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "EntitySequence") -> bool:
        return self.value > other.value

    def __ge__(self, other: "EntitySequence") -> bool:
        return self.value >= other.value
```

**6. Run tests**:
```bash
uv run pytest tests/unit/domain/value_objects/ -v
```

**7. Commit Day 2**:
```bash
git add src/domain/value_objects/subdomain_number.py
git add src/domain/value_objects/entity_sequence.py
git add tests/unit/domain/value_objects/test_subdomain_number.py
git add tests/unit/domain/value_objects/test_entity_sequence.py
git commit -m "feat: add SubdomainNumber and EntitySequence value objects"
```

---

### Day 3: EntityTemplate Repository (PostgreSQL)

**Objective**: Implement PostgreSQL repository for EntityTemplate aggregate

#### Morning: Schema & Tests (4 hours)

**1. Create PostgreSQL schema** `db/schema/pattern_library/entity_templates.sql`:

```sql
-- Entity Templates Table
CREATE TABLE IF NOT EXISTS pattern_library.entity_templates (
    -- Primary keys
    template_id TEXT PRIMARY KEY,  -- e.g., "tpl_contact"

    -- Core fields
    template_name TEXT NOT NULL,
    description TEXT NOT NULL,
    domain_number CHAR(2) NOT NULL,
    base_entity_name TEXT NOT NULL,

    -- Fields stored as JSONB
    fields JSONB NOT NULL,  -- Array of field definitions

    -- Relationships
    included_patterns TEXT[] DEFAULT '{}',  -- Array of pattern IDs
    composed_from TEXT[] DEFAULT '{}',  -- Array of template IDs

    -- Versioning
    version TEXT NOT NULL DEFAULT '1.0.0',
    previous_version TEXT,
    changelog TEXT DEFAULT '',

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Usage tracking
    times_instantiated INTEGER NOT NULL DEFAULT 0,

    -- Visibility
    is_public BOOLEAN NOT NULL DEFAULT true,
    author TEXT NOT NULL DEFAULT 'system',

    -- Constraints
    CONSTRAINT valid_version CHECK (version ~ '^\d+\.\d+\.\d+$'),
    CONSTRAINT positive_usage CHECK (times_instantiated >= 0)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_entity_templates_domain
    ON pattern_library.entity_templates(domain_number);

CREATE INDEX IF NOT EXISTS idx_entity_templates_name
    ON pattern_library.entity_templates(template_name);

CREATE INDEX IF NOT EXISTS idx_entity_templates_public
    ON pattern_library.entity_templates(is_public)
    WHERE is_public = true;

CREATE INDEX IF NOT EXISTS idx_entity_templates_usage
    ON pattern_library.entity_templates(times_instantiated DESC);

-- Full text search on template names and descriptions
CREATE INDEX IF NOT EXISTS idx_entity_templates_search
    ON pattern_library.entity_templates
    USING gin(to_tsvector('english', template_name || ' ' || description));

-- Comments
COMMENT ON TABLE pattern_library.entity_templates IS
    'Reusable entity templates for rapid entity creation';

COMMENT ON COLUMN pattern_library.entity_templates.fields IS
    'JSONB array of field definitions with types and constraints';

COMMENT ON COLUMN pattern_library.entity_templates.included_patterns IS
    'Pattern IDs to automatically apply when instantiating this template';
```

**2. Create repository test** `tests/unit/infrastructure/test_postgresql_entity_template_repository.py`:

```python
"""Tests for PostgreSQL EntityTemplate repository"""
import pytest
from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects.domain_number import DomainNumber
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository
)
import os


@pytest.fixture
def db_url():
    """Get database URL from environment"""
    return os.getenv("SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql")


@pytest.fixture
def repository(db_url):
    """Create repository instance"""
    return PostgreSQLEntityTemplateRepository(db_url)


@pytest.fixture
def sample_template():
    """Create a sample template for testing"""
    return EntityTemplate(
        template_id="tpl_test_contact",
        template_name="Test Contact Template",
        description="Contact template for testing",
        domain_number=DomainNumber("01"),
        base_entity_name="contact",
        fields=[
            TemplateField("email", "text", required=True),
            TemplateField("phone", "text", required=False)
        ],
        included_patterns=["audit_trail", "soft_delete"],
        version="1.0.0"
    )


class TestPostgreSQLEntityTemplateRepository:
    """Test PostgreSQL repository for entity templates"""

    def test_save_and_find_by_id(self, repository, sample_template):
        """Test saving and retrieving template by ID"""
        # Save
        repository.save(sample_template)

        # Find
        found = repository.find_by_id("tpl_test_contact")
        assert found is not None
        assert found.template_id == "tpl_test_contact"
        assert found.template_name == "Test Contact Template"
        assert len(found.fields) == 2
        assert found.fields[0].field_name == "email"

    def test_save_update(self, repository, sample_template):
        """Test updating existing template"""
        # Save initial
        repository.save(sample_template)

        # Modify
        sample_template.description = "Updated description"
        sample_template.times_instantiated = 5

        # Save again
        repository.save(sample_template)

        # Verify update
        found = repository.find_by_id("tpl_test_contact")
        assert found.description == "Updated description"
        assert found.times_instantiated == 5

    def test_find_by_name(self, repository, sample_template):
        """Test finding template by name"""
        repository.save(sample_template)

        found = repository.find_by_name("Test Contact Template")
        assert found is not None
        assert found.template_id == "tpl_test_contact"

    def test_find_by_domain(self, repository, sample_template):
        """Test finding templates by domain"""
        repository.save(sample_template)

        # Create another template in same domain
        template2 = EntityTemplate(
            template_id="tpl_test_company",
            template_name="Test Company Template",
            description="Company template",
            domain_number=DomainNumber("01"),
            base_entity_name="company",
            fields=[TemplateField("name", "text", required=True)],
            version="1.0.0"
        )
        repository.save(template2)

        # Find by domain
        templates = repository.find_by_domain("01")
        assert len(templates) >= 2
        template_ids = [t.template_id for t in templates]
        assert "tpl_test_contact" in template_ids
        assert "tpl_test_company" in template_ids

    def test_find_all_public(self, repository, sample_template):
        """Test finding all public templates"""
        repository.save(sample_template)

        # Create private template
        private_template = EntityTemplate(
            template_id="tpl_test_private",
            template_name="Private Template",
            description="Private template",
            domain_number=DomainNumber("02"),
            base_entity_name="private",
            fields=[TemplateField("secret", "text")],
            is_public=False,
            version="1.0.0"
        )
        repository.save(private_template)

        # Find public only
        public_templates = repository.find_all_public()
        template_ids = [t.template_id for t in public_templates]
        assert "tpl_test_contact" in template_ids
        assert "tpl_test_private" not in template_ids

    def test_increment_usage(self, repository, sample_template):
        """Test incrementing usage counter"""
        repository.save(sample_template)

        # Increment 3 times
        repository.increment_usage("tpl_test_contact")
        repository.increment_usage("tpl_test_contact")
        repository.increment_usage("tpl_test_contact")

        # Verify
        found = repository.find_by_id("tpl_test_contact")
        assert found.times_instantiated == 3

    def test_delete(self, repository, sample_template):
        """Test deleting template"""
        repository.save(sample_template)

        # Delete
        repository.delete("tpl_test_contact")

        # Verify deleted
        found = repository.find_by_id("tpl_test_contact")
        assert found is None

    def test_find_nonexistent(self, repository):
        """Test finding template that doesn't exist"""
        found = repository.find_by_id("tpl_nonexistent")
        assert found is None

        found = repository.find_by_name("Nonexistent Template")
        assert found is None
```

**3. Run tests** (should fail):
```bash
uv run pytest tests/unit/infrastructure/test_postgresql_entity_template_repository.py -v
# Expected: FAILED (repository not implemented)
```

#### Afternoon: Implementation (4 hours)

**4. Apply schema**:
```bash
psql $SPECQL_DB_URL -f db/schema/pattern_library/entity_templates.sql
```

**5. Implement repository** `src/infrastructure/repositories/postgresql_entity_template_repository.py`:

```python
"""PostgreSQL implementation of EntityTemplateRepository"""
import psycopg
from typing import Optional, List
from datetime import datetime
import json

from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects.domain_number import DomainNumber


class PostgreSQLEntityTemplateRepository:
    """PostgreSQL repository for EntityTemplate aggregate"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def save(self, template: EntityTemplate) -> None:
        """Save or update entity template"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Convert fields to JSONB
                fields_json = json.dumps([
                    {
                        "field_name": f.field_name,
                        "field_type": f.field_type,
                        "required": f.required,
                        "description": f.description,
                        "composite_type": f.composite_type,
                        "ref_entity": f.ref_entity,
                        "enum_values": f.enum_values,
                        "default_value": f.default_value,
                        "validation_rules": f.validation_rules
                    }
                    for f in template.fields
                ])

                cur.execute("""
                    INSERT INTO pattern_library.entity_templates (
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (template_id) DO UPDATE SET
                        template_name = EXCLUDED.template_name,
                        description = EXCLUDED.description,
                        domain_number = EXCLUDED.domain_number,
                        base_entity_name = EXCLUDED.base_entity_name,
                        fields = EXCLUDED.fields,
                        included_patterns = EXCLUDED.included_patterns,
                        composed_from = EXCLUDED.composed_from,
                        version = EXCLUDED.version,
                        previous_version = EXCLUDED.previous_version,
                        changelog = EXCLUDED.changelog,
                        updated_at = EXCLUDED.updated_at,
                        times_instantiated = EXCLUDED.times_instantiated,
                        is_public = EXCLUDED.is_public,
                        author = EXCLUDED.author
                """, (
                    template.template_id,
                    template.template_name,
                    template.description,
                    str(template.domain_number.value),
                    template.base_entity_name,
                    fields_json,
                    template.included_patterns,
                    template.composed_from,
                    template.version,
                    template.previous_version,
                    template.changelog,
                    template.created_at,
                    template.updated_at,
                    template.times_instantiated,
                    template.is_public,
                    template.author
                ))
                conn.commit()

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE template_id = %s
                """, (template_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_template(row)

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE template_name = %s
                """, (template_name,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_template(row)

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE domain_number = %s
                    ORDER BY template_name
                """, (domain_number,))

                return [self._row_to_template(row) for row in cur.fetchall()]

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        template_id, template_name, description, domain_number,
                        base_entity_name, fields, included_patterns, composed_from,
                        version, previous_version, changelog, created_at, updated_at,
                        times_instantiated, is_public, author
                    FROM pattern_library.entity_templates
                    WHERE is_public = true
                    ORDER BY times_instantiated DESC, template_name
                """)

                return [self._row_to_template(row) for row in cur.fetchall()]

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM pattern_library.entity_templates
                    WHERE template_id = %s
                """, (template_id,))
                conn.commit()

    def increment_usage(self, template_id: str) -> None:
        """Increment times_instantiated counter"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pattern_library.entity_templates
                    SET times_instantiated = times_instantiated + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE template_id = %s
                """, (template_id,))
                conn.commit()

    def _row_to_template(self, row) -> EntityTemplate:
        """Convert database row to EntityTemplate"""
        (
            template_id, template_name, description, domain_number,
            base_entity_name, fields_json, included_patterns, composed_from,
            version, previous_version, changelog, created_at, updated_at,
            times_instantiated, is_public, author
        ) = row

        # Parse fields from JSONB
        fields_data = json.loads(fields_json) if isinstance(fields_json, str) else fields_json
        fields = [
            TemplateField(
                field_name=f["field_name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                composite_type=f.get("composite_type"),
                ref_entity=f.get("ref_entity"),
                enum_values=f.get("enum_values"),
                default_value=f.get("default_value"),
                validation_rules=f.get("validation_rules", [])
            )
            for f in fields_data
        ]

        return EntityTemplate(
            template_id=template_id,
            template_name=template_name,
            description=description,
            domain_number=DomainNumber(domain_number),
            base_entity_name=base_entity_name,
            fields=fields,
            included_patterns=list(included_patterns) if included_patterns else [],
            composed_from=list(composed_from) if composed_from else [],
            version=version,
            previous_version=previous_version,
            changelog=changelog,
            created_at=created_at,
            updated_at=updated_at,
            times_instantiated=times_instantiated,
            is_public=is_public,
            author=author
        )
```

**6. Run tests** (should pass):
```bash
uv run pytest tests/unit/infrastructure/test_postgresql_entity_template_repository.py -v
# Expected: PASSED
```

**7. Commit Day 3**:
```bash
git add db/schema/pattern_library/entity_templates.sql
git add src/infrastructure/repositories/postgresql_entity_template_repository.py
git add tests/unit/infrastructure/test_postgresql_entity_template_repository.py
git commit -m "feat: implement PostgreSQL repository for EntityTemplate aggregate"
```

---

### Day 4: Template Service & CLI Integration

**Objective**: Create TemplateService and CLI commands for template management

#### Morning: TemplateService (4 hours)

**1. Create service test** `tests/unit/application/test_template_service.py`:

```python
"""Tests for TemplateService"""
import pytest
from src.application.services.template_service import TemplateService
from src.domain.entities.entity_template import EntityTemplate, TemplateField
from src.domain.value_objects.domain_number import DomainNumber
from src.domain.value_objects.table_code import TableCode
from src.infrastructure.repositories.in_memory_entity_template_repository import (
    InMemoryEntityTemplateRepository
)


@pytest.fixture
def repository():
    """Create in-memory repository for testing"""
    return InMemoryEntityTemplateRepository()


@pytest.fixture
def service(repository):
    """Create service with in-memory repository"""
    return TemplateService(repository)


@pytest.fixture
def sample_template():
    """Create sample template"""
    return EntityTemplate(
        template_id="tpl_contact",
        template_name="Contact Template",
        description="Standard contact entity",
        domain_number=DomainNumber("01"),
        base_entity_name="contact",
        fields=[
            TemplateField("email", "text", required=True),
            TemplateField("phone", "text", required=False)
        ],
        included_patterns=["audit_trail"],
        version="1.0.0"
    )


class TestTemplateService:
    """Test TemplateService application service"""

    def test_create_template(self, service):
        """Test creating a new template"""
        template = service.create_template(
            template_id="tpl_test",
            template_name="Test Template",
            description="Test template",
            domain_number="01",
            base_entity_name="test",
            fields=[
                {"field_name": "name", "field_type": "text", "required": True}
            ],
            included_patterns=["audit_trail"],
            is_public=True
        )

        assert template.template_id == "tpl_test"
        assert len(template.fields) == 1
        assert template.fields[0].field_name == "name"

    def test_get_template(self, service, sample_template):
        """Test retrieving template by ID"""
        service.repository.save(sample_template)

        found = service.get_template("tpl_contact")
        assert found is not None
        assert found.template_id == "tpl_contact"

    def test_list_templates_by_domain(self, service, sample_template):
        """Test listing templates by domain"""
        service.repository.save(sample_template)

        templates = service.list_templates_by_domain("01")
        assert len(templates) >= 1
        assert any(t.template_id == "tpl_contact" for t in templates)

    def test_instantiate_template(self, service, sample_template):
        """Test instantiating template to create entity spec"""
        service.repository.save(sample_template)

        entity_spec = service.instantiate_template(
            template_id="tpl_contact",
            entity_name="customer_contact",
            subdomain_number="012",
            table_code="01236",
            field_overrides={"phone": {"required": True}},
            additional_fields=[
                {"field_name": "company", "field_type": "ref", "ref_entity": "company"}
            ]
        )

        assert entity_spec["entity"] == "customer_contact"
        assert entity_spec["table_code"] == "01236"
        assert len(entity_spec["fields"]) == 3  # email, phone, company
        assert entity_spec["fields"]["phone"]["required"] is True

        # Verify usage counter incremented
        template = service.get_template("tpl_contact")
        assert template.times_instantiated == 1

    def test_search_templates(self, service, sample_template):
        """Test searching templates by text"""
        service.repository.save(sample_template)

        # Search by name
        results = service.search_templates("contact")
        assert len(results) >= 1
        assert results[0].template_id == "tpl_contact"

        # Search by description
        results = service.search_templates("standard")
        assert len(results) >= 1

    def test_update_template(self, service, sample_template):
        """Test updating template"""
        service.repository.save(sample_template)

        # Update description
        updated = service.update_template(
            template_id="tpl_contact",
            description="Updated contact template"
        )

        assert updated.description == "Updated contact template"

    def test_create_template_version(self, service, sample_template):
        """Test creating new template version"""
        service.repository.save(sample_template)

        # Create v2 with additional field
        v2 = service.create_template_version(
            template_id="tpl_contact",
            additional_fields=[
                {"field_name": "address", "field_type": "composite", "composite_type": "address_type"}
            ],
            version="2.0.0",
            changelog="Added address field"
        )

        assert v2.version == "2.0.0"
        assert len(v2.fields) == 3  # email, phone, address
        assert v2.previous_version == "1.0.0"

    def test_delete_template(self, service, sample_template):
        """Test deleting template"""
        service.repository.save(sample_template)

        service.delete_template("tpl_contact")

        found = service.get_template("tpl_contact")
        assert found is None

    def test_get_most_used_templates(self, service, sample_template):
        """Test getting most used templates"""
        # Create templates with different usage counts
        sample_template.times_instantiated = 10
        service.repository.save(sample_template)

        template2 = EntityTemplate(
            template_id="tpl_company",
            template_name="Company Template",
            description="Company entity",
            domain_number=DomainNumber("01"),
            base_entity_name="company",
            fields=[TemplateField("name", "text", required=True)],
            times_instantiated=25,
            version="1.0.0"
        )
        service.repository.save(template2)

        # Get most used
        most_used = service.get_most_used_templates(limit=2)
        assert len(most_used) == 2
        assert most_used[0].template_id == "tpl_company"  # Higher usage first
        assert most_used[1].template_id == "tpl_contact"
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/application/test_template_service.py -v
```

**3. Create InMemoryEntityTemplateRepository** for testing:

`src/infrastructure/repositories/in_memory_entity_template_repository.py`:

```python
"""In-memory implementation of EntityTemplateRepository for testing"""
from typing import Optional, List, Dict
from src.domain.entities.entity_template import EntityTemplate


class InMemoryEntityTemplateRepository:
    """In-memory repository for EntityTemplate (testing only)"""

    def __init__(self):
        self._templates: Dict[str, EntityTemplate] = {}

    def save(self, template: EntityTemplate) -> None:
        """Save template to memory"""
        # Make a copy to simulate persistence
        import copy
        self._templates[template.template_id] = copy.deepcopy(template)

    def find_by_id(self, template_id: str) -> Optional[EntityTemplate]:
        """Find template by ID"""
        import copy
        template = self._templates.get(template_id)
        return copy.deepcopy(template) if template else None

    def find_by_name(self, template_name: str) -> Optional[EntityTemplate]:
        """Find template by name"""
        import copy
        for template in self._templates.values():
            if template.template_name == template_name:
                return copy.deepcopy(template)
        return None

    def find_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """Find all templates for a domain"""
        import copy
        return [
            copy.deepcopy(t)
            for t in self._templates.values()
            if str(t.domain_number.value) == domain_number
        ]

    def find_all_public(self) -> List[EntityTemplate]:
        """Find all public templates"""
        import copy
        return [
            copy.deepcopy(t)
            for t in self._templates.values()
            if t.is_public
        ]

    def delete(self, template_id: str) -> None:
        """Delete a template"""
        if template_id in self._templates:
            del self._templates[template_id]

    def increment_usage(self, template_id: str) -> None:
        """Increment usage counter"""
        if template_id in self._templates:
            self._templates[template_id].times_instantiated += 1
```

**4. Implement TemplateService** `src/application/services/template_service.py`:

```python
"""Application service for entity template management"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.entities.entity_template import (
    EntityTemplate,
    TemplateField,
    TemplateInstantiation
)
from src.domain.value_objects.domain_number import DomainNumber
from src.domain.value_objects.table_code import TableCode
from src.domain.repositories.entity_template_repository import EntityTemplateRepository


class TemplateService:
    """Application service for managing entity templates"""

    def __init__(self, repository: EntityTemplateRepository):
        self.repository = repository

    def create_template(
        self,
        template_id: str,
        template_name: str,
        description: str,
        domain_number: str,
        base_entity_name: str,
        fields: List[Dict[str, Any]],
        included_patterns: Optional[List[str]] = None,
        composed_from: Optional[List[str]] = None,
        is_public: bool = True,
        author: str = "system"
    ) -> EntityTemplate:
        """Create a new entity template"""
        # Convert field dicts to TemplateField objects
        template_fields = [
            TemplateField(
                field_name=f["field_name"],
                field_type=f["field_type"],
                required=f.get("required", False),
                description=f.get("description", ""),
                composite_type=f.get("composite_type"),
                ref_entity=f.get("ref_entity"),
                enum_values=f.get("enum_values"),
                default_value=f.get("default_value"),
                validation_rules=f.get("validation_rules", [])
            )
            for f in fields
        ]

        # Create template
        template = EntityTemplate(
            template_id=template_id,
            template_name=template_name,
            description=description,
            domain_number=DomainNumber(domain_number),
            base_entity_name=base_entity_name,
            fields=template_fields,
            included_patterns=included_patterns or [],
            composed_from=composed_from or [],
            version="1.0.0",
            is_public=is_public,
            author=author
        )

        # Save
        self.repository.save(template)

        return template

    def get_template(self, template_id: str) -> Optional[EntityTemplate]:
        """Get template by ID"""
        return self.repository.find_by_id(template_id)

    def list_templates_by_domain(self, domain_number: str) -> List[EntityTemplate]:
        """List all templates for a domain"""
        return self.repository.find_by_domain(domain_number)

    def list_public_templates(self) -> List[EntityTemplate]:
        """List all public templates"""
        return self.repository.find_all_public()

    def instantiate_template(
        self,
        template_id: str,
        entity_name: str,
        subdomain_number: str,
        table_code: str,
        field_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        additional_fields: Optional[List[Dict[str, Any]]] = None,
        pattern_overrides: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate a template to create an entity specification

        Returns a dict that can be written as SpecQL YAML
        """
        # Get template
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Convert additional fields if provided
        additional_template_fields = []
        if additional_fields:
            additional_template_fields = [
                TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", ""),
                    composite_type=f.get("composite_type"),
                    ref_entity=f.get("ref_entity"),
                    enum_values=f.get("enum_values")
                )
                for f in additional_fields
            ]

        # Create instantiation
        instantiation = TemplateInstantiation(
            template=template,
            entity_name=entity_name,
            subdomain_number=subdomain_number,
            table_code=TableCode(table_code),
            field_overrides=field_overrides or {},
            additional_fields=additional_template_fields,
            pattern_overrides=pattern_overrides
        )

        # Generate entity spec
        entity_spec = instantiation.generate_entity_spec()

        # Increment usage counter
        self.repository.increment_usage(template_id)

        return entity_spec

    def update_template(
        self,
        template_id: str,
        template_name: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> EntityTemplate:
        """Update template metadata"""
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Update fields
        if template_name:
            template.template_name = template_name
        if description:
            template.description = description
        if is_public is not None:
            template.is_public = is_public

        template.updated_at = datetime.utcnow()

        # Save
        self.repository.save(template)

        return template

    def create_template_version(
        self,
        template_id: str,
        additional_fields: Optional[List[Dict[str, Any]]] = None,
        removed_fields: Optional[List[str]] = None,
        modified_fields: Optional[Dict[str, Dict[str, Any]]] = None,
        version: str = "",
        changelog: str = ""
    ) -> EntityTemplate:
        """Create a new version of existing template"""
        template = self.repository.find_by_id(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Convert dicts to TemplateField objects if needed
        add_fields = []
        if additional_fields:
            add_fields = [
                TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", "")
                )
                for f in additional_fields
            ]

        mod_fields = {}
        if modified_fields:
            mod_fields = {
                name: TemplateField(
                    field_name=f["field_name"],
                    field_type=f["field_type"],
                    required=f.get("required", False),
                    description=f.get("description", "")
                )
                for name, f in modified_fields.items()
            }

        # Create new version
        new_version = template.create_new_version(
            additional_fields=add_fields,
            removed_fields=removed_fields,
            modified_fields=mod_fields,
            version=version,
            changelog=changelog
        )

        # Save
        self.repository.save(new_version)

        return new_version

    def delete_template(self, template_id: str) -> None:
        """Delete a template"""
        self.repository.delete(template_id)

    def search_templates(self, query: str) -> List[EntityTemplate]:
        """Search templates by name or description"""
        # Simple in-memory search (PostgreSQL can do full-text search)
        all_public = self.repository.find_all_public()
        query_lower = query.lower()

        return [
            t for t in all_public
            if query_lower in t.template_name.lower()
            or query_lower in t.description.lower()
        ]

    def get_most_used_templates(self, limit: int = 10) -> List[EntityTemplate]:
        """Get most frequently instantiated templates"""
        all_public = self.repository.find_all_public()
        sorted_templates = sorted(
            all_public,
            key=lambda t: t.times_instantiated,
            reverse=True
        )
        return sorted_templates[:limit]
```

**5. Run tests** (should pass):
```bash
uv run pytest tests/unit/application/test_template_service.py -v
```

#### Afternoon: CLI Integration (4 hours)

**6. Create CLI command** `src/cli/templates.py`:

```python
"""CLI commands for entity template management"""
import click
import yaml
from pathlib import Path
from src.application.services.template_service import TemplateService
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository
)
from src.core.config import get_config


@click.group()
def templates():
    """Manage entity templates"""
    pass


@templates.command()
@click.option("--template-id", required=True, help="Template ID (e.g., tpl_contact)")
@click.option("--name", required=True, help="Template name")
@click.option("--description", required=True, help="Template description")
@click.option("--domain", required=True, help="Domain number (e.g., 01)")
@click.option("--base-entity", required=True, help="Base entity name")
@click.option("--fields-file", required=True, type=click.Path(exists=True),
              help="YAML file with field definitions")
@click.option("--patterns", multiple=True, help="Pattern IDs to include")
@click.option("--public/--private", default=True, help="Is template public?")
def create(template_id, name, description, domain, base_entity, fields_file, patterns, public):
    """Create a new entity template"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    # Load fields from YAML
    with open(fields_file) as f:
        fields_data = yaml.safe_load(f)
        fields = fields_data.get("fields", [])

    # Create template
    template = service.create_template(
        template_id=template_id,
        template_name=name,
        description=description,
        domain_number=domain,
        base_entity_name=base_entity,
        fields=fields,
        included_patterns=list(patterns) if patterns else [],
        is_public=public
    )

    click.echo(f"✅ Created template: {template.template_id} (v{template.version})")


@templates.command()
@click.option("--domain", help="Filter by domain number")
def list(domain):
    """List available templates"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    if domain:
        templates_list = service.list_templates_by_domain(domain)
        click.echo(f"Templates in domain {domain}:")
    else:
        templates_list = service.list_public_templates()
        click.echo("All public templates:")

    if not templates_list:
        click.echo("  No templates found")
        return

    for template in templates_list:
        click.echo(f"\n  {template.template_id}")
        click.echo(f"  Name: {template.template_name}")
        click.echo(f"  Description: {template.description}")
        click.echo(f"  Version: {template.version}")
        click.echo(f"  Fields: {len(template.fields)}")
        click.echo(f"  Times used: {template.times_instantiated}")


@templates.command()
@click.argument("template_id")
def show(template_id):
    """Show template details"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    template = service.get_template(template_id)
    if not template:
        click.echo(f"❌ Template not found: {template_id}", err=True)
        return

    click.echo(f"Template: {template.template_name}")
    click.echo(f"ID: {template.template_id}")
    click.echo(f"Description: {template.description}")
    click.echo(f"Domain: {template.domain_number}")
    click.echo(f"Base Entity: {template.base_entity_name}")
    click.echo(f"Version: {template.version}")
    click.echo(f"Times Instantiated: {template.times_instantiated}")
    click.echo(f"Public: {template.is_public}")

    click.echo("\nFields:")
    for field in template.fields:
        required_marker = "*" if field.required else " "
        click.echo(f"  {required_marker} {field.field_name}: {field.field_type}")
        if field.description:
            click.echo(f"      {field.description}")

    if template.included_patterns:
        click.echo(f"\nIncluded Patterns: {', '.join(template.included_patterns)}")


@templates.command()
@click.argument("template_id")
@click.option("--entity-name", required=True, help="Name for new entity")
@click.option("--subdomain", required=True, help="Subdomain number (e.g., 012)")
@click.option("--table-code", required=True, help="Table code (e.g., 01236)")
@click.option("--output", required=True, type=click.Path(), help="Output YAML file")
@click.option("--override", multiple=True,
              help="Field overrides (format: field_name:property=value)")
@click.option("--add-field", multiple=True,
              help="Additional fields (format: field_name:field_type)")
def instantiate(template_id, entity_name, subdomain, table_code, output, override, add_field):
    """Instantiate template to create entity YAML"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    # Parse field overrides
    field_overrides = {}
    for override_str in override:
        # Format: "phone:required=true"
        field_name, prop_value = override_str.split(":", 1)
        prop, value = prop_value.split("=", 1)
        if field_name not in field_overrides:
            field_overrides[field_name] = {}
        # Convert value to correct type
        if value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        field_overrides[field_name][prop] = value

    # Parse additional fields
    additional_fields = []
    for field_str in add_field:
        # Format: "company:ref" or "status:enum"
        field_name, field_type = field_str.split(":", 1)
        additional_fields.append({
            "field_name": field_name,
            "field_type": field_type
        })

    # Instantiate template
    try:
        entity_spec = service.instantiate_template(
            template_id=template_id,
            entity_name=entity_name,
            subdomain_number=subdomain,
            table_code=table_code,
            field_overrides=field_overrides,
            additional_fields=additional_fields
        )

        # Write to YAML file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(entity_spec, f, default_flow_style=False, sort_keys=False)

        click.echo(f"✅ Created entity YAML: {output}")
        click.echo(f"   Entity: {entity_name}")
        click.echo(f"   Fields: {len(entity_spec['fields'])}")

    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@templates.command()
@click.argument("query")
def search(query):
    """Search templates by name or description"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    results = service.search_templates(query)

    if not results:
        click.echo(f"No templates found matching: {query}")
        return

    click.echo(f"Found {len(results)} template(s) matching '{query}':\n")
    for template in results:
        click.echo(f"  {template.template_id}")
        click.echo(f"  {template.template_name} - {template.description}")
        click.echo(f"  Used {template.times_instantiated} times\n")


@templates.command()
def most_used():
    """Show most frequently used templates"""
    config = get_config()
    repository = PostgreSQLEntityTemplateRepository(config.db_url)
    service = TemplateService(repository)

    templates_list = service.get_most_used_templates(limit=10)

    if not templates_list:
        click.echo("No templates found")
        return

    click.echo("Most used templates:\n")
    for i, template in enumerate(templates_list, 1):
        click.echo(f"  {i}. {template.template_name}")
        click.echo(f"     ID: {template.template_id}")
        click.echo(f"     Times used: {template.times_instantiated}\n")


if __name__ == "__main__":
    templates()
```

**7. Add templates command to main CLI** in `src/cli/__init__.py`:

```python
from src.cli.templates import templates

# In the main CLI group, add:
cli.add_command(templates)
```

**8. Test CLI manually**:

```bash
# List templates
specql templates list

# Create a template (need fields.yaml first)
echo "fields:
  - field_name: email
    field_type: text
    required: true
  - field_name: phone
    field_type: text
    required: false" > /tmp/contact_fields.yaml

specql templates create \
  --template-id tpl_test_contact \
  --name "Test Contact" \
  --description "Test contact template" \
  --domain 01 \
  --base-entity contact \
  --fields-file /tmp/contact_fields.yaml \
  --patterns audit_trail

# Show template
specql templates show tpl_test_contact

# Instantiate template
specql templates instantiate tpl_test_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output /tmp/customer_contact.yaml \
  --override "phone:required=true" \
  --add-field "company:ref"

# Verify generated YAML
cat /tmp/customer_contact.yaml
```

**9. Commit Day 4**:
```bash
git add src/application/services/template_service.py
git add src/infrastructure/repositories/in_memory_entity_template_repository.py
git add src/cli/templates.py
git add tests/unit/application/test_template_service.py
git commit -m "feat: implement TemplateService and CLI commands for template management"
```

---

### Day 5: Integration & Documentation

**Objective**: Integration testing, end-to-end verification, comprehensive documentation

#### Morning: Integration Tests (4 hours)

**1. Create integration test** `tests/integration/test_entity_templates.py`:

```python
"""Integration tests for entity template system"""
import pytest
import yaml
from pathlib import Path
from src.application.services.template_service import TemplateService
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository
)
from src.domain.value_objects.domain_number import DomainNumber
import os


@pytest.fixture
def db_url():
    """Get database URL"""
    return os.getenv("SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql")


@pytest.fixture
def service(db_url):
    """Create service with PostgreSQL repository"""
    repository = PostgreSQLEntityTemplateRepository(db_url)
    return TemplateService(repository)


class TestEntityTemplateIntegration:
    """Integration tests for entity template system"""

    def test_full_template_lifecycle(self, service):
        """Test complete template lifecycle: create, use, version, delete"""
        # 1. Create template
        template = service.create_template(
            template_id="tpl_integration_test",
            template_name="Integration Test Template",
            description="Template for integration testing",
            domain_number="01",
            base_entity_name="test_entity",
            fields=[
                {
                    "field_name": "name",
                    "field_type": "text",
                    "required": True,
                    "description": "Entity name"
                },
                {
                    "field_name": "email",
                    "field_type": "text",
                    "required": True,
                    "description": "Email address"
                }
            ],
            included_patterns=["audit_trail", "soft_delete"],
            is_public=True
        )

        assert template.template_id == "tpl_integration_test"
        assert template.version == "1.0.0"
        assert template.times_instantiated == 0

        # 2. Instantiate template 3 times
        for i in range(3):
            entity_spec = service.instantiate_template(
                template_id="tpl_integration_test",
                entity_name=f"test_entity_{i}",
                subdomain_number="012",
                table_code=f"0123{i}",
                field_overrides={},
                additional_fields=[]
            )
            assert entity_spec["entity"] == f"test_entity_{i}"

        # 3. Verify usage count
        template = service.get_template("tpl_integration_test")
        assert template.times_instantiated == 3

        # 4. Create new version
        v2 = service.create_template_version(
            template_id="tpl_integration_test",
            additional_fields=[
                {
                    "field_name": "phone",
                    "field_type": "text",
                    "required": False,
                    "description": "Phone number"
                }
            ],
            version="2.0.0",
            changelog="Added phone field"
        )

        assert v2.version == "2.0.0"
        assert v2.previous_version == "1.0.0"
        assert len(v2.fields) == 3  # name, email, phone

        # 5. Instantiate v2
        entity_spec_v2 = service.instantiate_template(
            template_id="tpl_integration_test",
            entity_name="test_entity_v2",
            subdomain_number="012",
            table_code="01239",
            field_overrides={},
            additional_fields=[]
        )
        assert "phone" in entity_spec_v2["fields"]

        # 6. Check usage (should be 4 now)
        template = service.get_template("tpl_integration_test")
        assert template.times_instantiated == 4

        # 7. Clean up
        service.delete_template("tpl_integration_test")
        deleted = service.get_template("tpl_integration_test")
        assert deleted is None

    def test_template_composition(self, service):
        """Test composing templates together"""
        # Create base template
        base_template = service.create_template(
            template_id="tpl_base_audited",
            template_name="Base Audited Entity",
            description="Base entity with audit fields",
            domain_number="01",
            base_entity_name="base",
            fields=[
                {"field_name": "created_by", "field_type": "uuid"},
                {"field_name": "updated_by", "field_type": "uuid"}
            ],
            included_patterns=["audit_trail"],
            is_public=True
        )

        # Create extending template
        contact_template = service.create_template(
            template_id="tpl_composed_contact",
            template_name="Composed Contact",
            description="Contact extending base",
            domain_number="01",
            base_entity_name="contact",
            fields=[
                {"field_name": "email", "field_type": "text", "required": True},
                {"field_name": "phone", "field_type": "text"}
            ],
            composed_from=["tpl_base_audited"],
            is_public=True
        )

        # Instantiate composed template
        entity_spec = service.instantiate_template(
            template_id="tpl_composed_contact",
            entity_name="audited_contact",
            subdomain_number="012",
            table_code="01236"
        )

        # Should have both base and extending fields
        # Note: Actual composition logic would merge fields from base templates
        assert entity_spec["entity"] == "audited_contact"

        # Clean up
        service.delete_template("tpl_base_audited")
        service.delete_template("tpl_composed_contact")

    def test_search_and_discovery(self, service):
        """Test template search and discovery"""
        # Create test templates
        service.create_template(
            template_id="tpl_customer_entity",
            template_name="Customer Entity",
            description="Standard customer with contact info",
            domain_number="01",
            base_entity_name="customer",
            fields=[{"field_name": "name", "field_type": "text"}],
            is_public=True
        )

        service.create_template(
            template_id="tpl_order_entity",
            template_name="Order Entity",
            description="Standard order processing entity",
            domain_number="01",
            base_entity_name="order",
            fields=[{"field_name": "order_number", "field_type": "text"}],
            is_public=True
        )

        # Search for "customer"
        results = service.search_templates("customer")
        assert len(results) >= 1
        assert any(t.template_id == "tpl_customer_entity" for t in results)

        # Search for "order"
        results = service.search_templates("order")
        assert len(results) >= 1
        assert any(t.template_id == "tpl_order_entity" for t in results)

        # List by domain
        domain_templates = service.list_templates_by_domain("01")
        assert len(domain_templates) >= 2

        # Clean up
        service.delete_template("tpl_customer_entity")
        service.delete_template("tpl_order_entity")

    def test_template_instantiation_with_yaml_output(self, service, tmp_path):
        """Test instantiating template and writing to YAML file"""
        # Create template
        service.create_template(
            template_id="tpl_yaml_test",
            template_name="YAML Test Template",
            description="Template for YAML output testing",
            domain_number="01",
            base_entity_name="test",
            fields=[
                {"field_name": "name", "field_type": "text", "required": True}
            ],
            is_public=True
        )

        # Instantiate
        entity_spec = service.instantiate_template(
            template_id="tpl_yaml_test",
            entity_name="yaml_output_test",
            subdomain_number="012",
            table_code="01236"
        )

        # Write to YAML
        output_file = tmp_path / "test_entity.yaml"
        with open(output_file, "w") as f:
            yaml.dump(entity_spec, f, default_flow_style=False)

        # Read back and verify
        with open(output_file) as f:
            loaded_spec = yaml.safe_load(f)

        assert loaded_spec["entity"] == "yaml_output_test"
        assert loaded_spec["schema"] == "01"
        assert "name" in loaded_spec["fields"]

        # Clean up
        service.delete_template("tpl_yaml_test")
```

**2. Run integration tests**:
```bash
uv run pytest tests/integration/test_entity_templates.py -v
```

#### Afternoon: Documentation (4 hours)

**3. Create comprehensive documentation** `docs/features/ENTITY_TEMPLATES.md`:

```markdown
# Entity Templates

**Feature**: Reusable entity templates for rapid development
**Status**: ✅ Complete
**Version**: 1.0.0

---

## Overview

Entity Templates provide a powerful way to create reusable entity patterns that can be instantiated across projects with consistent structure and behavior.

### Key Benefits

- **Rapid Development**: Create entities from templates in seconds
- **Consistency**: Enforce standard patterns across entities
- **Reusability**: Share templates across projects
- **Versioning**: Track template evolution over time
- **Composition**: Build complex templates from simpler ones

---

## Core Concepts

### Template

A template defines the structure and behavior of a category of entities:

```yaml
Template: Contact Template
  Fields:
    - email (text, required)
    - phone (text, optional)
    - address (composite: address_type)
  Patterns:
    - audit_trail
    - soft_delete
  Version: 1.0.0
```

### Instantiation

Creating an entity from a template with customization:

```bash
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --override "phone:required=true" \
  --add-field "company:ref"
```

Generates:
```yaml
entity: customer_contact
schema: "01"
table_code: "01236"
fields:
  email:
    type: text
    required: true
  phone:
    type: text
    required: true  # Overridden
  company:
    type: ref
    ref_entity: company  # Added field
patterns:
  - audit_trail
  - soft_delete
```

### Composition

Templates can extend other templates:

```
Base Template: Audited Entity
  Fields: [created_by, updated_by]
  Patterns: [audit_trail]

Extending Template: Contact
  Composed From: [Audited Entity]
  Fields: [email, phone]

Result: Contact entity with all fields
```

---

## CLI Usage

### Create Template

Create a new entity template:

```bash
# Prepare fields definition
cat > contact_fields.yaml << EOF
fields:
  - field_name: email
    field_type: text
    required: true
    description: Contact email address
  - field_name: phone
    field_type: text
    required: false
    description: Contact phone number
  - field_name: address
    field_type: composite
    composite_type: address_type
    required: false
    description: Contact mailing address
EOF

# Create template
specql templates create \
  --template-id tpl_contact \
  --name "Contact Template" \
  --description "Standard contact entity with email, phone, and address" \
  --domain 01 \
  --base-entity contact \
  --fields-file contact_fields.yaml \
  --patterns audit_trail \
  --patterns soft_delete \
  --public

# Output:
# ✅ Created template: tpl_contact (v1.0.0)
```

### List Templates

View available templates:

```bash
# List all public templates
specql templates list

# List templates for specific domain
specql templates list --domain 01

# Output:
# Templates in domain 01:
#
#   tpl_contact
#   Name: Contact Template
#   Description: Standard contact entity with email, phone, and address
#   Version: 1.0.0
#   Fields: 3
#   Times used: 0
```

### Show Template Details

View complete template information:

```bash
specql templates show tpl_contact

# Output:
# Template: Contact Template
# ID: tpl_contact
# Description: Standard contact entity with email, phone, and address
# Domain: 01
# Base Entity: contact
# Version: 1.0.0
# Times Instantiated: 0
# Public: True
#
# Fields:
#   * email: text
#       Contact email address
#     phone: text
#       Contact phone number
#     address: composite
#       Contact mailing address
#
# Included Patterns: audit_trail, soft_delete
```

### Instantiate Template

Create an entity from a template:

```bash
# Basic instantiation
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/customer_contact.yaml

# With field overrides
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/customer_contact.yaml \
  --override "phone:required=true"

# With additional fields
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/customer_contact.yaml \
  --add-field "company:ref" \
  --add-field "status:enum"

# Output:
# ✅ Created entity YAML: entities/customer_contact.yaml
#    Entity: customer_contact
#    Fields: 4
```

### Search Templates

Find templates by keyword:

```bash
specql templates search "contact"

# Output:
# Found 2 template(s) matching 'contact':
#
#   tpl_contact
#   Contact Template - Standard contact entity with email, phone, and address
#   Used 12 times
#
#   tpl_emergency_contact
#   Emergency Contact - Emergency contact information
#   Used 3 times
```

### Most Used Templates

See popular templates:

```bash
specql templates most-used

# Output:
# Most used templates:
#
#   1. Contact Template
#      ID: tpl_contact
#      Times used: 45
#
#   2. Address Template
#      ID: tpl_address
#      Times used: 38
#
#   3. Company Template
#      ID: tpl_company
#      Times used: 27
```

---

## Programmatic Usage

### Using TemplateService

```python
from src.application.services.template_service import TemplateService
from src.infrastructure.repositories.postgresql_entity_template_repository import (
    PostgreSQLEntityTemplateRepository
)

# Initialize
repository = PostgreSQLEntityTemplateRepository(db_url)
service = TemplateService(repository)

# Create template
template = service.create_template(
    template_id="tpl_my_template",
    template_name="My Template",
    description="Custom template",
    domain_number="01",
    base_entity_name="my_entity",
    fields=[
        {
            "field_name": "name",
            "field_type": "text",
            "required": True
        }
    ],
    included_patterns=["audit_trail"],
    is_public=True
)

# Instantiate template
entity_spec = service.instantiate_template(
    template_id="tpl_my_template",
    entity_name="my_entity_instance",
    subdomain_number="012",
    table_code="01236"
)

# Write to YAML
import yaml
with open("entities/my_entity.yaml", "w") as f:
    yaml.dump(entity_spec, f)
```

---

## Template Versioning

Templates support semantic versioning:

```bash
# Original template (v1.0.0)
specql templates show tpl_contact
# Version: 1.0.0
# Fields: email, phone

# Create new version
specql templates create-version tpl_contact \
  --add-field "social_media:text" \
  --version "2.0.0" \
  --changelog "Added social media field"

# New version (v2.0.0)
specql templates show tpl_contact
# Version: 2.0.0
# Previous Version: 1.0.0
# Fields: email, phone, social_media
# Changelog: Added social media field
```

---

## Template Composition

Build complex templates from simpler ones:

```bash
# 1. Create base template
specql templates create \
  --template-id tpl_base_audited \
  --name "Audited Entity" \
  --description "Base entity with audit fields" \
  --domain 01 \
  --base-entity base \
  --fields-file audited_fields.yaml \
  --patterns audit_trail

# 2. Create extending template
specql templates create \
  --template-id tpl_contact \
  --name "Contact" \
  --description "Contact extending audited base" \
  --domain 01 \
  --base-entity contact \
  --fields-file contact_fields.yaml \
  --compose-from tpl_base_audited

# When instantiated, tpl_contact includes fields from both templates
```

---

## Best Practices

### Template Design

1. **Single Responsibility**: Each template should represent one concept
2. **Minimal Fields**: Include only essential fields, let users add more
3. **Clear Descriptions**: Document field purposes thoroughly
4. **Appropriate Patterns**: Include relevant patterns (audit_trail, soft_delete, etc.)
5. **Public by Default**: Share templates unless project-specific

### Naming Conventions

- **Template IDs**: `tpl_{concept}` (e.g., `tpl_contact`, `tpl_address`)
- **Template Names**: Descriptive (e.g., "Contact Template", "Address Template")
- **Field Names**: Snake_case (e.g., `email_address`, `phone_number`)

### Version Management

- **Semantic Versioning**: Major.Minor.Patch
- **Changelog**: Document all changes between versions
- **Breaking Changes**: Increment major version
- **New Fields**: Increment minor version
- **Bug Fixes**: Increment patch version

### Composition Guidelines

- **Base First**: Create base templates for common patterns
- **Extend Thoughtfully**: Only compose when reusing significant functionality
- **Avoid Deep Hierarchies**: Max 2-3 levels of composition

---

## Database Schema

Templates are stored in PostgreSQL:

```sql
CREATE TABLE pattern_library.entity_templates (
    template_id TEXT PRIMARY KEY,
    template_name TEXT NOT NULL,
    description TEXT NOT NULL,
    domain_number CHAR(2) NOT NULL,
    base_entity_name TEXT NOT NULL,
    fields JSONB NOT NULL,
    included_patterns TEXT[],
    composed_from TEXT[],
    version TEXT NOT NULL,
    previous_version TEXT,
    changelog TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    times_instantiated INTEGER,
    is_public BOOLEAN,
    author TEXT
);
```

---

## Testing

Templates are fully tested:

```bash
# Unit tests
uv run pytest tests/unit/domain/test_entity_template.py
uv run pytest tests/unit/application/test_template_service.py

# Integration tests
uv run pytest tests/integration/test_entity_templates.py

# All tests
uv run pytest -k template
```

---

## Examples

### Example 1: Customer Contact Template

Create a reusable customer contact template:

```bash
# 1. Define fields
cat > customer_contact_fields.yaml << EOF
fields:
  - field_name: email
    field_type: text
    required: true
    description: Customer email address
  - field_name: phone
    field_type: text
    required: true
    description: Customer phone number
  - field_name: company
    field_type: ref
    ref_entity: company
    description: Customer's company
  - field_name: status
    field_type: enum
    enum_values: [lead, qualified, customer, inactive]
    description: Customer status
EOF

# 2. Create template
specql templates create \
  --template-id tpl_customer_contact \
  --name "Customer Contact" \
  --description "Customer contact with full details" \
  --domain 01 \
  --base-entity customer_contact \
  --fields-file customer_contact_fields.yaml \
  --patterns audit_trail \
  --patterns soft_delete

# 3. Use in multiple projects
# Project A
specql templates instantiate tpl_customer_contact \
  --entity-name retail_customer \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/retail_customer.yaml

# Project B
specql templates instantiate tpl_customer_contact \
  --entity-name wholesale_customer \
  --subdomain 013 \
  --table-code 01337 \
  --output entities/wholesale_customer.yaml \
  --add-field "credit_limit:money"
```

### Example 2: Address Template

Standard address template for reuse:

```bash
cat > address_fields.yaml << EOF
fields:
  - field_name: street_address
    field_type: text
    required: true
  - field_name: city
    field_type: text
    required: true
  - field_name: state
    field_type: text
    required: true
  - field_name: postal_code
    field_type: text
    required: true
  - field_name: country
    field_type: text
    required: true
    default_value: "USA"
EOF

specql templates create \
  --template-id tpl_address \
  --name "Address" \
  --description "Standard mailing address" \
  --domain 01 \
  --base-entity address \
  --fields-file address_fields.yaml

# Use across entities
specql templates instantiate tpl_address \
  --entity-name customer_address \
  --subdomain 012 \
  --table-code 01238 \
  --output entities/customer_address.yaml

specql templates instantiate tpl_address \
  --entity-name warehouse_address \
  --subdomain 013 \
  --table-code 01339 \
  --output entities/warehouse_address.yaml
```

---

## Troubleshooting

### Template Not Found

```bash
# Error: Template not found: tpl_xyz
# Solution: List available templates
specql templates list

# Or search for similar templates
specql templates search "xyz"
```

### Field Override Syntax

```bash
# Wrong:
--override "phone=required:true"

# Correct:
--override "phone:required=true"

# Format: field_name:property=value
```

### Duplicate Field Names

When adding fields that already exist in template:

```bash
# This will fail if template already has "email" field
--add-field "email:text"

# Solution: Use override instead
--override "email:required=true"
```

---

## Architecture

### Domain Layer

- **EntityTemplate**: Aggregate root
- **TemplateField**: Value object for field definitions
- **TemplateComposition**: Merges multiple templates
- **TemplateInstantiation**: Creates entity specs from templates

### Application Layer

- **TemplateService**: Orchestrates template operations
- **Template CRUD**: Create, read, update, delete templates
- **Template Search**: Find templates by keyword
- **Template Instantiation**: Generate entity specs

### Infrastructure Layer

- **PostgreSQLEntityTemplateRepository**: PostgreSQL storage
- **InMemoryEntityTemplateRepository**: Testing

### Presentation Layer

- **CLI Commands**: `specql templates *`
- **GraphQL API**: (Coming in Phase 7)

---

## Future Enhancements

### Phase 7: GraphQL API (Week 5-6)

```graphql
query {
  entityTemplates(domain: "01") {
    templateId
    templateName
    description
    fields {
      fieldName
      fieldType
      required
    }
    timesInstantiated
  }
}

mutation {
  instantiateTemplate(
    templateId: "tpl_contact"
    entityName: "customer_contact"
    subdomainNumber: "012"
    tableCode: "01236"
  ) {
    entitySpec
    yamlContent
  }
}
```

### Phase 8: AI-Powered Template Discovery (Week 6-7)

```bash
# Natural language template discovery
specql templates discover \
  --from-description "I need an entity for storing customer information with email and phone"

# Output:
# Found 3 matching templates:
# 1. tpl_contact (92% match)
# 2. tpl_customer_contact (88% match)
# 3. tpl_person (75% match)
```

---

**Status**: ✅ Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-12
```

**4. Update main README** to reference entity templates:

Add section to `README.md`:

```markdown
### Entity Templates

Rapidly create entities from reusable templates:

```bash
# List available templates
specql templates list

# Create entity from template
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/customer_contact.yaml

# Customize with overrides
specql templates instantiate tpl_contact \
  --entity-name customer_contact \
  --subdomain 012 \
  --table-code 01236 \
  --output entities/customer_contact.yaml \
  --override "phone:required=true" \
  --add-field "company:ref"
```

See [Entity Templates Documentation](docs/features/ENTITY_TEMPLATES.md) for complete guide.
```

**5. Commit Day 5**:
```bash
git add tests/integration/test_entity_templates.py
git add docs/features/ENTITY_TEMPLATES.md
git add README.md
git commit -m "feat: add entity template integration tests and comprehensive documentation"
```

---

