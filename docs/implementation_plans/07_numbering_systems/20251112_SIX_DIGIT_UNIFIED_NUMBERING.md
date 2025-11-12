# Implementation Plan: 6-Digit Unified Numbering System (SDSEX)

**Date**: 2025-11-12
**Status**: Planning
**Priority**: High

---

## Executive Summary

Convert from the current 7-digit system (SSDSSEX) with 2-digit subdomains to a unified 6-digit system (SDSEX) with 1-digit subdomains, matching the proven printoptim_migration structure.

**Current**: `0120391` (7 digits) - SS(01) + D(2) + SS(03) + E(9) + X(1)
**Target**: `012321` (6 digits) - SS(01) + D(2) + S(3) + E(2) + X(1)

---

## Current State Analysis

### Current Implementation (7-digit SSDSSEX)

**Format**: Schema(2) + Domain(1) + Subdomain(2) + Entity(1) + FileSeq(1) = 7 digits

**Structure**:
```
01_write_side/
  012_crm/                    (3 digits)
    01203_customer/           (5 digits) ← skips 4-digit level!
      012039_testcontact/     (6 digits)
        0120391_tb_contact.sql (7 digits)
```

**Problems**:
1. Subdomain uses 2 digits (00-99), but only ~10 subdomains needed per domain
2. Skips the 4-digit directory level (jumps from 3 to 5 digits)
3. Inconsistent with printoptim_migration (6-digit system)
4. UUID encoding relies on 6-digit codes (user requirement)

---

## Target State (6-digit SDSEX)

### Format Specification

**SDSEX**: Schema(2) + Domain(1) + Subdomain(1) + Entity(1) + FileSeq(1) = 6 digits

**Digit Allocation**:
- **SS** (2 digits): Schema layer - 01=write_side, 02=query_side, 03=functions
- **D** (1 digit): Domain - 0-9 (max 10 domains)
- **S** (1 digit): Subdomain - 0-9 (max 10 subdomains per domain)
- **E** (1 digit): Entity - 0-9 (max 10 entities per subdomain)
- **X** (1 digit): File sequence - 0-9 (max 10 files per entity)

### Progressive Directory Structure

Each level adds exactly **one digit**:

```
0_schema/                     (base)
  01_write_side/              (2 digits: SS)
    012_crm/                  (3 digits: SS+D)
      0123_contact/           (4 digits: SS+D+S)
        01232_contact/        (5 digits: SS+D+S+E)
          012321_tb_contact.sql (6 digits: SS+D+S+E+X)
```

### Unified Across All Layers

**Write Side** (tables):
```
01_write_side/012_crm/0123_contact/01232_contact/012321_tb_contact.sql
```

**Query Side** (views):
```
02_query_side/022_crm/0223_contact/02232_contact/022321_v_contact.sql
```

**Functions** (mutations):
```
03_functions/032_crm/0323_contact/03232_contact/032321_fn_update_contact.sql
```

**Key Point**: All three layers have identical 6-level directory structure with entity directories.

---

## Impact Analysis

### 1. Core Parser (`src/numbering/numbering_parser.py`)

**Current State**:
- Accepts 6 or 7 digit codes
- Parses subdomain as 2 digits: `code[3:5]`
- Returns `subdomain_code` as 2-character string

**Required Changes**:
- Update parsing to use 1-digit subdomain: `code[3]`
- Update `TableCodeComponents.subdomain_code` documentation
- Remove 7-digit support (keep only 6-digit)
- Update validation regex from `[0-9]{6,7}` to `[0-9]{6}`

**Files**:
- `parse_table_code_detailed()` method
- `TableCodeComponents` dataclass comments

---

### 2. Naming Conventions (`src/generators/schema/naming_conventions.py`)

**Current State**:
- `derive_table_code()` builds 7-digit codes with 2-digit subdomain
- Registry stores subdomain codes as 2-digit strings ("01", "03", etc.)
- `validate_table_code()` accepts 7-digit decimal codes

**Required Changes**:

#### A. Code Generation
```python
# Current (line 892):
table_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence % 10}1"
# subdomain_code is 2 digits, e.g., "03"

# Target:
table_code = f"{schema_layer}{domain_code}{subdomain_code[0]}{entity_sequence % 10}1"
# Use only first digit of subdomain_code
```

#### B. Validation
```python
# Update validate_table_code() to accept only 6 digits
if not re.match(r"^[0-9]{6}$", table_code):
    raise ValueError("Must be exactly 6 decimal digits")
```

#### C. View Code Generation
```python
# Current derive_view_code() (line 1137):
return f"02{table_code[2:6]}0"  # Produces 7 digits

# Target:
return f"02{table_code[2:5]}0"  # Produces 6 digits (022320)
```

---

### 3. Domain Registry (`registry/domain_registry.yaml`)

**Current State**:
```yaml
domains:
  '2':
    name: crm
    subdomains:
      '01':  # 2-digit code
        name: core
      '03':  # 2-digit code
        name: customer
```

**Required Changes**:
- Convert all subdomain codes from 2 digits to 1 digit
- Update registry schema version
- Migrate existing entities to new codes

**Migration Strategy**:
```yaml
# Before: subdomain '01' → After: subdomain '1'
# Before: subdomain '03' → After: subdomain '3'
# Before: subdomain '09' → After: subdomain '9'

# Rule: Drop leading zero, use last digit
'01' → '1'
'03' → '3'
'09' → '9'
```

**Example**:
```yaml
domains:
  '2':
    name: crm
    subdomains:
      '1':  # 1-digit code (was '01')
        name: core
      '3':  # 1-digit code (was '03')
        name: customer
```

---

### 4. Path Generators

#### A. Write Side Path Generator (`src/generators/schema/write_side_path_generator.py`)

**Current State** (line 68-74):
```python
# Parses 7-digit code
base_code = file_spec.code[:6]
file_seq = file_spec.code[6]

# Gets subdomain using 2 digits
subdomain_info = self.naming.registry.get_subdomain(domain_code, subdomain_code.zfill(2))
```

**Required Changes**:
```python
# Parse 6-digit code
if len(file_spec.code) != 6:
    raise ValueError(f"Write-side code must be 6 digits, got: {file_spec.code}")

# Parse components (subdomain is 1 digit)
components = parser.parse_table_code_detailed(file_spec.code)

# Subdomain directory (4 digits)
subdomain_dir_code = f"{schema_layer}{domain_code}{subdomain_code}"  # e.g., "0123"
subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"  # e.g., "0123_contact"

# Entity directory (5 digits)
entity_dir_code = f"{subdomain_dir_code}{entity_sequence}"  # e.g., "01232"
entity_dir = f"{entity_dir_code}_{entity_snake}"  # e.g., "01232_contact"
```

#### B. Read Side Path Generator (`src/generators/schema/read_side_path_generator.py`)

**Current State**:
- Expects 7-digit view codes
- Builds 5-digit subdomain directories (skips entity level)

**Required Changes**:
```python
# Parse 6-digit view code
if len(file_spec.code) != 6:
    raise ValueError(f"Read-side code must be 6 digits, got: {file_spec.code}")

# Must include entity directory (matching write side structure)
# View code: 022321 (02=query, 2=crm, 3=contact, 2=entity, 1=file)

# Build paths:
# Layer 3: 022_crm/
# Layer 4: 0223_contact/          (4 digits - subdomain)
# Layer 5: 02232_contact/         (5 digits - entity)
# Layer 6: 022321_v_contact.sql   (6 digits - file)
```

#### C. Function Path Generator (`src/generators/actions/function_path_generator.py`)

**Current State**:
- May not exist or may use different structure

**Required Changes**:
```python
# Implement identical structure to write/read sides
# Function code: 032321 (03=functions, 2=crm, 3=contact, 2=entity, 1=file)

# Build paths:
# Layer 3: 032_crm/
# Layer 4: 0323_contact/          (4 digits - subdomain)
# Layer 5: 03232_contact/         (5 digits - entity)
# Layer 6: 032321_fn_update.sql   (6 digits - file)
```

---

### 5. CLI Orchestrator (`src/cli/orchestrator.py`)

**Current State** (line 630-684):
```python
# Gets 7-digit table code
table_code = self.get_table_code(entity)  # Returns "0120391"

# Extracts base code (6 digits)
base_code = table_code[:6]  # "012039"

# Generates file codes with sequences
table_spec = FileSpec(code=f"{base_code}1", ...)     # "0120391"
helpers_spec = FileSpec(code=f"{base_code}2", ...)   # "0120392"
func_spec = FileSpec(code=f"{base_code}3", ...)      # "0120393"
```

**Required Changes**:
```python
# Gets 6-digit table code
table_code = self.get_table_code(entity)  # Returns "012321"

# Extract base code (5 digits - without file sequence)
base_code = table_code[:5]  # "01232"

# Generate file codes with sequences
table_spec = FileSpec(code=f"{base_code}1", ...)     # "012321"
helpers_spec = FileSpec(code=f"{base_code}2", ...)   # "012322"
func_spec = FileSpec(code=f"{base_code}3", ...)      # "012323"
```

---

### 6. Test Files

#### A. `tests/integration/test_hierarchical_generation.py`

**Current Test Codes** (7-digit):
```yaml
table_code: "0120391"  # SS(01) + D(2) + SS(03) + E(9) + X(1)
table_code: "0120191"  # SS(01) + D(2) + SS(01) + E(9) + X(1)
```

**Target Test Codes** (6-digit):
```yaml
table_code: "012321"  # SS(01) + D(2) + S(3) + E(2) + X(1)
table_code: "012121"  # SS(01) + D(2) + S(1) + E(2) + X(1)
```

**Path Expectations**:
```python
# Current:
crm_write / "01203_customer" / "012039_testcontact" / "0120391_tb_testcontact.sql"

# Target:
crm_write / "0123_customer" / "01232_testcontact" / "012321_tb_testcontact.sql"
```

#### B. `tests/integration/test_table_code_integration.py`

**Update All Manual Codes**:
```python
# Current: "0140211" (7 digits)
# Target: "014021" (6 digits)

# Current: "0120311" (7 digits)
# Target: "012031" (6 digits)
```

#### C. `tests/unit/registry/test_naming_conventions.py`

**Update Test Cases**:
- All code validation tests
- Path generation tests
- Registry lookup tests

---

## Implementation Phases

### Phase 1: Update Core Parser & Data Structures ✅
**Goal**: Update the foundational parsing logic

**Tasks**:
1. Update `TableCodeComponents` dataclass
   - Change `subdomain_code` from 2 digits to 1 digit
   - Update documentation comments

2. Update `NumberingParser.parse_table_code_detailed()`
   - Remove 7-digit support
   - Parse subdomain as single digit: `code[3]`
   - Update validation to require exactly 6 digits

3. Update property methods
   - `full_group`: Should be `SS + D + S` (4 digits)
   - `full_entity`: Should be `SS + D + S + E` (5 digits)

**Files**:
- `src/numbering/numbering_parser.py`

**Validation**:
```python
# Test cases
assert parse("012321").subdomain_code == "3"  # Not "03"
assert parse("012321").full_group == "0123"   # Not "01203"
assert parse("012321").full_entity == "01232" # Not "012039"
```

---

### Phase 2: Update Domain Registry ✅
**Goal**: Migrate subdomain codes from 2-digit to 1-digit

**Tasks**:
1. Update `registry/domain_registry.yaml`
   - Convert all subdomain keys from 2-digit to 1-digit
   - Update schema version to indicate breaking change

2. Update `src/registry/domain_registry.py`
   - Handle 1-digit subdomain lookups
   - Update `get_subdomain()` method signature if needed

3. Create migration script (optional)
   - Script to auto-convert existing registry files
   - Preserve entity assignments

**Migration Example**:
```yaml
# Before
domains:
  '2':
    subdomains:
      '01':
        name: core
      '03':
        name: customer

# After
domains:
  '2':
    subdomains:
      '1':
        name: core
      '3':
        name: customer
```

**Files**:
- `registry/domain_registry.yaml`
- `src/registry/domain_registry.py`

---

### Phase 3: Update Naming Conventions ✅
**Goal**: Generate 6-digit codes with 1-digit subdomains

**Tasks**:
1. Update `derive_table_code()`
   - Use only first digit of subdomain code
   - Generate 6-digit codes instead of 7-digit

2. Update `validate_table_code()`
   - Accept only 6-digit codes
   - Update error messages

3. Update `derive_view_code()`
   - Generate 6-digit view codes
   - Use 1-digit subdomain

4. Update `derive_function_code()` (if exists)
   - Generate 6-digit function codes
   - Use 1-digit subdomain

**Code Changes**:
```python
# derive_table_code() line 892
# Before:
table_code = f"{schema_layer}{domain_code}{subdomain_code}{entity_sequence % 10}1"

# After:
subdomain_digit = subdomain_code[0] if len(subdomain_code) == 2 else subdomain_code
table_code = f"{schema_layer}{domain_code}{subdomain_digit}{entity_sequence % 10}1"

# derive_view_code() line 1137
# Before:
return f"02{table_code[2:6]}0"  # 7 digits

# After:
return f"02{table_code[2:5]}0"  # 6 digits
```

**Files**:
- `src/generators/schema/naming_conventions.py`

---

### Phase 4: Update Path Generators ✅
**Goal**: Generate correct hierarchical paths with 4-digit subdomain dirs

**Tasks**:

#### 4A: Write Side Path Generator
```python
# src/generators/schema/write_side_path_generator.py

# Update to expect 6-digit codes
if len(file_spec.code) != 6:
    raise ValueError(f"Write-side code must be 6 digits")

# Parse components (subdomain is now 1 digit)
components = parser.parse_table_code_detailed(file_spec.code)
subdomain_code = components.subdomain_code  # Single digit

# Build 4-digit subdomain directory
subdomain_dir_code = f"{schema_layer}{domain_code}{subdomain_code}"  # "0123"
subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"

# Build 5-digit entity directory
entity_dir_code = f"{subdomain_dir_code}{entity_sequence}"  # "01232"
entity_dir = f"{entity_dir_code}_{entity_snake}"

# File path (6 digits)
filename = f"{file_spec.code}_{file_spec.name}.sql"  # "012321_tb_contact.sql"
```

#### 4B: Read Side Path Generator
```python
# src/generators/schema/read_side_path_generator.py

# Add entity directory support (currently missing!)
# Structure must match write side:
# 022_crm/0223_contact/02232_contact/022321_v_contact.sql

# Parse 6-digit view code
components = parser.parse_table_code_detailed(file_spec.code)

# Build subdomain directory (4 digits)
subdomain_dir_code = f"{schema_layer}{domain_code}{subdomain_code}"

# Build entity directory (5 digits) ← NEW!
entity_dir_code = f"{subdomain_dir_code}{entity_sequence}"
entity_dir = f"{entity_dir_code}_{entity_name}"

# Complete path with entity level
path = base / schema_base / layer_dir / domain_dir / subdomain_dir / entity_dir / filename
```

#### 4C: Function Path Generator
```python
# src/generators/actions/function_path_generator.py

# Implement identical structure to write/read sides
# 032_crm/0323_contact/03232_contact/032321_fn_update.sql

# Same logic as write side, just different schema layer (03)
```

**Files**:
- `src/generators/schema/write_side_path_generator.py`
- `src/generators/schema/read_side_path_generator.py`
- `src/generators/actions/function_path_generator.py`

---

### Phase 5: Update CLI Orchestrator ✅
**Goal**: Generate correct file codes with 2-digit sequences

**Tasks**:
1. Update `generate_hierarchical()` method
   - Extract base code as 5 digits (not 6)
   - Generate file sequences correctly

2. Update FileSpec creation
   - Table: `{base}1`
   - Helpers: `{base}2`
   - Functions: `{base}3`, `{base}4`, etc.
   - Audit: `{base}9`

**Code Changes**:
```python
# line 631-684
table_code = self.get_table_code(entity)  # "012321" (6 digits)

# Extract base (5 digits - no file sequence)
base_code = table_code[:5]  # "01232"

# Generate file codes
table_spec = FileSpec(code=f"{base_code}1", ...)     # "012321"
helpers_spec = FileSpec(code=f"{base_code}2", ...)   # "012322"
func1_spec = FileSpec(code=f"{base_code}3", ...)     # "012323"
func2_spec = FileSpec(code=f"{base_code}4", ...)     # "012324"
audit_spec = FileSpec(code=f"{base_code}9", ...)     # "012329"
```

**Files**:
- `src/cli/orchestrator.py`

---

### Phase 6: Update All Tests ✅
**Goal**: Update test codes and path expectations

**Tasks**:

#### 6A: Update Test Data
```python
# Change all 7-digit codes to 6-digit
# Update subdomain codes from 2-digit to 1-digit

# Before:
table_code: "0120391"  # 7 digits, subdomain "03"

# After:
table_code: "012321"   # 6 digits, subdomain "3"
```

#### 6B: Update Path Assertions
```python
# Before:
assert (output_dir / "01203_customer" / "012039_entity").exists()

# After:
assert (output_dir / "0123_customer" / "01232_entity").exists()
```

#### 6C: Add Entity Directory Tests for Views/Functions
```python
# Verify views have entity directories
view_path = output_dir / "022_crm" / "0223_contact" / "02232_contact" / "022321_v_contact.sql"
assert view_path.exists()

# Verify functions have entity directories
func_path = output_dir / "032_crm" / "0323_contact" / "03232_contact" / "032321_fn_update.sql"
assert func_path.exists()
```

**Files**:
- `tests/integration/test_hierarchical_generation.py`
- `tests/integration/test_table_code_integration.py`
- `tests/unit/registry/test_naming_conventions.py`
- `tests/unit/numbering/test_numbering_parser.py` (if exists)

---

### Phase 7: Update Documentation ✅
**Goal**: Document the new 6-digit system

**Tasks**:
1. Update architecture docs
   - `docs/architecture/NUMBERING_SYSTEM.md` (create if missing)
   - Explain SDSEX format
   - Show directory structure examples

2. Update README.md
   - Update code examples to use 6-digit codes
   - Update directory structure diagrams

3. Update CLAUDE.md
   - Update quick reference with 6-digit examples

4. Add migration guide
   - `docs/migrations/7_TO_6_DIGIT_MIGRATION.md`
   - How to convert existing projects

**Files**:
- `README.md`
- `docs/README.md`
- `.claude/CLAUDE.md`
- `docs/architecture/NUMBERING_SYSTEM.md` (new)
- `docs/migrations/7_TO_6_DIGIT_MIGRATION.md` (new)

---

## Testing Strategy

### Unit Tests
- `test_numbering_parser.py`: Parse 6-digit codes correctly
- `test_naming_conventions.py`: Generate 6-digit codes
- `test_domain_registry.py`: Lookup 1-digit subdomains

### Integration Tests
- `test_hierarchical_generation.py`: Full pipeline with 6-digit codes
- `test_table_code_integration.py`: YAML → Entity → Code flow
- `test_path_generation.py`: Verify correct directory structure

### Validation Checklist
```bash
# 1. All tests pass
uv run pytest

# 2. Can generate write side with 6-digit codes
specql generate entities/contact.yaml --hierarchical

# 3. Directory structure is correct
# Expected: 01_write_side/012_crm/0123_contact/01232_contact/012321_tb_contact.sql
ls -R generated/0_schema/01_write_side/

# 4. Can generate views with entity directories
# Expected: 02_query_side/022_crm/0223_contact/02232_contact/022321_v_contact.sql

# 5. Can generate functions with entity directories
# Expected: 03_functions/032_crm/0323_contact/03232_contact/032321_fn_update.sql

# 6. Registry lookups work with 1-digit subdomains
python -c "from src.registry.domain_registry import DomainRegistry; \
           r = DomainRegistry(); \
           print(r.get_subdomain('2', '3'))"  # Should find 'customer'
```

---

## Rollout Strategy

### Development Environment
1. Implement all phases sequentially
2. Run tests after each phase
3. Fix any breaking changes immediately

### Staging Environment
1. Test with real printoptim data structure
2. Verify compatibility with UUID encoding
3. Performance test with large codebases

### Production Deployment
1. No backward compatibility needed (per user requirement)
2. Deploy as breaking change
3. Update all existing projects to new format
4. Clear migration documentation

---

## Risk Assessment

### High Risk
- **UUID encoding compatibility**: MUST validate that 6-digit codes work with UUID system
- **Registry migration**: Converting subdomain codes could break existing entities

### Medium Risk
- **Path generator logic**: Complex changes to multiple generators
- **Test updates**: Many tests need updating

### Low Risk
- **Parser updates**: Straightforward change from 7 to 6 digits
- **Documentation**: Non-breaking updates

### Mitigation Strategies
1. **UUID Validation**: Test UUID encoding/decoding with 6-digit codes FIRST
2. **Registry Backup**: Backup domain_registry.yaml before migration
3. **Incremental Testing**: Run tests after each phase
4. **Rollback Plan**: Keep 7-digit implementation in git history

---

## Success Criteria

### Must Have
- [ ] All layers use 6-digit SDSEX format
- [ ] Subdomain codes are 1 digit (0-9)
- [ ] Progressive directory structure (each level adds 1 digit)
- [ ] All tests pass
- [ ] UUID encoding works with 6-digit codes

### Nice to Have
- [ ] Migration script for existing projects
- [ ] Performance benchmarks
- [ ] Comprehensive documentation

---

## Timeline Estimate

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| 1 | Update parser | 1-2 hours | None |
| 2 | Update registry | 1-2 hours | Phase 1 |
| 3 | Update naming conventions | 2-3 hours | Phase 1, 2 |
| 4 | Update path generators | 3-4 hours | Phase 1, 2, 3 |
| 5 | Update orchestrator | 1-2 hours | Phase 3, 4 |
| 6 | Update tests | 2-3 hours | All previous |
| 7 | Update docs | 1-2 hours | All previous |
| **Total** | | **11-18 hours** | |

---

## Open Questions

1. **UUID Encoding**: Does the UUID encoding system expect exactly 6 digits, or is it flexible?
2. **Entity Limits**: Is 10 entities per subdomain (1 digit, 0-9) sufficient?
3. **Subdomain Limits**: Is 10 subdomains per domain (1 digit, 0-9) sufficient?
4. **File Sequence Limits**: Is 10 files per entity (1 digit, 0-9) sufficient?

**Recommendation**: If any limits are too low, consider moving to hexadecimal (0-F) for affected digits, which would allow 16 values instead of 10.

---

## Related Documents

- Current implementation: `docs/implementation_plans/20251112_SEVENTH_DIGIT_UNIFIED_NUMBERING.md`
- Reference system: `../printoptim_migration/db/0_schema/`
- Registry schema: `registry/domain_registry.yaml`

---

**Status**: Ready for implementation approval
**Next Step**: Review and approve implementation plan
