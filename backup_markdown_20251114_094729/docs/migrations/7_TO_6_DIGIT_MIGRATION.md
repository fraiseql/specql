# Migration Guide: 7-Digit to 6-Digit Numbering System

## Overview

This migration converts SpecQL from the legacy 7-digit SSDSSEX system to the unified 6-digit SDSEX system. The change eliminates the redundant file sequence digit and converts 2-digit subdomains to 1-digit.

## What Changed

### Code Format
- **Before**: `SSDSSEX` (7 digits) - Schema(2) + Domain(1) + Subdomain(2) + Entity(1) + File(1)
- **After**: `SDSEX` (6 digits) - Schema(2) + Domain(1) + Subdomain(1) + Entity(1) + File(1)

### Subdomain Codes
- **Before**: 2-digit codes (`"01"`, `"03"`, `"09"`)
- **After**: 1-digit codes (`"1"`, `"3"`, `"9"`)

### Directory Structure
- **Before**: Skipped 4-digit level, jumped from 3-digit to 5-digit directories
- **After**: Progressive structure with each level adding exactly 1 digit

## Migration Examples

### Table Codes
| Entity | Old Code | New Code | Path Change |
|--------|----------|----------|-------------|
| Contact | `0120391` | `012321` | `01203_customer` → `0123_customer` |
| Company | `0120191` | `012121` | `01201_core` → `0121_core` |
| Manufacturer | `0130291` | `013021` | `01302_manufacturer` → `0132_manufacturer` |

### Directory Structure Changes

**Before (7-digit)**:
```
01_write_side/
├── 012_crm/
│   ├── 01203_customer/     (5 digits - skipped 4-digit level!)
│   │   └── 012039_contact/ (6 digits)
│   │       └── 0120391_tb_contact.sql
│   └── 01201_core/
│       └── 012019_company/
│           └── 0120191_tb_company.sql
```

**After (6-digit)**:
```
01_write_side/
├── 012_crm/
│   ├── 0123_customer/      (4 digits - subdomain)
│   │   └── 01232_contact/  (5 digits - entity)
│   │       └── 012321_tb_contact.sql
│   └── 0121_core/
│       └── 01212_company/
│           └── 012121_tb_company.sql
```

## Files Modified

### Core Components
- `src/numbering/numbering_parser.py` - Updated to parse 6-digit codes
- `src/generators/schema/naming_conventions.py` - Generate 6-digit codes
- `registry/domain_registry.yaml` - Convert subdomain codes to 1-digit

### Path Generators
- `src/generators/schema/write_side_path_generator.py` - 6-digit codes, 1-digit subdomains
- `src/generators/schema/read_side_path_generator.py` - Added entity directories
- `src/generators/schema/code_parser.py` - Updated for 6-digit read-side codes
- `src/generators/actions/function_path_generator.py` - 6-digit function codes

### Tests
- `tests/integration/test_hierarchical_generation.py` - Updated codes and paths
- `tests/integration/test_table_code_integration.py` - Updated table codes
- `tests/unit/registry/test_naming_conventions.py` - Updated validation tests
- `tests/unit/numbering/test_numbering_parser.py` - Already correct for 6-digit

### Documentation
- `docs/architecture/NUMBERING_SYSTEM.md` - New comprehensive guide
- `.claude/CLAUDE.md` - Updated code format comments

## Migration Steps

### 1. Code Changes (Completed)
All code changes have been implemented and tested. The system now:
- Generates 6-digit codes
- Parses 6-digit codes only (rejects 7-digit)
- Uses 1-digit subdomain codes
- Creates proper hierarchical directory structures

### 2. Registry Migration (Completed)
Subdomain codes in `registry/domain_registry.yaml` converted:
- `"01"` → `"1"`
- `"02"` → `"2"`
- `"03"` → `"3"`
- etc.

### 3. Test Updates (Completed)
All test files updated with new codes and expected paths.

### 4. Existing Projects
For projects with existing 7-digit codes:

1. **Backup** your current `registry/domain_registry.yaml`
2. **Update** table codes in entity YAML files:
   ```yaml
   # Before
   table_code: "0120391"

   # After
   table_code: "012321"
   ```
3. **Regenerate** all files using the new system
4. **Verify** directory structure matches expectations

## Validation

Run these commands to verify the migration:

```bash
# Test core parsing
python3 -c "
from src.numbering.numbering_parser import NumberingParser
p = NumberingParser()
print('6-digit works:', p.parse_table_code_detailed('012321'))
try:
    p.parse_table_code_detailed('0120391')  # Should fail
    print('ERROR: 7-digit still accepted')
except ValueError:
    print('SUCCESS: 7-digit rejected')
"

# Test path generation
python3 -c "
from src.generators.schema.write_side_path_generator import WriteSidePathGenerator
from src.generators.schema.hierarchical_file_writer import FileSpec
gen = WriteSidePathGenerator()
spec = FileSpec(code='012321', name='tb_contact', content='test', layer='write_side')
print('Path:', gen.generate_path(spec))
"

# Run tests
uv run pytest tests/unit/numbering/ tests/unit/registry/test_naming_conventions.py -v
```

## Rollback Plan

If issues arise:

1. **Git**: All changes are committed, can revert to previous commit
2. **Registry**: Restore backup of `domain_registry.yaml`
3. **Projects**: Update table codes back to 7-digit format

## Benefits

- **Unified**: All layers use same 6-digit format
- **Progressive**: Directory structure adds 1 digit per level
- **Scalable**: 10×10×10×10 = 10,000 objects per layer
- **Compatible**: Works with UUID encoding requirements
- **Maintainable**: Consistent structure across all generators

## Questions?

See `docs/architecture/NUMBERING_SYSTEM.md` for detailed specification.</content>
</xai:function_call">Create the migration guide documentation