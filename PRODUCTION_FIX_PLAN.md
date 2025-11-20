# SpecQL 0.7.0 → 0.8.0: Production Fix Plan

**Date**: 2025-11-20
**Target**: Fix all critical user-reported bugs
**Estimated Timeline**: 3-4 days (phased approach)
**User Report**: `/tmp/SPECQL_FEEDBACK_REPORT.md`

---

## Executive Summary

First user testing revealed **7 critical/major issues** preventing production use. This plan addresses all blockers through a phased TDD approach, prioritizing by impact.

**Success Criteria**:
- ✅ Package installs cleanly (`pip install specql`)
- ✅ All Django field types extracted correctly
- ✅ Multi-model files fully processed
- ✅ Generated YAML passes validation
- ✅ Complete workflow works: reverse → validate → generate
- ✅ Pattern detection functions correctly

---

## Phase 1: Package Structure Foundation (P0 - CRITICAL)

**Objective**: Fix broken package installation so tool is actually usable

### Issues Addressed
- Issue #1: Broken package installation (import paths)
- Issue #7: Pattern import error (related to #1)

### Current State
```
❌ pip install specql==0.7.0
❌ specql --help
   → ModuleNotFoundError: No module named 'src'
```

**Root Cause**: Code uses `from src.cli.*` but package installs files at root level without `src/` directory.

---

### TDD Cycle 1.1: Package Structure Test

#### RED Phase
**Test**: `tests/integration/test_package_installation.py`

```python
"""Test that package installs and imports work correctly"""
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

def test_fresh_install_imports():
    """Test package installation in clean venv"""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"

        # Create clean venv
        venv.create(venv_path, with_pip=True)
        pip = venv_path / "bin" / "pip"
        python = venv_path / "bin" / "python"

        # Install package
        subprocess.run([pip, "install", "-e", "."], check=True)

        # Test imports
        result = subprocess.run(
            [python, "-c", "from cli.main import app; print('OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

def test_cli_command_works():
    """Test CLI entry point works after installation"""
    result = subprocess.run(
        ["specql", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "SpecQL" in result.stdout
```

**Run**: `uv run pytest tests/integration/test_package_installation.py -v`

**Expected**: FAIL - ModuleNotFoundError

---

#### GREEN Phase
**Implementation**: Fix package structure

**Option A: Flatten imports (RECOMMENDED - simpler)**

1. **Update all imports** - Remove `src.` prefix:
   ```bash
   # Find all files with src imports
   find . -name "*.py" -type f -exec grep -l "from src\." {} \;

   # Replace src.cli → cli, src.infrastructure → infrastructure, etc.
   # Use Edit tool for each file
   ```

2. **Update pyproject.toml**:
   ```toml
   [tool.setuptools.packages.find]
   where = ["."]
   include = ["cli*", "infrastructure*", "core*", "generators*", "registry*"]
   exclude = ["tests*", "docs*"]
   ```

3. **Update entry points**:
   ```toml
   [project.scripts]
   specql = "cli.main:app"  # NOT src.cli.main:app
   ```

**Option B: Keep src/ structure (requires packaging changes)**
- More complex, requires reorganizing package structure
- Defer unless Option A has issues

**Verification**:
```bash
# Build package
uv build

# Test in clean environment
pip install dist/specql-0.8.0-*.whl
specql --help  # Should work!
```

---

#### REFACTOR Phase
- Ensure consistent import patterns across codebase
- Update developer documentation
- Add import linting rules to prevent regression

---

#### QA Phase
**Tests**:
```bash
# Package installation tests
uv run pytest tests/integration/test_package_installation.py -v

# All unit tests still pass
uv run pytest tests/unit/ -v

# Manual verification
pip uninstall specql -y
pip install -e .
specql --help
specql reverse-python --help
```

**Success Criteria**:
- ✅ Package installs without errors
- ✅ All imports work
- ✅ CLI commands function
- ✅ No `src.` prefixes needed

---

## Phase 2: Django Field Extraction (P0 - CRITICAL)

**Objective**: Extract ALL model fields, not just some

### Issues Addressed
- Issue #2: Missing fields in reverse engineering

### Current State
```python
# Django model has 6 fields + id
class Booker(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    group_size = models.PositiveIntegerField(...)  # ❌ MISSING
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Generated YAML only has 5 fields
# group_size completely missing!
```

---

### TDD Cycle 2.1: Comprehensive Field Type Coverage

#### RED Phase
**Test**: `tests/unit/infrastructure/test_django_field_extraction.py`

```python
"""Test extraction of all Django field types"""
import textwrap
from infrastructure.django_parser import DjangoModelParser

def test_positive_integer_field_extraction():
    """Test PositiveIntegerField is extracted"""
    source_code = textwrap.dedent("""
        from django.db import models
        from django.core.validators import MinValueValidator

        class Booker(models.Model):
            group_size = models.PositiveIntegerField(
                validators=[MinValueValidator(1)]
            )
    """)

    parser = DjangoModelParser()
    entities = parser.parse(source_code)

    assert len(entities) == 1
    booker = entities[0]

    # Should extract group_size field
    field_names = [f.name for f in booker.fields]
    assert "group_size" in field_names

    # Should map to integer type
    group_size = next(f for f in booker.fields if f.name == "group_size")
    assert group_size.type == "integer"

def test_all_django_numeric_fields():
    """Test all numeric field types are extracted"""
    source_code = textwrap.dedent("""
        from django.db import models

        class TestModel(models.Model):
            int_field = models.IntegerField()
            positive_int = models.PositiveIntegerField()
            small_int = models.SmallIntegerField()
            big_int = models.BigIntegerField()
            decimal_field = models.DecimalField(max_digits=10, decimal_places=2)
            float_field = models.FloatField()
    """)

    parser = DjangoModelParser()
    entities = parser.parse(source_code)

    field_names = [f.name for f in entities[0].fields]
    assert len(field_names) == 6
    assert "int_field" in field_names
    assert "positive_int" in field_names
    assert "small_int" in field_names
    assert "big_int" in field_names
    assert "decimal_field" in field_names
    assert "float_field" in field_names

def test_field_with_validators():
    """Test fields with validators are extracted"""
    source_code = textwrap.dedent("""
        from django.db import models
        from django.core.validators import MinValueValidator, MaxValueValidator

        class TestModel(models.Model):
            age = models.PositiveIntegerField(
                validators=[
                    MinValueValidator(0),
                    MaxValueValidator(150)
                ]
            )
    """)

    parser = DjangoModelParser()
    entities = parser.parse(source_code)

    field_names = [f.name for f in entities[0].fields]
    assert "age" in field_names
```

**Run**: `uv run pytest tests/unit/infrastructure/test_django_field_extraction.py -v`

**Expected**: FAIL - group_size not extracted

---

#### GREEN Phase
**Investigation**: Debug why PositiveIntegerField is skipped

1. **Add logging to parser**:
   ```python
   # infrastructure/django_parser.py
   def _extract_fields(self, class_node):
       for node in ast.walk(class_node):
           if isinstance(node, ast.Assign):
               field_info = self._parse_field_assignment(node)
               if field_info:
                   self.logger.debug(f"✅ Extracted field: {field_info['name']}")
               else:
                   self.logger.debug(f"⚠️ Skipped assignment: {ast.unparse(node)}")
   ```

2. **Find root cause**:
   - Check field type mapping in `DJANGO_FIELD_TYPE_MAP`
   - Check if validators block extraction
   - Check AST parsing logic

3. **Fix field extraction**:
   ```python
   # Likely issue: PositiveIntegerField not in type map
   DJANGO_FIELD_TYPE_MAP = {
       'CharField': 'text',
       'EmailField': 'email',
       'IntegerField': 'integer',
       'PositiveIntegerField': 'integer',  # ← ADD THIS
       'PositiveSmallIntegerField': 'integer',
       'SmallIntegerField': 'integer',
       'BigIntegerField': 'integer',
       'DecimalField': 'decimal',
       'FloatField': 'decimal',
       # ... add all missing types
   }
   ```

**Verification**:
```bash
uv run pytest tests/unit/infrastructure/test_django_field_extraction.py -v
# Should now pass
```

---

#### REFACTOR Phase
**Improvements**:

1. **Comprehensive type coverage**:
   ```python
   # Add ALL Django field types
   DJANGO_FIELD_TYPE_MAP = {
       # Text
       'CharField': 'text',
       'TextField': 'text',
       'SlugField': 'text',
       'EmailField': 'email',
       'URLField': 'text',

       # Numeric
       'IntegerField': 'integer',
       'PositiveIntegerField': 'integer',
       'PositiveSmallIntegerField': 'integer',
       'SmallIntegerField': 'integer',
       'BigIntegerField': 'integer',
       'AutoField': 'integer',
       'BigAutoField': 'integer',
       'SmallAutoField': 'integer',
       'DecimalField': 'decimal',
       'FloatField': 'decimal',

       # DateTime
       'DateTimeField': 'timestamp',
       'DateField': 'date',
       'TimeField': 'time',

       # Boolean
       'BooleanField': 'boolean',
       'NullBooleanField': 'boolean',

       # Other
       'JSONField': 'json',
       'UUIDField': 'uuid',
       'BinaryField': 'binary',
       'FileField': 'text',
       'ImageField': 'text',
   }
   ```

2. **Add validator extraction** (optional):
   ```python
   def _extract_validators(self, field_node):
       """Extract validators and convert to constraints"""
       # MinValueValidator(1) → constraints: min: 1
       # MaxLengthValidator(255) → constraints: max_length: 255
       pass
   ```

---

#### QA Phase
**Tests**:
```bash
# Unit tests
uv run pytest tests/unit/infrastructure/test_django_field_extraction.py -v

# Integration test with real Django model
echo "from django.db import models
class TestModel(models.Model):
    group_size = models.PositiveIntegerField()" > /tmp/test_model.py

specql reverse-python /tmp/test_model.py --dry-run
# Should show: "Fields: 1" and include group_size
```

**Success Criteria**:
- ✅ All Django numeric field types extracted
- ✅ Fields with validators extracted
- ✅ User's Booker model extracts all 6 fields

---

## Phase 3: Multi-Model Detection (P0 - CRITICAL)

**Objective**: Process ALL models in a file, not just the first one

### Issues Addressed
- Issue #3: Multiple models not detected

### Current State
```python
# File has 3 models
class Booker(models.Model): pass      # ✅ Detected
class Accommodation(models.Model): pass  # ❌ Skipped
class Booking(models.Model): pass     # ❌ Skipped

# Only generates: booker.yaml
```

---

### TDD Cycle 3.1: Multi-Model Parsing

#### RED Phase
**Test**: `tests/unit/infrastructure/test_multi_model_parsing.py`

```python
"""Test parsing files with multiple Django models"""
import textwrap
from infrastructure.django_parser import DjangoModelParser

def test_multiple_models_in_one_file():
    """Test all models in file are detected"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Booker(models.Model):
            name = models.CharField(max_length=255)

        class Accommodation(models.Model):
            title = models.CharField(max_length=255)

        class Booking(models.Model):
            status = models.CharField(max_length=50)
    """)

    parser = DjangoModelParser()
    entities = parser.parse(source_code)

    # Should extract all 3 models
    assert len(entities) == 3

    entity_names = [e.name for e in entities]
    assert "Booker" in entity_names
    assert "Accommodation" in entity_names
    assert "Booking" in entity_names

def test_models_with_intermediate_classes():
    """Test models are detected even with non-model classes"""
    source_code = textwrap.dedent("""
        from django.db import models

        class HelperClass:
            pass

        class ModelA(models.Model):
            field1 = models.CharField(max_length=255)

        class AnotherHelper:
            pass

        class ModelB(models.Model):
            field2 = models.CharField(max_length=255)
    """)

    parser = DjangoModelParser()
    entities = parser.parse(source_code)

    # Should only extract models, not helpers
    assert len(entities) == 2
    entity_names = [e.name for e in entities]
    assert "ModelA" in entity_names
    assert "ModelB" in entity_names
    assert "HelperClass" not in entity_names
    assert "AnotherHelper" not in entity_names
```

**Run**: `uv run pytest tests/unit/infrastructure/test_multi_model_parsing.py -v`

**Expected**: FAIL - only first model detected

---

#### GREEN Phase
**Implementation**: Fix AST traversal

**Current code (likely issue)**:
```python
# infrastructure/django_parser.py
def parse(self, source_code: str) -> List[Entity]:
    tree = ast.parse(source_code)

    # ❌ BAD: Only processes first match
    for node in ast.walk(tree):
        if self._is_django_model(node):
            return [self._parse_model(node)]  # STOPS AFTER FIRST!

    return []
```

**Fixed code**:
```python
def parse(self, source_code: str) -> List[Entity]:
    tree = ast.parse(source_code)
    entities = []

    # ✅ GOOD: Process ALL classes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if self._is_django_model(node):
                entity = self._parse_model(node)
                entities.append(entity)

    return entities

def _is_django_model(self, class_node: ast.ClassDef) -> bool:
    """Check if class inherits from models.Model"""
    for base in class_node.bases:
        # Handle models.Model
        if isinstance(base, ast.Attribute):
            if base.attr == 'Model':
                return True
        # Handle direct Model import
        if isinstance(base, ast.Name):
            if base.id == 'Model':
                return True
    return False
```

**Verification**:
```bash
uv run pytest tests/unit/infrastructure/test_multi_model_parsing.py -v
# Should now pass
```

---

#### REFACTOR Phase
**Improvements**:

1. **Better class filtering**:
   ```python
   def _should_process_class(self, class_node: ast.ClassDef) -> bool:
       """Determine if class should be processed"""
       # Skip abstract models
       if self._is_abstract_model(class_node):
           return False

       # Skip proxy models (optional)
       if self._is_proxy_model(class_node):
           return False

       # Must inherit from models.Model
       return self._is_django_model(class_node)
   ```

2. **Preserve model order**:
   ```python
   # Use ast.iter_child_nodes instead of ast.walk
   # to maintain file order
   for node in tree.body:
       if isinstance(node, ast.ClassDef):
           if self._should_process_class(node):
               entities.append(self._parse_model(node))
   ```

---

#### QA Phase
**Tests**:
```bash
# Unit tests
uv run pytest tests/unit/infrastructure/test_multi_model_parsing.py -v

# Integration test
cat > /tmp/multi_models.py << 'EOF'
from django.db import models

class ModelA(models.Model):
    field_a = models.CharField(max_length=100)

class ModelB(models.Model):
    field_b = models.IntegerField()

class ModelC(models.Model):
    field_c = models.EmailField()
EOF

specql reverse-python /tmp/multi_models.py --preview
# Should show: "Would write: entities/modela.yaml"
#              "Would write: entities/modelb.yaml"
#              "Would write: entities/modelc.yaml"
```

**Success Criteria**:
- ✅ All models in file detected
- ✅ Each model generates separate YAML file
- ✅ Non-model classes ignored
- ✅ User's 3-model file generates 3 files

---

## Phase 4: YAML Validation (P1 - MAJOR)

**Objective**: Generated YAML must pass its own validation

### Issues Addressed
- Issue #5: Validation errors on generated YAML

### Current State
```bash
specql reverse bookings/models.py -o /tmp/output
specql validate /tmp/output/booker.yaml
# ❌ Error: 'list' object has no attribute 'items'
```

---

### TDD Cycle 4.1: Validation Compatibility

#### RED Phase
**Test**: `tests/integration/test_reverse_validate_roundtrip.py`

```python
"""Test that reverse engineering produces valid YAML"""
import tempfile
import textwrap
from pathlib import Path
from cli.commands.reverse import reverse_python
from cli.commands.validate import validate_files

def test_generated_yaml_passes_validation():
    """Test reverse → validate workflow"""
    # Create test Django model
    source_code = textwrap.dedent("""
        from django.db import models

        class Product(models.Model):
            name = models.CharField(max_length=255)
            price = models.DecimalField(max_digits=10, decimal_places=2)
            in_stock = models.BooleanField(default=True)
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write source file
        source_file = Path(tmpdir) / "models.py"
        source_file.write_text(source_code)

        # Generate YAML
        output_dir = Path(tmpdir) / "entities"
        reverse_python(source_file, output_dir=output_dir)

        # Validate generated YAML
        yaml_files = list(output_dir.glob("*.yaml"))
        assert len(yaml_files) == 1

        # Should pass validation
        result = validate_files(yaml_files)
        assert result.is_valid
        assert len(result.errors) == 0

def test_generated_yaml_with_actions():
    """Test validation of YAML with actions"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Order(models.Model):
            status = models.CharField(max_length=50)

            def cancel(self):
                self.status = 'cancelled'
                self.save()
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = Path(tmpdir) / "models.py"
        source_file.write_text(source_code)

        output_dir = Path(tmpdir) / "entities"
        reverse_python(source_file, output_dir=output_dir)

        yaml_files = list(output_dir.glob("*.yaml"))
        result = validate_files(yaml_files)

        # Should pass even with actions
        assert result.is_valid
```

**Run**: `uv run pytest tests/integration/test_reverse_validate_roundtrip.py -v`

**Expected**: FAIL - validation errors

---

#### GREEN Phase
**Investigation**: Find validation mismatch

1. **Add verbose validation**:
   ```python
   # cli/commands/validate.py
   try:
       schema = parse_specql_yaml(yaml_file)
   except Exception as e:
       print(f"❌ Validation failed: {yaml_file}")
       print(f"   Error: {e}")
       print(f"   Type: {type(e).__name__}")
       import traceback
       traceback.print_exc()
   ```

2. **Compare schemas**:
   ```yaml
   # What reverse engineering generates
   actions:
   - name: create_single_person
     steps:
     - type: return
       arguments:
         value: cls(name=name, email=email)

   # What validator expects
   actions:
   - name: create_single_person
     steps:
     - return: cls(name=name, email=email)  # Different format?
   ```

3. **Fix generator or validator**:
   - Option A: Update reverse engineering to match validation schema
   - Option B: Update validator to accept generated format
   - Option C: Both have bugs - fix to common standard

**Implementation**:
```python
# Likely issue: actions format mismatch
# infrastructure/django_parser.py

def _generate_action_yaml(self, method_node):
    # ❌ OLD: Complex nested structure
    return {
        'name': method_node.name,
        'steps': [
            {
                'type': 'return',
                'arguments': {'value': '...'}
            }
        ]
    }

    # ✅ NEW: Match validator schema
    return {
        'name': method_node.name,
        'steps': [
            {'return': '...'}  # Simpler format
        ]
    }
```

---

#### REFACTOR Phase
**Improvements**:

1. **Schema consistency**:
   - Define canonical YAML schema
   - Update generator to match
   - Update validator to match
   - Document schema format

2. **Better error messages**:
   ```python
   def validate_specql_yaml(yaml_path: Path) -> ValidationResult:
       try:
           with open(yaml_path) as f:
               data = yaml.safe_load(f)
       except yaml.YAMLError as e:
           return ValidationResult(
               is_valid=False,
               errors=[f"Invalid YAML syntax at line {e.line}: {e.reason}"]
           )

       # Validate structure
       errors = []
       if 'entity' not in data:
           errors.append("Missing required field: 'entity'")

       if 'fields' in data:
           if not isinstance(data['fields'], list):
               errors.append(f"'fields' must be a list, got {type(data['fields'])}")

       return ValidationResult(is_valid=len(errors) == 0, errors=errors)
   ```

---

#### QA Phase
**Tests**:
```bash
# Unit tests
uv run pytest tests/integration/test_reverse_validate_roundtrip.py -v

# Manual workflow test
specql reverse-python /tmp/test_model.py -o /tmp/entities
specql validate /tmp/entities/*.yaml
# Should show: ✅ All files valid

# Test with user's actual model
specql reverse-python bookings/domain/models.py -o /tmp/test
specql validate /tmp/test/*.yaml
# Should pass
```

**Success Criteria**:
- ✅ Generated YAML passes validation
- ✅ Clear error messages if validation fails
- ✅ User's workflow works end-to-end

---

## Phase 5: Pattern Detection (P1 - MAJOR)

**Objective**: Detect obvious patterns in Django models

### Issues Addressed
- Issue #4: Pattern detection completely fails

### Current State
```python
# Model with OBVIOUS audit trail pattern
class Booking(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Pattern detection result
specql detect-patterns bookings/models.py
# Output: No patterns detected
```

---

### TDD Cycle 5.1: Audit Trail Detection

#### RED Phase
**Test**: `tests/unit/infrastructure/test_pattern_detection.py`

```python
"""Test pattern detection on Django models"""
import textwrap
from infrastructure.pattern_detector import PatternDetector

def test_audit_trail_pattern_detection():
    """Test audit trail pattern is detected"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255)
            created_at = models.DateTimeField(auto_now_add=True)
            updated_at = models.DateTimeField(auto_now=True)
    """)

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    # Should detect audit trail
    assert len(patterns) > 0
    assert any(p.name == 'audit-trail' for p in patterns)

    audit_pattern = next(p for p in patterns if p.name == 'audit-trail')
    assert audit_pattern.confidence >= 0.9  # High confidence

def test_soft_delete_pattern_detection():
    """Test soft delete pattern is detected"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Document(models.Model):
            title = models.CharField(max_length=255)
            deleted_at = models.DateTimeField(null=True, blank=True)
            is_deleted = models.BooleanField(default=False)
    """)

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    assert any(p.name == 'soft-delete' for p in patterns)

def test_state_machine_pattern_detection():
    """Test state machine pattern is detected"""
    source_code = textwrap.dedent("""
        from django.db import models

        class Order(models.Model):
            status = models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('processing', 'Processing'),
                    ('shipped', 'Shipped'),
                    ('delivered', 'Delivered'),
                ],
                default='pending'
            )
    """)

    detector = PatternDetector()
    patterns = detector.detect(source_code)

    assert any(p.name == 'state-machine' for p in patterns)

def test_no_false_positives():
    """Test no patterns detected for simple model"""
    source_code = textwrap.dedent("""
        from django.db import models

        class SimpleModel(models.Model):
            name = models.CharField(max_length=255)
            value = models.IntegerField()
    """)

    detector = PatternDetector()
    patterns = detector.detect(source_code, min_confidence=0.5)

    # Should not detect any patterns
    assert len(patterns) == 0
```

**Run**: `uv run pytest tests/unit/infrastructure/test_pattern_detection.py -v`

**Expected**: FAIL - no patterns detected

---

#### GREEN Phase
**Implementation**: Pattern detection heuristics

```python
# infrastructure/pattern_detector.py

class Pattern:
    def __init__(self, name: str, confidence: float, fields: List[str]):
        self.name = name
        self.confidence = confidence
        self.fields = fields

class PatternDetector:
    def detect(self, source_code: str, min_confidence: float = 0.7) -> List[Pattern]:
        """Detect patterns in Django model code"""
        tree = ast.parse(source_code)
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Extract field information
                fields = self._extract_field_info(node)

                # Check for patterns
                patterns.extend(self._detect_audit_trail(fields))
                patterns.extend(self._detect_soft_delete(fields))
                patterns.extend(self._detect_state_machine(fields))

        # Filter by confidence
        return [p for p in patterns if p.confidence >= min_confidence]

    def _detect_audit_trail(self, fields: List[dict]) -> List[Pattern]:
        """Detect audit trail pattern"""
        field_names = [f['name'] for f in fields]

        # Pattern: created_at + updated_at
        has_created = any(name in ['created_at', 'created', 'date_created']
                          for name in field_names)
        has_updated = any(name in ['updated_at', 'updated', 'date_updated', 'modified_at']
                          for name in field_names)

        if has_created and has_updated:
            return [Pattern('audit-trail', confidence=1.0,
                           fields=['created_at', 'updated_at'])]

        # Partial match - only created_at
        if has_created:
            return [Pattern('audit-trail', confidence=0.6,
                           fields=['created_at'])]

        return []

    def _detect_soft_delete(self, fields: List[dict]) -> List[Pattern]:
        """Detect soft delete pattern"""
        field_names = [f['name'] for f in fields]

        # Pattern: deleted_at or is_deleted
        has_deleted_at = 'deleted_at' in field_names
        has_is_deleted = 'is_deleted' in field_names

        if has_deleted_at or has_is_deleted:
            confidence = 1.0 if has_deleted_at else 0.8
            return [Pattern('soft-delete', confidence=confidence,
                           fields=[name for name in ['deleted_at', 'is_deleted']
                                  if name in field_names])]

        return []

    def _detect_state_machine(self, fields: List[dict]) -> List[Pattern]:
        """Detect state machine pattern"""
        for field in fields:
            # Look for CharField with choices
            if field.get('type') == 'CharField' and field.get('choices'):
                num_states = len(field['choices'])

                # State machine if 3+ states
                if num_states >= 3:
                    confidence = 0.9
                    return [Pattern('state-machine', confidence=confidence,
                                   fields=[field['name']])]

        return []

    def _extract_field_info(self, class_node: ast.ClassDef) -> List[dict]:
        """Extract field information for pattern detection"""
        fields = []

        for node in class_node.body:
            if isinstance(node, ast.Assign):
                field_info = self._parse_field(node)
                if field_info:
                    fields.append(field_info)

        return fields

    def _parse_field(self, assign_node: ast.Assign) -> Optional[dict]:
        """Parse field assignment to extract metadata"""
        # Extract field name
        if not assign_node.targets:
            return None

        target = assign_node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        field_name = target.id

        # Extract field type and options
        if isinstance(assign_node.value, ast.Call):
            field_type = self._get_field_type(assign_node.value)
            choices = self._extract_choices(assign_node.value)

            return {
                'name': field_name,
                'type': field_type,
                'choices': choices
            }

        return None

    def _get_field_type(self, call_node: ast.Call) -> str:
        """Get Django field type from call node"""
        if isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        elif isinstance(call_node.func, ast.Name):
            return call_node.func.id
        return 'Unknown'

    def _extract_choices(self, call_node: ast.Call) -> Optional[List]:
        """Extract choices from CharField"""
        for keyword in call_node.keywords:
            if keyword.arg == 'choices':
                # Parse choices list
                if isinstance(keyword.value, ast.List):
                    return keyword.value.elts
        return None
```

**Verification**:
```bash
uv run pytest tests/unit/infrastructure/test_pattern_detection.py -v
# Should now pass
```

---

#### REFACTOR Phase
**Improvements**:

1. **More patterns**:
   - Foreign key patterns
   - Hierarchy patterns (parent_id, tree structure)
   - Tenant isolation (tenant_id)
   - Versioning (version field)

2. **Confidence scoring**:
   ```python
   def _calculate_confidence(self, indicators: dict) -> float:
       """Calculate pattern confidence based on indicators"""
       score = 0.0
       total = 0

       for indicator, weight in indicators.items():
           total += weight
           if indicator:
               score += weight

       return score / total if total > 0 else 0.0
   ```

3. **Pattern explanation**:
   ```python
   class Pattern:
       def __init__(self, name, confidence, fields, explanation):
           self.name = name
           self.confidence = confidence
           self.fields = fields
           self.explanation = explanation  # Why detected
   ```

---

#### QA Phase
**Tests**:
```bash
# Unit tests
uv run pytest tests/unit/infrastructure/test_pattern_detection.py -v

# Manual tests
specql detect-patterns bookings/models.py
# Should show:
#   ✅ audit-trail (confidence: 100%)
#   ✅ state-machine (confidence: 90%)

specql detect-patterns bookings/models.py --format json
# Should output JSON with pattern details
```

**Success Criteria**:
- ✅ Audit trail pattern detected
- ✅ State machine pattern detected
- ✅ Soft delete pattern detected
- ✅ No false positives on simple models

---

## Phase 6: Code Generation Templates (P1 - MAJOR)

**Objective**: Include all Jinja2 templates in package

### Issues Addressed
- Issue #6: Code generation completely broken

### Current State
```bash
specql generate entities/booker.yaml --foundation-only
# ❌ jinja2.exceptions.TemplateNotFound: 'mutation_result_type.sql.j2'
```

---

### TDD Cycle 6.1: Template Packaging

#### RED Phase
**Test**: `tests/integration/test_code_generation.py`

```python
"""Test SQL code generation"""
import tempfile
import textwrap
from pathlib import Path
from cli.commands.generate import generate_sql

def test_foundation_generation():
    """Test foundation SQL generation"""
    spec = textwrap.dedent("""
        entity: Product
        schema: catalog
        fields:
        - name: name
          type: text
        - name: price
          type: decimal
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "product.yaml"
        spec_file.write_text(spec)

        output_dir = Path(tmpdir) / "sql"

        # Should generate SQL without errors
        generate_sql(spec_file, output_dir=output_dir, foundation_only=True)

        # Check files exist
        assert (output_dir / "00_foundation" / "mutation_result_type.sql").exists()
        assert (output_dir / "10_tables" / "product.sql").exists()

def test_action_generation():
    """Test action SQL generation"""
    spec = textwrap.dedent("""
        entity: Order
        schema: sales
        fields:
        - name: status
          type: enum
          values: [pending, confirmed]
        actions:
        - name: confirm_order
          steps:
          - update: Order SET status = 'confirmed'
    """)

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "order.yaml"
        spec_file.write_text(spec)

        output_dir = Path(tmpdir) / "sql"

        # Should generate action SQL
        generate_sql(spec_file, output_dir=output_dir)

        assert (output_dir / "20_actions" / "confirm_order.sql").exists()
```

**Run**: `uv run pytest tests/integration/test_code_generation.py -v`

**Expected**: FAIL - template not found

---

#### GREEN Phase
**Implementation**: Fix template packaging

1. **Verify templates exist**:
   ```bash
   ls -la templates/sql/
   # Should show: mutation_result_type.sql.j2, table.sql.j2, etc.
   ```

2. **Update pyproject.toml**:
   ```toml
   [tool.setuptools.package-data]
   generators = ["templates/**/*"]

   # OR

   [tool.setuptools]
   include-package-data = true

   [tool.setuptools.packages.find]
   where = ["."]
   include = ["cli*", "generators*", "infrastructure*", "core*", "registry*"]

   [tool.setuptools.package-data]
   "*" = ["templates/**/*.j2"]
   ```

3. **Update MANIFEST.in**:
   ```
   recursive-include generators/templates *.j2
   recursive-include generators/templates *.sql.j2
   ```

4. **Fix template loading**:
   ```python
   # generators/base_generator.py
   import importlib.resources as resources

   class BaseGenerator:
       def _load_template(self, template_name: str):
           # ❌ OLD: File system path (breaks in installed package)
           template_dir = Path(__file__).parent / "templates"

           # ✅ NEW: Use package resources
           try:
               # Python 3.9+
               template_path = resources.files('generators') / 'templates' / template_name
               with template_path.open() as f:
                   return Template(f.read())
           except:
               # Fallback to file system (development)
               template_path = Path(__file__).parent / "templates" / template_name
               with open(template_path) as f:
                   return Template(f.read())
   ```

**Verification**:
```bash
# Rebuild package
uv build

# Install fresh
pip uninstall specql -y
pip install dist/specql-0.8.0-*.whl

# Test
specql generate entities/product.yaml --foundation-only
# Should work!
```

---

#### REFACTOR Phase
**Improvements**:

1. **Template discovery**:
   ```python
   def get_available_templates(self) -> List[str]:
       """List all available templates"""
       template_dir = resources.files('generators') / 'templates'
       return [f.name for f in template_dir.iterdir() if f.suffix == '.j2']
   ```

2. **Template validation**:
   ```python
   def validate_templates_exist(self):
       """Ensure all required templates are present"""
       required = [
           'mutation_result_type.sql.j2',
           'table.sql.j2',
           'action.sql.j2',
       ]

       for template in required:
           if not self._template_exists(template):
               raise TemplateNotFoundError(f"Required template missing: {template}")
   ```

---

#### QA Phase
**Tests**:
```bash
# Unit tests
uv run pytest tests/integration/test_code_generation.py -v

# Manual workflow
cat > /tmp/test.yaml << 'EOF'
entity: TestEntity
fields:
- name: value
  type: integer
EOF

specql generate /tmp/test.yaml -o /tmp/output --foundation-only
ls -la /tmp/output/
# Should show generated SQL files
```

**Success Criteria**:
- ✅ All templates included in package
- ✅ Code generation works in installed package
- ✅ Templates found via package resources
- ✅ User's workflow completes successfully

---

## Phase 7: Integration Testing & Polish (FINAL)

**Objective**: End-to-end testing and user experience improvements

### Tests
```bash
# Complete workflow test
specql reverse-python bookings/models.py -o entities/
specql validate entities/*.yaml
specql generate entities/*.yaml -o sql/
psql < sql/00_foundation/*.sql
psql < sql/10_tables/*.sql

# Expected: No errors, complete SQL schema generated
```

---

### TDD Cycle 7.1: Complete Workflow

#### RED Phase
**Test**: `tests/integration/test_complete_workflow.py`

```python
"""Test complete SpecQL workflow"""
def test_django_to_postgresql_workflow():
    """Test: Django model → SpecQL YAML → PostgreSQL SQL"""
    # 1. Create Django model
    django_model = create_test_django_model()

    # 2. Reverse engineer
    yaml_files = reverse_python(django_model)
    assert len(yaml_files) > 0

    # 3. Validate
    validation = validate_files(yaml_files)
    assert validation.is_valid

    # 4. Generate SQL
    sql_files = generate_sql(yaml_files)
    assert len(sql_files) > 0

    # 5. Test SQL in PostgreSQL
    with test_database() as db:
        for sql_file in sql_files:
            db.execute_file(sql_file)

        # Verify tables created
        tables = db.list_tables()
        assert 'tb_testmodel' in tables

def test_error_handling():
    """Test clear errors for common mistakes"""
    # Invalid YAML
    # Missing required fields
    # Invalid field types
    # etc.
```

---

#### GREEN Phase
Fix any remaining issues found in integration testing.

---

#### REFACTOR Phase
**Quality improvements**:

1. **Better CLI output**:
   ```python
   # Clear progress indicators
   with Progress() as progress:
       task = progress.add_task("Generating SQL...", total=len(entities))
       for entity in entities:
           generate_entity_sql(entity)
           progress.advance(task)
   ```

2. **Helpful error messages**:
   ```python
   # ❌ OLD
   Error: 'list' object has no attribute 'items'

   # ✅ NEW
   ❌ Validation Error in booker.yaml:
      Line 12: 'actions' must be a list of objects
      Found: ['create_single_person']
      Expected: [{'name': 'create_single_person', 'steps': [...]}]
   ```

3. **Rich metadata** (Issue #9):
   ```yaml
   _metadata:
     source_language: python
     source_file: /path/to/bookings/models.py
     generated_at: 2025-11-20T10:30:00Z
     specql_version: 0.8.0
     patterns_detected: [audit-trail]
     fields_extracted: 6
     fields_skipped: 0
   ```

---

#### QA Phase
**Full test suite**:
```bash
# All tests pass
make test

# Integration tests
make integration-test

# User's exact workflow
cd ~/django-project
specql reverse-python bookings/models.py -o specql/entities
specql validate specql/entities/*.yaml
specql generate specql/entities/*.yaml -o specql/sql
```

**Success Criteria**:
- ✅ All 7 critical issues fixed
- ✅ All tests passing (unit + integration)
- ✅ User's workflow completes without errors
- ✅ Clear, helpful error messages
- ✅ Package installs and works out of the box

---

## Release Checklist

### Pre-Release
- [ ] All Phase 1-7 tests passing
- [ ] Integration tests added for all fixed issues
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with all fixes
- [ ] Version bumped to 0.8.0

### Package Quality
- [ ] Fresh install test: `pip install specql==0.8.0` works
- [ ] All imports work without workarounds
- [ ] All CLI commands functional
- [ ] Templates included and loadable
- [ ] Help text complete and accurate

### User Validation
- [ ] Test with user's exact Django models
- [ ] All 3 models (Booker, Accommodation, Booking) processed
- [ ] All 6 fields extracted from Booker
- [ ] Patterns detected correctly
- [ ] Generated YAML validates
- [ ] SQL generation completes

### Documentation
- [ ] Update GETTING_STARTED.md
- [ ] Add troubleshooting guide
- [ ] Document limitations
- [ ] Add Django integration guide
- [ ] Update API docs

---

## Success Metrics

### Fixes Delivered
- ✅ Issue #1: Package installation works
- ✅ Issue #2: All fields extracted
- ✅ Issue #3: Multi-model detection works
- ✅ Issue #4: Pattern detection functional
- ✅ Issue #5: Generated YAML validates
- ✅ Issue #6: Code generation works
- ✅ Issue #7: Pattern imports work

### Quality Improvements
- ✅ 100% test coverage for fixed issues
- ✅ Integration tests for complete workflow
- ✅ Clear error messages
- ✅ Rich metadata in output
- ✅ Progress indicators

### User Experience
- ✅ Works out of the box (no workarounds)
- ✅ Complete workflow succeeds
- ✅ Fast and reliable
- ✅ Clear documentation

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Package Structure | Fix imports, update packaging | 4-6 hours |
| Phase 2: Field Extraction | Add field types, fix extraction | 3-4 hours |
| Phase 3: Multi-Model | Fix AST traversal | 2-3 hours |
| Phase 4: Validation | Fix schema format | 3-4 hours |
| Phase 5: Pattern Detection | Implement heuristics | 4-6 hours |
| Phase 6: Templates | Fix packaging, resource loading | 2-3 hours |
| Phase 7: Integration | E2E tests, polish | 4-6 hours |
| **Total** | | **22-32 hours** |

**Phased Delivery**:
- After Phase 1-3: **v0.8.0-beta1** (fixes critical blockers)
- After Phase 4-6: **v0.8.0-beta2** (fixes major features)
- After Phase 7: **v0.8.0** (production release)

---

## Risk Mitigation

### High Risk Areas
1. **Package structure changes** - May break development workflow
   - Mitigation: Test in CI before merging
   - Rollback plan: Revert imports, use symlink workaround

2. **Field extraction changes** - May affect other parsers
   - Mitigation: Run full test suite
   - Add regression tests

3. **Validation format changes** - May break existing YAML
   - Mitigation: Support both old and new formats temporarily
   - Add migration guide

### Testing Strategy
- Each phase has dedicated unit tests
- Integration tests after each phase
- Full regression suite before release
- Manual testing with user's models

---

## Post-Release

### Monitoring
- Track GitHub issues for new bug reports
- Monitor PyPI download stats
- Collect user feedback

### Follow-Up Work
- Performance optimization (if needed)
- Additional Django field types
- More pattern types
- Better documentation

---

**Next Steps**:
1. Review and approve this plan
2. Begin Phase 1 (package structure)
3. Deploy beta releases for user testing
4. Iterate based on feedback
5. Ship v0.8.0 production release

---

**End of Plan**
