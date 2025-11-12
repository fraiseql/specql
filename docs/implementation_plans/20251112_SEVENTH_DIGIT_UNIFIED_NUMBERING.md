# 7-Digit Unified Numbering System - Implementation Plan

**Date**: 2025-11-12
**Status**: Planning
**Complexity**: Medium
**Estimated Effort**: 3-5 days

---

## 🎯 Executive Summary

Implement **universal 7-digit numbering** (SSDSSEX format) across ALL schema layers to enable:
1. **Multiple functions per entity** (create, update, delete, custom actions)
2. **Multiple tables per entity** (main table + auxiliary tables like `_audit`, `_info`, `_node`)
3. **Multiple views per entity** (already supported for read-side)
4. **Consistent numbering across all layers**

---

## 📊 Current State Analysis

### Current Numbering Format

| Layer | Type | Current Digits | Format | Example | Problem |
|-------|------|----------------|--------|---------|---------|
| 01 | Write-side tables | **6** | SSDSSE | `012361` | ❌ Can't have multiple tables per entity |
| 02 | Read-side views | **7** ✅ | SSDSSEX | `0220310` | ✅ Already supports multiple views |
| 03 | Functions | **6** | SSDSSE | `032361` | ❌ Can't have multiple functions per entity |

### Format Breakdown

**Current 6-digit**: `SSDSSE`
- `SS` = Schema layer (01, 02, 03)
- `D` = Domain code (1-9)
- `SS` = Subdomain code (00-99)
- `E` = Entity sequence (0-9)

**Target 7-digit**: `SSDSSEX`
- `SS` = Schema layer (01, 02, 03)
- `D` = Domain code (1-9)
- `SS` = Subdomain code (00-99)
- `E` = Entity sequence (0-9)
- `X` = **File/Function sequence (0-9)** ⭐ NEW

---

## 🚨 Use Cases Requiring 7th Digit

### Use Case 1: Multiple Functions per Entity ⭐ PRIMARY

**Problem**: All actions for an entity would get the same 6-digit code.

**Example**: Contact entity with multiple actions
```yaml
entity: Contact
actions:
  - name: create_contact     # Need: 0323611
  - name: update_contact     # Need: 0323612
  - name: delete_contact     # Need: 0323613
  - name: qualify_lead       # Need: 0323614
  - name: convert_to_client  # Need: 0323615
```

**Current (6-digit)**: All get `032361` ❌ COLLISION!
**With 7-digit**: Each gets unique code ✅

### Use Case 2: Multiple Tables per Entity (Write-Side)

**Problem**: Auxiliary tables need their own codes.

#### 2a. Audit Tables
```sql
CREATE TABLE crm.tb_contact (...)        -- Main table: 0123611
CREATE TABLE crm.tb_contact_audit (...)  -- Audit: 0123612
```

#### 2b. Node+Info Split Pattern
For complex entities with >12 fields:
```sql
CREATE TABLE projects.tb_location_node (...)  -- Structure: 0142311
CREATE TABLE projects.tb_location_info (...)  -- Business data: 0142312
```

**Current (6-digit)**: Both get `012361` ❌ COLLISION!
**With 7-digit**: Each gets unique code ✅

#### 2c. Pairing Tables
For many-to-many relationships:
```sql
CREATE TABLE crm.tb_contact (...)             -- Main: 0123611
CREATE TABLE crm.tb_contact_company (...)     -- Junction: 0123612
```

### Use Case 3: Multiple Views per Entity (Read-Side) ✅ Already Works!

**Example**: Contact with multiple views
```sql
CREATE TABLE VIEW catalog.tv_contact (...)           -- 0220310
CREATE TABLE VIEW catalog.v_contact_with_company (...)  -- 0220320
CREATE MATERIALIZED VIEW catalog.mv_contact_cache (...)  -- 0220330
```

**Current (7-digit)**: ✅ Already supported!

---

## 🏗️ Implementation Design

### Phase 1: Update Core Numbering

#### 1.1 Update `naming_conventions.py`

**Current**:
```python
def derive_function_code(self, table_code: str) -> str:
    """Derive function code from table code by changing schema layer to 03"""
    if len(table_code) != 6:
        raise ValueError(f"Invalid table code format: {table_code}")

    # Replace schema layer (first 2 digits) with "03" (functions)
    return f"03{table_code[2:]}"  # Returns 6 digits
```

**New**:
```python
def derive_function_code(self, table_code: str, function_seq: int = 1) -> str:
    """
    Derive function code from table code by changing schema layer to 03

    Args:
        table_code: Base table code (6 or 7 digits, e.g., "012361" or "0123611")
        function_seq: Function sequence within entity (1-9, default: 1)

    Returns:
        7-digit function code (e.g., "0323611", "0323612")

    Examples:
        derive_function_code("012361", 1)  # First function → "0323611"
        derive_function_code("012361", 2)  # Second function → "0323612"
        derive_function_code("0123611", 3) # Third function → "0323613"
    """
    # Handle both 6-digit (legacy) and 7-digit input
    if len(table_code) == 6:
        base_code = table_code  # Use as-is
    elif len(table_code) == 7:
        base_code = table_code[:6]  # Strip file sequence
    else:
        raise ValueError(f"Invalid table code format: {table_code}")

    # Validate function sequence
    if function_seq < 0 or function_seq > 9:
        raise ValueError(f"Function sequence must be 0-9, got: {function_seq}")

    # Build 7-digit function code: 03 + domain/subdomain/entity + function_seq
    return f"03{base_code[2:]}{function_seq}"
```

#### 1.2 Add Table File Code Generation

```python
def derive_table_file_code(self, table_code: str, file_seq: int = 1) -> str:
    """
    Generate 7-digit code for additional table files (audit, info, node, etc.)

    Args:
        table_code: Base table code (6 or 7 digits)
        file_seq: File sequence within entity (1-9, default: 1)

    Returns:
        7-digit table file code

    Examples:
        derive_table_file_code("012361", 1)  # Main table → "0123611"
        derive_table_file_code("012361", 2)  # Audit table → "0123612"
        derive_table_file_code("012361", 3)  # Info table → "0123613"
    """
    # Handle both 6-digit (legacy) and 7-digit input
    if len(table_code) == 6:
        base_code = table_code
    elif len(table_code) == 7:
        base_code = table_code[:6]
    else:
        raise ValueError(f"Invalid table code format: {table_code}")

    # Validate file sequence
    if file_seq < 0 or file_seq > 9:
        raise ValueError(f"File sequence must be 0-9, got: {file_seq}")

    # Build 7-digit code: base_code + file_seq
    return f"{base_code}{file_seq}"
```

### Phase 2: Update Path Generators

#### 2.1 Update `WriteSidePathGenerator`

**File**: `src/generators/schema/write_side_path_generator.py:63`

**Current**:
```python
if len(file_spec.code) != 6:
    raise ValueError(f"Write-side code must be 6 digits, got: {file_spec.code}")
```

**New**:
```python
# Accept both 6-digit (legacy) and 7-digit (new standard)
if len(file_spec.code) not in [6, 7]:
    raise ValueError(f"Write-side code must be 6 or 7 digits, got: {file_spec.code}")

# Parse code (handle both formats)
if len(file_spec.code) == 6:
    # Legacy format: SSDSSE
    base_code = file_spec.code
    file_seq = "1"  # Default file sequence
else:
    # New format: SSDSSEX
    base_code = file_spec.code[:6]
    file_seq = file_spec.code[6]
```

#### 2.2 Update `hierarchical_file_writer.py`

**File**: `src/generators/schema/hierarchical_file_writer.py:166-170`

**Current**:
```python
# Validate code format based on layer
if file_spec.layer == "write_side" and len(file_spec.code) != 6:
    raise ValueError(f"Write-side code must be 6 digits, got {len(file_spec.code)}: {file_spec.code}")

if file_spec.layer == "read_side" and len(file_spec.code) != 7:
    raise ValueError(f"Read-side code must be 7 digits, got {len(file_spec.code)}: {file_spec.code}")
```

**New**:
```python
# Validate code format based on layer
if file_spec.layer == "write_side" and len(file_spec.code) not in [6, 7]:
    raise ValueError(
        f"Write-side code must be 6 or 7 digits, got {len(file_spec.code)}: {file_spec.code}"
    )

if file_spec.layer == "read_side" and len(file_spec.code) != 7:
    raise ValueError(
        f"Read-side code must be 7 digits, got {len(file_spec.code)}: {file_spec.code}"
    )
```

### Phase 3: Create Function Path Generator

**New File**: `src/generators/actions/function_path_generator.py`

```python
"""
Function path generation for write-side functions

Generates hierarchical file paths for function files based on 7-digit codes.
Functions use layer 03 and follow the same hierarchy as tables.
"""

from pathlib import Path
from src.generators.schema.hierarchical_file_writer import FileSpec, PathGenerator
from src.generators.schema.naming_conventions import NamingConventions


class FunctionPathGenerator(PathGenerator):
    """
    Generates hierarchical paths for function files (layer 03)

    Path structure:
    0_schema/03_functions/0{D}{D}_{domain}/0{D}{D}{S}_{subdomain}/{D}{D}{S}{E}_{entity}/{code}_{fn_name}.sql

    Where:
    - D: domain code (1 digit)
    - S: subdomain second digit (from 2-digit subdomain code)
    - E: entity sequence (1 digit)

    Example:
        generate_path(FileSpec(code="0323611", name="fn_contact_create", layer="functions"))
        → 0_schema/03_functions/032_crm/0323_customer/03236_contact/0323611_fn_contact_create.sql
    """

    # Schema layer constants
    SCHEMA_LAYER_FUNCTIONS = "03"
    SCHEMA_LAYER_PREFIX = "0_schema"
    FUNCTIONS_DIR = "03_functions"

    def __init__(self, base_dir: str = "generated"):
        """Initialize with base directory"""
        self.base_dir = Path(base_dir)
        self.naming = NamingConventions()

    def generate_path(self, file_spec: FileSpec) -> Path:
        """
        Generate hierarchical path from file specification

        Args:
            file_spec: File specification with function code (7 digits)

        Returns:
            Path object for the file location

        Raises:
            ValueError: If code format is invalid or not layer 03
        """
        if len(file_spec.code) != 7:
            raise ValueError(f"Function code must be 7 digits, got: {file_spec.code}")

        # Parse function code (same structure as table code but layer 03)
        schema_layer = file_spec.code[:2]
        domain_code = file_spec.code[2]
        subdomain_code = file_spec.code[3:5]
        entity_sequence = file_spec.code[5]
        function_sequence = file_spec.code[6]

        # Validate schema layer
        if schema_layer != "03":
            raise ValueError(
                f"Invalid schema layer '{schema_layer}' for function code (expected '03')"
            )

        # Get domain and subdomain info from registry
        domain_info = self.naming.registry.get_domain(domain_code)
        if not domain_info:
            raise ValueError(f"Unknown domain code: {domain_code}")

        subdomain_info = self.naming.registry.get_subdomain(domain_code, subdomain_code)
        if not subdomain_info:
            raise ValueError(f"Unknown subdomain code: {subdomain_code} in domain {domain_code}")

        # Build path components
        domain_name = domain_info.domain_name
        subdomain_name = subdomain_info.subdomain_name

        # Domain directory: 03{domain_code}_{domain_name}
        domain_dir = f"{schema_layer}{domain_code}_{domain_name}"

        # Subdomain directory: 03{domain_code}{subdomain_code[1]}_{subdomain_name}
        subdomain_dir = f"{schema_layer}{domain_code}{subdomain_code[1]}_{subdomain_name}"

        # Entity directory: infer from file_spec.name
        # file_spec.name format: "fn_contact_create_contact" or "fn_contact_create"
        if file_spec.name.startswith("fn_"):
            name_parts = file_spec.name[3:].split("_")
            entity_name = name_parts[0]  # First part is entity name
        else:
            raise ValueError(f"Function file name should start with 'fn_', got: {file_spec.name}")

        from src.generators.naming_utils import camel_to_snake
        entity_snake = camel_to_snake(entity_name)

        entity_dir_code = f"{schema_layer}{domain_code}{subdomain_code[1]}{entity_sequence}"
        entity_dir = f"{entity_dir_code}_{entity_snake}"

        # File name: {code}_{fn_name}.sql
        filename = f"{file_spec.code}_{file_spec.name}.sql"

        # Combine path
        return (
            self.base_dir
            / self.SCHEMA_LAYER_PREFIX
            / self.FUNCTIONS_DIR
            / domain_dir
            / subdomain_dir
            / entity_dir
            / filename
        )
```

### Phase 4: Update Registry

#### 4.1 Add Function Sequence Tracking

**File**: `src/generators/schema/naming_conventions.py`

Update `SubdomainInfo` dataclass:
```python
@dataclass
class SubdomainInfo:
    """Subdomain information from registry"""

    subdomain_code: str
    subdomain_name: str
    description: str
    next_entity_sequence: int
    entities: dict[str, dict]
    next_read_entity: int = 1  # Independent read-side sequence
    read_entities: dict[str, dict] = field(default_factory=dict)
    next_function_sequence: dict[str, int] = field(default_factory=dict)  # ⭐ NEW: Per-entity function counter
    next_table_file_sequence: dict[str, int] = field(default_factory=dict)  # ⭐ NEW: Per-entity table file counter
```

#### 4.2 Add Sequence Assignment Methods

```python
def assign_function_code(
    self,
    domain_name: str,
    subdomain_name: str,
    entity_name: str,
    action_name: str
) -> str:
    """
    Assign function code for an action

    Args:
        domain_name: Domain name
        subdomain_name: Subdomain name
        entity_name: Entity name
        action_name: Action name (e.g., "create_contact")

    Returns:
        7-digit function code (e.g., "0323611")
    """
    # Get entity info
    entity_entry = self.get_entity(entity_name)
    if not entity_entry:
        raise ValueError(f"Entity {entity_name} not registered")

    # Get base table code (6 digits)
    base_code = entity_entry.table_code

    # Get or initialize function sequence for this entity
    subdomain_info = self.get_subdomain(entity_entry.domain, subdomain_name)
    entity_key = entity_name.lower()

    if entity_key not in subdomain_info.next_function_sequence:
        subdomain_info.next_function_sequence[entity_key] = 1

    function_seq = subdomain_info.next_function_sequence[entity_key]

    # Build 7-digit function code
    function_code = self.naming.derive_function_code(base_code, function_seq)

    # Increment sequence
    subdomain_info.next_function_sequence[entity_key] += 1

    # Save registry
    self.save()

    return function_code
```

---

## 🧪 Testing Strategy

### Phase 1: Unit Tests

#### Test 1: Function Code Generation
```python
def test_derive_function_code_with_sequence():
    """Should generate 7-digit function codes with sequence"""
    nc = NamingConventions()

    # First function
    func1 = nc.derive_function_code("012361", function_seq=1)
    assert func1 == "0323611"

    # Second function
    func2 = nc.derive_function_code("012361", function_seq=2)
    assert func2 == "0323612"

    # Third function
    func3 = nc.derive_function_code("012361", function_seq=3)
    assert func3 == "0323613"
```

#### Test 2: Table File Code Generation
```python
def test_derive_table_file_code():
    """Should generate 7-digit codes for auxiliary tables"""
    nc = NamingConventions()

    # Main table
    main = nc.derive_table_file_code("012361", file_seq=1)
    assert main == "0123611"

    # Audit table
    audit = nc.derive_table_file_code("012361", file_seq=2)
    assert audit == "0123612"

    # Info table
    info = nc.derive_table_file_code("012361", file_seq=3)
    assert info == "0123613"
```

#### Test 3: Function Path Generation
```python
def test_function_path_generation():
    """Should generate correct hierarchical paths for functions"""
    generator = FunctionPathGenerator(base_dir="generated")

    file_spec = FileSpec(
        code="0323611",
        name="fn_contact_create_contact",
        content="CREATE OR REPLACE FUNCTION ...",
        layer="functions"
    )

    path = generator.generate_path(file_spec)

    expected = Path(
        "generated/0_schema/03_functions/032_crm/0323_customer/"
        "03236_contact/0323611_fn_contact_create_contact.sql"
    )
    assert path == expected
```

### Phase 2: Integration Tests

#### Test 4: Multiple Functions per Entity
```python
def test_multiple_functions_per_entity():
    """Should generate unique codes for multiple actions"""
    orchestrator = SchemaOrchestrator()

    entity = Entity(
        name="Contact",
        schema="crm",
        actions=[
            ActionDefinition(name="create_contact"),
            ActionDefinition(name="update_contact"),
            ActionDefinition(name="delete_contact"),
        ]
    )

    files = orchestrator.generate_function_files(entity)

    # Each action should get unique code
    codes = [f.code for f in files]
    assert len(codes) == 3
    assert len(set(codes)) == 3  # All unique
    assert all(len(c) == 7 for c in codes)  # All 7 digits
```

#### Test 5: Auxiliary Tables
```python
def test_auxiliary_table_generation():
    """Should generate unique codes for main + audit tables"""
    orchestrator = SchemaOrchestrator()

    entity = Entity(name="Contact", schema="crm", with_audit=True)

    files = orchestrator.generate_table_files(entity)

    # Should have main table + audit table
    assert len(files) == 2
    assert files[0].name == "tb_contact"
    assert files[1].name == "tb_contact_audit"

    # Both should have 7-digit codes
    assert len(files[0].code) == 7
    assert len(files[1].code) == 7

    # Codes should differ only in last digit
    assert files[0].code[:6] == files[1].code[:6]
    assert files[0].code != files[1].code
```

---

## 📝 Migration Strategy

### Option 1: Big Bang Migration (Recommended)

**Pros**: Clean break, no legacy code paths
**Cons**: Requires updating all tests and docs simultaneously

**Steps**:
1. Update all numbering functions to use 7 digits
2. Update all path generators to accept 7 digits
3. Update all tests to expect 7 digits
4. Update documentation

### Option 2: Gradual Migration

**Pros**: Lower risk, incremental rollout
**Cons**: Complex dual-mode code paths

**Steps**:
1. Add 7-digit support alongside 6-digit
2. Add deprecation warnings for 6-digit usage
3. Migrate existing entities incrementally
4. Remove 6-digit support after migration complete

**Recommendation**: **Option 1 (Big Bang)** - The codebase is still small enough and this is a foundational change.

---

## 📋 Implementation Checklist

### Phase 1: Core Numbering (Day 1-2)
- [ ] Update `derive_function_code()` to use 7 digits with sequence parameter
- [ ] Add `derive_table_file_code()` for auxiliary tables
- [ ] Add `assign_function_code()` to registry
- [ ] Add `next_function_sequence` tracking to `SubdomainInfo`
- [ ] Add `next_table_file_sequence` tracking to `SubdomainInfo`
- [ ] Write unit tests for new methods

### Phase 2: Path Generators (Day 2-3)
- [ ] Update `WriteSidePathGenerator` to accept 6 or 7 digits
- [ ] Update `hierarchical_file_writer.py` validation
- [ ] Create `FunctionPathGenerator` class
- [ ] Write unit tests for path generators
- [ ] Integration tests for file writing

### Phase 3: Orchestrators & Generation (Day 3-4)
- [ ] Update `SchemaOrchestrator` to use 7-digit codes
- [ ] Update `ActionOrchestrator` to use 7-digit codes
- [ ] Update `AuditGenerator` to use 7-digit codes
- [ ] Update node+info split pattern to use 7-digit codes
- [ ] Integration tests for full generation flow

### Phase 4: Testing & Documentation (Day 4-5)
- [ ] Update all existing tests to expect 7 digits
- [ ] Add comprehensive test coverage for new functionality
- [ ] Update architecture documentation
- [ ] Update CLAUDE.md with new numbering scheme
- [ ] Update domain registry examples
- [ ] Add migration guide for existing projects

---

## 🎯 Success Criteria

1. ✅ **All layers use 7-digit codes** (01, 02, 03)
2. ✅ **Multiple functions per entity** supported
3. ✅ **Multiple tables per entity** supported (audit, info, node)
4. ✅ **All tests pass** with new numbering
5. ✅ **Documentation updated** with new format
6. ✅ **No breaking changes** to existing YAML syntax
7. ✅ **Registry properly tracks** all sequence counters

---

## 🔮 Future Enhancements

### Beyond 7 Digits: Hexadecimal Support

If 10 functions per entity (0-9) becomes limiting, consider:

**8-digit hex codes**: `SSDSSEXX`
- Last 2 digits in hex: 00-FF = 256 functions/tables per entity
- Example: `03236101`, `03236102`, ..., `032361FF`

**Benefits**:
- 256 functions per entity (vs 10 with decimal)
- Still human-readable with proper tooling
- Future-proof for large-scale codebases

**Implementation**: Simple extension of current approach:
```python
function_code = f"03{base_code[2:]}{function_seq:02x}"  # Hex formatting
```

---

## 📚 References

- Current implementation: `src/generators/schema/naming_conventions.py:1001-1038`
- Path generators: `src/generators/schema/*_path_generator.py`
- File writer: `src/generators/schema/hierarchical_file_writer.py`
- Tests: `tests/unit/registry/test_naming_conventions.py:472-499`

---

**Last Updated**: 2025-11-12
**Next Review**: After Phase 1 completion
