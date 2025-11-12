# Issue #6 Implementation Plan: Fix Hierarchical Generator Subdomain Parsing

**Status**: COMPLEX - Phased TDD Approach
**Issue**: [#6 - Hierarchical generator incorrectly parses table_code subdomain](https://github.com/evoludigit/specql/issues/6)
**Created**: 2025-11-11
**Priority**: HIGH - Blocks production migration from PrintOptim backend

---

## Executive Summary

The hierarchical output generator incorrectly parses 6-digit table codes, extracting **2 digits** for the subdomain instead of **1 digit**. This results in:
- Incorrect directory names (e.g., `01311_subdomain_11` instead of `0131_classification`)
- Multiple directories created for entities in the same subdomain
- Generic `subdomain_XX` names instead of meaningful registry names

**Root Cause**: The subdomain code extraction in `naming_conventions.py:688-691` treats the subdomain as 2 digits when it should be 1 digit.

**Impact**:
- ✅ SQL generation is perfect (no functional issues)
- ❌ Directory structure doesn't match reference backend
- ❌ Makes navigation and comparison difficult during migration
- ❌ Violates user expectations for hierarchical organization

---

## Table Code Format Analysis

### Correct 6-Digit Format: `XYZWWF`

```
Example: 013111

Position breakdown:
  X Y = 01  Schema layer (write_side)
  Z   = 3   Domain code (catalog)
  W   = 1   Subdomain code (classification) ← SINGLE DIGIT
  W   = 1   Entity sequence within subdomain
  F   = 1   File sequence

Full breakdown:
  01 = write_side (schema layer)
  3  = catalog (domain)
  1  = classification (subdomain) ← THE BUG IS HERE
  1  = first entity in subdomain
  1  = first file for entity
```

### Current Incorrect Parsing

**File**: `src/generators/schema/naming_conventions.py`

```python
# Line 688-691 (INCORRECT)
subdomain_code = f"{components.subdomain_code}{components.entity_sequence}"[:2]
# For table_code "013111":
#   components.subdomain_code = "1" (position 3)
#   components.entity_sequence = "1" (position 4)
#   subdomain_code = "11"[:2] = "11" ❌ WRONG!

# This creates directory: "01311_subdomain_11" instead of "0131_classification"
```

### Correct Parsing Should Be

```python
# For table_code "013111":
#   schema_layer = "01" (positions 0-1)
#   domain_code = "3" (position 2)
#   subdomain_code = "1" (position 3) ✅ SINGLE DIGIT
#   entity_sequence = "1" (position 4)
#   file_sequence = "1" (position 5)

# This creates directory: "0131_classification"
```

### Real-World Examples from PrintOptim

| Table Code | Correct Parse | Current (Wrong) | Expected Directory | Current Directory |
|-----------|--------------|-----------------|-------------------|------------------|
| `013111` | 01-3-1-1-1 | 01-3-11-1 ❌ | `0131_classification/` | `01311_subdomain_11/` |
| `013121` | 01-3-1-2-1 | 01-3-12-1 ❌ | `0131_classification/` | `01312_subdomain_12/` |
| `013131` | 01-3-1-3-1 | 01-3-13-1 ❌ | `0131_classification/` | `01313_subdomain_13/` |
| `013211` | 01-3-2-1-1 | 01-3-21-1 ❌ | `0132_manufacturer/` | `01321_subdomain_21/` |
| `013231` | 01-3-2-3-1 | 01-3-23-1 ❌ | `0132_manufacturer/` | `01323_subdomain_23/` |
| `013242` | 01-3-2-4-2 | 01-3-24-2 ❌ | `0132_manufacturer/` | `01324_subdomain_24/` |

**Key Insight**: All entities with subdomain code `1` (classification) should be in **one** directory `0131_classification/`, not split across multiple directories!

---

## Domain Registry Structure

The registry already has correct subdomain definitions:

```yaml
domains:
  '3':
    name: catalog
    subdomains:
      '01':  # ← Single digit subdomain code
        name: classification
        description: Product classification, categories & taxonomies
      '02':  # ← Single digit subdomain code
        name: manufacturer
        description: Manufacturer-related entities (brand, model, range)
      '03':
        name: product
      '04':
        name: generic
      '05':
        name: financing
      '06':
        name: inventory
```

---

## PHASES

### Phase 1: Fix NumberingParser Subdomain Field

**Objective**: Update `TableCodeComponents` to correctly represent subdomain as single digit

**Why First**: The parser is the foundational layer - all other code depends on correct parsing

#### TDD Cycle 1.1: Add Failing Test for Subdomain Parsing

**RED**: Write test that expects single-digit subdomain
```python
# File: tests/unit/numbering/test_numbering_parser.py

def test_parse_table_code_subdomain_single_digit():
    """Subdomain should be SINGLE digit (position 3)"""
    parser = NumberingParser()

    # Test case from PrintOptim: ColorMode entity
    components = parser.parse_table_code_detailed("013111")

    assert components.schema_layer == "01"
    assert components.domain_code == "3"
    assert components.subdomain_code == "1"  # ← SINGLE DIGIT
    assert components.entity_sequence == "1"
    assert components.file_sequence == "1"

def test_parse_table_code_manufacturer_subdomain():
    """Manufacturer subdomain (code 2) should parse correctly"""
    parser = NumberingParser()

    components = parser.parse_table_code_detailed("013211")

    assert components.subdomain_code == "2"  # ← SINGLE DIGIT
    assert components.entity_sequence == "1"
```

Expected failure:
```
AssertionError: Subdomain code parsing not yet implemented
```

**GREEN**: Minimal implementation to pass
```python
# File: src/numbering/numbering_parser.py

@dataclass
class TableCodeComponents:
    """Structured representation of parsed table code components"""

    schema_layer: str      # 2 hex chars: schema type (01=write_side, etc.)
    domain_code: str       # 1 hex char: domain (0-F)
    subdomain_code: str    # 1 hex char: subdomain (0-F) ← NEW
    entity_sequence: str   # 1 hex char: entity sequence
    file_sequence: str     # 1 hex char: file sequence

def parse_table_code_detailed(self, table_code: str) -> TableCodeComponents:
    """Parse 6-character hexadecimal table code"""

    table_code = table_code.upper()

    if not re.match(r"^[0-9A-F]{6}$", table_code):
        raise ValueError(f"Invalid table_code: {table_code}")

    return TableCodeComponents(
        schema_layer=table_code[0:2],
        domain_code=table_code[2],
        subdomain_code=table_code[3],    # ← CORRECT: single digit
        entity_sequence=table_code[4],   # ← RENAMED from entity_code
        file_sequence=table_code[5],
    )
```

**REFACTOR**: Update tests to use new field names
```bash
# Run parser tests
uv run pytest tests/unit/numbering/test_numbering_parser.py -v
```

**QA**: Verify all numbering parser tests pass
```bash
# Full test suite for numbering module
uv run pytest tests/unit/numbering/ -v
uv run pytest tests/unit/cli/test_numbering_systems.py -v
```

**Success Criteria**:
- [ ] `test_parse_table_code_subdomain_single_digit` passes
- [ ] `test_parse_table_code_manufacturer_subdomain` passes
- [ ] All existing numbering tests still pass
- [ ] New field names are clearer than old ones

---

### Phase 2: Fix NamingConventions Subdomain Lookup

**Objective**: Update `generate_file_path()` to use correct single-digit subdomain code

**Why Second**: This is where directory paths are generated - depends on Phase 1

#### TDD Cycle 2.1: Add Failing Test for Directory Path Generation

**RED**: Write test that expects correct subdomain directory
```python
# File: tests/unit/registry/test_naming_conventions.py

def test_generate_file_path_subdomain_classification():
    """Entities in classification subdomain should share directory"""
    conventions = NamingConventions()

    # Mock entity
    from src.core.ast_models import Entity
    entity = Entity(name="ColorMode", schema="catalog")

    # Generate path for table_code 013111
    path = conventions.generate_file_path(
        entity=entity,
        table_code="013111",
        file_type="table",
        base_dir="generated"
    )

    # Should contain "0131_classification" subdomain directory
    assert "0131_classification" in path
    # Should NOT contain wrong codes
    assert "01311_subdomain_11" not in path
    assert "subdomain_11" not in path

def test_generate_file_path_same_subdomain_different_entities():
    """Multiple entities in same subdomain should share directory"""
    conventions = NamingConventions()

    from src.core.ast_models import Entity

    # Three entities in classification subdomain (code 1)
    entities = [
        ("ColorMode", "013111"),
        ("DuplexMode", "013121"),
        ("MachineFunction", "013131"),
    ]

    paths = []
    for name, table_code in entities:
        entity = Entity(name=name, schema="catalog")
        path = conventions.generate_file_path(
            entity=entity,
            table_code=table_code,
            file_type="table",
            base_dir="generated"
        )
        paths.append(path)

    # All three should contain "0131_classification"
    for path in paths:
        assert "0131_classification" in path

    # All three should share the same subdomain directory prefix
    subdomain_prefixes = [
        p.split("/")[2] for p in paths  # Extract subdomain dir
    ]
    assert len(set(subdomain_prefixes)) == 1  # All the same
    assert subdomain_prefixes[0] == "0131_classification"
```

Expected failure:
```
AssertionError: "0131_classification" not found in path
```

**GREEN**: Fix the subdomain code extraction
```python
# File: src/generators/schema/naming_conventions.py

def generate_file_path(
    self,
    entity: Entity,
    table_code: str,
    file_type: str = "table",
    base_dir: str = "generated/migrations",
) -> str:
    """Generate hierarchical file path for entity"""

    components = self.parser.parse_table_code_detailed(table_code)

    # Schema layer directory
    schema_layer_name = self.registry.registry["schema_layers"].get(
        components.schema_layer, f"schema_{components.schema_layer}"
    )
    schema_dir = f"{components.schema_layer}_{schema_layer_name}"

    # Domain directory
    domain_data = self.registry.registry["domains"].get(components.domain_code, {})
    domain_name = domain_data.get("name", f"domain_{components.domain_code}")
    domain_dir = f"{components.full_domain}_{domain_name}"

    # Subdomain directory - FIXED: use subdomain_code (single digit)
    subdomain_code = components.subdomain_code  # ← FIXED: single digit
    subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code, {})
    subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")

    # Build 4-digit subdomain directory code: schema_layer + domain + subdomain
    subdomain_dir_code = f"{components.schema_layer}{components.domain_code}{subdomain_code}"
    subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"

    # Entity group directory (5 digits: subdomain + entity_sequence)
    entity_lower = entity.name.lower()
    entity_group_code = f"{subdomain_dir_code}{components.entity_sequence}"
    entity_group_dir = f"{entity_group_code}_{entity_lower}_group"

    # File name
    file_extensions = {
        "table": "sql",
        "function": "sql",
        "comment": "sql",
        "test": "sql",
        "yaml": "yaml",
        "json": "json",
    }
    ext = file_extensions.get(file_type, "sql")

    file_prefixes = {
        "table": f"tb_{entity_lower}",
        "function": f"fn_{entity_lower}",
        "comment": f"comments_{entity_lower}",
        "test": f"test_{entity_lower}",
        "yaml": entity_lower,
        "json": entity_lower,
    }
    filename = file_prefixes.get(file_type, entity_lower)

    # Complete path
    return str(
        Path(base_dir)
        / schema_dir
        / domain_dir
        / subdomain_dir
        / entity_group_dir
        / f"{table_code}_{filename}.{ext}"
    )
```

**REFACTOR**: Simplify and add comments
```python
# Add property to TableCodeComponents for clarity
@property
def full_subdomain(self) -> str:
    """Full subdomain code: schema_layer + domain + subdomain (4 digits)"""
    return f"{self.schema_layer}{self.domain_code}{self.subdomain_code}"

# Use in generate_file_path
subdomain_dir_code = components.full_subdomain
```

**QA**: Verify all naming tests pass
```bash
# Run naming conventions tests
uv run pytest tests/unit/registry/test_naming_conventions.py -v

# Run full registry tests
uv run pytest tests/unit/registry/ -v
```

**Success Criteria**:
- [ ] `test_generate_file_path_subdomain_classification` passes
- [ ] `test_generate_file_path_same_subdomain_different_entities` passes
- [ ] All existing naming tests still pass
- [ ] Path generation is clearer and more maintainable

---

### Phase 3: Fix register_entity_auto Subdomain Code

**Objective**: Update entity registration to use correct single-digit subdomain code

**Why Third**: Entity registration depends on correct parsing and path generation

#### TDD Cycle 3.1: Add Failing Test for Entity Registration

**RED**: Write test for correct subdomain registration
```python
# File: tests/unit/registry/test_naming_conventions.py

def test_register_entity_auto_subdomain_classification(tmp_path):
    """Entity registration should use single-digit subdomain code"""

    # Create temporary registry
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("""
version: 1.0.0
domains:
  '3':
    name: catalog
    subdomains:
      '01':
        name: classification
        next_entity_sequence: 1
        entities: {}
      '02':
        name: manufacturer
        next_entity_sequence: 1
        entities: {}
""")

    conventions = NamingConventions(registry_path=str(registry_path))

    from src.core.ast_models import Entity
    entity = Entity(name="ColorMode", schema="catalog")

    # Register with table_code 013111
    # Subdomain should be "01" (classification), NOT "11"
    conventions.register_entity_auto(entity, "013111")

    # Reload registry
    conventions.registry.load()

    # Verify registered in correct subdomain
    assert "ColorMode" in conventions.registry.registry["domains"]["3"]["subdomains"]["01"]["entities"]
    # Should NOT be in wrong subdomain
    assert "11" not in conventions.registry.registry["domains"]["3"]["subdomains"]
```

Expected failure:
```
KeyError: '11'  # Tries to register in non-existent subdomain "11"
```

**GREEN**: Fix subdomain code extraction in register_entity_auto
```python
# File: src/generators/schema/naming_conventions.py

def register_entity_auto(self, entity: Entity, table_code: str):
    """Automatically register entity in registry after generation"""

    components = self.parser.parse_table_code_detailed(table_code)
    entity_code = self.derive_entity_code(entity.name)

    # FIXED: Use single-digit subdomain_code
    subdomain_code = components.subdomain_code  # ← Now correct

    # Subdomain codes in registry are 2-digit with leading zero
    # e.g., "01", "02", "03" not "1", "2", "3"
    subdomain_code_padded = subdomain_code.zfill(2)

    self.registry.register_entity(
        entity_name=entity.name,
        table_code=table_code,
        entity_code=entity_code,
        domain_code=components.domain_code,
        subdomain_code=subdomain_code_padded,  # ← Use padded version
    )
```

**REFACTOR**: Add validation
```python
def register_entity_auto(self, entity: Entity, table_code: str):
    """Automatically register entity in registry after generation"""

    components = self.parser.parse_table_code_detailed(table_code)
    entity_code = self.derive_entity_code(entity.name)

    # Get subdomain code (single hex digit)
    subdomain_code = components.subdomain_code

    # Registry uses 2-digit codes with leading zero
    subdomain_code_padded = subdomain_code.zfill(2)

    # Validate subdomain exists in registry
    domain_data = self.registry.registry["domains"].get(components.domain_code)
    if not domain_data:
        raise ValueError(f"Domain {components.domain_code} not found in registry")

    if subdomain_code_padded not in domain_data.get("subdomains", {}):
        raise ValueError(
            f"Subdomain {subdomain_code_padded} not found in domain {components.domain_code}. "
            f"Available: {list(domain_data.get('subdomains', {}).keys())}"
        )

    self.registry.register_entity(
        entity_name=entity.name,
        table_code=table_code,
        entity_code=entity_code,
        domain_code=components.domain_code,
        subdomain_code=subdomain_code_padded,
    )
```

**QA**: Verify registration works correctly
```bash
# Run registration tests
uv run pytest tests/unit/registry/test_naming_conventions.py::test_register_entity_auto -v

# Full registry tests
uv run pytest tests/unit/registry/ -v
```

**Success Criteria**:
- [ ] `test_register_entity_auto_subdomain_classification` passes
- [ ] Entities register in correct subdomain
- [ ] Clear error messages for invalid subdomains
- [ ] All registry tests pass

---

### Phase 4: Integration Testing with Real PrintOptim Data

**Objective**: Verify fix works with real-world 74-entity migration scenario

**Why Fourth**: Integration tests ensure all pieces work together

#### TDD Cycle 4.1: Add Integration Test for Multiple Entities

**RED**: Write comprehensive integration test
```python
# File: tests/integration/test_issue_6_subdomain_parsing.py

"""Integration tests for Issue #6: Subdomain parsing fix"""

import pytest
from pathlib import Path
from src.cli.orchestrator import CLIOrchestrator


class TestIssue6SubdomainParsing:
    """Test fix for Issue #6: Hierarchical generator subdomain parsing"""

    def test_classification_subdomain_entities_share_directory(self, tmp_path):
        """
        Test that entities in same subdomain share directory

        Reproduces PrintOptim scenario:
        - ColorMode (013111), DuplexMode (013121), MachineFunction (013131)
        - All have subdomain code "1" (classification)
        - Should all be in directory: 0131_classification/
        """

        # Create test YAML files for classification entities
        entities = [
            ("ColorMode", "013111", "Color mode options (BW, color, grayscale)"),
            ("DuplexMode", "013121", "Duplex printing modes"),
            ("MachineFunction", "013131", "Machine function categories"),
        ]

        yaml_files = []
        for name, table_code, desc in entities:
            yaml_file = tmp_path / f"{name.lower()}.yaml"
            yaml_file.write_text(f"""
entity: {name}
schema: catalog
organization:
  table_code: "{table_code}"
description: {desc}

fields:
  name: text
  code: text
""")
            yaml_files.append(str(yaml_file))

        # Generate with hierarchical output
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        # Verify no errors
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        # Check directory structure
        # Should have: 01_write_side/013_catalog/0131_classification/
        classification_dir = output_dir / "01_write_side" / "013_catalog" / "0131_classification"
        assert classification_dir.exists(), f"Classification subdomain directory not found"

        # All three entity groups should be under classification
        entity_groups = list(classification_dir.glob("*_group"))
        assert len(entity_groups) == 3, f"Expected 3 entity groups, found {len(entity_groups)}"

        # Verify entity group directory names
        group_names = [g.name for g in entity_groups]
        assert any("colormode" in g for g in group_names)
        assert any("duplexmode" in g for g in group_names)
        assert any("machinefunction" in g for g in group_names)

        # Verify NO wrong directories exist
        wrong_dirs = list(output_dir.rglob("*subdomain_11*"))
        assert len(wrong_dirs) == 0, f"Found wrong subdomain_11 directory: {wrong_dirs}"

    def test_manufacturer_subdomain_entities_share_directory(self, tmp_path):
        """
        Test manufacturer subdomain (code 2)

        Entities: Manufacturer (013211), Model (013231), Accessory (013242)
        All should be in: 0132_manufacturer/
        """

        entities = [
            ("Manufacturer", "013211", "Printer/copier manufacturers"),
            ("Model", "013231", "Manufacturer product models"),
            ("Accessory", "013242", "Machine accessories and add-ons"),
        ]

        yaml_files = []
        for name, table_code, desc in entities:
            yaml_file = tmp_path / f"{name.lower()}.yaml"
            yaml_file.write_text(f"""
entity: {name}
schema: catalog
organization:
  table_code: "{table_code}"
description: {desc}

fields:
  name: text
""")
            yaml_files.append(str(yaml_file))

        # Generate with hierarchical output
        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        # Verify no errors
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        # Check manufacturer subdomain directory
        manufacturer_dir = output_dir / "01_write_side" / "013_catalog" / "0132_manufacturer"
        assert manufacturer_dir.exists(), f"Manufacturer subdomain directory not found"

        # All three entity groups should be under manufacturer
        entity_groups = list(manufacturer_dir.glob("*_group"))
        assert len(entity_groups) == 3, f"Expected 3 entity groups, found {len(entity_groups)}"

        # Verify NO wrong directories
        wrong_dirs = list(output_dir.rglob("*subdomain_21*"))
        assert len(wrong_dirs) == 0, f"Found wrong subdomain_21 directory"
        wrong_dirs = list(output_dir.rglob("*subdomain_23*"))
        assert len(wrong_dirs) == 0, f"Found wrong subdomain_23 directory"

    def test_cross_subdomain_separation(self, tmp_path):
        """
        Test that different subdomains create separate directories

        ColorMode (013111) → 0131_classification/
        Manufacturer (013211) → 0132_manufacturer/
        """

        entities = [
            ("ColorMode", "013111", "catalog"),
            ("Manufacturer", "013211", "catalog"),
        ]

        yaml_files = []
        for name, table_code, schema in entities:
            yaml_file = tmp_path / f"{name.lower()}.yaml"
            yaml_file.write_text(f"""
entity: {name}
schema: {schema}
organization:
  table_code: "{table_code}"

fields:
  name: text
""")
            yaml_files.append(str(yaml_file))

        output_dir = tmp_path / "generated"
        orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

        result = orchestrator.generate_from_files(
            entity_files=yaml_files,
            output_dir=str(output_dir),
        )

        assert len(result.errors) == 0

        # Both subdomain directories should exist
        catalog_dir = output_dir / "01_write_side" / "013_catalog"
        classification_dir = catalog_dir / "0131_classification"
        manufacturer_dir = catalog_dir / "0132_manufacturer"

        assert classification_dir.exists(), "Classification subdomain missing"
        assert manufacturer_dir.exists(), "Manufacturer subdomain missing"

        # ColorMode should be under classification
        colormode_groups = list(classification_dir.glob("*colormode*"))
        assert len(colormode_groups) > 0, "ColorMode not in classification subdomain"

        # Manufacturer should be under manufacturer
        manufacturer_groups = list(manufacturer_dir.glob("*manufacturer*"))
        assert len(manufacturer_groups) > 0, "Manufacturer not in manufacturer subdomain"
```

**GREEN**: Verify all integration tests pass
```bash
# Run new integration tests
uv run pytest tests/integration/test_issue_6_subdomain_parsing.py -v

# Should pass with Phase 1-3 fixes applied
```

**REFACTOR**: Clean up and document
- Add docstrings explaining test scenarios
- Extract common test fixtures
- Add comments linking to issue #6

**QA**: Full integration test suite
```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run hex hierarchical tests
uv run pytest tests/integration/test_hex_hierarchical_generation.py -v
```

**Success Criteria**:
- [ ] All three new integration tests pass
- [ ] Directory structure matches PrintOptim reference
- [ ] No `subdomain_XX` generic names generated
- [ ] All existing integration tests still pass

---



### Phase 4.5: Snake_case Conversion & Remove _group Suffix

**Objective**: Convert entity names to snake_case and remove `_group` suffix from directories

**Why Here**: After integration testing to ensure consistent naming

**Detailed Plan**: See [`issue_6_phase_4_5_naming.md`](./issue_6_phase_4_5_naming.md)

#### Summary

**Current Behavior** (After Phases 1-4):
```
0131_classification/
  01311_colormode_group/          ← lowercase only, has _group
  01312_duplexmode_group/         ← lowercase only, has _group
```

**Desired Behavior** (After Phase 4.5):
```
0131_classification/
  01311_color_mode/               ✅ snake_case, no _group
  01312_duplex_mode/              ✅ snake_case, no _group
```

#### Key Changes

1. **New Utility**: `src/generators/naming_utils.py`
   - `camel_to_snake()` function
   - Handles all edge cases (acronyms, numbers, etc.)

2. **Update `generate_file_path()`**: Use `camel_to_snake(entity.name)`
   - Convert entity names to snake_case
   - Remove `_group` suffix from directory names

3. **Update Tests**: Expect snake_case and no `_group`

4. **Update Documentation**: Show snake_case in examples

#### TDD Cycles

- **Cycle 4.5.1**: Add utility function with tests
- **Cycle 4.5.2**: Update path generation
- **Cycle 4.5.3**: Update integration tests
- **Cycle 4.5.4**: Update other usages (CLI, etc.)

**Estimated Time**: 2-3 hours

**Success Criteria**:
- [ ] `camel_to_snake()` utility implemented and tested
- [ ] All paths use snake_case
- [ ] No `_group` suffix anywhere
- [ ] All tests pass
- [ ] Documentation updated

---

### Phase 6: Documentation & Examples

**Objective**: Document the fix and update examples

**Why Last**: Help users understand the correct behavior with all changes complete

#### Tasks:

1. **Update Architecture Docs**
```markdown
# File: docs/architecture/NUMBERING_SYSTEMS_VERIFICATION.md

## Table Code Format (6 Digits)

**Correct Format**: `XYZWWF`

- `XY` (2 digits): Schema layer (01=write_side, 02=read_side, 03=functions)
- `Z` (1 digit): Domain code (1-F)
- `W` (1 digit): **Subdomain code (0-F)** ← Single digit
- `W` (1 digit): Entity sequence within subdomain
- `F` (1 digit): File sequence

### Example: ColorMode (013111)

```
01 = write_side (schema layer)
3  = catalog (domain)
1  = classification (subdomain) ← SINGLE DIGIT
1  = first entity in subdomain
1  = first file
```

### Hierarchical Directory Structure

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/        ← 4 digits: layer+domain+subdomain
        01311_color_mode/         ← 5 digits: +entity_sequence, snake_case
          013111_tb_color_mode.sql ← 6 digits: +file_sequence
        01312_duplex_mode/        ← snake_case, no _group
          013121_tb_duplex_mode.sql
```
```

2. **Update README Examples**
```markdown
# File: README.md

## Hierarchical Output

SpecQL can organize generated SQL files in a hierarchical directory structure
based on table codes:

```bash
specql generate entities/*.yaml --use-registry --output-format hierarchical
```

This creates a structure like:

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/
        01311_color_mode/
          013111_tb_color_mode.sql
```

Entities in the same subdomain share a directory, making it easy to navigate
related tables. Entity names use snake_case for consistency.
```

3. **Add Migration Guide for Users**
```markdown
# File: docs/migration/issue_6_subdomain_fix.md

# Migration Guide: Subdomain Parsing Fix (Issue #6)

## What Changed

SpecQL v0.2.1 fixes subdomain parsing in hierarchical output:

**Before (v0.2.0)**:
```
generated/
  01_write_side/
    013_catalog/
      01311_subdomain_11/  ← Wrong: 2-digit subdomain
      01312_subdomain_12/  ← Wrong: separate directory
      01313_subdomain_13/  ← Wrong: separate directory
```

**After (v0.2.1)**:
```
generated/
  01_write_side/
    013_catalog/
      0131_classification/  ← Correct: 1-digit subdomain, shared directory
        01311_color_mode/   ← snake_case, no _group
        01312_duplex_mode/
        01313_machine_function/
```

## Impact

- ✅ SQL generation unchanged (no breaking changes to database schema)
- ✅ Directory structure now matches registry subdomain names
- ✅ Entities in same subdomain grouped together

## Action Required

If you generated files with v0.2.0 using `--output-format hierarchical`:

1. **Re-generate** with v0.2.1 to get correct directory structure
2. **Update** any scripts that reference old directory names
3. **No database changes** needed - SQL content is identical

## Checking Your Version

```bash
specql --version  # Should show v0.2.1 or higher
```
```

4. **Update CLI Help Text**
```python
# File: src/cli/generate.py

@click.option(
    "--output-format",
    type=click.Choice(["hierarchical", "confiture"]),
    default="hierarchical",
    help=(
        "Output format:\n"
        "  hierarchical: Full registry-based directory structure\n"
        "                (e.g., 01_write_side/013_catalog/0131_classification/)\n"
        "  confiture: Flat db/schema/ structure compatible with Confiture"
    ),
)
```

**Success Criteria**:
- [ ] Architecture docs updated with correct format
- [ ] README has clear examples
- [ ] Migration guide published
- [ ] CLI help text is accurate

---

## Testing Strategy

### Unit Tests
```bash
# Parser tests
uv run pytest tests/unit/numbering/test_numbering_parser.py -v

# Naming conventions tests
uv run pytest tests/unit/registry/test_naming_conventions.py -v

# Full unit suite
uv run pytest tests/unit/ -v
```

### Integration Tests
```bash
# Issue #6 specific tests
uv run pytest tests/integration/test_issue_6_subdomain_parsing.py -v

# Hex hierarchical tests
uv run pytest tests/integration/test_hex_hierarchical_generation.py -v

# Full integration suite
uv run pytest tests/integration/ -v
```

### Regression Tests
```bash
# Ensure no breaking changes
uv run pytest tests/unit/cli/test_numbering_systems.py -v
uv run pytest tests/unit/cli/test_registry_integration.py -v

# Full test suite
uv run pytest --tb=short
```

### Manual Testing
```bash
# Generate with PrintOptim-like entities
specql generate entities/catalog/*.yaml \
  --use-registry \
  --output-format hierarchical \
  --output-dir generated/test

# Verify directory structure
tree generated/test

# Should see:
# 01_write_side/
#   013_catalog/
#     0131_classification/
#       01311_colormode_group/
#       01312_duplexmode_group/
#     0132_manufacturer/
#       01321_manufacturer_group/
#       01323_model_group/
```

---

## Success Criteria

### Phase 1 ✅
- [ ] `TableCodeComponents` has `subdomain_code` field (single digit)
- [ ] `TableCodeComponents` has `entity_sequence` field

- [ ] All numbering parser tests pass

### Phase 2 ✅
- [ ] `generate_file_path()` uses `subdomain_code` (single digit)
- [ ] Subdomain directories use 4-digit codes (e.g., `0131_classification`)
- [ ] Subdomain names looked up from registry
- [ ] All naming convention tests pass

### Phase 3 ✅
- [ ] `register_entity_auto()` uses correct subdomain code
- [ ] Entities register in correct subdomain section
- [ ] Registry validation prevents invalid subdomains
- [ ] All registry tests pass

### Phase 4 ✅
- [ ] Integration tests verify PrintOptim scenario
- [ ] Multiple entities in same subdomain share directory
- [ ] No `subdomain_XX` generic names generated
- [ ] Cross-subdomain separation works correctly

### Phase 4.5 ✅
- [ ] `camel_to_snake()` utility implemented in `src/generators/naming_utils.py`
- [ ] All entity names converted to snake_case
- [ ] No `_group` suffix in directory names
- [ ] All paths use snake_case naming
- [ ] All tests updated to expect snake_case
- [ ] Documentation shows snake_case examples



### Phase 6 ✅
- [ ] Architecture docs updated
- [ ] README examples updated
- [ ] Migration guide published
- [ ] CLI help text accurate

### Final Validation ✅
- [ ] Full test suite passes (`make test`)
- [ ] PrintOptim 74-entity migration works
- [ ] Directory structure matches reference backend
- [ ] No regressions in existing functionality

---

## Risk Assessment

### Low Risk
- ✅ SQL generation unchanged (no database impact)
- ✅ Affects only directory structure (file organization)
- ✅ Backward compatibility maintained

### Medium Risk
- ⚠️ External scripts referencing directory paths may break
- ⚠️ Users with v0.2.0 hierarchical output need to regenerate

### Mitigation
- 📋 Clear migration guide
- 📋 Deprecation warnings for old field names
- 📋 Comprehensive test coverage
- 📋 Documentation updates

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|---------------|------------|
| Phase 1: Parser Fix | 1-2 hours | Low |
| Phase 2: Path Generation | 2-3 hours | Medium |
| Phase 3: Registration | 1-2 hours | Low |
| Phase 4: Integration Tests | 2-3 hours | Medium |
| **Phase 4.5: Snake_case & Remove _group** | **2-3 hours** | **Medium** |

| Phase 6: Documentation | 2-3 hours | Low |
| **Total** | **10-16 hours** | **Medium** |

---

## Next Steps

1. **Start with Phase 1** - Fix the parser (foundational)
2. **TDD Discipline** - Write failing tests first
3. **Incremental Progress** - Complete one phase before moving to next
4. **Documentation as You Go** - Update docs with each phase
5. **Continuous Testing** - Run full suite after each phase

---

**Implementation Ready**: YES
**Blocking Issues**: NONE
**Dependencies**: NONE

---

*Last Updated: 2025-11-11*
*Status: Ready for Implementation*
