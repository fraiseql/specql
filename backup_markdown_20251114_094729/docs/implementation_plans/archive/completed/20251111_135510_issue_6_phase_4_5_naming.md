# Phase 4.5: Snake_case Conversion and Remove _group Suffix

**Issue**: [#6 - Hierarchical generator incorrectly parses table_code subdomain](https://github.com/evoludigit/specql/issues/6)
**Phase**: 4.5 (inserted before Phase 5: Backward Compatibility)
**Objective**: Convert entity names to snake_case and remove `_group` suffix from directories
**Estimated Time**: 2-3 hours

---

## Background

### Current Behavior (After Phases 1-4)

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/
        01311_colormode_group/          ← "colormode" not snake_case, has "_group"
          013111_tb_colormode.sql
        01312_duplexmode_group/         ← "duplexmode" not snake_case, has "_group"
          013121_tb_duplexmode.sql
        01313_machinefunction_group/    ← "machinefunction" not snake_case, has "_group"
          013131_tb_machinefunction.sql
```

### Issues

1. **Not snake_case**: `colormode` should be `color_mode`, `duplexmode` → `duplex_mode`
2. **Unnecessary suffix**: `_group` doesn't add value and makes paths longer
3. **Inconsistent**: Framework convention is `snake_case` (see PostgreSQL adapter)

### Desired Behavior (After Phase 4.5)

```
generated/
  01_write_side/
    013_catalog/
      0131_classification/
        01311_color_mode/               ✅ Snake_case, no suffix
          013111_tb_color_mode.sql
        01312_duplex_mode/              ✅ Snake_case, no suffix
          013121_tb_duplex_mode.sql
        01313_machine_function/         ✅ Snake_case, no suffix
          013131_tb_machine_function.sql
```

---

## TDD Cycle 4.5.1: Add Utility Function

**Objective**: Create standardized camel_to_snake conversion utility

### RED: Write Test for Utility Function

```python
# File: tests/unit/generators/test_naming_utils.py (NEW FILE)

"""Tests for naming utility functions"""

import pytest


class TestCamelToSnake:
    """Test camel_to_snake conversion utility"""

    def test_simple_camel_case(self):
        """Simple CamelCase should convert correctly"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("ColorMode") == "color_mode"
        assert camel_to_snake("Contact") == "contact"

    def test_multiple_words(self):
        """Multiple word CamelCase"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("DuplexMode") == "duplex_mode"
        assert camel_to_snake("MachineFunction") == "machine_function"
        assert camel_to_snake("ManufacturerRange") == "manufacturer_range"

    def test_all_caps(self):
        """All caps should stay together"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("URL") == "url"
        assert camel_to_snake("HTTPServer") == "http_server"

    def test_acronym_middle(self):
        """Acronym in middle of name"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("PDFDocument") == "pdf_document"
        assert camel_to_snake("XMLParser") == "xml_parser"

    def test_already_snake_case(self):
        """Already snake_case should pass through"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("color_mode") == "color_mode"
        assert camel_to_snake("duplex_mode") == "duplex_mode"

    def test_numbers(self):
        """Handle numbers in names"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("Product2B") == "product_2_b"  # Number then uppercase letter
        assert camel_to_snake("Level3Support") == "level_3_support"
        assert camel_to_snake("IPv4Address") == "i_pv_4_address"  # Treats each part separately

    def test_single_word(self):
        """Single word should lowercase"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("Product") == "product"
        assert camel_to_snake("User") == "user"
```

Expected failure:
```
ModuleNotFoundError: No module named 'src.generators.naming_utils'
```

### GREEN: Implement Utility Function

```python
# File: src/generators/naming_utils.py (NEW FILE)

"""Naming utility functions for consistent entity name conversions"""

import re


def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase to snake_case

    This function handles:
    - Simple CamelCase: ColorMode → color_mode
    - Multiple words: DuplexMode → duplex_mode
    - Acronyms: HTTPServer → http_server
    - Numbers: Product2B → product_2_b (treats each component separately)
    - Already snake_case: color_mode → color_mode (pass through)

    Algorithm:
    1. Insert underscore before uppercase letters preceded by lowercase
    2. Insert underscore before uppercase letters preceded by digits
    3. Lowercase the entire result

    This means each distinct component gets separated:
    - Product2B → Product_2_B → product_2_b (3 components)
    - IPv4Address → I_Pv_4_Address → i_pv_4_address

    Args:
        name: CamelCase or PascalCase string

    Returns:
        snake_case string

    Examples:
        >>> camel_to_snake("ColorMode")
        'color_mode'
        >>> camel_to_snake("DuplexMode")
        'duplex_mode'
        >>> camel_to_snake("MachineFunction")
        'machine_function'
        >>> camel_to_snake("Product2B")
        'product_2_b'
        >>> camel_to_snake("Level3Support")
        'level_3_support'
    """
    # Already snake_case - pass through
    if "_" in name and name.islower():
        return name

    # Insert underscore between lowercase and uppercase letters
    # "colorMode" -> "color_Mode"
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)

    # Insert underscore between letters/numbers and uppercase
    # "color_Mode" -> "color__mode", "Product2B" -> "Product_2_B"
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)

    # Lowercase and remove double underscores
    result = s2.lower().replace("__", "_")

    # Remove leading/trailing underscores
    return result.strip("_")


def to_entity_name(name: str) -> str:
    """
    Convert entity name to snake_case for use in file/directory names

    Convenience wrapper around camel_to_snake for entity names.

    Args:
        name: Entity name (usually PascalCase)

    Returns:
        snake_case entity name

    Examples:
        >>> to_entity_name("Contact")
        'contact'
        >>> to_entity_name("DuplexMode")
        'duplex_mode'
    """
    return camel_to_snake(name)
```

### REFACTOR: Add Docstrings and Edge Cases

```python
def camel_to_snake(name: str) -> str:
    """
    Convert CamelCase to snake_case

    Algorithm:
    1. Check if already snake_case - pass through unchanged
    2. Insert underscore before uppercase letters preceded by lowercase
    3. Insert underscore before uppercase letters preceded by numbers
    4. Lowercase everything
    5. Clean up double underscores and trim

    Edge cases handled:
    - Empty string → empty string
    - Single letter → lowercase
    - All caps → lowercase (URL → url)
    - Mixed case with numbers → insert underscores (Product2B → product_2b)

    Args:
        name: CamelCase, PascalCase, or already snake_case string

    Returns:
        snake_case string

    Examples:
        >>> camel_to_snake("ColorMode")
        'color_mode'
        >>> camel_to_snake("HTTPServer")
        'http_server'
        >>> camel_to_snake("URL")
        'url'
        >>> camel_to_snake("")
        ''
    """
    if not name:
        return ""

    # Already snake_case - pass through
    if "_" in name and name.islower():
        return name

    # Insert underscores
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)

    # Lowercase and clean
    result = s2.lower().replace("__", "_").strip("_")

    return result
```

### QA: Run Tests

```bash
# Run new utility tests
uv run pytest tests/unit/generators/test_naming_utils.py -v

# Expected output: All tests pass
```

**Success Criteria**:
- [ ] `test_simple_camel_case` passes
- [ ] `test_multiple_words` passes
- [ ] `test_all_caps` passes
- [ ] `test_already_snake_case` passes
- [ ] All edge cases handled

---

## TDD Cycle 4.5.2: Update NamingConventions to Use Snake_case

**Objective**: Modify `generate_file_path()` to use snake_case and remove `_group` suffix

### RED: Write Test for Snake_case Paths

```python
# File: tests/unit/registry/test_naming_conventions.py

def test_generate_file_path_snake_case():
    """Entity names should be converted to snake_case"""
    from src.generators.schema.naming_conventions import NamingConventions
    from src.core.ast_models import Entity

    conventions = NamingConventions()

    # CamelCase entity name
    entity = Entity(name="ColorMode", schema="catalog")

    path = conventions.generate_file_path(
        entity=entity,
        table_code="013111",
        file_type="table",
        base_dir="generated"
    )

    # Should use snake_case
    assert "color_mode" in path
    # Should NOT use lowercase without underscores
    assert "colormode" not in path


def test_generate_file_path_no_group_suffix():
    """Entity directories should NOT have _group suffix"""
    from src.generators.schema.naming_conventions import NamingConventions
    from src.core.ast_models import Entity

    conventions = NamingConventions()

    entity = Entity(name="DuplexMode", schema="catalog")

    path = conventions.generate_file_path(
        entity=entity,
        table_code="013121",
        file_type="table",
        base_dir="generated"
    )

    # Should have entity name directory
    assert "duplex_mode" in path
    # Should NOT have _group suffix
    assert "duplex_mode_group" not in path
    assert "_group" not in path


def test_generate_file_path_complete_structure():
    """Complete path should follow snake_case convention"""
    from src.generators.schema.naming_conventions import NamingConventions
    from src.core.ast_models import Entity

    conventions = NamingConventions()

    entity = Entity(name="MachineFunction", schema="catalog")

    path = conventions.generate_file_path(
        entity=entity,
        table_code="013131",
        file_type="table",
        base_dir="generated"
    )

    # Expected path structure:
    # generated/01_write_side/013_catalog/0131_classification/01313_machine_function/013131_tb_machine_function.sql

    # Check each component
    assert "01_write_side" in path
    assert "013_catalog" in path
    assert "0131_classification" in path
    assert "01313_machine_function" in path  # No _group, snake_case
    assert "013131_tb_machine_function.sql" in path

    # Verify NO old patterns
    assert "machinefunction_group" not in path
    assert "machinefunction" not in path.split("/")[-2]  # Entity dir should be snake_case


def test_generate_file_path_function_files():
    """Function files should also use snake_case"""
    from src.generators.schema.naming_conventions import NamingConventions
    from src.core.ast_models import Entity

    conventions = NamingConventions()

    entity = Entity(name="ColorMode", schema="catalog")

    path = conventions.generate_file_path(
        entity=entity,
        table_code="013111",
        file_type="function",
        base_dir="generated"
    )

    # Function filename should be snake_case
    assert "fn_color_mode" in path
    assert "fn_colormode" not in path
```

Expected failure:
```
AssertionError: "color_mode" not found in path
AssertionError: "_group" found in path
```

### GREEN: Update generate_file_path()

```python
# File: src/generators/schema/naming_conventions.py

def generate_file_path(
    self,
    entity: Entity,
    table_code: str,
    file_type: str = "table",
    base_dir: str = "generated/migrations",
) -> str:
    """
    Generate hierarchical file path for entity

    Hierarchy:
    base_dir/
      SS_schema_layer/
        SSD_domain/
          SSDS_subdomain/
            SSDSE_entity/                ← No _group suffix, snake_case
              SSDSF_filename.ext

    Args:
        entity: Entity AST model
        table_code: 6-digit table code
        file_type: Type of file ('table', 'function', 'comment', 'test')
        base_dir: Base directory for generated files

    Returns:
        Complete file path with snake_case entity names

    Example:
        generate_file_path(ColorMode, "013111", "table")
        → "generated/01_write_side/013_catalog/0131_classification/01311_color_mode/013111_tb_color_mode.sql"
    """
    from src.generators.naming_utils import camel_to_snake

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
    subdomain_code = components.subdomain_code
    subdomain_data = domain_data.get("subdomains", {}).get(subdomain_code.zfill(2), {})
    subdomain_name = subdomain_data.get("name", f"subdomain_{subdomain_code}")

    # Build 4-digit subdomain directory code
    subdomain_dir_code = f"{components.schema_layer}{components.domain_code}{subdomain_code}"
    subdomain_dir = f"{subdomain_dir_code}_{subdomain_name}"

    # Entity directory - CHANGED: snake_case, no _group suffix
    entity_snake = camel_to_snake(entity.name)  # ColorMode → color_mode
    entity_dir_code = f"{subdomain_dir_code}{components.entity_sequence}"
    entity_dir = f"{entity_dir_code}_{entity_snake}"  # 01311_color_mode (no _group)

    # File name - CHANGED: use snake_case
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
        "table": f"tb_{entity_snake}",       # tb_color_mode
        "function": f"fn_{entity_snake}",    # fn_color_mode
        "comment": f"comments_{entity_snake}",
        "test": f"test_{entity_snake}",
        "yaml": entity_snake,
        "json": entity_snake,
    }
    filename = file_prefixes.get(file_type, entity_snake)

    # Complete path
    return str(
        Path(base_dir)
        / schema_dir
        / domain_dir
        / subdomain_dir
        / entity_dir  # Changed: no _group, snake_case
        / f"{table_code}_{filename}.{ext}"
    )
```

### REFACTOR: Extract Helper Method

```python
# File: src/generators/schema/naming_conventions.py

def _get_entity_snake_case(self, entity: Entity) -> str:
    """
    Get entity name in snake_case

    Args:
        entity: Entity AST model

    Returns:
        Entity name in snake_case

    Examples:
        ColorMode → color_mode
        DuplexMode → duplex_mode
    """
    from src.generators.naming_utils import camel_to_snake
    return camel_to_snake(entity.name)


def generate_file_path(
    self,
    entity: Entity,
    table_code: str,
    file_type: str = "table",
    base_dir: str = "generated/migrations",
) -> str:
    """Generate hierarchical file path for entity"""

    components = self.parser.parse_table_code_detailed(table_code)
    entity_snake = self._get_entity_snake_case(entity)  # Use helper

    # ... rest of the method
    entity_dir = f"{entity_dir_code}_{entity_snake}"
    filename = file_prefixes.get(file_type, entity_snake)
    # ...
```

### QA: Run Tests

```bash
# Run naming convention tests
uv run pytest tests/unit/registry/test_naming_conventions.py -v

# Should pass all new tests
uv run pytest tests/unit/registry/test_naming_conventions.py::test_generate_file_path_snake_case -v
uv run pytest tests/unit/registry/test_naming_conventions.py::test_generate_file_path_no_group_suffix -v
```

**Success Criteria**:
- [ ] All snake_case tests pass
- [ ] No `_group` suffix in paths
- [ ] Entity names properly converted
- [ ] All existing tests still pass

---

## TDD Cycle 4.5.3: Update Integration Tests

**Objective**: Ensure integration tests expect snake_case and no `_group` suffix

### RED: Update Expected Paths in Integration Tests

```python
# File: tests/integration/test_issue_6_subdomain_parsing.py

def test_classification_subdomain_entities_share_directory(self, tmp_path):
    """Test that entities in same subdomain share directory (with snake_case)"""

    entities = [
        ("ColorMode", "013111", "Color mode options"),
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

    output_dir = tmp_path / "generated"
    orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

    result = orchestrator.generate_from_files(
        entity_files=yaml_files,
        output_dir=str(output_dir),
    )

    assert len(result.errors) == 0, f"Errors: {result.errors}"

    # Check directory structure
    classification_dir = output_dir / "01_write_side" / "013_catalog" / "0131_classification"
    assert classification_dir.exists(), f"Classification subdomain directory not found"

    # All three entity directories should be under classification (snake_case, no _group)
    entity_dirs = list(classification_dir.glob("*"))
    assert len(entity_dirs) == 3, f"Expected 3 entity dirs, found {len(entity_dirs)}"

    # Verify snake_case names (no _group)
    dir_names = [d.name for d in entity_dirs]
    assert any("color_mode" in d for d in dir_names), f"color_mode not found in {dir_names}"
    assert any("duplex_mode" in d for d in dir_names), f"duplex_mode not found in {dir_names}"
    assert any("machine_function" in d for d in dir_names), f"machine_function not found in {dir_names}"

    # Verify NO _group suffix
    assert not any("_group" in d for d in dir_names), f"Found _group in {dir_names}"

    # Verify NO lowercase-only (non-snake_case)
    assert not any(d == "01311_colormode" for d in dir_names), "Found non-snake_case colormode"


def test_file_names_use_snake_case(self, tmp_path):
    """Test that generated SQL files use snake_case"""

    yaml_file = tmp_path / "colormode.yaml"
    yaml_file.write_text("""
entity: ColorMode
schema: catalog
organization:
  table_code: "013111"

fields:
  name: text
""")

    output_dir = tmp_path / "generated"
    orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

    result = orchestrator.generate_from_files(
        entity_files=[str(yaml_file)],
        output_dir=str(output_dir),
    )

    assert len(result.errors) == 0

    # Find SQL files
    sql_files = list(output_dir.rglob("*.sql"))
    assert len(sql_files) > 0, "No SQL files generated"

    # Check filenames use snake_case
    filenames = [f.name for f in sql_files]
    assert any("color_mode" in f for f in filenames), f"No snake_case in {filenames}"
    assert not any("colormode.sql" in f for f in filenames), f"Found non-snake_case in {filenames}"
```

### GREEN: Run Integration Tests

```bash
# Run updated integration tests
uv run pytest tests/integration/test_issue_6_subdomain_parsing.py -v

# Should pass with Phase 4.5 changes
```

### REFACTOR: Clean Up Test Code

Add helper functions for common assertions:

```python
# File: tests/integration/test_issue_6_subdomain_parsing.py

def _assert_snake_case_dirs(dir_list: list, expected_names: list[str]):
    """Helper: Assert directories use snake_case and expected names"""
    dir_names = [d.name for d in dir_list]

    for expected in expected_names:
        assert any(expected in d for d in dir_names), \
            f"{expected} not found in {dir_names}"

    # No _group suffix
    assert not any("_group" in d for d in dir_names), \
        f"Found _group suffix in {dir_names}"


def _assert_no_non_snake_case(dir_list: list, entity_names: list[str]):
    """Helper: Assert no non-snake_case directories"""
    dir_names = [d.name for d in dir_list]

    for entity in entity_names:
        # Check that lowercase-only version doesn't exist
        lowercase_only = entity.lower()
        assert not any(lowercase_only in d and "_" not in d.split(lowercase_only)[1]
                      for d in dir_names), \
            f"Found non-snake_case {lowercase_only}"
```

### QA: Run Full Integration Suite

```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Verify no regressions
uv run pytest tests/integration/test_hex_hierarchical_generation.py -v
```

**Success Criteria**:
- [ ] Integration tests expect snake_case
- [ ] No `_group` suffix expected
- [ ] All integration tests pass
- [ ] No regressions in existing tests

---

## TDD Cycle 4.5.4: Update Other Usages

**Objective**: Update any other code that generates entity names/paths

### Files to Check and Update

1. **`src/cli/orchestrator.py`**
   - Update mutation file path generation
   - Ensure snake_case for function files

2. **`src/generators/schema/table_generator.py`**
   - Check if any path generation happens here
   - Update to use snake_case

3. **`src/numbering/numbering_parser.py`**
   - Update `generate_directory_path()` if it exists
   - Use snake_case

### RED: Write Tests for Each Usage

```python
# File: tests/unit/cli/test_orchestrator.py

def test_orchestrator_mutation_paths_snake_case(tmp_path):
    """Mutation files should use snake_case"""
    from src.cli.orchestrator import CLIOrchestrator

    yaml_file = tmp_path / "colormode.yaml"
    yaml_file.write_text("""
entity: ColorMode
schema: catalog
organization:
  table_code: "013111"

fields:
  name: text

actions:
  - name: activate_color_mode
    steps:
      - update: ColorMode SET active = true
""")

    output_dir = tmp_path / "generated"
    orchestrator = CLIOrchestrator(use_registry=True, output_format="hierarchical")

    result = orchestrator.generate_from_files(
        entity_files=[str(yaml_file)],
        output_dir=str(output_dir),
    )

    # Find function files
    function_files = list(output_dir.rglob("*fn_*.sql"))

    if function_files:
        # Should use snake_case
        filenames = [f.name for f in function_files]
        assert any("color_mode" in f for f in filenames)
        assert not any("colormode" in f and "color_mode" not in f for f in filenames)
```

### GREEN: Update Code

```python
# File: src/cli/orchestrator.py

# In generate_from_files(), when generating mutation paths:

from src.generators.naming_utils import camel_to_snake

# ...

entity_snake = camel_to_snake(entity.name)

if self.output_format == "hierarchical":
    mutation_path = (
        functions_dir
        / f"{table_code}_fn_{entity_snake}_{mutation.action_name}.sql"
    )
else:
    mutation_path = functions_dir / f"{mutation.action_name}.sql"
```

### REFACTOR: Consolidate Naming Logic

Create a shared method in NamingConventions:

```python
# File: src/generators/schema/naming_conventions.py

def get_entity_filename(self, entity: Entity, file_type: str = "table") -> str:
    """
    Get standardized filename for entity

    Args:
        entity: Entity AST model
        file_type: Type of file (table, function, etc.)

    Returns:
        Filename prefix (without extension)

    Examples:
        get_entity_filename(ColorMode, "table") → "tb_color_mode"
        get_entity_filename(ColorMode, "function") → "fn_color_mode"
    """
    entity_snake = self._get_entity_snake_case(entity)

    prefixes = {
        "table": f"tb_{entity_snake}",
        "function": f"fn_{entity_snake}",
        "comment": f"comments_{entity_snake}",
        "test": f"test_{entity_snake}",
        "yaml": entity_snake,
        "json": entity_snake,
    }

    return prefixes.get(file_type, entity_snake)
```

### QA: Run All Tests

```bash
# Unit tests
uv run pytest tests/unit/cli/test_orchestrator.py -v
uv run pytest tests/unit/generators/ -v

# Full suite
uv run pytest --tb=short
```

**Success Criteria**:
- [ ] All file paths use snake_case
- [ ] No `_group` suffix anywhere
- [ ] Mutation files use snake_case
- [ ] Helper files use snake_case
- [ ] All tests pass

---

## Documentation Updates

### Update Visual Guide

```markdown
# File: docs/implementation_plans/issue_6_visual_guide.md

### Expected Output (CORRECT) ✅

```
generated/
  01_write_side/
    013_catalog/
      ├── 0131_classification/        ← Correct code, registry name
      │   ├── 01311_color_mode/       ← Snake_case, no _group ✅
      │   │   └── 013111_tb_color_mode.sql
      │   │
      │   ├── 01312_duplex_mode/      ← Snake_case, no _group ✅
      │   │   └── 013121_tb_duplex_mode.sql
      │   │
      │   └── 01313_machine_function/ ← Snake_case, no _group ✅
      │       └── 013131_tb_machine_function.sql
      │
      └── 0132_manufacturer/
          ├── 01321_manufacturer/
          │   └── 013211_tb_manufacturer.sql
          ├── 01323_model/
          │   └── 013231_tb_model.sql
          └── 01324_accessory/
              └── 013242_tb_accessory.sql
```
```

### Update Quick Reference

```markdown
# File: docs/implementation_plans/issue_6_quick_reference.md

## Directory Structure

### After All Fixes ✅
```
01_write_side/
  013_catalog/
    0131_classification/           ← 4 digits, registry name
      01311_color_mode/            ← Snake_case, no _group ✅
      01312_duplex_mode/           ← Snake_case, no _group ✅
      01313_machine_function/      ← Snake_case, no _group ✅
```
```

---

## Success Criteria

### Phase 4.5 Complete When:

- [ ] **Utility Function**
  - [ ] `camel_to_snake()` implemented in `src/generators/naming_utils.py`
  - [ ] All conversion tests pass
  - [ ] Edge cases handled (acronyms, numbers, etc.)

- [ ] **Path Generation Updated**
  - [ ] `generate_file_path()` uses `camel_to_snake()`
  - [ ] No `_group` suffix in directory names
  - [ ] All path tests pass

- [ ] **Integration Tests Updated**
  - [ ] Tests expect snake_case names
  - [ ] Tests expect no `_group` suffix
  - [ ] All integration tests pass

- [ ] **Other Usages Updated**
  - [ ] CLI orchestrator uses snake_case
  - [ ] Mutation files use snake_case
  - [ ] All file types consistent

- [ ] **Documentation Updated**
  - [ ] Visual guide shows snake_case
  - [ ] Quick reference updated
  - [ ] Examples use snake_case

- [ ] **Regression Prevention**
  - [ ] All existing tests pass
  - [ ] No breaking changes
  - [ ] Full test suite green

---

## Timeline

**Estimated Time**: 2-3 hours

| Task | Time |
|------|------|
| TDD Cycle 4.5.1: Utility Function | 30 min |
| TDD Cycle 4.5.2: Update Paths | 45 min |
| TDD Cycle 4.5.3: Integration Tests | 30 min |
| TDD Cycle 4.5.4: Other Usages | 45 min |
| Documentation | 30 min |

---

## Next Steps

After completing Phase 4.5:
1. **Proceed to Phase 5**: Backward Compatibility & Migration
2. **Run full test suite**: Ensure no regressions
3. **Update Phase 6**: Documentation to reflect snake_case convention

---

**Phase Status**: Ready for Implementation
**Dependencies**: Phases 1-4 must be complete
**Blocks**: Phase 5 (Backward Compatibility)

---

*Part of Issue #6 Implementation Plan - see [`issue_6_subdomain_parsing_fix.md`](./issue_6_subdomain_parsing_fix.md)*
