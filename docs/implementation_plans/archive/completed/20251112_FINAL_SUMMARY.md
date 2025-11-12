# Hierarchical View Organization - FINAL SUMMARY (With Hex Support)

**Date**: 2025-11-12
**Status**: Ready for Implementation
**Estimated Effort**: 26-35 hours (3-4 days)

---

## Code Format: `0LDSEV` (Hexadecimal)

### Each position is a HEX digit (0-9, A-F):

| Pos | Component | Range | Capacity |
|-----|-----------|-------|----------|
| 1 | Schema | `0` | Always 0 |
| 2 | Layer | `1-3` | Write/Read/Functions |
| 3 | Domain | `0-F` | **16 domains** |
| 4 | Subdomain | `1-F` | **15 subdomains** |
| 5 | Entity | `1-F` | **15 entities** |
| 6 | File | `1-F` | **15 files** |

### Example Breakdown

**Decimal code**: `014112` (current usage)
```
0  1  4  1  1  2
│  │  │  │  │  └─ File 2
│  │  │  │  └──── Entity 1
│  │  │  └─────── Subdomain 1
│  │  └────────── Domain 4 (dimensions)
│  └───────────── Layer 1 (write_side)
└──────────────── Schema 0
```

**Hex code**: `01A3C5` (when you scale beyond 9)
```
0  1  A  3  C  5
│  │  │  │  │  └─ File 5
│  │  │  │  └──── Entity C (hex C = decimal 12)
│  │  │  └─────── Subdomain 3
│  │  └────────── Domain A (hex A = decimal 10)
│  └───────────── Layer 1 (write_side)
└──────────────── Schema 0
```

---

## Capacity (Hexadecimal)

### Per Subdomain
- 15 entities × 15 files = **225 files**

### Per Domain
- 15 subdomains × 225 files = **3,375 files**

### Total System
- 16 domains × 3,375 × 2 layers = **108,000 files possible**

**This eliminates all practical scalability concerns!**

---

## The Gap

### Current Implementation
```
output/
└── 200_table_views.sql    ← All tv_ tables in one file
```

### Target Implementation
```
0_schema/02_query_side/
├── 022_crm/
│   └── 0223_customer/
│       ├── 0223A0_tv_contact.sql      ← Entity A (hex 10)
│       └── 0223B0_tv_company.sql      ← Entity B (hex 11)
│
└── 024_dim/
    └── 0241_geo/
        └── 024130_tv_location.sql     ← Entity 3
```

---

## Key Insight: Independent Read-Side Sequencing

Write-side and read-side entity sequences are **completely independent**:

```
Write-side (Layer 1):
  014111 - Entity 1, File 1 (tb_location_info)
  014112 - Entity 1, File 2 (tb_location)
  014121 - Entity 2, File 1 (tb_building)
  ...
  01419A - Entity 9, File A (when you exceed 9 files)

Read-side (Layer 2) - INDEPENDENT!:
  024110 - Entity 1, File 0 (v_location_summary)
  024120 - Entity 2, File 0 (v_count_allocations)
  024130 - Entity 3, File 0 (tv_location)  ← tv_!
  ...
  0241A0 - Entity A, File 0 (when you have 10+ entities)
```

---

## Implementation Phases

### Phase 1: Registry Enhancement (6-8 hours)
**Goal**: Support independent read-side sequencing with hex

**Changes**:
```yaml
domains:
  '4':  # Hex domain code
    subdomains:
      '1':  # Hex subdomain code
        # Separate tracking per layer
        next_write_entity: '3'   # Hex string
        write_entities: {...}

        next_read_entity: 'A'    # Hex string (decimal 10)
        read_entities: {...}
```

**Key Functions**:
- `assign_read_entity_code()` - Hex-aware sequencing
- `increment_hex_sequence()` - Handle 9→A, F→overflow
- `parse_hex_code()` - Parse 6-char hex codes

---

### Phase 2: Path Generation (4-5 hours)
**Goal**: Generate hierarchical paths from hex codes

**Algorithm**:
```python
def generate_path(code: str) -> Path:
    # Parse: '01A3C5'
    layer = code[1]      # '1'
    domain = code[2]     # 'A' (keep as hex)
    subdomain = code[3]  # '3'
    entity = code[4]     # 'C'
    file_num = code[5]   # '5'

    # Build: 0_schema/01_write_side/01A_analytics/01A3_marketing/01A3C_segment/01A3C5_tb_segment.sql
```

---

### Phase 3: File Splitting (4-6 hours)
**Goal**: One file per tv_ entity

**Current**:
```python
return "\n\n".join(all_tv_sql)  # Monolithic
```

**Target**:
```python
return [
    TableViewFile(code='022370', content='...'),
    TableViewFile(code='022380', content='...'),
]
```

---

### Phase 4: Orchestrator Integration (5-7 hours)
**Goal**: CLI generates hierarchical structure with hex codes

**Flow**:
```python
for entity in entities:
    # Assign hex code
    code = registry.assign_read_entity_code(domain, subdomain, entity.name)
    # Generate path
    path = path_gen.generate_path(code, entity.name)
    # Create file
    result.migrations.append(MigrationFile(code=code, path=path, content=...))
    # Persist
    registry.save()
```

---

### Phase 5: Migration & Validation (4-5 hours)
**Goal**: Migrate existing registry, validate hex codes

**Validation**:
```python
def validate_hex_code(code: str) -> bool:
    # Length check
    # Hex character check (0-9, A-F)
    # Uppercase enforcement
    # Range checks (domain 0-F, subdomain 1-F, etc.)
```

---

### Phase 6: Documentation (3-4 hours)
**Goal**: Complete docs with hex examples

---

## Registry Schema (Hex-Aware)

```yaml
version: 2.0.0
hex_support: true  # NEW: Flag for hex support

domains:
  '4':  # Hex domain (dimensions)
    name: dim
    subdomains:
      '1':  # Hex subdomain (geo)
        name: geo

        # Write-side
        next_write_entity: '2'  # Next: entity 2
        write_entities:
          location:
            entity_num: '1'  # Hex string
            files:
              - code: '014111'
                type: tb_
              - code: '014112'
                type: tb_

        # Read-side (independent!)
        next_read_entity: '4'  # Next: entity 4
        read_entities:
          v_location:
            entity_num: '1'
            files:
              - code: '024110'
          v_count:
            entity_num: '2'
            files:
              - code: '024120'
          tv_location:
            entity_num: '3'
            files:
              - code: '024130'
                type: tv_
                depends_on: []

  'A':  # Hex domain A (decimal 10) - Analytics
    name: analytics
    subdomains:
      '3':  # Hex subdomain 3
        name: marketing
        next_read_entity: 'D'  # Next: entity D (decimal 13)
        read_entities:
          customer_segment:
            entity_num: 'C'  # Hex C (decimal 12)
            files:
              - code: '02A3C0'
                type: tv_
```

---

## Code Generation Examples

### Hex Sequence Progression

**Entity sequence** (when you have >9 entities):
```
1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F
                           ↑  ↑  ↑  ↑  ↑  ↑
                          10 11 12 13 14 15 (decimal)
```

**File sequence** (when you have >9 files for one entity):
```
Entity 3, Files: 1, 2, 3, ..., 9, A, B, C, D, E, F
                                ↑
                                10th file (hex A)
```

---

## Hex Helper Functions

### Increment Hex Sequence

```python
def increment_hex(current: str) -> str:
    """
    Increment hex sequence: '9' → 'A', 'F' → overflow

    Examples:
        '1' → '2'
        '9' → 'A'
        'E' → 'F'
        'F' → raise OverflowError
    """
    val = int(current, 16)
    if val >= 15:
        raise OverflowError("Max value (F) reached")
    return format(val + 1, 'X')  # Uppercase hex
```

### Parse Hex Code

```python
def parse_code(code: str) -> dict:
    """Parse '01A3C5' → components"""
    return {
        'schema': code[0],           # '0'
        'layer': int(code[1], 16),   # 1
        'domain': int(code[2], 16),  # 10 (hex A)
        'subdomain': int(code[3], 16), # 3
        'entity': int(code[4], 16),  # 12 (hex C)
        'file': int(code[5], 16),    # 5
    }
```

---

## Migration from Current System

### Existing Decimal Codes

**No migration needed!** Decimal 0-9 are valid hex values:
- `014112` is valid hex (all chars 0-9)
- Works with hex parser: `int('014112', 16)`

### When You Hit 10+ Entities

**Automatic progression** to hex:
```python
# Entity sequence in subdomain
1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C...

# Codes generated
024110  # Entity 1
024120  # Entity 2
...
024190  # Entity 9
0241A0  # Entity A (decimal 10) ← First hex entity
0241B0  # Entity B (decimal 11)
```

---

## Validation Rules

### Valid Hex Code

```python
VALID_HEX = re.compile(r'^0[123][0-9A-F]{4}$')

def validate_code(code: str) -> bool:
    """
    Rules:
    - 6 characters
    - Position 1: '0'
    - Position 2: '1', '2', or '3' (layer)
    - Positions 3-6: Hex (0-9, A-F)
    - Uppercase only
    - Subdomain/Entity/File: Not '0' (1-F)
    """
    if not VALID_HEX.match(code):
        return False

    # Check subdomain, entity, file not zero
    if code[3] == '0' or code[4] == '0' or code[5] == '0':
        return False

    return True
```

---

## Success Criteria

- [ ] `specql generate --include-tv` creates hierarchical structure
- [ ] Registry assigns hex codes (A-F when needed)
- [ ] Paths generated correctly for hex codes
- [ ] Registry tracks sequences per subdomain per layer
- [ ] Hex increment works (9→A, F→overflow error)
- [ ] Validation accepts hex codes
- [ ] All tests pass
- [ ] Documentation complete

---

## Open Questions (Resolved)

1. ✅ **Hex support**: Confirmed - use 0-9, A-F
2. ✅ **Capacity**: 15 entities/subdomain is sufficient
3. ⏭️ **CLI flag**: `--tv-output-mode=hierarchical` (default)
4. ⏭️ **Migration**: Automatic hex progression when >9

---

## Files to Create/Modify

### New Files
```
src/generators/schema/read_side_path_generator.py
src/generators/schema/hex_code_utils.py          ← NEW: Hex helpers
src/generators/schema/code_parser.py
src/registry/migrator.py
src/registry/validator.py
+ 8 new test files
+ 4 documentation files
```

### Modified Files
```
src/generators/schema/naming_conventions.py  (DomainRegistry - hex aware)
src/generators/schema_orchestrator.py        (generate_table_views)
src/cli/orchestrator.py                      (lines 424-437)
registry/domain_registry.yaml                (add hex_support: true)
```

---

## Timeline

**Phase 1**: Registry Enhancement (hex) - 6-8 hours
**Phase 2**: Path Generation (hex) - 4-5 hours
**Phase 3**: File Splitting - 4-6 hours
**Phase 4**: Orchestrator Integration - 5-7 hours
**Phase 5**: Migration & Validation (hex) - 4-5 hours
**Phase 6**: Documentation - 3-4 hours

**Total**: 26-35 hours (3-4 working days)

---

## Next Steps

1. ✅ Gap analysis complete
2. ✅ Hex format understood
3. ✅ Implementation plan created
4. ⏭️ **Review documents**
5. ⏭️ **Create feature branch**: `feature/hierarchical-tv-hex`
6. ⏭️ **Begin Phase 1**: Registry enhancement with hex support

---

**Key Documents**:
- `20251112_code_format_HEXADECIMAL.md` - Complete hex spec
- `20251112_hierarchical_view_organization_REVISED.md` - Full plan (needs hex update)
- `20251112_current_vs_target_comparison.md` - Visual comparison

**The hex support eliminates all scalability concerns - you can scale to hundreds of entities per subdomain if needed!**
