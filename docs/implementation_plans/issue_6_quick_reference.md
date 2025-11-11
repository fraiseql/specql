# Issue #6 Quick Reference Card

## The Bug

```python
# WRONG (old code)
subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
# "013111" → subdomain_code = "11" ❌

# CORRECT (fixed code)
subdomain_code = components.subdomain_code
# "013111" → subdomain_code = "1" ✅
```

---

## Table Code Format

```
Table Code: 013111

Position: 0 1 2 3 4 5
Value:    0 1 3 1 1 1
          └─┘ │ │ │ └─ file_sequence (1)
Schema      │ │ └─── entity_sequence (1)
layer       │ └───── subdomain_code (1) ← SINGLE DIGIT
            └─────── domain_code (3)

Breakdown:
  01 = write_side (schema layer)
  3  = catalog (domain)
  1  = classification (subdomain) ← THE FIX
  1  = first entity
  1  = first file
```

---

## Directory Structure

### Before Fix ❌
```
01_write_side/
  013_catalog/
    01311_subdomain_11/     ← 5 digits, generic name
    01312_subdomain_12/     ← Different directory!
    01313_subdomain_13/     ← Different directory!
```

### After Fix ✅
```
01_write_side/
  013_catalog/
    0131_classification/    ← 4 digits, registry name
      01311_color_mode/     ← Snake_case, no _group
      01312_duplex_mode/    ← Snake_case, no _group
      01313_machine_function/ ← Snake_case, no _group
```

---

## Files to Change

### 1. Parser (`src/numbering/numbering_parser.py`)

```python
@dataclass
class TableCodeComponents:
    schema_layer: str      # 2 digits
    domain_code: str       # 1 digit
    subdomain_code: str    # 1 digit ← NEW
    entity_sequence: str   # 1 digit ← RENAMED
    file_sequence: str     # 1 digit

def parse_table_code_detailed(self, table_code: str):
    return TableCodeComponents(
        schema_layer=table_code[0:2],
        domain_code=table_code[2],
        subdomain_code=table_code[3],    # ← FIX
        entity_sequence=table_code[4],   # ← FIX
        file_sequence=table_code[5],
    )
```

### 2. Path Generator (`src/generators/schema/naming_conventions.py`)

```python
def generate_file_path(self, entity, table_code, ...):
    components = self.parser.parse_table_code_detailed(table_code)

    # OLD (WRONG):
    # subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]

    # NEW (CORRECT):
    subdomain_code = components.subdomain_code

    # Look up name from registry
    subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code, {})
    subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")

    # Build 4-digit subdomain directory
    subdomain_dir = f"{components.schema_layer}{components.domain_code}{subdomain_code}_{subdomain_name}"
    # Result: "0131_classification"
```

### 3. Registration (`src/generators/schema/naming_conventions.py`)

```python
def register_entity_auto(self, entity, table_code):
    components = self.parser.parse_table_code_detailed(table_code)

    # OLD (WRONG):
    # subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]

    # NEW (CORRECT):
    subdomain_code = components.subdomain_code

    # Registry uses 2-digit codes with leading zero
    subdomain_code_padded = subdomain_code.zfill(2)  # "1" → "01"

    self.registry.register_entity(
        entity_name=entity.name,
        table_code=table_code,
        entity_code=entity_sequence,
        domain_code=components.domain_code,
        subdomain_code=subdomain_code_padded,  # "01"
    )
```

---

## Test Examples

### Unit Test (Parser)
```python
def test_parse_subdomain_single_digit():
    parser = NumberingParser()
    components = parser.parse_table_code_detailed("013111")

    assert components.subdomain_code == "1"  # Single digit
    assert components.entity_sequence == "1"  # Renamed
```

### Unit Test (Path Generation)
```python
def test_generate_path_subdomain_classification():
    conventions = NamingConventions()
    entity = Entity(name="ColorMode", schema="catalog")

    path = conventions.generate_file_path(entity, "013111", "table")

    assert "0131_classification" in path  # 4 digits + name
    assert "subdomain_11" not in path     # No generic name
```

### Integration Test (Same Subdomain)
```python
def test_same_subdomain_shared_directory():
    # ColorMode (013111), DuplexMode (013121), MachineFunction (013131)
    # All subdomain code "1" (classification)

    result = orchestrator.generate_from_files([...])

    # All should be in: 0131_classification/
    classification_dir = output_dir / "01_write_side" / "013_catalog" / "0131_classification"
    assert classification_dir.exists()

    entity_groups = list(classification_dir.glob("*_group"))
    assert len(entity_groups) == 3  # All together
```

---

## Registry Structure

```yaml
domains:
  '3':
    name: catalog
    subdomains:
      '01':  # ← 2 digits in registry (with leading zero)
        name: classification  # ← Look up this name
      '02':
        name: manufacturer
```

**Mapping**:
- Table code subdomain: `1` (single digit)
- Registry subdomain: `01` (zero-padded)
- Directory name: `0131_classification` (schema+domain+subdomain+name)

---

## TDD Workflow

```bash
# Phase 1: Parser
pytest tests/unit/numbering/test_numbering_parser.py -v

# Phase 2: Path Generation
pytest tests/unit/registry/test_naming_conventions.py -v

# Phase 3: Registration
pytest tests/unit/registry/test_naming_conventions.py::test_register_entity_auto -v

# Phase 4: Integration
pytest tests/integration/test_issue_6_subdomain_parsing.py -v

# Full Suite
pytest --tb=short
```

---

## Common Pitfalls

### ❌ Don't Do This
```python
# Taking 2 characters
subdomain = table_code[3:5]  # "013111"[3:5] = "11" ❌
```

### ✅ Do This
```python
# Taking 1 character
subdomain = table_code[3]  # "013111"[3] = "1" ✅

# Or use parser
components = parser.parse_table_code_detailed(table_code)
subdomain = components.subdomain_code  # "1" ✅
```

### ❌ Don't Forget
- Registry uses 2-digit codes (`"01"`, `"02"`)
- Table codes use 1-digit (`"1"`, `"2"`)
- Need to pad when registering: `subdomain.zfill(2)`

---

## Validation Checklist

- [ ] Parser extracts single digit for subdomain
- [ ] Path generation uses 4-digit subdomain directory
- [ ] Subdomain name looked up from registry
- [ ] Same-subdomain entities share directory
- [ ] No generic `subdomain_XX` names
- [ ] Registry registration uses correct subdomain
- [ ] Backward compatibility maintained
- [ ] All tests pass

---

## Expected Changes

| Metric | Before | After |
|--------|--------|-------|
| Subdomain digits | 2 | 1 |
| Directory code length | 5 digits | 4 digits |
| Directory naming | Generic `subdomain_XX` | Registry name |
| Entities per directory | 1 | Multiple (shared) |
| SQL changes | N/A | None |

---

**Files Changed**: 3 core files + 3 test files + 2 doc files
**Lines Changed**: ~80 lines total
**Risk Level**: LOW (no SQL changes)
**Test Coverage**: Unit + Integration
**Estimated Time**: 9-15 hours

---

*See full plan: [`issue_6_subdomain_parsing_fix.md`](./issue_6_subdomain_parsing_fix.md)*
