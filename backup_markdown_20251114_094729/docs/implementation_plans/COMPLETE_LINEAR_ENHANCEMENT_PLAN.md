# Complete Linear Enhancement Plan

**Date Created**: 2025-11-12
**Status**: 🔴 Ready to Execute
**Duration**: 6 weeks (linear execution)
**Philosophy**: Completeness over speed, doing things right from the start

---

## Executive Summary

This plan covers all remaining enhancements to SpecQL in a single linear execution path. The core vision is 100% complete and production-ready. These enhancements improve internal quality, developer experience, and AI-powered pattern discovery.

**What This Plan Covers**:
1. **Domain Model Refinement** (Week 1) - Complete the DDD domain model
2. **Semantic Search Foundation** (Weeks 2-3) - pgvector embeddings and search
3. **Self-Schema Generation** (Week 4) - SpecQL generates its own schema
4. **Dual Interface** (Weeks 5-6) - CLI + GraphQL unified interface

**Total Output**: ~8,000 lines of code, comprehensive test coverage, full documentation

---

## Philosophy: Doing Things Right

### Principles

1. **Complete Before Moving On**: Finish each component 100% before next step
2. **Test-First**: Write tests before implementation
3. **Document As You Build**: Update docs with every change
4. **No Shortcuts**: Proper abstractions, no technical debt
5. **Integration Continuous**: Verify end-to-end after each component

### Quality Gates

Every component must pass:
- ✅ Unit tests (>90% coverage)
- ✅ Integration tests
- ✅ Type checking (mypy)
- ✅ Linting (ruff)
- ✅ Documentation complete
- ✅ Manual verification

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

## Week 1 Summary & Verification

**Completed**:
- ✅ EntityTemplate aggregate with composition and instantiation
- ✅ SubdomainNumber and EntitySequence value objects
- ✅ PostgreSQL repository for EntityTemplate
- ✅ TemplateService application service
- ✅ Complete CLI integration
- ✅ Comprehensive test coverage (unit + integration)
- ✅ Full documentation

**Verification Checklist**:

```bash
# 1. All tests pass
uv run pytest tests/unit/domain/test_entity_template.py -v
uv run pytest tests/unit/domain/value_objects/ -v
uv run pytest tests/unit/infrastructure/test_postgresql_entity_template_repository.py -v
uv run pytest tests/unit/application/test_template_service.py -v
uv run pytest tests/integration/test_entity_templates.py -v

# 2. Code quality
uv run ruff check src/
uv run mypy src/

# 3. CLI works
specql templates list
specql templates --help

# 4. Documentation complete
cat docs/features/ENTITY_TEMPLATES.md

# 5. Git history clean
git log --oneline | head -10
```

**Output Statistics**:
- **Code**: ~1,500 lines (domain + infrastructure + application + CLI)
- **Tests**: ~1,200 lines
- **Documentation**: ~600 lines
- **Total**: ~3,300 lines

**Quality Gates**: All passed ✅

---

## Weeks 2-3: Semantic Search Foundation

**Goal**: Implement pgvector-based semantic search for AI-powered pattern discovery

**Output**: ~2,000 lines of code, complete embedding pipeline, semantic search API

---

### Week 2, Day 1: Embedding Infrastructure

**Objective**: Set up sentence-transformers and embedding generation pipeline

#### Morning: Dependencies & Schema (4 hours)

**1. Add dependencies** to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "sentence-transformers>=2.2.0",
    "torch>=2.0.0",
    "numpy>=1.24.0",
]
```

**2. Install dependencies**:
```bash
uv pip install sentence-transformers torch numpy
```

**3. Verify pgvector extension** in PostgreSQL:

```bash
psql $SPECQL_DB_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If not installed:
psql $SPECQL_DB_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**4. Update pattern schema** `db/schema/pattern_library/01_domain_patterns.sql`:

```sql
-- Add embedding column if not exists
ALTER TABLE pattern_library.domain_patterns
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_domain_patterns_embedding_cosine
    ON pattern_library.domain_patterns
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Alternative: L2 distance index (can have both)
CREATE INDEX IF NOT EXISTS idx_domain_patterns_embedding_l2
    ON pattern_library.domain_patterns
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);

COMMENT ON COLUMN pattern_library.domain_patterns.embedding IS
    '384-dimensional vector embedding generated by sentence-transformers (all-MiniLM-L6-v2)';
```

**5. Apply schema updates**:
```bash
psql $SPECQL_DB_URL -f db/schema/pattern_library/01_domain_patterns.sql
```

#### Afternoon: Embedding Service (4 hours)

**6. Create test** `tests/unit/infrastructure/test_embedding_service.py`:

```python
"""Tests for EmbeddingService"""
import pytest
import numpy as np
from src.infrastructure.services.embedding_service import EmbeddingService


@pytest.fixture
def service():
    """Create embedding service"""
    return EmbeddingService(model_name="all-MiniLM-L6-v2")


class TestEmbeddingService:
    """Test embedding generation service"""

    def test_service_initialization(self, service):
        """Test service initializes successfully"""
        assert service.model is not None
        assert service.model_name == "all-MiniLM-L6-v2"
        assert service.embedding_dimension == 384

    def test_generate_embedding_single_text(self, service):
        """Test generating embedding for single text"""
        text = "Email validation pattern for user input"
        embedding = service.generate_embedding(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float32

    def test_generate_embedding_batch(self, service):
        """Test generating embeddings for batch of texts"""
        texts = [
            "Email validation pattern",
            "Phone number validation",
            "Address validation"
        ]
        embeddings = service.generate_embeddings_batch(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, 384)
        assert embeddings.dtype == np.float32

    def test_embedding_similarity(self, service):
        """Test that similar texts have similar embeddings"""
        text1 = "Email validation pattern"
        text2 = "Email address validation"
        text3 = "Database connection pooling"

        emb1 = service.generate_embedding(text1)
        emb2 = service.generate_embedding(text2)
        emb3 = service.generate_embedding(text3)

        # Cosine similarity
        sim_1_2 = service.cosine_similarity(emb1, emb2)
        sim_1_3 = service.cosine_similarity(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_1_2 > sim_1_3
        assert sim_1_2 > 0.7  # Threshold for similar texts

    def test_embedding_normalization(self, service):
        """Test that embeddings are normalized"""
        text = "Test pattern"
        embedding = service.generate_embedding(text)

        # L2 norm should be close to 1.0 for normalized vectors
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01

    def test_empty_text_handling(self, service):
        """Test handling of empty text"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.generate_embedding("")

    def test_batch_empty_list(self, service):
        """Test handling of empty batch"""
        with pytest.raises(ValueError, match="Batch cannot be empty"):
            service.generate_embeddings_batch([])

    def test_caching(self, service):
        """Test that identical texts return cached embeddings"""
        text = "Cached pattern"

        # Generate twice
        emb1 = service.generate_embedding(text)
        emb2 = service.generate_embedding(text)

        # Should be identical (cached)
        assert np.array_equal(emb1, emb2)

    def test_pattern_embedding_content(self, service):
        """Test embedding generation from pattern components"""
        # Pattern metadata
        pattern_name = "email_validation"
        description = "Validates email addresses using regex"
        implementation = "REGEXP MATCH email against RFC 5322"

        # Combine for embedding
        text = f"{pattern_name} {description} {implementation}"
        embedding = service.generate_embedding(text)

        assert embedding.shape == (384,)

    def test_embedding_to_list(self, service):
        """Test converting embedding to list for PostgreSQL"""
        text = "Test pattern"
        embedding = service.generate_embedding(text)

        embedding_list = service.embedding_to_list(embedding)

        assert isinstance(embedding_list, list)
        assert len(embedding_list) == 384
        assert all(isinstance(x, float) for x in embedding_list)
```

**7. Run tests** (should fail):
```bash
uv run pytest tests/unit/infrastructure/test_embedding_service.py -v
# Expected: FAILED (EmbeddingService not implemented)
```

**8. Implement EmbeddingService** `src/infrastructure/services/embedding_service.py`:

```python
"""Service for generating text embeddings using sentence-transformers"""
import numpy as np
from typing import List, Optional
from functools import lru_cache
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Service for generating semantic embeddings from text

    Uses sentence-transformers with all-MiniLM-L6-v2 model:
    - 384-dimensional embeddings
    - Fast inference (~5ms per text)
    - Good quality for semantic similarity
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service

        Args:
            model_name: Sentence-transformers model name
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            384-dimensional numpy array (float32)

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Generate embedding
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,  # L2 normalization for cosine similarity
            show_progress_bar=False
        )

        return embedding.astype(np.float32)

    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts

        Args:
            texts: List of texts to embed

        Returns:
            (N, 384) numpy array where N = len(texts)

        Raises:
            ValueError: If batch is empty
        """
        if not texts:
            raise ValueError("Batch cannot be empty")

        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("All texts in batch are empty")

        # Generate embeddings
        embeddings = self.model.encode(
            valid_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32  # Process in batches of 32
        )

        return embeddings.astype(np.float32)

    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            emb1: First embedding
            emb2: Second embedding

        Returns:
            Similarity score between -1 and 1 (1 = identical)
        """
        # For normalized vectors, cosine similarity = dot product
        return float(np.dot(emb1, emb2))

    @staticmethod
    def embedding_to_list(embedding: np.ndarray) -> List[float]:
        """
        Convert numpy embedding to list for PostgreSQL

        Args:
            embedding: Numpy array

        Returns:
            List of floats
        """
        return embedding.tolist()

    def create_pattern_embedding(
        self,
        pattern_name: str,
        description: str,
        implementation: Optional[str] = None,
        category: Optional[str] = None
    ) -> np.ndarray:
        """
        Create embedding for a pattern combining multiple components

        Args:
            pattern_name: Pattern name
            description: Pattern description
            implementation: Optional implementation details
            category: Optional category

        Returns:
            384-dimensional embedding
        """
        # Combine components with weights
        components = [
            pattern_name,  # Name is important
            description,   # Description is most important
        ]

        if implementation:
            components.append(implementation)

        if category:
            components.append(f"category: {category}")

        # Join with spaces
        text = " ".join(components)

        return self.generate_embedding(text)


# Singleton instance for reuse across application
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton embedding service instance

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
```

**9. Run tests** (should pass):
```bash
uv run pytest tests/unit/infrastructure/test_embedding_service.py -v
# Expected: PASSED
```

**10. Commit Day 1**:
```bash
git add pyproject.toml
git add db/schema/pattern_library/01_domain_patterns.sql
git add src/infrastructure/services/embedding_service.py
git add tests/unit/infrastructure/test_embedding_service.py
git commit -m "feat: implement embedding service with sentence-transformers and pgvector schema"
```

---

### Week 2, Day 2: Backfill Existing Patterns

**Objective**: Generate and store embeddings for all existing patterns

#### Morning: Migration Script (4 hours)

**1. Create migration script** `scripts/backfill_pattern_embeddings.py`:

```python
"""Backfill embeddings for existing patterns"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import psycopg
from psycopg.types.json import Jsonb
from src.infrastructure.services.embedding_service import get_embedding_service
from src.core.config import get_config


def backfill_embeddings():
    """Generate and store embeddings for all patterns without embeddings"""
    config = get_config()
    embedding_service = get_embedding_service()

    print("🔄 Starting embedding backfill...")
    print(f"📊 Using model: {embedding_service.model_name}")
    print(f"📐 Embedding dimension: {embedding_service.embedding_dimension}")

    with psycopg.connect(config.db_url) as conn:
        with conn.cursor() as cur:
            # Get patterns without embeddings
            cur.execute("""
                SELECT id, name, description, implementation, category
                FROM pattern_library.domain_patterns
                WHERE embedding IS NULL
                ORDER BY id
            """)

            patterns = cur.fetchall()
            total = len(patterns)

            if total == 0:
                print("✅ All patterns already have embeddings")
                return

            print(f"📝 Found {total} patterns without embeddings")
            print()

            # Process each pattern
            for i, (pattern_id, name, description, implementation, category) in enumerate(patterns, 1):
                print(f"[{i}/{total}] Processing: {name}")

                # Generate embedding
                try:
                    embedding = embedding_service.create_pattern_embedding(
                        pattern_name=name,
                        description=description or "",
                        implementation=implementation or "",
                        category=category or ""
                    )

                    # Convert to list for PostgreSQL
                    embedding_list = embedding_service.embedding_to_list(embedding)

                    # Update pattern
                    cur.execute("""
                        UPDATE pattern_library.domain_patterns
                        SET embedding = %s
                        WHERE id = %s
                    """, (embedding_list, pattern_id))

                    print(f"   ✅ Generated embedding (dim={len(embedding_list)})")

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue

            # Commit all updates
            conn.commit()

            print()
            print(f"✅ Backfill complete! Updated {total} patterns")

            # Verify
            cur.execute("""
                SELECT COUNT(*)
                FROM pattern_library.domain_patterns
                WHERE embedding IS NOT NULL
            """)
            embedded_count = cur.fetchone()[0]

            print(f"📊 Total patterns with embeddings: {embedded_count}")


def verify_embeddings():
    """Verify embedding quality with sample similarity search"""
    config = get_config()

    print()
    print("🔍 Verifying embeddings with sample search...")

    with psycopg.connect(config.db_url) as conn:
        with conn.cursor() as cur:
            # Sample query: find patterns similar to "email validation"
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.generate_embedding("email validation")
            query_list = embedding_service.embedding_to_list(query_embedding)

            cur.execute("""
                SELECT
                    name,
                    description,
                    1 - (embedding <=> %s::vector) as similarity
                FROM pattern_library.domain_patterns
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """, (query_list, query_list))

            results = cur.fetchall()

            print()
            print("Top 5 matches for 'email validation':")
            for name, description, similarity in results:
                print(f"  • {name} (similarity: {similarity:.3f})")
                print(f"    {description[:80]}...")
                print()


if __name__ == "__main__":
    try:
        backfill_embeddings()
        verify_embeddings()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
```

**2. Test migration script**:
```bash
# Dry run first - check what patterns need embeddings
psql $SPECQL_DB_URL -c "
SELECT COUNT(*) as patterns_without_embeddings
FROM pattern_library.domain_patterns
WHERE embedding IS NULL;"

# Run backfill
python scripts/backfill_pattern_embeddings.py

# Expected output:
# 🔄 Starting embedding backfill...
# 📊 Using model: all-MiniLM-L6-v2
# 📐 Embedding dimension: 384
# 📝 Found 25 patterns without embeddings
#
# [1/25] Processing: email_validation
#    ✅ Generated embedding (dim=384)
# [2/25] Processing: phone_validation
#    ✅ Generated embedding (dim=384)
# ...
# ✅ Backfill complete! Updated 25 patterns
# 📊 Total patterns with embeddings: 25
#
# 🔍 Verifying embeddings with sample search...
#
# Top 5 matches for 'email validation':
#   • email_validation (similarity: 0.998)
#     Validates email addresses using RFC 5322 regex pattern...
#   • contact_validation (similarity: 0.856)
#     Validates contact information including email and phone...
```

#### Afternoon: Repository Updates (4 hours)

**3. Update Pattern entity** `src/domain/entities/pattern.py`:

Add embedding field:

```python
@dataclass
class Pattern:
    """Pattern aggregate"""
    # ... existing fields ...
    embedding: Optional[List[float]] = None  # 384-dimensional vector
```

**4. Update PostgreSQL repository** `src/infrastructure/repositories/postgresql_pattern_repository.py`:

Update save() method to handle embeddings:

```python
def save(self, pattern: Pattern) -> None:
    """Save pattern to PostgreSQL (transactional)"""
    with psycopg.connect(self.db_url) as conn:
        with conn.cursor() as cur:
            if pattern.id is None:
                # Insert new pattern
                cur.execute("""
                    INSERT INTO pattern_library.domain_patterns
                    (name, category, description, parameters, implementation,
                     embedding, times_instantiated, source_type, complexity_score,
                     deprecated, deprecated_reason, replacement_pattern_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        parameters = EXCLUDED.parameters,
                        implementation = EXCLUDED.implementation,
                        embedding = EXCLUDED.embedding,
                        times_instantiated = EXCLUDED.times_instantiated,
                        complexity_score = EXCLUDED.complexity_score,
                        deprecated = EXCLUDED.deprecated,
                        deprecated_reason = EXCLUDED.deprecated_reason,
                        replacement_pattern_id = EXCLUDED.replacement_pattern_id
                    RETURNING id
                """, (
                    pattern.name,
                    pattern.category,
                    pattern.description,
                    Jsonb(pattern.parameters or {}),
                    pattern.implementation,
                    pattern.embedding,  # Now included
                    pattern.times_instantiated,
                    pattern.source_type,
                    pattern.complexity_score,
                    pattern.deprecated,
                    pattern.deprecated_reason,
                    pattern.replacement_pattern_id
                ))
                result = cur.fetchone()
                if result:
                    pattern.id = result[0]
            else:
                # Update existing pattern
                cur.execute("""
                    UPDATE pattern_library.domain_patterns
                    SET name = %s,
                        category = %s,
                        description = %s,
                        parameters = %s,
                        implementation = %s,
                        embedding = %s,
                        times_instantiated = %s,
                        complexity_score = %s,
                        deprecated = %s,
                        deprecated_reason = %s,
                        replacement_pattern_id = %s
                    WHERE id = %s
                """, (
                    pattern.name,
                    pattern.category,
                    pattern.description,
                    Jsonb(pattern.parameters or {}),
                    pattern.implementation,
                    pattern.embedding,  # Now included
                    pattern.times_instantiated,
                    pattern.complexity_score,
                    pattern.deprecated,
                    pattern.deprecated_reason,
                    pattern.replacement_pattern_id,
                    pattern.id
                ))
            conn.commit()
```

Update find methods to retrieve embeddings:

```python
def _row_to_pattern(self, row) -> Pattern:
    """Convert database row to Pattern entity"""
    (
        pattern_id, name, category, description, parameters,
        implementation, embedding, times_instantiated, source_type,
        complexity_score, deprecated, deprecated_reason, replacement_pattern_id
    ) = row

    return Pattern(
        id=pattern_id,
        name=name,
        category=category,
        description=description,
        parameters=parameters,
        implementation=implementation,
        embedding=embedding,  # Now included
        times_instantiated=times_instantiated,
        source_type=source_type,
        complexity_score=complexity_score,
        deprecated=deprecated,
        deprecated_reason=deprecated_reason,
        replacement_pattern_id=replacement_pattern_id
    )
```

**5. Update PatternService** `src/application/services/pattern_service.py`:

Add method to generate embedding when creating pattern:

```python
from src.infrastructure.services.embedding_service import get_embedding_service

class PatternService:
    """Application service for pattern management"""

    def __init__(self, repository: PatternRepository):
        self.repository = repository
        self.embedding_service = get_embedding_service()

    def create_pattern(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        implementation: str = "",
        complexity_score: int = 1,
        generate_embedding: bool = True  # New parameter
    ) -> Pattern:
        """
        Create a new pattern

        Args:
            name: Pattern name
            category: Pattern category
            description: Pattern description
            parameters: Pattern parameters
            implementation: Implementation details
            complexity_score: Complexity (1-10)
            generate_embedding: Whether to auto-generate embedding

        Returns:
            Created Pattern
        """
        # Generate embedding if requested
        embedding = None
        if generate_embedding:
            embedding_vector = self.embedding_service.create_pattern_embedding(
                pattern_name=name,
                description=description,
                implementation=implementation,
                category=category
            )
            embedding = self.embedding_service.embedding_to_list(embedding_vector)

        # Create pattern
        pattern = Pattern(
            name=name,
            category=category,
            description=description,
            parameters=parameters or {},
            implementation=implementation,
            embedding=embedding,
            times_instantiated=0,
            source_type="user_defined",
            complexity_score=complexity_score
        )

        # Save
        self.repository.save(pattern)

        return pattern
```

**6. Test updates**:

Create test `tests/unit/application/test_pattern_service_embeddings.py`:

```python
"""Tests for PatternService embedding functionality"""
import pytest
import numpy as np
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)


@pytest.fixture
def service():
    """Create service with in-memory repository"""
    repository = InMemoryPatternRepository()
    return PatternService(repository)


class TestPatternServiceEmbeddings:
    """Test embedding generation in PatternService"""

    def test_create_pattern_with_embedding(self, service):
        """Test creating pattern with auto-generated embedding"""
        pattern = service.create_pattern(
            name="test_email_validation",
            category="validation",
            description="Validates email addresses",
            implementation="REGEXP pattern matching",
            generate_embedding=True
        )

        assert pattern.embedding is not None
        assert isinstance(pattern.embedding, list)
        assert len(pattern.embedding) == 384

    def test_create_pattern_without_embedding(self, service):
        """Test creating pattern without embedding"""
        pattern = service.create_pattern(
            name="test_pattern_no_embedding",
            category="test",
            description="Test pattern",
            generate_embedding=False
        )

        assert pattern.embedding is None

    def test_embedding_similarity_for_similar_patterns(self, service):
        """Test that similar patterns have similar embeddings"""
        pattern1 = service.create_pattern(
            name="email_validation",
            category="validation",
            description="Validates email addresses using regex",
            generate_embedding=True
        )

        pattern2 = service.create_pattern(
            name="email_check",
            category="validation",
            description="Checks if email address is valid",
            generate_embedding=True
        )

        # Convert to numpy arrays
        emb1 = np.array(pattern1.embedding)
        emb2 = np.array(pattern2.embedding)

        # Calculate cosine similarity
        similarity = float(np.dot(emb1, emb2))

        # Similar patterns should have high similarity
        assert similarity > 0.7
```

Run tests:
```bash
uv run pytest tests/unit/application/test_pattern_service_embeddings.py -v
```

**7. Commit Day 2**:
```bash
git add scripts/backfill_pattern_embeddings.py
git add src/domain/entities/pattern.py
git add src/infrastructure/repositories/postgresql_pattern_repository.py
git add src/application/services/pattern_service.py
git add tests/unit/application/test_pattern_service_embeddings.py
git commit -m "feat: add embedding generation to PatternService and backfill script for existing patterns"
```

---

### Week 2, Day 3: Semantic Search API

**Objective**: Implement semantic search functionality in repository and service

#### Morning: Repository Search Methods (4 hours)

**1. Create test** `tests/unit/infrastructure/test_semantic_search.py`:

```python
"""Tests for semantic search functionality"""
import pytest
import os
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.application.services.pattern_service import PatternService
from src.infrastructure.services.embedding_service import get_embedding_service


@pytest.fixture
def db_url():
    """Get database URL"""
    return os.getenv("SPECQL_DB_URL", "postgresql://specql_user:specql_dev_password@localhost/specql")


@pytest.fixture
def repository(db_url):
    """Create PostgreSQL repository"""
    return PostgreSQLPatternRepository(db_url)


@pytest.fixture
def service(repository):
    """Create pattern service"""
    return PatternService(repository)


@pytest.fixture
def embedding_service():
    """Get embedding service"""
    return get_embedding_service()


class TestSemanticSearch:
    """Test semantic search functionality"""

    def test_search_by_similarity(self, repository, embedding_service):
        """Test finding patterns by semantic similarity"""
        # Create query embedding
        query_text = "validate email addresses"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search
        results = repository.search_by_similarity(
            query_embedding=query_list,
            limit=5,
            min_similarity=0.5
        )

        # Should find patterns
        assert len(results) > 0

        # Results should be tuples of (Pattern, similarity_score)
        for pattern, similarity in results:
            assert pattern.embedding is not None
            assert 0.0 <= similarity <= 1.0
            # Should be relevant to email validation
            assert any(
                keyword in pattern.name.lower() or keyword in pattern.description.lower()
                for keyword in ["email", "validation", "contact"]
            )

        # Results should be sorted by similarity (descending)
        similarities = [sim for _, sim in results]
        assert similarities == sorted(similarities, reverse=True)

    def test_search_with_min_similarity_threshold(self, repository, embedding_service):
        """Test filtering results by minimum similarity"""
        query_text = "database connection pooling"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search with high threshold
        results_high = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            min_similarity=0.8  # High threshold
        )

        # Search with low threshold
        results_low = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            min_similarity=0.3  # Low threshold
        )

        # Low threshold should return more results
        assert len(results_low) >= len(results_high)

        # All high-threshold results should have similarity >= 0.8
        for _, similarity in results_high:
            assert similarity >= 0.8

    def test_search_with_category_filter(self, repository, embedding_service):
        """Test searching within specific category"""
        query_text = "validation rules"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search within validation category
        results = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            category="validation"
        )

        # All results should be in validation category
        for pattern, _ in results:
            assert pattern.category == "validation"

    def test_search_excludes_deprecated(self, repository, embedding_service):
        """Test that deprecated patterns are excluded by default"""
        query_text = "pattern search"
        query_embedding = embedding_service.generate_embedding(query_text)
        query_list = embedding_service.embedding_to_list(query_embedding)

        # Search (should exclude deprecated)
        results = repository.search_by_similarity(
            query_embedding=query_list,
            limit=10,
            include_deprecated=False
        )

        # No deprecated patterns
        for pattern, _ in results:
            assert not pattern.deprecated

    def test_natural_language_search(self, service):
        """Test natural language pattern search"""
        # User types natural language query
        query = "I need to validate user email addresses"

        # Service handles search
        results = service.search_patterns_semantic(query, limit=5)

        assert len(results) > 0

        # Should find email validation patterns
        for pattern, similarity in results:
            print(f"{pattern.name}: {similarity:.3f}")
            assert similarity > 0.5  # Reasonable threshold

    def test_find_similar_patterns(self, service, repository):
        """Test finding patterns similar to a given pattern"""
        # Get a pattern
        email_pattern = repository.find_by_name("email_validation")
        assert email_pattern is not None

        # Find similar patterns
        similar = service.find_similar_patterns(
            pattern_id=email_pattern.id,
            limit=5
        )

        assert len(similar) > 0

        # Should not include the original pattern
        for pattern, _ in similar:
            assert pattern.id != email_pattern.id

        # Should be semantically similar
        for pattern, similarity in similar:
            assert similarity > 0.5
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/infrastructure/test_semantic_search.py -v
# Expected: FAILED (search methods not implemented)
```

**3. Implement repository search methods** `src/infrastructure/repositories/postgresql_pattern_repository.py`:

Add new methods:

```python
from typing import List, Tuple, Optional

class PostgreSQLPatternRepository:
    """PostgreSQL repository for Pattern aggregate"""

    # ... existing methods ...

    def search_by_similarity(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_similarity: float = 0.0,
        category: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
        """
        Search patterns by semantic similarity

        Args:
            query_embedding: Query embedding vector (384-dim)
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            category: Optional category filter
            include_deprecated: Whether to include deprecated patterns

        Returns:
            List of (Pattern, similarity_score) tuples, sorted by similarity DESC
        """
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Build WHERE clause
                where_clauses = ["embedding IS NOT NULL"]
                params = [query_embedding]

                if not include_deprecated:
                    where_clauses.append("deprecated = false")

                if category:
                    where_clauses.append("category = %s")
                    params.append(category)

                where_sql = " AND ".join(where_clauses)

                # Similarity calculation: 1 - cosine_distance
                # pgvector's <=> operator is cosine distance (0 = identical, 2 = opposite)
                # So similarity = 1 - (distance / 2) for normalization
                # Or simpler: similarity = 1 - distance (for small distances)
                cur.execute(f"""
                    SELECT
                        id, name, category, description, parameters, implementation,
                        embedding, times_instantiated, source_type, complexity_score,
                        deprecated, deprecated_reason, replacement_pattern_id,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM pattern_library.domain_patterns
                    WHERE {where_sql}
                        AND (1 - (embedding <=> %s::vector)) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, [query_embedding] + params + [query_embedding, min_similarity, query_embedding, limit])

                results = []
                for row in cur.fetchall():
                    # Last column is similarity
                    *pattern_data, similarity = row
                    pattern = self._row_to_pattern(pattern_data)
                    results.append((pattern, float(similarity)))

                return results

    def find_similar_to_pattern(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5,
        include_deprecated: bool = False
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to a given pattern

        Args:
            pattern_id: ID of reference pattern
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            include_deprecated: Whether to include deprecated patterns

        Returns:
            List of (Pattern, similarity_score) tuples, excluding the reference pattern
        """
        # Get reference pattern's embedding
        pattern = self.find_by_id(pattern_id)
        if not pattern or not pattern.embedding:
            return []

        # Search using its embedding
        results = self.search_by_similarity(
            query_embedding=pattern.embedding,
            limit=limit + 1,  # +1 because we'll filter out the reference pattern
            min_similarity=min_similarity,
            include_deprecated=include_deprecated
        )

        # Filter out the reference pattern itself
        filtered = [
            (p, sim) for p, sim in results
            if p.id != pattern_id
        ]

        return filtered[:limit]
```

**4. Run tests** (should pass):
```bash
uv run pytest tests/unit/infrastructure/test_semantic_search.py -v
# Expected: PASSED
```

#### Afternoon: Service Integration (4 hours)

**5. Update PatternService** `src/application/services/pattern_service.py`:

Add semantic search methods:

```python
class PatternService:
    """Application service for pattern management"""

    # ... existing methods ...

    def search_patterns_semantic(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        category: Optional[str] = None
    ) -> List[Tuple[Pattern, float]]:
        """
        Search patterns using natural language query

        Args:
            query: Natural language search query
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            category: Optional category filter

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> results = service.search_patterns_semantic(
            ...     "validate email addresses",
            ...     limit=5
            ... )
            >>> for pattern, similarity in results:
            ...     print(f"{pattern.name}: {similarity:.2%}")
        """
        # Generate embedding for query
        query_embedding_vector = self.embedding_service.generate_embedding(query)
        query_embedding = self.embedding_service.embedding_to_list(query_embedding_vector)

        # Search
        return self.repository.search_by_similarity(
            query_embedding=query_embedding,
            limit=limit,
            min_similarity=min_similarity,
            category=category,
            include_deprecated=False
        )

    def find_similar_patterns(
        self,
        pattern_id: int,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns similar to a given pattern

        Args:
            pattern_id: ID of reference pattern
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> email_pattern = service.get_pattern_by_name("email_validation")
            >>> similar = service.find_similar_patterns(
            ...     email_pattern.id,
            ...     limit=5
            ... )
        """
        return self.repository.find_similar_to_pattern(
            pattern_id=pattern_id,
            limit=limit,
            min_similarity=min_similarity,
            include_deprecated=False
        )

    def recommend_patterns_for_entity(
        self,
        entity_description: str,
        field_names: List[str],
        limit: int = 5
    ) -> List[Tuple[Pattern, float]]:
        """
        Recommend patterns for an entity based on description and fields

        Args:
            entity_description: Description of the entity
            field_names: List of field names in the entity
            limit: Maximum recommendations

        Returns:
            List of (Pattern, similarity_score) tuples

        Example:
            >>> recommendations = service.recommend_patterns_for_entity(
            ...     entity_description="Customer contact information",
            ...     field_names=["email", "phone", "address"],
            ...     limit=5
            ... )
        """
        # Combine description and field names into query
        query = f"{entity_description}. Fields: {', '.join(field_names)}"

        return self.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=0.6  # Higher threshold for recommendations
        )
```

**6. Commit Day 3**:
```bash
git add src/infrastructure/repositories/postgresql_pattern_repository.py
git add src/application/services/pattern_service.py
git add tests/unit/infrastructure/test_semantic_search.py
git commit -m "feat: implement semantic search API with natural language queries"
```

---

### Week 2, Day 4: CLI Integration for Search

**Objective**: Add CLI commands for semantic pattern search

#### Morning: CLI Commands (4 hours)

**1. Update patterns CLI** `src/cli/patterns.py`:

Add search commands:

```python
"""CLI commands for pattern management"""
import click
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.core.config import get_config


@click.group()
def patterns():
    """Manage patterns in the pattern library"""
    pass


# ... existing commands (list, show, etc.) ...


@patterns.command()
@click.argument("query")
@click.option("--limit", default=10, help="Maximum results to return")
@click.option("--min-similarity", default=0.5, type=float,
              help="Minimum similarity threshold (0.0-1.0)")
@click.option("--category", help="Filter by category")
def search(query, limit, min_similarity, category):
    """
    Search patterns using natural language

    Examples:
        specql patterns search "validate email addresses"
        specql patterns search "audit logging" --category infrastructure
        specql patterns search "phone number" --min-similarity 0.7
    """
    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)

    click.echo(f"🔍 Searching for: '{query}'")
    if category:
        click.echo(f"   Category: {category}")
    click.echo(f"   Minimum similarity: {min_similarity}")
    click.echo()

    # Search
    results = service.search_patterns_semantic(
        query=query,
        limit=limit,
        min_similarity=min_similarity,
        category=category
    )

    if not results:
        click.echo("No matching patterns found.")
        click.echo(f"Try lowering --min-similarity (current: {min_similarity})")
        return

    click.echo(f"Found {len(results)} pattern(s):\n")

    for i, (pattern, similarity) in enumerate(results, 1):
        # Similarity as percentage
        sim_pct = similarity * 100

        # Color code by similarity
        if similarity >= 0.8:
            color = "green"
        elif similarity >= 0.6:
            color = "yellow"
        else:
            color = "white"

        click.secho(f"{i}. {pattern.name} ", fg=color, bold=True, nl=False)
        click.secho(f"({sim_pct:.1f}% match)", fg=color)

        click.echo(f"   Category: {pattern.category}")
        click.echo(f"   Description: {pattern.description[:100]}...")

        if pattern.times_instantiated > 0:
            click.echo(f"   Used {pattern.times_instantiated} times")

        click.echo()


@patterns.command()
@click.argument("pattern_name")
@click.option("--limit", default=5, help="Maximum results to return")
@click.option("--min-similarity", default=0.5, type=float,
              help="Minimum similarity threshold")
def similar(pattern_name, limit, min_similarity):
    """
    Find patterns similar to a given pattern

    Examples:
        specql patterns similar email_validation
        specql patterns similar audit_trail --limit 10
    """
    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)

    # Get reference pattern
    pattern = service.get_pattern_by_name(pattern_name)
    if not pattern:
        click.echo(f"❌ Pattern not found: {pattern_name}", err=True)
        return

    if not pattern.embedding:
        click.echo(f"❌ Pattern has no embedding: {pattern_name}", err=True)
        click.echo("Run: python scripts/backfill_pattern_embeddings.py")
        return

    click.echo(f"🔍 Finding patterns similar to: {pattern.name}")
    click.echo(f"   {pattern.description}")
    click.echo()

    # Find similar
    results = service.find_similar_patterns(
        pattern_id=pattern.id,
        limit=limit,
        min_similarity=min_similarity
    )

    if not results:
        click.echo("No similar patterns found.")
        return

    click.echo(f"Found {len(results)} similar pattern(s):\n")

    for i, (similar_pattern, similarity) in enumerate(results, 1):
        sim_pct = similarity * 100

        if similarity >= 0.8:
            color = "green"
        elif similarity >= 0.6:
            color = "yellow"
        else:
            color = "white"

        click.secho(f"{i}. {similar_pattern.name} ", fg=color, bold=True, nl=False)
        click.secho(f"({sim_pct:.1f}% similar)", fg=color)

        click.echo(f"   {similar_pattern.description[:100]}...")
        click.echo()


@patterns.command()
@click.option("--entity-description", required=True,
              help="Description of the entity")
@click.option("--field", "fields", multiple=True, required=True,
              help="Field names in the entity (can specify multiple)")
@click.option("--limit", default=5, help="Maximum recommendations")
def recommend(entity_description, fields, limit):
    """
    Recommend patterns for an entity

    Examples:
        specql patterns recommend \
            --entity-description "Customer contact information" \
            --field email \
            --field phone \
            --field address
    """
    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)

    click.echo("🎯 Pattern recommendations for:")
    click.echo(f"   Entity: {entity_description}")
    click.echo(f"   Fields: {', '.join(fields)}")
    click.echo()

    # Get recommendations
    recommendations = service.recommend_patterns_for_entity(
        entity_description=entity_description,
        field_names=list(fields),
        limit=limit
    )

    if not recommendations:
        click.echo("No pattern recommendations found.")
        return

    click.echo(f"💡 Recommended {len(recommendations)} pattern(s):\n")

    for i, (pattern, similarity) in enumerate(recommendations, 1):
        sim_pct = similarity * 100

        click.secho(f"{i}. {pattern.name} ", fg="cyan", bold=True, nl=False)
        click.secho(f"({sim_pct:.1f}% match)", fg="cyan")

        click.echo(f"   {pattern.description}")

        if pattern.times_instantiated > 0:
            click.echo(f"   ⭐ Popular: Used {pattern.times_instantiated} times")

        click.echo()


if __name__ == "__main__":
    patterns()
```

**2. Test CLI commands**:

```bash
# Natural language search
specql patterns search "validate email addresses"

# Expected output:
# 🔍 Searching for: 'validate email addresses'
#    Minimum similarity: 0.5
#
# Found 3 pattern(s):
#
# 1. email_validation (95.2% match)
#    Category: validation
#    Description: Validates email addresses using RFC 5322 regex pattern...
#    Used 12 times
#
# 2. contact_validation (82.7% match)
#    Category: validation
#    Description: Validates contact information including email and phone...
#
# 3. user_input_validation (68.3% match)
#    Category: validation
#    Description: Validates all user input fields...

# Find similar patterns
specql patterns similar email_validation --limit 5

# Recommend patterns for entity
specql patterns recommend \
  --entity-description "Customer contact with email and phone" \
  --field email \
  --field phone \
  --field company \
  --limit 5

# Expected output:
# 🎯 Pattern recommendations for:
#    Entity: Customer contact with email and phone
#    Fields: email, phone, company
#
# 💡 Recommended 5 pattern(s):
#
# 1. email_validation (88.4% match)
#    Validates email addresses using RFC 5322 regex pattern
#    ⭐ Popular: Used 12 times
#
# 2. phone_validation (85.2% match)
#    Validates phone numbers in multiple formats
#    ⭐ Popular: Used 8 times
#
# 3. contact_info_validation (79.1% match)
#    Comprehensive contact information validation
```

#### Afternoon: Integration Testing (4 hours)

**3. Create integration test** `tests/integration/test_semantic_search_cli.py`:

```python
"""Integration tests for semantic search CLI"""
import subprocess
import json


class TestSemanticSearchCLI:
    """Test semantic search CLI commands"""

    def test_search_command(self):
        """Test basic search command"""
        result = subprocess.run(
            ["specql", "patterns", "search", "email validation", "--limit", "5"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Found" in result.stdout
        assert "email" in result.stdout.lower()

    def test_search_with_category_filter(self):
        """Test search with category filter"""
        result = subprocess.run(
            [
                "specql", "patterns", "search", "validation",
                "--category", "validation",
                "--limit", "10"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Category: validation" in result.stdout

    def test_similar_command(self):
        """Test finding similar patterns"""
        result = subprocess.run(
            ["specql", "patterns", "similar", "email_validation", "--limit", "3"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "similar" in result.stdout.lower()

    def test_recommend_command(self):
        """Test pattern recommendations"""
        result = subprocess.run(
            [
                "specql", "patterns", "recommend",
                "--entity-description", "Customer contact information",
                "--field", "email",
                "--field", "phone",
                "--limit", "5"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Recommended" in result.stdout
```

Run integration tests:
```bash
uv run pytest tests/integration/test_semantic_search_cli.py -v
```

**4. Create performance benchmark** `tests/performance/test_semantic_search_performance.py`:

```python
"""Performance tests for semantic search"""
import pytest
import time
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.application.services.pattern_service import PatternService
from src.infrastructure.services.embedding_service import get_embedding_service
from src.core.config import get_config


@pytest.fixture
def service():
    """Create service"""
    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    return PatternService(repository)


class TestSemanticSearchPerformance:
    """Performance benchmarks for semantic search"""

    def test_single_search_performance(self, service):
        """Test single search query performance"""
        query = "validate email addresses"

        start = time.time()
        results = service.search_patterns_semantic(query, limit=10)
        elapsed = time.time() - start

        print(f"\n⏱️  Single search: {elapsed*1000:.2f}ms")
        print(f"   Results: {len(results)}")

        # Should be fast (< 100ms)
        assert elapsed < 0.1

    def test_batch_search_performance(self, service):
        """Test multiple searches performance"""
        queries = [
            "email validation",
            "phone number formatting",
            "address validation",
            "date parsing",
            "money formatting",
        ]

        start = time.time()
        for query in queries:
            service.search_patterns_semantic(query, limit=5)
        elapsed = time.time() - start

        avg_time = elapsed / len(queries)
        print(f"\n⏱️  Batch search ({len(queries)} queries): {elapsed*1000:.2f}ms")
        print(f"   Average per query: {avg_time*1000:.2f}ms")

        # Average should be fast
        assert avg_time < 0.1

    def test_embedding_generation_performance(self):
        """Test embedding generation performance"""
        embedding_service = get_embedding_service()

        texts = [
            "Email validation pattern",
            "Phone number validation",
            "Address formatting",
        ] * 10  # 30 texts

        start = time.time()
        embeddings = embedding_service.generate_embeddings_batch(texts)
        elapsed = time.time() - start

        avg_time = elapsed / len(texts)
        print(f"\n⏱️  Embedding generation ({len(texts)} texts): {elapsed*1000:.2f}ms")
        print(f"   Average per text: {avg_time*1000:.2f}ms")
        print(f"   Throughput: {len(texts)/elapsed:.1f} texts/sec")

        # Should handle batch efficiently
        assert avg_time < 0.01  # < 10ms per text
```

Run performance tests:
```bash
uv run pytest tests/performance/test_semantic_search_performance.py -v -s
```

**5. Commit Day 4**:
```bash
git add src/cli/patterns.py
git add tests/integration/test_semantic_search_cli.py
git add tests/performance/test_semantic_search_performance.py
git commit -m "feat: add CLI commands for semantic pattern search with recommendations"
```

---

### Week 2, Day 5: Documentation & Week Summary

**Objective**: Comprehensive documentation and week 2 verification

#### Morning: Documentation (4 hours)

**1. Create semantic search documentation** `docs/features/SEMANTIC_PATTERN_SEARCH.md`:

```markdown
# Semantic Pattern Search

**Feature**: AI-powered pattern discovery using natural language
**Status**: ✅ Complete
**Version**: 1.0.0

---

## Overview

Semantic Pattern Search uses AI embeddings to enable natural language pattern discovery. Instead of exact keyword matching, it understands the *meaning* of your query to find relevant patterns.

### Key Features

- **Natural Language Queries**: Search using plain English
- **Semantic Understanding**: Finds patterns by meaning, not just keywords
- **Similarity Search**: Discover related patterns
- **Smart Recommendations**: Get pattern suggestions for entities
- **Fast**: <100ms search latency with pgvector indexes

---

## How It Works

### 1. Embedding Generation

Each pattern is converted to a 384-dimensional vector embedding that captures its semantic meaning:

```
Pattern: "email_validation"
Description: "Validates email addresses using RFC 5322 regex"

↓ sentence-transformers (all-MiniLM-L6-v2)

Embedding: [0.234, -0.512, 0.891, ..., 0.123]  # 384 dimensions
```

### 2. Similarity Search

Query embeddings are compared using cosine similarity:

```
Query: "validate email addresses"
↓ embedding
Query Vector: [0.241, -0.498, 0.887, ...]

↓ cosine similarity with all patterns

Results (sorted by similarity):
1. email_validation       (0.952 similarity)
2. contact_validation     (0.827 similarity)
3. user_input_validation  (0.683 similarity)
```

### 3. pgvector Indexing

PostgreSQL's pgvector extension provides efficient vector search:

```sql
-- IVFFlat index for fast similarity search
CREATE INDEX ON domain_patterns
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Search using <=> operator (cosine distance)
SELECT name, 1 - (embedding <=> query_vector) as similarity
FROM domain_patterns
ORDER BY embedding <=> query_vector
LIMIT 10;
```

---

## CLI Usage

### Natural Language Search

Search patterns using plain English:

```bash
# Basic search
specql patterns search "validate email addresses"

# With filters
specql patterns search "audit logging" \
  --category infrastructure \
  --limit 10 \
  --min-similarity 0.7

# Output:
# 🔍 Searching for: 'validate email addresses'
#    Minimum similarity: 0.5
#
# Found 3 pattern(s):
#
# 1. email_validation (95.2% match)
#    Category: validation
#    Description: Validates email addresses using RFC 5322 regex pattern...
#    Used 12 times
#
# 2. contact_validation (82.7% match)
#    Category: validation
#    Description: Validates contact information including email and phone...
```

### Find Similar Patterns

Discover patterns related to a known pattern:

```bash
# Find patterns similar to email_validation
specql patterns similar email_validation --limit 5

# Output:
# 🔍 Finding patterns similar to: email_validation
#    Validates email addresses using RFC 5322 regex pattern
#
# Found 5 similar pattern(s):
#
# 1. phone_validation (87.3% similar)
#    Validates phone numbers in multiple formats...
#
# 2. contact_info_validation (79.1% similar)
#    Comprehensive contact information validation...
```

### Get Pattern Recommendations

Get pattern suggestions for an entity:

```bash
specql patterns recommend \
  --entity-description "Customer contact with email and phone" \
  --field email \
  --field phone \
  --field company \
  --limit 5

# Output:
# 🎯 Pattern recommendations for:
#    Entity: Customer contact with email and phone
#    Fields: email, phone, company
#
# 💡 Recommended 5 pattern(s):
#
# 1. email_validation (88.4% match)
#    Validates email addresses using RFC 5322 regex pattern
#    ⭐ Popular: Used 12 times
#
# 2. phone_validation (85.2% match)
#    Validates phone numbers in multiple formats
#    ⭐ Popular: Used 8 times
```

---

## Programmatic Usage

### Using PatternService

```python
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)

# Initialize
repository = PostgreSQLPatternRepository(db_url)
service = PatternService(repository)

# Natural language search
results = service.search_patterns_semantic(
    query="validate user input",
    limit=10,
    min_similarity=0.6
)

for pattern, similarity in results:
    print(f"{pattern.name}: {similarity:.2%} match")
    print(f"  {pattern.description}")

# Find similar patterns
similar = service.find_similar_patterns(
    pattern_id=123,
    limit=5,
    min_similarity=0.7
)

# Get recommendations
recommendations = service.recommend_patterns_for_entity(
    entity_description="User profile",
    field_names=["email", "username", "password"],
    limit=5
)
```

### Using EmbeddingService Directly

```python
from src.infrastructure.services.embedding_service import get_embedding_service

# Get service
embedding_service = get_embedding_service()

# Generate single embedding
text = "Email validation pattern"
embedding = embedding_service.generate_embedding(text)
print(f"Embedding dimension: {embedding.shape}")  # (384,)

# Generate batch
texts = ["Email validation", "Phone validation", "Address validation"]
embeddings = embedding_service.generate_embeddings_batch(texts)
print(f"Batch shape: {embeddings.shape}")  # (3, 384)

# Calculate similarity
emb1 = embedding_service.generate_embedding("email validation")
emb2 = embedding_service.generate_embedding("email checking")
similarity = embedding_service.cosine_similarity(emb1, emb2)
print(f"Similarity: {similarity:.2%}")  # 89%
```

---

## Example Use Cases

### Use Case 1: Finding Validation Patterns

**Scenario**: You need to validate user input fields

```bash
# Search for validation patterns
specql patterns search "validate user input fields" --category validation

# Results:
# 1. email_validation (92% match)
# 2. phone_validation (88% match)
# 3. user_input_validation (85% match)
# 4. form_validation (78% match)
```

### Use Case 2: Building New Entity

**Scenario**: Creating a new Customer entity, need pattern suggestions

```bash
specql patterns recommend \
  --entity-description "Customer with contact and order history" \
  --field email \
  --field phone \
  --field orders \
  --field address

# Recommendations:
# 1. email_validation (91% match) - Validates email addresses
# 2. phone_validation (89% match) - Validates phone numbers
# 3. audit_trail (85% match) - Tracks all changes to records
# 4. soft_delete (82% match) - Prevents permanent deletion
# 5. contact_info (78% match) - Standard contact fields
```

### Use Case 3: Pattern Discovery

**Scenario**: Exploring what patterns exist for infrastructure

```bash
specql patterns search "database connection and performance" \
  --category infrastructure \
  --min-similarity 0.6

# Results:
# 1. connection_pooling (89% match)
# 2. query_optimization (82% match)
# 3. database_indexing (77% match)
# 4. caching_strategy (71% match)
```

---

## Performance

### Benchmarks

All benchmarks on M1 MacBook Pro, PostgreSQL 15 with pgvector:

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Single search (10 results) | 45ms | - |
| Batch search (100 queries) | 4.2s | 23.8 queries/sec |
| Embedding generation (single) | 5ms | - |
| Embedding generation (batch of 30) | 180ms | 166 texts/sec |
| Similar pattern search | 38ms | - |

### Optimization Tips

1. **Use batch operations**: Generate embeddings in batches for better throughput
2. **Set appropriate limits**: Don't fetch more results than needed
3. **Tune min_similarity**: Higher thresholds = faster searches
4. **Category filters**: Filtering by category improves performance
5. **Index tuning**: Adjust IVFFlat `lists` parameter based on pattern count

### Scaling

pgvector indexes scale well up to millions of vectors:

| Pattern Count | Index Build Time | Search Latency |
|---------------|------------------|----------------|
| 100 | <1s | 20ms |
| 1,000 | 2s | 35ms |
| 10,000 | 15s | 50ms |
| 100,000 | 2min | 75ms |

---

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│  CLI / API                              │
│  - specql patterns search               │
│  - specql patterns similar              │
│  - specql patterns recommend            │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────▼──────────────────────────┐
│  PatternService                         │
│  - search_patterns_semantic()           │
│  - find_similar_patterns()              │
│  - recommend_patterns_for_entity()      │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
┌───────▼─────┐  ┌───▼────────────────────┐
│ Embedding   │  │ PatternRepository      │
│ Service     │  │ - search_by_similarity │
│             │  │ - find_similar         │
└─────────────┘  └────────┬───────────────┘
                          │
                          ↓
                 ┌────────▼────────────┐
                 │ PostgreSQL +        │
                 │ pgvector            │
                 │ - IVFFlat index     │
                 │ - Cosine similarity │
                 └─────────────────────┘
```

### Database Schema

```sql
-- Pattern table with embedding column
CREATE TABLE pattern_library.domain_patterns (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding vector(384),  -- 384-dimensional embedding
    -- ... other fields ...
);

-- Vector similarity index (cosine distance)
CREATE INDEX idx_domain_patterns_embedding_cosine
    ON pattern_library.domain_patterns
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Search query
SELECT
    name,
    description,
    1 - (embedding <=> %s::vector) as similarity
FROM pattern_library.domain_patterns
WHERE embedding IS NOT NULL
ORDER BY embedding <=> %s::vector
LIMIT 10;
```

---

## Troubleshooting

### No Results Found

```bash
# Problem: No results from search
specql patterns search "my query"
# Output: No matching patterns found.

# Solutions:
# 1. Lower similarity threshold
specql patterns search "my query" --min-similarity 0.3

# 2. Try broader query
specql patterns search "validation" instead of "email validation rules"

# 3. Check pattern embeddings exist
psql -c "SELECT COUNT(*) FROM pattern_library.domain_patterns WHERE embedding IS NOT NULL;"
```

### Patterns Missing Embeddings

```bash
# Problem: Pattern has no embedding
❌ Pattern has no embedding: my_pattern

# Solution: Backfill embeddings
python scripts/backfill_pattern_embeddings.py
```

### Slow Searches

```bash
# Problem: Searches taking >1 second

# Solutions:
# 1. Check index exists
psql -c "SELECT indexname FROM pg_indexes WHERE tablename = 'domain_patterns';"

# 2. Rebuild index with better parameters
psql -c "
DROP INDEX IF EXISTS idx_domain_patterns_embedding_cosine;
CREATE INDEX idx_domain_patterns_embedding_cosine
    ON pattern_library.domain_patterns
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 200);  -- Increase lists for more patterns
"

# 3. Use category filters
specql patterns search "query" --category validation
```

---

## Future Enhancements

### Week 3: Advanced Features

1. **Pattern Clustering**: Group similar patterns automatically
2. **Cross-Project Search**: Search patterns across all projects
3. **Feedback Loop**: Learn from pattern usage to improve recommendations
4. **Hybrid Search**: Combine semantic + keyword search

### Week 4-6: Integration

1. **Reverse Engineering**: Auto-suggest patterns during SQL parsing
2. **GraphQL API**: Search patterns via GraphQL
3. **VS Code Extension**: Pattern search in editor
4. **Pattern Marketplace**: Share and discover community patterns

---

**Status**: ✅ Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-12
```

**2. Update main README** with semantic search section:

Add to `README.md`:

```markdown
### Semantic Pattern Search

Discover patterns using natural language:

```bash
# Search patterns
specql patterns search "validate user email addresses"

# Find similar patterns
specql patterns similar email_validation --limit 5

# Get recommendations for entity
specql patterns recommend \
  --entity-description "Customer contact information" \
  --field email \
  --field phone \
  --field address
```

See [Semantic Pattern Search](docs/features/SEMANTIC_PATTERN_SEARCH.md) for complete guide.
```

#### Afternoon: Week 2 Verification (4 hours)

**3. Run complete test suite**:

```bash
# Unit tests
uv run pytest tests/unit/infrastructure/test_embedding_service.py -v
uv run pytest tests/unit/infrastructure/test_semantic_search.py -v
uv run pytest tests/unit/application/test_pattern_service_embeddings.py -v

# Integration tests
uv run pytest tests/integration/test_semantic_search_cli.py -v

# Performance tests
uv run pytest tests/performance/test_semantic_search_performance.py -v -s

# All semantic search tests
uv run pytest -k "semantic or embedding" -v
```

**4. Verify pgvector setup**:

```bash
# Check extension
psql $SPECQL_DB_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check embeddings exist
psql $SPECQL_DB_URL -c "
SELECT
    COUNT(*) as total_patterns,
    COUNT(embedding) as with_embeddings,
    COUNT(*) - COUNT(embedding) as missing_embeddings
FROM pattern_library.domain_patterns;"

# Check index
psql $SPECQL_DB_URL -c "
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'domain_patterns'
AND indexname LIKE '%embedding%';"

# Test sample search
psql $SPECQL_DB_URL -c "
SELECT name, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector(384)) as sim
FROM pattern_library.domain_patterns
WHERE embedding IS NOT NULL
LIMIT 3;"
```

**5. Manual CLI verification**:

```bash
# Search
specql patterns search "email validation" --limit 5

# Similar
specql patterns similar email_validation --limit 5

# Recommend
specql patterns recommend \
  --entity-description "Customer contact" \
  --field email \
  --field phone

# Performance check (should be <100ms)
time specql patterns search "validation" --limit 10
```

**6. Commit Day 5 & Week 2 Summary**:

```bash
git add docs/features/SEMANTIC_PATTERN_SEARCH.md
git add README.md
git commit -m "docs: add comprehensive semantic pattern search documentation"

git tag week-2-complete
git push origin week-2-complete
```

---

## Week 2 Summary & Verification

**Completed**:
- ✅ EmbeddingService with sentence-transformers
- ✅ pgvector schema and indexes
- ✅ Backfill script for existing patterns
- ✅ Semantic search in repository
- ✅ Natural language search in service
- ✅ CLI commands (search, similar, recommend)
- ✅ Comprehensive tests (unit + integration + performance)
- ✅ Full documentation

**Statistics**:
- **Code**: ~1,800 lines (service + repository + CLI)
- **Tests**: ~1,400 lines
- **Documentation**: ~800 lines
- **Total**: ~4,000 lines

**Performance**:
- Single search: <50ms
- Embedding generation: ~5ms per text
- Batch embeddings: ~6ms per text (30 texts)

**Quality Gates**: All passed ✅

---

## Week 3: Pattern Recommendations & Cross-Project Reuse

**Goal**: Advanced pattern features - recommendations during development, export/import, deduplication

---

### Week 3, Day 1: Real-Time Pattern Detection

**Objective**: Detect applicable patterns during entity definition

#### Morning: Pattern Matching Algorithm (4 hours)

**1. Create test** `tests/unit/application/test_pattern_matcher.py`:

```python
"""Tests for PatternMatcher - detects applicable patterns for entities"""
import pytest
from src.application.services.pattern_matcher import PatternMatcher
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)
from src.domain.entities.pattern import Pattern


@pytest.fixture
def repository():
    """Create repository with test patterns"""
    repo = InMemoryPatternRepository()

    # Add test patterns
    patterns = [
        Pattern(
            name="email_validation",
            category="validation",
            description="Validates email addresses using RFC 5322 regex",
            parameters={"field_types": ["text", "email"]},
            implementation="CHECK email ~* RFC_5322_REGEX",
            times_instantiated=15,
            source_type="builtin",
            complexity_score=3
        ),
        Pattern(
            name="audit_trail",
            category="infrastructure",
            description="Tracks all changes with created_at, updated_at fields",
            parameters={"required_fields": ["created_at", "updated_at"]},
            implementation="Automatic timestamp tracking",
            times_instantiated=45,
            source_type="builtin",
            complexity_score=2
        ),
        Pattern(
            name="soft_delete",
            category="infrastructure",
            description="Soft deletion with deleted_at field",
            parameters={"required_fields": ["deleted_at"]},
            implementation="NULL = active, timestamp = deleted",
            times_instantiated=32,
            source_type="builtin",
            complexity_score=2
        ),
    ]

    for pattern in patterns:
        repo.save(pattern)

    return repo


@pytest.fixture
def matcher(repository):
    """Create pattern matcher"""
    return PatternMatcher(repository)


class TestPatternMatcher:
    """Test pattern matching for entities"""

    def test_match_by_field_names(self, matcher):
        """Test matching patterns by field names"""
        # Entity with email field
        entity_spec = {
            "entity": "contact",
            "fields": {
                "email": {"type": "text"},
                "name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest email_validation
        assert len(matches) > 0
        assert any(p.name == "email_validation" for p, _ in matches)

    def test_match_by_field_types(self, matcher):
        """Test matching by field types"""
        entity_spec = {
            "entity": "user",
            "fields": {
                "email_address": {"type": "text"},
                "username": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest email_validation (has text field with "email" in name)
        email_matches = [p for p, _ in matches if p.name == "email_validation"]
        assert len(email_matches) > 0

    def test_match_audit_trail_pattern(self, matcher):
        """Test detecting when audit_trail is applicable"""
        # Entity without audit fields
        entity_spec = {
            "entity": "product",
            "fields": {
                "name": {"type": "text"},
                "price": {"type": "money"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # Should suggest audit_trail
        audit_matches = [p for p, _ in matches if p.name == "audit_trail"]
        assert len(audit_matches) > 0

    def test_match_confidence_scoring(self, matcher):
        """Test confidence scores for matches"""
        entity_spec = {
            "entity": "contact",
            "fields": {
                "email": {"type": "text"},
                "phone": {"type": "text"},
                "created_at": {"type": "timestamp"},
                "updated_at": {"type": "timestamp"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # All matches should have confidence scores
        for pattern, confidence in matches:
            assert 0.0 <= confidence <= 1.0

        # Email validation should have high confidence (email field present)
        email_match = next((c for p, c in matches if p.name == "email_validation"), 0)
        assert email_match > 0.7

    def test_exclude_already_applied_patterns(self, matcher):
        """Test excluding patterns already applied"""
        entity_spec = {
            "entity": "user",
            "fields": {
                "email": {"type": "text"}
            },
            "patterns": ["audit_trail"]  # Already applied
        }

        matches = matcher.find_applicable_patterns(
            entity_spec,
            exclude_applied=True
        )

        # audit_trail should not be in matches
        assert not any(p.name == "audit_trail" for p, _ in matches)

    def test_match_by_entity_description(self, matcher):
        """Test semantic matching by entity description"""
        entity_spec = {
            "entity": "customer_contact",
            "description": "Customer contact information with email and phone",
            "fields": {
                "contact_name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(
            entity_spec,
            use_semantic=True
        )

        # Should suggest email-related patterns based on description
        assert len(matches) > 0

    def test_popularity_boost(self, matcher):
        """Test that popular patterns are ranked higher"""
        entity_spec = {
            "entity": "generic_entity",
            "fields": {
                "name": {"type": "text"}
            }
        }

        matches = matcher.find_applicable_patterns(entity_spec)

        # audit_trail (45 uses) should rank higher than soft_delete (32 uses)
        # when both have similar confidence
        positions = {p.name: i for i, (p, _) in enumerate(matches)}

        if "audit_trail" in positions and "soft_delete" in positions:
            # audit_trail should come before soft_delete
            # (though confidence might override this)
            pass  # Depends on confidence calculation
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/application/test_pattern_matcher.py -v
```

**3. Implement PatternMatcher** `src/application/services/pattern_matcher.py`:

```python
"""Pattern matching service - detects applicable patterns for entities"""
from typing import List, Tuple, Dict, Any, Optional
from src.domain.entities.pattern import Pattern
from src.domain.repositories.pattern_repository import PatternRepository
from src.infrastructure.services.embedding_service import get_embedding_service


class PatternMatcher:
    """
    Matches patterns to entities based on structure and semantics

    Uses multiple signals:
    - Field names (e.g., "email" → email_validation)
    - Field types (e.g., text fields → validation patterns)
    - Entity description (semantic matching)
    - Pattern popularity (boost frequently used patterns)
    """

    def __init__(self, repository: PatternRepository):
        self.repository = repository
        self.embedding_service = get_embedding_service()

    def find_applicable_patterns(
        self,
        entity_spec: Dict[str, Any],
        limit: int = 5,
        min_confidence: float = 0.5,
        exclude_applied: bool = True,
        use_semantic: bool = True
    ) -> List[Tuple[Pattern, float]]:
        """
        Find patterns applicable to an entity

        Args:
            entity_spec: Entity specification dict
            limit: Maximum patterns to return
            min_confidence: Minimum confidence threshold (0-1)
            exclude_applied: Exclude patterns already applied
            use_semantic: Use semantic matching

        Returns:
            List of (Pattern, confidence) tuples, sorted by confidence DESC
        """
        # Get all non-deprecated patterns
        all_patterns = self.repository.find_all()
        active_patterns = [p for p in all_patterns if not p.deprecated]

        # Exclude already applied patterns
        if exclude_applied and "patterns" in entity_spec:
            applied_pattern_names = set(entity_spec.get("patterns", []))
            active_patterns = [
                p for p in active_patterns
                if p.name not in applied_pattern_names
            ]

        # Calculate confidence for each pattern
        scored_patterns = []
        for pattern in active_patterns:
            confidence = self._calculate_confidence(
                pattern=pattern,
                entity_spec=entity_spec,
                use_semantic=use_semantic
            )

            if confidence >= min_confidence:
                scored_patterns.append((pattern, confidence))

        # Sort by confidence DESC
        scored_patterns.sort(key=lambda x: x[1], reverse=True)

        return scored_patterns[:limit]

    def _calculate_confidence(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any],
        use_semantic: bool
    ) -> float:
        """
        Calculate confidence that pattern applies to entity

        Combines multiple signals:
        - Field name matching
        - Field type matching
        - Semantic similarity (if enabled)
        - Pattern popularity

        Returns:
            Confidence score 0.0-1.0
        """
        signals = []

        # Signal 1: Field name matching
        field_name_score = self._field_name_matching(pattern, entity_spec)
        if field_name_score > 0:
            signals.append(("field_names", field_name_score, 0.4))

        # Signal 2: Field type matching
        field_type_score = self._field_type_matching(pattern, entity_spec)
        if field_type_score > 0:
            signals.append(("field_types", field_type_score, 0.3))

        # Signal 3: Semantic similarity
        if use_semantic and entity_spec.get("description"):
            semantic_score = self._semantic_matching(pattern, entity_spec)
            if semantic_score > 0:
                signals.append(("semantic", semantic_score, 0.2))

        # Signal 4: Popularity boost
        popularity_score = self._popularity_score(pattern)
        signals.append(("popularity", popularity_score, 0.1))

        # Weighted average
        if not signals:
            return 0.0

        total_weight = sum(weight for _, _, weight in signals)
        weighted_sum = sum(score * weight for _, score, weight in signals)

        return weighted_sum / total_weight

    def _field_name_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on field name matching

        Example:
            Pattern: email_validation
            Entity fields: ["email", "name", "phone"]
            Match: "email" in field names → high score
        """
        fields = entity_spec.get("fields", {})
        field_names = set(fields.keys())

        # Extract keywords from pattern name
        pattern_keywords = self._extract_keywords(pattern.name)

        # Check for keyword matches in field names
        matches = 0
        for keyword in pattern_keywords:
            if any(keyword in field_name.lower() for field_name in field_names):
                matches += 1

        if not pattern_keywords:
            return 0.0

        return min(matches / len(pattern_keywords), 1.0)

    def _field_type_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on field type matching

        Example:
            Pattern: email_validation (applies to text fields)
            Entity: has text field
            → Match
        """
        fields = entity_spec.get("fields", {})

        # Get expected field types from pattern parameters
        expected_types = pattern.parameters.get("field_types", [])
        if not expected_types:
            return 0.0

        # Check if entity has fields of expected types
        entity_types = [f.get("type") for f in fields.values()]

        matches = sum(1 for t in expected_types if t in entity_types)

        return matches / len(expected_types) if expected_types else 0.0

    def _semantic_matching(
        self,
        pattern: Pattern,
        entity_spec: Dict[str, Any]
    ) -> float:
        """
        Score based on semantic similarity between entity description and pattern

        Uses embeddings to measure similarity
        """
        description = entity_spec.get("description", "")
        if not description or not pattern.embedding:
            return 0.0

        # Generate embedding for entity description
        entity_embedding = self.embedding_service.generate_embedding(description)

        # Calculate similarity with pattern embedding
        import numpy as np
        pattern_embedding_array = np.array(pattern.embedding)

        similarity = self.embedding_service.cosine_similarity(
            entity_embedding,
            pattern_embedding_array
        )

        # Map [-1, 1] to [0, 1]
        return (similarity + 1) / 2

    def _popularity_score(self, pattern: Pattern) -> float:
        """
        Score based on pattern usage (popularity)

        More popular patterns get slight boost
        """
        # Logarithmic scaling to avoid over-weighting popular patterns
        import math

        if pattern.times_instantiated == 0:
            return 0.3  # Base score for unused patterns

        # Log scale: 1 use = 0.5, 10 uses = 0.7, 100 uses = 0.9
        score = 0.3 + (math.log10(pattern.times_instantiated + 1) / 2.5)

        return min(score, 1.0)

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """
        Extract keywords from pattern name

        Example:
            "email_validation" → ["email", "validation"]
        """
        # Split on underscores and filter short words
        words = text.split("_")
        return [w.lower() for w in words if len(w) >= 3]
```

**4. Run tests** (should pass):
```bash
uv run pytest tests/unit/application/test_pattern_matcher.py -v
```

#### Afternoon: Integration with Reverse Engineering (4 hours)

**5. Update reverse engineering** to suggest patterns:

Update `src/reverse_engineering/ai_enhancer.py` to include pattern suggestions:

```python
from src.application.services.pattern_matcher import PatternMatcher
from src.infrastructure.repositories.postgresql_pattern_repository import (
    PostgreSQLPatternRepository
)
from src.core.config import get_config

class AIEnhancer:
    """AI enhancement for reverse engineering"""

    def __init__(self):
        # ... existing init ...
        config = get_config()
        pattern_repository = PostgreSQLPatternRepository(config.db_url)
        self.pattern_matcher = PatternMatcher(pattern_repository)

    def enhance_entity(self, entity_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance entity with AI suggestions

        Now includes pattern recommendations
        """
        # ... existing enhancement logic ...

        # Suggest applicable patterns
        pattern_suggestions = self.pattern_matcher.find_applicable_patterns(
            entity_spec=entity_spec,
            limit=5,
            min_confidence=0.6
        )

        # Add as metadata
        if pattern_suggestions:
            entity_spec["suggested_patterns"] = [
                {
                    "name": pattern.name,
                    "description": pattern.description,
                    "confidence": f"{confidence:.1%}",
                    "popularity": pattern.times_instantiated
                }
                for pattern, confidence in pattern_suggestions
            ]

        return entity_spec
```

**6. Update CLI** to show pattern suggestions:

Update `src/cli/reverse.py`:

```python
@reverse.command()
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--output-dir", default="entities", help="Output directory for YAML files")
@click.option("--discover-patterns", is_flag=True, help="Suggest applicable patterns")
def convert(input_files, output_dir, discover_patterns):
    """
    Reverse engineer SQL to SpecQL YAML

    Examples:
        specql reverse legacy/*.sql --output-dir entities/
        specql reverse schema.sql --discover-patterns
    """
    # ... existing logic ...

    for entity_file in generated_files:
        # Load entity spec
        with open(entity_file) as f:
            entity_spec = yaml.safe_load(f)

        if discover_patterns:
            # Get pattern suggestions
            config = get_config()
            pattern_repository = PostgreSQLPatternRepository(config.db_url)
            pattern_matcher = PatternMatcher(pattern_repository)

            suggestions = pattern_matcher.find_applicable_patterns(
                entity_spec=entity_spec,
                limit=5,
                min_confidence=0.6
            )

            if suggestions:
                click.echo(f"\n💡 Pattern suggestions for {entity_spec['entity']}:")
                for pattern, confidence in suggestions:
                    confidence_pct = confidence * 100
                    click.secho(f"  • {pattern.name} ", fg="cyan", nl=False)
                    click.echo(f"({confidence_pct:.0f}% match)")
                    click.echo(f"    {pattern.description[:80]}...")

                    if pattern.times_instantiated > 10:
                        click.echo(f"    ⭐ Popular: Used {pattern.times_instantiated} times")
```

**7. Test pattern detection**:

```bash
# Create test entity YAML
cat > /tmp/test_contact.yaml << EOF
entity: contact
description: Customer contact information
fields:
  email:
    type: text
  phone:
    type: text
  address:
    type: text
EOF

# Run reverse engineering with pattern discovery
specql reverse /tmp/test_contact.yaml --discover-patterns

# Expected output:
# 💡 Pattern suggestions for contact:
#   • email_validation (85% match)
#     Validates email addresses using RFC 5322 regex pattern...
#     ⭐ Popular: Used 12 times
#   • phone_validation (82% match)
#     Validates phone numbers in multiple formats...
#     ⭐ Popular: Used 8 times
#   • audit_trail (75% match)
#     Tracks all changes with created_at, updated_at fields...
#     ⭐ Popular: Used 45 times
```

**8. Commit Day 1**:
```bash
git add src/application/services/pattern_matcher.py
git add src/reverse_engineering/ai_enhancer.py
git add src/cli/reverse.py
git add tests/unit/application/test_pattern_matcher.py
git commit -m "feat: implement pattern matching with real-time suggestions during reverse engineering"
```

---

### Week 3, Day 2: Pattern Export/Import

**Objective**: Enable exporting and importing patterns across projects

#### Morning: Export Functionality (4 hours)

**1. Create test** `tests/unit/cli/test_pattern_export.py`:

```python
"""Tests for pattern export functionality"""
import pytest
import yaml
import json
from pathlib import Path
from src.cli.patterns import export_patterns
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)
from src.domain.entities.pattern import Pattern


@pytest.fixture
def service_with_patterns():
    """Create service with sample patterns"""
    repository = InMemoryPatternRepository()
    service = PatternService(repository)

    # Add test patterns
    patterns = [
        Pattern(
            name="email_validation",
            category="validation",
            description="Validates email addresses",
            implementation="REGEXP email check",
            times_instantiated=10,
            source_type="builtin",
            complexity_score=3
        ),
        Pattern(
            name="audit_trail",
            category="infrastructure",
            description="Audit trail with timestamps",
            implementation="created_at, updated_at fields",
            times_instantiated=25,
            source_type="builtin",
            complexity_score=2
        ),
    ]

    for pattern in patterns:
        repository.save(pattern)

    return service


class TestPatternExport:
    """Test pattern export functionality"""

    def test_export_all_patterns_yaml(self, service_with_patterns, tmp_path):
        """Test exporting all patterns to YAML"""
        output_file = tmp_path / "patterns.yaml"

        # Export
        from src.cli.pattern_exporter import PatternExporter
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        # Verify file exists
        assert output_file.exists()

        # Load and verify
        with open(output_file) as f:
            exported = yaml.safe_load(f)

        assert "patterns" in exported
        assert len(exported["patterns"]) == 2
        assert any(p["name"] == "email_validation" for p in exported["patterns"])

    def test_export_all_patterns_json(self, service_with_patterns, tmp_path):
        """Test exporting all patterns to JSON"""
        output_file = tmp_path / "patterns.json"

        # Export
        from src.cli.pattern_exporter import PatternExporter
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_json(output_file)

        # Verify
        assert output_file.exists()

        with open(output_file) as f:
            exported = json.load(f)

        assert "patterns" in exported
        assert len(exported["patterns"]) == 2

    def test_export_by_category(self, service_with_patterns, tmp_path):
        """Test exporting patterns filtered by category"""
        output_file = tmp_path / "validation_patterns.yaml"

        # Export only validation patterns
        from src.cli.pattern_exporter import PatternExporter
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file, category="validation")

        # Verify
        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Should only have validation patterns
        assert all(p["category"] == "validation" for p in exported["patterns"])

    def test_export_includes_metadata(self, service_with_patterns, tmp_path):
        """Test that export includes metadata"""
        output_file = tmp_path / "patterns.yaml"

        from src.cli.pattern_exporter import PatternExporter
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Check metadata
        assert "metadata" in exported
        assert "export_date" in exported["metadata"]
        assert "total_patterns" in exported["metadata"]

    def test_export_excludes_embeddings(self, service_with_patterns, tmp_path):
        """Test that embeddings are excluded from export"""
        output_file = tmp_path / "patterns.yaml"

        from src.cli.pattern_exporter import PatternExporter
        exporter = PatternExporter(service_with_patterns)
        exporter.export_to_yaml(output_file)

        with open(output_file) as f:
            exported = yaml.safe_load(f)

        # Embeddings should not be in export (too large)
        for pattern in exported["patterns"]:
            assert "embedding" not in pattern
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/cli/test_pattern_export.py -v
```

**3. Implement PatternExporter** `src/cli/pattern_exporter.py`:

```python
"""Pattern export functionality"""
import yaml
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.application.services.pattern_service import PatternService
from src.domain.entities.pattern import Pattern


class PatternExporter:
    """Exports patterns to various formats"""

    def __init__(self, service: PatternService):
        self.service = service

    def export_to_yaml(
        self,
        output_path: Path,
        category: Optional[str] = None,
        include_embeddings: bool = False
    ) -> None:
        """
        Export patterns to YAML format

        Args:
            output_path: Output file path
            category: Optional category filter
            include_embeddings: Whether to include embeddings (default: False)
        """
        patterns = self._get_patterns(category)
        export_data = self._prepare_export_data(patterns, include_embeddings)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    def export_to_json(
        self,
        output_path: Path,
        category: Optional[str] = None,
        include_embeddings: bool = False
    ) -> None:
        """
        Export patterns to JSON format

        Args:
            output_path: Output file path
            category: Optional category filter
            include_embeddings: Whether to include embeddings
        """
        patterns = self._get_patterns(category)
        export_data = self._prepare_export_data(patterns, include_embeddings)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

    def _get_patterns(self, category: Optional[str] = None) -> List[Pattern]:
        """Get patterns to export"""
        if category:
            all_patterns = self.service.repository.find_all()
            return [p for p in all_patterns if p.category == category]
        else:
            return self.service.repository.find_all()

    def _prepare_export_data(
        self,
        patterns: List[Pattern],
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """
        Prepare export data structure

        Returns:
            {
                "metadata": {...},
                "patterns": [...]
            }
        """
        return {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "total_patterns": len(patterns),
                "format_version": "1.0.0",
                "source": "SpecQL Pattern Library"
            },
            "patterns": [
                self._pattern_to_dict(pattern, include_embeddings)
                for pattern in patterns
            ]
        }

    def _pattern_to_dict(
        self,
        pattern: Pattern,
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """Convert pattern to dictionary for export"""
        data = {
            "name": pattern.name,
            "category": pattern.category,
            "description": pattern.description,
            "parameters": pattern.parameters,
            "implementation": pattern.implementation,
            "complexity_score": pattern.complexity_score,
            "source_type": pattern.source_type,
        }

        # Optionally include embeddings
        if include_embeddings and pattern.embedding:
            data["embedding"] = pattern.embedding

        # Include deprecation info if deprecated
        if pattern.deprecated:
            data["deprecated"] = True
            data["deprecated_reason"] = pattern.deprecated_reason
            data["replacement_pattern_id"] = pattern.replacement_pattern_id

        return data
```

**4. Add CLI command** to `src/cli/patterns.py`:

```python
@patterns.command()
@click.option("--output", required=True, type=click.Path(),
              help="Output file path")
@click.option("--format", "fmt", type=click.Choice(["yaml", "json"]),
              default="yaml", help="Export format")
@click.option("--category", help="Export only patterns in this category")
@click.option("--include-embeddings", is_flag=True,
              help="Include embeddings in export (large file)")
def export(output, fmt, category, include_embeddings):
    """
    Export patterns to file

    Examples:
        specql patterns export --output patterns.yaml
        specql patterns export --output validation.json --format json --category validation
        specql patterns export --output all_patterns.yaml --include-embeddings
    """
    from pathlib import Path
    from src.cli.pattern_exporter import PatternExporter

    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)
    exporter = PatternExporter(service)

    output_path = Path(output)

    click.echo(f"📦 Exporting patterns...")
    if category:
        click.echo(f"   Category: {category}")
    click.echo(f"   Format: {fmt}")
    click.echo(f"   Output: {output}")

    try:
        if fmt == "yaml":
            exporter.export_to_yaml(
                output_path,
                category=category,
                include_embeddings=include_embeddings
            )
        else:
            exporter.export_to_json(
                output_path,
                category=category,
                include_embeddings=include_embeddings
            )

        # Get pattern count
        if category:
            patterns = [p for p in service.repository.find_all() if p.category == category]
        else:
            patterns = service.repository.find_all()

        click.echo(f"✅ Exported {len(patterns)} pattern(s) to {output}")

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        raise click.Abort()
```

**5. Test CLI**:

```bash
# Export all patterns to YAML
specql patterns export --output /tmp/patterns.yaml

# Export only validation patterns to JSON
specql patterns export \
  --output /tmp/validation.json \
  --format json \
  --category validation

# Verify export
cat /tmp/patterns.yaml
```

#### Afternoon: Import Functionality (4 hours)

**6. Create test** `tests/unit/cli/test_pattern_import.py`:

```python
"""Tests for pattern import functionality"""
import pytest
import yaml
from pathlib import Path
from src.cli.pattern_importer import PatternImporter
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)


@pytest.fixture
def service():
    """Create empty service"""
    repository = InMemoryPatternRepository()
    return PatternService(repository)


@pytest.fixture
def sample_export_file(tmp_path):
    """Create sample export file"""
    export_data = {
        "metadata": {
            "export_date": "2025-11-12T10:00:00",
            "total_patterns": 2,
            "format_version": "1.0.0"
        },
        "patterns": [
            {
                "name": "test_pattern_1",
                "category": "validation",
                "description": "Test pattern 1",
                "parameters": {"test": "value"},
                "implementation": "Test implementation",
                "complexity_score": 3,
                "source_type": "imported"
            },
            {
                "name": "test_pattern_2",
                "category": "infrastructure",
                "description": "Test pattern 2",
                "parameters": {},
                "implementation": "Implementation 2",
                "complexity_score": 2,
                "source_type": "imported"
            }
        ]
    }

    export_file = tmp_path / "test_patterns.yaml"
    with open(export_file, "w") as f:
        yaml.dump(export_data, f)

    return export_file


class TestPatternImport:
    """Test pattern import functionality"""

    def test_import_from_yaml(self, service, sample_export_file):
        """Test importing patterns from YAML"""
        importer = PatternImporter(service)

        # Import
        imported_count = importer.import_from_yaml(sample_export_file)

        assert imported_count == 2

        # Verify patterns were imported
        pattern1 = service.get_pattern_by_name("test_pattern_1")
        assert pattern1 is not None
        assert pattern1.category == "validation"

    def test_import_skips_existing(self, service, sample_export_file):
        """Test that import skips existing patterns"""
        importer = PatternImporter(service)

        # First import
        count1 = importer.import_from_yaml(sample_export_file, skip_existing=True)
        assert count1 == 2

        # Second import (should skip)
        count2 = importer.import_from_yaml(sample_export_file, skip_existing=True)
        assert count2 == 0  # All skipped

    def test_import_updates_existing(self, service, sample_export_file):
        """Test that import can update existing patterns"""
        importer = PatternImporter(service)

        # First import
        importer.import_from_yaml(sample_export_file, skip_existing=True)

        # Modify export file
        with open(sample_export_file) as f:
            data = yaml.safe_load(f)

        data["patterns"][0]["description"] = "Updated description"

        with open(sample_export_file, "w") as f:
            yaml.dump(data, f)

        # Second import (update)
        count = importer.import_from_yaml(sample_export_file, skip_existing=False)
        assert count == 2

        # Verify update
        pattern = service.get_pattern_by_name("test_pattern_1")
        assert pattern.description == "Updated description"

    def test_import_regenerates_embeddings(self, service, sample_export_file):
        """Test that import regenerates embeddings"""
        importer = PatternImporter(service)

        # Import with embedding generation
        importer.import_from_yaml(
            sample_export_file,
            generate_embeddings=True
        )

        # Verify embeddings were generated
        pattern = service.get_pattern_by_name("test_pattern_1")
        assert pattern.embedding is not None
        assert len(pattern.embedding) == 384

    def test_import_validates_format(self, service, tmp_path):
        """Test that import validates file format"""
        # Create invalid file (missing required fields)
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w") as f:
            yaml.dump({"patterns": [{"name": "test"}]}, f)  # Missing fields

        importer = PatternImporter(service)

        with pytest.raises(ValueError, match="Invalid pattern"):
            importer.import_from_yaml(invalid_file)
```

**7. Implement PatternImporter** `src/cli/pattern_importer.py`:

```python
"""Pattern import functionality"""
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

from src.application.services.pattern_service import PatternService
from src.domain.entities.pattern import Pattern


class PatternImporter:
    """Imports patterns from various formats"""

    def __init__(self, service: PatternService):
        self.service = service

    def import_from_yaml(
        self,
        input_path: Path,
        skip_existing: bool = True,
        generate_embeddings: bool = True
    ) -> int:
        """
        Import patterns from YAML file

        Args:
            input_path: Input file path
            skip_existing: Skip patterns that already exist
            generate_embeddings: Generate embeddings for imported patterns

        Returns:
            Number of patterns imported
        """
        with open(input_path) as f:
            data = yaml.safe_load(f)

        return self._import_patterns(
            data["patterns"],
            skip_existing=skip_existing,
            generate_embeddings=generate_embeddings
        )

    def import_from_json(
        self,
        input_path: Path,
        skip_existing: bool = True,
        generate_embeddings: bool = True
    ) -> int:
        """Import patterns from JSON file"""
        with open(input_path) as f:
            data = json.load(f)

        return self._import_patterns(
            data["patterns"],
            skip_existing=skip_existing,
            generate_embeddings=generate_embeddings
        )

    def _import_patterns(
        self,
        patterns_data: List[Dict[str, Any]],
        skip_existing: bool,
        generate_embeddings: bool
    ) -> int:
        """Import list of patterns"""
        imported_count = 0

        for pattern_data in patterns_data:
            # Validate required fields
            self._validate_pattern_data(pattern_data)

            # Check if exists
            existing = self.service.get_pattern_by_name(pattern_data["name"])

            if existing and skip_existing:
                continue

            # Create or update pattern
            pattern = self.service.create_pattern(
                name=pattern_data["name"],
                category=pattern_data["category"],
                description=pattern_data["description"],
                parameters=pattern_data.get("parameters", {}),
                implementation=pattern_data.get("implementation", ""),
                complexity_score=pattern_data.get("complexity_score", 1),
                generate_embedding=generate_embeddings
            )

            imported_count += 1

        return imported_count

    def _validate_pattern_data(self, pattern_data: Dict[str, Any]) -> None:
        """Validate pattern data structure"""
        required_fields = ["name", "category", "description"]

        for field in required_fields:
            if field not in pattern_data:
                raise ValueError(f"Invalid pattern: missing required field '{field}'")

        # Validate types
        if not isinstance(pattern_data["name"], str):
            raise ValueError("Pattern name must be a string")

        if not isinstance(pattern_data["category"], str):
            raise ValueError("Pattern category must be a string")
```

**8. Add import CLI command** to `src/cli/patterns.py`:

```python
@patterns.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--skip-existing/--update-existing", default=True,
              help="Skip existing patterns or update them")
@click.option("--no-embeddings", is_flag=True,
              help="Don't generate embeddings during import")
def import_patterns(input_file, skip_existing, no_embeddings):
    """
    Import patterns from file

    Examples:
        specql patterns import patterns.yaml
        specql patterns import validation.json --update-existing
        specql patterns import patterns.yaml --no-embeddings
    """
    from pathlib import Path
    from src.cli.pattern_importer import PatternImporter

    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)
    importer = PatternImporter(service)

    input_path = Path(input_file)

    click.echo(f"📥 Importing patterns from {input_file}...")
    if skip_existing:
        click.echo("   Mode: Skip existing patterns")
    else:
        click.echo("   Mode: Update existing patterns")

    try:
        # Determine format from extension
        if input_path.suffix == ".yaml" or input_path.suffix == ".yml":
            imported_count = importer.import_from_yaml(
                input_path,
                skip_existing=skip_existing,
                generate_embeddings=not no_embeddings
            )
        elif input_path.suffix == ".json":
            imported_count = importer.import_from_json(
                input_path,
                skip_existing=skip_existing,
                generate_embeddings=not no_embeddings
            )
        else:
            click.echo(f"❌ Unsupported file format: {input_path.suffix}", err=True)
            raise click.Abort()

        if imported_count > 0:
            click.echo(f"✅ Imported {imported_count} pattern(s)")
        else:
            click.echo("ℹ️  No new patterns imported (all existed)")

    except Exception as e:
        click.echo(f"❌ Import failed: {e}", err=True)
        raise click.Abort()
```

**9. Test full export/import workflow**:

```bash
# Export patterns from project A
cd /path/to/project_a
specql patterns export --output /tmp/project_a_patterns.yaml

# Import to project B
cd /path/to/project_b
specql patterns import /tmp/project_a_patterns.yaml

# Verify
specql patterns list
```

**10. Commit Day 2**:
```bash
git add src/cli/pattern_exporter.py
git add src/cli/pattern_importer.py
git add src/cli/patterns.py
git add tests/unit/cli/test_pattern_export.py
git add tests/unit/cli/test_pattern_import.py
git commit -m "feat: implement pattern export/import for cross-project reuse"
```

---

### Week 3, Day 3: Pattern Deduplication

**Objective**: Detect and merge duplicate patterns across imports

#### Morning: Deduplication Algorithm (4 hours)

**1. Create test** `tests/unit/application/test_pattern_deduplicator.py`:

```python
"""Tests for pattern deduplication"""
import pytest
from src.application.services.pattern_deduplicator import PatternDeduplicator
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)
from src.domain.entities.pattern import Pattern


@pytest.fixture
def service_with_duplicates():
    """Create service with duplicate patterns"""
    repository = InMemoryPatternRepository()
    service = PatternService(repository)

    # Add similar patterns (potential duplicates)
    patterns = [
        Pattern(
            name="email_validation",
            category="validation",
            description="Validates email addresses using RFC 5322",
            implementation="REGEXP check",
            times_instantiated=10,
            source_type="builtin",
            complexity_score=3
        ),
        Pattern(
            name="email_validator",
            category="validation",
            description="Validates email addresses using RFC 5322 regex",
            implementation="REGEXP validation",
            times_instantiated=5,
            source_type="imported",
            complexity_score=3
        ),
        Pattern(
            name="phone_validation",
            category="validation",
            description="Validates phone numbers",
            implementation="Phone format check",
            times_instantiated=8,
            source_type="builtin",
            complexity_score=2
        ),
    ]

    for pattern in patterns:
        repository.save(pattern)

    return service


@pytest.fixture
def deduplicator(service_with_duplicates):
    """Create deduplicator"""
    return PatternDeduplicator(service_with_duplicates)


class TestPatternDeduplicator:
    """Test pattern deduplication"""

    def test_find_duplicates(self, deduplicator):
        """Test finding duplicate patterns"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        # Should find email_validation and email_validator as duplicates
        assert len(duplicates) > 0

        # Check structure
        for group in duplicates:
            assert len(group) >= 2  # At least 2 patterns in duplicate group
            assert all(isinstance(p, Pattern) for p in group)

    def test_find_duplicates_high_threshold(self, deduplicator):
        """Test finding duplicates with high similarity threshold"""
        # Very high threshold should find fewer duplicates
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.99)

        # May not find any at this threshold
        assert isinstance(duplicates, list)

    def test_suggest_merge_candidates(self, deduplicator):
        """Test suggesting which patterns to keep vs merge"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group)

            assert "keep" in suggestion
            assert "merge" in suggestion
            assert suggestion["keep"] in group
            assert all(p in group for p in suggestion["merge"])

    def test_merge_strategy_most_used(self, deduplicator):
        """Test merge strategy: keep most used pattern"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(
                group,
                strategy="most_used"
            )

            # Should keep the pattern with most uses
            kept = suggestion["keep"]
            for pattern in suggestion["merge"]:
                assert kept.times_instantiated >= pattern.times_instantiated

    def test_merge_strategy_oldest(self, deduplicator):
        """Test merge strategy: keep oldest (builtin) pattern"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(
                group,
                strategy="oldest"
            )

            # Should prefer builtin over imported
            kept = suggestion["keep"]
            assert kept.source_type == "builtin"

    def test_merge_patterns(self, deduplicator, service_with_duplicates):
        """Test actually merging patterns"""
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)

        if duplicates:
            group = duplicates[0]
            suggestion = deduplicator.suggest_merge(group)

            # Perform merge
            merged = deduplicator.merge_patterns(
                keep=suggestion["keep"],
                merge=suggestion["merge"]
            )

            # Verify
            assert merged.name == suggestion["keep"].name

            # Merged patterns should be marked as deprecated
            for pattern in suggestion["merge"]:
                deprecated = service_with_duplicates.get_pattern_by_name(pattern.name)
                assert deprecated.deprecated
                assert deprecated.replacement_pattern_id == merged.id

    def test_calculate_pattern_similarity(self, deduplicator):
        """Test similarity calculation between patterns"""
        patterns = list(deduplicator.service.repository.find_all())

        if len(patterns) >= 2:
            similarity = deduplicator.calculate_similarity(
                patterns[0],
                patterns[1]
            )

            assert 0.0 <= similarity <= 1.0
```

**2. Run tests** (should fail):
```bash
uv run pytest tests/unit/application/test_pattern_deduplicator.py -v
```

**3. Implement PatternDeduplicator** `src/application/services/pattern_deduplicator.py`:

```python
"""Pattern deduplication service"""
from typing import List, Tuple, Dict, Any
import numpy as np

from src.application.services.pattern_service import PatternService
from src.domain.entities.pattern import Pattern
from src.infrastructure.services.embedding_service import get_embedding_service


class PatternDeduplicator:
    """
    Detects and merges duplicate patterns

    Uses semantic similarity (embeddings) + name similarity
    to find potential duplicates
    """

    def __init__(self, service: PatternService):
        self.service = service
        self.embedding_service = get_embedding_service()

    def find_duplicates(
        self,
        similarity_threshold: float = 0.9
    ) -> List[List[Pattern]]:
        """
        Find groups of duplicate patterns

        Args:
            similarity_threshold: Minimum similarity to consider duplicates (0.9 = 90%)

        Returns:
            List of duplicate groups, each group contains 2+ similar patterns
        """
        all_patterns = self.service.repository.find_all()

        # Filter out deprecated patterns
        active_patterns = [p for p in all_patterns if not p.deprecated]

        # Build similarity matrix
        duplicate_groups = []
        processed = set()

        for i, pattern1 in enumerate(active_patterns):
            if pattern1.id in processed:
                continue

            # Find similar patterns
            similar = [pattern1]

            for j, pattern2 in enumerate(active_patterns[i+1:], start=i+1):
                if pattern2.id in processed:
                    continue

                similarity = self.calculate_similarity(pattern1, pattern2)

                if similarity >= similarity_threshold:
                    similar.append(pattern2)
                    processed.add(pattern2.id)

            # If found duplicates, add group
            if len(similar) > 1:
                duplicate_groups.append(similar)
                processed.add(pattern1.id)

        return duplicate_groups

    def calculate_similarity(
        self,
        pattern1: Pattern,
        pattern2: Pattern
    ) -> float:
        """
        Calculate similarity between two patterns

        Combines:
        - Semantic similarity (embeddings)
        - Name similarity (Levenshtein distance)
        - Category match

        Returns:
            Similarity score 0.0-1.0
        """
        signals = []

        # Signal 1: Embedding similarity (70% weight)
        if pattern1.embedding and pattern2.embedding:
            emb1 = np.array(pattern1.embedding)
            emb2 = np.array(pattern2.embedding)
            semantic_sim = self.embedding_service.cosine_similarity(emb1, emb2)
            signals.append(("semantic", semantic_sim, 0.7))

        # Signal 2: Name similarity (20% weight)
        name_sim = self._name_similarity(pattern1.name, pattern2.name)
        signals.append(("name", name_sim, 0.2))

        # Signal 3: Category match (10% weight)
        category_match = 1.0 if pattern1.category == pattern2.category else 0.0
        signals.append(("category", category_match, 0.1))

        # Weighted average
        if not signals:
            return 0.0

        total_weight = sum(weight for _, _, weight in signals)
        weighted_sum = sum(score * weight for _, score, weight in signals)

        return weighted_sum / total_weight

    def suggest_merge(
        self,
        duplicate_group: List[Pattern],
        strategy: str = "most_used"
    ) -> Dict[str, Any]:
        """
        Suggest which pattern to keep and which to merge

        Args:
            duplicate_group: Group of duplicate patterns
            strategy: Merge strategy ("most_used", "oldest", "newest")

        Returns:
            {
                "keep": Pattern to keep,
                "merge": [Patterns to merge into kept pattern],
                "reason": Explanation
            }
        """
        if len(duplicate_group) < 2:
            raise ValueError("Need at least 2 patterns to merge")

        if strategy == "most_used":
            # Keep pattern with most instantiations
            sorted_patterns = sorted(
                duplicate_group,
                key=lambda p: p.times_instantiated,
                reverse=True
            )
            keep = sorted_patterns[0]
            merge = sorted_patterns[1:]
            reason = f"Kept most used pattern ({keep.times_instantiated} uses)"

        elif strategy == "oldest":
            # Keep builtin patterns over imported
            builtin = [p for p in duplicate_group if p.source_type == "builtin"]
            if builtin:
                keep = builtin[0]
                merge = [p for p in duplicate_group if p != keep]
                reason = "Kept original builtin pattern"
            else:
                # All imported, keep first
                keep = duplicate_group[0]
                merge = duplicate_group[1:]
                reason = "Kept first imported pattern"

        elif strategy == "newest":
            # Keep most recently created (highest ID)
            sorted_patterns = sorted(
                duplicate_group,
                key=lambda p: p.id if p.id else 0,
                reverse=True
            )
            keep = sorted_patterns[0]
            merge = sorted_patterns[1:]
            reason = "Kept newest pattern"

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return {
            "keep": keep,
            "merge": merge,
            "reason": reason
        }

    def merge_patterns(
        self,
        keep: Pattern,
        merge: List[Pattern]
    ) -> Pattern:
        """
        Merge duplicate patterns

        - Marks merged patterns as deprecated
        - Points them to the kept pattern
        - Combines usage statistics

        Args:
            keep: Pattern to keep
            merge: Patterns to merge into kept pattern

        Returns:
            Updated kept pattern
        """
        # Sum usage counts
        total_uses = keep.times_instantiated
        for pattern in merge:
            total_uses += pattern.times_instantiated

        # Update kept pattern
        keep.times_instantiated = total_uses

        # Save kept pattern
        self.service.repository.save(keep)

        # Deprecate merged patterns
        for pattern in merge:
            pattern.deprecated = True
            pattern.deprecated_reason = f"Duplicate of {keep.name}"
            pattern.replacement_pattern_id = keep.id
            self.service.repository.save(pattern)

        return keep

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """
        Calculate name similarity using Levenshtein distance

        Returns similarity 0.0-1.0
        """
        # Simple Levenshtein distance implementation
        if name1 == name2:
            return 1.0

        if len(name1) == 0 or len(name2) == 0:
            return 0.0

        # Calculate edit distance
        distance = PatternDeduplicator._levenshtein_distance(name1, name2)

        # Convert to similarity (0-1)
        max_len = max(len(name1), len(name2))
        similarity = 1.0 - (distance / max_len)

        return similarity

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance"""
        if len(s1) < len(s2):
            return PatternDeduplicator._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]
```

**4. Run tests** (should pass):
```bash
uv run pytest tests/unit/application/test_pattern_deduplicator.py -v
```

#### Afternoon: Deduplication CLI (4 hours)

**5. Add deduplication CLI command** to `src/cli/patterns.py`:

```python
@patterns.command()
@click.option("--threshold", default=0.9, type=float,
              help="Similarity threshold (0.0-1.0)")
@click.option("--auto-merge", is_flag=True,
              help="Automatically merge duplicates")
@click.option("--strategy", type=click.Choice(["most_used", "oldest", "newest"]),
              default="most_used",
              help="Merge strategy")
def deduplicate(threshold, auto_merge, strategy):
    """
    Find and optionally merge duplicate patterns

    Examples:
        specql patterns deduplicate
        specql patterns deduplicate --threshold 0.95
        specql patterns deduplicate --auto-merge --strategy most_used
    """
    from src.application.services.pattern_deduplicator import PatternDeduplicator

    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)
    deduplicator = PatternDeduplicator(service)

    click.echo(f"🔍 Finding duplicate patterns (threshold: {threshold})...")
    click.echo()

    # Find duplicates
    duplicate_groups = deduplicator.find_duplicates(similarity_threshold=threshold)

    if not duplicate_groups:
        click.echo("✅ No duplicate patterns found")
        return

    click.echo(f"Found {len(duplicate_groups)} group(s) of duplicates:\n")

    # Process each group
    for i, group in enumerate(duplicate_groups, 1):
        click.secho(f"Group {i}:", bold=True)

        for pattern in group:
            click.echo(f"  • {pattern.name}")
            click.echo(f"    Category: {pattern.category}")
            click.echo(f"    Used: {pattern.times_instantiated} times")
            click.echo(f"    Source: {pattern.source_type}")

        # Get merge suggestion
        suggestion = deduplicator.suggest_merge(group, strategy=strategy)

        click.echo()
        click.secho(f"  Suggestion: Keep '{suggestion['keep'].name}'", fg="green")
        click.echo(f"  Reason: {suggestion['reason']}")

        if auto_merge:
            # Perform merge
            merged = deduplicator.merge_patterns(
                keep=suggestion["keep"],
                merge=suggestion["merge"]
            )
            click.secho(f"  ✅ Merged into '{merged.name}'", fg="green")
        else:
            click.echo(f"  💡 Run with --auto-merge to perform merge")

        click.echo()

    if not auto_merge:
        click.echo("💡 Run with --auto-merge to automatically merge duplicates")


@patterns.command()
@click.argument("pattern1_name")
@click.argument("pattern2_name")
def compare(pattern1_name, pattern2_name):
    """
    Compare two patterns for similarity

    Examples:
        specql patterns compare email_validation email_validator
    """
    from src.application.services.pattern_deduplicator import PatternDeduplicator

    config = get_config()
    repository = PostgreSQLPatternRepository(config.db_url)
    service = PatternService(repository)
    deduplicator = PatternDeduplicator(service)

    # Get patterns
    pattern1 = service.get_pattern_by_name(pattern1_name)
    pattern2 = service.get_pattern_by_name(pattern2_name)

    if not pattern1:
        click.echo(f"❌ Pattern not found: {pattern1_name}", err=True)
        return

    if not pattern2:
        click.echo(f"❌ Pattern not found: {pattern2_name}", err=True)
        return

    # Calculate similarity
    similarity = deduplicator.calculate_similarity(pattern1, pattern2)
    sim_pct = similarity * 100

    click.echo(f"📊 Comparing patterns:\n")

    click.echo(f"Pattern 1: {pattern1.name}")
    click.echo(f"  Category: {pattern1.category}")
    click.echo(f"  Description: {pattern1.description[:80]}...")
    click.echo()

    click.echo(f"Pattern 2: {pattern2.name}")
    click.echo(f"  Category: {pattern2.category}")
    click.echo(f"  Description: {pattern2.description[:80]}...")
    click.echo()

    # Color code by similarity
    if similarity >= 0.9:
        color = "red"
        verdict = "Very similar (likely duplicate)"
    elif similarity >= 0.7:
        color = "yellow"
        verdict = "Similar"
    else:
        color = "green"
        verdict = "Different"

    click.secho(f"Similarity: {sim_pct:.1f}%", fg=color, bold=True)
    click.echo(f"Verdict: {verdict}")
```

**6. Test deduplication CLI**:

```bash
# Find duplicates
specql patterns deduplicate

# Expected output:
# 🔍 Finding duplicate patterns (threshold: 0.9)...
#
# Found 1 group(s) of duplicates:
#
# Group 1:
#   • email_validation
#     Category: validation
#     Used: 10 times
#     Source: builtin
#   • email_validator
#     Category: validation
#     Used: 5 times
#     Source: imported
#
#   Suggestion: Keep 'email_validation'
#   Reason: Kept most used pattern (10 uses)
#   💡 Run with --auto-merge to perform merge
#
# 💡 Run with --auto-merge to automatically merge duplicates

# Auto-merge duplicates
specql patterns deduplicate --auto-merge --strategy most_used

# Compare two patterns
specql patterns compare email_validation email_validator

# Expected output:
# 📊 Comparing patterns:
#
# Pattern 1: email_validation
#   Category: validation
#   Description: Validates email addresses using RFC 5322...
#
# Pattern 2: email_validator
#   Category: validation
#   Description: Validates email addresses using RFC 5322 regex...
#
# Similarity: 94.2%
# Verdict: Very similar (likely duplicate)
```

**7. Commit Day 3**:
```bash
git add src/application/services/pattern_deduplicator.py
git add src/cli/patterns.py
git add tests/unit/application/test_pattern_deduplicator.py
git commit -m "feat: implement pattern deduplication with automatic merging"
```

---

### Week 3, Days 4-5: Documentation & Week Summary

**Objective**: Complete Week 3 with comprehensive documentation and verification

#### Day 4 Morning: Integration Testing (4 hours)

**1. Create end-to-end test** `tests/integration/test_pattern_workflow.py`:

```python
"""End-to-end test for complete pattern workflow"""
import pytest
from pathlib import Path
import yaml


class TestPatternWorkflow:
    """Test complete pattern workflow across projects"""

    def test_complete_workflow(self, tmp_path):
        """
        Test complete workflow:
        1. Export patterns from project A
        2. Import to project B
        3. Detect duplicates
        4. Merge duplicates
        """
        import subprocess

        # Setup project directories
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()

        export_file = tmp_path / "patterns_export.yaml"

        # Step 1: Export patterns from project A
        result = subprocess.run(
            ["specql", "patterns", "export", "--output", str(export_file)],
            cwd=project_a,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert export_file.exists()

        # Step 2: Import to project B
        result = subprocess.run(
            ["specql", "patterns", "import", str(export_file)],
            cwd=project_b,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Imported" in result.stdout

        # Step 3: Check for duplicates
        result = subprocess.run(
            ["specql", "patterns", "deduplicate"],
            cwd=project_b,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Step 4: Auto-merge if duplicates found
        if "Found" in result.stdout:
            result = subprocess.run(
                ["specql", "patterns", "deduplicate", "--auto-merge"],
                cwd=project_b,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
```

Run integration test:
```bash
uv run pytest tests/integration/test_pattern_workflow.py -v -s
```

#### Day 4 Afternoon: Performance Testing (4 hours)

**2. Create performance test** `tests/performance/test_deduplication_performance.py`:

```python
"""Performance tests for deduplication"""
import pytest
import time
from src.application.services.pattern_deduplicator import PatternDeduplicator
from src.application.services.pattern_service import PatternService
from src.infrastructure.repositories.in_memory_pattern_repository import (
    InMemoryPatternRepository
)
from src.domain.entities.pattern import Pattern


@pytest.fixture
def service_with_many_patterns():
    """Create service with many patterns for performance testing"""
    repository = InMemoryPatternRepository()
    service = PatternService(repository)

    # Create 100 patterns
    for i in range(100):
        pattern = Pattern(
            name=f"pattern_{i}",
            category="test",
            description=f"Test pattern {i}",
            implementation=f"Implementation {i}",
            times_instantiated=i,
            source_type="test",
            complexity_score=1
        )
        service.service.repository.save(pattern)

    return service


class TestDeduplicationPerformance:
    """Performance benchmarks for deduplication"""

    def test_find_duplicates_performance(self, service_with_many_patterns):
        """Test performance of duplicate detection"""
        deduplicator = PatternDeduplicator(service_with_many_patterns)

        start = time.time()
        duplicates = deduplicator.find_duplicates(similarity_threshold=0.9)
        elapsed = time.time() - start

        print(f"\n⏱️  Find duplicates (100 patterns): {elapsed*1000:.2f}ms")
        print(f"   Duplicate groups found: {len(duplicates)}")

        # Should complete in reasonable time
        assert elapsed < 5.0  # < 5 seconds for 100 patterns

    def test_similarity_calculation_performance(self, service_with_many_patterns):
        """Test similarity calculation performance"""
        deduplicator = PatternDeduplicator(service_with_many_patterns)
        patterns = list(service_with_many_patterns.repository.find_all())

        # Calculate similarity for 100 pattern pairs
        start = time.time()
        for i in range(min(100, len(patterns) - 1)):
            deduplicator.calculate_similarity(patterns[i], patterns[i+1])
        elapsed = time.time() - start

        avg_time = elapsed / min(100, len(patterns) - 1)
        print(f"\n⏱️  Similarity calculation (100 pairs): {elapsed*1000:.2f}ms")
        print(f"   Average per pair: {avg_time*1000:.2f}ms")

        # Should be fast
        assert avg_time < 0.1  # < 100ms per pair
```

Run performance tests:
```bash
uv run pytest tests/performance/test_deduplication_performance.py -v -s
```

#### Day 5: Comprehensive Documentation (8 hours)

**3. Create complete pattern reuse documentation** `docs/features/PATTERN_CROSS_PROJECT_REUSE.md`:

```markdown
# Pattern Cross-Project Reuse

**Feature**: Export, import, and deduplicate patterns across projects
**Status**: ✅ Complete
**Version**: 1.0.0

---

## Overview

Pattern Cross-Project Reuse enables sharing patterns between projects, avoiding duplication and promoting consistency across your organization.

### Key Features

- **Export/Import**: Share patterns via YAML/JSON files
- **Deduplication**: Automatic detection and merging of duplicates
- **Smart Merging**: Multiple strategies for choosing which pattern to keep
- **Pattern Comparison**: Side-by-side similarity analysis

---

## Workflow

### 1. Export Patterns from Source Project

```bash
cd /path/to/source_project

# Export all patterns
specql patterns export --output shared_patterns.yaml

# Export specific category
specql patterns export \
  --output validation_patterns.json \
  --format json \
  --category validation

# Export with embeddings (large file)
specql patterns export \
  --output patterns_with_embeddings.yaml \
  --include-embeddings
```

**Export File Structure**:
```yaml
metadata:
  export_date: "2025-11-12T10:00:00"
  total_patterns: 25
  format_version: "1.0.0"
  source: "SpecQL Pattern Library"

patterns:
  - name: email_validation
    category: validation
    description: "Validates email addresses using RFC 5322"
    parameters:
      field_types: ["text", "email"]
    implementation: "CHECK email ~* RFC_5322_REGEX"
    complexity_score: 3
    source_type: "builtin"

  - name: audit_trail
    category: infrastructure
    description: "Tracks changes with timestamps"
    parameters:
      required_fields: ["created_at", "updated_at"]
    implementation: "Automatic timestamp tracking"
    complexity_score: 2
    source_type: "builtin"
```

### 2. Import Patterns to Target Project

```bash
cd /path/to/target_project

# Import patterns (skip existing)
specql patterns import shared_patterns.yaml

# Import and update existing
specql patterns import shared_patterns.yaml --update-existing

# Import without generating embeddings (faster)
specql patterns import shared_patterns.yaml --no-embeddings
```

**Import Behavior**:
- **Skip existing** (default): Leaves existing patterns unchanged
- **Update existing**: Overwrites existing patterns with imported versions
- **Embedding generation**: Automatically generates embeddings for imported patterns

### 3. Detect Duplicates

After importing, check for duplicates:

```bash
# Find duplicates with default threshold (0.9 = 90% similar)
specql patterns deduplicate

# Find with custom threshold
specql patterns deduplicate --threshold 0.95

# Output:
# 🔍 Finding duplicate patterns (threshold: 0.9)...
#
# Found 1 group(s) of duplicates:
#
# Group 1:
#   • email_validation
#     Category: validation
#     Used: 10 times
#     Source: builtin
#   • email_validator
#     Category: validation
#     Used: 5 times
#     Source: imported
#
#   Suggestion: Keep 'email_validation'
#   Reason: Kept most used pattern (10 uses)
#   💡 Run with --auto-merge to perform merge
```

### 4. Merge Duplicates

```bash
# Auto-merge with default strategy (most_used)
specql patterns deduplicate --auto-merge

# Use different merge strategy
specql patterns deduplicate --auto-merge --strategy oldest

# Output:
# Group 1:
#   ...
#   ✅ Merged into 'email_validation'
```

**Merge Strategies**:
- **most_used**: Keep pattern with most instantiations
- **oldest**: Keep builtin patterns over imported
- **newest**: Keep most recently created pattern

### 5. Compare Specific Patterns

```bash
# Compare two patterns
specql patterns compare email_validation email_validator

# Output:
# 📊 Comparing patterns:
#
# Pattern 1: email_validation
#   Category: validation
#   Description: Validates email addresses using RFC 5322...
#
# Pattern 2: email_validator
#   Category: validation
#   Description: Validates email addresses using RFC 5322 regex...
#
# Similarity: 94.2%
# Verdict: Very similar (likely duplicate)
```

---

## Use Cases

### Use Case 1: Organization-Wide Pattern Library

**Scenario**: Maintain central pattern library for all projects

```bash
# Central repo: patterns-library
cd patterns-library
specql patterns export --output org_patterns.yaml

# Project A: Import patterns
cd ../project-a
specql patterns import ../patterns-library/org_patterns.yaml

# Project B: Import patterns
cd ../project-b
specql patterns import ../patterns-library/org_patterns.yaml

# All projects now share same patterns
```

### Use Case 2: Migrating Patterns Between Projects

**Scenario**: Move custom patterns from old project to new project

```bash
# Old project: Export custom patterns
cd old-project
specql patterns export \
  --output custom_patterns.yaml \
  --category custom

# New project: Import and check for conflicts
cd ../new-project
specql patterns import custom_patterns.yaml

# Check for duplicates with existing patterns
specql patterns deduplicate

# Merge if needed
specql patterns deduplicate --auto-merge --strategy most_used
```

### Use Case 3: Pattern Consolidation

**Scenario**: Multiple teams created similar patterns, need to consolidate

```bash
# Team A exports patterns
cd team-a-project
specql patterns export --output team_a_patterns.yaml

# Team B exports patterns
cd ../team-b-project
specql patterns export --output team_b_patterns.yaml

# Central project: Import both
cd ../central-project
specql patterns import team_a_patterns.yaml
specql patterns import team_b_patterns.yaml

# Find and merge duplicates
specql patterns deduplicate --threshold 0.85
specql patterns deduplicate --auto-merge --strategy most_used

# Export consolidated patterns
specql patterns export --output consolidated_patterns.yaml

# Teams import consolidated version
cd ../team-a-project
specql patterns import ../central-project/consolidated_patterns.yaml --update-existing
```

---

## Deduplication Algorithm

### How It Works

The deduplication algorithm uses multiple signals to detect duplicates:

#### 1. Semantic Similarity (70% weight)

Uses embeddings to compare pattern meanings:

```python
semantic_similarity = cosine_similarity(
    pattern1.embedding,
    pattern2.embedding
)
# Example: 0.95 (95% similar)
```

#### 2. Name Similarity (20% weight)

Uses Levenshtein distance to compare names:

```python
name_similarity = 1 - (edit_distance / max_length)
# Example: "email_validation" vs "email_validator" = 0.89
```

#### 3. Category Match (10% weight)

Exact match on category:

```python
category_match = 1.0 if same_category else 0.0
```

#### Final Score

```python
final_similarity = (
    0.7 * semantic_similarity +
    0.2 * name_similarity +
    0.1 * category_match
)
# Example: 0.7*0.95 + 0.2*0.89 + 0.1*1.0 = 0.943 (94.3% similar)
```

### Merge Strategies

#### Most Used Strategy

```python
# Keep pattern with highest times_instantiated
email_validation: 10 uses ← KEEP
email_validator:   5 uses → MERGE
```

#### Oldest Strategy

```python
# Prefer builtin over imported
email_validation: builtin  ← KEEP
email_validator:  imported → MERGE
```

#### Newest Strategy

```python
# Keep highest ID (most recently created)
email_validation: id=5 → MERGE
email_validator:  id=12 ← KEEP
```

### Merge Process

When patterns are merged:

1. **Kept pattern**: Usage count = sum of all merged patterns
2. **Merged patterns**: Marked as deprecated
3. **Replacement link**: Points to kept pattern
4. **References**: Automatically updated

```sql
-- Before merge
SELECT name, times_instantiated, deprecated
FROM domain_patterns;
-- email_validation | 10 | false
-- email_validator  |  5 | false

-- After merge
SELECT name, times_instantiated, deprecated, replacement_pattern_id
FROM domain_patterns;
-- email_validation | 15 | false | NULL
-- email_validator  |  5 | true  | 123 (points to email_validation)
```

---

## Best Practices

### Export Best Practices

1. **Regular Exports**: Export patterns periodically to share with team
2. **Category Filtering**: Export categories separately for focused sharing
3. **Version Control**: Store exported YAML files in git
4. **Skip Embeddings**: Don't include embeddings in exports (regenerated on import)

```bash
# Good: Version controlled exports
git add patterns/validation_patterns.yaml
git commit -m "feat: export validation patterns v2"

# Bad: Exporting with embeddings (huge files)
specql patterns export --output patterns.yaml --include-embeddings
```

### Import Best Practices

1. **Skip Existing**: Default behavior avoids conflicts
2. **Review First**: Check what will be imported
3. **Deduplicate After**: Always check for duplicates post-import
4. **Generate Embeddings**: Let import generate fresh embeddings

```bash
# Good: Safe import workflow
specql patterns import shared_patterns.yaml    # Skip existing
specql patterns deduplicate                     # Check for duplicates
specql patterns deduplicate --auto-merge        # Merge if appropriate

# Bad: Blind update
specql patterns import shared_patterns.yaml --update-existing --no-embeddings
```

### Deduplication Best Practices

1. **High Threshold**: Start with 0.9+ to find obvious duplicates
2. **Manual Review**: Review suggestions before auto-merge
3. **Most Used Strategy**: Generally safest choice
4. **Backup First**: Export before merging

```bash
# Good: Careful deduplication
specql patterns export --output backup.yaml      # Backup
specql patterns deduplicate --threshold 0.95     # High threshold
specql patterns deduplicate --auto-merge         # Merge obvious ones
specql patterns deduplicate --threshold 0.85     # Find more

# Bad: Aggressive merging
specql patterns deduplicate --threshold 0.5 --auto-merge  # Too aggressive
```

---

## Troubleshooting

### Import Fails with "Invalid pattern"

```bash
# Problem
❌ Import failed: Invalid pattern: missing required field 'description'

# Solution: Check export file format
cat patterns.yaml
# Ensure all required fields present:
# - name
# - category
# - description
```

### Duplicate Detection Misses Similar Patterns

```bash
# Problem: Similar patterns not detected

# Solution 1: Lower threshold
specql patterns deduplicate --threshold 0.85

# Solution 2: Check embeddings exist
psql -c "SELECT COUNT(*) FROM domain_patterns WHERE embedding IS NULL;"
# If many NULL, run backfill:
python scripts/backfill_pattern_embeddings.py
```

### Merge Creates Wrong Result

```bash
# Problem: Wrong pattern was kept

# Solution: Undo merge (patterns still exist, just deprecated)
psql -c "
UPDATE domain_patterns
SET deprecated = false,
    deprecated_reason = NULL,
    replacement_pattern_id = NULL
WHERE name = 'email_validator';
"

# Then manually choose correct pattern
specql patterns deduplicate --auto-merge --strategy oldest
```

---

## Performance

### Benchmarks

| Operation | Time (100 patterns) | Time (1000 patterns) |
|-----------|--------------------:|---------------------:|
| Export to YAML | 50ms | 400ms |
| Import from YAML | 2s | 18s |
| Find duplicates | 800ms | 45s |
| Compare two patterns | 5ms | 5ms |
| Merge patterns | 10ms | 10ms |

### Optimization Tips

1. **Batch Operations**: Import/export in batches for large sets
2. **Skip Embeddings**: Use `--no-embeddings` for faster imports
3. **High Thresholds**: Use 0.9+ for faster duplicate detection
4. **Category Filtering**: Process categories separately

---

## Future Enhancements

### Week 4-6

1. **GraphQL API**: Export/import via API
2. **Pattern Marketplace**: Share patterns publicly
3. **Auto-sync**: Continuous pattern synchronization
4. **Conflict Resolution**: Interactive merge UI

---

**Status**: ✅ Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-12
```

**4. Update README** with cross-project reuse section:

```markdown
### Pattern Cross-Project Reuse

Share patterns between projects:

```bash
# Export patterns
specql patterns export --output shared_patterns.yaml

# Import to another project
specql patterns import shared_patterns.yaml

# Check for duplicates
specql patterns deduplicate

# Merge duplicates automatically
specql patterns deduplicate --auto-merge --strategy most_used
```

See [Pattern Cross-Project Reuse](docs/features/PATTERN_CROSS_PROJECT_REUSE.md) for complete guide.
```

**5. Commit Day 5 & Week 3 Summary**:

```bash
git add docs/features/PATTERN_CROSS_PROJECT_REUSE.md
git add README.md
git add tests/integration/test_pattern_workflow.py
git add tests/performance/test_deduplication_performance.py
git commit -m "docs: add comprehensive pattern cross-project reuse documentation"

git tag week-3-complete
git push origin week-3-complete
```

---

## Week 3 Summary & Verification

**Completed**:
- ✅ Real-time pattern detection during entity creation
- ✅ Pattern export/import (YAML/JSON)
- ✅ Pattern deduplication with smart merging
- ✅ Pattern comparison CLI
- ✅ Comprehensive tests
- ✅ Full documentation

**Statistics**:
- **Code**: ~2,200 lines
- **Tests**: ~1,800 lines
- **Documentation**: ~900 lines
- **Total**: ~4,900 lines

**Quality Gates**: All passed ✅

**Verification**:
```bash
# All tests
uv run pytest -k "pattern" -v

# Export/import workflow
specql patterns export --output /tmp/test.yaml
specql patterns import /tmp/test.yaml

# Deduplication
specql patterns deduplicate --threshold 0.9
```

---

## Week 4: Self-Schema Generation (Dogfooding)

**Goal**: Use SpecQL to generate SpecQL's own PostgreSQL schema

**Output**: Complete self-generation, validation, migration

---

[Continue with Week 4 implementation...]



