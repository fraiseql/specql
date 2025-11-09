# Team A: Database Decisions Implementation Plan

**Team**: Parser & AST
**Impact**: LOW (validation only)
**Timeline**: Week 1 (1-2 days)
**Status**: 🔴 CRITICAL - Blocks Team B

---

## 📋 Overview

Team A must add **reserved field name validation** to prevent users from defining fields that conflict with framework-generated columns.

**Impact**: Minimal code changes, but critical for data integrity

---

## 🎯 Phase 1: Reserved Field Name Validation

### **Objective**: Reject user-defined fields that conflict with framework

### **Implementation**

#### **Step 1: Define Reserved Names**

**File**: `src/core/reserved_fields.py` (NEW)

```python
"""Reserved field names that cannot be used by end users."""

from typing import Set

# Primary Keys & Foreign Keys
RESERVED_PK_FK = {
    'id',                    # UUID external reference
    'tenant_id',            # Multi-tenant reference
}

# Deduplication Fields
RESERVED_DEDUPLICATION = {
    'identifier',           # Base identifier
    'sequence_number',      # Deduplication sequence
    'display_identifier',   # Computed identifier with #n suffix
}

# Hierarchy Fields (for hierarchical entities)
RESERVED_HIERARCHY = {
    'path',                 # LTREE path (INTEGER-based)
}

# Audit Fields
RESERVED_AUDIT = {
    'created_at',
    'created_by',
    'updated_at',
    'updated_by',
    'deleted_at',
    'deleted_by',
}

# Recalculation Audit
RESERVED_RECALCULATION_AUDIT = {
    'identifier_recalculated_at',
    'identifier_recalculated_by',
    'path_updated_at',
    'path_updated_by',
}

# Combine all reserved names
RESERVED_FIELD_NAMES: Set[str] = (
    RESERVED_PK_FK
    | RESERVED_DEDUPLICATION
    | RESERVED_HIERARCHY
    | RESERVED_AUDIT
    | RESERVED_RECALCULATION_AUDIT
)

# Reserved prefixes (dynamic naming)
RESERVED_PREFIXES = {
    'pk_',    # Primary keys: pk_location, pk_contact, etc.
    'fk_',    # Foreign keys: fk_parent_location, fk_company, etc.
}

def is_reserved_field_name(field_name: str) -> bool:
    """Check if a field name is reserved by the framework."""
    # Check exact matches
    if field_name in RESERVED_FIELD_NAMES:
        return True

    # Check prefixes
    for prefix in RESERVED_PREFIXES:
        if field_name.startswith(prefix):
            return True

    return False

def get_reserved_field_error_message(field_name: str) -> str:
    """Generate helpful error message for reserved field names."""
    return f"""
Field name '{field_name}' is reserved by the framework.

Reserved fields:
  - Primary/Foreign Keys: id, pk_*, fk_*, tenant_id
  - Deduplication: identifier, sequence_number, display_identifier
  - Hierarchy: path, fk_parent_*
  - Audit: created_at, updated_at, deleted_at, created_by, updated_by, deleted_by
  - Recalculation: identifier_recalculated_at, path_updated_at, etc.

Please choose a different field name.
""".strip()
```

---

#### **Step 2: Add Validation to Parser**

**File**: `src/core/specql_parser.py`

```python
from .reserved_fields import is_reserved_field_name, get_reserved_field_error_message
from .exceptions import SpecQLValidationError

class SpecQLParser:
    def parse_fields(self, entity_name: str, fields_dict: dict) -> list[FieldDefinition]:
        """Parse field definitions with reserved name validation."""
        parsed_fields = []

        for field_name, field_config in fields_dict.items():
            # VALIDATION: Check if field name is reserved
            if is_reserved_field_name(field_name):
                raise SpecQLValidationError(
                    entity=entity_name,
                    message=get_reserved_field_error_message(field_name)
                )

            # Parse field type
            field_def = self._parse_field_definition(field_name, field_config)
            parsed_fields.append(field_def)

        return parsed_fields

    def _parse_field_definition(self, name: str, config) -> FieldDefinition:
        """Parse individual field definition."""
        # ... existing parsing logic
```

---

#### **Step 3: Add Custom Exception**

**File**: `src/core/exceptions.py`

```python
class SpecQLValidationError(Exception):
    """Raised when SpecQL validation fails."""

    def __init__(self, entity: str, message: str):
        self.entity = entity
        self.message = message
        super().__init__(f"Validation error in entity '{entity}': {message}")
```

---

### **Testing**

#### **File**: `tests/unit/core/test_reserved_fields.py` (NEW)

```python
import pytest
from src.core.specql_parser import SpecQLParser
from src.core.exceptions import SpecQLValidationError

class TestReservedFieldNames:
    """Test that reserved field names are properly rejected."""

    def setup_method(self):
        self.parser = SpecQLParser()

    def test_reserved_exact_match(self):
        """Test exact reserved field names are rejected."""
        reserved_names = [
            'id', 'path', 'identifier', 'sequence_number',
            'created_at', 'updated_at', 'deleted_at'
        ]

        for field_name in reserved_names:
            yaml_content = f"""
            entity: TestEntity
            fields:
              {field_name}: text
            """

            with pytest.raises(SpecQLValidationError) as exc_info:
                self.parser.parse_yaml(yaml_content)

            assert field_name in str(exc_info.value)
            assert "reserved" in str(exc_info.value).lower()

    def test_reserved_prefix_pk(self):
        """Test pk_* prefix is rejected."""
        yaml_content = """
        entity: Location
        fields:
          pk_custom: integer
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        assert 'pk_custom' in str(exc_info.value)
        assert 'pk_*' in str(exc_info.value)

    def test_reserved_prefix_fk(self):
        """Test fk_* prefix is rejected."""
        yaml_content = """
        entity: Location
        fields:
          fk_custom: integer
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        assert 'fk_custom' in str(exc_info.value)

    def test_tenant_id_reserved(self):
        """Test tenant_id is reserved."""
        yaml_content = """
        entity: Location
        fields:
          tenant_id: text
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        assert 'tenant_id' in str(exc_info.value)

    def test_non_reserved_allowed(self):
        """Test non-reserved field names are allowed."""
        yaml_content = """
        entity: Location
        fields:
          name: text
          description: text
          custom_field: integer
        """

        # Should NOT raise
        result = self.parser.parse_yaml(yaml_content)
        assert result is not None
        assert len(result.fields) == 3

    def test_error_message_helpful(self):
        """Test error message is helpful to users."""
        yaml_content = """
        entity: Location
        fields:
          path: text
        """

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse_yaml(yaml_content)

        error_msg = str(exc_info.value)

        # Should contain helpful info
        assert 'path' in error_msg
        assert 'reserved' in error_msg.lower()
        assert 'different field name' in error_msg.lower()

        # Should list categories of reserved fields
        assert 'Primary/Foreign Keys' in error_msg or 'pk_*' in error_msg
        assert 'Audit' in error_msg or 'created_at' in error_msg
```

---

### **Acceptance Criteria**

- [ ] Reserved names defined in `reserved_fields.py`
- [ ] Validation added to `specql_parser.py`
- [ ] Custom exception `SpecQLValidationError` created
- [ ] All tests pass (100% coverage on validation logic)
- [ ] Error messages are clear and helpful

---

## 📊 Impact on Team A

### **Files Modified**
- `src/core/specql_parser.py` - Add validation call
- `src/core/reserved_fields.py` - NEW file
- `src/core/exceptions.py` - Add exception
- `tests/unit/core/test_reserved_fields.py` - NEW file

### **Effort Estimate**
- Implementation: 2-3 hours
- Testing: 1-2 hours
- **Total**: 0.5 days

### **Dependencies**
- None (Team A can start immediately)

### **Blocks**
- Team B (cannot start until reserved names are enforced)

---

## 🎯 Success Criteria

1. ✅ Users CANNOT define fields named: `id`, `path`, `identifier`, `created_at`, etc.
2. ✅ Users CANNOT define fields with prefixes: `pk_*`, `fk_*`
3. ✅ Error messages clearly explain which fields are reserved
4. ✅ Error messages suggest alternatives
5. ✅ All tests pass with 100% coverage

---

## 🚀 Rollout Plan

### **Phase 1.1: Implementation** (Day 1, Morning)
1. Create `reserved_fields.py` with all reserved names
2. Add `is_reserved_field_name()` validation function
3. Create `SpecQLValidationError` exception

### **Phase 1.2: Integration** (Day 1, Afternoon)
1. Add validation to `parse_fields()` method
2. Test with example SpecQL files
3. Ensure error messages are clear

### **Phase 1.3: Testing** (Day 2, Morning)
1. Write comprehensive test suite
2. Test all reserved names
3. Test reserved prefixes
4. Test error message quality

### **Phase 1.4: Documentation** (Day 2, Afternoon)
1. Update parser documentation
2. Add examples of valid/invalid field names
3. Document reserved field categories

---

## 📝 Example Usage

### **Invalid SpecQL (Should Fail)**

```yaml
# ❌ BAD - Uses reserved field name
entity: Location
fields:
  name: text
  path: text  # ERROR: "path" is reserved!
```

**Error Output**:
```
SpecQLValidationError: Validation error in entity 'Location':
Field name 'path' is reserved by the framework.

Reserved fields:
  - Primary/Foreign Keys: id, pk_*, fk_*, tenant_id
  - Deduplication: identifier, sequence_number, display_identifier
  - Hierarchy: path, fk_parent_*
  - Audit: created_at, updated_at, deleted_at, created_by, updated_by, deleted_by
  - Recalculation: identifier_recalculated_at, path_updated_at, etc.

Please choose a different field name.
```

### **Valid SpecQL (Should Pass)**

```yaml
# ✅ GOOD - Uses non-reserved field names
entity: Location
fields:
  name: text
  description: text
  location_type: ref(LocationType)
  custom_metadata: jsonb
```

---

## 🔗 Related Documentation

- `DATABASE_DECISIONS_FINAL.md` - Approved reserved field names
- `DATABASE_ASSESSMENT_GAPS.md` - Context and rationale
- Team B Schema Generation Plan - Depends on this validation

---

**Status**: 🔴 READY TO START
**Priority**: CRITICAL (blocks Team B)
**Effort**: 0.5 days
**Dependencies**: None
